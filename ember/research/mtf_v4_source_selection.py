"""Independent Python selection-port of ORIGINAL SMOKE 4H zone visibility.

Only the source's snapshot generation windows and dedup-before-active order
are replicated. Native score/ranking parity and all entry rules are NOT
claimed. No changes to V3, main, PAPER, live exchange or parameter search.
"""
from __future__ import annotations

from collections.abc import Sequence

from ember.research.mtf_v2_bars import FlowBar
from ember.research.mtf_v3_zones import Zone, build_source_zones, source_pivots

FAMILIES = ("order_block", "swing", "fvg")


def source_visible_active_zones(bars: Sequence[FlowBar]) -> list[dict]:
    """Source windows -> ordered *including inactive* -> dedup -> active.

    Faithful to 4H buildZones() geometry-selection semantics except score
    which is deliberately not used in this presence/geometry-only audit.
    """
    zones, events = build_source_zones(bars)
    lookup = {z.zone_id: z for z in zones}

    def get(family: str, kind: str, origin_index: int) -> Zone | None:
        return lookup.get(f"4h-{family}-{kind}-{bars[origin_index].ts}")

    candidates: list[Zone] = []

    # Source: detectStructure(...).slice(-24), repeated BOS events may reuse OB.
    breaks = [x for x in events if x["event"] == "STRUCTURE_BREAK"]
    first_ts = bars[0].ts
    step = 4 * 3600000
    for event in breaks[-24:]:
        i = (event["break_at"] - first_ts) // step
        if i < 1 or i >= len(bars):
            continue
        side = event["side"]
        origin_i = None
        for j in range(i-1, max(-1, i-11), -1):
            bearish = bars[j].close < bars[j].open
            if (side == "long" and bearish) or (side == "short" and not bearish):
                origin_i = j
                break
        if origin_i is None:
            origin_i = i - 1
        kind = "demand" if side == "long" else "supply"
        zone = get("order_block", kind, origin_i)
        if zone:
            candidates.append(zone)

    # Source: findPivots(...).slice(-20), not all historical pivots.
    pivot_rows = []
    for confirmed, items in source_pivots(bars).items():
        for kind, _price, origin_i, _label in items:
            pivot_rows.append((origin_i, 0 if kind == "high" else 1, kind))
    pivot_rows.sort()
    for i, _order, kind in pivot_rows[-20:]:
        side = "demand" if kind == "low" else "supply"
        zone = get("swing", side, i)
        if zone:
            candidates.append(zone)

    # Source: last 180 FVG source bars, not last 180 successful gap births.
    for i in range(max(2, len(bars)-180), len(bars)):
        for kind in ("demand", "supply"):
            zone = get("fvg", kind, i)
            if zone:
                candidates.append(zone)

    # Source: .filter(... same-side midpoint within 0.06%) BEFORE sorting
    # and WITHOUT filtering inactive source levels first.
    chosen: list[Zone] = []
    for z in candidates:
        if any(
            other.kind == z.kind
            and abs(other.midpoint - z.midpoint) / max(z.midpoint, 1e-9) < .0006
            for other in chosen
        ):
            continue
        chosen.append(z)

    # Source zoneStillActive checks ALL subsequent closes after origin candle,
    # including those *prior to zone confirmation*.
    visible = []
    for z in chosen:
        broken_from_origin = any(
            (b.close < z.low if z.kind == "demand" else b.close > z.high)
            for b in bars if b.ts > z.origin_at
        )
        if not broken_from_origin:
            visible.append({
                "family": z.family, "kind": z.kind, "origin_at": z.origin_at,
                "low": z.low, "high": z.high, "active": True,
            })
    return visible
