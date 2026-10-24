"""C48: preregistered SOURCE-ONLY time-to-1H IMB windows after C47 4H first contact.

This is not course VC. No returns, trading, author POI, stops or fills.
Policies 6/24/72 hours are independent declared alternatives, not tuned to PnL.
C47's full-history earliest 1H source is masked until fully closed at as-of;
status also masks future parent zone formation and future 3m first contact.
"""
from dataclasses import dataclass
from c21b_original_3m_raid_break_geometry import THREE,HOUR
from c47_post_4h_contact_1h_imb_source_link import (
    FourToOneSourceObservation,C47SourceJoin)

WINDOWS=(
    ("C48_ADAPTED_6H_POST_CONTACT_1H_CLOSE_V1",6*HOUR),
    ("C48_ADAPTED_24H_POST_CONTACT_1H_CLOSE_V1",24*HOUR),
    ("C48_ADAPTED_72H_POST_CONTACT_1H_CLOSE_V1",72*HOUR),
)
OUTCOMES=(
    "PARENT_4H_SOURCE_NOT_YET_KNOWN",
    "NO_ORIGINAL_3M_CONTACT_KNOWN_AS_OF",
    "WINDOW_OPEN_NO_1H_SOURCE_KNOWN",
    "WINDOW_ELAPSED_WITHOUT_1H_SOURCE",
    "LATER_1H_SOURCE_WITHIN_WINDOW",
    "FIRST_LATER_1H_SOURCE_AFTER_WINDOW",
)

@dataclass(frozen=True)
class C48WindowDecision:
    window_policy:str
    window_ms:int
    snapshot_as_of_ms:int
    state:str
    passes_research_source_window:bool
    observed_first_1h_lag_ms:int|None
    selected_first_1h_raw_native3m_id:str|None
    author_volume_confirmation_certified:bool=False
    author_poi_test_certified:bool=False
    trades:tuple=()
    orders:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C48ContextReview:
    parent_4h_source_known_ms:int
    selected_original3m_first_contact_id:str|None
    policy_decisions:tuple[C48WindowDecision,...]
    author_poi_certified:bool=False
    author_volume_confirmation_certified:bool=False
    trades:tuple=()
    orders:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C48WindowReview:
    symbol:str
    snapshot_as_of_ms:int
    source_parent_context_count:int
    completed_source_parent_contacts:int
    policy_count:int
    outcomes:tuple[C48ContextReview,...]
    author_poi_test_goldens:int=0
    author_1h_vc_goldens:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _validate_parent(obs):
    if not isinstance(obs,FourToOneSourceObservation):
        raise ValueError("C48_UNTRUSTED_C47_SOURCE_CONTEXT")
    if (obs.course_typed_poi_approved or obs.course_first_valid_test_approved
        or obs.course_volume_confirmation_approved or obs.author_chart_golden_count
        or obs.orders or obs.trades or obs.readiness!="NOT_TRADE_READY"):
        raise ValueError("C48_FORGED_AUTHOR_APPROVAL_OR_ORDER")
    if (obs.original4h_zone_side not in ("LONG","SHORT")
        or type(obs.original4h_zone_known_ms) is not int
        or obs.original4h_zone_known_ms%(4*HOUR)
        or len(obs.original4h_zone_first_raw3m_ids)!=3
        or any(not isinstance(s,str) or not s for s in obs.original4h_zone_first_raw3m_ids)):
        raise ValueError("C48_INVALID_PARENT_SOURCE_PROVENANCE")
    touch=obs.original4h_first_contact_closed_known_ms
    selected=obs.first_post_contact_1h_imb_source
    if touch is None:
        if (obs.original4h_first_contact_native3m_id is not None
            or obs.post_contact_same_side_1h_candidate_count
            or selected is not None):
            raise ValueError("C48_FICTITIOUS_FIRST_CONTACT")
    elif (type(touch) is not int or touch%THREE or
          touch<=obs.original4h_zone_known_ms or
          not obs.original4h_first_contact_native3m_id):
        raise ValueError("C48_INVALID_FIRST_CONTACT_TIME")
    if selected is None:
        if obs.post_contact_same_side_1h_candidate_count!=0:
            raise ValueError("C48_MISSING_FIRST_1H_CANDIDATE")
    elif (touch is None or obs.post_contact_same_side_1h_candidate_count<=0
          or selected.academic_vc_certified or selected.orders or selected.trades
          or selected.side!=obs.original4h_zone_side
          or selected.first_hour_start_ms<touch
          or selected.fully_known_ms!=selected.third_hour_start_ms+HOUR
          or selected.fully_known_ms<=touch
          or len(selected.first_raw_native3m_ids)!=3
          or any(not x for x in selected.first_raw_native3m_ids)):
        raise ValueError("C48_FORGED_OR_PRECONTACT_1H_SOURCE")
    return touch,selected

def evaluate_source_window(obs,*,as_of_ms,policy):
    touch,selected=_validate_parent(obs)
    if type(as_of_ms) is not int or as_of_ms<0 or as_of_ms%THREE:
        raise ValueError("C48_NOT_CLOSED_NATIVE3M_SNAPSHOT")
    windows=dict(WINDOWS)
    if policy not in windows:
        raise ValueError("C48_UNKNOWN_PREREGISTERED_SOURCE_WINDOW")
    window=windows[policy]
    state="NO_ORIGINAL_3M_CONTACT_KNOWN_AS_OF"
    available=None
    if obs.original4h_zone_known_ms>as_of_ms:
        state="PARENT_4H_SOURCE_NOT_YET_KNOWN"
    elif touch is None or touch>as_of_ms:
        state="NO_ORIGINAL_3M_CONTACT_KNOWN_AS_OF"
    elif selected is not None and selected.fully_known_ms<=as_of_ms:
        available=selected.fully_known_ms-touch
        state=("LATER_1H_SOURCE_WITHIN_WINDOW" if available<=window
               else "FIRST_LATER_1H_SOURCE_AFTER_WINDOW")
    elif as_of_ms<touch+window:
        state="WINDOW_OPEN_NO_1H_SOURCE_KNOWN"
    else:
        state="WINDOW_ELAPSED_WITHOUT_1H_SOURCE"
    return C48WindowDecision(policy,window,as_of_ms,state,
        state=="LATER_1H_SOURCE_WITHIN_WINDOW",
        available,
        selected.first_raw_native3m_ids[0] if available is not None else None)

def inspect_c47_source_windows(parent,*,as_of_ms):
    if not isinstance(parent,C47SourceJoin):
        raise ValueError("C48_UNTRUSTED_C47_PARENT_SOURCE")
    if (parent.author_vc_goldens or parent.author_poi_goldens
        or parent.orders or parent.trades or parent.readiness!="NOT_TRADE_READY"):
        raise ValueError("C48_FORGED_PARENT_TRADE_OR_VC")
    if type(as_of_ms) is not int or as_of_ms%THREE or as_of_ms>parent.as_of_ms:
        raise ValueError("C48_FUTURE_OR_PARTIAL_PARENT_ASOF")
    if (len(parent.observations)!=parent.original_source4h_candidates
        or sum(x.original4h_first_contact_native3m_id is not None
               for x in parent.observations)!=parent.original_source4h_first_contacts):
        raise ValueError("C48_PARENT_COUNTS_INCONSISTENT")
    reviews=tuple(C48ContextReview(x.original4h_zone_known_ms,
        x.original4h_first_contact_native3m_id
            if x.original4h_first_contact_closed_known_ms is not None
            and x.original4h_first_contact_closed_known_ms<=as_of_ms else None,
        tuple(evaluate_source_window(x,as_of_ms=as_of_ms,policy=pid) for pid,_ in WINDOWS))
        for x in parent.observations)
    return C48WindowReview(parent.symbol,as_of_ms,len(parent.observations),
        sum(x.selected_original3m_first_contact_id is not None for x in reviews),
        len(WINDOWS),reviews)
