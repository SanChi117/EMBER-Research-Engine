"""MTF Initiative V2: strict UTC closed-bar data and 4H confirmed structures.

Research-only; no trades, exchange orders, or schedulers.
"""
from __future__ import annotations

import csv
from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

M15 = 900_000
H1 = 4 * M15
H4 = 16 * M15
D1 = 96 * M15


@dataclass(frozen=True)
class FlowBar:
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    taker_buy: float

    def as_v1(self):
        from ember.research.initiative_transition import Bar
        return Bar(self.ts, self.open, self.high, self.low, self.close, self.volume)


@dataclass(frozen=True)
class Context:
    asof: int  # Latest fully CLOSED 4H bar end time.
    pivot_low: float | None
    pivot_high: float | None
    pivot_low_at: int | None
    pivot_high_at: int | None
    atr4: float | None
    daily_regime: str


def read_futures_15m(path: str | Path) -> list[FlowBar]:
    with open(path, encoding="utf-8", newline="") as handle:
        result = [
            FlowBar(
                int(r["time_ms"]), float(r["open"]), float(r["high"]),
                float(r["low"]), float(r["close"]), float(r["volume"]),
                float(r["taker_buy_base"]),
            )
            for r in csv.DictReader(handle)
        ]
    validate(result)
    return result


def validate(rows: Sequence[FlowBar]) -> None:
    for i, bar in enumerate(rows):
        if (
            bar.ts % M15
            or not (0 < bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high)
            or bar.volume < 0
            or not 0 <= bar.taker_buy <= bar.volume * (1 + 1e-9)
            or (i and bar.ts != rows[i - 1].ts + M15)
        ):
            raise ValueError(f"invalid/missing/unordered 15m futures bar at {i}")


def aggregate(rows: Sequence[FlowBar], period_ms: int) -> list[FlowBar]:
    if period_ms % M15 or period_ms < M15:
        raise ValueError("invalid aggregation")
    count = period_ms // M15
    out: list[FlowBar] = []
    for i, first in enumerate(rows):
        if first.ts % period_ms != 0 or i + count > len(rows):
            continue
        part = rows[i:i + count]
        if part[-1].ts + M15 != first.ts + period_ms:
            continue
        out.append(
            FlowBar(
                first.ts, first.open, max(x.high for x in part),
                min(x.low for x in part), part[-1].close,
                sum(x.volume for x in part), sum(x.taker_buy for x in part),
            )
        )
    return out


def atr_prior(rows: Sequence[FlowBar], i: int, n: int = 14) -> float:
    if i < n + 1:
        raise ValueError("insufficient prior bars")
    return sum(
        max(
            rows[j].high - rows[j].low,
            abs(rows[j].high - rows[j - 1].close),
            abs(rows[j].low - rows[j - 1].close),
        )
        for j in range(i - n, i)
    ) / n


def confirmed_pivots(rows: Sequence[FlowBar]) -> tuple[list[tuple[int, float, int]], list[tuple[int, float, int]]]:
    """Time the pivot is KNOWN, price, origin time; 2 bars right-verified."""
    lows, highs = [], []
    for i in range(2, len(rows) - 2):
        bar = rows[i]
        window = rows[i - 2:i + 3]
        available = rows[i + 2].ts + H4
        if all(bar.low < other.low for j, other in enumerate(window) if j != 2):
            lows.append((available, bar.low, bar.ts))
        if all(bar.high > other.high for j, other in enumerate(window) if j != 2):
            highs.append((available, bar.high, bar.ts))
    return lows, highs


def daily_regime(days: Sequence[FlowBar], asof: int) -> str:
    known = [bar for bar in days if bar.ts + D1 <= asof]
    if len(known) < 21:
        return "UNKNOWN"
    ref = sum(x.close for x in known[-21:-1]) / 20
    last = known[-1].close
    return "UP" if last > ref * 1.01 else "DOWN" if last < ref * .99 else "RANGE"


def contexts(four: Sequence[FlowBar], days: Sequence[FlowBar]) -> tuple[list[Context], list[int]]:
    lows, highs = confirmed_pivots(four)
    ltimes, htimes = [x[0] for x in lows], [x[0] for x in highs]
    result: list[Context] = []
    for i, bar in enumerate(four):
        asof = bar.ts + H4
        li, hi = bisect_right(ltimes, asof) - 1, bisect_right(htimes, asof) - 1
        lv = lows[li] if li >= 0 else None
        hv = highs[hi] if hi >= 0 else None
        low = lv[1] if lv and bar.close > lv[1] else None
        high = hv[1] if hv and bar.close < hv[1] else None
        atr = atr_prior(four, i + 1) if i >= 14 else None
        result.append(
            Context(
                asof, low, high,
                lv[2] if low is not None and lv else None,
                hv[2] if high is not None and hv else None,
                atr, daily_regime(days, asof),
            )
        )
    return result, [x.asof for x in result]
