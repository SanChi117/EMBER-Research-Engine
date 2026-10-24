"""C49: FIRST later fully closed original3m directional exit after C46 4H IMB contact.

SOURCE-only technical observation, not course-certified POI, reaction,
Volume Confirmation, order, stop or TP. No same-bar contact/reaction:
price OHLC wicks do not establish intrabar order. Separate preregistered
1h/4h/12h horizons; windows measured from first 3m contact bar CLOSE.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21_native3m_source_bridge import Original3mRow
from c21b_original_3m_raid_break_geometry import _source,THREE,HOUR
from c46_original_4h_classic_imb_first_contact import (
    inspect_original_4h_imb_source,PoiContactObservation)

HORIZONS=(
    ("C49_ADAPTED_1H_FIRST_LATER_3M_CLOSE_V1",HOUR),
    ("C49_ADAPTED_4H_FIRST_LATER_3M_CLOSE_V1",4*HOUR),
    ("C49_ADAPTED_12H_FIRST_LATER_3M_CLOSE_V1",12*HOUR),
)
VALID_STATES={
    "NO_PARENT_4H_FIRST_CONTACT_AS_OF",
    "FIRST_LATER_FAVORABLE_3M_CLOSE",
    "FIRST_LATER_ADVERSE_3M_CLOSE",
    "NO_LATER_DIRECTIONAL_CLOSE_WINDOW_OPEN",
    "NO_LATER_DIRECTIONAL_CLOSE_HORIZON_COMPLETE",
}

@dataclass(frozen=True)
class C49DirectionalCloseObservation:
    horizon_id:str
    horizon_ms:int
    as_of_ms:int
    status:str
    first_later_event_original3m_id:str|None
    first_later_event_close_known_ms:int|None
    first_later_event_close_price:str|None
    favorable_3m_close:bool
    adverse_3m_close:bool
    author_reaction_certified:bool=False
    author_volume_confirmation_certified:bool=False
    trades:tuple=()
    orders:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C49ParentReactionSource:
    original_4h_zone_side:str
    original_4h_zone_fully_known_ms:int
    source_original3m_first_contact_id:str|None
    source_original3m_first_contact_closed_ms:int|None
    window_observations:tuple[C49DirectionalCloseObservation,...]
    academic_valid_first_test:bool=False
    academic_valid_reaction:bool=False
    trades:tuple=()
    orders:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C49SourceReview:
    symbol:str
    as_of_ms:int
    original_native3m_closed:int
    original_4h_source_candidates:int
    native3m_first_contact_count:int
    window_count:int
    observations:tuple[C49ParentReactionSource,...]
    course_reaction_goldens:int=0
    course_volume_confirmation_goldens:int=0
    trades:tuple=()
    orders:tuple=()
    readiness:str="NOT_TRADE_READY"

def observe_post_contact_directional_close(rows,obs,*,as_of_ms,horizon_id):
    if not isinstance(obs,PoiContactObservation):
        raise ValueError("C49_UNTRUSTED_C46_4H_CONTACT_SOURCE")
    c=obs.candidate
    if (c.author_poi_certified or c.orders or c.trades or
        obs.academic_poi_test_certified or obs.academic_volume_confirmation_certified
        or obs.orders or obs.trades or obs.readiness!="NOT_TRADE_READY"
        or not obs.has_complete_original3m_prefix_after_known):
        raise ValueError("C49_FORGED_AUTHOR_POI_OR_TRADE")
    if (c.side not in ("LONG","SHORT")
        or c.source_status!="C46_NATIVE_4H_CLASSIC_IMB_GEOMETRY_ONLY"
        or type(as_of_ms) is not int or as_of_ms%THREE or
        as_of_ms<c.fully_known_ms):
        raise ValueError("C49_INVALID_ZONE_DIRECTION_OR_ASOF")
    periods=dict(HORIZONS)
    if horizon_id not in periods:
        raise ValueError("C49_UNREGISTERED_SOURCE_HORIZON")
    if not isinstance(rows,tuple) or not rows:
        raise ValueError("C49_NO_COMPLETE_SOURCE_PREFIX")
    if rows[-1].known_ms!=as_of_ms:
        raise ValueError("C49_INCOMPLETE_3M_CLOSED_SOURCE_PREFIX")
    for i,r in enumerate(rows):
        if (not isinstance(r,Original3mRow) or
            r.known_ms!=r.start_ms+THREE or
            (i and r.start_ms!=rows[i-1].known_ms) or
            not r.raw_id or
            any(type(v) is not Decimal or not v.is_finite()
                for v in (r.open,r.high,r.low,r.close)) or
            not (0<r.low<=min(r.open,r.close)<=max(r.open,r.close)<=r.high)):
            raise ValueError("C49_MALFORMED_OR_NONCONTIGUOUS_3M_SOURCE")
    lo=Decimal(c.bottom);hi=Decimal(c.top)
    if not (lo.is_finite() and hi.is_finite() and 0<lo<hi):
        raise ValueError("C49_INVALID_4H_SOURCE_WICK_GAP")
    window=periods[horizon_id]
    contact=obs.first_contact_closed_known_ms
    if contact is None:
        if (obs.first_contact_original3m_id is not None or
            obs.first_contact_bar_start_ms is not None):
            raise ValueError("C49_FICTITIOUS_3M_CONTACT_ID")
        return C49DirectionalCloseObservation(horizon_id,window,as_of_ms,
            "NO_PARENT_4H_FIRST_CONTACT_AS_OF",None,None,None,False,False)
    if (type(contact) is not int or contact%THREE or
        contact>as_of_ms or contact<c.fully_known_ms+THREE or
        obs.first_contact_bar_start_ms!=contact-THREE or
        not obs.first_contact_original3m_id):
        raise ValueError("C49_INVALID_FIRST_CONTACT_CLOSED_CHRONOLOGY")
    first_contact_rows=[r for r in rows if r.known_ms==contact]
    if (len(first_contact_rows)!=1 or
        first_contact_rows[0].raw_id!=obs.first_contact_original3m_id or
        first_contact_rows[0].high<lo or first_contact_rows[0].low>hi):
        raise ValueError("C49_FIRST_CONTACT_NOT_IN_ORIGINAL_SOURCE")
    event=None
    cutoff=min(as_of_ms,contact+window)
    for bar in rows:
        if bar.start_ms<contact:continue  # exclude SAME contact bar
        if bar.known_ms>cutoff:break
        favorable=(bar.close>hi if c.side=="LONG" else bar.close<lo)
        adverse=(bar.close<lo if c.side=="LONG" else bar.close>hi)
        if favorable or adverse:
            event=(bar,favorable,adverse)
            break
    if event is not None:
        bar,fav,adv=event
        if fav==adv:raise ValueError("C49_AMBIGUOUS_SINGLE_CLOSE_DIRECTION")
        state=("FIRST_LATER_FAVORABLE_3M_CLOSE" if fav
               else "FIRST_LATER_ADVERSE_3M_CLOSE")
        return C49DirectionalCloseObservation(horizon_id,window,as_of_ms,
            state,bar.raw_id,bar.known_ms,str(bar.close),fav,adv)
    state=("NO_LATER_DIRECTIONAL_CLOSE_WINDOW_OPEN" if as_of_ms<contact+window
           else "NO_LATER_DIRECTIONAL_CLOSE_HORIZON_COMPLETE")
    return C49DirectionalCloseObservation(horizon_id,window,as_of_ms,
        state,None,None,None,False,False)

def inspect_original_source_4h_contact_directional_close(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    parent=inspect_original_4h_imb_source(source,as_of_ms=as_of_ms)
    if (parent.orders or parent.trades or parent.author_poi_goldens or
        parent.readiness!="NOT_TRADE_READY" or
        len(parent.observations)!=parent.candidate_count):
        raise ValueError("C49_FORGED_C46_AUTHOR_APPROVAL_OR_PARENT_COUNT")
    results=[]
    for obs in parent.observations:
        decisions=tuple(observe_post_contact_directional_close(
            rows,obs,as_of_ms=as_of_ms,horizon_id=pid) for pid,_ in HORIZONS)
        results.append(C49ParentReactionSource(obs.candidate.side,
            obs.candidate.fully_known_ms,obs.first_contact_original3m_id,
            obs.first_contact_closed_known_ms,decisions))
    if sum(x.source_original3m_first_contact_id is not None for x in results)!=parent.first_original3m_contact_count:
        raise ValueError("C49_PARENT_CONTACT_DRIFT")
    return C49SourceReview(parent.symbol,as_of_ms,len(rows),
        len(results),parent.first_original3m_contact_count,len(HORIZONS),
        tuple(results))
