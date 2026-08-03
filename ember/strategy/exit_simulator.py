"""Future-only exit simulation with deterministic intra-candle paths."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import polars as pl

from ember.config import EmberConfig
from ember.models import RiskPlan, SimulatedExit
from ember.utils import ensure_utc, median_bar_minutes


class ExitSimulator:
    def __init__(self, config: EmberConfig | None = None) -> None:
        self.config = config or EmberConfig()

    def simulate(
        self,
        plan: RiskPlan,
        future_df: pl.DataFrame,
    ) -> SimulatedExit | None:
        """Simulate strictly from bars after ``plan.entry_time``.

        An empty or truncated future window is invalid and returns ``None``. No fallback
        result is fabricated.
        """

        if future_df.is_empty():
            return None
        future = future_df.filter(pl.col("time") > pl.lit(plan.entry_time)).sort("time")
        if future.is_empty():
            return None
        rows = future.to_dicts()
        times = [self._time(row) for row in rows]
        bar_minutes = median_bar_minutes(times, default=15)
        max_bars = max(1, int(self.config.max_holding_hours * 60 / bar_minutes))

        risk_distance = abs(plan.entry - plan.stop)
        if risk_distance <= 0:
            return None
        slipped_stop = (
            plan.stop - risk_distance * 0.02
            if plan.side == "long"
            else plan.stop + risk_distance * 0.02
        )

        for bars_held, row in enumerate(rows[:max_bars], start=1):
            hit = self._resolve_bar(plan, row)
            if hit is not None:
                reason, touched_price = hit
                if reason == "stop_loss":
                    open_price = float(row["open"])
                    if plan.side == "long":
                        exit_price = min(open_price, slipped_stop) if open_price <= plan.stop else slipped_stop
                    else:
                        exit_price = max(open_price, slipped_stop) if open_price >= plan.stop else slipped_stop
                else:
                    exit_price = touched_price
                return SimulatedExit(
                    exit_time=self._time(row),
                    exit_price=exit_price,
                    result_r=self._result_r(plan, exit_price),
                    exit_reason=reason,
                    bars_held=bars_held,
                )

            if bars_held == max_bars:
                exit_price = float(row["close"])
                return SimulatedExit(
                    exit_time=self._time(row),
                    exit_price=exit_price,
                    result_r=self._result_r(plan, exit_price),
                    exit_reason="time_stop",
                    bars_held=bars_held,
                )

        # The dataset ended before TP, SL or the configured time stop could be observed.
        return None

    def _resolve_bar(
        self,
        plan: RiskPlan,
        row: dict[str, Any],
    ) -> tuple[str, float] | None:
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])

        if plan.side == "long":
            if open_price <= plan.stop:
                return "stop_loss", open_price
            if open_price >= plan.target:
                return "take_profit", open_price
        else:
            if open_price >= plan.stop:
                return "stop_loss", open_price
            if open_price <= plan.target:
                return "take_profit", open_price

        if close > open_price:
            points = (open_price, low, high, close)  # OLHC
        elif close < open_price:
            points = (open_price, high, low, close)  # OHLC
        else:
            points = (open_price, high, low, close)  # neutral -> OHLC

        for start, end in zip(points, points[1:]):
            touched = self._first_touch_on_segment(plan, start, end)
            if touched is not None:
                return touched
        return None

    @staticmethod
    def _first_touch_on_segment(
        plan: RiskPlan,
        start: float,
        end: float,
    ) -> tuple[str, float] | None:
        minimum, maximum = sorted((start, end))
        candidates: list[tuple[float, str, float]] = []
        if minimum <= plan.stop <= maximum:
            candidates.append((abs(plan.stop - start), "stop_loss", plan.stop))
        if minimum <= plan.target <= maximum:
            candidates.append((abs(plan.target - start), "take_profit", plan.target))
        if not candidates:
            return None
        _, reason, price = min(candidates, key=lambda item: item[0])
        return reason, price

    @staticmethod
    def _result_r(plan: RiskPlan, exit_price: float) -> float:
        risk_distance = abs(plan.entry - plan.stop)
        if plan.side == "long":
            return (exit_price - plan.entry) / risk_distance
        return (plan.entry - exit_price) / risk_distance

    @staticmethod
    def _time(row: dict[str, Any]) -> datetime:
        value = row["time"]
        if not isinstance(value, datetime):
            raise TypeError("time must be a datetime")
        return ensure_utc(value)
