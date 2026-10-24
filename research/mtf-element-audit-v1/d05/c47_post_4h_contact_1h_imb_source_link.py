"""C47: original4H IMB first native3m contact -> later closed1H IMB source.

A joined record is ONLY chronologically admissible source geometry:
- 4H source is 3 fully closed 4H original3m-derived wick candles,
- first contact is the first original native3m wick intersection after known,
- all THREE 1H technical IMB source candles start AFTER contact candle closes,
- the later 1H technical wick gap is same source side,
- no author-labelled Volume Confirmation, POI, StrongHL, entry, SL, TP,
  fills, PnL or orders, ever. PAPER ONLY / NOT_TRADE_READY.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21b_original_3m_raid_break_geometry import _source,_hours,THREE,HOUR
from c20b_hourly_fractal_source_observer import HourSource
from c36_adapted_slot_registry import ACADEMIC_CORE_ID
from c46_original_4h_classic_imb_first_contact import (
    inspect_original_4h_imb_source,PoiContactObservation)

@dataclass(frozen=True)
class OneHourImbSource:
    side:str
    bottom:str
    top:str
    first_hour_start_ms:int
    second_hour_start_ms:int
    third_hour_start_ms:int
    fully_known_ms:int
    first_raw_native3m_ids:tuple[str,str,str]
    last_raw_native3m_ids:tuple[str,str,str]
    academic_vc_certified:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class FourToOneSourceObservation:
    symbol:str
    original4h_zone_side:str
    original4h_zone_known_ms:int
    original4h_zone_first_raw3m_ids:tuple[str,str,str]
    original4h_first_contact_native3m_id:str|None
    original4h_first_contact_closed_known_ms:int|None
    post_contact_same_side_1h_candidate_count:int
    first_post_contact_1h_imb_source:OneHourImbSource|None
    course_typed_poi_approved:bool=False
    course_first_valid_test_approved:bool=False
    course_volume_confirmation_approved:bool=False
    author_chart_golden_count:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C47SourceJoin:
    symbol:str
    as_of_ms:int
    original_native3m_closed:int
    original_native1h_closed:int
    original_source4h_candidates:int
    original_source4h_first_contacts:int
    matched_later_technical1h_imb_count:int
    unmatched_after_first_contact_count:int
    academic_core_id:str
    observations:tuple[FourToOneSourceObservation,...]
    author_vc_goldens:int=0
    author_poi_goldens:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def independently_original_1h_imb(hours):
    if not isinstance(hours,tuple):
        raise ValueError("C47_UNTRUSTED_ORIGINAL_HOURLY_SOURCE")
    for i,h in enumerate(hours):
        if (not isinstance(h,HourSource) or h.close_ms!=h.start_ms+HOUR
            or len(h.native_rows)!=20 or h.low<=0 or h.high<h.low
            or type(h.high) is not Decimal or type(h.low) is not Decimal
            or not h.high.is_finite() or not h.low.is_finite()
            or (i and h.start_ms!=hours[i-1].close_ms)):
            raise ValueError("C47_INVALID_HOUR_NATIVE3M_OR_TIME")
    out=[]
    for i in range(2,len(hours)):
        a,m,c=hours[i-2:i+1]
        if c.low>a.high:
            side="LONG";low=a.high;high=c.low
        elif c.high<a.low:
            side="SHORT";low=c.high;high=a.low
        else:continue
        out.append(OneHourImbSource(side,str(low),str(high),
            a.start_ms,m.start_ms,c.start_ms,c.close_ms,
            (a.native_rows[0],m.native_rows[0],c.native_rows[0]),
            (a.native_rows[-1],m.native_rows[-1],c.native_rows[-1])))
    return tuple(out)

def match_later_closed_source(poi_obs,onehour,*,as_of_ms):
    if not isinstance(poi_obs,PoiContactObservation):
        raise ValueError("C47_UNTRUSTED_4H_FIRST_CONTACT_WITNESS")
    if (poi_obs.academic_poi_test_certified or poi_obs.academic_volume_confirmation_certified
        or poi_obs.orders or poi_obs.trades or poi_obs.readiness!="NOT_TRADE_READY"
        or poi_obs.candidate.author_poi_certified
        or not poi_obs.has_complete_original3m_prefix_after_known):
        raise ValueError("C47_FORGED_AUTHOR_POI_SOURCE")
    if not isinstance(onehour,tuple):
        raise ValueError("C47_UNTRUSTED_1H_SOURCE_CANDIDATES")
    if type(as_of_ms) is not int or as_of_ms%THREE:
        raise ValueError("C47_INVALID_CLOSED_ASOF")
    c=poi_obs.candidate
    if (c.side not in ("LONG","SHORT") or c.fully_known_ms>as_of_ms
        or c.fully_known_ms% (4*HOUR) or
        c.source_status!="C46_NATIVE_4H_CLASSIC_IMB_GEOMETRY_ONLY"):
        raise ValueError("C47_INVALID_PARENT_4H_KNOWN")
    if poi_obs.first_contact_closed_known_ms is None:
        if (poi_obs.first_contact_original3m_id is not None or
            poi_obs.first_contact_bar_start_ms is not None):
            raise ValueError("C47_FICTITIOUS_FIRST_CONTACT")
        cutoff=None
    else:
        if (poi_obs.first_contact_original3m_id is None or
            poi_obs.first_contact_bar_start_ms is None or
            poi_obs.first_contact_closed_known_ms!=poi_obs.first_contact_bar_start_ms+THREE
            or poi_obs.first_contact_bar_start_ms<c.fully_known_ms
            or poi_obs.first_contact_closed_known_ms>as_of_ms):
            raise ValueError("C47_INVALID_SOURCE_FIRST_CONTACT_CHRONOLOGY")
        cutoff=poi_obs.first_contact_closed_known_ms
    selected=[]
    last_end=None
    for h in onehour:
        if (not isinstance(h,OneHourImbSource) or h.academic_vc_certified
            or h.orders or h.trades):
            raise ValueError("C47_FORGED_AUTHOR_1H_VC")
        if h.fully_known_ms>as_of_ms:
            raise ValueError("C47_FUTURE_1H_SOURCE_LEAK")
        if (h.fully_known_ms!=h.third_hour_start_ms+HOUR or
            h.second_hour_start_ms!=h.first_hour_start_ms+HOUR or
            h.third_hour_start_ms!=h.second_hour_start_ms+HOUR or
            h.first_hour_start_ms%HOUR or
            len(h.first_raw_native3m_ids)!=3 or len(h.last_raw_native3m_ids)!=3
            or any(not x for x in h.first_raw_native3m_ids+h.last_raw_native3m_ids)
            or not Decimal(h.bottom).is_finite() or not Decimal(h.top).is_finite()
            or Decimal(h.bottom)<=0 or Decimal(h.top)<=Decimal(h.bottom)):
            raise ValueError("C47_MALFORMED_1H_SOURCE_PROVENANCE")
        if last_end is not None and h.fully_known_ms<=last_end:
            raise ValueError("C47_1H_SOURCE_GAP_ORDER_DRIFT")
        last_end=h.fully_known_ms
        if h.side not in ("LONG","SHORT"):
            raise ValueError("C47_FORGED_1H_SOURCE_DIRECTION")
        if cutoff is not None and h.side==c.side and h.first_hour_start_ms>=cutoff:
            selected.append(h)
    return tuple(selected)

def scan_original_4h_first_contact_to_later_1h_source(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    parent=inspect_original_4h_imb_source(source,as_of_ms=as_of_ms)
    if (parent.academic_core_id!=ACADEMIC_CORE_ID or
        parent.orders or parent.trades or parent.author_poi_goldens
        or parent.readiness!="NOT_TRADE_READY" or
        parent.original_native3m_closed!=len(rows)):
        raise ValueError("C47_PARENT_ACADEMIC_OR_SOURCE_DRIFT")
    hour=_hours(rows)
    technical=independently_original_1h_imb(hour)
    observations=[]
    for ob in parent.observations:
        links=match_later_closed_source(ob,technical,as_of_ms=as_of_ms)
        c=ob.candidate
        observations.append(FourToOneSourceObservation(parent.symbol,c.side,
            c.fully_known_ms,c.three_original_source_first_native3m_ids,
            ob.first_contact_original3m_id,ob.first_contact_closed_known_ms,
            len(links),links[0] if links else None))
    count=sum(x.first_post_contact_1h_imb_source is not None for x in observations)
    has_parent=sum(x.original4h_first_contact_native3m_id is not None for x in observations)
    if has_parent!=parent.first_original3m_contact_count:
        raise ValueError("C47_FIRST_CONTACT_PARENT_COUNT_DRIFT")
    return C47SourceJoin(parent.symbol,as_of_ms,len(rows),len(hour),
        parent.candidate_count,has_parent,count,has_parent-count,
        ACADEMIC_CORE_ID,tuple(observations))
