"""Read-only Binance USD-M historical source adapter with injectable HTTP transport.

The client never places orders, requests account data or falls back to spot data.
Each returned record keeps source time and a caller-pinned availability lag.
No claim is made that a guessed publication lag equals real exchange delivery.
Historical order-book queues are not available through these public endpoints.
"""
from __future__ import annotations

from dataclasses import dataclass
from json import loads
from typing import Any, Callable, Mapping
from urllib.parse import urlencode
from urllib.request import urlopen

from .binance import parse_funding, parse_kline, parse_oi, parse_book_ticker
from .types import Candle, Evidence
from .market import Book

BASE = 'https://fapi.binance.com'
KLINE_INTERVAL = {'1m':60,'3m':180,'5m':300,'15m':900,'30m':1800,'1h':3600,'2h':7200,'4h':14400,'6h':21600,'8h':28800,'12h':43200,'1d':86400,'3d':259200,'1w':604800}
OI_INTERVAL = {'5m','15m','30m','1h','2h','4h','6h','12h','1d'}

class SourceUnavailable(RuntimeError):
    """Required exchange history cannot be obtained; do not substitute spot or interpolate."""

class InvalidSource(ValueError):
    """Malformed, out-of-order or inconsistent Binance public record."""


def _http_get(path: str, params: Mapping[str, Any], timeout: float) -> Any:
    url = BASE + path + '?' + urlencode(params)
    with urlopen(url, timeout=timeout) as response:
        return loads(response.read(15_000_000).decode('utf-8'))


@dataclass
class BinanceUSDMPublic:
    """Dependency-injected source for deterministic tests and read-only research.

    transport(path, params, timeout) must return decoded JSON; its provenance
    remains the caller's responsibility. Exchange data may be geoblocked.
    """
    transport: Callable[[str, Mapping[str, Any], float], Any] = _http_get
    timeout: float = 8.0
    max_pages: int = 40

    def __post_init__(self) -> None:
        if not 0 < self.timeout <= 120 or not 1 <= self.max_pages <= 500:
            raise ValueError('invalid client limits')

    @staticmethod
    def symbol(symbol: str) -> str:
        value = symbol.strip().upper()
        if len(value) < 5 or len(value) > 20 or not value.isalnum() or not value.endswith('USDT'):
            raise ValueError('explicit USDT-M symbol required')
        return value

    def _query(self, path: str, **params: Any) -> Any:
        allowed = {'/fapi/v1/klines','/fapi/v1/markPriceKlines','/fapi/v1/fundingRate','/futures/data/openInterestHist','/fapi/v1/premiumIndex','/fapi/v1/depth','/fapi/v1/ticker/bookTicker'}
        if path not in allowed:
            raise ValueError('unsupported read-only endpoint')
        try:
            result = self.transport(path, params, self.timeout)
        except Exception as exc:
            raise SourceUnavailable(f'{path}: {type(exc).__name__}: {exc}') from exc
        if isinstance(result, Mapping) and 'code' in result and 'msg' in result:
            raise SourceUnavailable(f'{path}: {result["code"]} {result["msg"]}')
        return result

    def _paged(self, path: str, symbol: str, start_ms: int, end_ms: int, *, limit: int, **extra: Any) -> list[Any]:
        if not 0 <= start_ms < end_ms or limit < 1 or limit > 1500:
            raise ValueError('invalid historical window/limit')
        cursor = start_ms
        rows: list[Any] = []
        seen: set[int] = set()
        for _ in range(self.max_pages):
            page = self._query(path, symbol=self.symbol(symbol), startTime=cursor, endTime=end_ms, limit=limit, **extra)
            if not isinstance(page, list):
                raise InvalidSource('Binance response is not an array')
            if not page:
                break
            prev_key = cursor-1
            for row in page:
                if path.endswith('fundingRate'):
                    key = int(row['fundingTime'])
                elif path.endswith('openInterestHist'):
                    key = int(row['timestamp'])
                else:
                    key = int(row[0])
                if key < prev_key:
                    raise InvalidSource('exchange page out of order')
                prev_key = key
                if start_ms <= key <= end_ms and key not in seen:
                    seen.add(key)
                    rows.append(row)
            next_cursor = prev_key + 1
            if next_cursor <= cursor:
                raise InvalidSource('non-advancing pagination')
            if next_cursor > end_ms or len(page) < limit:
                break
            cursor = next_cursor
        else:
            raise SourceUnavailable('pagination exceeds configured max_pages; request a smaller window')
        return rows

    def klines(self, symbol: str, interval: str, start_ms: int, end_ms: int, *, publish_lag_ms: int = 1000, mark: bool = False) -> list[Candle]:
        if interval not in KLINE_INTERVAL or publish_lag_ms < 0:
            raise ValueError('unsupported interval/lag')
        path = '/fapi/v1/markPriceKlines' if mark else '/fapi/v1/klines'
        rows = self._paged(path, symbol, start_ms, end_ms, limit=1000, interval=interval)
        candles = [parse_kline(row, publish_lag_ms=publish_lag_ms) for row in rows]
        # Request may include a final unfinished candle; caller must pass an as-of cutoff.
        return candles

    def klines_with_taker(self, symbol: str, interval: str, start_ms: int, end_ms: int, *, publish_lag_ms: int = 1000) -> list[tuple[Candle,float]]:
        """Z22: closed futures OHLCV and taker-buy BASE volume from the SAME row.

        Mark-price klines lack volume, so they cannot be used for taker pressure.
        """
        if interval not in KLINE_INTERVAL or publish_lag_ms < 0:
            raise ValueError('unsupported interval/lag')
        rows=self._paged('/fapi/v1/klines',symbol,start_ms,end_ms,limit=1000,interval=interval)
        result=[]
        for row in rows:
            if len(row)<11:
                raise InvalidSource('missing futures taker volume field')
            bar=parse_kline(row,publish_lag_ms=publish_lag_ms)
            buy=float(row[9])
            if not 0<=buy<=bar.volume:
                raise InvalidSource('invalid futures taker-buy base asset volume')
            result.append((bar,buy))
        return result

    def funding(self, symbol: str, start_ms: int, end_ms: int, *, publication_lag_ms: int) -> list[Evidence]:
        if publication_lag_ms < 0:
            raise ValueError('publication lag required')
        return [parse_funding(row, publication_lag_ms=publication_lag_ms) for row in self._paged('/fapi/v1/fundingRate',symbol,start_ms,end_ms,limit=1000)]

    def oi(self, symbol: str, period: str, start_ms: int, end_ms: int, *, publication_lag_ms: int) -> list[Evidence]:
        if period not in OI_INTERVAL or publication_lag_ms < 0:
            raise ValueError('invalid OI period/lag')
        # API only provides a rolling recent horizon (historically ~30 days).
        # If the requested window is outside retention, callers must provide
        # separately archived OI or mark the feature blocked.
        return [parse_oi(row, publication_lag_ms=publication_lag_ms) for row in self._paged('/futures/data/openInterestHist',symbol,start_ms,end_ms,limit=500,period=period)]

    def best_book(self, symbol: str, *, received_ms: int) -> Book:
        row = self._query('/fapi/v1/ticker/bookTicker', symbol=self.symbol(symbol))
        if not isinstance(row, Mapping):
            raise InvalidSource('bookTicker is not an object')
        return parse_book_ticker(row, receive_ms=received_ms)

    def depth_now(self, symbol: str, *, limit: int = 100) -> Mapping[str, Any]:
        """Current L2 only. Historical order queue cannot be reconstructed."""
        if limit not in (5,10,20,50,100,500,1000):
            raise ValueError('unsupported depth limit')
        row=self._query('/fapi/v1/depth',symbol=self.symbol(symbol),limit=limit)
        if not isinstance(row,Mapping) or not {'bids','asks','lastUpdateId'} <= set(row):
            raise InvalidSource('invalid depth snapshot')
        return row
