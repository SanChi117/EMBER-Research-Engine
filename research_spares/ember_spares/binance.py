"""Explicit Binance USDT-M public data decoding; offline, no HTTP request.

All time inputs are milliseconds, all internal timestamps epoch seconds.
Historical publication delays MUST be supplied by caller. A candlestick's
closeTime (Binance interval close - 1ms) is normalized to the next second.
This reader handles standard Binance kline, funding and OI records.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

from .market import Book
from .types import Candle, Evidence


def _ms(value: Any) -> int:
    number = int(value)
    if number < 1_000_000_000_000 or number >= 100_000_000_000_000:
        raise ValueError('expected Binance Unix timestamp in milliseconds')
    return number


def _number(value: Any, label: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError(f'nonfinite {label}')
    return number


def parse_kline(row: Sequence[Any] | Mapping[str, Any], *, publish_lag_ms: int = 0) -> Candle:
    """Convert Binance HTTP 12-field OHLCV or WebSocket closed kline `k`.

    publish_lag_ms is the *assumed* delay after bar close. For a historical
    simulation specify the conservative documented feed delay; for live
    records supply original receive/arrival timestamps separately.
    """
    if publish_lag_ms < 0:
        raise ValueError('negative publication lag')
    if isinstance(row, Mapping):
        k = row.get('k', row)
        if not isinstance(k, Mapping):
            raise ValueError('invalid Binance kline object')
        if k.get('x') is not True:
            raise ValueError('WebSocket kline is not final')
        start, finish, o, h, lo, c, v = (k[x] for x in ('t', 'T', 'o', 'h', 'l', 'c', 'v'))
    else:
        if len(row) < 7:
            raise ValueError('too short Binance kline row')
        start, o, h, lo, c, v, finish = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
    start_ms, finish_ms = _ms(start), _ms(finish)
    if finish_ms <= start_ms:
        raise ValueError('inconsistent candle interval')
    # Binance closeTime ends in ...999. Normalize to the next full second.
    close_second = (finish_ms + 1 + 999) // 1000
    available_second = (finish_ms + 1 + publish_lag_ms + 999) // 1000
    return Candle(start_ms // 1000, close_second, _number(o, 'open'), _number(h, 'high'),
                  _number(lo, 'low'), _number(c, 'close'), _number(v, 'volume'), available_second)


def parse_klines(rows: Sequence[Sequence[Any] | Mapping[str, Any]], *, publish_lag_ms: int = 0) -> list[Candle]:
    output = [parse_kline(row, publish_lag_ms=publish_lag_ms) for row in rows]
    output.sort(key=lambda c: c.open_time)
    if len({c.open_time for c in output}) != len(output):
        raise ValueError('duplicate Binance candles')
    for a, b in zip(output, output[1:]):
        if b.open_time < a.close_time:
            raise ValueError('overlapping candles')
    return output


def parse_funding(row: Mapping[str, Any], *, publication_lag_ms: int, source: str = 'binance:funding') -> Evidence:
    """Use *explicit* publication latency; a funding settle time is not a guaranteed public timestamp."""
    if publication_lag_ms < 0:
        raise ValueError('funding release lag must be >=0')
    event_ms = _ms(row['fundingTime'])
    return Evidence(event_ms // 1000, (event_ms + publication_lag_ms + 999) // 1000,
                    _number(row['fundingRate'], 'fundingRate'), source)


def parse_oi(row: Mapping[str, Any], *, publication_lag_ms: int, source: str = 'binance:open_interest') -> Evidence:
    """OI aggregates require source-specific timestamp and explicit assumed delay."""
    if publication_lag_ms < 0:
        raise ValueError('OI release lag must be >=0')
    event_ms = _ms(row['timestamp'])
    volume = row.get('sumOpenInterest', row.get('openInterest'))
    if volume is None:
        raise ValueError('missing open interest')
    return Evidence(event_ms // 1000, (event_ms + publication_lag_ms + 999) // 1000,
                    _number(volume, 'open interest'), source)


def parse_book_ticker(row: Mapping[str, Any], *, receive_ms: int) -> Book:
    """BookTicker has no confirmed queue/depth, but can yield BBO microprice."""
    observed_ms = _ms(row.get('T', row.get('E', receive_ms)))
    received = _ms(receive_ms)
    if received < observed_ms:
        raise ValueError('received before exchange event')
    return Book(_number(row['b'], 'bid'), _number(row['a'], 'ask'),
                _number(row['B'], 'bid_qty'), _number(row['A'], 'ask_qty'),
                observed_ms // 1000, (received + 999) // 1000)
