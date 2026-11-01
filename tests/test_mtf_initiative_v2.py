"""MTF V2 closed-bar causality, provenance, flow ablation and exits."""
from __future__ import annotations

from dataclasses import replace

import pytest

from ember.research.mtf_v2_bars import (
    D1,
    H1,
    H4,
    M15,
    FlowBar,
    aggregate,
    confirmed_pivots,
    contexts,
    daily_regime,
    validate,
)
from ember.research.mtf_v2_evaluation import simulate
from ember.research.mtf_v2_signals import detect


def sample() -> list[FlowBar]:
    bars = [
        FlowBar(i * M15, 100, 101, 99, 100, 100, 50)
        for i in range(1000)
    ]
    # Preexisting 4H opposing structural high, confirmed by 2 right 4H bars.
    bars[32 * 16] = replace(bars[32 * 16], high=110)
    # Preexisting 4H low, right-confirmed before contest in H4 #40.
    bars[35 * 16] = replace(bars[35 * 16], low=97.5)
    # Hour #0: seller aggressor sweep below 4H low, closes back inside.
    for i in range(40 * 16, 40 * 16 + 4):
        bars[i] = FlowBar(i * M15, 100, 101, 97, 98, 500, 100)
    # Later and distinct fully closed H1 bar: buyer initiative.
    for i in range(40 * 16 + 4, 40 * 16 + 8):
        bars[i] = FlowBar(i * M15, 100, 101, 99, 100.5, 500, 350)
    # Subsequent closed 15m break above six PRIOR M15 candle highs.
    i = 40 * 16 + 8
    bars[i] = FlowBar(i * M15, 100.5, 102, 100, 101.6, 400, 320)
    return bars


def test_closed_parent_h1_and_m15_form_one_entry() -> None:
    bars = sample()
    entries, events = detect("TESTUSDT", bars)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.side == "long"
    assert entry.parent_4h_close <= entry.attempt_1h_close - H1
    assert entry.attempt_1h_close < entry.confirm_1h_close < entry.trigger_15m_close
    assert entry.eligible_entry_at == entry.trigger_15m_close
    assert entry.h4_opposite_pivot == 110
    assert entry.h4_boundary == 97.5
    assert entry.stop < entry.attempt_extreme
    assert entry.structural_rr >= 1.25
    assert {"H1_CONTEST", "H1_TRANSFER", "ENTRY_READY"} <= {x["event"] for x in events}


def test_prefix_results_invariant_to_future_changes() -> None:
    bars = sample()
    prefix = bars[:650]
    decisions_a, _ = detect("TESTUSDT", prefix)
    future = bars[:]
    for i in range(650, len(future)):
        future[i] = FlowBar(i * M15, 100, 200, 1, 150, 10000, 9500)
    decisions_b, _ = detect("TESTUSDT", future)
    assert decisions_a == [x for x in decisions_b if x.trigger_15m_close <= 650 * M15]


def test_taker_flow_matters_beyond_price_pattern() -> None:
    bars = sample()
    for i in range(40 * 16, 40 * 16 + 4):
        bars[i] = replace(bars[i], taker_buy=250)  # .50, no seller aggression.
    flow_entries, _ = detect("TESTUSDT", bars, require_flow=True)
    control_entries, _ = detect("TESTUSDT", bars, require_flow=False)
    assert not flow_entries
    assert len(control_entries) == 1


def test_conservative_stop_first_when_both_hit_same_m15() -> None:
    bars = sample()
    entry = detect("TESTUSDT", bars)[0][0]
    first = entry.eligible_entry_at // M15
    bars[first] = FlowBar(first * M15, 101, 111, 90, 100, 400, 200)
    outcome = simulate([entry], bars)[0]
    assert outcome.reason == "BOTH_STOP_FIRST"
    assert outcome.stress_pct < 0


def test_gap_cancels_intention_and_never_records_fake_pnl() -> None:
    bars = sample()
    entry = detect("TESTUSDT", bars)[0][0]
    first = entry.eligible_entry_at // M15
    bars[first] = FlowBar(first * M15, 120, 121, 119, 120, 100, 50)
    outcome = simulate([entry], bars)[0]
    assert outcome.reason == "GAP_INVALIDATED"
    assert outcome.gross_pct is None


def test_confirmed_pivot_not_available_before_two_right_4h_bars() -> None:
    four = aggregate(sample(), H4)
    lows, highs = confirmed_pivots(four)
    origin = 35 * H4
    found = [x for x in lows if x[2] == origin]
    assert len(found) == 1
    assert found[0][0] == (35 + 3) * H4
    assert any(x[2] == 32 * H4 for x in highs)
    ctx, times = contexts(four, [])
    assert all(a <= b for a, b in zip(times, times[1:]))
    assert ctx[36].pivot_low_at != origin
    assert ctx[37].pivot_low_at == origin


def test_daily_state_cannot_see_future_or_partial_day() -> None:
    days = [FlowBar(i * D1, 100, 101, 99, 100 + i * .01, 100, 50) for i in range(25)]
    asof = 21 * D1 + 12 * H1
    before = daily_regime(days, asof)
    mutated = days[:]
    mutated[21] = replace(mutated[21], close=500)
    assert daily_regime(mutated, asof) == before
    assert daily_regime(mutated, 22 * D1) != before


def test_bad_gap_and_impossible_taker_volume_rejected() -> None:
    bars = sample()
    changed = bars[:]
    changed[20] = replace(changed[20], ts=changed[19].ts)
    with pytest.raises(ValueError, match="invalid"):
        validate(changed)
    changed = bars[:]
    changed[20] = replace(changed[20], taker_buy=changed[20].volume + 10)
    with pytest.raises(ValueError, match="invalid"):
        validate(changed)


def test_incomplete_trade_kept_censored_without_pnl() -> None:
    bars = sample()
    entry = detect("TESTUSDT", bars)[0][0]
    result = simulate([entry], bars[:entry.eligible_entry_at // M15 + 20])
    assert result[0].reason == "INCOMPLETE"
    assert result[0].stress_pct is None


def test_no_orders_or_paper_actions_in_research_modules() -> None:
    from inspect import getsource

    from ember.research import mtf_v2_bars, mtf_v2_evaluation, mtf_v2_signals

    for module in (mtf_v2_bars, mtf_v2_evaluation, mtf_v2_signals):
        source = getsource(module)
        assert "create_order(" not in source
        assert "api_key =" not in source


def test_execution_only_ablation_keeps_h1_flow_but_not_third_gate() -> None:
    bars = sample()
    strict, _ = detect("TESTUSDT", bars, execution_mode="m15_break")
    direct, _ = detect("TESTUSDT", bars, execution_mode="next_m15_open")
    assert len(strict) == 1 and len(direct) == 1
    d = direct[0]
    assert d.confirm_1h_close == d.trigger_15m_close
    assert d.eligible_entry_at == d.trigger_15m_close
    assert d.parent_4h_close < d.attempt_1h_close
    assert d.model == "MTF_V2_FLOW_DIRECT"
    assert d.stop == strict[0].stop
    assert d.target == strict[0].target


def test_invalid_execution_policy_rejected() -> None:
    with pytest.raises(ValueError, match="execution mode"):
        detect("TESTUSDT", sample(), execution_mode="unrecognized")
