"""C60: original Binance USD-M native3m 4H technical-IMB lifecycle.

Course text FVG: only FIRST POI test is pristine; later returns may build
liquidity. We measure technically observable contact EPISODES:
  - first wick intersection AFTER all 3 parent 4H candles CLOSE;
  - adjacent overlapping 3m bars are ONE continuous visit;
  - new episode requires at least one full CLOSED 3m non-contact bar
    between visits; intrabar travels are unknowable from OHLC;
  - open last episode at as-of is RIGHT CENSORED.

NO author-selected typed POI, course-valid first test, VC/BOS, StrongHL,
entry, stop, fill or PnL are inferred.
"""
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
import re
from c21b_original_3m_raid_break_geometry import _source,THREE
from c46_original_4h_classic_imb_first_contact import (
    FourHourImbCandidate,inspect_original_4h_imb_source)
from c36_adapted_slot_registry import ACADEMIC_CORE_ID

@dataclass(frozen=True)
class SourceVisit:
    kind:str
    first_original3m_raw_id:str
    first_bar_start_ms:int
    first_bar_known_ms:int
    last_original3m_raw_id:str
    last_bar_known_ms:int
    candle_count:int
    separated_from_prior_by_fully_closed_outside_3m:bool
    still_inside_at_source_end:bool
    author_valid_poi_test_verified:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class C60TechnicalPoiLifecycle:
    symbol:str
    technical_4h_zone_side:str
    zone_known_ms:int
    zone_bottom:str
    zone_top:str
    original_4h_first_row_ids:tuple[str,str,str]
    first_contact_original3m_id:str|None
    all_closed_3m_visit_episodes:tuple[SourceVisit,...]
    repeated_distinct_returns_after_first:int
    first_episode_still_open_at_source_end:bool
    last_episode_still_open_at_source_end:bool
    no_intrabar_path_claim:bool=True
    course_author_valid_first_test:bool=False
    course_author_StrongHL:bool=False
    academic_trade_signal:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C60SourceAudit:
    symbol:str
    as_of_ms:int
    original3m_closed:int
    technical_4h_candidate_count:int
    candidates_with_first_source_contact:int
    candidates_with_repeated_source_returns:int
    total_separate_source_visits:int
    right_censored_final_episodes:int
    candidate_visits:tuple[C60TechnicalPoiLifecycle,...]
    author_valid_poi_tests:int=0
    author_stronghl_goldens:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _price(s):
    if not isinstance(s,str):raise ValueError("C60_INVALID_ORIGINAL_4H_ZONE")
    try:d=Decimal(s)
    except (ValueError,InvalidOperation) as e:
        raise ValueError("C60_INVALID_ORIGINAL_4H_ZONE") from e
    if not d.is_finite() or d<=0:
        raise ValueError("C60_INVALID_ORIGINAL_4H_ZONE")
    return d

def observe_original3m_zone_visits(rows,candidate,*,as_of_ms):
    if not isinstance(candidate,FourHourImbCandidate):
        raise ValueError("C60_UNTRUSTED_ORIGINAL_4H_CANDIDATE")
    if (candidate.author_poi_certified or candidate.orders or candidate.trades or
        candidate.source_status!="C46_NATIVE_4H_CLASSIC_IMB_GEOMETRY_ONLY" or
        candidate.side not in ("LONG","SHORT") or
        type(as_of_ms) is not int or as_of_ms%THREE or
        candidate.fully_known_ms>as_of_ms or candidate.fully_known_ms%14_400_000):
        raise ValueError("C60_FORGED_AUTHOR_OR_UNCLOSED_PARENT_4H")
    lower,upper=_price(candidate.bottom),_price(candidate.top)
    if lower>=upper:
        raise ValueError("C60_INVALID_ORIGINAL_4H_ZONE")
    if not isinstance(rows,tuple) or not rows:
        raise ValueError("C60_MISSING_COMPLETE_ORIGINAL_3M_PREFIX")
    last=None;after=[];started=False
    for row in rows:
        if (not hasattr(row,"start_ms") or not hasattr(row,"known_ms") or
            not hasattr(row,"raw_id") or not hasattr(row,"high") or
            not hasattr(row,"low") or type(row.start_ms) is not int or
            not isinstance(row.raw_id,str) or
            not re.fullmatch(r"[0-9a-f]{64}:[0-9]{13}",row.raw_id) or
            int(row.raw_id.rsplit(":",1)[1])!=row.start_ms or
            row.known_ms!=row.start_ms+THREE or
            row.known_ms>as_of_ms or
            (last is not None and row.start_ms!=last) or
            not isinstance(row.high,Decimal) or not isinstance(row.low,Decimal) or
            not row.high.is_finite() or not row.low.is_finite() or
            row.high<row.low or row.low<=0):
            raise ValueError("C60_INVALID_CLOSED_SOURCE_3M_GRID")
        last=row.known_ms
        if row.start_ms>=candidate.fully_known_ms:
            if not started and row.start_ms!=candidate.fully_known_ms:
                raise ValueError("C60_GAPPED_AFTER_KNOWN_4H_SOURCE")
            started=True;after.append(row)
    # A 4H candidate created by the VERY LAST fully closed candle has
    # exactly zero post-known 3m bars. It is correctly untouched, not a
    # missing-prefix error: there is no future source yet to observe.
    if rows[-1].known_ms!=as_of_ms or (not started and candidate.fully_known_ms!=as_of_ms):
        raise ValueError("C60_INCOMPLETE_OR_FUTURE_SOURCE_PREFIX")
    result=[];first=None;last_hit=None;n=0
    for row in after:
        touches=(row.high>=lower and row.low<=upper)
        if touches:
            if first is None:
                first=row;n=1;last_hit=row
            else:
                n+=1;last_hit=row
            continue
        if first is not None:
            result.append(SourceVisit(
                "FIRST_SOURCE_WICK_VISIT" if not result else "REPEATED_SOURCE_WICK_RETURN",
                first.raw_id,first.start_ms,first.known_ms,
                last_hit.raw_id,last_hit.known_ms,n,
                bool(result),False))
            first=None;last_hit=None;n=0
    if first is not None:
        result.append(SourceVisit(
            "FIRST_SOURCE_WICK_VISIT" if not result else "REPEATED_SOURCE_WICK_RETURN",
            first.raw_id,first.start_ms,first.known_ms,
            last_hit.raw_id,last_hit.known_ms,n,
            bool(result),True))
    if any(x.author_valid_poi_test_verified or x.orders or x.trades
           for x in result):
        raise ValueError("C60_FORGED_AUTHOR_FIRST_TEST")
    if result and (result[0].kind!="FIRST_SOURCE_WICK_VISIT" or
       any(x.kind!="REPEATED_SOURCE_WICK_RETURN" for x in result[1:])):
        raise ValueError("C60_SOURCE_FIRST_TEST_EPISODE_ORDER_DRIFT")
    return tuple(result)

def scan_c60_original_source(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    parent=inspect_original_4h_imb_source(source,as_of_ms=as_of_ms)
    if (parent.academic_core_id!=ACADEMIC_CORE_ID or
        parent.original_native3m_closed!=len(rows) or
        parent.orders or parent.trades or parent.author_poi_goldens or
        parent.readiness!="NOT_TRADE_READY" or
        parent.candidate_count!=len(parent.observations)):
        raise ValueError("C60_ORIGINAL_C46_SOURCE_DRIFT")
    out=[]
    for p in parent.observations:
        obs=observe_original3m_zone_visits(rows,p.candidate,as_of_ms=as_of_ms)
        first=obs[0].first_original3m_raw_id if obs else None
        if (first!=p.first_contact_original3m_id or
            (obs and obs[0].first_bar_start_ms!=p.first_contact_bar_start_ms) or
            (obs and obs[0].first_bar_known_ms!=p.first_contact_closed_known_ms) or
            p.academic_poi_test_certified or p.academic_volume_confirmation_certified or
            p.orders or p.trades or p.readiness!="NOT_TRADE_READY"):
            raise ValueError("C60_ORIGINAL_C46_FIRST_SOURCE_TOUCH_ID_DRIFT")
        out.append(C60TechnicalPoiLifecycle(
            parent.symbol,p.candidate.side,p.candidate.fully_known_ms,
            p.candidate.bottom,p.candidate.top,
            p.candidate.three_original_source_first_native3m_ids,
            first,obs,max(0,len(obs)-1),
            bool(len(obs)==1 and obs[0].still_inside_at_source_end),
            bool(obs and obs[-1].still_inside_at_source_end)))
    return C60SourceAudit(parent.symbol,as_of_ms,len(rows),
        parent.candidate_count,sum(x.first_contact_original3m_id is not None for x in out),
        sum(x.repeated_distinct_returns_after_first>0 for x in out),
        sum(len(x.all_closed_3m_visit_episodes) for x in out),
        sum(x.last_episode_still_open_at_source_end for x in out),
        tuple(out))
