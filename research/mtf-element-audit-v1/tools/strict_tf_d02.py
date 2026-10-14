#!/usr/bin/env python3
"""D02 v1: deterministic, point-in-time TF aggregation and pivot confirmation.

Separate from all trading signals. Relies on D01 bars and declared provenance;
does not prove exchange authenticity (D04), strategy semantics or profitability.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence
from strict_bar_closed import ClosedBar, D01Rejected, TF_MS, UTC_WEEK_ANCHOR_MS, utc_ms


class D02Rejected(ValueError):
    def __init__(self, code: str, detail: str = ''):
        self.code = code
        super().__init__(code + (': ' + detail if detail else ''))


@dataclass(frozen=True)
class SyncedBar:
    symbol: str
    timeframe: str
    open_at_ms: int
    close_exclusive_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source_timeframe: str
    child_count: int
    confirmed_at_ms: int


@dataclass(frozen=True)
class Snapshot:
    timeframe: str
    as_of_ms: int
    bars: tuple[SyncedBar, ...]
    leading_partial_buckets: int
    trailing_partial_buckets: int
    input_closed_bars: int
    ignored_future_bars: int


@dataclass(frozen=True)
class Pivot:
    side: str
    pivot_open_at_ms: int
    pivot_price: Decimal
    confirmed_at_ms: int
    confirmed_by_open_at_ms: int
    timeframe: str


def _anchor(tf):
    return UTC_WEEK_ANCHOR_MS if tf == '1w' else 0


def _start_at(t, tf):
    period = TF_MS[tf]
    anchor = _anchor(tf)
    return ((t - anchor) // period) * period + anchor


def _validate_bar(bar, tf, symbol, previous):
    """Validate even direct/manual bars, not only those instantiated by D01."""
    if bar.symbol != symbol or bar.timeframe != tf:
        raise D02Rejected('CHILD_IDENTITY_MISMATCH')
    if type(bar.open_at_ms) is not int or type(bar.close_exclusive_ms) is not int:
        raise D02Rejected('NONINTEGER_CHILD_TIME')
    p = TF_MS[tf]
    if (bar.open_at_ms - _anchor(tf)) % p != 0:
        raise D02Rejected('CHILD_OFF_GRID')
    if bar.close_exclusive_ms != bar.open_at_ms + p:
        raise D02Rejected('CHILD_CLOSE_MISMATCH')
    if previous is not None:
        if bar.open_at_ms <= previous.open_at_ms:
            raise D02Rejected('CHILD_UNSORTED_OR_DUPLICATE')
        if bar.open_at_ms != previous.close_exclusive_ms:
            raise D02Rejected('CHILD_GAP')
    if any(not isinstance(x, Decimal) or not x.is_finite() for x in (bar.open,bar.high,bar.low,bar.close,bar.volume)):
        raise D02Rejected('CHILD_BAD_DECIMAL')
    if (min(bar.open,bar.close,bar.high,bar.low) <= 0 or bar.volume < 0
            or bar.high < max(bar.open,bar.close,bar.low) or bar.low > min(bar.open,bar.close,bar.high)):
        raise D02Rejected('CHILD_INVALID_OHLCV')


def snapshot_htf(source_bars: Sequence[ClosedBar], target_tf: str, *, as_of_utc, expected_source_start_utc=None) -> Snapshot:
    """Aggregates only completely CLOSED parent buckets; never pads incomplete data.

    The future suffix is invisible to calculations as-of. Interior gaps/missing
    children are fatal; partial first/last parent buckets are excluded with
    explicit counts. Requires consecutive closed child bars in the as-of prefix.
    """
    if target_tf not in TF_MS:
        raise D02Rejected('UNKNOWN_TARGET')
    if not source_bars:
        raise D02Rejected('NO_SOURCE_BARS')
    child_tf = source_bars[0].timeframe
    if child_tf not in TF_MS or TF_MS[target_tf] <= TF_MS[child_tf]:
        raise D02Rejected('UNSUPPORTED_AGGREGATION')
    target_ms, child_ms = TF_MS[target_tf], TF_MS[child_tf]
    if target_ms % child_ms != 0:
        raise D02Rejected('INCOMMENSURATE_TIMEFRAMES')
    # Refuse 3m/5m substitution from 15m; only finer-to-coarser is supported.
    as_of = utc_ms(as_of_utc)
    first_symbol = source_bars[0].symbol
    # The first row cannot tell us whether prior rows were omitted. When full
    # source-range coverage is required, bind the first timestamp externally.
    if expected_source_start_utc is not None and source_bars[0].open_at_ms != utc_ms(expected_source_start_utc):
        raise D02Rejected('SOURCE_START_MISMATCH')
    closed: list[ClosedBar] = []
    previous = None
    for b in source_bars:
        # The as-of result cannot depend on any future bar, even its OHLC.
        if b.open_at_ms >= as_of:
            break
        if b.close_exclusive_ms > as_of:
            break
        _validate_bar(b, child_tf, first_symbol, previous)
        closed.append(b)
        previous = b
    if not closed:
        return Snapshot(target_tf,as_of,(),0,0,0,len(source_bars))
    # Reject silent late/missing child bars: the point-in-time input must extend
    # through the last child boundary closed by as_of. Otherwise a truncated
    # final parent could be falsely treated as an ordinary forming HTF candle.
    anchor_child=_anchor(child_tf)
    required_closed_until=((as_of-anchor_child)//child_ms)*child_ms+anchor_child
    if closed[-1].close_exclusive_ms != required_closed_until:
        raise D02Rejected('STALE_OR_MISSING_RECENT_CHILDREN')
    grouped: dict[int,list[ClosedBar]] = {}
    for b in closed:
        bucket = _start_at(b.open_at_ms, target_tf)
        grouped.setdefault(bucket, []).append(b)
    keys = sorted(grouped)
    if any(keys[k+1] != keys[k] + target_ms for k in range(len(keys)-1)):
        raise D02Rejected('MISSING_PARENT_BUCKET')
    aggregated=[]
    leading=trailing=0
    required=target_ms//child_ms
    for n,key in enumerate(keys):
        members=grouped[key]
        is_full=(len(members)==required and members[0].open_at_ms==key
                 and members[-1].close_exclusive_ms==key+target_ms)
        if not is_full:
            if n==0: leading+=1
            elif n==len(keys)-1: trailing+=1
            else: raise D02Rejected('INTERIOR_PARENT_INCOMPLETE')
            continue
        if key+target_ms>as_of:
            raise D02Rejected('PARENT_FUTURE_LEAK')
        aggregated.append(SyncedBar(first_symbol,target_tf,key,key+target_ms,
            members[0].open,max(b.high for b in members),min(b.low for b in members),
            members[-1].close,sum((b.volume for b in members),Decimal('0')),
            child_tf,len(members),key+target_ms))
    return Snapshot(target_tf,as_of,tuple(aggregated),leading,trailing,
                    len(closed),len(source_bars)-len(closed))


def native_snapshot(source_bars: Sequence[ClosedBar], *, as_of_utc) -> Snapshot:
    """Select already-final native bars without using unclosed current HTF."""
    if not source_bars:
        raise D02Rejected('NO_SOURCE_BARS')
    tf=source_bars[0].timeframe
    if tf not in TF_MS:
        raise D02Rejected('UNKNOWN_TARGET')
    as_of=utc_ms(as_of_utc)
    out=[];previous=None
    for b in source_bars:
        if b.open_at_ms>=as_of or b.close_exclusive_ms>as_of:break
        _validate_bar(b,tf,source_bars[0].symbol,previous)
        out.append(SyncedBar(b.symbol,tf,b.open_at_ms,b.close_exclusive_ms,b.open,
            b.high,b.low,b.close,b.volume,tf,1,b.close_exclusive_ms));previous=b
    if out:
        interval=TF_MS[tf];anchor=_anchor(tf)
        expected_last_close=((as_of-anchor)//interval)*interval+anchor
        if out[-1].close_exclusive_ms != expected_last_close:
            raise D02Rejected('STALE_NATIVE_HTF_HISTORY')
    return Snapshot(tf,as_of,tuple(out),0,0,len(out),len(source_bars)-len(out))


def confirmed_pivots(snapshot: Snapshot, *, left: int, right: int, as_of_utc=None) -> tuple[Pivot,...]:
    """A pivot at index i may be known ONLY after bar i+right closes.

    Strict comparisons discard equal-high/low ties, avoiding arbitrary
    'winner' choices. This is arithmetic confirmation, not IDM/Strong High.
    """
    if type(left) is not int or type(right) is not int or left<1 or right<1:
        raise D02Rejected('BAD_PIVOT_LOOKAROUND')
    as_of=snapshot.as_of_ms if as_of_utc is None else utc_ms(as_of_utc)
    if as_of>snapshot.as_of_ms:
        raise D02Rejected('ASOF_EXCEEDS_SNAPSHOT')
    out=[];bs=snapshot.bars
    for i in range(left,len(bs)-right):
        c=bs[i]; window=bs[i-left:i]+bs[i+1:i+right+1]
        confirmation=bs[i+right]
        if confirmation.close_exclusive_ms>as_of:continue
        if c.high>max(b.high for b in window):
            out.append(Pivot('HIGH',c.open_at_ms,c.high,confirmation.close_exclusive_ms,
                             confirmation.open_at_ms,snapshot.timeframe))
        if c.low<min(b.low for b in window):
            out.append(Pivot('LOW',c.open_at_ms,c.low,confirmation.close_exclusive_ms,
                             confirmation.open_at_ms,snapshot.timeframe))
    return tuple(out)
