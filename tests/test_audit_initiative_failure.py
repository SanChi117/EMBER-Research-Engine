"""V3 initiative failure: no-future and diagnostic-only invariants."""
import pytest

from ember.research.mtf_v2_bars import H1, FlowBar
from scripts.audit_initiative_failure import (
    contrast,
    enrich,
    prior_hour_true_range,
    split_chronologically,
    stats,
)


def fixture_bars(n=140):
    return [
        FlowBar(i * H1, 100, 102, 98, 100, 1000, 500)
        for i in range(n)
    ]


def test_range_uses_only_bars_closed_before_entry() -> None:
    bars = fixture_bars()
    assert prior_hour_true_range(bars, 40*H1) == 4
    bars[40] = FlowBar(40*H1, 100, 150, 20, 120, 1000, 500)
    assert prior_hour_true_range(bars, 40*H1) == 4
    bars[39] = FlowBar(39*H1, 100, 104, 98, 100, 1000, 500)
    assert prior_hour_true_range(bars, 40*H1) == 4


def test_missing_bar_prevents_feature_computation() -> None:
    with pytest.raises(ValueError, match="warmup"):
        prior_hour_true_range(fixture_bars(), 10*H1)


def fake_contact():
    return {
        "event_id":"X",
        "available_at": 36*H1,
        "event_at":37*H1,
        "h4_close_available_at":36*H1,
        "h4_atr_asof":8,
        "zone_prior_retests":0,"zone_4h_age":3,
        "d1_bias_asof":"UP","side":"long",
        "close_position":.8,"effort_volume_ratio":1.8,
        "aggressor_pressure":.05,"penetration_atr4":.2,
    }


def fake_trade():
    return {
        "event_id":"X","status":"SIMULATED","symbol":"BTCUSDT",
        "side":"long","contact_at":37*H1,"confirmed_at":38*H1,
        "entry_at":39*H1,"exit_at":43*H1,
        "entry":101,"stop":97,"zone_family":"swing",
        "preopen_rr":2.0,
        "stress_proxy_nominal_pct":-.7,
        "gross_nominal_pct":-.35,
        "exit_reason":"STOP",
    }


def test_features_asof_and_future_exit_does_not_change_them() -> None:
    trade = fake_trade()
    original = enrich([trade],{"X":fake_contact()},
                      {"BTCUSDT":{"1h":fixture_bars()}})[0]
    assert original["stop_per_prior_1h_true_range"] == 1
    assert original["stop_per_4h_atr"] == .5
    trade["exit_reason"] = "4H_OPPOSITE_ZONE"
    trade["stress_proxy_nominal_pct"] = 5
    changed = enrich([trade],{"X":fake_contact()},
                     {"BTCUSDT":{"1h":fixture_bars()}})[0]
    for field in ("stop_per_prior_1h_true_range","stop_per_4h_atr",
                  "close_position","effort_volume_ratio","aggressor_pressure"):
        assert original[field] == changed[field]


def test_future_confirmation_cannot_be_used_at_earlier_entry() -> None:
    trade = fake_trade()
    trade["confirmed_at"] = trade["entry_at"] + H1
    with pytest.raises(ValueError, match="ordering"):
        enrich([trade],{"X":fake_contact()},
               {"BTCUSDT":{"1h":fixture_bars()}})


def test_no_claim_of_independent_trade_count_from_repeated_daily_samples() -> None:
    x=[{"entry_at":day*86_400_000,"outcome_nominal_pct":((-1)**day)*.5,
        "exit_reason":"STOP" if day%2 else "4H_OPPOSITE_ZONE",
        "gross_nominal_pct":.1,"symbol":"BTCUSDT",
        "stop_per_4h_atr":.5 if day%2 else 1.5}
       for day in range(20)]
    assert stats(x)["unique_utc_days"]==20
    result=contrast(x,"stop_per_4h_atr",1.0)
    assert result["above_or_equal"]["n"]==10
    assert result["below"]["n"]==10
    assert len(result["difference"]["bootstrap_95pct"])==2
    parts=split_chronologically(x)
    assert parts["earlier"] and parts["later"] and parts["embargo"]
    assert max(r["entry_at"] for r in parts["earlier"]) < min(
        r["entry_at"] for r in parts["later"]
    )
