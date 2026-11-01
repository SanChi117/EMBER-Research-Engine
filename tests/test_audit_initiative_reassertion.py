"""Reassertion research invariants: pre-known clock, symmetric attempt, stop-first."""
from copy import deepcopy

import pytest

from ember.research.mtf_v2_bars import H1, FlowBar
from scripts.audit_initiative_reassertion import (
    classify_reassertion,
    delayed_case,
    evaluate_path,
)


def bar(i, *, op=100, high=101, low=99, close=100):
    return FlowBar(i*H1, op, high, low, close, 1000, 500)


def series(n=100):
    return [bar(i) for i in range(n)]


def v3_original():
    return {
        "symbol":"BTCUSDT","event_id":"E","research_variant":"PRICE_ONLY",
        "status":"SIMULATED","side":"long","zone_family":"swing",
        "contact_at":39*H1,"confirmed_at":41*H1,
        "entry_at":41*H1,"exit_at":50*H1,
        "entry":100,"stop":96,"target":108,
        "stress_proxy_nominal_pct":-1.0,
    }


def event(reference=99.5):
    return {
        "event_at":39*H1,"available_at":36*H1,
        "h4_close_available_at":36*H1,
        "contact_close":reference,
    }


def idx(bars):
    return {b.ts:i for i,b in enumerate(bars)}


def test_reassertion_long_short_mirror_and_no_attempt():
    b=[bar(0,close=100,low=99),bar(1,close=100,low=99),
       bar(2,close=100,low=99)]
    assert classify_reassertion(b,side="long",contact_close=99.5) == (
        "OLD_SIDE_REASSERTION_FAILED"
    )
    assert classify_reassertion(b,side="long",contact_close=98.5) == (
        "NO_REASSERTION"
    )
    assert classify_reassertion(b,side="short",contact_close=100.5) == (
        "OLD_SIDE_REASSERTION_FAILED"
    )
    assert classify_reassertion(b,side="short",contact_close=101.5) == (
        "NO_REASSERTION"
    )
    with pytest.raises(ValueError,match="exactly"):
        classify_reassertion(b[:2],side="long",contact_close=99)


def test_retest_which_loses_control_later_in_window_not_defended():
    b=[bar(1),bar(2,op=100,high=101,low=97,close=98),
       bar(3,op=98,high=100,low=97,close=98)]
    assert classify_reassertion(b,side="long",contact_close=99.5)==(
        "OLD_SIDE_REASSERTION_NOT_REJECTED"
    )


def test_decision_clock_and_no_future_label_leakage():
    bars=series()
    original=v3_original()
    out=delayed_case(original,event(),bars,idx(bars))
    assert out["decision_at"]==44*H1
    assert out["entry_at"]==44*H1
    assert out["state"]=="OLD_SIDE_REASSERTION_FAILED"
    assert out["status"]=="SIMULATED"
    # The original future outcome is a LABEL, never part of recognition.
    altered=deepcopy(original)
    altered["stress_proxy_nominal_pct"]=42
    altered["exit_at"]=99*H1
    x=delayed_case(altered,event(),bars,idx(bars))
    for key in ("state","decision_at","entry_at","entry","rr_asof",
                "stress_proxy_nominal_pct","exit_reason"):
        assert x[key]==out[key]
    # Altering a future bar can affect OUTCOME but not as-of classification.
    future=deepcopy(bars)
    future[50]=bar(50,op=100,high=125,low=99,close=110)
    y=delayed_case(original,event(),future,idx(future))
    for key in ("state","decision_at","entry_at","entry","rr_asof"):
        assert y[key]==out[key]
    assert y["exit_reason"]=="4H_OPPOSITE_ZONE"


def test_survival_applies_before_classification_for_both_groups():
    bars=series()
    bars[42]=bar(42,op=100,high=101,low=94,close=100)
    out=delayed_case(v3_original(),event(),bars,idx(bars))
    assert out["status"]=="PRECHECK_STOP"
    assert out["state"]=="UNCLASSIFIED"
    no_attempt=delayed_case(v3_original(),event(98.5),bars,idx(bars))
    assert no_attempt["status"]=="PRECHECK_STOP"


def test_tp_reached_before_fixed_checkpoint_not_tradable():
    bars=series()
    bars[43]=bar(43,op=100,high=109,low=99,close=100)
    out=delayed_case(v3_original(),event(),bars,idx(bars))
    assert out["status"]=="PRECHECK_TARGET"


def test_both_stop_first_path_and_delayed_next_open():
    bars=series()
    bars[44]=bar(44,op=100,high=110,low=95,close=100)
    out=delayed_case(v3_original(),event(),bars,idx(bars))
    assert out["status"]=="SIMULATED"
    assert out["exit_reason"]=="BOTH_STOP_FIRST"
    assert out["stress_proxy_nominal_pct"]<0


def test_cannot_use_future_4h_parent_or_missing_confirmation():
    bars=series()
    bad=event()
    bad["available_at"]=45*H1
    with pytest.raises(ValueError,match="future"):
        delayed_case(v3_original(),bad,bars,idx(bars))
    x=v3_original()
    x["confirmed_at"]=105*H1
    with pytest.raises(ValueError,match="confirmation"):
        delayed_case(x,event(),bars,idx(bars))


def test_explicit_future_censor():
    bars=series(62)
    original=v3_original()
    original["confirmed_at"]=40*H1
    out=delayed_case(original,event(),bars,idx(bars))
    assert out["status"]=="CENSORED_AT_FIXED_CHECKPOINT"


def test_standalone_path_gaps():
    bars=series()
    bars[46]=bar(46,op=95,high=99,low=94,close=97)
    out=evaluate_path(bars,entry_idx=44,sign=1,entry=100,stop=96,target=108)
    assert out["exit_reason"]=="GAP_STOP"
