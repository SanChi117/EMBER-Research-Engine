"""Pydantic configuration for the HYBRID v2 baseline."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class EmberConfig(BaseModel):
    """Immutable project configuration.

    Percentage fields use human-readable percentage points. For example,
    ``risk_per_trade_pct=1.0`` means one percent of equity.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = "HYBRID_v2"
    context_tfs: tuple[str, ...] = ("1d", "4h")
    entry_tf: str = "15m"
    confirm_tf: str = "5m"
    core_symbols: tuple[str, ...] = (
        "INJUSDT",
        "TONUSDT",
        "DOGEUSDT",
        "ARBUSDT",
        "NEARUSDT",
        "OPUSDT",
    )
    allowed_setups: tuple[str, ...] = ("pullback", "ignition")
    blocked_setups: tuple[str, ...] = (
        "breakout",
        "range_rotation",
        "liquidity_reclaim",
        "watch",
    )
    # Kept exactly as specified. The setup detector maps "down" to bearish context.
    allowed_direction_contexts: tuple[str, ...] = ("down",)

    # The specification baseline is EMA20 with a +/-2% neutral band. Alternative
    # modes are research profiles and do not silently replace the baseline.
    htf_bias_mode: Literal["ema", "structure"] = "ema"
    htf_ema_period: int = 20
    htf_ema_threshold_pct: float = 2.0

    # ContextBuilder emits "high_vol", not "high". An empty tuple means that the
    # setup layer observes high-volatility candidates instead of blocking them.
    blocked_volatility_regimes: tuple[str, ...] = ()
    min_confidence: float = 43.0
    min_volume_ratio: float = 0.70
    risk_per_trade_pct: float = 1.0
    min_rr: float = 1.8
    max_positions: int = 1
    daily_drawdown_stop_pct: float = 2.0
    weekly_drawdown_stop_pct: float = 5.0
    consecutive_loss_stop: int = 3
    atr_period: int = 14
    atr_stop_multiplier: float = 1.5
    min_stop_distance_pct: float = 0.5
    max_stop_distance_pct: float = 5.0
    max_holding_hours: int = 8
    fee_rate: float = 0.001
    slippage_rate: float = 0.0002
    leverage: float = 20.0
    tp_mode: Literal["fixed_rr", "opposite_htf_liquidity"] = "fixed_rr"
    wfo_folds: int = 4
    wfo_lookback_days: int = 30
    wfo_embargo_bars: int = 3
    paper_min_trades: int = 100
    paper_min_days: int = 30
    paper_db_path: Path = Path("paper_trades.db")

    @field_validator(
        "min_confidence",
        "min_volume_ratio",
        "risk_per_trade_pct",
        "min_rr",
        "daily_drawdown_stop_pct",
        "weekly_drawdown_stop_pct",
        "atr_stop_multiplier",
        "min_stop_distance_pct",
        "max_stop_distance_pct",
        "fee_rate",
        "slippage_rate",
        "leverage",
        "htf_ema_threshold_pct",
    )
    @classmethod
    def _positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("value must be positive")
        return value

    @field_validator(
        "max_positions",
        "consecutive_loss_stop",
        "atr_period",
        "max_holding_hours",
        "wfo_folds",
        "wfo_lookback_days",
        "wfo_embargo_bars",
        "paper_min_trades",
        "paper_min_days",
        "htf_ema_period",
    )
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be positive")
        return value

    @field_validator("max_stop_distance_pct")
    @classmethod
    def _stop_range_is_valid(cls, value: float, info: object) -> float:
        data = getattr(info, "data", {})
        minimum = data.get("min_stop_distance_pct")
        if minimum is not None and value < minimum:
            raise ValueError("max_stop_distance_pct must be >= min_stop_distance_pct")
        return value
