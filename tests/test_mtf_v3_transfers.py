"""V3 structural 4H SL/TP transfer decision timing and conservative OHLC path."""
from __future__ import annotations

from dataclasses import replace

from ember.research.mtf_v2_bars import H1, FlowBar
from scripts.run_mtf_v3_transfers import replay


def example(side: str = "long"):
    bars=[FlowBar(i*H1,100,101,99,100,100,50) for i in range(50)]
    sign=1 if side=="long" else -1
    bars[10]=FlowBar(10*H1,100,101.5,98.5,100.5 if sign==1 else 99.5,100,30 if sign==1 else 70)
    bars[11]=FlowBar(11*H1,100.5 if sign==1 else 99.5,103 if sign==1 else 101,99 if sign==1 else 97,101.5 if sign==1 else 98.5,100,75 if sign==1 else 25)
    bars[12]=FlowBar(12*H1,101.5 if sign==1 else 98.5,103 if sign==1 else 100,99 if sign==1 else 97,101.5 if sign==1 else 98.5,100,60 if sign==1 else 40)
    bars[13]=FlowBar(13*H1,101 if sign==1 else 99,108 if sign==1 else 101,99.3 if sign==1 else 93,105 if sign==1 else 95,100,70 if sign==1 else 30)
    event={
        "symbol":"TESTUSDT","event_id":"test-1","event_at":11*H1,
        "side":side,"zone_family":"swing","zone_id":"level-1",
        "indicative_stop":98.5 if sign==1 else 101.5,
        "opposite_structural_target":107 if sign==1 else 94,
        "effort_volume_ratio":1.5,"aggressor_pressure":.2,
        "penetration_atr4":.3,"reclaimed_zone_at_close":True,
        "contact_close":100.5 if sign==1 else 99.5,
        "h4_atr_asof":2,
    }
    zone={"symbol":"TESTUSDT","zone_id":"level-1","broken_at":None,"expires_at":None}
    return event,{"TESTUSDT":{"1h":bars}},[zone]


def test_long_is_decided_only_after_future_closed_hour() -> None:
    e,s,z=example("long")
    t=replay([e],s,z,require_flow=True)
    assert len(t)==1
    assert t[0]["status"]=="SIMULATED"
    assert t[0]["confirmed_at"]==12*H1
    assert t[0]["entry_at"]>=t[0]["confirmed_at"]
    assert t[0]["entry"]==101.5
    assert t[0]["exit_reason"]=="4H_OPPOSITE_ZONE"
    assert t[0]["stress_proxy_nominal_pct"]>0


def test_short_is_symmetric() -> None:
    e,s,z=example("short")
    t=replay([e],s,z,require_flow=True)
    assert len(t)==1
    assert t[0]["status"]=="SIMULATED"
    assert t[0]["exit_reason"]=="4H_OPPOSITE_ZONE"


def test_future_price_does_not_change_preexisting_transfer_time() -> None:
    e,s,z=example()
    earlier=replay([e],s,z,require_flow=True)[0]
    bar=s["TESTUSDT"]["1h"][14]
    s["TESTUSDT"]["1h"][14]=replace(bar,high=300,close=300)
    later=replay([e],s,z,require_flow=True)[0]
    assert earlier["confirmed_at"]==later["confirmed_at"]


def test_parent_zone_broken_before_transfer_cancels() -> None:
    e,s,z=example()
    z[0]["broken_at"]=12*H1
    result=replay([e],s,z,require_flow=True)[0]
    assert result["status"]=="4H_ZONE_NOT_ACTIVE_AT_CONFIRM"
