"""Research-only state machine tests: causality, geometry and conservative execution."""
from __future__ import annotations

from dataclasses import replace

import pytest

from ember.research.initiative_transition import (
    BAR_MS,
    Bar,
    asof_regime,
    closed_daily,
    detect,
    prior_atr,
    simulate,
    validate_bars,
)


def sample(side: str = "long") -> list[Bar]:
    bars = [
        Bar(i * BAR_MS, 100, 101, 99, 100, 100)
        for i in range(165)
    ]
    # Older, PREEXISTING opposite-side structure, not in the most recent 12 bars.
    if side == "long":
        bars[100] = replace(bars[100], high=106)
        bars[130] = Bar(130 * BAR_MS, 100, 100.8, 98.5, 100.2, 400)
        bars[131] = Bar(131 * BAR_MS, 100.2, 102, 99.6, 101.1, 130)
        bars[132] = Bar(132 * BAR_MS, 101.1, 107, 100.0, 105, 100)
    else:
        bars[100] = replace(bars[100], low=94)
        bars[130] = Bar(130 * BAR_MS, 100, 101.5, 99.2, 99.8, 400)
        bars[131] = Bar(131 * BAR_MS, 99.8, 100.4, 98.0, 98.9, 130)
        bars[132] = Bar(132 * BAR_MS, 98.9, 100.0, 93, 94.2, 100)
    return bars


@pytest.mark.parametrize("side", ["long", "short"])
def test_entry_requires_two_separate_closed_4h_bars(side: str) -> None:
    bars = sample(side)
    assert detect("TESTUSDT", bars[:131])[0] == []  # attempt close only
    decisions, audit = detect("TESTUSDT", bars[:132])
    assert len(decisions) == 1
    d = decisions[0]
    assert d.side == side
    assert d.decision_at == 132 * BAR_MS
    assert d.eligible_entry_at == d.decision_at
    assert d.attempt_at == 131 * BAR_MS
    assert d.reference_entry == bars[131].close
    assert d.room_rr >= 1.25
    assert [x["status"] for x in audit] == ["ACCEPTED"]


@pytest.mark.parametrize("side", ["long", "short"])
def test_clean_path_target_is_only_diagnostic(side: str) -> None:
    bars = sample(side)
    decisions, _ = detect("TESTUSDT", bars)
    outcomes = simulate(decisions, bars)
    assert len(decisions) == 1
    assert len(outcomes) == 1
    assert outcomes[0].exit_reason == "STRUCTURE"
    assert outcomes[0].entry_at >= decisions[0].decision_at
    assert outcomes[0].gross_pct > 0


def test_change_future_cannot_rewrite_closed_signal() -> None:
    bars = sample()
    past = bars[:132]
    before = detect("TESTUSDT", past)[0]
    extended = bars[:]
    for i in range(132, len(extended)):
        extended[i] = Bar(i * BAR_MS, 100, 500, 1, 250, 10000)
    after = [d for d in detect("TESTUSDT", extended)[0] if d.decision_at <= 132 * BAR_MS]
    assert before == after


def test_same_candle_stop_target_is_stop_first() -> None:
    bars = sample()
    bars[132] = Bar(132 * BAR_MS, 101.1, 110, 90, 101, 200)
    decisions, _ = detect("TESTUSDT", bars)
    result = simulate(decisions, bars)
    assert result[0].exit_reason == "BOTH_STOP_FIRST"
    assert result[0].gross_pct < 0
    assert result[0].stress_pct < result[0].base_pct


def test_candidate_is_invalidated_when_attempt_extreme_revisited() -> None:
    bars = sample()
    bars[131] = Bar(131 * BAR_MS, 100.2, 103, 98.4, 102, 100)
    decisions, audit = detect("TESTUSDT", bars[:132])
    assert not decisions
    assert audit[0]["reason"] == "EXTREME_REVISITED"


def test_next_open_gap_cancels_unfilled_intent_without_pnl() -> None:
    bars = sample()
    bars[132] = Bar(132 * BAR_MS, 120, 121, 115, 119, 100)
    decisions, _ = detect("TESTUSDT", bars)
    outcome = simulate(decisions, bars)[0]
    assert outcome.exit_reason == "GAP_INVALIDATED"
    assert outcome.gross_pct is None
    assert outcome.stress_pct is None


def test_daily_context_never_uses_partial_day() -> None:
    bars = sample()
    days = closed_daily(bars)
    end = [d[0] for d in days]
    asof = 21 * 24 * 3600 * 1000 + 5 * BAR_MS
    assert all(d[0] <= asof for d in days if d[0] <= asof)
    original = asof_regime(days, end, asof)
    changed = bars[:]
    changed[21 * 6 + 5] = Bar((21 * 6 + 5) * BAR_MS, 100, 1000, 0.1, 900, 999)
    days_changed = closed_daily(changed)
    assert original == asof_regime(days_changed, [d[0] for d in days_changed], asof)


def test_data_continuity_and_atr_exclude_attempt_bar() -> None:
    bars = sample()
    assert prior_atr(bars, 130) == pytest.approx(2.0)
    assert prior_atr(bars, 131) > 2.0
    damaged = bars[:]
    damaged[5] = replace(damaged[5], ts=damaged[4].ts)
    with pytest.raises(ValueError, match="gap, duplicate"):
        validate_bars(damaged)


def test_short_history_never_issues_signal() -> None:
    assert detect("TESTUSDT", sample()[:40]) == ([], [])


def test_no_quote_or_live_order_dependencies() -> None:
    """This module has no broker, API key, order execution or scheduler code."""
    import inspect

    from ember.research import initiative_transition

    src = inspect.getsource(initiative_transition)
    assert "create_order(" not in src
    assert "api_key" not in src
