from __future__ import annotations

from datetime import datetime, timezone

from ember.config import EmberConfig
from ember.models import Trade
from ember.research.synthetic import trending_synthetic_data
from ember.simulation.backtester import Backtester
from ember.simulation.portfolio import PortfolioSimulator


def test_backtest_produces_positive_pf_on_trending_synthetic_data() -> None:
    config = EmberConfig(
        allowed_direction_contexts=("bear",),
        min_confidence=40.0,
        consecutive_loss_stop=10,
    )
    result = Backtester(config).run(trending_synthetic_data(bars=1000))
    assert result.metrics.num_trades > 0
    assert result.metrics.profit_factor > 1.0


def test_kill_switch_halts_on_daily_drawdown() -> None:
    config = EmberConfig(risk_per_trade_pct=1.0)
    portfolio = PortfolioSimulator(10_000.0, config)
    loss = Trade(
        id=1,
        symbol="DOGEUSDT",
        side="short",
        setup_type="pullback",
        entry_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        exit_time=datetime(2024, 1, 1, 1, tzinfo=timezone.utc),
        entry_price=100.0,
        stop_price=101.0,
        target_price=98.2,
        planned_rr=1.8,
        result_r=-2.1,
        exit_reason="stop_loss",
        bars_held=1,
        mfe_r=0.0,
        mae_r=-2.1,
        status="closed",
        regime="trend",
        confidence=70.0,
        quality_grade="B",
        structure_grade="B",
        risk_amount=100.0,
    )
    assert portfolio.open_trade(loss)
    portfolio.close_trade(loss)
    assert portfolio.state.halted is True
    assert portfolio.state.halt_reason is not None
