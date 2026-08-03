"""Shared immutable data models for EMBER."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

Bias = Literal["bull", "bear", "neutral"]
Regime = Literal["trend", "range", "high_vol", "low_vol"]
Side = Literal["long", "short"]
SetupType = Literal[
    "pullback",
    "ignition",
    "breakout",
    "range_rotation",
    "liquidity_reclaim",
]
GradeABCD = Literal["A", "B", "C", "D"]


@dataclass(frozen=True, slots=True)
class MTFContext:
    symbol: str
    time: datetime
    bias: Bias
    regime: Regime
    pda_position: float
    session: Literal["asia", "london", "ny"]
    htf_liquidity_swept: bool
    htf_poi_active: bool
    htf_structure: Literal["uptrend", "downtrend", "consolidation"]
    volume_ratio: float
    atr: float
    opposite_htf_liquidity: float | None = None


@dataclass(frozen=True, slots=True)
class SetupCandidate:
    symbol: str
    time: datetime
    setup_type: SetupType
    side: Side
    confidence: float
    trigger_price: float
    notes: str


@dataclass(frozen=True, slots=True)
class RiskPlan:
    symbol: str
    side: Side
    entry: float
    stop: float
    target: float
    target_rr: float
    risk_amount: float
    position_size: float
    notional: float
    margin: float
    leverage: float
    setup_type: str
    entry_time: datetime
    fee_cost: float
    slippage_cost: float
    net_edge: float
    grade: Literal["A", "B", "C"]


@dataclass(frozen=True, slots=True)
class SimulatedExit:
    exit_time: datetime
    exit_price: float
    result_r: float
    exit_reason: Literal["take_profit", "stop_loss", "time_stop", "end_of_data"]
    bars_held: int


@dataclass(frozen=True, slots=True)
class QualityScore:
    trade_id: int
    setup_score: float
    location_score: float
    timing_score: float
    structure_score: float
    composite: float
    grade: GradeABCD


@dataclass(frozen=True, slots=True)
class StructureScore:
    trade_id: int
    recency_score: float
    consistency_score: float
    regime_score: float
    composite: float
    grade: GradeABCD


@dataclass(slots=True)
class Trade:
    id: int
    symbol: str
    side: Side
    setup_type: str
    entry_time: datetime
    exit_time: datetime | None
    entry_price: float
    stop_price: float
    target_price: float
    planned_rr: float
    result_r: float | None
    exit_reason: str | None
    bars_held: int
    mfe_r: float
    mae_r: float
    status: Literal["open", "closed", "invalid"]
    regime: str
    confidence: float
    quality_grade: GradeABCD
    structure_grade: GradeABCD
    risk_amount: float


@dataclass(frozen=True, slots=True)
class BacktestMetrics:
    total_return: float
    profit_factor: float
    max_drawdown: float
    win_rate: float
    avg_trade: float
    num_trades: int
    final_equity: float


@dataclass(frozen=True, slots=True)
class BacktestResult:
    trades: list[Trade]
    metrics: BacktestMetrics
    equity_curve: list[tuple[datetime, float]]


@dataclass(slots=True)
class PortfolioState:
    cash: float
    equity: float
    peak_equity: float
    open_trades: list[Trade] = field(default_factory=list)
    closed_trades: list[Trade] = field(default_factory=list)
    daily_pnl: dict[date, float] = field(default_factory=dict)
    weekly_pnl: dict[str, float] = field(default_factory=dict)
    consecutive_losses: int = 0
    halted: bool = False
    halt_reason: str | None = None


@dataclass(frozen=True, slots=True)
class WFOFold:
    fold: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    return_pct: float
    profit_factor: float
    max_drawdown: float
    num_trades: int
    positive: bool


@dataclass(frozen=True, slots=True)
class WFOSummary:
    folds: list[WFOFold]
    avg_return: float
    avg_pf: float
    worst_dd: float
    stability_score: float
    pass_fail: Literal["PASS", "FAIL"]
