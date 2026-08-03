from __future__ import annotations

from typing import Any

from ember.config import EmberConfig
from ember.core import binance_history
from ember.core.context_builder import ContextBuilder
from ember.research.profiles import diagnostic_profiles
from ember.research.synthetic import mixed_regime_synthetic_data, trending_synthetic_data
from ember.simulation.backtester import Backtester


def test_backtester_rejection_accounting_is_complete() -> None:
    candles = trending_synthetic_data(bars=300)
    backtester = Backtester(EmberConfig(allowed_direction_contexts=("bull", "bear")))
    result = backtester.run(candles)
    diagnostics = backtester.last_diagnostics

    scan_total = sum(
        diagnostics[key]
        for key in (
            "neutral_context",
            "direction_reject",
            "regime_reject",
            "no_setup",
            "setup_blocked",
            "confidence_low",
            "volume_low",
            "candidate_passed",
        )
    )
    assert diagnostics["bars_seen"] == candles.height - 60
    assert scan_total == diagnostics["bars_seen"]
    assert diagnostics["executed"] == result.metrics.num_trades


def test_mixed_synthetic_is_reproducible_and_has_all_regimes() -> None:
    first = mixed_regime_synthetic_data(bars=2200, seed=7)
    second = mixed_regime_synthetic_data(bars=2200, seed=7)
    assert first.equals(second)
    assert set(first.get_column("source_regime").unique().to_list()) == {
        "trend_up",
        "trend_down",
        "range",
        "high_vol",
    }


def test_paginated_fetch_history_assembles_multiple_pages(monkeypatch: Any) -> None:
    base_ms = 1_700_000_000_000
    calls: list[int | None] = []

    def fake_request(
        symbol: str,
        interval: str,
        limit: int,
        end_time: int | None,
    ) -> list[list[object]]:
        del symbol, interval, limit
        calls.append(end_time)
        indices = range(10, 20) if len(calls) == 1 else range(5, 10)
        return [
            [
                base_ms + index * 900_000,
                "100",
                "101",
                "99",
                "100.5",
                "10",
            ]
            for index in indices
        ]

    monkeypatch.setattr(binance_history, "request_klines", fake_request)
    frame = binance_history.fetch_history("DOGEUSDT", "15m", 15)
    assert frame.height == 15
    assert len(calls) == 2
    assert frame.get_column("time").is_sorted()


def test_tighter_ema_band_changes_neutral_to_directional() -> None:
    rows = [{"close": 100.0} for _ in range(20)] + [{"close": 101.0}]
    baseline = ContextBuilder(EmberConfig())
    tighter = ContextBuilder(EmberConfig(htf_ema_threshold_pct=0.5))

    assert baseline._bias(rows, "consolidation") == "neutral"  # noqa: SLF001
    assert tighter._bias(rows, "consolidation") == "bull"  # noqa: SLF001


def test_structure_bias_maps_structure_without_ema_override() -> None:
    builder = ContextBuilder(EmberConfig(htf_bias_mode="structure"))
    rows = [{"close": 100.0}]

    assert builder._bias(rows, "uptrend") == "bull"  # noqa: SLF001
    assert builder._bias(rows, "downtrend") == "bear"  # noqa: SLF001
    assert builder._bias(rows, "consolidation") == "neutral"  # noqa: SLF001


def test_bias_profiles_change_only_declared_assumptions() -> None:
    profiles = diagnostic_profiles()
    baseline = profiles["baseline"]
    both = profiles["both-directions"]
    tight = profiles["ema-tight"]
    ema50 = profiles["ema50"]
    structure = profiles["structure-bias"]

    assert baseline.htf_bias_mode == "ema"
    assert baseline.htf_ema_period == 20
    assert baseline.htf_ema_threshold_pct == 2.0
    assert both.allowed_direction_contexts == ("bull", "bear")
    assert tight.htf_ema_threshold_pct == 0.5
    assert tight.htf_ema_period == baseline.htf_ema_period
    assert ema50.htf_ema_period == 50
    assert ema50.htf_ema_threshold_pct == baseline.htf_ema_threshold_pct
    assert structure.htf_bias_mode == "structure"
    assert structure.min_rr == baseline.min_rr


def test_volatility_and_target_profiles_are_isolated() -> None:
    profiles = diagnostic_profiles()
    baseline = profiles["baseline"]
    high_vol = profiles["high-vol-block"]
    opposite = profiles["opposite-liquidity"]

    assert high_vol.blocked_volatility_regimes == ("high_vol",)
    assert high_vol.tp_mode == baseline.tp_mode
    assert high_vol.allowed_direction_contexts == baseline.allowed_direction_contexts
    assert opposite.tp_mode == "opposite_htf_liquidity"
    assert opposite.blocked_volatility_regimes == baseline.blocked_volatility_regimes
    assert opposite.allowed_direction_contexts == baseline.allowed_direction_contexts

    baseline_data = baseline.model_dump()
    high_vol_data = high_vol.model_dump()
    opposite_data = opposite.model_dump()
    high_vol_data["blocked_volatility_regimes"] = baseline_data[
        "blocked_volatility_regimes"
    ]
    opposite_data["tp_mode"] = baseline_data["tp_mode"]
    assert high_vol_data == baseline_data
    assert opposite_data == baseline_data
