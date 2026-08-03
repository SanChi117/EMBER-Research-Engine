"""Deterministic synthetic candles for sanity checks, not profitability claims."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import polars as pl


def trending_synthetic_data(
    bars: int = 1000,
    symbol: str = "DOGEUSDT",
    start_price: float = 500.0,
    start_time: datetime | None = None,
) -> pl.DataFrame:
    """Create a slow bearish trend with repeatable impulse/pullback cycles.

    Each 20-bar cycle contains compression, a bearish displacement and
    continuation, a retracement into premium, a rejection candle and another
    continuation. The construction is deterministic and exists only to
    exercise the complete research pipeline; it is not evidence of live
    profitability.
    """

    if bars < 100:
        raise ValueError("bars must be at least 100")
    start_time = start_time or datetime(2024, 1, 1, tzinfo=timezone.utc)
    price = start_price
    rows: list[dict[str, object]] = []
    for index in range(bars):
        phase = index % 20
        open_price = price
        if phase <= 6:
            change = -0.0003
            volume = 850.0
        elif phase == 7:
            change = -0.018
            volume = 2200.0
        elif phase == 8:
            change = -0.012
            volume = 1200.0
        elif phase <= 11:
            change = 0.014
            volume = 950.0
        elif phase == 12:
            change = -0.003
            volume = 1350.0
        else:
            change = -0.002
            volume = 900.0

        close_price = max(5.0, open_price * (1.0 + change))
        if phase in {7, 8}:
            high = open_price * 1.0005
            low = close_price * 0.998
        elif phase == 12:
            high = open_price * 1.008
            low = close_price * 0.998
        else:
            high = max(open_price, close_price) * 1.0005
            low = min(open_price, close_price) * 0.9995

        rows.append(
            {
                "symbol": symbol,
                "time": start_time + timedelta(minutes=15 * index),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close_price,
                "volume": volume,
            }
        )
        price = close_price
    return pl.DataFrame(rows)
