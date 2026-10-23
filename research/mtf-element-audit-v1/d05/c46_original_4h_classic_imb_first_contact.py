"""C46: independently recover *source geometry* of 4H classic 3-candle IMB.

These are SOURCE-DERIVED candidate zones, never course-certified 4H POI.
Find original native3m FIRST observed contact after all original 4H three
candles have closed. Missing historical prefix => fail closed. No fills,
VC, trading order or course chart golden. No change to C43/C44/C45.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21b_original_3m_raid_break_geometry import _source,_hours,THREE,HOUR
from c20b_hourly_fractal_source_observer import HourSource
from c36_adapted_slot_registry import ACADEMIC_CORE_ID

FOUR=4*HOUR

@dataclass(frozen=True)
class FourBar:
    start_ms:int
    known_ms:int
    high:Decimal
    low:Decimal
    first_original3m_id:str
    last_original3m_id:str

@dataclass(frozen=True)
class FourHourImbCandidate:
    side:str
    bottom:str
    top:str
    fully_known_ms:int
    source_4h_first_start_ms:int
    source_4h_second_start_ms:int
    source_4h_third_start_ms:int
    three_original_source_first_native3m_ids:tuple[str,str,str]
    three_original_source_last_native3m_ids:tuple[str,str,str]
    source_status:str="C46_NATIVE_4H_CLASSIC_IMB_GEOMETRY_ONLY"
    author_poi_certified:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class PoiContactObservation:
    candidate:FourHourImbCandidate
    first_contact_bar_start_ms:int|None
    first_contact_closed_known_ms:int|None
    first_contact_original3m_id:str|None
    has_complete_original3m_prefix_after_known:bool
    observed_state:str
    academic_poi_test_certified:bool=False
    academic_volume_confirmation_certified:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C46SourceResult:
    symbol:str
    as_of_ms:int
    original_native3m_closed:int
    complete_original_4h_candles:int
    academic_core_id:str
    candidate_count:int
    first_original3m_contact_count:int
    untouched_candidate_count:int
    observations:tuple[PoiContactObservation,...]
    author_poi_goldens:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def aggregate_original_4h(hours):
    if not isinstance(hours,tuple):
        raise ValueError("C46_MISSING_ORIGINAL_HOURLY_SOURCE")
    for i,h in enumerate(hours):
        if (not isinstance(h,HourSource) or len(h.native_rows)!=20 or
            h.close_ms!=h.start_ms+HOUR or
            (i and h.start_ms!=hours[i-1].close_ms) or
            type(h.high) is not Decimal or type(h.low) is not Decimal or
            not h.high.is_finite() or not h.low.is_finite() or
            h.low<=0 or h.high<h.low):
            raise ValueError("C46_INVALID_HOUR_OR_NATIVE3M_SOURCE")
    out=[]
    for i in range(0,len(hours)//4*4,4):
        group=hours[i:i+4]
        if group[0].start_ms%FOUR or group[-1].close_ms!=group[0].start_ms+FOUR:
            raise ValueError("C46_NONALIGNED_FOUR_HOUR_SOURCE")
        out.append(FourBar(group[0].start_ms,group[-1].close_ms,
            max(h.high for h in group),min(h.low for h in group),
            group[0].native_rows[0],group[-1].native_rows[-1]))
    return tuple(out)

def classic_three_fourhour_imb(bars):
    """Strict wick gap a.high<c.low (long) or c.high<a.low (short)."""
    if not isinstance(bars,tuple):
        raise ValueError("C46_UNTRUSTED_4H_SOURCE")
    for i,x in enumerate(bars):
        if (not isinstance(x,FourBar) or x.known_ms!=x.start_ms+FOUR or
            (i and x.start_ms!=bars[i-1].known_ms) or
            not x.first_original3m_id or not x.last_original3m_id):
            raise ValueError("C46_NOT_ORIGINAL_CLOSED_4H_GRID")
    out=[]
    for i in range(2,len(bars)):
        a,m,c=bars[i-2:i+1]
        if c.low>a.high:
            side="LONG";bottom=a.high;top=c.low
        elif c.high<a.low:
            side="SHORT";bottom=c.high;top=a.low
        else:
            continue
        assert bottom<top and c.known_ms>a.known_ms
        out.append(FourHourImbCandidate(side,str(bottom),str(top),
            c.known_ms,a.start_ms,m.start_ms,c.start_ms,
            (a.first_original3m_id,m.first_original3m_id,c.first_original3m_id),
            (a.last_original3m_id,m.last_original3m_id,c.last_original3m_id)))
    return tuple(out)

def original_first_contact(source_rows,candidate,as_of_ms):
    if not isinstance(candidate,FourHourImbCandidate):
        raise ValueError("C46_INVALID_SOURCE_ZONE")
    if candidate.author_poi_certified or candidate.orders or candidate.trades:
        raise ValueError("C46_FORGED_AUTHOR_POI_OR_TRADE")
    if (not isinstance(source_rows,tuple) or
        any(source_rows[k].start_ms!=source_rows[k-1].known_ms
            for k in range(1,len(source_rows))) or
        type(as_of_ms) is not int or as_of_ms%THREE):
        raise ValueError("C46_INVALID_ORIGINAL_NATIVE3M_PREFIX")
    if not source_rows or as_of_ms!=source_rows[-1].known_ms:
        raise ValueError("C46_INCOMPLETE_OR_FUTURE_SOURCE_PREFIX")
    if candidate.fully_known_ms>as_of_ms or candidate.fully_known_ms%FOUR:
        raise ValueError("C46_FUTURE_OR_PARTIAL_4H_CANDIDATE")
    bottom,top=Decimal(candidate.bottom),Decimal(candidate.top)
    if not bottom.is_finite() or not top.is_finite() or bottom<=0 or bottom>=top:
        raise ValueError("C46_FORGED_ZONE_BOUNDARY")
    after=[bar for bar in source_rows if bar.start_ms>=candidate.fully_known_ms]
    if after and after[0].start_ms!=candidate.fully_known_ms:
        raise ValueError("C46_GAPPED_POST_KNOWN_NATIVE3M")
    first=next((bar for bar in after if bar.high>=bottom and bar.low<=top),None)
    return PoiContactObservation(candidate,
        first.start_ms if first else None,
        first.known_ms if first else None,
        first.raw_id if first else None,
        True,
        "FIRST_NATIVE3M_SOURCE_CONTACT_OBSERVED_NOT_ACADEMIC_TEST"
            if first else "UNTOUCHED_IN_COMPLETE_OBSERVED_NATIVE3M_PREFIX")

def inspect_original_4h_imb_source(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    if not rows:
        raise ValueError("C46_MISSING_ORIGINAL_SOURCE_BARS")
    hours=_hours(rows)
    four=aggregate_original_4h(hours)
    candidates=classic_three_fourhour_imb(four)
    observations=tuple(original_first_contact(rows,c,as_of_ms) for c in candidates)
    n=sum(x.first_contact_original3m_id is not None for x in observations)
    if n>len(observations):
        raise ValueError("C46_INVALID_CONTACT_COUNT")
    return C46SourceResult(source.symbol,as_of_ms,len(rows),len(four),
        ACADEMIC_CORE_ID,len(observations),n,len(observations)-n,observations)
