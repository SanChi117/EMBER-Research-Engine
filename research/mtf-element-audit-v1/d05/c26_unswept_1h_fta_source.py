"""C26 forensic unswept 1H target and prior FTA candidates (PAPER ONLY).

Only known, closed original 3m rows are inspected before technical BOS BAR START.
No candle's intrabar tick order is inferred. A 'candidate' is NEVER an order,
author-approved target, author RR/FTA threshold, or author stop buffer.
C21B/C24/C25 and frozen source receipts remain unmodified.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21b_original_3m_raid_break_geometry import _source, _hours, observe_native3m_raid_break
from c20b_hourly_fractal_source_observer import observe_fractals_and_first_breach
from c25_session_freshness_target_source import inspect_c25

@dataclass(frozen=True)
class LevelHistory:
    state: str
    first_wick_cross_ms: int|None
    first_body_close_through_ms: int|None
    first_equality_ms: int|None
    first_wick_source_row_id: str|None

@dataclass(frozen=True)
class Obstacle:
    kind: str
    level: str
    center_ms: int
    known_ms: int
    history: LevelHistory

@dataclass(frozen=True)
class Case:
    symbol: str
    raid_ms: int
    break_start_ms: int
    break_original_row_id: str
    side: str
    research_entry_close: str
    research_raid_extreme: str
    unbuffered_stop_span: str
    nearest_historical_target: str|None
    nearest_target_center_ms: int|None
    nearest_target_known_ms: int|None
    nearest_target_history: LevelHistory|None
    alternative_intact_target: str|None
    alternative_intact_center_ms: int|None
    obstacles_before_nearest_target: tuple[Obstacle,...]
    target_fta_same_3m_bar_order_unknown: bool
    reasons: tuple[str,...]
    readiness: str="NOT_TRADE_READY"
    author_approved: bool=False

@dataclass(frozen=True)
class Review:
    symbol: str
    as_of_ms: int
    original_parent_edges: int
    research_single_cases: int
    nearest_target_already_crossed: int
    nearest_target_equality_unresolved: int
    nearest_target_intact: int
    nearest_target_not_preknown: int
    alternatives_intact_found: int
    with_preknown_intervening_1h_obstacle: int
    same_bar_tick_order_unresolved: int
    cases: tuple[Case,...]
    readiness: str="NOT_TRADE_READY"
    author_approved_trades: int=0

def _valid_pivot(p, break_start_ms):
    if p.kind not in ("BSL","SSL") or not isinstance(p.level,Decimal) or not p.level.is_finite():
        raise ValueError("C26_INVALID_1H_FRACTAL")
    if p.known_ms<=p.center_ms or p.known_ms>break_start_ms:
        raise ValueError("TARGET_NOT_PREKNOWN")
    if not p.source_rows:
        raise ValueError("C26_FRACTAL_WITHOUT_SOURCE_ROWS")

def level_history(p, rows, *, break_start_ms):
    """Historical, strict cross; equality is not a cross. Exclude BOS bar entirely."""
    _valid_pivot(p,break_start_ms)
    first_wick=first_close=first_equal=None
    first_id=None
    last=-1
    for b in rows:
        if b.start_ms<last or b.known_ms<=b.start_ms:
            raise ValueError("C26_UNORDERED_OR_UNCLOSED_ROW")
        last=b.start_ms
        if b.start_ms<p.known_ms:
            continue
        if b.known_ms>break_start_ms:
            break
        if not all(isinstance(x,Decimal) and x.is_finite() for x in (b.high,b.low,b.close)):
            raise ValueError("C26_BAD_ORIGINAL_PRICE")
        if p.kind=="BSL":
            wick=b.high>p.level
            close=b.close>p.level
            equal=b.high==p.level or b.close==p.level
        else:
            wick=b.low<p.level
            close=b.close<p.level
            equal=b.low==p.level or b.close==p.level
        if wick and first_wick is None:
            first_wick=b.start_ms
            first_id=b.raw_id
        if close and first_close is None:
            first_close=b.start_ms
        if equal and first_equal is None:
            first_equal=b.start_ms
    if first_close is not None:
        state="BODY_CLOSE_THROUGH"
    elif first_wick is not None:
        state="WICK_CROSS"
    elif first_equal is not None:
        state="EQUALITY_TOUCH_UNRESOLVED"
    else:
        state="NO_CROSS_OBSERVED"
    return LevelHistory(state,first_wick,first_close,first_equal,first_id)

def _opposing_candidates(pivots, side, entry, break_start_ms):
    if side not in ("LONG","SHORT") or not isinstance(entry,Decimal) or not entry.is_finite():
        raise ValueError("C26_INVALID_SIDE_OR_ENTRY")
    kind="SSL" if side=="SHORT" else "BSL"
    return sorted((p for p in pivots if p.kind==kind and p.known_ms<=break_start_ms
                   and (p.level<entry if side=="SHORT" else p.level>entry)),
                  key=lambda p:(abs(p.level-entry),p.center_ms))

def _same_bar_unknown(side,bar,stop,target):
    """True only for inclusive price-range reach; never infer sequence or fill."""
    if target is None:return False
    if side=="SHORT":
        return bar.high>=stop and bar.low<=target
    return bar.low<=stop and bar.high>=target

def inspect_c26(source,*,as_of_ms):
    """Source-gated C25 cases; one and only one C21B event per C24 singleton."""
    rows=_source(source,as_of_ms)
    prior=inspect_c25(source,as_of_ms=as_of_ms)
    events=observe_native3m_raid_break(source,as_of_ms=as_of_ms)
    pivots,_=observe_fractals_and_first_breach(_hours(rows))
    keyed={(e.pivot_center_ms,e.raid_start_ms,e.break_start_ms):e
           for e in events.potential_breaks}
    if len(keyed)!=len(events.potential_breaks):
        raise ValueError("AMBIGUOUS_PARENT")
    produced=[]
    for x in prior.cases:
        e=keyed.get((x.raid_fractal_ms,x.raid_ms,x.break_ms))
        if (e is None or e.source_original_3m_row_id!=x.original_source_row_id
            or e.side!=x.side or str(e.break_close)!=x.research_entry_close
            or str(e.raid_extreme)!=x.raid_extreme):
            raise ValueError("C26_C25_CAUSAL_SOURCE_JOIN_DRIFT")
        if e.break_start_ms>=as_of_ms or e.break_known_ms>as_of_ms:
            raise ValueError("C26_UNCLOSED_BREAK_BAR")
        i=(e.break_start_ms-rows[0].start_ms)//180000
        if i<0 or i>=len(rows) or rows[i].raw_id!=x.original_source_row_id:
            raise ValueError("C26_ORIGINAL_ROW_ID_DRIFT")
        entry=e.break_close
        potential=_opposing_candidates(pivots,e.side,entry,e.break_start_ms)
        near=potential[0] if potential else None
        if (str(near.level) if near else None)!=x.nearest_preknown_opposing_1h_fractal_price:
            raise ValueError("C26_FROZEN_C25_TARGET_DRIFT")
        # Memo by immutable (kind,center,level), not by approximated float.
        memo={}
        def hist(p):
            key=(p.kind,p.center_ms,p.level)
            if key not in memo:
                memo[key]=level_history(p,rows,break_start_ms=e.break_start_ms)
            return memo[key]
        first=hist(near) if near else None
        alt=next((p for p in potential[1:] if hist(p).state=="NO_CROSS_OBSERVED"),None)
        obstacles=[]
        if near:
            for p in pivots:
                if p.known_ms>e.break_start_ms or p==near:
                    continue
                if (entry>p.level>near.level if e.side=="SHORT"
                    else entry<p.level<near.level):
                    obstacles.append(Obstacle(p.kind,str(p.level),p.center_ms,
                                              p.known_ms,hist(p)))
        obstacles.sort(key=lambda o:(abs(Decimal(o.level)-entry),o.center_ms))
        reasons=[]
        if near is None:
            reasons.append("TARGET_NOT_PREKNOWN")
        elif first.state in ("WICK_CROSS","BODY_CLOSE_THROUGH"):
            reasons.append("REJECT_ALREADY_SWEPT_TARGET")
        elif first.state=="EQUALITY_TOUCH_UNRESOLVED":
            reasons.append("TARGET_EQUALITY_SEMANTICS_UNKNOWN")
        if obstacles:
            reasons.append("UNKNOWN_AUTHOR_FTA")
        else:
            reasons.append("FTA_THRESHOLD_AUTHOR_UNKNOWN")
        reasons.extend(("UNKNOWN_AUTHOR_SL_BUFFER","UNKNOWN_AUTHOR_SESSION_DST",
                        "UNKNOWN_AUTHOR_BOS_GOLDENS","NOT_TRADE_READY"))
        stop=e.raid_extreme
        distance=(stop-entry if e.side=="SHORT" else entry-stop)
        if distance<=0 or str(distance)!=x.minimum_unbuffered_stop_distance:
            raise ValueError("C26_C25_STOP_GEOMETRY_DRIFT")
        ambiguous=_same_bar_unknown(e.side,rows[i],stop,near.level if near else None)
        if ambiguous:
            reasons.append("SAME_BAR_TICK_ORDER_UNKNOWN")
        produced.append(Case(source.symbol,e.raid_start_ms,e.break_start_ms,
            x.original_source_row_id,e.side,str(entry),str(stop),str(distance),
            str(near.level) if near else None,near.center_ms if near else None,
            near.known_ms if near else None,first,str(alt.level) if alt else None,
            alt.center_ms if alt else None,tuple(obstacles),ambiguous,tuple(reasons)))
    result=tuple(produced)
    if len(result)!=prior.research_single_parent_cases:
        raise ValueError("C26_C24_CASE_COUNT_DRIFT")
    return Review(source.symbol,as_of_ms,prior.original_parent_edges,len(result),
        sum(x.nearest_target_history is not None and x.nearest_target_history.state
            in ("WICK_CROSS","BODY_CLOSE_THROUGH") for x in result),
        sum(x.nearest_target_history is not None and x.nearest_target_history.state
            =="EQUALITY_TOUCH_UNRESOLVED" for x in result),
        sum(x.nearest_target_history is not None and x.nearest_target_history.state
            =="NO_CROSS_OBSERVED" for x in result),
        sum(x.nearest_target_history is None for x in result),
        sum(x.alternative_intact_target is not None for x in result),
        sum(bool(x.obstacles_before_nearest_target) for x in result),
        sum(x.target_fta_same_3m_bar_order_unknown for x in result),result)
