"""Ready-to-call adapters from EMBER/SMOKE OHLCV frames to the spare library.

Inputs: list-of-dicts, pandas DataFrame, Polars DataFrame, Binance kline rows.
Uses duck typing; pandas/polars are optional and never imported here. No I/O.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Mapping, Sequence

from .binance import parse_klines
from .plugin import SpareInputError, invoke
from .types import Candle


def _seconds(value: Any) -> int:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise SpareInputError('naive datetime rejected; timestamp must carry UTC offset')
        return int(value.astimezone(timezone.utc).timestamp())
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise SpareInputError('timestamp must be aware datetime or numeric epoch')
    if value < 0:
        raise SpareInputError('negative timestamp')
    return int(value // 1000 if value >= 10**12 else value)


def _records(frame: Any) -> list[Any]:
    if isinstance(frame, list):
        return frame
    if hasattr(frame,'collect') and not hasattr(frame,'to_dicts'):
        frame = frame.collect()
    if hasattr(frame,'to_dicts'):
        return frame.to_dicts()
    if hasattr(frame,'to_dict'):
        try:
            return frame.to_dict('records')
        except (TypeError, ValueError):
            raise SpareInputError('DataFrame must support to_dict(records)') from None
    raise SpareInputError('expected list, pandas or Polars DataFrame')


def normalized_candles(frame: Any, *, timeframe_seconds: int | None=None,
                       time_is: str='open', publish_lag_seconds: int=0,
                       symbol: str | None=None) -> list[dict]:
    """Normalize raw price records into explicit closed bars.

    Timestamp `time`/`timestamp` is interpreted as OPEN unless `time_is='close'`;
    `close_time` field always takes precedence. Missing interval is an error.
    `publish_lag_seconds` models availability conservatively, never earlier
    than close. Result is JSON-ready for `invoke('Z16', {'candles': ...})`.
    """
    if publish_lag_seconds < 0 or (timeframe_seconds is not None and timeframe_seconds < 1):
        raise SpareInputError('invalid timeframe or publication delay')
    if time_is not in ('open','close'):
        raise SpareInputError('time_is must be open or close')
    rows = _records(frame)
    if not rows:
        return []
    symbols={str(r['symbol']) for r in rows if isinstance(r,Mapping) and 'symbol' in r}
    if symbol is not None:
        rows=[r for r in rows if isinstance(r,Mapping) and str(r.get('symbol')) == symbol]
        if not rows:
            raise SpareInputError(f'no rows for symbol {symbol}')
    elif len(symbols)>1:
        raise SpareInputError('multi-symbol frame: provide symbol explicitly to prevent cross-asset mixing')
    if isinstance(rows[0],(list,tuple)):
        return [asdict(c) for c in parse_klines(rows,publish_lag_ms=publish_lag_seconds*1000)]
    out=[]
    for row in rows:
        if not isinstance(row,Mapping):
            raise SpareInputError('row must be object')
        # A typed Candle already has fully explicit times: preserve original availability.
        if 'open_time' in row and 'close_time' in row and 'available_at' in row:
            c=Candle(_seconds(row['open_time']),_seconds(row['close_time']),*(float(row[k]) for k in ('open','high','low','close','volume')),_seconds(row['available_at']))
            out.append(asdict(c));continue
        if timeframe_seconds is None and 'close_time' not in row:
            raise SpareInputError('timeframe_seconds is required for raw rows')
        t=row.get('open_time',row.get('timestamp',row.get('date',row.get('time'))))
        if t is None:
            raise SpareInputError('missing candle timestamp')
        stamp=_seconds(t)
        if 'close_time' in row:
            close=_seconds(row['close_time'])
            start=stamp
        else:
            close=stamp + timeframe_seconds if time_is=='open' else stamp
            start=stamp if time_is=='open' else stamp-timeframe_seconds
        lagged=close+publish_lag_seconds
        c=Candle(start,close,*(float(row[k]) for k in ('open','high','low','close','volume')),lagged)
        out.append(asdict(c))
    out.sort(key=lambda c:c['open_time'])
    if len({x['open_time'] for x in out})!=len(out):
        raise SpareInputError('duplicate source candles')
    if any(b['open_time'] < a['close_time'] for a,b in zip(out,out[1:])):
        raise SpareInputError('overlapping source candles')
    return out


def run_on_candles(component_id: str, frame: Any, *, timeframe_seconds: int | None=None,
                   decision_at: int, candles_arg: str='candles', time_is: str='open',
                   publish_lag_seconds: int=0, symbol: str | None=None, **kwargs: Any) -> Any:
    """One-call adapter, e.g. run_on_candles('Z16', dataframe, timeframe_seconds=900, decision_at=...)."""
    candles=normalized_candles(frame,timeframe_seconds=timeframe_seconds,time_is=time_is,publish_lag_seconds=publish_lag_seconds,symbol=symbol)
    return invoke(component_id,{candles_arg:candles,**kwargs},decision_at=decision_at)
