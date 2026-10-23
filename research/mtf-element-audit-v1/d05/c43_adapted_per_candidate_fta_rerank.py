"""C43 ADAPTED source-only FTA reselection over ALL source-preknown candidates.

Independently audit each original 1H candidate (fractal/3-hour IMB) against
original closed native3m wicks strictly before BOS BAR START. Rank only at
BOS BAR CLOSE because C39 candidate distances use retrospective BOS close.
Three inherited C39 family priorities × three independent C42 touch gates.
Zero instructor certification, fill inference, target orders, trades or PnL.
PAPER ONLY / NOT_TRADE_READY. Frozen C39/C40/C41/C42 are not changed.
"""
from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal
from c21b_original_3m_raid_break_geometry import _source, _hours, THREE
from c28_source_fta_inventory import classic_1h_imb
from c36_adapted_pivot_hypotheses import VARIANTS
from c36_adapted_slot_registry import ACADEMIC_CORE_ID
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted
from c38_adapted_post_raid_reaction import REACTION_VARIANTS
from c39_adapted_preknown_fta_source import (
    FTA_VARIANTS, PotentialObstacle, confirmed_1h_fractal_obstacles,
    source_preknown_potential_obstacles)
from c40_pre_bos_fta_touch_state import TouchAudit, STATES
from c41_source_only_bos_reaction_fta_join import scan_original_c41_source_matrix
from c42_adapted_source_fta_eligibility import (
    ELIGIBILITY_POLICIES, decide_source_eligibility)

FRACTALS=("BSL_1H_FRACTAL","SSL_1H_FRACTAL")
IMBS=("BULL_CLASSIC_IMB","BEAR_CLASSIC_IMB")

@dataclass(frozen=True)
class CandidateObservation:
    source:PotentialObstacle
    touch:TouchAudit

@dataclass(frozen=True)
class ReRankDecision:
    eligibility_policy_id:str
    known_at_ms:int
    eligible_candidate_count:int
    original_selected_gate_eligible:bool
    selected_candidate:CandidateObservation|None
    selected_candidate_rank:int|None
    substituted_after_original_gate_rejection:bool
    author_fta_approved:bool=False
    order_allowed:bool=False

@dataclass(frozen=True)
class ReRankContext:
    symbol:str
    bos_hypothesis_id:str
    reaction_hypothesis_id:str
    fta_hypothesis_id:str
    original_bos_3m_row_id:str
    original_raid_fractal_center_ms:int
    bos_bar_start_ms:int
    bos_bar_closed_known_ms:int
    source_reaction_confirmed:bool
    source_preknown_candidate_count:int
    distinct_source_candidate_count:int
    original_c39_candidate:CandidateObservation|None
    decisions:tuple[ReRankDecision,...]
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class ReRankRoute:
    bos:str
    reaction:str
    fta:str
    parent_contexts:int
    selected_by_policy:dict
    replacements_by_policy:dict
    contexts:tuple[ReRankContext,...]
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class ReRankMatrix:
    symbol:str
    as_of_ms:int
    source_original3m_closed:int
    academic_core_id:str
    original_c41_routes:int
    adapted_policies:tuple[str,...]
    routes:tuple[ReRankRoute,...]
    author_fta_goldens:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

class Original3mFirstTouchIndex:
    """Segment-tree search is exact at a leaf; node bounds only prune.

    Every returned row is an original input row; OHLC cannot infer intrabar
    crossing order or execution. All searches explicitly end BEFORE BOS.
    """
    def __init__(self,rows):
        if not rows:
            raise ValueError("C43_MISSING_ORIGINAL_NATIVE3M")
        self.rows=tuple(rows)
        self.closes=tuple(x.known_ms for x in rows)
        if any(x.known_ms!=x.start_ms+THREE or not x.raw_id or
               (i and (x.start_ms!=rows[i-1].known_ms or
                       x.symbol!=rows[0].symbol))
               for i,x in enumerate(rows)):
            raise ValueError("C43_UNTRUSTED_NATIVE3M_GRID")
        n=1
        while n<len(rows):
            n*=2
        self.size=n
        self.low=[Decimal("Infinity")]*(2*n)
        self.high=[Decimal("-Infinity")]*(2*n)
        for i,x in enumerate(rows):
            self.low[n+i]=x.low
            self.high[n+i]=x.high
        for i in range(n-1,0,-1):
            self.low[i]=min(self.low[2*i],self.low[2*i+1])
            self.high[i]=max(self.high[2*i],self.high[2*i+1])

    def find_first(self,start,stop,low_cap=None,high_floor=None,low_strict=False,high_strict=False):
        if not (0<=start<=stop<=len(self.rows)):
            raise ValueError("C43_NATIVE3M_RANGE_INVALID")
        if low_cap is None and high_floor is None:
            raise ValueError("C43_EMPTY_TOUCH_PREDICATE")
        def eligible(i):
            if low_cap is not None and (self.low[i]>=low_cap if low_strict else self.low[i]>low_cap):
                return False
            if high_floor is not None and (self.high[i]<=high_floor if high_strict else self.high[i]<high_floor):
                return False
            return True
        def recurse(node,left,right):
            if right<=start or left>=stop or not eligible(node):
                return None
            if right-left==1:
                return left if left<len(self.rows) else None
            middle=(left+right)//2
            first=recurse(node*2,left,middle)
            return first if first is not None else recurse(node*2+1,middle,right)
        return recurse(1,0,self.size)

def _identity(s):
    return (s.kind,s.source_known_ms,s.source_level,
        s.source_first_native3m_row_id,s.source_last_native3m_row_id)

def _source_registry(fractals,gaps):
    registry={}
    for kind,level,known,first,last in fractals:
        key=(kind,known,str(level),first,last)
        registry.setdefault(key,[]).append(("fractal",level,None,None))
    for gap in gaps:
        for edge in (gap.bottom,gap.top):
            key=(gap.kind,gap.known_ms,str(edge),
                gap.original_1h_row_ids[0],gap.original_1h_row_ids[-1])
            registry.setdefault(key,[]).append(("imb",edge,gap.bottom,gap.top))
    return registry

def audit_individual_candidate(event,source,index,registry,fta_hypothesis):
    if not isinstance(source,PotentialObstacle):
        raise ValueError("C43_UNTRUSTED_FTA_OBSTACLE")
    if source.author_priority_attested or source.mitigation_or_freshness_attested:
        raise ValueError("C43_FORGED_AUTHOR_FTA")
    if (source.source_known_ms>event.break_bar_start_ms or
        source.source_known_ms<index.closes[0] or
        event.break_bar_closed_known_ms!=event.break_bar_start_ms+THREE):
        raise ValueError("C43_FUTURE_OR_INVALID_OBSTACLE")
    variants=registry.get(_identity(source),())
    if len(variants)!=1:
        raise ValueError("C43_FTA_SOURCE_PROVENANCE_MISSING_OR_AMBIGUOUS")
    family,level,bottom,top=variants[0]
    expected=(("BSL_1H_FRACTAL" if event.side=="LONG" else "SSL_1H_FRACTAL"))
    if family=="fractal" and source.kind!=expected:
        raise ValueError("C43_INCORRECT_DIRECTIONAL_FRACTAL")
    try:
        expected_level=Decimal(source.source_level)
    except (ValueError,ArithmeticError,TypeError) as exc:
        raise ValueError("C43_NON_DECIMAL_SOURCE_LEVEL") from exc
    if not expected_level.is_finite() or expected_level<=0 or expected_level!=level:
        raise ValueError("C43_INVALID_PRICE_OR_SOURCE")
    idx,mod=divmod(event.break_bar_start_ms-index.rows[0].start_ms,THREE)
    if (mod or idx<0 or idx>=len(index.rows) or
        index.rows[idx].raw_id!=event.break_original_native3m_row_id or
        index.rows[idx].known_ms!=event.break_bar_closed_known_ms):
        raise ValueError("C43_BOS_RAW_SHA_OR_GRID_MISMATCH")
    begin=bisect_right(index.closes,source.source_known_ms)
    stop=bisect_right(index.closes,event.break_bar_start_ms)
    if stop!=idx:
        raise ValueError("C43_BOS_PRIOR_CANDLE_CUTOFF_DRIFT")
    if family=="fractal" and event.side=="LONG":
        first=index.find_first(begin,stop,high_floor=level)
        sweep=index.find_first(begin,stop,high_floor=level,high_strict=True)
    elif family=="fractal":
        first=index.find_first(begin,stop,low_cap=level)
        sweep=index.find_first(begin,stop,low_cap=level,low_strict=True)
    else:
        first=index.find_first(begin,stop,low_cap=top,high_floor=bottom)
        sweep=index.find_first(begin,stop,low_cap=bottom,high_floor=top)
    if sweep is not None and (first is None or sweep<first):
        raise ValueError("C43_IMPOSSIBLE_FIRST_SWEEP_CHRONOLOGY")
    state=("PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL" if sweep is not None else
           "PRIOR_BOUNDARY_TOUCH" if first is not None else
           "NO_PRIOR_SOURCE_TOUCH")
    touch=TouchAudit(event.symbol,event.hypothesis_id,fta_hypothesis,
        event.break_original_native3m_row_id,source.kind,source.source_level,
        source.source_known_ms,index.rows[first].start_ms if first is not None else None,
        index.rows[first].raw_id if first is not None else None,
        index.rows[sweep].start_ms if sweep is not None else None,state)
    if state not in STATES or touch.orders or touch.trades:
        raise ValueError("C43_FORGED_TOUCH_STATE")
    return CandidateObservation(source,touch)

def _reorder(candidates,hypothesis):
    if hypothesis not in FTA_VARIANTS:
        raise ValueError("C43_UNKNOWN_FTA_FAMILY_RANK")
    if hypothesis==FTA_VARIANTS[0]:
        return tuple(candidates)
    primary=FRACTALS if hypothesis==FTA_VARIANTS[1] else IMBS
    return tuple(x for x in candidates if x.source.kind in primary)+tuple(
        x for x in candidates if x.source.kind not in primary)

def _allow(touch_state,policy):
    if policy not in ELIGIBILITY_POLICIES:
        raise ValueError("C43_UNKNOWN_TOUCH_POLICY")
    if touch_state not in STATES or touch_state=="NO_PREKNOWN_FTA_CANDIDATE":
        raise ValueError("C43_INVALID_INDIVIDUAL_CANDIDATE_TOUCH")
    if policy==ELIGIBILITY_POLICIES[0]:
        return True
    if policy==ELIGIBILITY_POLICIES[1]:
        return touch_state!="PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL"
    return touch_state=="NO_PRIOR_SOURCE_TOUCH"

def choose_ranked_candidate(ordered,policy):
    """Pure causal post-BOS rank decision; NONE when no candidate passes."""
    found=None
    for i,c in enumerate(ordered):
        if not isinstance(c,CandidateObservation):
            raise ValueError("C43_FORGED_RANKED_CANDIDATE")
        ok=_allow(c.touch.classification,policy)
        if found is None and ok:
            found=(i,c)
    return found

def rerank_event(event,rows,index,fractals,gaps,registry,original_by_fta):
    """Compute all candidate touches ONCE for BOS then 3×3 pure rankings."""
    raw=source_preknown_potential_obstacles(event,rows,fractals,gaps)
    seen=set()
    distinct=[]
    for s in raw:
        identity=_identity(s)
        if identity not in seen:
            seen.add(identity)
            distinct.append(s)
    audited=tuple(audit_individual_candidate(event,s,index,registry,FTA_VARIANTS[0])
                  for s in distinct)
    result={}
    for hypothesis in FTA_VARIANTS:
        parent=original_by_fta[hypothesis]
        if (parent.original_bos_native3m_row_id!=event.break_original_native3m_row_id or
            parent.original_raid_fractal_center_ms!=event.raid_fractal_center_ms or
            parent.bos_bar_closed_known_ms!=event.break_bar_closed_known_ms):
            raise ValueError("C43_PARENT_EVENT_DRIFT")
        ordered=_reorder(audited,hypothesis)
        prior=parent.potential_1h_obstacle_kind
        baseline=ordered[0] if ordered else None
        if (len(raw)==0)!=(prior is None):
            raise ValueError("C43_ORIGINAL_SELECTED_MISSING_DRIFT")
        if baseline is not None:
            x=baseline.source
            if (x.kind!=prior or
                x.source_known_ms!=parent.potential_1h_obstacle_source_known_ms or
                x.source_first_native3m_row_id!=parent.original_potential_1h_source_first_native3m_row_id or
                baseline.touch.classification!=parent.source_prior_touch_classification or
                baseline.touch.first_touch_original3m_row_id!=parent.first_prior_touch_original_native3m_row_id or
                baseline.touch.first_full_sweep_or_traversal_ms!=parent.first_prior_full_sweep_or_traversal_ms):
                raise ValueError("C43_C39_C40_ORIGINAL_SELECTED_SOURCE_DRIFT")
        decisions=[]
        for policy in ELIGIBILITY_POLICIES:
            old_gate=decide_source_eligibility(parent,policy)
            if old_gate.eligible!=(baseline is not None and
                                  _allow(baseline.touch.classification,policy)):
                raise ValueError("C43_C42_ORIGINAL_GATE_DRIFT")
            selected=choose_ranked_candidate(ordered,policy)
            chosen_rank,chosen=(selected if selected is not None else (None,None))
            if policy==ELIGIBILITY_POLICIES[0] and chosen!=baseline:
                raise ValueError("C43_UNFILTERED_C39_BASELINE_DRIFT")
            decisions.append(ReRankDecision(policy,event.break_bar_closed_known_ms,
                sum(_allow(c.touch.classification,policy) for c in ordered),
                old_gate.eligible, chosen,chosen_rank,
                chosen is not None and baseline is not None and chosen!=baseline))
        result[hypothesis]=(len(raw),len(distinct),baseline,tuple(decisions))
    return result

def scan_original_per_candidate_fta_rerank(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    index=Original3mFirstTouchIndex(rows)
    hours=_hours(rows)
    fractals=confirmed_1h_fractal_obstacles(hours)
    gaps=classic_1h_imb(hours)
    registry=_source_registry(fractals,gaps)
    c41=scan_original_c41_source_matrix(source,as_of_ms=as_of_ms)
    bos=scan_original_3m_adapted(source,as_of_ms=as_of_ms)
    if (c41.academic_core_id!=ACADEMIC_CORE_ID or
        c41.orders or c41.trades or c41.author_goldens or
        c41.readiness!="NOT_TRADE_READY" or
        bos.academic_core_sha256!=ACADEMIC_CORE_ID or
        bos.orders or bos.trades or bos.author_bos_approved or
        bos.readiness!="NOT_TRADE_READY" or c41.route_count!=36):
        raise ValueError("C43_PARENT_AUTHOR_OR_READINESS_DRIFT")
    parents={(route.bos,route.reaction,route.fta):route for route in c41.routes}
    expected={(b,r,f) for b in VARIANTS for r in REACTION_VARIANTS for f in FTA_VARIANTS}
    if set(parents)!=expected:
        raise ValueError("C43_PARENT_36_ROUTE_INCOMPLETE")
    reranked={}
    for stream in bos.routes:
        b=stream.hypothesis_id
        for i,event in enumerate(stream.events):
            original_by_fta={f:parents[(b,REACTION_VARIANTS[0],f)].observations[i]
                            for f in FTA_VARIANTS}
            calculated=rerank_event(event,rows,index,fractals,gaps,registry,original_by_fta)
            for f,record in calculated.items():
                reranked[(b,f,i)]=record
    routes=[]
    for stream in bos.routes:
        b=stream.hypothesis_id
        for reaction in REACTION_VARIANTS:
            for fta in FTA_VARIANTS:
                parent=parents[(b,reaction,fta)]
                if len(parent.observations)!=len(stream.events):
                    raise ValueError("C43_PARENT_REACTION_COUNT_DRIFT")
                contexts=[]
                for i,(e,ref) in enumerate(zip(stream.events,parent.observations)):
                    if (ref.original_bos_native3m_row_id!=e.break_original_native3m_row_id or
                        ref.original_raid_fractal_center_ms!=e.raid_fractal_center_ms or
                        ref.bos_bar_closed_known_ms!=e.break_bar_closed_known_ms or
                        ref.reaction_hypothesis_id!=reaction or
                        ref.fta_hypothesis_id!=fta):
                        raise ValueError("C43_UNTRUSTED_REACTION_PROJECTION")
                    raw_count,distinct_count,original,decisions=reranked[(b,fta,i)]
                    if (original is not None and
                        original.touch.classification!=ref.source_prior_touch_classification):
                        raise ValueError("C43_PARENT_TOUCH_DRIFT")
                    contexts.append(ReRankContext(e.symbol,b,reaction,fta,
                        e.break_original_native3m_row_id,e.raid_fractal_center_ms,
                        e.break_bar_start_ms,e.break_bar_closed_known_ms,
                        ref.source_reaction_confirmed,raw_count,distinct_count,
                        original,decisions))
                selected={p:sum(c.decisions[k].selected_candidate is not None for c in contexts)
                          for k,p in enumerate(ELIGIBILITY_POLICIES)}
                replacements={p:sum(c.decisions[k].substituted_after_original_gate_rejection
                                  for c in contexts)
                              for k,p in enumerate(ELIGIBILITY_POLICIES)}
                if not (selected[ELIGIBILITY_POLICIES[0]]>=
                        selected[ELIGIBILITY_POLICIES[1]]>=
                        selected[ELIGIBILITY_POLICIES[2]]):
                    raise ValueError("C43_ELIGIBILITY_NESTED_MONOTONICITY")
                routes.append(ReRankRoute(b,reaction,fta,len(contexts),
                    selected,replacements,tuple(contexts)))
    if len(routes)!=36:
        raise ValueError("C43_ALL_36_ROUTES_MISSING")
    return ReRankMatrix(source.symbol,as_of_ms,len(rows),
        ACADEMIC_CORE_ID,36,ELIGIBILITY_POLICIES,tuple(routes))
