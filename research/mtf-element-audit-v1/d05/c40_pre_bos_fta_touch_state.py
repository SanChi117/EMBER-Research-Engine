"""C40: Source-native PRIOR contact state of C39 potential 1H obstacles.

A previously known fractal may already have been swept; a three-candle IMB
may already have been touched or fully traversed. Discover this from original
closed native 3m OHLC ONLY BETWEEN source obstacle fully-known and the BOS
break bar START. No tick order, fills, or instructor FTA freshness asserted.
All selected candidate source IDs are independently matched against the
original hour-derived fractal/Gap tuples, never caller-provided "ready" data.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21b_original_3m_raid_break_geometry import _source,_hours,THREE
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted,AdaptedClosedBreak
from c39_adapted_preknown_fta_source import (
    scan_original_preknown_fta,confirmed_1h_fractal_obstacles,
    PotentialObstacle)
from c28_source_fta_inventory import classic_1h_imb

STATES=("NO_PRIOR_SOURCE_TOUCH","PRIOR_BOUNDARY_TOUCH","PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL",
        "NO_PREKNOWN_FTA_CANDIDATE")

@dataclass(frozen=True)
class TouchAudit:
    symbol:str
    bos_hypothesis_id:str
    fta_hypothesis_id:str
    original_bos_native3m_row_id:str
    candidate_source_kind:str|None
    source_potential_fta:str|None
    original_candidate_source_known_ms:int|None
    first_touch_bar_ms:int|None
    first_touch_original3m_row_id:str|None
    first_full_sweep_or_traversal_ms:int|None
    classification:str
    author_freshness_certified:bool=False
    author_target_certified:bool=False
    order_approval:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def classify_pre_bos_obstacle_touch(e,selected,rows,fractals,gaps,fta_hypothesis):
    if not isinstance(e,AdaptedClosedBreak) or e.author_bos_approved or e.paper_trade_allowed or e.orders or e.trades:
        raise ValueError("C40_FORGED_BOS_OR_TRADE")
    if selected is None:
        return TouchAudit(e.symbol,e.hypothesis_id,fta_hypothesis,
           e.break_original_native3m_row_id,None,None,None,None,None,None,
           "NO_PREKNOWN_FTA_CANDIDATE")
    if not isinstance(selected,PotentialObstacle) or selected.author_priority_attested or selected.mitigation_or_freshness_attested:
        raise ValueError("C40_FORGED_AUTHOR_FTA_OR_SOURCE")
    if selected.source_known_ms>e.break_bar_start_ms:
        raise ValueError("C40_FUTURE_1H_OBSTACLE")
    try:
        level=Decimal(selected.source_level)
    except (ArithmeticError,ValueError,TypeError) as exc:
        raise ValueError("C40_INVALID_SOURCE_OBSTACLE_LEVEL") from exc
    if not level.is_finite() or level<=0:
        raise ValueError("C40_INVALID_SOURCE_OBSTACLE_LEVEL")
    # independently prove candidate is truly one of the original 1H source
    # elements, not an externally supplied price or SHA ref.
    gap_bounds=None
    if selected.kind in ("BSL_1H_FRACTAL","SSL_1H_FRACTAL"):
        matches=[f for f in fractals if f[0]==selected.kind and
             f[1]==level and f[2]==selected.source_known_ms and
             f[3]==selected.source_first_native3m_row_id and
             f[4]==selected.source_last_native3m_row_id]
        if len(matches)!=1:raise ValueError("C40_UNMATCHED_ORIGINAL_1H_FRACTAL")
        if (selected.kind=="BSL_1H_FRACTAL" and e.side!="LONG" or
            selected.kind=="SSL_1H_FRACTAL" and e.side!="SHORT"):
            raise ValueError("C40_FRACTAL_OPPOSITE_TRADE_SIDE")
    elif selected.kind in ("BULL_CLASSIC_IMB","BEAR_CLASSIC_IMB"):
        matches=[g for g in gaps if g.kind==selected.kind and
            g.known_ms==selected.source_known_ms and
            g.original_1h_row_ids[0]==selected.source_first_native3m_row_id and
            g.original_1h_row_ids[2]==selected.source_last_native3m_row_id and
            level==(g.bottom if e.side=="LONG" else g.top)]
        if len(matches)!=1:raise ValueError("C40_UNMATCHED_ORIGINAL_CLASSIC_IMB")
        gap_bounds=(matches[0].bottom,matches[0].top)
    else:
        raise ValueError("C40_UNSUPPORTED_FTA_FAMILY")
    if not rows or rows[0].symbol!=e.symbol:
        raise ValueError("C40_ORIGINAL_SYMBOL_MISMATCH")
    if (e.break_bar_start_ms-rows[0].start_ms)%THREE:
        raise ValueError("C40_FUTURE_OR_NON_NATIVE_BAR_GRID")
    cut=(e.break_bar_start_ms-rows[0].start_ms)//THREE
    if cut>=len(rows) or cut<0 or rows[cut].raw_id!=e.break_original_native3m_row_id:
        raise ValueError("C40_ORIGINAL_BREAK_ROW_SHA_MISMATCH")
    first=None
    firstid=None
    crossed=None
    for b in rows[:cut]:
        if b.known_ms<=selected.source_known_ms:continue
        if b.known_ms>e.break_bar_start_ms:
            raise ValueError("C40_FUTURE_BAR_IN_PRIOR_TOUCH_HISTORY")
        if gap_bounds is not None:
            low,high=gap_bounds
            touched=b.low<=high and b.high>=low
            full=b.low<=low and b.high>=high
        elif e.side=="LONG":
            touched=b.high>=level
            full=b.high>level
        else:
            touched=b.low<=level
            full=b.low<level
        if touched and first is None:
            first=b.start_ms
            firstid=b.raw_id
        if full and crossed is None:
            crossed=b.start_ms
    state=("PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL" if crossed is not None else
           "PRIOR_BOUNDARY_TOUCH" if first is not None else
           "NO_PRIOR_SOURCE_TOUCH")
    return TouchAudit(e.symbol,e.hypothesis_id,fta_hypothesis,
        e.break_original_native3m_row_id,selected.kind,selected.source_level,
        selected.source_known_ms,first,firstid,crossed,state)

def inspect_original_fta_prior_touch(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    bos=scan_original_3m_adapted(source,as_of_ms=as_of_ms)
    fta=scan_original_preknown_fta(source,as_of_ms=as_of_ms)
    hours=_hours(rows)
    fractals=confirmed_1h_fractal_obstacles(hours)
    gaps=classic_1h_imb(hours)
    lookup={r.hypothesis_id:r.events for r in bos.routes}
    result=[]
    for route in fta.routes:
        expected=lookup[route.bos_hypothesis_id]
        if len(expected)!=len(route.observations):
            raise ValueError("C40_BOS_FTA_SOURCE_ROUTE_DRIFT")
        observations=[]
        for e,r in zip(expected,route.observations):
            if (r.original_bos_3m_break_row_id!=e.break_original_native3m_row_id
                or r.raid_1h_pivot_center_ms!=e.raid_fractal_center_ms
                or r.hypothesis_id!=route.fta_hypothesis_id):
                raise ValueError("C40_CROSS_MODULE_EVENT_MISMATCH")
            observations.append(classify_pre_bos_obstacle_touch(e,
               r.selected_potential_obstacle,rows,fractals,gaps,route.fta_hypothesis_id))
        result.append({"bos":route.bos_hypothesis_id,"fta":route.fta_hypothesis_id,
            "contexts":len(observations),
            "states":{state:sum(o.classification==state for o in observations)
                for state in STATES},
            "observations":tuple(observations)})
    if len(result)!=12:
        raise ValueError("C40_4_BOS_3_FTA_ROUTES_MISSING")
    return {"schema":"EMBER_C40_PRIOR_SOURCE_FTA_TOUCH_STATES_V1",
        "symbol":source.symbol,"as_of_ms":as_of_ms,
        "source_original3m_rows":len(rows),"route_count":len(result),
        "routes":tuple(result),
        "author_fta_freshness_goldens":0,"orders":(),
        "trades":(),"readiness":"NOT_TRADE_READY"}
