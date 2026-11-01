"""RESET-07: frozen, causal, Decimal-only OHLCV management backtest.

No exchange clients, no tuning, no live or PAPER orders. All calculations use
source-pinned Binance UM candles, not synthetic test trades for verdicts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

from .data_contract import END, INTERVALS, START, SYMBOLS, audit_all, load_raw

STEP = INTERVALS["4h"]
FEE = D("0.0004")
SLIP = D("0.0002")
CAP = D("15")
SERIES_MAX_RISK = D("0.10")
ATR_BUFFER = D("1.75")
INITIAL_EQUITY = D("920")
KILL = D("736")
BACK_WINDOW = 120
RANGE_WINDOW = 180
YEAR_WINDOW = 2190
SCENARIOS = (("LONG", D("0.01")), ("LONG", D("0.02")),
             ("SHORT", D("0.01")), ("SHORT", D("0.02")))


class InvalidResearchData(ValueError):
    pass


@dataclass(frozen=True)
class Bar:
    ts: int
    o: D
    h: D
    low: D
    c: D


def bar_rows(rows: list[list]) -> list[Bar]:
    return [Bar(int(x[0]), D(x[1]), D(x[2]), D(x[3]), D(x[4])) for x in rows]


def _atr_series(bars: list[Bar]) -> list[D | None]:
    result: list[D | None] = [None] * len(bars)
    tr: list[D] = []
    for i, bar in enumerate(bars):
        prev = bars[i - 1].c if i else bar.c
        tr.append(max(bar.h - bar.low, abs(bar.h - prev), abs(bar.low - prev)))
        if i == 13:
            result[i] = sum(tr[-14:], D("0")) / D(14)
        elif i > 13:
            result[i] = (result[i - 1] * D(13) + tr[i]) / D(14)
    return result


def is_chop(
    current_atr_ratio: D, trailing_ratios: list[D],
    high_30: D, low_30: D, previous_close: D,
) -> bool:
    if len(trailing_ratios) != YEAR_WINDOW:
        raise InvalidResearchData("INSUFFICIENT_365D_ATR_REFERENCE")
    p20 = sorted(trailing_ratios)[(YEAR_WINDOW * 20 + 99) // 100 - 1]
    return (
        current_atr_ratio < p20
        and (high_30 - low_30) / previous_close < D("0.15")
    )


def _fractal_last_confirmed(
    bars: list[Bar], i: int, last_low: D | None, last_high: D | None,
) -> tuple[D | None, D | None]:
    pivot = i - 2
    if pivot >= 2:
        candidate = bars[pivot]
        others = [bars[k] for k in (pivot - 2, pivot - 1, pivot + 1, pivot + 2)]
        if candidate.low < min(b.low for b in others):
            last_low = candidate.low
        if candidate.h > max(b.h for b in others):
            last_high = candidate.h
    return last_low, last_high


def prepare_signals(bars: list[Bar], side: str):
    """No hindsight: confirmation of fractal at close pivot+2 only."""
    atrs = _atr_series(bars)
    last_low = last_high = None
    signals = {}
    timestamps = {b.ts for b in bars}
    for i, bar in enumerate(bars):
        last_low, last_high = _fractal_last_confirmed(
            bars, i, last_low, last_high
        )
        if i < YEAR_WINDOW + 14 or bar.ts < START or bar.ts >= END - STEP:
            continue
        if any(bars[k].ts + STEP != bars[k + 1].ts
               for k in range(i - YEAR_WINDOW, i)):
            continue
        if atrs[i] is None or bar.c == 0:
            continue
        prev = bars[i - BACK_WINDOW:i]
        breached = (
            bar.c > max(b.h for b in prev) if side == "LONG"
            else bar.c < min(b.low for b in prev)
        )
        if not breached:
            continue
        ratios = [atrs[k] / bars[k].c for k in range(i - YEAR_WINDOW + 1, i + 1)]
        if any(a is None for a in atrs[i - YEAR_WINDOW + 1:i + 1]):
            continue
        prior = bars[i - RANGE_WINDOW:i]
        if is_chop(
            atrs[i] / bar.c, ratios,
            max(b.h for b in prior), min(b.low for b in prior), bars[i - 1].c,
        ):
            signals[bar.ts + STEP] = {"reason": "SKIPPED_CHOP"}
            continue
        pivot = last_low if side == "LONG" else last_high
        if pivot is None:
            signals[bar.ts + STEP] = {"reason": "SKIPPED_NO_SWING"}
            continue
        stop = pivot - ATR_BUFFER * atrs[i] if side == "LONG" else (
            pivot + ATR_BUFFER * atrs[i]
        )
        signals[bar.ts + STEP] = {
            "stop": stop,
            "signal_time": bar.ts,
            "pivot": pivot,
        }
        if bar.ts + STEP not in timestamps:
            signals[bar.ts + STEP] = {"reason": "SKIPPED_GAP"}
    return signals


def _exit_fill(raw_price: D, sign: int) -> D:
    return raw_price * (D("1") - D(sign) * SLIP)


def _net_pnl(position: dict, exit_raw: D) -> D:
    fill = _exit_fill(exit_raw, position["sign"])
    return position["q"] * (
        D(position["sign"]) * (fill - position["entry"])
        - FEE * (position["entry"] + fill)
    )


def _be_price(entry: D, sign: int) -> D:
    if sign == 1:
        return (entry * (D("1") + FEE) / (D("1") - FEE)) / (D("1") - SLIP)
    return (entry * (D("1") - FEE) / (D("1") + FEE)) / (D("1") + SLIP)


def _risk_unit(entry: D, stop: D, sign: int) -> D:
    out = _exit_fill(stop, sign)
    return D(sign) * (entry - out) + FEE * (entry + out)


def size_ticket(
    *, equity: D, risk_fraction: D, entry: D, stop: D,
    sign: int, reserved: D, open_count: int,
) -> tuple[D, D] | None:
    if open_count >= 6 or reserved >= equity * SERIES_MAX_RISK:
        return None
    per_unit = _risk_unit(entry, stop, sign)
    if per_unit <= 0 or entry <= 0 or not (D(sign) * (entry - stop) > 0):
        return None
    budget = min(equity * risk_fraction, equity * SERIES_MAX_RISK - reserved)
    if budget <= 0:
        return None
    q = min(budget / per_unit, equity * CAP / entry)
    if q <= 0:
        return None
    return q, q * per_unit


def _year(t: int) -> int:
    return datetime.fromtimestamp(t / 1000, tz=timezone.utc).year


def run_one(
    bars_by_symbol: dict[str, list[Bar]], *,
    side: str, fraction: D,
) -> dict:
    sign = 1 if side == "LONG" else -1
    signals = {
        s: prepare_signals(bars_by_symbol[s], side) for s in SYMBOLS
    }
    by_time = {
        s: {b.ts: b for b in bars_by_symbol[s]} for s in SYMBOLS
    }
    times = sorted({t for values in by_time.values()
                    for t in values if START <= t < END})
    positions: dict[str, dict] = {}
    equity = INITIAL_EQUITY
    peak = INITIAL_EQUITY
    max_dd = D("0")
    kill_touch = False
    records: list[dict] = []
    skipped = []
    year_start = {2024: INITIAL_EQUITY}
    year_end = {}
    latest_close: dict[str, D] = {}
    recent_fractals: dict[str, tuple[D | None, D | None]] = {
        s: (None, None) for s in SYMBOLS
    }
    # Fractals are prepared causally on close in signal precomputation for
    # entries. For runner trail, derive only from currently CLOSED 4h candles.
    indices: dict[str, dict[int, int]] = {
        s: {b.ts: i for i, b in enumerate(bars_by_symbol[s])} for s in SYMBOLS
    }

    def finish(symbol: str, raw_exit: D, ts: int, cause: str) -> None:
        nonlocal equity
        position = positions.pop(symbol)
        pnl = _net_pnl(position, raw_exit)
        equity += pnl
        records.append({
            "symbol": symbol, "side": side, "open_ms": position["open_ms"],
            "close_ms": ts, "entry": format(position["entry"], "f"),
            "exit": format(_exit_fill(raw_exit, sign), "f"),
            "quantity": format(position["q"], "f"),
            "risk_usdt": format(position["risk"], "f"),
            "pnl_usdt": format(pnl, "f"),
            "net_R": format(pnl / position["risk"], "f"),
            "cause": cause, "runner_armed": position["armed"],
        })

    prev_year = 2024
    for ts in times:
        yr = _year(ts)
        if yr != prev_year:
            year_end[prev_year] = equity
            year_start[yr] = equity
            prev_year = yr
        # 1. Mark latest observed candle before event decisions.
        for symbol in SYMBOLS:
            bar = by_time[symbol].get(ts)
            if bar is not None:
                latest_close[symbol] = bar.c

        # 2. Stops at first available open (gap-through-stop).
        for symbol in sorted(list(positions)):
            bar = by_time[symbol].get(ts)
            if bar is None:
                continue
            p = positions[symbol]
            if (sign == 1 and bar.o <= p["stop"]) or (
                sign == -1 and bar.o >= p["stop"]
            ):
                finish(symbol, bar.o, ts, "GAP_STOP")

        # 3. Open next-candle tickets from previously CLOSED-bar signals.
        for symbol in SYMBOLS:
            bar = by_time[symbol].get(ts)
            ticket = signals[symbol].get(ts)
            if bar is None or ticket is None:
                continue
            if symbol in positions:
                skipped.append({"symbol": symbol, "ts": ts,
                                "reason": "SKIPPED_OPEN_SYMBOL"})
                continue
            if "reason" in ticket:
                skipped.append({"symbol": symbol, "ts": ts,
                                "reason": ticket["reason"]})
                continue
            entry = bar.o * (D("1") + D(sign) * SLIP)
            stop = ticket["stop"]
            if D(sign) * (entry - stop) <= 0:
                skipped.append({"symbol": symbol, "ts": ts,
                                "reason": "SKIPPED_STOP_GEOMETRY"})
                continue
            reserved = sum((x["risk"] for x in positions.values()), D("0"))
            proposal = size_ticket(
                equity=equity, risk_fraction=fraction, entry=entry, stop=stop,
                sign=sign, reserved=reserved, open_count=len(positions),
            )
            if proposal is None:
                skipped.append({"symbol": symbol, "ts": ts,
                                "reason": "SKIPPED_BUDGET"})
                continue
            q, risk = proposal
            unit = risk / q
            positions[symbol] = {
                "entry": entry, "stop": stop, "q": q,
                "risk": risk, "open_ms": ts, "armed": False,
                "tp": entry + D(sign) * D(2) * unit,
                "trigger": entry + D(sign) * unit,
                "activation_pending": False, "last_pivot": ticket["pivot"],
            }

        # 4. Causally check OHLC. Stop ALWAYS wins ambiguous same bar.
        for symbol in sorted(list(positions)):
            bar = by_time[symbol].get(ts)
            if bar is None:
                continue
            p = positions[symbol]
            if (sign == 1 and bar.low <= p["stop"]) or (
                sign == -1 and bar.h >= p["stop"]
            ):
                finish(symbol, p["stop"], ts, "STOP")
                continue
            if not p["armed"] and (
                (sign == 1 and bar.h >= p["tp"])
                or (sign == -1 and bar.low <= p["tp"])
            ):
                finish(symbol, p["tp"], ts, "TP_2R_BEFORE_RUNNER")
                continue

        # 5. Update pivots only at completed current bar; runner close trail
        # and +1R activation apply conservatively after OHLC resolution.
        for symbol in sorted(list(positions)):
            bar = by_time[symbol].get(ts)
            if bar is None:
                continue
            p = positions[symbol]
            i = indices[symbol][ts]
            last_low, last_high = recent_fractals[symbol]
            recent_fractals[symbol] = _fractal_last_confirmed(
                bars_by_symbol[symbol], i, last_low, last_high,
            )
            pivot = recent_fractals[symbol][0 if sign == 1 else 1]
            if p["armed"] and pivot is not None and (
                (sign == 1 and bar.c < pivot)
                or (sign == -1 and bar.c > pivot)
            ):
                finish(symbol, bar.c, ts, "RUNNER_4H_SWING_CLOSE")
                continue
            if not p["armed"] and (
                (sign == 1 and bar.h >= p["trigger"])
                or (sign == -1 and bar.low <= p["trigger"])
            ):
                p["armed"] = True
                be = _be_price(p["entry"], sign)
                # BE starts only next OHLC bar, never retrospectively.
                p["stop"] = max(p["stop"], be) if sign == 1 else min(p["stop"], be)

        mark = equity + sum(
            (_net_pnl(p, latest_close[s]) for s, p in positions.items()
             if s in latest_close),
            D("0"),
        )
        peak = max(peak, mark)
        max_dd = max(max_dd, (peak - mark) / peak)
        if mark <= KILL:
            kill_touch = True

    if times:
        last = times[-1]
        for symbol in sorted(list(positions)):
            bar = by_time[symbol].get(last)
            price = bar.c if bar is not None else latest_close[symbol]
            finish(symbol, price, last, "END_OF_WINDOW")
    year_end[prev_year] = equity

    wins = [D(x["pnl_usdt"]) for x in records if D(x["pnl_usdt"]) > 0]
    losses = [-D(x["pnl_usdt"]) for x in records if D(x["pnl_usdt"]) < 0]
    gross_p = sum(wins, D("0"))
    gross_l = sum(losses, D("0"))
    pf = gross_p / gross_l if gross_l else None
    records.sort(key=lambda r: (r["close_ms"], r["symbol"], r["open_ms"]))
    streak = worst = 0
    for row in records:
        if D(row["pnl_usdt"]) < 0:
            streak += 1
            worst = max(worst, streak)
        else:
            streak = 0
    positive = sorted(
        (r for r in records if D(r["pnl_usdt"]) > 0),
        key=lambda r: D(r["pnl_usdt"]), reverse=True,
    )
    annual = {
        str(y): format(
            (year_end.get(y, year_start.get(y, equity))
             / year_start.get(y, equity) - 1) * D("100"), "f",
        ) for y in (2024, 2025, 2026)
    }
    top5_ratio = sum(
        (D(r["pnl_usdt"]) for r in positive[:5]), D("0")
    ) / gross_p if gross_p > 0 else None
    top3_ratio = sum(
        (D(r["pnl_usdt"]) for r in positive[:3]), D("0")
    ) / gross_p if gross_p > 0 else None
    return {
        "side": side, "risk_fraction": format(fraction, "f"),
        "initial_equity_usdt": format(INITIAL_EQUITY, "f"),
        "final_equity_usdt": format(equity, "f"),
        "trades": len(records),
        "pf": None if pf is None else format(pf, "f"),
        "win_rate": format(D(len(wins)) / D(len(records)), "f") if records else None,
        "average_R": format(
            sum((D(r["net_R"]) for r in records), D("0")) / D(len(records)), "f"
        ) if records else None,
        "max_losing_streak": worst,
        "max_dd_fraction": format(max_dd, "f"),
        "kill_touch": kill_touch,
        "annual_return_percent": annual,
        "top5_share_of_gross_profit": (
            None if top5_ratio is None else format(top5_ratio, "f")
        ),
        "top3_share_of_gross_profit": (
            None if top3_ratio is None else format(top3_ratio, "f")
        ),
        "top5_trades": positive[:5],
        "gross_profit_usdt": format(gross_p, "f"),
        "gross_loss_usdt": format(gross_l, "f"),
        "skipped_budget": sum(x["reason"] == "SKIPPED_BUDGET" for x in skipped),
        "skipped_events": skipped,
        "closed_trades": records,
    }


def classify(results: list[dict]) -> str:
    if len(results) != 4:
        return "DATA_BLOCKED"
    for r in results:
        n = r["trades"]
        pf = D(r["pf"]) if r["pf"] is not None else D("0")
        top3 = D(r["top3_share_of_gross_profit"]) if r["top3_share_of_gross_profit"] else D("0")
        if pf <= 1 or n < 30 or r["kill_touch"] or top3 >= 1:
            return "LOTTERY"
    pass_all = True
    for r in results:
        pf = D(r["pf"])
        annual = r["annual_return_percent"]
        share = D(r["top5_share_of_gross_profit"]) if r["top5_share_of_gross_profit"] else D("1")
        if not (
            pf > D("1.3") and r["trades"] >= 60
            and D(r["max_dd_fraction"]) <= D("0.30") and share < D("0.60")
            and D(annual["2024"]) >= 0
            and D(annual["2025"]) + D(annual["2026"]) >= 0
        ):
            pass_all = False
    return "REPEATABLE" if pass_all else "GRAY"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", default="research/convex_runner/raw")
    parser.add_argument("--sha-manifest", required=True)
    parser.add_argument("--summary-path")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    manifest_raw = Path(args.sha_manifest).read_bytes()
    pins = json.loads(manifest_raw)
    audit = audit_all(Path(args.raw_root), pins)
    for symbol in SYMBOLS:
        for tf in ("4h", "1d"):
            if audit[symbol][tf]["gaps"]:
                raise InvalidResearchData("GAPPED_BAR_SERIES_" + symbol + "_" + tf)
            if audit[symbol][tf]["last_open_ms"] < END - INTERVALS[tf]:
                raise InvalidResearchData("MISSING_FINAL_BAR_" + symbol + "_" + tf)
    bars = {}
    for symbol in SYMBOLS:
        rows, _ = load_raw(Path(args.raw_root), symbol, "4h",
                           expected_sha=pins[symbol]["4h"])
        bars[symbol] = bar_rows(rows)
    scenarios = [run_one(bars, side=side, fraction=fraction)
                 for side, fraction in SCENARIOS]
    sol_rows, _ = load_raw(Path(args.raw_root), "SOLUSDT", "1d",
                           expected_sha=pins["SOLUSDT"]["1d"])
    sol_eval = [row for row in sol_rows if START <= row[0] < END]
    sol_hold = (D(sol_eval[-1][4]) / D(sol_eval[0][1]) - 1) * 100
    result = {
        "model": "RESET07_CONVEX_FROZEN", "market": "BINANCE_USDT_M_FUTURES",
        "window": [START, END], "input_sha_manifest_sha256":
            hashlib.sha256(manifest_raw).hexdigest(),
        "funding": "NOT_INCLUDED_AND_NOT_YET_VERIFIED",
        "alpha_permission": False, "live_allowed": False,
        "buyhold_sol_return_percent": format(sol_hold, "f"),
        "classification": classify(scenarios),
        "owner_trade_comparison": "PUMP excluded from universe; FIL excluded; owner PnL sizes not normalized to same equity/risk, comparison is not valid",
        "scenarios": scenarios,
    }
    encoded = json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    if args.summary_path:
        Path(args.summary_path).write_text(encoded + "\n", encoding="utf-8")
    if args.stdout:
        compact = {key: value for key, value in result.items() if key != "scenarios"}
        compact["scenarios"] = [
            {k: v for k, v in s.items() if k not in ("closed_trades", "skipped_events")}
            for s in scenarios
        ]
        print("RESET07_RESULT_JSON=" + json.dumps(compact, sort_keys=True, separators=(",", ":")))
    print("RESET07_FINAL_VERDICT=" + result["classification"])


if __name__ == "__main__":
    main()
