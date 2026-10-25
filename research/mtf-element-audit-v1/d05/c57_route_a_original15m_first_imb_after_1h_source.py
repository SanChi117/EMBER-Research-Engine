"""C57 source-only Route A chronology: 4H IMB first 3m touch, later 1H
technical same-side IMB, FIRST ANY native 15m classic three-bar wick gap.

Explicitly *not* course-typed 4H POI, author 1H trigger, volume confirmation,
trade entry, directional performance, SL/TP or a proxy for route B IDM.
Source price from verified original C08 native15m, 1H/4H from C46/C47
original3m, strict closed as-of and no retroactive use of unclosed bars.
The fixed six-hour observation horizon is a technical bounded observation,
not the instructor's permissible entry window or optimized parameter.
"""
from dataclasses import dataclass
from decimal import Decimal
import re
from c16_c08_monthly_daily_htf_lineage import NativeKline,SEPT_START
from c47_post_4h_contact_1h_imb_source_link import (
    C47SourceJoin,FourToOneSourceObservation,OneHourImbSource)
from c45_recovered_course_text_contract import TEXT_ROUTE_MODES,recovered_text_claims
from c36_adapted_slot_registry import ACADEMIC_CORE_ID

FIFTEEN=900_000
HOUR=3_600_000
WINDOW=6*HOUR
SOURCE_SCOPE="A_4H_TRIGGER_15M_VC"
STATUS=("NO_ORIGINAL_3M_FIRST_CONTACT",
        "NO_POST_CONTACT_1H_IMB_SOURCE",
        "NO_NATIVE15M_CLASSIC_IMB_WITHIN_FIXED_6H",
        "FIRST_ANY_NATIVE15M_IMB_SAME_SIDE_AS_4H",
        "FIRST_ANY_NATIVE15M_IMB_OPPOSITE_SIDE_TO_4H",
        "RIGHT_CENSORED_NO_15M_IMB_BY_SOURCE_END")
RAW=re.compile(r"[a-f0-9]{64}:[0-9]{13}\Z")
BLOCKERS=("C46_CLASSIC_4H_IMB_NOT_AUTHOR_TYPED_POI",
          "C46_FIRST_NATIVE3M_CONTACT_NOT_AUTHOR_VALID_TEST",
          "C47_TECHNICAL_1H_IMB_NOT_AUTHOR_TRIGGER",
          "C57_NATIVE15M_CLASSIC_IMB_NOT_ACADEMIC_VC_OR_VOLUME_PROOF",
          "STRONGHL_ENTRY_FTA_SL_TP_OOS_AND_EXECUTION_UNKNOWN")

@dataclass(frozen=True)
class FifteenMinuteImb:
    side:str
    bottom:str
    top:str
    first_start_ms:int
    third_start_ms:int
    fully_known_ms:int
    original_native15m_ids:tuple[str,str,str]
    academic_vc_certified:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class C57RouteAObservation:
    symbol:str
    fourh_source_side:str
    fourh_source_known_ms:int
    original3m_first_contact_id:str|None
    original3m_first_contact_known_ms:int|None
    subsequent_1h_source_known_ms:int|None
    first_any_15m_imb:FifteenMinuteImb|None
    source_status:str
    upper_observation_boundary_ms:int|None
    fixed_six_hour_window_fully_observed:bool|None
    route_mode:str=SOURCE_SCOPE
    course_author_POI_verified:bool=False
    course_author_first_valid_test_verified:bool=False
    course_author_1h_trigger_verified:bool=False
    course_author_15m_VC_verified:bool=False
    paper_order_approved:bool=False
    blockers:tuple[str,...]=BLOCKERS
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C57SourceReview:
    symbol:str
    as_of_ms:int
    original_closed_native15m_count:int
    original_C47_4h_candidate_count:int
    source_status_counts:tuple[tuple[str,int],...]
    observations:tuple[C57RouteAObservation,...]
    route_mode:str=SOURCE_SCOPE
    author_POI_goldens:int=0
    author_15m_VC_goldens:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _positive(v):
    if not isinstance(v,Decimal) or not v.is_finite() or v<=0:
        raise ValueError("C57_NOT_FINITE_POSITIVE_NATIVE_PRICE")
    return v

def validate_native15m(rows,*,as_of_ms,symbol):
    if (not isinstance(rows,tuple) or not rows or
        type(as_of_ms) is not int or as_of_ms%FIFTEEN or
        as_of_ms<SEPT_START+FIFTEEN or
        len(rows)!=(as_of_ms-SEPT_START)//FIFTEEN):
        raise ValueError("C57_NATIVE15M_NOT_COMPLETE_CLOSED_PREFIX")
    for i,z in enumerate(rows):
        if (not isinstance(z,NativeKline) or z.tf!="15m" or
            z.symbol!=symbol or z.start_ms!=SEPT_START+i*FIFTEEN or
            z.known_at_ms!=z.start_ms+FIFTEEN or
            not isinstance(z.origin_zip_sha256,str) or
            not re.fullmatch(r"[a-f0-9]{64}",z.origin_zip_sha256) or
            z.origin_raw_row_id!=z.origin_zip_sha256+":"+str(z.start_ms) or
            not RAW.fullmatch(z.origin_raw_row_id) or
            not isinstance(z.volume,Decimal) or not z.volume.is_finite() or z.volume<0):
            raise ValueError("C57_INVALID_ORIGINAL_NATIVE15M_PRICE_ROW")
        lo,hi=_positive(z.low),_positive(z.high)
        op,cl=_positive(z.open),_positive(z.close)
        if not (lo<=min(op,cl)<=max(op,cl)<=hi):
            raise ValueError("C57_NATIVE15M_IMPOSSIBLE_OHLC")
    return True

def observed_15m_gaps(rows):
    """All strictly closed technical three-bar wick gaps, no signal labels."""
    out=[]
    for i in range(2,len(rows)):
        a,m,c=rows[i-2:i+1]
        if c.low>a.high:
            side="LONG";bottom=a.high;top=c.low
        elif c.high<a.low:
            side="SHORT";bottom=c.high;top=a.low
        else:
            continue
        out.append(FifteenMinuteImb(side,str(bottom),str(top),
            a.start_ms,c.start_ms,c.known_at_ms,
            (a.origin_raw_row_id,m.origin_raw_row_id,c.origin_raw_row_id)))
    return tuple(out)

def first_any_after_parent(p,gaps,*,symbol,as_of_ms):
    if not isinstance(p,FourToOneSourceObservation):
        raise ValueError("C57_UNTRUSTED_C47_PARENT")
    if (p.symbol!=symbol or p.original4h_zone_side not in ("LONG","SHORT") or
        p.original4h_zone_known_ms% (4*HOUR) or
        p.original4h_zone_known_ms>as_of_ms or
        p.course_typed_poi_approved or p.course_first_valid_test_approved or
        p.course_volume_confirmation_approved or p.author_chart_golden_count or
        p.orders or p.trades or p.readiness!="NOT_TRADE_READY"):
        raise ValueError("C57_FORGED_AUTHOR_POI_OR_PARENT")
    if (p.original4h_first_contact_native3m_id is None)!=(
        p.original4h_first_contact_closed_known_ms is None):
        raise ValueError("C57_PARTIAL_FIRST_CONTACT")
    if not isinstance(gaps,tuple):
        raise ValueError("C57_UNTRUSTED_NATIVE15M_GAP_TIMELINE")
    last=None
    for g in gaps:
        if (not isinstance(g,FifteenMinuteImb) or g.academic_vc_certified or
            g.orders or g.trades or g.side not in ("LONG","SHORT") or
            type(g.first_start_ms) is not int or
            g.first_start_ms%FIFTEEN or
            g.third_start_ms!=g.first_start_ms+2*FIFTEEN or
            g.fully_known_ms!=g.third_start_ms+FIFTEEN or
            g.fully_known_ms>as_of_ms or
            len(g.original_native15m_ids)!=3 or
            not all(RAW.fullmatch(x) and int(x.rsplit(":",1)[1])==
                g.first_start_ms+i*FIFTEEN
                for i,x in enumerate(g.original_native15m_ids)) or
            not Decimal(g.bottom).is_finite() or not Decimal(g.top).is_finite() or
            not (0<Decimal(g.bottom)<Decimal(g.top)) or
            (last is not None and g.fully_known_ms<=last)):
            raise ValueError("C57_FORGED_OR_UNCLOSED_15M_IMB_SOURCE")
        last=g.fully_known_ms
    one=p.first_post_contact_1h_imb_source
    if p.original4h_first_contact_closed_known_ms is None:
        if one is not None or p.post_contact_same_side_1h_candidate_count:
            raise ValueError("C57_1H_WITHOUT_4H_FIRST_CONTACT")
        status=STATUS[0];bound=None;first=None;complete=None
    else:
        c=p.original4h_first_contact_closed_known_ms
        if (type(c) is not int or c<=p.original4h_zone_known_ms or
            c>as_of_ms or c%180000 or
            not RAW.fullmatch(p.original4h_first_contact_native3m_id) or
            int(p.original4h_first_contact_native3m_id.rsplit(":",1)[1])!=c-180000):
            raise ValueError("C57_INVALID_FIRST_NATIVE3M_CONTACT")
        if one is None:
            if p.post_contact_same_side_1h_candidate_count:
                raise ValueError("C57_MISSING_FIRST_1H_CANDIDATE")
            status=STATUS[1];bound=None;first=None;complete=None
        else:
            if (not isinstance(one,OneHourImbSource) or
                one.side!=p.original4h_zone_side or
                one.academic_vc_certified or one.orders or one.trades or
                not 1<=p.post_contact_same_side_1h_candidate_count or
                one.first_hour_start_ms<c or
                one.first_hour_start_ms%HOUR or
                one.second_hour_start_ms!=one.first_hour_start_ms+HOUR or
                one.third_hour_start_ms!=one.second_hour_start_ms+HOUR or
                one.fully_known_ms!=one.third_hour_start_ms+HOUR or
                one.fully_known_ms>as_of_ms or
                len(one.first_raw_native3m_ids)!=3 or
                len(one.last_raw_native3m_ids)!=3 or
                not all(RAW.fullmatch(x) and int(x.rsplit(":",1)[1])==
                    one.first_hour_start_ms+i*HOUR
                    for i,x in enumerate(one.first_raw_native3m_ids)) or
                not all(RAW.fullmatch(x) and int(x.rsplit(":",1)[1])==
                    one.first_hour_start_ms+(i+1)*HOUR-180000
                    for i,x in enumerate(one.last_raw_native3m_ids)) or
                not (Decimal(one.top)>Decimal(one.bottom)>0)):
                raise ValueError("C57_1H_C47_GEOMETRY_OR_KNOWN_TIME_FORGED")
            bound=min(as_of_ms,one.fully_known_ms+WINDOW)
            complete=as_of_ms>=one.fully_known_ms+WINDOW
            first=next((v for v in gaps if
                v.first_start_ms>=one.fully_known_ms and
                v.fully_known_ms<=bound),None)
            status=(STATUS[3] if first.side==p.original4h_zone_side else STATUS[4]
                    ) if first is not None else STATUS[2] if complete else STATUS[5]
    return C57RouteAObservation(
        symbol,p.original4h_zone_side,p.original4h_zone_known_ms,
        p.original4h_first_contact_native3m_id,
        p.original4h_first_contact_closed_known_ms,
        one.fully_known_ms if one else None,first,status,bound,complete)

def scan_c57_original_route_a(c47,original15,*,as_of_ms):
    if (not isinstance(c47,C47SourceJoin) or
        c47.readiness!="NOT_TRADE_READY" or c47.orders or c47.trades or
        c47.author_vc_goldens or c47.author_poi_goldens or
        c47.academic_core_id!=ACADEMIC_CORE_ID or
        c47.as_of_ms!=as_of_ms or
        c47.original_source4h_candidates!=len(c47.observations) or
        c47.original_source4h_first_contacts!=sum(
          x.original4h_first_contact_native3m_id is not None
          for x in c47.observations) or
        c47.matched_later_technical1h_imb_count!=sum(
          x.first_post_contact_1h_imb_source is not None
          for x in c47.observations)):
        raise ValueError("C57_UNVERIFIED_C47_ORIGINAL_SOURCE_PARENT")
    if (SOURCE_SCOPE not in TEXT_ROUTE_MODES or
        TEXT_ROUTE_MODES[SOURCE_SCOPE]!=("4H","1H","15M","15M","4H") or
        len(recovered_text_claims())!=18):
        raise ValueError("C57_ACADEMIC_ROUTE_A_TEXT_CONTRACT_DRIFT")
    validate_native15m(original15,as_of_ms=as_of_ms,symbol=c47.symbol)
    gaps=observed_15m_gaps(original15)
    out=tuple(first_any_after_parent(x,gaps,symbol=c47.symbol,as_of_ms=as_of_ms)
              for x in c47.observations)
    from collections import Counter
    counts=Counter(x.source_status for x in out)
    if sum(counts.values())!=len(out):
        raise ValueError("C57_PARENT_COUNT_DRIFT")
    return C57SourceReview(c47.symbol,as_of_ms,len(original15),
          len(out),tuple((s,counts[s]) for s in STATUS),out)
