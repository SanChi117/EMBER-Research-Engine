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
