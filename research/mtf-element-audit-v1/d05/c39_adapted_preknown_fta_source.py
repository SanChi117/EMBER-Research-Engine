"""C39 potential FIRST TROUBLE AREA source families; ADAPTED geometry only.

Uses frozen academic concepts 1H BSL/SSL fractals and classic 3-candle IMB
from native original 3m ZIP, and independently timed C37 BOS bar CLOSE
research price. Candidate source must be fully known BEFORE BOS bar START.

NOT the instructor's selected first FTA; ignores author priority, mitigation,
touched fractal/zone freshness, sessions, RB, SNR and EQ. Also cannot infer
real entry/order fill, fees or structural RR from bar-close research price.
PAPER ONLY / NOT_TRADE_READY.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21b_original_3m_raid_break_geometry import _source,_hours,THREE
from c37_native_adapted_bos_event_scanner import (
    scan_original_3m_adapted,AdaptedClosedBreak)
from c20b_hourly_fractal_source_observer import HourSource
from c28_source_fta_inventory import classic_1h_imb
from c36_adapted_pivot_hypotheses import VARIANTS
from c36_adapted_slot_registry import ACADEMIC_CORE_ID

FTA_VARIANTS=(
  "CLOSEST_PRIOR_1H_OBSTACLE_V1",
  "FRACTAL_FAMILY_PRIORITY_V1",
  "CLASSIC_IMB_FAMILY_PRIORITY_V1",
)
HOUR=3600000

@dataclass(frozen=True)
class PotentialObstacle:
    kind:str
    source_known_ms:int
    source_level:str
    source_first_native3m_row_id:str
    source_last_native3m_row_id:str
    distance_from_retrospective_break_close:str
    author_priority_attested:bool=False
    mitigation_or_freshness_attested:bool=False

@dataclass(frozen=True)
class PotentialFTAReview:
    hypothesis_id:str
    bos_hypothesis_id:str
    symbol:str
    raid_1h_pivot_center_ms:int
    original_bos_3m_break_row_id:str
    research_break_3m_close_known_ms:int
    retrospective_break_close:str
    source_preknown_candidate_count:int
    selected_potential_obstacle:PotentialObstacle|None
    classification:str="ADAPTED_RESEARCH_SOURCE_POTENTIAL_FTA_NOT_AUTHOR_SELECTED"
    author_selected_FTA:bool=False
    paper_signal_allowed:bool=False
    target_orders:tuple=()
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class PotentialFTARoute:
    bos_hypothesis_id:str
    fta_hypothesis_id:str
    research_BOS_raid_contexts:int
    with_potential_source_obstacle:int
    without_source_obstacle:int
    observations:tuple[PotentialFTAReview,...]
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class PotentialFTAMatrix:
    symbol:str
    as_of_ms:int
    source_original_native3m_rows:int
    academic_core_id:str
    bos_hypotheses:tuple[str,...]
    fta_hypotheses:tuple[str,...]
    routes:tuple[PotentialFTARoute,...]
    author_fta_goldens:int=0
    author_approved_targets:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def confirmed_1h_fractal_obstacles(hours):
    """Original hourly OHLC 1+1 pivots, known only at next hour close."""
    if not isinstance(hours,tuple):raise ValueError("C39_UNTRUSTED_HOURLY_SOURCE")
    result=[]
    for i in range(1,len(hours)-1):
        a,b,c=hours[i-1:i+2]
        for h in (a,b,c):
            if not isinstance(h,HourSource) or len(h.native_rows)!=20:
                raise ValueError("C39_MISSING_NATIVE_1H_SOURCE")
        if b.high>a.high and b.high>c.high:
            result.append(("BSL_1H_FRACTAL",b.high,c.close_ms,
                           a.native_rows[0],c.native_rows[-1]))
        if b.low<a.low and b.low<c.low:
            result.append(("SSL_1H_FRACTAL",b.low,c.close_ms,
                           a.native_rows[0],c.native_rows[-1]))
    return tuple(result)

def source_preknown_potential_obstacles(e,rows,fractals,gaps):
    if not isinstance(e,AdaptedClosedBreak):
        raise ValueError("C39_UNTRUSTED_RESEARCH_BOS")
    if (e.hypothesis_id not in VARIANTS or
        e.status!="ADAPTED_RESEARCH_CLOSED_BREAK_NOT_AUTHOR_BOS" or
        e.author_bos_approved or e.paper_trade_allowed or e.orders or e.trades or
        e.side not in ("LONG","SHORT") or
        e.raid_fractal_kind!=("BSL" if e.side=="SHORT" else "SSL") or
        e.break_bar_closed_known_ms!=e.break_bar_start_ms+THREE):
        raise ValueError("C39_FORGED_BOS_READY_OR_INVALID_EVENT")
    if not rows or e.symbol!=rows[0].symbol:
        raise ValueError("C39_NATIVE_SOURCE_SYMBOL_MISMATCH")
    start=rows[0].start_ms
    idx=(e.break_bar_start_ms-start)//THREE
    if (e.break_bar_start_ms-start)%THREE or idx<0 or idx>=len(rows):
        raise ValueError("C39_BOS_BREAK_NOT_ON_ORIGINAL_3M_GRID")
    b=rows[idx]
    if (b.raw_id!=e.break_original_native3m_row_id or
        b.known_ms!=e.break_bar_closed_known_ms or
        str(b.close)!=e.break_close):
        raise ValueError("C39_RETROSPECTIVE_ENTRY_BAR_SHA_PRICE_DRIFT")
    try:price=Decimal(e.break_close)
    except (ValueError,ArithmeticError) as exc:
        raise ValueError("C39_INVALID_RETROSPECTIVE_PRICE") from exc
    if not price.is_finite() or price<=0:
        raise ValueError("C39_INVALID_RETROSPECTIVE_PRICE")
    candidates=[]
    for kind,level,known,first_id,last_id in fractals:
        if kind!=("BSL_1H_FRACTAL" if e.side=="LONG" else "SSL_1H_FRACTAL"):
            continue
        if (type(level) is not Decimal or not level.is_finite() or level<=0
            or type(known)!=int or known>e.break_bar_start_ms):
            if type(known)==int and known>e.break_bar_start_ms:continue
            raise ValueError("C39_INVALID_1H_SOURCE_FRACTAL")
        dist=level-price if e.side=="LONG" else price-level
        if dist>0:
            candidates.append(PotentialObstacle(kind,known,str(level),
                first_id,last_id,str(dist)))
    for gap in gaps:
        if gap.known_ms>e.break_bar_start_ms:continue
        if (gap.kind not in ("BULL_CLASSIC_IMB","BEAR_CLASSIC_IMB") or
            type(gap.bottom) is not Decimal or type(gap.top) is not Decimal or
            not gap.bottom.is_finite() or not gap.top.is_finite() or
            gap.bottom<=0 or gap.top<=gap.bottom):
            raise ValueError("C39_INVALID_PRIOR_CLASSIC_IMB")
        # Strictly ahead of retrospective close; gap containing entry is
        # not automatically an untouched first future obstacle.
        edge=gap.bottom if e.side=="LONG" else gap.top
        dist=edge-price if e.side=="LONG" else price-edge
        if dist>0:
            candidates.append(PotentialObstacle(gap.kind,gap.known_ms,str(edge),
               gap.original_1h_row_ids[0],gap.original_1h_row_ids[-1],str(dist)))
    # Stable tie-break by source time, kind and native row provenance. No
    # strength ranking, mitigation assumption or author FTA certification.
    candidates.sort(key=lambda x:(Decimal(x.distance_from_retrospective_break_close),
        x.source_known_ms,x.kind,x.source_first_native3m_row_id))
    if any(x.source_known_ms>e.break_bar_start_ms for x in candidates):
        raise ValueError("C39_FUTURE_FTA_OBSTACLE_LEAKAGE")
    return tuple(candidates)

def classify_potential_fta(e,rows,fractals,gaps,hypothesis):
    if hypothesis not in FTA_VARIANTS:
        raise ValueError("C39_UNKNOWN_ADAPTED_FTA")
    all_candidates=source_preknown_potential_obstacles(e,rows,fractals,gaps)
    family=("BSL_1H_FRACTAL","SSL_1H_FRACTAL")
    if hypothesis=="FRACTAL_FAMILY_PRIORITY_V1":
        prioritized=[p for p in all_candidates if p.kind in family]
        first=prioritized[0] if prioritized else (all_candidates[0] if all_candidates else None)
    elif hypothesis=="CLASSIC_IMB_FAMILY_PRIORITY_V1":
        prioritized=[p for p in all_candidates if p.kind in (
            "BULL_CLASSIC_IMB","BEAR_CLASSIC_IMB")]
        first=prioritized[0] if prioritized else (all_candidates[0] if all_candidates else None)
    else:first=all_candidates[0] if all_candidates else None
    return PotentialFTAReview(hypothesis,e.hypothesis_id,e.symbol,
        e.raid_fractal_center_ms,e.break_original_native3m_row_id,
        e.break_bar_closed_known_ms,e.break_close,len(all_candidates),first)

def scan_original_preknown_fta(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    bos=scan_original_3m_adapted(source,as_of_ms=as_of_ms)
    if bos.academic_core_sha256!=ACADEMIC_CORE_ID:
        raise ValueError("C39_ACADEMIC_CORE_SHA_DRIFT")
    hours=_hours(rows)
    fractals=confirmed_1h_fractal_obstacles(hours)
    gaps=classic_1h_imb(hours)
    routes=[]
    for r in bos.routes:
        for hypothesis in FTA_VARIANTS:
            observations=tuple(classify_potential_fta(e,rows,fractals,gaps,hypothesis)
                               for e in r.events)
            count=sum(o.selected_potential_obstacle is not None for o in observations)
            routes.append(PotentialFTARoute(r.hypothesis_id,hypothesis,
                len(r.events),count,len(r.events)-count,observations))
    if len(routes)!=len(VARIANTS)*len(FTA_VARIANTS):
        raise ValueError("C39_MISSING_BOS_FTA_MATRIX")
    return PotentialFTAMatrix(source.symbol,as_of_ms,len(rows),
         ACADEMIC_CORE_ID,VARIANTS,FTA_VARIANTS,tuple(routes))
