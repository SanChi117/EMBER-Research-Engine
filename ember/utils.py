"""Small deterministic utility functions."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from statistics import median
from typing import Iterable

_TIMEFRAME_RE = re.compile(r"^(?P<count>\d+)(?P<unit>[mhd])$")


def timeframe_to_minutes(value: str) -> int:
    """Convert Binance-style ``15m``, ``4h`` or ``1d`` to minutes."""

    match = _TIMEFRAME_RE.fullmatch(value.lower())
    if not match:
        raise ValueError(f"unsupported timeframe: {value}")
    count = int(match.group("count"))
    unit = match.group("unit")
    multiplier = {"m": 1, "h": 60, "d": 1440}[unit]
    return count * multiplier


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def bounded(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def safe_mean(values: Iterable[float], default: float = 0.0) -> float:
    materialized = [float(value) for value in values]
    return sum(materialized) / len(materialized) if materialized else default


def profit_factor(result_rs: Iterable[float]) -> float:
    """Return a finite PF, capped at 99 when no losing trades exist."""

    values = [float(value) for value in result_rs if math.isfinite(float(value))]
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = abs(sum(value for value in values if value < 0))
    if gross_loss == 0:
        return 99.0 if gross_profit > 0 else 0.0
    return min(99.0, gross_profit / gross_loss)


def median_bar_minutes(times: list[datetime], default: int = 15) -> int:
    if len(times) < 2:
        return default
    deltas = [
        max(1.0, (ensure_utc(right) - ensure_utc(left)).total_seconds() / 60.0)
        for left, right in zip(times, times[1:])
    ]
    return max(1, int(round(median(deltas))))
