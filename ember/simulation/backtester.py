"""Event-driven, zero-look-ahead backtest pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import polars as pl

from ember.config import EmberConfig
from ember.core.context_builder import ContextBuilder
from ember.core.data_engine import DataEngine
from ember.core.features import FeatureBuilder
from ember.filters.quality_gate import QualityGate
from ember.filters.structure_gate import StructureGate
from ember.models import (
    BacktestMetrics,
    BacktestResult,
    MTFContext,
    SetupCandidate,
    Trade,
)
from ember.simulation.portfolio import PortfolioSimulator
from ember.strategy.exit_simulator import ExitSimulator
from ember.strategy.risk_engine import RiskEngine
from ember.strategy.setups import SetupDetector
from ember.utils import ensure_utc, profit_factor, safe_mean


@dataclass(frozen=True, slots=True)
class _CandidateEvent:
    symbol: str
    row_index: int
    time: datetime
    candidate: SetupCandidate
    context: MTFContext


class Backtester:
    def __init__(self, config: EmberConfig | None = None) -> None:
        self.config = config or EmberConfig()
        self.features = FeatureBuilder(self.config)
        self.contexts = ContextBuilder(self.config)
        self.setups = SetupDetector(self.config)
        self.risk = RiskEngine(self.config)
        self.exits = ExitSimulator(self.config)
        self.quality = QualityGate()
        self.structure = StructureGate()
        self.last_diagnostics = self._new_diagnostics()

    def run(
        self,
        candles: pl.DataFrame | pl.LazyFrame,
        initial_equity: float = 10_000.0,
        initial_history: list[Trade] | None = None,
        diagnostics: bool = False,
    ) -> BacktestResult:
        rejects = self._new_diagnostics()
        self.last_diagnostics = rejects

        lazy = candles.lazy() if isinstance(candles, pl.DataFrame) else candles
        validated = DataEngine.validate(lazy)
        entry_frame = self.features.add_features(validated).collect()
        if entry_frame.is_empty():
            if diagnostics:
                self.print_diagnostics()
            return self._empty_result(initial_equity)

        htf_frames = {
            timeframe: self.features.add_features(
                DataEngine.resample(validated, self.config.entry_tf, timeframe)
            ).collect()
            for timeframe in self.config.context_tfs
            if timeframe != self.config.entry_tf
        }
        symbol_frames = {
            symbol: entry_frame.filter(pl.col("symbol") == symbol).sort("time")
            for symbol in entry_frame.get_column("symbol").unique().to_list()
        }
        events = self._find_candidate_events(symbol_frames, htf_frames, rejects)
        portfolio = PortfolioSimulator(initial_equity, self.config)
        history = list(initial_history or [])
        executed: list[Trade] = []
        equity_curve: list[tuple[datetime, float]] = []
        next_available_time: datetime | None = None

        for event in sorted(events, key=lambda item: (item.time, item.symbol)):
            if portfolio.state.halted:
                rejects["halted"] += 1
                break
            if next_available_time is not None and event.time < next_available_time:
                rejects["overlap_reject"] += 1
                continue

            frame = symbol_frames[event.symbol]
            plan, risk_reason = self.risk.plan_with_reason(
                event.candidate,
                event.context,
                portfolio.state.equity,
            )
            if plan is None:
                rejects[risk_reason or "risk_none"] += 1
                continue

            trade_id = len(history) + len(executed) + 1
            quality = self.quality.score(trade_id, event.candidate, event.context)
            if quality.grade == "D":
                rejects["quality_reject"] += 1
                continue

            structure = self.structure.score(
                trade_id=trade_id,
                symbol=event.symbol,
                setup_type=event.candidate.setup_type,
                side=event.candidate.side,
                regime=event.context.regime,
                entry_time=event.time,
                all_trades=[*history, *executed],
                lookback_days=self.config.wfo_lookback_days,
            )
            if structure.grade == "D":
                rejects["structure_reject"] += 1
                continue

            future = frame.slice(event.row_index + 1)
            simulated = self.exits.simulate(plan, future)
            if simulated is None:
                rejects["no_future"] += 1
                continue

            cost_r = (plan.fee_cost + plan.slippage_cost) * plan.notional / plan.risk_amount
            net_result_r = simulated.result_r - cost_r
            mfe_r, mae_r = self._excursions(plan, future, simulated.exit_time)
            trade = Trade(
                id=trade_id,
                symbol=event.symbol,
                side=event.candidate.side,
                setup_type=event.candidate.setup_type,
                entry_time=event.time,
                exit_time=simulated.exit_time,
                entry_price=plan.entry,
                stop_price=plan.stop,
                target_price=plan.target,
                planned_rr=plan.target_rr,
                result_r=net_result_r,
                exit_reason=simulated.exit_reason,
                bars_held=simulated.bars_held,
                mfe_r=mfe_r,
                mae_r=mae_r,
                status="closed",
                regime=event.context.regime,
                confidence=event.candidate.confidence,
                quality_grade=quality.grade,
                structure_grade=structure.grade,
                risk_amount=plan.risk_amount,
            )
            if not portfolio.open_trade(trade):
                rejects["portfolio_reject"] += 1
                continue
            portfolio.close_trade(trade)
            executed.append(trade)
            rejects["executed"] += 1
            equity_curve.append((simulated.exit_time, portfolio.state.equity))
            next_available_time = simulated.exit_time

        metrics = self._metrics(initial_equity, portfolio.state.equity, executed, equity_curve)
        if diagnostics:
            self.print_diagnostics()
        return BacktestResult(trades=executed, metrics=metrics, equity_curve=equity_curve)

    def _find_candidate_events(
        self,
        symbol_frames: dict[str, pl.DataFrame],
        htf_frames: dict[str, pl.DataFrame],
        rejects: dict[str, int],
    ) -> list[_CandidateEvent]:
        events: list[_CandidateEvent] = []
        for symbol, frame in symbol_frames.items():
            for row_index in range(60, frame.height):
                rejects["bars_seen"] += 1
                past = frame.slice(0, row_index + 1)
                row = past.tail(1).row(0, named=True)
                time = row["time"]
                if not isinstance(time, datetime):
                    raise TypeError("time must be a datetime")
                context = self.contexts.build_at(
                    symbol=symbol,
                    entry_time=time,
                    entry_row=row,
                    htf_frames=htf_frames,
                )
                candidate, reason = self.setups.detect_with_reason(past, context)
                if candidate is None:
                    rejects[reason or "no_setup"] += 1
                    continue
                rejects["candidate_passed"] += 1
                events.append(
                    _CandidateEvent(
                        symbol=symbol,
                        row_index=row_index,
                        time=ensure_utc(time),
                        candidate=candidate,
                        context=context,
                    )
                )
        return events

    def print_diagnostics(self) -> None:
        print("=== REJECT DIAGNOSTICS ===")
        for key, value in self.last_diagnostics.items():
            print(f"  {key}: {value}")

    @staticmethod
    def _new_diagnostics() -> dict[str, int]:
        return {
            "bars_seen": 0,
            "neutral_context": 0,
            "direction_reject": 0,
            "regime_reject": 0,
            "no_setup": 0,
            "setup_blocked": 0,
            "confidence_low": 0,
            "volume_low": 0,
            "candidate_passed": 0,
            "risk_none": 0,
            "rr_low": 0,
            "cost_gate": 0,
            "quality_reject": 0,
            "structure_reject": 0,
            "no_future": 0,
            "overlap_reject": 0,
            "portfolio_reject": 0,
            "halted": 0,
            "executed": 0,
        }

    @staticmethod
    def _excursions(
        plan: object,
        future: pl.DataFrame,
        exit_time: datetime,
    ) -> tuple[float, float]:
        relevant = future.filter(pl.col("time") <= pl.lit(exit_time))
        if relevant.is_empty():
            return 0.0, 0.0
        entry = float(getattr(plan, "entry"))
        stop = float(getattr(plan, "stop"))
        side = str(getattr(plan, "side"))
        risk_distance = abs(entry - stop)
        if risk_distance <= 0:
            return 0.0, 0.0
        highest = float(relevant.get_column("high").max())
        lowest = float(relevant.get_column("low").min())
        if side == "long":
            return (highest - entry) / risk_distance, (lowest - entry) / risk_distance
        return (entry - lowest) / risk_distance, (entry - highest) / risk_distance

    @staticmethod
    def _metrics(
        initial_equity: float,
        final_equity: float,
        trades: list[Trade],
        equity_curve: list[tuple[datetime, float]],
    ) -> BacktestMetrics:
        results = [float(trade.result_r) for trade in trades if trade.result_r is not None]
        peak = initial_equity
        max_drawdown = 0.0
        for _, equity in equity_curve:
            peak = max(peak, equity)
            if peak > 0:
                max_drawdown = max(max_drawdown, (peak - equity) / peak * 100.0)
        return BacktestMetrics(
            total_return=(final_equity - initial_equity) / initial_equity * 100.0,
            profit_factor=profit_factor(results),
            max_drawdown=max_drawdown,
            win_rate=(sum(result > 0 for result in results) / len(results) * 100.0)
            if results
            else 0.0,
            avg_trade=safe_mean(results),
            num_trades=len(results),
            final_equity=final_equity,
        )

    @staticmethod
    def _empty_result(initial_equity: float) -> BacktestResult:
        return BacktestResult(
            trades=[],
            metrics=BacktestMetrics(
                total_return=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                avg_trade=0.0,
                num_trades=0,
                final_equity=initial_equity,
            ),
            equity_curve=[],
        )
