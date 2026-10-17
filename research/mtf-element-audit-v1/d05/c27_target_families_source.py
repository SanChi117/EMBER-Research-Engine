"""C27: source-family hypotheses for 1H TP/FTA, never author approval.

Primary-source families are (a) strict 1+1 BSL/SSL fractals, (b) >=2
same-side swing levels for EQH/EQL, (c) preceding-session high/low,
(d) FTA as an explicit UNKNOWN. Numeric near-equality tolerance and author
trading timezone/session semantics are ABSENT. Exact-price pairs are a
deliberately narrow witness, NOT all EQH/EQL and NOT a TP signal.
All 3 IANA calendars are experiments, not attributed to the instructor.
C21-C26 historical evidence is read-only. PAPER ONLY.
"""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta, time
from decimal import Decimal
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from c21b_original_3m_raid_break_geometry import _source,_hours
from c20b_hourly_fractal_source_observer import observe_fractals_and_first_breach
from c26_unswept_1h_fta_source import inspect_c26,level_history
from c25_session_freshness_target_source import ZONES

HOUR=3600000

@dataclass(frozen=True)
class ExactPairWitness:
    family: str
    level: str
    first_center_ms: int
    second_center_ms: int
    first_known_ms: int
    second_known_ms: int
    first_source_1h_row_id: str
    second_source_1h_row_id: str
    before_break_cross_state: str
    price_side: str
    status: str="EXACT_PRICE_PAIR_ONLY_AUTHOR_EQ_TOLERANCE_UNKNOWN"

@dataclass(frozen=True)
class PreviousSessionWitness:
    zone: str
    family: str
    local_previous_date: str
    observed_closed_1h_hours: int
    required_closed_1h_hours: int
    value: str|None
    known_ms: int|None
    source_1h_row_id: str|None
    research_price_side: str
    strict_prior_cross_state: str
    status: str="AUTHOR_TIMEZONE_SESSION_UNATTESTED"

@dataclass(frozen=True)
class Case:
    symbol: str
    raid_ms: int
    break_start_ms: int
    source_original3m_break_row_id: str
    side: str
    research_entry_close: str
    c26_initial_target_cross_state: str|None
    exact_price_pairs_on_research_side: tuple[ExactPairWitness,...]
    previous_calendar_scenarios: tuple[PreviousSessionWitness,...]
    has_any_exact_price_pair: bool
    session_scenario_value_disagreement: bool
    unknowns: tuple[str,...]
    readiness: str="NOT_TRADE_READY"
    author_target_approved: bool=False

@dataclass(frozen=True)
class Review:
    symbol: str
    as_of_ms: int
    original_parent_edges: int
    research_single_cases: int
    with_exact_price_pair_on_side: int
    exact_price_pairs_total: int
    with_session_scenario_disagreement: int
    incomplete_session_windows: int
    prior_target_crossed_by_c26: int
    cases: tuple[Case,...]
    author_approved_trades: int=0
    readiness: str="NOT_TRADE_READY"

def _known_same_price_pairs(pivots,side,entry,break_start_ms,rows):
    """Only EXACT Decimal pair witnesses. Never use ATR, tick or % tolerance."""
    if side not in ("LONG","SHORT") or not isinstance(entry,Decimal) or not entry.is_finite():
        raise ValueError("C27_INVALID_SIDE_OR_ENTRY")
    if type(break_start_ms)!=int:
        raise ValueError("C27_INVALID_BREAK_START")
    kind="BSL" if side=="LONG" else "SSL"
    grouped={}
    for p in pivots:
        if p.known_ms>break_start_ms or p.kind!=kind:
            continue
        if not (isinstance(p.level,Decimal) and p.level.is_finite()
                and p.source_rows and p.known_ms>p.center_ms):
            raise ValueError("C27_CORRUPTED_FRACTAL")
        if not (p.level>entry if side=="LONG" else p.level<entry):
            continue
        grouped.setdefault(p.level,[]).append(p)
    pairs=[]
    for level,group in grouped.items():
        group.sort(key=lambda p:(p.known_ms,p.center_ms))
        for a,b in zip(group,group[1:]):
            if a.center_ms==b.center_ms or a.known_ms>break_start_ms or b.known_ms>break_start_ms:
                raise ValueError("C27_EQ_PAIR_NOT_TWO_CONFIRMED_SWINGS")
            if not rows or rows[0].start_ms>b.known_ms:
                raise ValueError("C27_EQ_PAIR_PRICE_LINEAGE_MISSING")
            prior=level_history(a,rows,break_start_ms=break_start_ms)
            pairs.append(ExactPairWitness(
                "EXACT_1H_EQH_WITNESS" if kind=="BSL" else "EXACT_1H_EQL_WITNESS",
                str(level),a.center_ms,b.center_ms,a.known_ms,b.known_ms,
                a.source_rows[0],b.source_rows[0],prior.state,
                "LONG_ABOVE" if side=="LONG" else "SHORT_BELOW"))
    return tuple(sorted(pairs,key=lambda p:(abs(Decimal(p.level)-entry),p.second_center_ms)))

def _local_dt(ms,zone):
    return datetime.fromtimestamp(ms/1000,timezone.utc).astimezone(ZoneInfo(zone))

def previous_zone_extrema(hours,rows,*,zone,raid_ms,break_start_ms,side,entry):
    """Four independent author-UNATTESTED descriptions per IANA calendar.

    Local previous calendar day (24 complete 1H bars) and 09-17
    previous-day window (8 complete bars) are independent EXPERIMENTS.
    Their highs and lows are not automatically selected as trade targets.
    """
    if zone not in ZONES or side not in ("LONG","SHORT"):
        raise ValueError("C27_UNKNOWN_AUTHOR_TIMEZONE_OR_SIDE")
    if any(type(t)!=int for t in (raid_ms,break_start_ms)) or raid_ms>=break_start_ms:
        raise ValueError("C27_INVALID_TIMESTAMP")
    if not isinstance(entry,Decimal) or not entry.is_finite():
        raise ValueError("C27_BAD_ENTRY")
    prev_date=_local_dt(raid_ms,zone).date()-timedelta(days=1)
    z=ZoneInfo(zone)
    local_start=datetime.combine(prev_date,time.min,tzinfo=z)
    local_end=datetime.combine(prev_date+timedelta(days=1),time.min,tzinfo=z)
    required_calendar_hours=int((local_end.astimezone(timezone.utc)-
                                 local_start.astimezone(timezone.utc)).total_seconds()//3600)
    if required_calendar_hours not in (23,24,25):
        raise ValueError("C27_INVALID_IANA_DST_CALENDAR_DAY")
    previous=[h for h in hours if h.close_ms<=break_start_ms and
              _local_dt(h.start_ms,zone).date()==prev_date]
    out=[]
    for scope,window,required in (("PREVIOUS_LOCAL_DAY",previous,required_calendar_hours),
                                   ("PREVIOUS_LOCAL_09_17",
                                    [h for h in previous if 9<=_local_dt(h.start_ms,zone).hour<17],8)):
        # No 'completed session' from incomplete data, missing source or double counting.
        complete=(len(window)==required and
                  len({h.start_ms for h in window})==required and
                  all(h.close_ms-h.start_ms==HOUR and h.native_rows for h in window))
        for edge in ("HIGH","LOW"):
            family=scope+"_"+edge
            if not complete:
                out.append(PreviousSessionWitness(zone,family,prev_date.isoformat(),
                    len(window),required,None,None,None,"UNKNOWN_SOURCE_INCOMPLETE",
                    "UNKNOWN_SOURCE_INCOMPLETE"))
                continue
            best=max(window,key=lambda h:h.high) if edge=="HIGH" else min(window,key=lambda h:h.low)
            price=best.high if edge=="HIGH" else best.low
            known=max(h.close_ms for h in window)
            state=("ON_RESEARCH_SIDE" if ((price>entry if side=="LONG" else price<entry))
                   else "NOT_ON_RESEARCH_SIDE_OR_EQUAL")
            proxy=SimpleNamespace(kind="BSL" if edge=="HIGH" else "SSL",
                level=price,center_ms=best.start_ms,known_ms=known,
                source_rows=best.native_rows)
            history=level_history(proxy,rows,break_start_ms=break_start_ms)
            out.append(PreviousSessionWitness(zone,family,prev_date.isoformat(),
                len(window),required,str(price),known,best.native_rows[0],
                state,history.state))
    return tuple(out)

def inspect_c27(source,*,as_of_ms):
    """Explicit source family taxonomy grafted onto 165 C26 price-only cases."""
    rows=_source(source,as_of_ms)
    prior=inspect_c26(source,as_of_ms=as_of_ms)
    hours=_hours(rows)
    pivots,_=observe_fractals_and_first_breach(hours)
    output=[]
    for c in prior.cases:
        if c.readiness!="NOT_TRADE_READY" or c.author_approved:
            raise ValueError("C27_FORGED_C26_APPROVAL")
        entry=Decimal(c.research_entry_close)
        available=tuple(p for p in pivots if p.known_ms<=c.break_start_ms)
        # Strict prefix: no closed 3m bar from the breaking candle or later.
        causal_rows=rows[:(c.break_start_ms-rows[0].start_ms)//180000]
        pairs=_known_same_price_pairs(available,c.side,entry,c.break_start_ms,causal_rows)
        calendars=tuple(w for zone in ZONES for w in previous_zone_extrema(
            hours,causal_rows,zone=zone,raid_ms=c.raid_ms,
            break_start_ms=c.break_start_ms,side=c.side,entry=entry))
        if len(calendars)!=12:
            raise ValueError("C27_SCENARIO_CARDINALITY_DRIFT")
        signature={}
        for w in calendars:
            signature.setdefault(w.family,[]).append((w.value,w.local_previous_date))
        disagrees=any(len(set(v))>1 for v in signature.values())
        unknowns=("AUTHOR_EQ_TOLERANCE_UNKNOWN","AUTHOR_SESSION_TIMEZONE_DST_UNKNOWN",
                  "AUTHOR_PREVIOUS_SESSION_BOUNDARY_UNKNOWN","AUTHOR_FTA_RULE_UNKNOWN",
                  "AUTHOR_BOS_PIVOT_GOLDENS_UNKNOWN","AUTHOR_SL_BUFFER_UNKNOWN",
                  "TARGET_FAMILY_NOT_AUTHOR_SELECTED")
        output.append(Case(source.symbol,c.raid_ms,c.break_start_ms,
            c.break_original_row_id,c.side,c.research_entry_close,
            c.nearest_target_history.state if c.nearest_target_history else None,
            pairs,calendars,bool(pairs),disagrees,unknowns))
    cases=tuple(output)
    if len(cases)!=prior.research_single_cases:
        raise ValueError("C27_C26_CASE_COUNT_DRIFT")
    return Review(source.symbol,as_of_ms,prior.original_parent_edges,len(cases),
        sum(c.has_any_exact_price_pair for c in cases),
        sum(len(c.exact_price_pairs_on_research_side) for c in cases),
        sum(c.session_scenario_value_disagreement for c in cases),
        sum(w.value is None for c in cases for w in c.previous_calendar_scenarios),
        prior.nearest_target_already_crossed,cases)
