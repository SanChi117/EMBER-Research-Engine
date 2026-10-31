"""Strict, UTC-epoch based shared types (seconds for all event timestamps)."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence


def finite(*numbers: float) -> None:
    if not all(isfinite(x) for x in numbers):
        raise ValueError("non-finite numeric input")


def positive(*numbers: float) -> None:
    finite(*numbers)
    if not all(x > 0 for x in numbers):
        raise ValueError("value must be > 0")


@dataclass(frozen=True)
class Candle:
    """One fully CLOSED candle. `available_at` is first possible signal time."""
    open_time: int
    close_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    available_at: int

    def __post_init__(self) -> None:
        positive(self.open, self.high, self.low, self.close)
        finite(self.volume)
        if self.volume < 0 or self.high < max(self.open, self.close, self.low) or self.low > min(self.open, self.close, self.high):
            raise ValueError("inconsistent OHLCV")
        if not (self.open_time < self.close_time <= self.available_at):
            raise ValueError("candle must be closed before availability")


@dataclass(frozen=True)
class Evidence:
    event_time: int
    available_at: int
    value: float
    source: str

    def __post_init__(self) -> None:
        finite(self.value)
        if self.available_at < self.event_time or not self.source:
            raise ValueError("invalid evidence")


def ascending(values: Sequence[float]) -> None:
    for a, b in zip(values, values[1:]):
        if b <= a:
            raise ValueError("timestamps must be strictly ascending")
