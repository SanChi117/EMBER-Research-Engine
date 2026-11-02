"""RESET-08 causal window, immutable 3-arm scope, pending cancellation."""
from __future__ import annotations

import json
from decimal import Decimal as D
from pathlib import Path

import pytest

from research.convex_runner import backtest_limit_v2 as old
from research.convex_runner import reset08_runner as trial
from research.convex_runner import reset08_window as gate
from research.convex_runner.reset08_btc_contract import check_btc

ROOT = Path(__file__).resolve().parents[1]


def _frozen_calendar(monkeypatch, *, changed_day=None):
    first = 1672531200000  # 2023-01-01 00:00 UTC
    timestamps = [first + i * gate.DAY for i in range(600)]

    def mocked_measure(rows):
        symbol = rows[0][0]
        prices = {t: D(100) + D(i) / D(10)
                  for i, t in enumerate(timestamps)}
        if symbol == "BTC" and changed_day is not None:
            prices[changed_day] = D("1")
        volatility = {t: D("0.01") + D(i) / D(100000)
                      for i, t in enumerate(timestamps)}
        return prices, volatility

    monkeypatch.setattr(gate, "daily_measures", mocked_measure)
    btc = [["BTC"]]
    alt = {s: [[s]] for s in gate.SYMBOLS}
    return btc, alt


def test_hysteresis_three_open_two_fail_close():
    state = gate.advance_state(False, (True, True, False), known=True)
    assert not state
    state = gate.advance_state(state, (True, True, True), known=True)
    assert state
    state = gate.advance_state(state, (False, True, True), known=True)
    assert state
    state = gate.advance_state(state, (False, False, True), known=True)
    assert not state
    assert not gate.advance_state(True, (True, True, True), known=False)


def test_strict_D_minus_one_no_future_leak(monkeypatch):
    btc, alt = _frozen_calendar(monkeypatch)
    start = 1722470400000  # Aug 1 2024
    baseline = gate.build_calendar(btc, alt, start_ms=start,
                                   end_ms=start + 4 * gate.DAY)
    btc, alt = _frozen_calendar(monkeypatch, changed_day=start)
    changed = gate.build_calendar(btc, alt, start_ms=start,
                                  end_ms=start + 4 * gate.DAY)
    assert baseline["days"][0] == changed["days"][0]
    assert baseline["days"][1]["btc"] is True
    assert changed["days"][1]["btc"] is False


def test_calendar_cross_med_has_strict_full_365d_lookback(monkeypatch):
    btc, alt = _frozen_calendar(monkeypatch)
    first = 1672531200000
    result = gate.build_calendar(
        btc, alt, start_ms=first + 100 * gate.DAY,
        end_ms=first + 400 * gate.DAY,
    )
    assert not result["days"][0]["known"]
    assert result["days"][-1]["known"]


def test_fake_BTC_hash_is_rejected():
    raw = ROOT / "research/convex_runner/raw"
    with pytest.raises(ValueError, match="BTC_SHA256_MISMATCH"):
        check_btc(raw, {"1d": "0" * 64, "4h": "0" * 64})


def _portfolio(*, touch_at=None, total=12):
    bars = {}
    for s in old.SYMBOLS:
        b = []
        for i in range(total):
            price = D("105") if s == "SOLUSDT" else D("106")
            low = D("90") if s == "SOLUSDT" and touch_at == i else D("100")
            b.append(old.Bar(old.START + i * old.STEP, price,
                             D("108"), low, price))
        bars[s] = b
    return bars


def _alarm(bars, _side):
    if bars[0].o != D("105"):
        return {}
    return {
        old.START: {"limit": D("95"), "stop": D("80"),
                    "pivot": D("80"), "signal_time": old.START - old.STEP}
    }


def test_gate_accepts_primary_and_rejects_control(monkeypatch):
    monkeypatch.setattr(trial, "prepare_signals", _alarm)
    day = old.START
    states = {day: {"known": True, "state": "OPEN"}}
    primary = trial.run_one(
        _portfolio(touch_at=0, total=3),
        side="LONG", fraction=D("0.01"),
        calendar_by_day=states, required_regime="OPEN",
    )
    control = trial.run_one(
        _portfolio(touch_at=0, total=3),
        side="LONG", fraction=D("0.01"),
        calendar_by_day=states, required_regime="CLOSED",
    )
    assert primary["signals_limit_filled"] == 1
    assert primary["trades"] == 1
    assert control["signals_limit_filled"] == 0
    assert control["skipped_regime"] == 1


def test_pending_canceled_before_touch_after_day_changes(monkeypatch):
    monkeypatch.setattr(trial, "prepare_signals", _alarm)
    day = old.START
    states = {
        day: {"known": True, "state": "OPEN"},
        day + gate.DAY: {"known": True, "state": "CLOSED"},
    }
    result = trial.run_one(
        _portfolio(touch_at=6), side="LONG", fraction=D("0.01"),
        calendar_by_day=states, required_regime="OPEN",
    )
    assert result["signals_limit_placed"] == 1
    assert result["cancelled_regime"] == 1
    assert result["signals_limit_filled"] == 0
    assert result["trades"] == 0


def test_filled_positions_managed_when_window_closes(monkeypatch):
    monkeypatch.setattr(trial, "prepare_signals", _alarm)
    day = old.START
    states = {
        day: {"known": True, "state": "OPEN"},
        day + gate.DAY: {"known": True, "state": "CLOSED"},
    }
    portfolio = _portfolio(touch_at=0)
    # Already-entered position stops next day, even after gate closes.
    portfolio["SOLUSDT"][6] = old.Bar(day + gate.DAY, D("75"), D("90"),
                                       D("74"), D("75"))
    result = trial.run_one(
        portfolio, side="LONG", fraction=D("0.01"),
        calendar_by_day=states, required_regime="OPEN",
    )
    assert result["signals_limit_filled"] == 1
    assert result["trades"] == 1
    assert result["closed_trades"][0]["cause"] in ("STOP", "GAP_STOP")


def test_v3_strict_long_only():
    with pytest.raises(ValueError, match="RESET08_LONG_ONLY"):
        trial.run_one(_portfolio(), side="SHORT", fraction=D("0.01"),
                      calendar_by_day={}, required_regime="OPEN")


def test_window_verdict_exact_gates():
    trials = [
        {"pf": "1.31", "trades": 40, "max_dd_fraction": "0.299"},
        {"pf": "1.2", "trades": 40, "max_dd_fraction": "0.29"},
        {"pf": "1.05", "trades": 50, "max_dd_fraction": "0.29"},
    ]
    cal = {"window_share": "0.20"}
    assert trial._classify_window(cal, trials).startswith("WINDOW_WORKS")
    trials[2]["pf"] = "1.06"
    assert trial._classify_window(cal, trials) == "WINDOW_DEAD"
    trials[2]["pf"] = "1.05"
    trials[0]["pf"] = "1.30"
    assert trial._classify_window(cal, trials) == "WINDOW_DEAD"


def test_runner_determinism_with_exact_same_gate(monkeypatch):
    monkeypatch.setattr(trial, "prepare_signals", _alarm)
    states = {old.START: {"known": True, "state": "OPEN"}}
    bars = _portfolio(touch_at=0, total=3)
    first = trial.run_one(
        bars, side="LONG", fraction=D("0.02"),
        calendar_by_day=states, required_regime="OPEN",
    )
    second = trial.run_one(
        bars, side="LONG", fraction=D("0.02"),
        calendar_by_day=states, required_regime="OPEN",
    )
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
