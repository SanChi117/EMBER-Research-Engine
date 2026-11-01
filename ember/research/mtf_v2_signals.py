"""Closed-time MTF transfer detector. Research-only; never submits orders."""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import asdict, dataclass
from typing import Sequence

from ember.research.mtf_v2_bars import (
    H1, H4, M15, FlowBar, aggregate, contexts, validate,
)


@dataclass(frozen=True)
class Entry:
    symbol: str
    side: str
    model: str
    parent_4h_close: int
    parent_pivot_at: int
    attempt_1h_close: int
    confirm_1h_close: int
    trigger_15m_close: int
    eligible_entry_at: int
    daily_regime: str
    h4_boundary: float
    h4_opposite_pivot: float
    attempt_extreme: float
    attempt_taker_fraction: float
    confirm_taker_fraction: float
    trigger_taker_fraction: float
    effort_volume_ratio: float
    response_atr4: float
    reference_entry: float
    stop: float
    target: float
    structural_rr: float
    evidence: tuple[str, ...]

    def as_dict(self) -> dict:
        record = asdict(self)
        record["evidence"] = list(self.evidence)
        return record


def detect(symbol: str, source: Sequence[FlowBar], *, require_flow: bool = True) -> tuple[list[Entry], list[dict]]:
    """D1 context / 4H structural pivot / 1H transfer / 15m execution.

    Failed seller/buyer effort:
      1H sweep a previously confirmed 4H pivot by .10 ATR4H; close back
      inside it; >=1.15x trailing 1H volume; aggression taker fraction
      <=.48 for failed sell, >=.52 for failed buy.
    H1 opposite result: later CLOSED hourly bar displacement >=.15 ATR4H,
      directional candle body >=.08 ATR4H and taker-side reversal.
    M15 trigger: close beyond previous six 15m highs/lows on >=1.10x volume,
      with buyer/seller taker alignment.
    Structural SL: beyond initial failed extreme by .15 ATR4H;
    structural TP: opposite previously confirmed 4H pivot.
    Flow-disabled run is a controlled ablation, NOT an optimized strategy.
    """
    validate(source)
    one, four = aggregate(source, H1), aggregate(source, H4)
    from ember.research.mtf_v2_bars import D1
    parents, times = contexts(four, aggregate(source, D1))
    one_by_close = {bar.ts + H1: i for i, bar in enumerate(one)}
    entries: list[Entry] = []
    events: list[dict] = []
    state: dict | None = None
    last_parent_attempt: dict[tuple[str, int], int] = {}

    for k in range(130, len(source)):
        bar = source[k]
        now = bar.ts + M15
        if state is not None and state["stage"] == "AWAIT_H1":
            if now in one_by_close:
                hour = one[one_by_close[now]]
                age = (now - state["attempt"]) // H1
                sign = state["sign"]
                broke = hour.low <= state["extreme"] if sign == 1 else hour.high >= state["extreme"]
                if broke or age > 3:
                    events.append({"event": "REJECTED", "time": now, "symbol": symbol, "side": state["side"], "attempt": state["attempt"], "reason": "EXTREME_REBROKEN" if broke else "H1_TIMEOUT"})
                    state = None
                elif age >= 1:
                    fraction = hour.taker_buy / hour.volume if hour.volume else .5
                    progress = sign * (hour.close - state["attempt_price"]) / state["atr"]
                    body = sign * (hour.close - hour.open) / state["atr"]
                    flow = not require_flow or (fraction >= .52 if sign == 1 else fraction <= .48)
                    if progress >= .15 and body >= .08 and flow and sign * (hour.close - state["boundary"]) >= .05 * state["atr"]:
                        state["stage"] = "AWAIT_M15"
                        state["confirm"] = now
                        state["confirm_flow"] = fraction
                        state["response"] = progress
                        events.append({"event": "H1_TRANSFER", "time": now, "symbol": symbol, "side": state["side"], "attempt": state["attempt"], "response_atr4": progress})
            continue

        if state is not None and state["stage"] == "AWAIT_M15":
            sign = state["sign"]
            broke = bar.low <= state["extreme"] if sign == 1 else bar.high >= state["extreme"]
            if broke or now - state["confirm"] > 8 * M15:
                events.append({"event": "REJECTED", "time": now, "symbol": symbol, "side": state["side"], "attempt": state["attempt"], "reason": "EXTREME_REBROKEN" if broke else "M15_TIMEOUT"})
                state = None
                continue
            previous = source[k - 6:k]
            breakout = max(x.high for x in previous) if sign == 1 else min(x.low for x in previous)
            fraction = bar.taker_buy / bar.volume if bar.volume else .5
            flow = not require_flow or (fraction >= .52 if sign == 1 else fraction <= .48)
            avg = sum(x.volume for x in source[k - 20:k]) / 20
            if sign * (bar.close - breakout) > 0 and flow and bar.volume >= 1.10 * avg:
                stop = state["extreme"] - sign * .15 * state["atr"]
                target = state["target"]
                risk = sign * (bar.close - stop)
                room = sign * (target - bar.close)
                rr = room / risk if risk > 0 else -1
                if risk > 0 and risk <= 2.5 * state["atr"] and rr >= 1.25:
                    entries.append(
                        Entry(
                            symbol, state["side"], "MTF_V2_FLOW" if require_flow else "MTF_V2_PRICE_ONLY",
                            state["parent_close"], state["pivot_at"],
                            state["attempt"], state["confirm"], now, now,
                            state["daily"], state["boundary"], target,
                            state["extreme"], state["attempt_flow"], state["confirm_flow"], fraction,
                            state["volume_ratio"], state["response"],
                            bar.close, stop, target, rr,
                            (
                                "H4_PIVOT_CONFIRMED_BEFORE_H1_CONTEST",
                                "H1_AGGRESSOR_FAILURE_AT_H4_LEVEL",
                                "OPPOSITE_H1_RESPONSE_AFTER_ORIGINAL_H1_CLOSE",
                                "M15_CLOSE_BREAKS_SIX_PRIOR_BARS",
                                "H4_PARENT_STOP_TARGET",
                                "D1_FULL_DAYS_AS_OF",
                                "TAKER_FLOW_ALIGNED" if require_flow else "PRICE_ONLY_CONTROL",
                            ),
                        )
                    )
                    events.append({"event": "ENTRY_READY", "time": now, "symbol": symbol, "side": state["side"], "attempt": state["attempt"], "rr": rr})
                else:
                    events.append({"event": "REJECTED", "time": now, "symbol": symbol, "side": state["side"], "attempt": state["attempt"], "reason": "H4_STRUCTURAL_GEOMETRY", "rr": rr})
                state = None
            continue

        if now not in one_by_close:
            continue
        j = one_by_close[now]
        if j < 21:
            continue
        hour = one[j]
        pi = bisect_right(times, hour.ts) - 1
        if pi < 0:
            continue
        parent = parents[pi]
        if parent.atr4 is None or parent.atr4 <= 0:
            continue
        average = sum(x.volume for x in one[j - 20:j]) / 20
        if average <= 0 or hour.volume / average < 1.15:
            continue
        fraction = hour.taker_buy / hour.volume if hour.volume else .5
        possibilities = [
            ("long", +1, parent.pivot_low, parent.pivot_low_at, parent.pivot_high, hour.low),
            ("short", -1, parent.pivot_high, parent.pivot_high_at, parent.pivot_low, hour.high),
        ]
        matches = []
        for side, sign, level, pivot_at, target, extreme in possibilities:
            if level is None or pivot_at is None or target is None:
                continue
            penetration = level - hour.low if sign == 1 else hour.high - level
            reclaim = sign * (hour.close - level)
            pressure = not require_flow or (fraction <= .48 if sign == 1 else fraction >= .52)
            if penetration > .10 * parent.atr4 and reclaim > 0 and pressure:
                matches.append((side, sign, level, pivot_at, target, extreme))
        if len(matches) != 1:
            continue
        side, sign, level, pivot_at, target, extreme = matches[0]
        key = (side, pivot_at)
        if now - last_parent_attempt.get(key, -10**18) < 2 * H4:
            continue
        last_parent_attempt[key] = now
        state = {
            "stage": "AWAIT_H1", "side": side, "sign": sign,
            "boundary": level, "extreme": extreme, "target": target,
            "pivot_at": pivot_at, "atr": parent.atr4, "parent_close": parent.asof,
            "daily": parent.daily_regime, "attempt": now,
            "attempt_price": hour.close, "attempt_flow": fraction,
            "volume_ratio": hour.volume / average,
        }
        events.append(
            {"event": "H1_CONTEST", "time": now, "symbol": symbol, "side": side,
             "attempt": now, "parent_close": parent.asof, "pivot_at": pivot_at,
             "boundary": level, "taker_buy_fraction": fraction,
             "effort_volume_ratio": hour.volume / average}
        )
    if state is not None:
        events.append({"event": "CENSORED", "time": source[-1].ts + M15, "symbol": symbol, "side": state["side"], "attempt": state["attempt"]})
    return entries, events
