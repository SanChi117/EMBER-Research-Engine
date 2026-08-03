from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from scripts.run_portfolio_wfo import (
    MIN_TOTAL_TRADES,
    protocol_passes,
    render_markdown,
    serialize_summary,
)


def _fold(number: int, trades: int, positive: bool = True) -> SimpleNamespace:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=number * 10)
    return SimpleNamespace(
        fold=number,
        train_start=start,
        train_end=start + timedelta(days=30),
        test_start=start + timedelta(days=30, minutes=45),
        test_end=start + timedelta(days=55, minutes=45),
        return_pct=1.0 if positive else -1.0,
        profit_factor=2.0 if positive else 0.5,
        max_drawdown=1.0,
        num_trades=trades,
        positive=positive,
    )


def _summary(*, stability: float = 75.0, trades_per_fold: int = 5) -> SimpleNamespace:
    return SimpleNamespace(
        pass_fail="PASS",
        avg_return=1.0,
        avg_pf=2.0,
        worst_dd=2.0,
        stability_score=stability,
        folds=[_fold(index, trades_per_fold) for index in range(1, 5)],
    )


def test_protocol_requires_twenty_total_test_trades() -> None:
    summary = _summary(trades_per_fold=4)
    assert sum(fold.num_trades for fold in summary.folds) == 16
    assert not protocol_passes(summary, 16)
    assert protocol_passes(summary, MIN_TOTAL_TRADES)


def test_protocol_keeps_stability_gate() -> None:
    summary = _summary(stability=50.0, trades_per_fold=5)
    assert not protocol_passes(summary, 20)


def test_serialized_status_uses_complete_protocol_not_engine_only() -> None:
    summary = _summary(trades_per_fold=2)
    result = serialize_summary(
        summary,
        ("PEPEUSDT", "FETUSDT", "WIFUSDT", "SUIUSDT"),
    )
    assert result["engine_status"] == "PASS"
    assert result["total_trades"] == 8
    assert result["status"] == "FAIL"
    assert result["portfolio_mode"] is True


def test_markdown_contains_required_summary_and_blocked_next_step() -> None:
    summary = _summary(stability=50.0, trades_per_fold=2)
    result = serialize_summary(
        summary,
        ("PEPEUSDT", "FETUSDT", "WIFUSDT", "SUIUSDT"),
    )
    payload = {
        "symbols": ["PEPEUSDT", "FETUSDT", "WIFUSDT", "SUIUSDT"],
        "profile": "high-vol-block",
        "interval": "15m",
        "bars_per_symbol": 15000,
        "initial_equity": 10000.0,
        "result": result,
    }
    report = render_markdown(payload)
    assert "# Portfolio WFO — OOS 4 Alts" in report
    assert "- Total Trades: 8" in report
    assert "- Status: **FAIL**" in report
    assert "Universe expansion is blocked" in report
