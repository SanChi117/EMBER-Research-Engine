"""RESET-07 v2: limit touch, TTL and budget tests — no alpha from fixtures."""
from __future__ import annotations

import json
from decimal import Decimal as D
from pathlib import Path

from research.convex_runner import backtest as old
from research.convex_runner import backtest_limit_v2 as v2

ROOT = Path(__file__).resolve().parents[1]


def candles(n=45, *, low="100", high="110", close="105"):
    return [
        old.Bar(old.START + i * old.STEP, D("105"), D(high), D(low), D(close))
        for i in range(n)
    ]


def mock_alarm(bars, _side):
    if bars[0].c == D("106"):
        return {}
    return {
        old.START: {
            "limit": D("95"),
            "stop": D("80"),
            "pivot": D("80"),
            "signal_time": old.START - old.STEP,
        }
    }


def target_portfolio(n=45, *, low="100", high="110", close="105"):
    main = candles(n, low=low, high=high, close=close)
    silent = candles(n, low="100", high="110", close="106")
    return {symbol: main if symbol == "SOLUSDT" else silent
            for symbol in old.SYMBOLS}


def test_7day_ttl_no_touch_expires_once(monkeypatch):
    monkeypatch.setattr(v2, "prepare_signals", mock_alarm)
    result = v2.run_one(target_portfolio(), side="LONG", fraction=D("0.01"))
    assert result["signals_limit_placed"] == 1
    assert result["signals_limit_filled"] == 0
    assert result["signals_expired_unfilled"] == 1
    assert result["trades"] == 0
    assert result["limit_touch_rate"] == "0"
    expired = [x for x in result["limit_events"] if x["reason"] == "EXPIRED_UNFILLED"]
    assert len(expired) == 1
    assert expired[0]["ts"] == old.START + 42 * old.STEP


def test_touch_only_after_registration_fills_trade(monkeypatch):
    monkeypatch.setattr(v2, "prepare_signals", mock_alarm)
    result = v2.run_one(
        target_portfolio(3, low="90", high="108", close="100"),
        side="LONG", fraction=D("0.01"),
    )
    assert result["signals_limit_placed"] == 1
    assert result["signals_limit_filled"] == 1
    assert result["trades"] == 1
    assert result["limit_touch_rate"] == "1"
    assert result["more_than_60pct_fill_explanation"] is not None
    assert D(result["closed_trades"][0]["entry"]) > D("95")  # slip accounted


def test_same_candle_touch_and_stop_never_claims_free_win(monkeypatch):
    monkeypatch.setattr(v2, "prepare_signals", mock_alarm)
    result = v2.run_one(
        target_portfolio(3, low="75", high="108", close="100"),
        side="LONG", fraction=D("0.01"),
    )
    assert result["signals_limit_filled"] == 1
    assert result["trades"] == 1
    assert D(result["closed_trades"][0]["pnl_usdt"]) < 0
    touched = [r for r in result["limit_events"]
               if r["reason"] == "LIMIT_FILLED_TOUCH_ASSUMED"]
    assert touched[0]["same_bar_stop_ordering_undetermined"] is True


def test_six_ticket_budget_enforced_at_fill_not_order(monkeypatch):
    monkeypatch.setattr(
        v2, "prepare_signals",
        lambda _bars, _side: mock_alarm(candles(), _side),
    )
    result = v2.run_one(
        {s: candles(2, low="90", high="108", close="105") for s in old.SYMBOLS},
        side="LONG", fraction=D("0.01"),
    )
    assert result["signals_limit_placed"] == 10
    assert result["signals_limit_filled"] == 6
    assert result["signals_budget_touch_rejected"] == 4
    assert result["skipped_budget"] == 4


def test_no_order_before_alert(monkeypatch):
    monkeypatch.setattr(
        v2, "prepare_signals",
        lambda _bars, _side: {
            old.START + old.STEP: {"limit": D("95"),
                                  "stop": D("80"), "pivot": D("80"),
                                  "signal_time": old.START}
        },
    )
    result = v2.run_one(
        {s: candles(2, low="90", high="108", close="105") for s in old.SYMBOLS},
        side="LONG", fraction=D("0.01"),
    )
    assert all(x["placed_at_ms"] >= old.START + old.STEP
               for x in result["limit_events"]
               if x["reason"] == "LIMIT_PLACED")


def test_expiry_censored_at_end_of_window(monkeypatch):
    monkeypatch.setattr(v2, "prepare_signals", mock_alarm)
    result = v2.run_one(target_portfolio(3), side="LONG", fraction=D("0.01"))
    assert result["signals_expired_unfilled"] == 0
    assert result["signals_right_censored_end"] == 1


def test_same_inputs_produce_byte_identical_json(monkeypatch):
    monkeypatch.setattr(v2, "prepare_signals", mock_alarm)
    portfolio = target_portfolio(7, low="90", high="108", close="105")
    a = v2.run_one(portfolio, side="LONG", fraction=D("0.01"))
    b = v2.run_one(portfolio, side="LONG", fraction=D("0.01"))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert not hasattr(v2, "place_order")


def test_1pct_original_source_and_sha_is_reused_untouched():
    assert (ROOT / "research/convex_runner/raw_sha256_manifest.json").exists()
    assert (ROOT / "research/convex_runner/preregistration.json").exists()
    assert (ROOT / "research/convex_runner/limit_v2_preregistration.json").exists()
    assert v2.START == old.START and v2.END == old.END


def test_owner_not_given_limit_level_unambiguous():
    prereg = json.loads((ROOT / "research/convex_runner/limit_v2_preregistration.json").read_text())
    assert prereg["limit_price"].startswith("IMPLEMENTER_ASSUMPTION")
    assert prereg["only_changed_mechanism"].startswith("entry execution")
    assert prereg["live_allowed"] is False
