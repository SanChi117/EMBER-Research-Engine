"""V3 research: causal 4H zone birth, lifecycle and bar validation."""
from __future__ import annotations

from dataclasses import replace

import pytest

from ember.research.mtf_v2_bars import H4, FlowBar
from ember.research.mtf_v3_zones import (
    build_source_zones,
    source_pivots,
    validate_four,
    wilder_atr,
)


def four_bars(n: int = 155) -> list[FlowBar]:
    bars = [FlowBar(i*H4,100,101,99,100,100,50) for i in range(n)]
    bars[10] = FlowBar(10*H4,102,104,97,100,100,50)
    bars[20] = FlowBar(20*H4,103,105,102,104,180,95)
    return bars


def test_swing_delayed_until_three_full_right_bars() -> None:
    bars = four_bars()
    pivots = source_pivots(bars)
    assert any(origin == 10 and kind == "low" for kind,price,origin,label in pivots[13])
    zones,events = build_source_zones(bars)
    found = [z for z in zones if z.family == "swing" and z.origin_at == 10*H4 and z.kind == "demand"]
    assert len(found) == 1
    z = found[0]
    assert z.available_at == 14*H4
    assert not z.known_active(13*H4)
    assert z.known_active(14*H4)
    assert any(e["event"] == "ZONE_BORN" and e["time"] == z.available_at for e in events)


def test_fvg_known_only_after_closing_third_four_hour_candle() -> None:
    zones,_ = build_source_zones(four_bars())
    found = [z for z in zones if z.family == "fvg" and z.origin_at == 20*H4]
    assert len(found) == 1
    z = found[0]
    assert (z.low,z.high,z.available_at) == (101,102,21*H4)
    assert not z.known_active(20*H4)


def test_mutating_future_does_not_rewrite_past_zone_status() -> None:
    past = four_bars()[:80]
    first,_ = build_source_zones(past)
    extended = four_bars()
    for i in range(80,len(extended)):
        extended[i] = FlowBar(i*H4,100,300,1,150,1000,900)
    second,_ = build_source_zones(extended)
    cutoff = 80*H4
    a = {(z.zone_id,z.available_at,z.known_active(cutoff)) for z in first if z.available_at <= cutoff}
    b = {(z.zone_id,z.available_at,z.known_active(cutoff)) for z in second if z.available_at <= cutoff}
    assert a == b


def test_source_atr_and_missing_bar_guard() -> None:
    bars=four_bars()
    atr=wilder_atr(bars)
    assert atr[0] == pytest.approx(2)
    assert atr[1] == pytest.approx(2)
    bars[10]=replace(bars[10],ts=bars[9].ts)
    with pytest.raises(ValueError,match="gapped"):
        validate_four(bars)
