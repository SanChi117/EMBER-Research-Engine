from __future__ import annotations

from datetime import datetime, timedelta, timezone

import polars as pl
from hypothesis import given
from hypothesis import strategies as st

from ember.config import EmberConfig
from ember.core.data_engine import DataEngine
from ember.core.features import FeatureBuilder
from ember.filters.structure_gate import StructureGate
from ember.models import MTFContext, RiskPlan, Trade
from ember.research.synthetic import trending_synthetic_data
from ember.simulation.backtester import Backtester
from ember.strategy.exit_simulator import ExitSimulator
from ember.strategy.setups import SetupDetector
from ember.utils import profit_factor

UTC = timezone.utc


def test_no_future_prices_in_setup_detection() -> None:
    candles = trending_synthetic_data(bars=120)
    cutoff = candles.get_column("time")[99]
    past = candles.filter(pl.col("time") <= cutoff)
    future = candles.filter(pl.col("time") > cutoff).with_columns(
        (pl.col("high") * 10.0).alias("high"),
        (pl.col("low") * 0.1).alias("low"),
        (pl.col("close") * 5.0).alias("close"),
    )
    extended = pl.concat([past, future])
    builder = FeatureBuilder(EmberConfig())
    features_past = builder.add_features(past.lazy()).collect()
    features_extended = (
        builder.add_features(extended.lazy()).collect().filter(pl.col("time") <= cutoff)
    )
    columns = [
        "atr",
        "volume_ratio",
        "swing_high",
        "swing_low",
        "bos_choch",
        "fvg",
        "pda_position",
    ]
    assert features_past.select(columns).tail(1).to_dicts() == features_extended.select(columns).tail(1).to_dicts()

    row = features_past.tail(1).row(0, named=True)
    context = MTFContext(
        symbol=str(row["symbol"]),
        time=row["time"],
        bias="bear",
        regime="trend",
        pda_position=float(row["pda_position"]),
        session="ny",
        htf_liquidity_swept=True,
        htf_poi_active=True,
        htf_structure="downtrend",
        volume_ratio=float(row["volume_ratio"]),
        atr=float(row["atr"]),
    )
    detector = SetupDetector(EmberConfig(allowed_direction_contexts=("bear",)))
    first = detector.detect(features_past, context)
    second = detector.detect(features_extended.filter(pl.col("time") <= cutoff), context)
    assert first == second


def test_exit_simulation_uses_only_future() -> None:
    entry_time = datetime(2024, 1, 1, 0, 30, tzinfo=UTC)
    plan = RiskPlan(
        symbol="DOGEUSDT",
        side="long",
        entry=100.0,
        stop=99.0,
        target=101.8,
        target_rr=1.8,
        risk_amount=100.0,
        position_size=100.0,
        notional=10_000.0,
        margin=500.0,
        leverage=20.0,
        setup_type="pullback",
        entry_time=entry_time,
        fee_cost=0.002,
        slippage_cost=0.0004,
        net_edge=0.0056,
        grade="B",
    )
    future = pl.DataFrame(
        {
            "symbol": ["DOGEUSDT", "DOGEUSDT"],
            "time": [entry_time + timedelta(minutes=15), entry_time + timedelta(minutes=30)],
            "open": [100.0, 100.5],
            "high": [102.0, 103.0],
            "low": [99.8, 100.0],
            "close": [101.5, 102.0],
            "volume": [1.0, 1.0],
        }
    )
    result = ExitSimulator().simulate(plan, future)
    assert result is not None
    assert result.exit_time == entry_time + timedelta(minutes=15)
    assert result.exit_time > entry_time


def test_structure_learning_no_lookahead() -> None:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    trades = [
        _trade(1, base, base + timedelta(hours=1), 1.0),
        _trade(2, base + timedelta(minutes=30), base + timedelta(hours=1, minutes=30), -1.0),
        _trade(3, base + timedelta(hours=1), None, None, status="open"),
    ]
    score = StructureGate().score(
        trade_id=99,
        symbol="DOGEUSDT",
        setup_type="pullback",
        side="short",
        regime="trend",
        entry_time=base + timedelta(minutes=30),
        all_trades=trades,
    )
    assert score.consistency_score == 50.0


def test_no_placeholder_results() -> None:
    config = EmberConfig(allowed_direction_contexts=("bear",))
    plan = RiskPlan(
        symbol="DOGEUSDT",
        side="short",
        entry=100.0,
        stop=101.0,
        target=98.2,
        target_rr=1.8,
        risk_amount=100.0,
        position_size=100.0,
        notional=10_000.0,
        margin=500.0,
        leverage=20.0,
        setup_type="pullback",
        entry_time=datetime(2024, 1, 1, tzinfo=UTC),
        fee_cost=0.002,
        slippage_cost=0.0004,
        net_edge=0.0056,
        grade="B",
    )
    assert ExitSimulator(config).simulate(plan, pl.DataFrame()) is None

    flat = _flat_candles(80)
    result = Backtester(config).run(flat)
    assert result.metrics.num_trades == 0


def test_pf_no_division_by_zero() -> None:
    assert profit_factor([1.0, 2.0, 0.5]) == 99.0


def test_ohlc_validation() -> None:
    time = datetime(2024, 1, 1, tzinfo=UTC)
    frame = pl.DataFrame(
        {
            "symbol": ["DOGEUSDT", "DOGEUSDT"],
            "time": [time, time + timedelta(minutes=15)],
            "open": [10.0, 10.0],
            "high": [11.0, 8.0],
            "low": [9.0, 9.0],
            "close": [10.5, 10.0],
            "volume": [1.0, 1.0],
        }
    )
    validated = DataEngine.validate(frame.lazy()).collect()
    assert validated.height == 1


@given(
    open_price=st.floats(min_value=1.0, max_value=10_000.0, allow_nan=False, allow_infinity=False),
    move=st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
)
def test_valid_ohlc_survives_property_validation(open_price: float, move: float) -> None:
    close = open_price + move / 4.0
    frame = pl.DataFrame(
        {
            "symbol": ["XUSDT"],
            "time": [datetime(2024, 1, 1, tzinfo=UTC)],
            "open": [open_price],
            "high": [max(open_price, close) + move],
            "low": [min(open_price, close) - min(move, open_price * 0.5)],
            "close": [close],
            "volume": [0.0],
        }
    )
    assert DataEngine.validate(frame.lazy()).collect().height == 1


def _trade(
    trade_id: int,
    entry_time: datetime,
    exit_time: datetime | None,
    result_r: float | None,
    status: str = "closed",
) -> Trade:
    return Trade(
        id=trade_id,
        symbol="DOGEUSDT",
        side="short",
        setup_type="pullback",
        entry_time=entry_time,
        exit_time=exit_time,
        entry_price=100.0,
        stop_price=101.0,
        target_price=98.2,
        planned_rr=1.8,
        result_r=result_r,
        exit_reason="take_profit" if result_r and result_r > 0 else "stop_loss",
        bars_held=1,
        mfe_r=1.0,
        mae_r=-0.5,
        status=status,  # type: ignore[arg-type]
        regime="trend",
        confidence=70.0,
        quality_grade="B",
        structure_grade="B",
        risk_amount=100.0,
    )


def _flat_candles(bars: int) -> pl.DataFrame:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    return pl.DataFrame(
        {
            "symbol": ["DOGEUSDT"] * bars,
            "time": [start + timedelta(minutes=15 * index) for index in range(bars)],
            "open": [100.0] * bars,
            "high": [100.1] * bars,
            "low": [99.9] * bars,
            "close": [100.0] * bars,
            "volume": [100.0] * bars,
        }
    )
