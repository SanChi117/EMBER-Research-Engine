"""Deterministic synthetic candles for sanity checks, not profitability claims."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import polars as pl


def trending_synthetic_data(
    bars: int = 1000,
    symbol: str = "DOGEUSDT",
    start_price: float = 500.0,
    start_time: datetime | None = None,
) -> pl.DataFrame:
    """Create a deterministic bearish trend used by narrow unit tests."""

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
                "source_regime": "trend_down",
            }
        )
        price = close_price
    return pl.DataFrame(rows).drop("source_regime")


def mixed_regime_synthetic_data(
    bars: int = 5000,
    symbol: str = "DOGEUSDT",
    start_price: float = 100.0,
    start_time: datetime | None = None,
    seed: int = 42,
    regime_bars: int = 500,
) -> pl.DataFrame:
    """Create reproducible trend, range and high-volatility regimes.

    Trend segments contain repeatable displacement/pullback structures. Some
    cycles deliberately reverse after the trigger area so the backtest must
    observe both winning and losing outcomes. Randomness is seeded and is only
    used to avoid an unrealistically identical candle stream.
    """

    if bars < 500:
        raise ValueError("bars must be at least 500")
    if regime_bars < 100:
        raise ValueError("regime_bars must be at least 100")
    if start_price <= 0:
        raise ValueError("start_price must be positive")

    rng = random.Random(seed)
    start_time = start_time or datetime(2024, 1, 1, tzinfo=timezone.utc)
    regimes = ("trend_up", "trend_down", "range", "high_vol")
    rows: list[dict[str, object]] = []
    price = start_price
    range_anchor = start_price

    for index in range(bars):
        regime_index = index // regime_bars
        regime = regimes[regime_index % len(regimes)]
        local_index = index % regime_bars
        if local_index == 0:
            range_anchor = price

        open_price = price
        phase = local_index % 20
        cycle = regime_index * max(1, regime_bars // 20) + local_index // 20
        change, volume = _regime_change(
            regime=regime,
            phase=phase,
            cycle=cycle,
            price=price,
            range_anchor=range_anchor,
            rng=rng,
        )
        close_price = max(1.0, open_price * (1.0 + change))

        base_wick = 0.0015 if regime != "high_vol" else 0.006
        upper_wick = abs(rng.gauss(base_wick, base_wick * 0.45))
        lower_wick = abs(rng.gauss(base_wick, base_wick * 0.45))
        if phase == 12 and regime == "trend_up":
            lower_wick += 0.008
        elif phase == 12 and regime == "trend_down":
            upper_wick += 0.008

        high = max(open_price, close_price) * (1.0 + upper_wick)
        low = min(open_price, close_price) * max(0.01, 1.0 - lower_wick)
        rows.append(
            {
                "symbol": symbol,
                "time": start_time + timedelta(minutes=15 * index),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close_price,
                "volume": max(100.0, volume),
                "source_regime": regime,
            }
        )
        price = close_price

    return pl.DataFrame(rows)


def _regime_change(
    regime: str,
    phase: int,
    cycle: int,
    price: float,
    range_anchor: float,
    rng: random.Random,
) -> tuple[float, float]:
    if regime in {"trend_up", "trend_down"}:
        sign = 1.0 if regime == "trend_up" else -1.0
        noise = rng.gauss(0.0, 0.00035)
        if phase <= 6:
            change = sign * 0.0004 + noise
            volume = rng.gauss(850.0, 80.0)
        elif phase == 7:
            change = sign * 0.018 + noise
            volume = rng.gauss(2300.0, 180.0)
        elif phase == 8:
            change = sign * 0.011 + noise
            volume = rng.gauss(1450.0, 130.0)
        elif phase <= 11:
            change = -sign * 0.010 + noise
            volume = rng.gauss(920.0, 90.0)
        elif phase == 12:
            change = sign * 0.003 + noise
            volume = rng.gauss(1400.0, 120.0)
        elif phase == 13 and cycle % 4 == 0:
            change = -sign * 0.035 + noise
            volume = rng.gauss(2100.0, 180.0)
        else:
            change = sign * 0.002 + noise
            volume = rng.gauss(900.0, 90.0)
        return change, volume

    if regime == "range":
        distance = (range_anchor - price) / max(range_anchor, 1e-12)
        change = distance * 0.12 + rng.gauss(0.0, 0.0035)
        return change, rng.gauss(1000.0, 220.0)

    change = max(-0.07, min(0.07, rng.gauss(0.0, 0.022)))
    return change, rng.gauss(1800.0, 500.0)
