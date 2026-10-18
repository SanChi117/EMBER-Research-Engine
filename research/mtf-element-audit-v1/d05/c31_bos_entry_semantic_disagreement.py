"""C31 BOS mechanism disagreement: first wick crossing vs first CLOSED 3m BOS.

Never infer tick-level fill, live trade, author-approved BOS, author timeframe
timezone, or FTA from 3m OHLC. Observed original C21 events are RESEARCH
PROXIES. Other public ICT examples are ANALOGS, not instructor goldens.
Author's own 1H/3m Notion annotated backtest source is unavailable.
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from c21b_original_3m_raid_break_geometry import (
    ThreeBreak,observe_native3m_raid_break,_source,THREE)
from c25_session_freshness_target_source import inspect_c25

@dataclass(frozen=True)
class BOSWitness:
    symbol:str
    pivot_center_ms:int
    raid_start_ms:int
    raid_confirmed_ms:int
    selected_3m_swing_center_ms:int
    selected_3m_swing_known_ms:int
    swing_price:str
    research_break_start_ms:int
    research_break_close_known_ms:int
    research_break_original3m_row_id:str
    side:str
    raid_fractal_level:str
    raid_extreme:str
    strictly_bos_side_of_raid_fractal:bool
    first_earlier_wick_cross_ms:int|None
    first_earlier_wick_cross_source_row_id:str|None
    earlier_wick_cross_count:int
    earlier_wick_without_confirmed_bos_count:int
    lag_raid_confirmed_to_break_minutes:int
    preceding_calendar_day_hypotheses:tuple[tuple[str,bool],...]
    academic_bos_pivot_status:str="AUTHOR_SELECTED_BOS_PIVOT_UNKNOWN"
    author_entry_status:str="MARKET_CROSS_VS_CLOSE_OR_LIMIT_UNKNOWN"
    author_fta_status:str="AUTHOR_FTA_TP_PRIORITY_UNKNOWN"
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class SourceAudit:
    symbol:str
    as_of_ms:int
    source_original3m_closed:int
    strict_closed_3m_research_edges:int
    research_single_case_count:int
    proxy_raid_fractal_bos_order_pass:int
    edges_with_prior_strict_wick_cross:int
    prior_strict_wick_cross_observations:int
    edges_with_prior_wick_without_close_confirmation:int
    break_at_raid_confirmation_hour_count:int
    break_later_than_3h_after_raid_confirmation:int
    previous_calendar_day_hypotheses:tuple[tuple[str,int],...]
    cases:tuple[BOSWitness,...]
    author_annotated_1h3m_goldens:int=0
    author_approved_trades:int=0
    readiness:str="NOT_TRADE_READY"

ZONES=("UTC","Europe/Kyiv","Europe/London")

def _strict_side(kind, price, level):
    return price<level if kind=="SHORT" else price>level

def _prior_first_wicks(event,rows):
    """Previously closed 3m bars; selected pivot is retrospective research key."""
    begin=max(event.raid_confirmed_ms,event.swing.known_ms)
    if begin>event.break_start_ms:
        raise ValueError("C31_RESEARCH_SWING_NOT_KNOWN_BEFORE_BREAK")
    previous=[]
    missed=[]
    last=-1
    for x in rows:
        if x.start_ms>=event.break_start_ms:break
        if x.start_ms<begin:continue
        if x.start_ms<=last or x.known_ms>x.start_ms+THREE:
            raise ValueError("C31_INVALID_3M_SOURCE_ORDER")
        last=x.start_ms
        if x.known_ms>event.break_start_ms:
            raise ValueError("C31_FUTURE_PREBREAK_BAR")
        wick=_strict_side(event.side,x.low if event.side=="SHORT" else x.high,event.swing.level)
        close=_strict_side(event.side,x.close,event.swing.level)
        if wick:
            previous.append(x)
            if not close:missed.append(x)
    return tuple(previous),tuple(missed)

def _previous_calendar_day(event,zone):
    tz=ZoneInfo(zone)
    a=datetime.fromtimestamp(event.pivot_center_ms/1000,timezone.utc).astimezone(tz)
    b=datetime.fromtimestamp(event.raid_start_ms/1000,timezone.utc).astimezone(tz)
    return (b.date()-a.date()).days==1

def audit_single_bos(event,rows):
    """C21 original event plus _source-gated 3m rows only, never invent BOS."""
    if not isinstance(event,ThreeBreak) or not isinstance(rows,tuple):
        raise ValueError("C31_UNTRUSTED_EVENT_OR_SOURCE_ROWS")
    if (event.side not in ("SHORT","LONG")
        or (event.side=="SHORT" and event.pivot_kind!="BSL")
        or (event.side=="LONG" and event.pivot_kind!="SSL")
        or (event.side=="SHORT" and event.swing.kind!="LOW")
        or (event.side=="LONG" and event.swing.kind!="HIGH")):
        raise ValueError("C31_BAD_RAID_OR_BOS_SIDE")
    points=(event.raid_extreme,event.raid_level,event.swing.level,event.break_close)
    if any(type(p)!=Decimal or not p.is_finite() or p<=0 for p in points):
        raise ValueError("C31_INVALID_DECIMAL_PRICE")
    if (event.pivot_center_ms>=event.raid_start_ms
        or event.raid_confirmed_ms<=event.raid_start_ms
        or event.swing.center_ms<event.raid_start_ms
        or event.swing.known_ms>event.break_start_ms
        or event.break_start_ms<event.raid_confirmed_ms
        or event.break_known_ms!=event.break_start_ms+THREE):
        raise ValueError("C31_FUTURE_OR_NONCAUSAL_EVENT")
    if not rows:
        raise ValueError("C31_EMPTY_CLOSED_SOURCE")
    if any(type(t)!=int for t in (event.break_start_ms,event.break_known_ms,event.raid_confirmed_ms)):
        raise ValueError("C31_BAD_EVENT_TIMESTAMPS")
    last=next((r for r in rows if r.start_ms==event.break_start_ms),None)
    if (last is None or last.raw_id!=event.source_original_3m_row_id
        or last.known_ms!=event.break_known_ms or last.close!=event.break_close):
        raise ValueError("C31_3M_ORIGINAL_SOURCE_ROW_MISMATCH")
    if (not _strict_side(event.side,event.swing.level,event.raid_level)
        or not _strict_side(event.side,event.break_close,event.swing.level)
        or (event.side=="SHORT" and event.raid_extreme<=event.raid_level)
        or (event.side=="LONG" and event.raid_extreme>=event.raid_level)):
        raise ValueError("C31_NO_STRICT_BOS_OR_WICK_RAID_GEOMETRY")
    prior,missed=_prior_first_wicks(event,rows)
    first=prior[0] if prior else None
    lag=(event.break_start_ms-event.raid_confirmed_ms)//60000
    return BOSWitness(
        rows[0].symbol,event.pivot_center_ms,event.raid_start_ms,
        event.raid_confirmed_ms,event.swing.center_ms,event.swing.known_ms,
        str(event.swing.level),event.break_start_ms,event.break_known_ms,
        event.source_original_3m_row_id,event.side,str(event.raid_level),
        str(event.raid_extreme),True,
        first.start_ms if first else None,first.raw_id if first else None,
        len(prior),len(missed),lag,
        tuple((zone,_previous_calendar_day(event,zone)) for zone in ZONES))

def inspect_c31_bos(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    prev=inspect_c25(source,as_of_ms=as_of_ms)
    observations=observe_native3m_raid_break(source,as_of_ms=as_of_ms)
    casekeys={(x.raid_fractal_ms,x.raid_ms,x.break_ms,x.original_source_row_id)
              for x in prev.cases}
    if len(casekeys)!=prev.research_single_parent_cases:
        raise ValueError("C31_DUPLICATE_PREVIOUS_SINGLETON_CASES")
    existing={(e.pivot_center_ms,e.raid_start_ms,e.break_start_ms,e.source_original_3m_row_id)
              for e in observations.potential_breaks}
    if len(existing)!=len(observations.potential_breaks) or not casekeys.issubset(existing):
        raise ValueError("C31_C25_JOIN_OR_RESEARCH_PARENT_DRIFT")
    result=tuple(audit_single_bos(e,rows) for e in observations.potential_breaks)
    if len(result)!=prev.original_parent_edges:
        raise ValueError("C31_539_PARENT_EDGE_DRIFT")
    n0=sum(x.lag_raid_confirmed_to_break_minutes==0 for x in result)
    zones=tuple((z,sum(dict(x.preceding_calendar_day_hypotheses)[z] for x in result)) for z in ZONES)
    return SourceAudit(source.symbol,as_of_ms,len(rows),len(result),
        len(casekeys),sum(x.strictly_bos_side_of_raid_fractal for x in result),
        sum(x.earlier_wick_cross_count>0 for x in result),
        sum(x.earlier_wick_cross_count for x in result),
        sum(x.earlier_wick_without_confirmed_bos_count>0 for x in result),
        n0,sum(x.lag_raid_confirmed_to_break_minutes>180 for x in result),
        zones,result)
