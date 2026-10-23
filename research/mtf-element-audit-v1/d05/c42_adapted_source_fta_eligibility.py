"""C42: three EXPLICITLY ADAPTED source-obstacle eligibility policies.

These policies annotate each accepted C41 4 BOS x 3 Reaction x 3 potential-FTA
research context. C40 source touches use only closed original3m bars before
the BOS candle. The C39 *selection* depends on retrospective BOS candle CLOSE,
so a C42 eligibility result is available NO EARLIER than that close.
No author-approved freshness, no target/entry, no simulated or real order.
PAPER ONLY / NOT_TRADE_READY.
"""
from dataclasses import dataclass
from c21b_original_3m_raid_break_geometry import THREE
from c36_adapted_pivot_hypotheses import VARIANTS
from c36_adapted_slot_registry import ACADEMIC_CORE_ID
from c38_adapted_post_raid_reaction import REACTION_VARIANTS
from c39_adapted_preknown_fta_source import FTA_VARIANTS
from c40_pre_bos_fta_touch_state import STATES
from c41_source_only_bos_reaction_fta_join import (
    C41SourceContext, C41SourceMatrix, scan_original_c41_source_matrix,
)

ELIGIBILITY_POLICIES=(
    "ANY_PREKNOWN_RESEARCH_OBSTACLE_V1",
    "EXCLUDE_PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL_V1",
    "REQUIRE_NO_PRIOR_OBSERVED_TOUCH_V1",
)

@dataclass(frozen=True)
class SourceEligibilityDecision:
    hypothesis_id:str
    eligible:bool
    reason:str
    decision_known_at_ms:int
    author_fta_freshness_approved:bool=False
    author_target_approved:bool=False
    order_allowed:bool=False

@dataclass(frozen=True)
class SourceEligibilityContext:
    symbol:str
    bos_hypothesis_id:str
    reaction_hypothesis_id:str
    fta_hypothesis_id:str
    original_bos_native3m_row_id:str
    original_raid_fractal_center_ms:int
    bos_bar_start_ms:int
    bos_bar_closed_known_ms:int
    potential_obstacle_kind:str|None
    potential_obstacle_known_ms:int|None
    observed_prior_touch_state:str
    prior_touch_original3m_row_id:str|None
    decisions:tuple[SourceEligibilityDecision,...]
    author_freshness_approved:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class EligibilityRoute:
    bos:str
    reaction:str
    fta:str
    parent_contexts:int
    policy_eligible_counts:dict
    observations:tuple[SourceEligibilityContext,...]
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class EligibilityMatrix:
    symbol:str
    as_of_ms:int
    source_original3m_closed:int
    academic_core_id:str
    parent_route_count:int
    policies:tuple[str,...]
    routes:tuple[EligibilityRoute,...]
    author_fta_goldens:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _source_fidelity(c):
    if not isinstance(c,C41SourceContext):
        raise ValueError("C42_UNTRUSTED_SOURCE_CONTEXT")
    if (c.author_bos_approved or c.author_reaction_approved or
        c.author_fta_approved or c.paper_signal_allowed or c.orders or
        c.trades or c.readiness!="NOT_TRADE_READY"):
        raise ValueError("C42_FORGED_AUTHOR_OR_ORDER")
    if c.source_prior_touch_classification not in STATES:
        raise ValueError("C42_UNKNOWN_PRE_BOS_TOUCH_STATE")
    if (c.bos_bar_closed_known_ms!=c.bos_bar_start_ms+THREE or
        not c.original_bos_native3m_row_id or
        c.original_raid_fractal_center_ms>c.bos_bar_start_ms):
        raise ValueError("C42_INVALID_BOS_SOURCE_CHRONOLOGY")
    if c.source_reaction_confirmed:
        if (c.first_reaction_closed_known_ms is None or
            not c.first_reaction_original_native3m_row_id or
            c.first_reaction_closed_known_ms>c.bos_bar_start_ms):
            raise ValueError("C42_FUTURE_OR_UNMATCHED_REACTION")
    elif (c.first_reaction_original_native3m_row_id is not None or
          c.first_reaction_closed_known_ms is not None):
        raise ValueError("C42_INVENTED_REACTION")
    state=c.source_prior_touch_classification
    if c.potential_1h_obstacle_kind is None:
        if (state!="NO_PREKNOWN_FTA_CANDIDATE" or
            c.potential_1h_obstacle_source_known_ms is not None or
            c.original_potential_1h_source_first_native3m_row_id is not None or
            c.first_prior_touch_original_native3m_row_id is not None or
            c.first_prior_full_sweep_or_traversal_ms is not None):
            raise ValueError("C42_INVENTED_MISSING_OBSTACLE")
    else:
        if (not c.original_potential_1h_source_first_native3m_row_id or
            c.potential_1h_obstacle_source_known_ms is None or
            c.potential_1h_obstacle_source_known_ms>c.bos_bar_start_ms or
            c.potential_1h_obstacle_source_known_ms<0 or
            state=="NO_PREKNOWN_FTA_CANDIDATE"):
            raise ValueError("C42_FUTURE_OR_UNPROVEN_SOURCE_OBSTACLE")
        touched=c.first_prior_touch_original_native3m_row_id is not None
        traversed=c.first_prior_full_sweep_or_traversal_ms is not None
        if ((state=="NO_PRIOR_SOURCE_TOUCH" and (touched or traversed)) or
            (state=="PRIOR_BOUNDARY_TOUCH" and (not touched or traversed)) or
            (state=="PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL" and
             (not touched or not traversed))):
            raise ValueError("C42_TOUCH_STATE_EVIDENCE_CONTRADICTION")
        if traversed and (c.first_prior_full_sweep_or_traversal_ms>=c.bos_bar_start_ms or
                          c.first_prior_full_sweep_or_traversal_ms<
                          c.potential_1h_obstacle_source_known_ms):
            raise ValueError("C42_FUTURE_OR_PREKNOWN_TRAVERSAL")
    return state

def decide_source_eligibility(c,policy):
    if policy not in ELIGIBILITY_POLICIES:
        raise ValueError("C42_UNKNOWN_ADAPTED_ELIGIBILITY_POLICY")
    state=_source_fidelity(c)
    if state=="NO_PREKNOWN_FTA_CANDIDATE":
        allowed=False
        reason="NO_C39_SOURCE_OBSTACLE"
    elif policy=="ANY_PREKNOWN_RESEARCH_OBSTACLE_V1":
        allowed=True
        reason="SOURCE_EXISTS_WITHOUT_FRESHNESS_GATE"
    elif state=="PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL":
        allowed=False
        reason="PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL"
    elif policy=="EXCLUDE_PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL_V1":
        allowed=True
        reason=("NO_PRIOR_TOUCH_OBSERVED" if state=="NO_PRIOR_SOURCE_TOUCH" else
                "BOUNDARY_TOUCH_TOLERATED")
    elif state=="PRIOR_BOUNDARY_TOUCH":
        allowed=False
        reason="PRIOR_BOUNDARY_TOUCH"
    else:
        allowed=True
        reason="NO_PRIOR_TOUCH_OBSERVED"
    return SourceEligibilityDecision(policy,allowed,reason,c.bos_bar_closed_known_ms)

def apply_source_eligibility(c41):
    if not isinstance(c41,C41SourceMatrix):
        raise ValueError("C42_UNTRUSTED_PARENT_MATRIX")
    if (c41.academic_core_id!=ACADEMIC_CORE_ID or
        c41.author_goldens or c41.orders or c41.trades or
        c41.readiness!="NOT_TRADE_READY"):
        raise ValueError("C42_ACADEMIC_DRIFT_OR_FORGED_READY")
    expected={(b,r,f) for b in VARIANTS for r in REACTION_VARIANTS for f in FTA_VARIANTS}
    if c41.route_count!=36 or len(c41.routes)!=36 or not expected:
        raise ValueError("C42_PARENT_36_ROUTES_MISSING")
    route_keys=set()
    routes=[]
    for rt in c41.routes:
        key=(rt.bos,rt.reaction,rt.fta)
        if key in route_keys or key not in expected:
            raise ValueError("C42_DUPLICATE_OR_UNKNOWN_SOURCE_ROUTE")
        route_keys.add(key)
        if (len(rt.observations)!=rt.parent_bos_contexts or
            rt.orders or rt.trades or rt.readiness!="NOT_TRADE_READY"):
            raise ValueError("C42_PARENT_ROUTE_COUNT_OR_READY_DRIFT")
        observations=[]
        for c in rt.observations:
            if (c.symbol!=c41.symbol or
                (c.bos_hypothesis_id,c.reaction_hypothesis_id,c.fta_hypothesis_id)!=key or
                c.bos_bar_closed_known_ms>c41.as_of_ms):
                raise ValueError("C42_WRONG_ROUTE_SYMBOL_OR_FUTURE")
            decisions=tuple(decide_source_eligibility(c,p) for p in ELIGIBILITY_POLICIES)
            if any(d.decision_known_at_ms!=c.bos_bar_closed_known_ms or
                   d.author_fta_freshness_approved or d.author_target_approved or
                   d.order_allowed for d in decisions):
                raise ValueError("C42_FORGED_EARLY_OR_ORDER_DECISION")
            observations.append(SourceEligibilityContext(
                c.symbol,rt.bos,rt.reaction,rt.fta,
                c.original_bos_native3m_row_id,c.original_raid_fractal_center_ms,
                c.bos_bar_start_ms,c.bos_bar_closed_known_ms,
                c.potential_1h_obstacle_kind,c.potential_1h_obstacle_source_known_ms,
                c.source_prior_touch_classification,
                c.first_prior_touch_original_native3m_row_id,decisions))
        counts={p:sum(x.decisions[i].eligible for x in observations)
                for i,p in enumerate(ELIGIBILITY_POLICIES)}
        if not (counts[ELIGIBILITY_POLICIES[0]]>=counts[ELIGIBILITY_POLICIES[1]]>=
                counts[ELIGIBILITY_POLICIES[2]]):
            raise ValueError("C42_GATE_MONOTONICITY_VIOLATION")
        routes.append(EligibilityRoute(rt.bos,rt.reaction,rt.fta,
            rt.parent_bos_contexts,counts,tuple(observations)))
    if route_keys!=expected:
        raise ValueError("C42_36_SOURCE_ROUTE_GAP")
    return EligibilityMatrix(c41.symbol,c41.as_of_ms,c41.source_original3m_closed,
        ACADEMIC_CORE_ID,36,ELIGIBILITY_POLICIES,tuple(routes))

def scan_original_source_eligibility(source,*,as_of_ms):
    return apply_source_eligibility(
        scan_original_c41_source_matrix(source,as_of_ms=as_of_ms))
