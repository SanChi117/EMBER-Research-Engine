"""Purged walk-forward validation with an embargo between train and test."""

from __future__ import annotations

from datetime import datetime, timedelta

import polars as pl

from ember.config import EmberConfig
from ember.models import WFOFold, WFOSummary
from ember.simulation.backtester import Backtester
from ember.utils import ensure_utc, safe_mean, timeframe_to_minutes


class WalkForwardValidator:
    def __init__(self, config: EmberConfig | None = None) -> None:
        self.config = config or EmberConfig()

    def run(
        self,
        candles: pl.DataFrame | pl.LazyFrame,
        initial_equity: float = 10_000.0,
        test_days: int | None = None,
    ) -> WFOSummary:
        lazy = candles.lazy() if isinstance(candles, pl.DataFrame) else candles
        bounds = (
            lazy.select(
                pl.col("time").min().alias("start_time"),
                pl.col("time").max().alias("end_time"),
            )
            .collect()
            .row(0)
        )
        start, end = bounds
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            return self._empty()
        start = ensure_utc(start)
        end = ensure_utc(end)
        total_days = max(1, int((end - start).total_seconds() / 86400.0))
        if test_days is None:
            available = total_days - self.config.wfo_lookback_days
            test_days = max(1, available // max(1, self.config.wfo_folds + 1))

        bar_duration = timedelta(minutes=timeframe_to_minutes(self.config.entry_tf))
        embargo = bar_duration * self.config.wfo_embargo_bars
        folds: list[WFOFold] = []
        for index in range(self.config.wfo_folds):
            train_start = start + timedelta(days=index * test_days)
            train_end = train_start + timedelta(days=self.config.wfo_lookback_days)
            test_start = train_end + embargo
            test_end = test_start + timedelta(days=test_days)
            if test_end > end:
                break

            train = lazy.filter(
                (pl.col("time") >= pl.lit(train_start))
                & (pl.col("time") < pl.lit(train_end))
            ).collect()
            test = lazy.filter(
                (pl.col("time") >= pl.lit(test_start))
                & (pl.col("time") < pl.lit(test_end))
            ).collect()
            if train.is_empty() or test.is_empty():
                continue

            backtester = Backtester(self.config)
            train_result = backtester.run(train, initial_equity=initial_equity)
            test_result = backtester.run(
                test,
                initial_equity=initial_equity,
                initial_history=train_result.trades,
            )
            metrics = test_result.metrics
            folds.append(
                WFOFold(
                    fold=index + 1,
                    train_start=train_start,
                    train_end=train_end,
                    test_start=test_start,
                    test_end=test_end,
                    return_pct=metrics.total_return,
                    profit_factor=metrics.profit_factor,
                    max_drawdown=metrics.max_drawdown,
                    num_trades=metrics.num_trades,
                    positive=metrics.total_return > 0,
                )
            )

        if not folds:
            return self._empty()
        avg_return = safe_mean(fold.return_pct for fold in folds)
        avg_pf = safe_mean(fold.profit_factor for fold in folds)
        worst_dd = max(fold.max_drawdown for fold in folds)
        stability_score = sum(fold.positive for fold in folds) / len(folds) * 100.0
        passed = stability_score >= 70.0 and avg_pf >= 1.5 and worst_dd < 10.0 and avg_return > 0
        return WFOSummary(
            folds=folds,
            avg_return=avg_return,
            avg_pf=avg_pf,
            worst_dd=worst_dd,
            stability_score=stability_score,
            pass_fail="PASS" if passed else "FAIL",
        )

    @staticmethod
    def _empty() -> WFOSummary:
        return WFOSummary(
            folds=[],
            avg_return=0.0,
            avg_pf=0.0,
            worst_dd=0.0,
            stability_score=0.0,
            pass_fail="FAIL",
        )
