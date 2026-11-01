"""Research-only recognizer of an initiative transition on CLOSED 4h futures candles.

No original-strategy parity claim. No orders, account access or PAPER integration.
The raw USD-M 4h CSVs are sourced from the preceding independent behavior audit.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import asdict, dataclass
from typing import Sequence

BAR_MS = 4 * 60 * 60 * 1000
DAY_MS = 6 * BAR_MS


@dataclass(frozen=True)
class Bar:
    ts: int  # UTC 4h OPEN timestamp, milliseconds
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Decision:
    symbol: str
    attempt_at: int
    decision_at: int  # 4h confirmation candle CLOSE, first instant known
    eligible_entry_at: int  # next 4h OPEN; never simulate earlier
    side: str
    daily_regime: str  # descriptive, not an optimized directional gate
    boundary: float
    failed_extreme: float
    atr_at_attempt: float
    volume_ratio: float
    rejection_fraction: float
    response_atr: float
    reference_entry: float  # CONFIRM close, NOT a backtest fill
    stop: float
    opposite_structure: float
    room_rr: float
    evidence: tuple[str, ...]

    def as_dict(self) -> dict:
        result = asdict(self)
        result["evidence"] = list(self.evidence)
        return result


@dataclass(frozen=True)
class Outcome:
    symbol: str
    decision_at: int
    side: str
    entry_at: int | None
    entry: float | None
    exit_at: int | None
    exit: float | None
    exit_reason: str
    gross_pct: float | None
    base_pct: float | None
    stress_pct: float | None

    def as_dict(self) -> dict:
        return asdict(self)


def parse_csv(path: str) -> list[Bar]:
    """Read archived Binance USD-M raw bars; no spot API or live data."""
    import csv

    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        bars = [
            Bar(
                int(r["time_ms"]),
                float(r["open"]),
                float(r["high"]),
                float(r["low"]),
                float(r["close"]),
                float(r["volume"]),
            )
            for r in reader
        ]
    validate_bars(bars)
    return bars


def validate_bars(bars: Sequence[Bar]) -> None:
    for i, b in enumerate(bars):
        if b.ts % BAR_MS or (
            min(b.open, b.close) < b.low
            or max(b.open, b.close) > b.high
            or b.high < b.low
            or b.low <= 0
            or b.volume < 0
        ):
            raise ValueError(f"invalid USD-M 4h OHLCV at {i}")
        if i and b.ts - bars[i - 1].ts != BAR_MS:
            raise ValueError(f"gap, duplicate or unsorted 4h bars at {i}")


def prior_atr(bars: Sequence[Bar], index: int, count: int = 14) -> float:
    """ATR from bars [index-count, index), never including the decision bar."""
    if index <= count:
        raise ValueError("insufficient ATR lookback")
    return sum(
        max(
            bars[j].high - bars[j].low,
            abs(bars[j].high - bars[j - 1].close),
            abs(bars[j].low - bars[j - 1].close),
        )
        for j in range(index - count, index)
    ) / count


def closed_daily(bars: Sequence[Bar]) -> list[tuple[int, float, float, float]]:
    """Build only complete six-bar UTC days; end time is availability time."""
    days: list[tuple[int, float, float, float]] = []
    for i in range(0, len(bars)):
        if bars[i].ts % DAY_MS != 0 or i + 6 > len(bars):
            continue
        group = bars[i : i + 6]
        if any(group[j].ts != group[0].ts + j * BAR_MS for j in range(6)):
            continue
        days.append(
            (
                group[0].ts + DAY_MS,
                max(x.high for x in group),
                min(x.low for x in group),
                group[-1].close,
            )
        )
    return days


def asof_regime(daily: Sequence[tuple[int, float, float, float]], close_times: Sequence[int], asof: int) -> str:
    """Ex-ante daily context; no partially formed daily bar."""
    end = bisect_right(close_times, asof)
    if end < 21:
        return "UNKNOWN"
    window = daily[end - 21 : end]
    tr = sum(
        max(
            window[j][1] - window[j][2],
            abs(window[j][1] - window[j - 1][3]),
            abs(window[j][2] - window[j - 1][3]),
        )
        for j in range(7, 21)
    ) / 14
    if tr <= 0:
        return "RANGE"
    drift = (window[-1][3] - window[0][3]) / tr
    return "UP" if drift > 1.5 else "DOWN" if drift < -1.5 else "RANGE"


def detect(symbol: str, bars: Sequence[Bar]) -> tuple[list[Decision], list[dict]]:
    """Causal state machine: failed effort -> acceptance -> structurally viable entry.

    Each failed attempt is also retained with a rejection reason.
    Daily context is reported but NEVER silently excludes a countertrend signal.
    """
    validate_bars(bars)
    daily = closed_daily(bars)
    close_times = [x[0] for x in daily]
    decisions: list[Decision] = []
    attempts: list[dict] = []
    pending: dict | None = None
    for i in range(130, len(bars)):
        b = bars[i]
        if pending is not None:
            p = pending
            age = i - p["index"]
            # Conservative: any violation of the original failed extreme invalidates.
            failed = b.low <= p["extreme"] if p["side"] == "long" else b.high >= p["extreme"]
            if failed:
                attempts.append({**p["audit"], "status": "REJECTED", "reason": "EXTREME_REVISITED"})
                pending = None
                continue
            if age > 3:
                attempts.append({**p["audit"], "status": "REJECTED", "reason": "CONFIRMATION_EXPIRED"})
                pending = None
                continue
            response = (b.close - p["close"]) * p["sign"] / p["atr"]
            body = (b.close - b.open) * p["sign"] / p["atr"]
            close_location = ((b.close - b.low) / max(b.high - b.low, 1e-12)) if p["sign"] == 1 else (
                (b.high - b.close) / max(b.high - b.low, 1e-12)
            )
            # Two temporally distinct closed candles are required.
            acceptance = (
                response >= 0.35
                and body >= 0.15
                and close_location >= 0.58
                and (b.close - p["level"]) * p["sign"] > 0.10 * p["atr"]
            )
            if not acceptance:
                continue
            reference = b.close
            stop = p["extreme"] - p["sign"] * 0.15 * p["atr"]
            risk = (reference - stop) * p["sign"]
            room = (p["opposite"] - reference) * p["sign"]
            rr = room / risk if risk > 0 else -1.0
            if risk <= 0 or risk > 2.5 * p["atr"]:
                reason = "LATE_OR_INVALID_STOP"
            elif rr < 1.25 or room <= 0:
                reason = "INSUFFICIENT_STRUCTURAL_ROOM"
            else:
                decision_at = b.ts + BAR_MS
                regime = asof_regime(daily, close_times, decision_at)
                decisions.append(
                    Decision(
                        symbol=symbol,
                        attempt_at=p["attempt_at"],
                        decision_at=decision_at,
                        eligible_entry_at=decision_at,
                        side=p["side"],
                        daily_regime=regime,
                        boundary=p["level"],
                        failed_extreme=p["extreme"],
                        atr_at_attempt=p["atr"],
                        volume_ratio=p["volume_ratio"],
                        rejection_fraction=p["rejection_fraction"],
                        response_atr=response,
                        reference_entry=reference,
                        stop=stop,
                        opposite_structure=p["opposite"],
                        room_rr=rr,
                        evidence=(
                            "4H_BOUNDARY_FROM_PREVIOUS_12_BARS",
                            "4H_EFFORT_ON_HIGH_RELATIVE_VOLUME",
                            "4H_SWEEP_REJECTED_AT_CLOSE",
                            "SUBSEQUENT_4H_OPPOSING_RESPONSE",
                            "ORIGINAL_EXTREME_UNBROKEN",
                            "ROOM_TO_PREEXISTING_OPPOSITE_STRUCTURE",
                            "D1_CONTEXT_CLOSED_ONLY",
                        ),
                    )
                )
                attempts.append({**p["audit"], "status": "ACCEPTED", "reason": "CONFIRMED"})
                pending = None
                continue
            attempts.append({**p["audit"], "status": "REJECTED", "reason": reason})
            pending = None
            continue

        atr = prior_atr(bars, i)
        if atr <= 0:
            continue
        prior = bars[i - 12 : i]
        lower = min(x.low for x in prior)
        upper = max(x.high for x in prior)
        if b.low < lower - 0.15 * atr and b.high > upper + 0.15 * atr:
            continue
        vol_avg = sum(x.volume for x in bars[i - 20 : i]) / 20
        if vol_avg <= 0 or b.volume / vol_avg < 1.2:
            continue
        sweep_lower = b.low < lower - 0.15 * atr and b.close > lower
        sweep_upper = b.high > upper + 0.15 * atr and b.close < upper
        if sweep_lower == sweep_upper:
            continue
        side = "long" if sweep_lower else "short"
        sign = 1 if sweep_lower else -1
        level = lower if sweep_lower else upper
        extreme = b.low if sweep_lower else b.high
        rejection_fraction = (
            (b.close - b.low) / max(b.high - b.low, 1e-12)
            if sweep_lower
            else (b.high - b.close) / max(b.high - b.low, 1e-12)
        )
        if rejection_fraction < 0.65 or b.high - b.low < 0.8 * atr:
            continue
        history = bars[i - 48 : i]
        opposite = max(x.high for x in history) if sweep_lower else min(x.low for x in history)
        pending = {
            "index": i,
            "attempt_at": b.ts + BAR_MS,
            "side": side,
            "sign": sign,
            "level": level,
            "extreme": extreme,
            "atr": atr,
            "close": b.close,
            "opposite": opposite,
            "volume_ratio": b.volume / vol_avg,
            "rejection_fraction": rejection_fraction,
            "audit": {
                "symbol": symbol,
                "attempt_at": b.ts + BAR_MS,
                "side": side,
                "level": level,
                "volume_ratio": round(b.volume / vol_avg, 6),
                "rejection_fraction": round(rejection_fraction, 6),
            },
        }
    if pending is not None:
        attempts.append({**pending["audit"], "status": "PENDING", "reason": "FUTURE_NOT_AVAILABLE"})
    return decisions, attempts


def simulate(
    decisions: Sequence[Decision],
    bars: Sequence[Bar],
    *,
    max_bars: int = 12,
    base_cost: float = 0.002,
    stress_cost: float = 0.0035,
) -> list[Outcome]:
    """OHLC path diagnostic only: NOT mark/funding/fill or portfolio validation.

    Same 4h candle touches both stop and structure: conservatively STOP.
    SL gaps execute at worse opening price; targets never get optimistic gap credit.
    If future bars are incomplete, PnL=None (never substitute a synthetic exit).
    """
    by_open = {bar.ts: i for i, bar in enumerate(bars)}
    out: list[Outcome] = []
    for d in decisions:
        first = by_open.get(d.eligible_entry_at)
        if first is None or first + max_bars - 1 >= len(bars):
            out.append(Outcome(d.symbol, d.decision_at, d.side, None, None, None, None, "INCOMPLETE", None, None, None))
            continue
        entry = bars[first].open
        sign = 1 if d.side == "long" else -1
        risk = sign * (entry - d.stop)
        room = sign * (d.opposite_structure - entry)
        # Cancel an as-yet unfilled next-open market intention if open is beyond the precommitted structure.
        if risk <= 0 or room <= 0 or room / risk < 1.25:
            out.append(Outcome(d.symbol, d.decision_at, d.side, bars[first].ts, entry, None, None, "GAP_INVALIDATED", None, None, None))
            continue
        exit_at = None
        exit_price = None
        reason = "INCOMPLETE"
        for j in range(first, first + max_bars):
            b = bars[j]
            # Market open is assumed to fill first. On ENTRY bar, do not claim
            # the open is a subsequent stop/target trigger before fill.
            if j > first and sign * (b.open - d.stop) <= 0:
                exit_at, exit_price, reason = b.ts, b.open, "GAP_STOP"
                break
            stop_touch = b.low <= d.stop if sign == 1 else b.high >= d.stop
            target_touch = b.high >= d.opposite_structure if sign == 1 else b.low <= d.opposite_structure
            if stop_touch:
                exit_at, exit_price, reason = b.ts + BAR_MS, d.stop, (
                    "BOTH_STOP_FIRST" if target_touch else "STOP"
                )
                break
            if target_touch:
                exit_at, exit_price, reason = b.ts + BAR_MS, d.opposite_structure, "STRUCTURE"
                break
            if j == first + max_bars - 1:
                exit_at, exit_price, reason = b.ts + BAR_MS, b.close, "TIME"
        if exit_price is None:
            out.append(Outcome(d.symbol, d.decision_at, d.side, bars[first].ts, entry, None, None, "INCOMPLETE", None, None, None))
            continue
        gross = sign * (exit_price - entry) / entry * 100
        out.append(
            Outcome(
                symbol=d.symbol,
                decision_at=d.decision_at,
                side=d.side,
                entry_at=bars[first].ts,
                entry=entry,
                exit_at=exit_at,
                exit=exit_price,
                exit_reason=reason,
                gross_pct=gross,
                base_pct=gross - 100 * base_cost,
                stress_pct=gross - 100 * stress_cost,
            )
        )
    return out


def summary(decisions: Sequence[Decision], attempts: Sequence[dict], outcomes: Sequence[Outcome]) -> dict:
    resolved = [x for x in outcomes if x.stress_pct is not None]
    n = len(resolved)
    return {
        "status": "RESEARCH_ONLY_NOT_VERIFIED",
        "attempts": len(attempts),
        "accepted": len(decisions),
        "rejected": sum(x["status"] == "REJECTED" for x in attempts),
        "pending": sum(x["status"] == "PENDING" for x in attempts),
        "simulated": n,
        "incomplete_or_gap_cancelled": len(outcomes) - n,
        "wins_after_stress": sum(x.stress_pct > 0 for x in resolved),
        "mean_gross_pct_notional": sum(x.gross_pct for x in resolved) / n if n else None,
        "mean_base_pct_notional": sum(x.base_pct for x in resolved) / n if n else None,
        "mean_stress_pct_notional": sum(x.stress_pct for x in resolved) / n if n else None,
        "exit_reasons": {k: sum(x.exit_reason == k for x in outcomes) for k in sorted({x.exit_reason for x in outcomes})},
        "limitations": "not executable exchange PnL; no mark, signed funding, real slippage, margin, portfolio, or OOS",
    }
