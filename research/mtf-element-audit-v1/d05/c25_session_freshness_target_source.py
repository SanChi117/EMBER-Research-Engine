"""C25 independent original 1H/3m session sensitivity and FTA/SL geometry.

Academic source: previous-session fresh fractal (at most preceding day);
Frankfurt ~09 to NY KZ ~17 author local clock UNKNOWN; previous session
is NOT a verified fixed UTC clock. 1H liquidity target, structural stop
beyond swept liquidity. No Binance-specific 15 FX pip threshold.
These three IANA timezone interpretations are EXPLICIT EXPERIMENTS,
never author session adjudication. Every output NOT_TRADE_READY.
"""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
from c21b_original_3m_raid_break_geometry import (
    _source,_hours,observe_native3m_raid_break)
from c20b_hourly_fractal_source_observer import observe_fractals_and_first_breach
from c24_bos_research_admission_gate import audit_route_admission

ZONES=("UTC","Europe/Kyiv","Europe/London")
HOUR=3600000

@dataclass(frozen=True)
class Scenario:
    zone:str
    raid_local_date:str
    raid_local_hour:int
    raid_local_utc_offset_minutes:int
    pivot_local_date:str
    pivot_local_hour:int
    pivot_local_utc_offset_minutes:int
    pivot_was_previous_local_day:bool
    pivot_in_previous_09_17_session:bool
    raid_in_local_09_17_window:bool
    status:str="HYPOTHESIS_ONLY_AUTHOR_TIMEZONE_UNAVAILABLE"

@dataclass(frozen=True)
class Case:
    symbol:str
    raid_ms:int
    raid_fractal_ms:int
    break_ms:int
    original_source_row_id:str
    side:str
    zones:tuple[Scenario,...]
    zones_disagree_on_previous_day:bool
    zones_disagree_on_previous_09_17_session:bool
    zones_disagree_on_raid_09_17:bool
    raid_extreme:str
    research_entry_close:str
    minimum_unbuffered_stop_distance:str
    nearest_preknown_opposing_1h_fractal_price:str|None
    nearest_opposing_1h_fractal_center_ms:int|None
    target_beyond_entry_geometrically:bool
    readiness:str="NOT_TRADE_READY"
    author_session_attested:bool=False
    author_fta_attested:bool=False
    author_stop_buffer_attested:bool=False
    author_approved_trade:bool=False

@dataclass(frozen=True)
class Review:
    symbol:str
    as_of_ms:int
    original_parent_edges:int
    research_single_parent_cases:int
    cases:tuple[Case,...]
    previous_day_timezone_disagreements:int
    previous_session_timezone_disagreements:int
    raid_window_timezone_disagreements:int
    no_geometric_preknown_opposing_1h_target:int
    nonpositive_unbuffered_stop_distance:int
    previous_local_day_by_scenario:tuple[tuple[str,int],...]
    previous_09_17_session_by_scenario:tuple[tuple[str,int],...]
    raid_in_09_17_by_scenario:tuple[tuple[str,int],...]
    author_approved_trades:int=0
    readiness:str="NOT_TRADE_READY"

def scenario(fractal_ms:int,raid_ms:int,zone:str)->Scenario:
    if zone not in ZONES or type(fractal_ms)!=int or type(raid_ms)!=int:
        raise ValueError("C25_UNATTESTED_ZONE_OR_TIMESTAMP")
    if fractal_ms>=raid_ms:
        raise ValueError("C25_FUTURE_PARENT_FRACTAL")
    tz=ZoneInfo(zone)
    fractal=datetime.fromtimestamp(fractal_ms/1000,timezone.utc).astimezone(tz)
    raid=datetime.fromtimestamp(raid_ms/1000,timezone.utc).astimezone(tz)
    previous=raid.date()-timedelta(days=1)
    same_prev=fractal.date()==previous
    return Scenario(zone,raid.date().isoformat(),raid.hour,
        int(raid.utcoffset().total_seconds()//60),
        fractal.date().isoformat(),fractal.hour,
        int(fractal.utcoffset().total_seconds()//60),
        same_prev, same_prev and 9<=fractal.hour<17,
        9<=raid.hour<17)

def _nearest_geometric_target(pivots,side,close,known_before_ms):
    opposing="SSL" if side=="SHORT" else "BSL"
    options=[p for p in pivots
        if p.kind==opposing and p.known_ms<=known_before_ms
        and (p.level<close if side=="SHORT" else p.level>close)]
    if not options:return None
    return min(options,key=lambda p:(abs(p.level-close),p.center_ms))

def inspect_c25(source,*,as_of_ms:int)->Review:
    bars=_source(source,as_of_ms)
    base=audit_route_admission(source,as_of_ms=as_of_ms)
    original=observe_native3m_raid_break(source,as_of_ms=as_of_ms)
    pivots,_=observe_fractals_and_first_breach(_hours(bars))
    lookup={(e.pivot_center_ms,e.raid_start_ms,e.break_start_ms):e
            for e in original.potential_breaks}
    if len(lookup)!=len(original.potential_breaks):
        raise ValueError("C25_DUPLICATED_RAID_PARENT_ID")
    output=[]
    for case in base.cases:
        if case.reason!="RESEARCH_SINGLE_CANDIDATE_AUTHOR_SESSION_FTA_SL_UNVERIFIED":
            continue
        event=lookup.get((case.raid_fractal_ms,case.raid_start_ms,case.break_start_ms))
        if event is None or event.source_original_3m_row_id!=case.original_break_row_id:
            raise ValueError("C25_C24_SOURCE_PARENT_DRIFT")
        if event.raid_confirmed_ms>event.break_start_ms:
            raise ValueError("C25_PREMATURE_1H_RAID")
        zones=tuple(scenario(event.pivot_center_ms,event.raid_start_ms,z) for z in ZONES)
        known_target=_nearest_geometric_target(pivots,event.side,event.break_close,event.break_start_ms)
        risk=(event.raid_extreme-event.break_close if event.side=="SHORT"
              else event.break_close-event.raid_extreme)
        if not (isinstance(risk,Decimal) and risk.is_finite()):
            raise ValueError("C25_CORRUPTED_ORIGINAL_PRICE")
        day_diff=len({z.pivot_was_previous_local_day for z in zones})>1
        session_diff=len({z.pivot_in_previous_09_17_session for z in zones})>1
        window_diff=len({z.raid_in_local_09_17_window for z in zones})>1
        output.append(Case(source.symbol,event.raid_start_ms,
            event.pivot_center_ms,event.break_start_ms,case.original_break_row_id,
            event.side,zones,day_diff,session_diff,window_diff,
            str(event.raid_extreme),str(event.break_close),str(risk),
            str(known_target.level) if known_target else None,
            known_target.center_ms if known_target else None,
            known_target is not None))
    cases=tuple(output)
    if len(cases)!=base.single_research_without_author_labels:
        raise ValueError("C25_165_PARENT_CAUSAL_JOIN_DRIFT")
    return Review(
        source.symbol,as_of_ms,base.total_original_research_edges,len(cases),
        cases,sum(x.zones_disagree_on_previous_day for x in cases),
        sum(x.zones_disagree_on_previous_09_17_session for x in cases),
        sum(x.zones_disagree_on_raid_09_17 for x in cases),
        sum(x.nearest_preknown_opposing_1h_fractal_price is None for x in cases),
        sum(Decimal(x.minimum_unbuffered_stop_distance)<=0 for x in cases),
        tuple((z,sum(x.zones[i].pivot_was_previous_local_day for x in cases))
              for i,z in enumerate(ZONES)),
        tuple((z,sum(x.zones[i].pivot_in_previous_09_17_session for x in cases))
              for i,z in enumerate(ZONES)),
        tuple((z,sum(x.zones[i].raid_in_local_09_17_window for x in cases))
              for i,z in enumerate(ZONES)))
