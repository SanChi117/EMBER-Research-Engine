"""Turn externally produced original-executor records into identical trace schemas.

Adapters DO NOT run/replace Freqtrade, Pine or original code: caller must supply
actual result files exported by those runtimes with pinned versions.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any,Mapping,Sequence
import csv,json

from .research import TraceRow,ObservedTrade,diff_traces


def _timestamp(value: Any) -> int:
    if isinstance(value,bool):
        raise ValueError('bad timestamp')
    if isinstance(value,(int,float)):
        if value<0:
            raise ValueError('negative timestamp')
        return int(value/1000 if value>=10**12 else value)
    if not isinstance(value,str) or not value.strip():
        raise ValueError('empty time')
    raw=value.strip().replace('Z','+00:00')
    try:
        stamp=datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError('timestamp must be ISO 8601 or UTC epoch') from exc
    if stamp.tzinfo is None:
        raise ValueError('UTC offset required; no silent timezone assumption')
    return int(stamp.astimezone(timezone.utc).timestamp())


def normalized_signal_rows(rows:Sequence[Mapping[str,Any]], *,source:str,fields:Mapping[str,str]|None=None)->list[TraceRow]:
    """Z04/Z33/Z38: explicit header map, fails closed on unknown fields.

    Default names: decision_at, symbol, side, entry, stop, target.
    Can map TV/Pine/Freqtrade custom export columns without changing engine code.
    """
    if not source:
        raise ValueError('pinned original executor source required')
    names={'decision_at':'decision_at','symbol':'symbol','side':'side','entry':'entry','stop':'stop','target':'target'}
    names.update(fields or {})
    output=[]
    for row in rows:
        def read(field):
            key=names[field]
            if key not in row:
                raise ValueError('missing column: '+key)
            return row[key]
        side=str(read('side')).strip().lower()
        if side in ('buy','long','1'):
            side='long'
        elif side in ('sell','short','-1'):
            side='short'
        elif side in ('none','flat','0'):
            side='none'
        else:
            raise ValueError('unrecognized original signal direction')
        def price(field):
            x=read(field)
            return None if x in ('',None) else float(x)
        output.append(TraceRow(_timestamp(read('decision_at')),str(read('symbol')).upper(),side,
                               price('entry'),price('stop'),price('target'),source))
    return output


def trade_report_rows(rows:Sequence[Mapping[str,Any]], *,source:str,
                      symbols_key:str='pair',time_key:str='close_date',
                      pnl_key:str='profit_abs')->list[ObservedTrade]:
    """Z31/Z35: Freqtrade-like completed trades as ObservedTrade.

    This is a schema converter only. Some exporters report profit in base coin
    or omit funding: caller must confirm USDT monetary units beforehand.
    """
    if not source:
        raise ValueError('source identity required')
    report=[]
    for i,row in enumerate(rows):
        if any(k not in row for k in (symbols_key,time_key,pnl_key)):
            raise ValueError('trade CSV missing required columns')
        trade_id=str(row.get('trade_id',row.get('id',f'{source}:{i}')))
        report.append(ObservedTrade(trade_id,str(row[symbols_key]).upper().replace('/',''),source,
                                    float(row[pnl_key]),_timestamp(row[time_key]),
                                    str(row.get('enter_tag',row.get('setup','unknown')))))
    return report


def read_csv_rows(path:str|Path, *,max_bytes:int=25_000_000)->list[dict[str,str]]:
    p=Path(path)
    if not p.exists() or p.stat().st_size>max_bytes:
        raise ValueError('CSV missing or too large')
    with p.open('r',encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def parity_from_exports(original_rows:Sequence[Mapping[str,Any]],other_rows:Sequence[Mapping[str,Any]], *,
                        original_source:str,challenger_source:str,
                        original_fields:Mapping[str,str]|None=None,
                        challenger_fields:Mapping[str,str]|None=None,
                        price_tolerance:float=1e-8)->dict[str,Any]:
    """Z38: from two actual exported signal streams to fully disclosed diff."""
    a=normalized_signal_rows(original_rows,source=original_source,fields=original_fields)
    b=normalized_signal_rows(other_rows,source=challenger_source,fields=challenger_fields)
    differences=diff_traces(a,b,price_abs_tolerance=price_tolerance)
    return {'parity':not differences,'n_original':len(a),'n_challenger':len(b),
            'differences':differences,'original_source':original_source,'challenger_source':challenger_source}
