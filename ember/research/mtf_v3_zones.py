"""Source-derived SMOKE 4H POI lifecycle, research-only and as-of safe.

Source receipts (SMOKE main, read 2026-11-01):
  structure.ts blob 7f8a18913d0674ab873964c43c18f32236fcf31a
  zones.ts blob f5ca1bd6a7757b8574d3cbd833abb9b0b077405d
  math.ts blob 125f8551a0fa27b093dd9e6ab94a146cd1607319

Geometry mirrors known SMOKE definitions: 3-left/3-right pivots,
BOS/CHoCH breaks, last opposite candle OB within prior ten bars,
3-bar 0.12*WilderATR FVG, swing 0.28*ATR envelopes.

Differences from SMOKE: zone life tracked event-by-event instead of a
snapshot after all future candles; dedup/score/departure-quality omitted
pending strict source-native parity. NEVER claim this exact SMOKE parity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from ember.research.mtf_v2_bars import H4, FlowBar


@dataclass(slots=True)
class Zone:
    zone_id: str
    kind: str
    family: str
    low: float
    high: float
    origin_at: int
    available_at: int
    parent_event: str
    broken_at: int | None = None
    retests: list[int] = field(default_factory=list)

    @property
    def midpoint(self) -> float:
        return (self.low + self.high) / 2

    def known_active(self, time: int) -> bool:
        return self.available_at <= time and (self.broken_at is None or time < self.broken_at)

    def to_dict(self) -> dict:
        return {
            "zone_id": self.zone_id,
            "kind": self.kind,
            "family": self.family,
            "low": self.low,
            "high": self.high,
            "origin_at": self.origin_at,
            "available_at": self.available_at,
            "parent_event": self.parent_event,
            "broken_at": self.broken_at,
            "retests": self.retests,
        }


def validate_four(bars: Sequence[FlowBar]) -> None:
    for i, b in enumerate(bars):
        if (b.ts % H4 or b.low <= 0 or b.high < max(b.open, b.close)
                or b.low > min(b.open, b.close) or b.high < b.low
                or b.volume < 0 or not 0 <= b.taker_buy <= b.volume * (1 + 1e-9)
                or (i and b.ts != bars[i-1].ts + H4)):
            raise ValueError(f"invalid/gapped 4H futures OHLCV index={i}")


def wilder_atr(bars: Sequence[FlowBar], length: int = 14) -> list[float]:
    values = []
    tr: list[float] = []
    atr = 0.0
    for i, b in enumerate(bars):
        prev = bars[i-1] if i > 0 else None
        tr.append(max(
            b.high - b.low,
            abs(b.high - prev.close) if prev else 0,
            abs(b.low - prev.close) if prev else 0,
        ))
        if i < length:
            atr = sum(tr) / len(tr)
        else:
            atr = (atr * (length - 1) + tr[-1]) / length
        values.append(atr)
    return values


def source_pivots(bars: Sequence[FlowBar], left: int = 3, right: int = 3) -> dict[int, list[tuple[str, float, int, str]]]:
    """Map CONFIRMATION bar index to (kind, price, origin_index, HH/HL/LH/LL)."""
    confirmed: dict[int, list[tuple[str, float, int, str]]] = {}
    previous_high = previous_low = None
    for i in range(left, len(bars) - right):
        bar = bars[i]
        window = bars[i-left:i+right+1]
        if all(bar.high > x.high for k,x in enumerate(window) if k != left):
            label = "HH" if previous_high is None or bar.high > previous_high else "LH"
            confirmed.setdefault(i+right, []).append(("high", bar.high, i, label))
            previous_high = bar.high
        if all(bar.low < x.low for k,x in enumerate(window) if k != left):
            label = "HL" if previous_low is not None and bar.low > previous_low else "LL"
            confirmed.setdefault(i+right, []).append(("low", bar.low, i, label))
            previous_low = bar.low
    return confirmed


def build_source_zones(bars: Sequence[FlowBar]) -> tuple[list[Zone], list[dict]]:
    """Reconstruct 4H zone births/deaths with strict available-at timestamps."""
    validate_four(bars)
    atr = wilder_atr(bars)
    pivots = source_pivots(bars)
    zones: list[Zone] = []
    events: list[dict] = []
    last_high: tuple[float,int] | None = None
    last_low: tuple[float,int] | None = None
    bias = "neutral"
    crossed_high = crossed_low = None
    touched_now: dict[str, bool] = {}
    known_ids: set[str] = set()

    def born(kind: str, family: str, low: float, high: float, origin_i: int,
             known_i: int, parent: str) -> None:
        if high <= low:
            return
        item_id = f"4h-{family}-{kind}-{bars[origin_i].ts}"
        # Source may produce repeated break events for one historical OB.
        if item_id in known_ids:
            return
        known_ids.add(item_id)
        z = Zone(item_id,kind,family,low,high,bars[origin_i].ts,bars[known_i].ts+H4,parent)
        zones.append(z)
        touched_now[item_id] = False
        events.append({"event":"ZONE_BORN","time":z.available_at,"zone_id":item_id,
                       "family":family,"kind":kind,"origin_at":z.origin_at,
                       "low":low,"high":high,"parent_event":parent})

    for i, bar in enumerate(bars):
        now = bar.ts + H4
        # Lifecycle applies ONLY to zones known at beginning of this bar.
        for z in zones:
            if z.available_at > bar.ts or z.broken_at is not None:
                continue
            hit = bar.low <= z.high and bar.high >= z.low
            if hit and not touched_now[z.zone_id]:
                z.retests.append(now)
                events.append({"event":"ZONE_RETEST","time":now,"zone_id":z.zone_id})
            touched_now[z.zone_id] = hit
            broken = bar.close < z.low if z.kind == "demand" else bar.close > z.high
            if broken:
                z.broken_at = now
                events.append({"event":"ZONE_BROKEN","time":now,"zone_id":z.zone_id})
        for kind, price, pivot_i, label in pivots.get(i, []):
            # Source swing band: ATR at ORIGIN, 0.28*ATR width, asymmetric.
            width = atr[pivot_i] * .28
            if kind == "low":
                born("demand","swing",price-width*.15,price+width,pivot_i,i,label)
                last_low = (price,pivot_i)
            else:
                born("supply","swing",price-width,price+width*.15,pivot_i,i,label)
                last_high = (price,pivot_i)

        # Source BOS/CHoCH: break of latest already confirmed swing at close.
        directions = []
        if last_high and bar.close > last_high[0] and crossed_high != last_high[1]:
            tag = "CHoCH" if bias == "down" else "BOS"
            directions.append(("long",tag,last_high[1]))
            crossed_high = last_high[1]
            bias = "up"
        if last_low and bar.close < last_low[0] and crossed_low != last_low[1]:
            tag = "CHoCH" if bias == "up" else "BOS"
            directions.append(("short",tag,last_low[1]))
            crossed_low = last_low[1]
            bias = "down"
        for side, tag, pivot_i in directions:
            events.append({"event":"STRUCTURE_BREAK","time":now,"side":side,"tag":tag,
                           "pivot_at":bars[pivot_i].ts,"break_at":bar.ts})
            origin_i = None
            for j in range(i-1,max(-1,i-11),-1):
                opposite = bars[j].close < bars[j].open if side == "long" else bars[j].close >= bars[j].open
                if opposite:
                    origin_i = j
                    break
            if origin_i is None:
                origin_i = i-1
            if origin_i >= 0:
                origin = bars[origin_i]
                if side == "long":
                    born("demand","order_block",origin.low,
                         max(origin.open,origin.close),origin_i,i,tag)
                else:
                    born("supply","order_block",min(origin.open,origin.close),
                         origin.high,origin_i,i,tag)

        # Source FVG geometry (current.low > previous2.high / opposite).
        if i >= 2:
            prev2 = bars[i-2]
            threshold = atr[i] * .12
            if bar.low > prev2.high and bar.low-prev2.high >= threshold:
                born("demand","fvg",prev2.high,bar.low,i,i,"THREE_CANDLE_GAP")
            elif bar.high < prev2.low and prev2.low-bar.high >= threshold:
                born("supply","fvg",bar.high,prev2.low,i,i,"THREE_CANDLE_GAP")
    return zones, events
