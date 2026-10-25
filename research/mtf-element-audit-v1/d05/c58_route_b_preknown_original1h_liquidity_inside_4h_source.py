"""C58 course Route B IDM prerequisites: original, PREKNOWN 1H BSL/SSL
fractal liquidity *inside* technical 4H C46 classic IMB source zone at
its FIRST original 3m contact, optionally unswept up to contact bar START.

NOT a course-authored IDM, not tested typed POI, StrongHL or order. The
author's 'inside or ahead' is not fully specified: this observer ONLY tests
numeric INSIDE source geometry, never calls above/below an 'ahead' IDM.

Each native 1H pivot must be fully closed and known after 4H zone creation
and before contact 3m BAR START; each prior 3m high/low is only known at
close before contact. Do not rank/select 'best' inducement after outcome.
"""
from dataclasses import dataclass
from decimal import Decimal
import re
from c46_original_4h_classic_imb_first_contact import PoiContactObservation,C46SourceResult
from c20b_hourly_fractal_source_observer import HourFractal,observe_fractals_and_first_breach
from c21b_original_3m_raid_break_geometry import _source,_hours,THREE,HOUR
from c45_recovered_course_text_contract import TEXT_ROUTE_MODES,recovered_text_claims
from c36_adapted_slot_registry import ACADEMIC_CORE_ID

ROUTE="B_4H_VC_1H_IDM"
RAW=re.compile(r"[a-f0-9]{64}:[0-9]{13}\Z")
STATUS=("NO_ORIGINAL_NATIVE3M_FIRST_4H_SOURCE_CONTACT",
        "NO_PREKNOWN_1H_FRACTAL_INSIDE_4H_SOURCE_GAP",
        "ONLY_PRIOR_SWEPT_1H_FRACTAL_LEVELS_INSIDE_4H_GAP",
        "PREKNOWN_UNSWEPT_1H_FRACTAL_INSIDE_4H_GAP")
BLOCKERS=("C46_TECHNICAL_4H_WICK_IMB_NOT_AUTHOR_CONTEXTUAL_VC_POI",
          "INTERIOR_PREKNOWN_1H_FRACTAL_NOT_AUTHOR_IDM",
          "INSIDE_ONLY_AHEAD_AUTHOR_DIRECTION_NOT_CERTIFIED",
          "STRONG_HIGH_LOW_FIRST_TEST_COURSE_SEMANTICS_UNKNOWN",
          "NO_ACADEMIC_ENTRY_STOP_FTA_RR_EXECUTION_OOS")

@dataclass(frozen=True)
class C58LiquidityCandidate:
    kind:str
    level:str
    pivot_center_ms:int
    pivot_fully_known_ms:int
    pivot_original_native3m_center_row_id:str
    inspected_original3m_closed_count:int
    first_original3m_strict_breach_id:str|None
    unswept_until_contact_bar_start:bool
    author_idm_certified:bool=False
    strong_high_low_author_certified:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class C58OriginalParent:
    symbol:str
    technical_4h_imb_side:str
    technical_4h_imb_bottom:str
    technical_4h_imb_top:str
    four_hour_gap_fully_known_ms:int
    first_contact_original3m_id:str|None
    first_contact_bar_start_ms:int|None
    preknown_inside_1h_liquidity:tuple[C58LiquidityCandidate,...]
    source_state:str
    academic_idm_approved:bool=False
    author_typed_poi_verified:bool=False
    author_stronghl_verified:bool=False
    blockers:tuple[str,...]=BLOCKERS
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C58SourceAudit:
    symbol:str
    as_of_ms:int
    source_original3m_closed:int
    source_original1h_closed:int
    original_4h_source_candidate_count:int
    source_states:tuple[tuple[str,int],...]
    reviewed_parents:tuple[C58OriginalParent,...]
    author_idm_goldens:int=0
    paper_signals:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _id(x,start):
    return isinstance(x,str) and RAW.fullmatch(x) and int(x.rsplit(":",1)[1])==start

def evaluate_preknown_original_pivot(p,closed3,*,gap_known_ms,contact_start_ms):
    if not isinstance(p,HourFractal) or p.kind not in ("BSL","SSL"):
        raise ValueError("C58_INVALID_1H_LIQUIDITY_PIVOT")
    if (type(p.center_ms) is not int or p.center_ms%HOUR or
        type(p.known_ms) is not int or p.known_ms!=p.center_ms+2*HOUR or
        p.known_ms<gap_known_ms or p.known_ms>contact_start_ms or
        not isinstance(p.level,Decimal) or not p.level.is_finite() or p.level<=0 or
        len(p.source_rows)!=60 or
        not _id(p.source_rows[20],p.center_ms)):
        raise ValueError("C58_FUTURE_OR_UNPROVEN_1H_FRACTAL")
    if not isinstance(closed3,tuple):
        raise ValueError("C58_NOT_ORIGINAL_3M_CANDLE_PREFIX")
    last=None
    for row in closed3:
        if (not hasattr(row,"start_ms") or not hasattr(row,"known_ms") or
            not hasattr(row,"high") or not hasattr(row,"low") or
            not hasattr(row,"raw_id") or
            not _id(row.raw_id,row.start_ms) or
            type(row.start_ms) is not int or
            row.known_ms!=row.start_ms+THREE or
            row.known_ms>contact_start_ms or row.start_ms<p.known_ms or
            (last is not None and row.start_ms!=last) or
            not isinstance(row.high,Decimal) or not isinstance(row.low,Decimal)
            or not row.high.is_finite() or not row.low.is_finite() or
            row.low<=0 or row.high<row.low):
            raise ValueError("C58_FUTURE_OR_FORGED_PRECONTACT_3M_PRICE")
        last=row.known_ms
    seen=next((x for x in closed3 if
               (x.high>p.level if p.kind=="BSL" else x.low<p.level)),None)
    return C58LiquidityCandidate(p.kind,str(p.level),p.center_ms,p.known_ms,
         p.source_rows[20],len(closed3),seen.raw_id if seen else None,
         seen is None)

def source_inside_first_contact(c46obs,pivots,original3m,*,symbol,as_of_ms):
    if not isinstance(c46obs,PoiContactObservation):
        raise ValueError("C58_NOT_FROZEN_C46_PARENT")
    c=c46obs.candidate
    if (c.source_status!="C46_NATIVE_4H_CLASSIC_IMB_GEOMETRY_ONLY" or
        c.author_poi_certified or c.orders or c.trades or
        c46obs.academic_poi_test_certified or
        c46obs.academic_volume_confirmation_certified or
        c46obs.orders or c46obs.trades or
        c46obs.readiness!="NOT_TRADE_READY" or
        not c46obs.has_complete_original3m_prefix_after_known or
        c.side not in ("LONG","SHORT") or
        c.fully_known_ms%(4*HOUR) or
        c.fully_known_ms>as_of_ms):
        raise ValueError("C58_FORGED_AUTHOR_POI_OR_FUTURE_4H")
    try:
        bottom,top=Decimal(c.bottom),Decimal(c.top)
    except Exception as ex:
        raise ValueError("C58_INVALID_4H_GAP_PRICE") from ex
    if not (bottom.is_finite() and top.is_finite() and 0<bottom<top):
        raise ValueError("C58_INVALID_4H_GAP_PRICE")
    if not isinstance(pivots,tuple) or not isinstance(original3m,tuple):
        raise ValueError("C58_UNTRUSTED_ORIGINAL_CRYPTO_SOURCE")
    contact=c46obs.first_contact_bar_start_ms
    first_id=c46obs.first_contact_original3m_id
    if c46obs.first_contact_closed_known_ms is None:
        if contact is not None or first_id is not None:
            raise ValueError("C58_FICTITIOUS_FIRST_CONTACT")
        return C58OriginalParent(symbol,c.side,str(bottom),str(top),
           c.fully_known_ms,None,None,(),STATUS[0])
    if (type(contact) is not int or contact< c.fully_known_ms or
        contact%THREE or contact+THREE!=c46obs.first_contact_closed_known_ms or
        c46obs.first_contact_closed_known_ms>as_of_ms or not _id(first_id,contact)):
        raise ValueError("C58_INVALID_ORIGINAL_FIRST_CONTACT")
    levels=[]
    last_known=None
    for pivot in pivots:
        if (not isinstance(pivot,HourFractal) or
            type(pivot.known_ms) is not int or
            (last_known is not None and pivot.known_ms<last_known)):
            raise ValueError("C58_UNORDERED_OR_UNTRUSTED_1H_PIVOT_SOURCE")
        last_known=pivot.known_ms
        if (pivot.known_ms<c.fully_known_ms or pivot.known_ms>contact or
            pivot.level<bottom or pivot.level>top):
            continue
        if pivot.kind not in ("BSL","SSL"):
            raise ValueError("C58_FORGED_1H_LIQUIDITY_KIND")
        start=(pivot.known_ms-original3m[0].start_ms)//THREE
        end=(contact-original3m[0].start_ms)//THREE
        if start<0 or end>len(original3m) or end<start:
            raise ValueError("C58_MISSING_PRECONTACT_NATIVE3M_SOURCE")
        segment=original3m[start:end]
        levels.append(evaluate_preknown_original_pivot(pivot,segment,
            gap_known_ms=c.fully_known_ms,contact_start_ms=contact))
    state=(STATUS[1] if not levels else
           STATUS[3] if any(x.unswept_until_contact_bar_start for x in levels)
           else STATUS[2])
    return C58OriginalParent(symbol,c.side,str(bottom),str(top),
           c.fully_known_ms,first_id,contact,tuple(levels),state)

def scan_c58_source_only(original3m,*,as_of_ms):
    rows=_source(original3m,as_of_ms)
    hours=_hours(rows)
    pivots,_=observe_fractals_and_first_breach(hours)
    from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
    parent=inspect_original_4h_imb_source(original3m,as_of_ms=as_of_ms)
    if (parent.academic_core_id!=ACADEMIC_CORE_ID or
        parent.orders or parent.trades or parent.author_poi_goldens or
        parent.readiness!="NOT_TRADE_READY" or
        parent.candidate_count!=len(parent.observations) or
        ROUTE not in TEXT_ROUTE_MODES or
        TEXT_ROUTE_MODES[ROUTE]!=("4H","1H",None,"1H","4H") or
        len(recovered_text_claims())!=18):
        raise ValueError("C58_COURSE_OR_ORIGINAL_C46_PARENT_CONTRACT_DRIFT")
    events=tuple(source_inside_first_contact(x,pivots,rows,
            symbol=parent.symbol,as_of_ms=as_of_ms)
            for x in parent.observations)
    from collections import Counter
    counts=Counter(x.source_state for x in events)
    return C58SourceAudit(parent.symbol,as_of_ms,len(rows),len(hours),
        len(events),tuple((status,counts[status]) for status in STATUS),events)
