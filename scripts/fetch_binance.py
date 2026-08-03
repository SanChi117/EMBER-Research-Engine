from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import polars as pl

from ember.core.data_engine import DataEngine
from ember.utils import timeframe_to_minutes

_ENDPOINTS = (
    "https://data-api.binance.vision/api/v3/klines",
    "https://fapi.binance.com/fapi/v1/klines",
)


def fetch_history(symbol: str, interval: str, limit: int) -> pl.DataFrame:
    """Download more than one Binance API page without API keys."""

    if limit <= 0:
        raise ValueError("limit must be positive")
    timeframe_to_minutes(interval)
    symbol = symbol.upper().strip()
    if not symbol:
        raise ValueError("symbol must not be empty")

    rows_by_open_time: dict[int, list[Any]] = {}
    end_time: int | None = None
    previous_earliest: int | None = None
    while len(rows_by_open_time) < limit:
        batch_limit = min(1000, limit - len(rows_by_open_time))
        batch = _request_klines(symbol, interval, batch_limit, end_time)
        if not batch:
            break
        for row in batch:
            if len(row) >= 6:
                rows_by_open_time[int(row[0])] = row
        earliest = min(int(row[0]) for row in batch)
        if previous_earliest == earliest:
            break
        previous_earliest = earliest
        end_time = earliest - 1
        time.sleep(0.12)

    ordered = [rows_by_open_time[key] for key in sorted(rows_by_open_time)]
    ordered = ordered[-limit:]
    frame = DataEngine._klines_to_frame(symbol, ordered)  # noqa: SLF001
    return DataEngine.validate(frame.lazy()).collect()


def _request_klines(
    symbol: str,
    interval: str,
    limit: int,
    end_time: int | None,
) -> list[list[Any]]:
    params: dict[str, Any] = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }
    if end_time is not None:
        params["endTime"] = end_time

    last_error: Exception | None = None
    for endpoint in _ENDPOINTS:
        for attempt, delay in enumerate((1.0, 2.0, 4.0), start=1):
            request = Request(
                f"{endpoint}?{urlencode(params)}",
                headers={"User-Agent": "EMBER-Research-Engine/0.2.0"},
            )
            try:
                with urlopen(request, timeout=30) as response:  # noqa: S310
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
    raise RuntimeError(f"failed to fetch {symbol} history") from last_error


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch paginated public Binance klines")
    parser.add_argument("--symbols", required=True, help="comma-separated symbols")
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--out-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for raw_symbol in args.symbols.split(","):
        symbol = raw_symbol.strip().upper()
        if not symbol:
            continue
        frame = fetch_history(symbol, args.interval, args.limit)
        path = args.out_dir / f"{symbol}_{args.interval}_{args.limit}.csv"
        frame.write_csv(path)
        print(f"{symbol}: {frame.height} rows -> {path}")


if __name__ == "__main__":
    main()
