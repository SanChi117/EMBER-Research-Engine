from __future__ import annotations

from typing import Any

from ember.config import EmberConfig
from ember.core import binance_history
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
