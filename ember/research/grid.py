"""Small deterministic parameter-grid research runner."""

from __future__ import annotations

from itertools import product
from typing import Iterable

import polars as pl

from ember.config import EmberConfig
from ember.simulation.backtester import Backtester


class ParameterGridResearch:
    def run(
        self,
        candles: pl.DataFrame | pl.LazyFrame,
        base_config: EmberConfig,
        min_confidences: Iterable[float],
        min_rrs: Iterable[float],
        atr_multipliers: Iterable[float],
        initial_equity: float = 10_000.0,
    ) -> list[dict[str, float | int]]:
        rows: list[dict[str, float | int]] = []
        for confidence, rr, atr_multiplier in product(
            min_confidences,
            min_rrs,
            atr_multipliers,
        ):
            config = base_config.model_copy(
                update={
                    "min_confidence": float(confidence),
                    "min_rr": float(rr),
                    "atr_stop_multiplier": float(atr_multiplier),
                }
            )
            result = Backtester(config).run(candles, initial_equity=initial_equity)
            rows.append(
                {
                    "min_confidence": float(confidence),
                    "min_rr": float(rr),
                    "atr_stop_multiplier": float(atr_multiplier),
                    "total_return": round(result.metrics.total_return, 6),
                    "profit_factor": round(result.metrics.profit_factor, 6),
                    "max_drawdown": round(result.metrics.max_drawdown, 6),
                    "num_trades": result.metrics.num_trades,
                }
            )
        return sorted(rows, key=lambda row: (float(row["total_return"]), float(row["profit_factor"])), reverse=True)
