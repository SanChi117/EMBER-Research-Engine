"""C44: ADAPTED candidate-bounded 1H potential FTA source, NOT academy POI.

Re-evaluates ALL independently verified original 1H FTA candidates from C39,
with native original3m C43 prior-touch classification per candidate, plus
four declared *research-only* bounds on source age, source price distance and
previous fully CLOSED 4H/1D candle range. Prior closed candle range is NOT an
author POI or structural SNR/IMB. The 1%/3% and 24h/72h bounds are NOT fitted
or validated academic parameters and must not be trade-optimized here.

C39 reference price is original 3m BOS candle CLOSE, so final C44 source
selection available no earlier than that CLOSE. No fills or orders.
PAPER ONLY / NOT_TRADE_READY. Never changes C37-C43 source or evidence.
"""
from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal
from c21b_original_3m_raid_break_geometry import _source,_hours,THREE,HOUR
from c28_source_fta_inventory import classic_1h_imb
from c36_adapted_pivot_hypotheses import VARIANTS
from c36_adapted_slot_registry import ACADEMIC_CORE_ID
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted
from c38_adapted_post_raid_reaction import REACTION_VARIANTS
from c39_adapted_preknown_fta_source import (
    FTA_VARIANTS,source_preknown_potential_obstacles,confirmed_1h_fractal_obstacles)
from c43_adapted_per_candidate_fta_rerank import (
    Original3mFirstTouchIndex,_source_registry,_identity,_reorder,
    audit_individual_candidate,scan_original_per_candidate_fta_rerank)

DAY=24*HOUR
FOUR=4*HOUR
POLICIES=(
    "NT_SOURCE_MAX_24H_MAX_1PCT_ADAPTED_V1",
    "NT_SOURCE_MAX_72H_MAX_3PCT_ADAPTED_V1",
    "NT_72H_3PCT_PREV_CLOSED_4H_RANGE_PROXY_V1",
    "NT_72H_3PCT_PREV_CLOSED_1D_RANGE_PROXY_V1",
)
BOUNDS=(
    (24*HOUR,Decimal("1"),None),
    (72*HOUR,Decimal("3"),None),
    (72*HOUR,Decimal("3"),"4H"),
    (72*HOUR,Decimal("3"),"1D"),
)

@dataclass(frozen=True)
class ClosedRange:
    kind:str
    start_ms:int
    close_ms:int
    low:Decimal
    high:Decimal
    source_first_native3m_row_id:str
    source_last_native3m_row_id:str

@dataclass(frozen=True)
class CandidateBound:
    kind:str
    level:str
    first_source_raw3m_id:str
    last_source_raw3m_id:str
    source_known_ms:int
    source_age_at_bos_start_ms:int
    distance_from_retrospective_bos_close_pct:str
    original_prior_touch_state:str

@dataclass(frozen=True)
class C44PolicyReview:
    policy_id:str
    source_preknown_distinct_candidates:int
    source_candidates_passing_policy:int
    selected_candidate:CandidateBound|None
    selected_candidate_rank:int|None
    previous_closed_4h_start_ms:int|None
    previous_closed_1d_start_ms:int|None
    decision_known_at_ms:int
    author_poi_verified:bool=False
    author_fta_verified:bool=False
    trade_allowed:bool=False

@dataclass(frozen=True)
class C44BoundedContext:
    symbol:str
    bos:str
    reaction:str
    fta:str
    original_bos_3m_row_id:str
    original_raid_center_ms:int
    original_bos_start_ms:int
    original_bos_closed_ms:int
    source_reaction_confirmed:bool
    original_c43_no_touch_selected_source_key:tuple|None
    decisions:tuple[C44PolicyReview,...]
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C44BoundedRoute:
    bos:str
    reaction:str
    fta:str
    contexts:tuple[C44BoundedContext,...]
    selected_count_by_policy:dict
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C44BoundedMatrix:
    symbol:str
    as_of_ms:int
    source_native3m_closed:int
    academic_core_id:str
    routes:tuple[C44BoundedRoute,...]
    policies:tuple[str,...]=POLICIES
    academic_author_fta_goldens:int=0
    author_poi_goldens:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def completed_native_candle_ranges(hours,kind):
    if kind not in ("4H","1D"):
        raise ValueError("C44_UNKNOWN_RANGE_TIMEFRAME")
    duration=FOUR if kind=="4H" else DAY
    per=duration//HOUR
    result=[]
    i=0
    while i+per<=len(hours):
        batch=hours[i:i+per]
        if (batch[0].start_ms%duration or
            any(h.start_ms!=batch[0].start_ms+k*HOUR or
                h.close_ms!=h.start_ms+HOUR or len(h.native_rows)!=20
                for k,h in enumerate(batch))):
            raise ValueError("C44_UNTRUSTED_CLOSED_HTF_SOURCE_TIME")
        result.append(ClosedRange(kind,batch[0].start_ms,batch[-1].close_ms,
            min(h.low for h in batch),max(h.high for h in batch),
            batch[0].native_rows[0],batch[-1].native_rows[-1]))
        i+=per
    return tuple(result)

def latest_completed_range(candles,break_start_ms):
    if not candles:return None
    closes=[x.close_ms for x in candles]
    i=bisect_right(closes,break_start_ms)-1
    if i<0:return None
    x=candles[i]
    if x.close_ms>break_start_ms:
        raise ValueError("C44_FUTURE_HTF_SOURCE_RANGE")
    return x

def bound_info(candidate,event):
    if (candidate.touch.orders or candidate.touch.trades or
        candidate.touch.readiness!="NOT_TRADE_READY" or
        candidate.touch.author_freshness_certified or
        candidate.touch.author_target_certified or
        candidate.source.author_priority_attested or
        candidate.source.mitigation_or_freshness_attested or
        candidate.touch.classification=="NO_PREKNOWN_FTA_CANDIDATE"):
        raise ValueError("C44_FORGED_SOURCE_OR_TRADE")
    src=candidate.source
    if src.source_known_ms>event.break_bar_start_ms:
        raise ValueError("C44_FUTURE_SOURCE_CANDIDATE")
    px=Decimal(event.break_close)
    level=Decimal(src.source_level)
    if not (px.is_finite() and px>0 and level.is_finite() and level>0):
        raise ValueError("C44_INVALID_SOURCE_CLOSE_OR_LEVEL")
    delta=level-px if event.side=="LONG" else px-level
    if delta<=0 or Decimal(src.distance_from_retrospective_break_close)!=delta:
        raise ValueError("C44_C39_DISTANCE_SOURCE_DRIFT")
    age=event.break_bar_start_ms-src.source_known_ms
    if age<0:
        raise ValueError("C44_NEGATIVE_SOURCE_AGE")
    return CandidateBound(src.kind,src.source_level,
        src.source_first_native3m_row_id,src.source_last_native3m_row_id,
        src.source_known_ms,age,str(delta*Decimal(100)/px),
        candidate.touch.classification)

def eligible(candidate_info,policy,closed4h,closed1d):
    if policy not in POLICIES:raise ValueError("C44_UNKNOWN_BOUNDED_POLICY")
    age,maxdist,range_kind=BOUNDS[POLICIES.index(policy)]
    if (candidate_info.original_prior_touch_state!="NO_PRIOR_SOURCE_TOUCH" or
        candidate_info.source_age_at_bos_start_ms>age or
        Decimal(candidate_info.distance_from_retrospective_bos_close_pct)>maxdist):
        return False
    ref=closed4h if range_kind=="4H" else closed1d if range_kind=="1D" else None
    if range_kind:
        if ref is None:return False
        val=Decimal(candidate_info.level)
        if not (ref.low<=val<=ref.high):return False
    return True

def evaluate_bounded_candidates(event,source,observed_by_fta,closed4h,closed1d):
    if (event.author_bos_approved or event.paper_trade_allowed or event.orders or
        event.trades or event.readiness!="NOT_TRADE_READY" or
        event.break_bar_closed_known_ms!=event.break_bar_start_ms+THREE):
        raise ValueError("C44_FORGED_BOS_OR_EARLY_DECISION")
    raw=source_preknown_potential_obstacles(event,source["rows"],source["fractals"],source["gaps"])
    identities=set()
    unique=[]
    for x in raw:
        k=_identity(x)
        if k not in identities:
            identities.add(k);unique.append(x)
    verified=tuple(audit_individual_candidate(event,x,source["index"],
        source["registry"],FTA_VARIANTS[0]) for x in unique)
    result={}
    for f in FTA_VARIANTS:
        expected=observed_by_fta[f]
        if (expected.original_bos_3m_row_id!=event.break_original_native3m_row_id or
            expected.original_raid_fractal_center_ms!=event.raid_fractal_center_ms or
            expected.original_bos_closed_ms!=event.break_bar_closed_known_ms):
            raise ValueError("C44_C43_EVENT_PROVENANCE_DRIFT")
        ranked=_reorder(verified,f)
        bound=tuple(bound_info(x,event) for x in ranked)
        expected_no_touch=expected.decisions[2].selected_candidate
        actual_first=next((i for i,c in enumerate(ranked)
                           if c.touch.classification=="NO_PRIOR_SOURCE_TOUCH"),None)
        if expected_no_touch is None:
            if actual_first is not None:raise ValueError("C44_C43_BASELINE_NO_TOUCH_DRIFT")
        else:
            if actual_first is None or _identity(ranked[actual_first].source)!=_identity(expected_no_touch.source):
                raise ValueError("C44_C43_BASELINE_SOURCE_ID_DRIFT")
        reviews=[]
        for policy in POLICIES:
            accepted=[i for i,v in enumerate(bound) if eligible(v,policy,closed4h,closed1d)]
            chosen=accepted[0] if accepted else None
            reviews.append(C44PolicyReview(policy,len(unique),len(accepted),
                bound[chosen] if chosen is not None else None,chosen,
                closed4h.start_ms if closed4h else None,
                closed1d.start_ms if closed1d else None,event.break_bar_closed_known_ms))
        if reviews[0].source_candidates_passing_policy>reviews[1].source_candidates_passing_policy:
            raise ValueError("C44_NESTED_NO_TOUCH_BOUNDS_INCONSISTENT")
        if reviews[2].source_candidates_passing_policy>reviews[1].source_candidates_passing_policy or (
            reviews[3].source_candidates_passing_policy>reviews[1].source_candidates_passing_policy):
            raise ValueError("C44_RANGE_PROXY_FILTER_NOT_SUBSET")
        result[f]=(tuple(reviews),_identity(expected_no_touch.source) if expected_no_touch else None)
    return result

def scan_original_c44_bounded_source(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    hours=_hours(rows)
    original=scan_original_per_candidate_fta_rerank(source,as_of_ms=as_of_ms)
    b=scan_original_3m_adapted(source,as_of_ms=as_of_ms)
    if (original.academic_core_id!=ACADEMIC_CORE_ID or
        original.author_fta_goldens or original.orders or original.trades or
        original.readiness!="NOT_TRADE_READY" or
        b.academic_core_sha256!=ACADEMIC_CORE_ID or b.orders or b.trades or
        b.author_bos_approved or b.readiness!="NOT_TRADE_READY"):
        raise ValueError("C44_PARENT_ACADEMIC_OR_READINESS_DRIFT")
    r4=completed_native_candle_ranges(hours,"4H")
    r1=completed_native_candle_ranges(hours,"1D")
    registry=_source_registry(confirmed_1h_fractal_obstacles(hours),classic_1h_imb(hours))
    source_inputs={"rows":rows,"fractals":confirmed_1h_fractal_obstacles(hours),
        "gaps":classic_1h_imb(hours),"index":Original3mFirstTouchIndex(rows),
        "registry":registry}
    parents={(r.bos,r.reaction,r.fta):r for r in original.routes}
    keys={(bos,reaction,fta) for bos in VARIANTS for reaction in REACTION_VARIANTS for fta in FTA_VARIANTS}
    if set(parents)!=keys or len(original.routes)!=36:
        raise ValueError("C44_C43_PARENT_ROUTE_SET_DRIFT")
    rechecked={}
    for stream in b.routes:
        for i,e in enumerate(stream.events):
            by_fta={fta:parents[(stream.hypothesis_id,REACTION_VARIANTS[0],fta)].contexts[i]
                    for fta in FTA_VARIANTS}
            prior4=latest_completed_range(r4,e.break_bar_start_ms)
            prior1=latest_completed_range(r1,e.break_bar_start_ms)
            checked=evaluate_bounded_candidates(e,source_inputs,by_fta,prior4,prior1)
            for f,value in checked.items():rechecked[(stream.hypothesis_id,f,i)]=value
    routes=[]
    for stream in b.routes:
        for reaction in REACTION_VARIANTS:
            for fta in FTA_VARIANTS:
                parent=parents[(stream.hypothesis_id,reaction,fta)]
                if len(parent.contexts)!=len(stream.events):
                    raise ValueError("C44_C43_PARENT_EVENT_COUNT_DRIFT")
                contexts=[]
                for i,(e,x) in enumerate(zip(stream.events,parent.contexts)):
                    if (x.original_bos_3m_row_id!=e.break_original_native3m_row_id or
                        x.original_raid_fractal_center_ms!=e.raid_fractal_center_ms or
                        x.original_bos_closed_ms!=e.break_bar_closed_known_ms or
                        x.bos!=stream.hypothesis_id or x.reaction!=reaction or
                        x.fta!=fta or x.orders or x.trades or
                        x.readiness!="NOT_TRADE_READY"):
                        raise ValueError("C44_C43_PARENT_EVENT_MISMATCH")
                    decisions,source_key=rechecked[(stream.hypothesis_id,fta,i)]
                    if (x.decisions[2].selected_candidate is None)!=(source_key is None):
                        raise ValueError("C44_C43_NO_TOUCH_GATING_DRIFT")
                    contexts.append(C44BoundedContext(e.symbol,stream.hypothesis_id,
                        reaction,fta,e.break_original_native3m_row_id,
                        e.raid_fractal_center_ms,e.break_bar_start_ms,
                        e.break_bar_closed_known_ms,x.source_reaction_confirmed,
                        source_key,decisions))
                counts={p:sum(c.decisions[j].selected_candidate is not None for c in contexts)
                        for j,p in enumerate(POLICIES)}
                if not (counts[POLICIES[0]]<=counts[POLICIES[1]] and
                        counts[POLICIES[2]]<=counts[POLICIES[1]] and
                        counts[POLICIES[3]]<=counts[POLICIES[1]]):
                    raise ValueError("C44_ROUTE_ELIGIBILITY_RELATION_DRIFT")
                routes.append(C44BoundedRoute(stream.hypothesis_id,reaction,fta,
                    tuple(contexts),counts))
    if len(routes)!=36:raise ValueError("C44_36_SOURCE_ROUTES_MISSING")
    return C44BoundedMatrix(source.symbol,as_of_ms,len(rows),ACADEMIC_CORE_ID,tuple(routes))
