"""C41 source-only chronological BOS x Reaction x potential-FTA join.

Four independent ADAPTED BOS streams, three post-raid ADAPTED reactions,
three ADAPTED prior-known 1H obstacle ranks, and C40 pre-BOS source touch
observations are joined only by original raid pivot + original3m break ID.
Everything is source geometry. No author goldens, entry/TP/SL, ticks,
fill assumptions, trades or orders. PAPER ONLY / NOT_TRADE_READY.
"""
from dataclasses import dataclass
from c21b_original_3m_raid_break_geometry import _source, THREE
from c36_adapted_pivot_hypotheses import VARIANTS
from c36_adapted_slot_registry import ACADEMIC_CORE_ID
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted
from c38_adapted_post_raid_reaction import scan_adapted_reactions, REACTION_VARIANTS
from c39_adapted_preknown_fta_source import scan_original_preknown_fta, FTA_VARIANTS
from c40_pre_bos_fta_touch_state import inspect_original_fta_prior_touch, STATES

@dataclass(frozen=True)
class C41SourceContext:
    symbol: str
    bos_hypothesis_id: str
    reaction_hypothesis_id: str
    fta_hypothesis_id: str
    original_raid_fractal_center_ms: int
    original_bos_native3m_row_id: str
    bos_bar_start_ms: int
    bos_bar_closed_known_ms: int
    source_reaction_confirmed: bool
    first_reaction_original_native3m_row_id: str | None
    first_reaction_closed_known_ms: int | None
    potential_1h_obstacle_kind: str | None
    potential_1h_obstacle_source_known_ms: int | None
    original_potential_1h_source_first_native3m_row_id: str | None
    source_prior_touch_classification: str
    first_prior_touch_original_native3m_row_id: str | None
    first_prior_full_sweep_or_traversal_ms: int | None
    author_bos_approved: bool = False
    author_reaction_approved: bool = False
    author_fta_approved: bool = False
    paper_signal_allowed: bool = False
    orders: tuple = ()
    trades: tuple = ()
    readiness: str = "NOT_TRADE_READY"

@dataclass(frozen=True)
class C41SourceRoute:
    bos: str
    reaction: str
    fta: str
    parent_bos_contexts: int
    source_confirmed_reactions: int
    with_preknown_obstacle: int
    with_no_prior_touch_observed: int
    observations: tuple[C41SourceContext, ...]
    orders: tuple = ()
    trades: tuple = ()
    readiness: str = "NOT_TRADE_READY"

@dataclass(frozen=True)
class C41SourceMatrix:
    symbol: str
    as_of_ms: int
    source_original3m_closed: int
    academic_core_id: str
    route_count: int
    routes: tuple[C41SourceRoute, ...]
    author_goldens: int = 0
    orders: tuple = ()
    trades: tuple = ()
    readiness: str = "NOT_TRADE_READY"

def _route_lookup(items, kind):
    if kind == "reaction":
        pairs = ((x.bos_hypothesis_id, x.reaction_hypothesis_id, x) for x in items)
    elif kind == "fta":
        pairs = ((x.bos_hypothesis_id, x.fta_hypothesis_id, x) for x in items)
    elif kind == "touch":
        pairs = ((x["bos"], x["fta"], x) for x in items)
    else:
        raise ValueError("C41_UNKNOWN_ROUTE_KIND")
    result = {}
    for bos, adapt, item in pairs:
        if (bos, adapt) in result:
            raise ValueError("C41_DUPLICATED_ROUTE_ID")
        result[(bos, adapt)] = item
    return result

def join_c41_source_records(bos, reaction, fta, touch, rows):
    """Testable fail-closed join of independently computed source snapshots."""
    if not rows or any(x.symbol != rows[0].symbol for x in rows):
        raise ValueError("C41_MIXED_OR_MISSING_NATIVE3M_SOURCE")
    if (bos.symbol != reaction.symbol or bos.symbol != fta.symbol or
        bos.symbol != touch["symbol"] or bos.symbol != rows[0].symbol):
        raise ValueError("C41_SOURCE_SYMBOL_DRIFT")
    if (bos.as_of_ms != reaction.as_of_ms or bos.as_of_ms != fta.as_of_ms or
        bos.as_of_ms != touch["as_of_ms"]):
        raise ValueError("C41_SOURCE_ASOF_DRIFT")
    if (bos.academic_core_sha256 != ACADEMIC_CORE_ID or
        reaction.academic_core_id != ACADEMIC_CORE_ID or
        fta.academic_core_id != ACADEMIC_CORE_ID):
        raise ValueError("C41_ACADEMIC_CORE_DRIFT")
    if (bos.orders or bos.trades or reaction.orders or reaction.trades or
        fta.orders or fta.trades or touch["orders"] or touch["trades"] or
        bos.author_bos_approved or reaction.author_bos_goldens or
        reaction.author_reaction_goldens or fta.author_fta_goldens or
        fta.author_approved_targets or touch["author_fta_freshness_goldens"]):
        raise ValueError("C41_FORGED_AUTHOR_OR_EXECUTION_READY")
    if (bos.readiness != "NOT_TRADE_READY" or reaction.readiness != "NOT_TRADE_READY" or
        fta.readiness != "NOT_TRADE_READY" or touch["readiness"] != "NOT_TRADE_READY"):
        raise ValueError("C41_FORGED_READY")
    if not (len(bos.routes)==len(VARIANTS)==4 and
            len(reaction.routes)==len(VARIANTS)*len(REACTION_VARIANTS)==12 and
            len(fta.routes)==len(VARIANTS)*len(FTA_VARIANTS)==12 and
            len(touch["routes"])==len(VARIANTS)*len(FTA_VARIANTS)==12):
        raise ValueError("C41_INCOMPLETE_PARENT_ROUTE_COUNT")
    if (len(rows) != bos.source_closed_original3m_bars or
        len(rows) != reaction.original_closed_3m_bars or
        len(rows) != fta.source_original_native3m_rows or
        len(rows) != touch["source_original3m_rows"]):
        raise ValueError("C41_ORIGINAL_NATIVE_SOURCE_LENGTH_DRIFT")

    rx = _route_lookup(reaction.routes, "reaction")
    ft = _route_lookup(fta.routes, "fta")
    tx = _route_lookup(touch["routes"], "touch")
    expected_rx={(b, r) for b in VARIANTS for r in REACTION_VARIANTS}
    expected_ft={(b, f) for b in VARIANTS for f in FTA_VARIANTS}
    if set(rx)!=expected_rx or set(ft)!=expected_ft or set(tx)!=expected_ft:
        raise ValueError("C41_MISSING_OR_UNKNOWN_ROUTE")
    if tuple(x.hypothesis_id for x in bos.routes)!=VARIANTS:
        raise ValueError("C41_BOS_VARIANT_ORDER_DRIFT")
    first=rows[0].start_ms
    routes=[]
    for br in bos.routes:
        b=br.hypothesis_id
        if br.orders or br.trades or br.readiness!="NOT_TRADE_READY":
            raise ValueError("C41_BOS_ORDER_PROMOTION")
        for r in REACTION_VARIANTS:
            rr=rx[(b,r)]
            for f in FTA_VARIANTS:
                fr=ft[(b,f)]
                tr=tx[(b,f)]
                obs=tr["observations"]
                if (len(rr.observations)!=len(br.events) or
                    len(fr.observations)!=len(br.events) or
                    len(obs)!=len(br.events) or
                    rr.total_bos_parent_contexts!=len(br.events) or
                    fr.research_BOS_raid_contexts!=len(br.events) or
                    tr["contexts"]!=len(br.events)):
                    raise ValueError("C41_PARENT_CONTEXT_COUNTS_DRIFT")
                contexts=[]
                for e,w,p,t in zip(br.events,rr.observations,fr.observations,obs):
                    if (e.symbol!=bos.symbol or
                        w.symbol!=e.symbol or p.symbol!=e.symbol or t.symbol!=e.symbol or
                        e.hypothesis_id!=b or w.bos_hypothesis_id!=b or
                        p.bos_hypothesis_id!=b or t.bos_hypothesis_id!=b or
                        w.reaction_hypothesis_id!=r or p.hypothesis_id!=f or
                        t.fta_hypothesis_id!=f or
                        w.raid_fractal_center_ms!=e.raid_fractal_center_ms or
                        p.raid_1h_pivot_center_ms!=e.raid_fractal_center_ms or
                        w.original_bos_break_row_id!=e.break_original_native3m_row_id or
                        p.original_bos_3m_break_row_id!=e.break_original_native3m_row_id or
                        t.original_bos_native3m_row_id!=e.break_original_native3m_row_id or
                        w.bos_break_bar_start_ms!=e.break_bar_start_ms or
                        p.research_break_3m_close_known_ms!=e.break_bar_closed_known_ms):
                        raise ValueError("C41_CROSS_MODULE_EVENT_OR_ID_MISMATCH")
                    idx,mod=divmod(e.break_bar_start_ms-first,THREE)
                    if (mod or idx<0 or idx>=len(rows) or
                        rows[idx].raw_id!=e.break_original_native3m_row_id or
                        rows[idx].known_ms!=e.break_bar_closed_known_ms or
                        e.break_bar_closed_known_ms>bos.as_of_ms or
                        e.break_bar_start_ms<e.raid_confirmed_ms):
                        raise ValueError("C41_BOS_SOURCE_TIME_OR_RAW_ID_MISMATCH")
                    if (w.author_reaction_verified or w.author_bos_verified or
                        w.paper_signal_allowed or w.orders or w.trades or
                        p.author_selected_FTA or p.paper_signal_allowed or
                        p.target_orders or p.orders or p.trades or
                        t.author_freshness_certified or t.author_target_certified or
                        t.order_approval or t.orders or t.trades or
                        t.classification not in STATES):
                        raise ValueError("C41_FORGED_CHILD_AUTHOR_OR_EXECUTION")
                    if w.condition_satisfied:
                        when=w.first_confirmed_reaction_bar_closed_ms
                        start=w.first_confirmed_reaction_bar_start_ms
                        if (when is None or start is None or
                            when!=start+THREE or when>e.break_bar_start_ms or
                            start<e.raid_confirmed_ms or
                            not w.first_confirmed_native3m_row_id):
                            raise ValueError("C41_REACTION_FUTURE_OR_SOURCE_ID")
                        k,remainder=divmod(start-first,THREE)
                        if (remainder or k<0 or k>=idx or
                            rows[k].raw_id!=w.first_confirmed_native3m_row_id or
                            rows[k].known_ms!=when):
                            raise ValueError("C41_REACTION_RAW3M_SHA_DRIFT")
                    elif (w.first_confirmed_reaction_bar_start_ms is not None or
                          w.first_confirmed_reaction_bar_closed_ms is not None or
                          w.first_confirmed_native3m_row_id is not None):
                        raise ValueError("C41_INVENTED_UNCONFIRMED_REACTION")
                    selected=p.selected_potential_obstacle
                    if selected is None:
                        if (t.source_potential_fta is not None or
                            t.original_candidate_source_known_ms is not None or
                            t.classification!="NO_PREKNOWN_FTA_CANDIDATE"):
                            raise ValueError("C41_MISSING_OBSTACLE_DISAGREEMENT")
                        source_kind=None
                        source_known=None
                        source_first=None
                    else:
                        source_kind=selected.kind
                        source_known=selected.source_known_ms
                        source_first=selected.source_first_native3m_row_id
                        if (source_known>e.break_bar_start_ms or
                            t.candidate_source_kind!=source_kind or
                            t.source_potential_fta!=selected.source_level or
                            t.original_candidate_source_known_ms!=source_known or
                            selected.author_priority_attested or
                            selected.mitigation_or_freshness_attested):
                            raise ValueError("C41_FUTURE_FTA_OR_SELECTED_SOURCE_DRIFT")
                        if t.first_touch_bar_ms is not None:
                            k,remainder=divmod(t.first_touch_bar_ms-first,THREE)
                            if (remainder or k<0 or k>=idx or
                                rows[k].raw_id!=t.first_touch_original3m_row_id or
                                rows[k].known_ms>e.break_bar_start_ms or
                                rows[k].known_ms<=source_known):
                                raise ValueError("C41_PRIOR_TOUCH_FUTURE_OR_RAW_ID")
                        elif t.first_touch_original3m_row_id is not None:
                            raise ValueError("C41_INVENTED_TOUCH_SOURCE_ID")
                        if t.first_full_sweep_or_traversal_ms is not None:
                            k,remainder=divmod(t.first_full_sweep_or_traversal_ms-first,THREE)
                            if (remainder or k<0 or k>=idx or
                                rows[k].known_ms>e.break_bar_start_ms or
                                rows[k].known_ms<=source_known or
                                t.first_touch_bar_ms is None):
                                raise ValueError("C41_FUTURE_FULL_TRAVERSAL")
                    contexts.append(C41SourceContext(
                        e.symbol,b,r,f,e.raid_fractal_center_ms,
                        e.break_original_native3m_row_id,e.break_bar_start_ms,
                        e.break_bar_closed_known_ms,w.condition_satisfied,
                        w.first_confirmed_native3m_row_id,
                        w.first_confirmed_reaction_bar_closed_ms,
                        source_kind,source_known,source_first,
                        t.classification,t.first_touch_original3m_row_id,
                        t.first_full_sweep_or_traversal_ms))
                routes.append(C41SourceRoute(b,r,f,len(br.events),
                    sum(x.source_reaction_confirmed for x in contexts),
                    sum(x.potential_1h_obstacle_kind is not None for x in contexts),
                    sum(x.source_prior_touch_classification=="NO_PRIOR_SOURCE_TOUCH"
                        for x in contexts),tuple(contexts)))
    if len(routes)!=36:
        raise ValueError("C41_36_ADAPTED_SOURCE_COMBINATIONS_REQUIRED")
    return C41SourceMatrix(bos.symbol,bos.as_of_ms,len(rows),
        ACADEMIC_CORE_ID,len(routes),tuple(routes))

def scan_original_c41_source_matrix(source, *, as_of_ms):
    rows=_source(source,as_of_ms)
    b=scan_original_3m_adapted(source,as_of_ms=as_of_ms)
    r=scan_adapted_reactions(source,as_of_ms=as_of_ms)
    f=scan_original_preknown_fta(source,as_of_ms=as_of_ms)
    t=inspect_original_fta_prior_touch(source,as_of_ms=as_of_ms)
    return join_c41_source_records(b,r,f,t,rows)
