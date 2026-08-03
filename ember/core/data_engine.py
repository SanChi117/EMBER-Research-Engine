"""Lazy OHLCV ingestion, validation and resampling."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import polars as pl

from ember.utils import timeframe_to_minutes

REQUIRED_COLUMNS = ("symbol", "time", "open", "high", "low", "close", "volume")


class DataEngine:
    """Load and normalize OHLCV without materializing large CSV files."""

    @staticmethod
    def load_csv(path: Path) -> pl.LazyFrame:
        if not path.exists():
            raise FileNotFoundError(path)
        lazy = pl.scan_csv(path, try_parse_dates=True, infer_schema_length=10_000)
        return DataEngine._normalize_schema(lazy)

    @staticmethod
    def _normalize_schema(lf: pl.LazyFrame) -> pl.LazyFrame:
        names = lf.collect_schema().names()
        rename_map = {name: name.strip().lower() for name in names}
        lf = lf.rename(rename_map)
        names = lf.collect_schema().names()
        aliases = {
            "timestamp": "time",
            "datetime": "time",
            "date": "time",
            "open_time": "time",
            "ticker": "symbol",
            "asset": "symbol",
            "vol": "volume",
        }
        for source, target in aliases.items():
            if source in names and target not in names:
                lf = lf.rename({source: target})
                names = lf.collect_schema().names()

        missing = [column for column in REQUIRED_COLUMNS if column not in names]
        if missing:
            raise ValueError(f"missing required OHLCV columns: {missing}")

        schema = lf.collect_schema()
        time_dtype = schema["time"]
        if time_dtype == pl.String:
            lf = lf.with_columns(
                pl.col("time")
                .str.to_datetime(strict=False, time_zone="UTC")
                .alias("time")
            )
        elif time_dtype in {
            pl.Int8,
            pl.Int16,
            pl.Int32,
            pl.Int64,
            pl.UInt8,
            pl.UInt16,
            pl.UInt32,
            pl.UInt64,
        }:
            # Binance open times are milliseconds. Values below 10^12 are treated as seconds.
            lf = lf.with_columns(
                pl.when(pl.col("time").abs() >= 1_000_000_000_000)
                .then(pl.from_epoch(pl.col("time"), time_unit="ms"))
                .otherwise(pl.from_epoch(pl.col("time"), time_unit="s"))
                .dt.replace_time_zone("UTC")
                .alias("time")
            )
        elif time_dtype == pl.Date:
            lf = lf.with_columns(pl.col("time").cast(pl.Datetime("us", "UTC")))
        elif isinstance(time_dtype, pl.Datetime) and time_dtype.time_zone is None:
            lf = lf.with_columns(pl.col("time").dt.replace_time_zone("UTC"))

        return lf.with_columns(
            pl.col("symbol").cast(pl.String).str.to_uppercase(),
            *(pl.col(column).cast(pl.Float64) for column in REQUIRED_COLUMNS[2:]),
        ).select(REQUIRED_COLUMNS)

    @staticmethod
    def validate(lf: pl.LazyFrame) -> pl.LazyFrame:
        """Filter malformed bars and deterministically deduplicate by symbol/time."""

        normalized = DataEngine._normalize_schema(lf)
        valid = (
            pl.col("symbol").is_not_null()
            & pl.col("time").is_not_null()
            & pl.col("open").is_finite()
            & pl.col("high").is_finite()
            & pl.col("low").is_finite()
            & pl.col("close").is_finite()
            & pl.col("volume").is_finite()
            & (pl.col("high") >= pl.max_horizontal("open", "close"))
            & (pl.col("low") <= pl.min_horizontal("open", "close"))
            & (pl.col("high") >= pl.col("low"))
            & (pl.col("volume") >= 0)
        )
        return (
            normalized.filter(valid)
            .sort(["symbol", "time"])
            .unique(subset=["symbol", "time"], keep="last", maintain_order=True)
        )

    @staticmethod
    def resample(
        lf: pl.LazyFrame,
        from_tf: str,
        to_tf: str,
    ) -> pl.LazyFrame:
        """Resample OHLCV while preserving symbol boundaries.

        ``from_tf`` is validated to prevent accidental downsampling in the wrong direction.
        """

        from_minutes = timeframe_to_minutes(from_tf)
        to_minutes = timeframe_to_minutes(to_tf)
        if to_minutes < from_minutes:
            raise ValueError("resample only supports equal or higher timeframes")
        if to_minutes % from_minutes != 0:
            raise ValueError("target timeframe must be an integer multiple of source timeframe")

        validated = DataEngine.validate(lf)
        return (
            validated.sort(["symbol", "time"])
            .group_by_dynamic(
                index_column="time",
                every=to_tf,
                period=to_tf,
                group_by="symbol",
                closed="left",
                label="left",
            )
            .agg(
                pl.col("open").first().alias("open"),
                pl.col("high").max().alias("high"),
                pl.col("low").min().alias("low"),
                pl.col("close").last().alias("close"),
                pl.col("volume").sum().alias("volume"),
            )
            .drop_nulls(["open", "high", "low", "close"])
            .sort(["symbol", "time"])
        )

    @staticmethod
    def fetch_binance(
        symbols: list[str],
        interval: str,
        limit: int,
    ) -> pl.DataFrame:
        """Fetch public klines with retry and endpoint fallback.

        No API key is accepted or required. Binance Vision spot data is attempted first;
        Binance Futures public ``fapi`` is the fallback. HTTP 451 always moves to Vision.
        """

        if not 1 <= limit <= 1500:
            raise ValueError("limit must be between 1 and 1500")
        timeframe_to_minutes(interval)
        frames: list[pl.DataFrame] = []
        for raw_symbol in symbols:
            symbol = raw_symbol.upper().strip()
            if not symbol:
                continue
            rows = DataEngine._fetch_symbol(symbol, interval, limit)
            frames.append(DataEngine._klines_to_frame(symbol, rows))
            time.sleep(0.05)
        if not frames:
            return pl.DataFrame(schema={
                "symbol": pl.String,
                "time": pl.Datetime("ms", "UTC"),
                "open": pl.Float64,
                "high": pl.Float64,
                "low": pl.Float64,
                "close": pl.Float64,
                "volume": pl.Float64,
            })
        return pl.concat(frames, how="vertical").sort(["symbol", "time"])

    @staticmethod
    def _fetch_symbol(symbol: str, interval: str, limit: int) -> list[list[Any]]:
        endpoints = (
            "https://data-api.binance.vision/api/v3/klines",
            "https://fapi.binance.com/fapi/v1/klines",
        )
        last_error: Exception | None = None
        for endpoint in endpoints:
            for attempt, delay in enumerate((1.0, 2.0, 4.0), start=1):
                query = urlencode({"symbol": symbol, "interval": interval, "limit": limit})
                request = Request(
                    f"{endpoint}?{query}",
                    headers={"User-Agent": "EMBER-Research-Engine/0.2.0"},
                )
                try:
                    with urlopen(request, timeout=20) as response:  # noqa: S310
                        payload = json.loads(response.read().decode("utf-8"))
                    if not isinstance(payload, list):
                        raise ValueError(f"unexpected Binance response: {payload!r}")
                    return payload
                except HTTPError as error:
                    last_error = error
                    if error.code == 451:
                        break
                    if attempt < 3:
                        time.sleep(delay)
                except (URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
                    last_error = error
                    if attempt < 3:
                        time.sleep(delay)
            # Move to fallback endpoint after retries or HTTP 451.
        raise RuntimeError(f"failed to fetch {symbol} from Binance public endpoints") from last_error

    @staticmethod
    def _klines_to_frame(symbol: str, rows: list[list[Any]]) -> pl.DataFrame:
        records = [
            {
                "symbol": symbol,
                "time": int(row[0]),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
            }
            for row in rows
            if len(row) >= 6
        ]
        if not records:
            return pl.DataFrame(schema={
                "symbol": pl.String,
                "time": pl.Datetime("ms", "UTC"),
                "open": pl.Float64,
                "high": pl.Float64,
                "low": pl.Float64,
                "close": pl.Float64,
                "volume": pl.Float64,
            })
        return pl.DataFrame(records).with_columns(
            pl.from_epoch(pl.col("time"), time_unit="ms")
            .dt.replace_time_zone("UTC")
            .alias("time")
        )
