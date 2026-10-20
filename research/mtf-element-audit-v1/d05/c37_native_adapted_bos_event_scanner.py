"""C37 independent ADAPTED source-native raid -> 3m closed-break scanner.

Unlike C36 retrospective comparison, this scans each original 3m candle
chronologically and selects each of four adapted swing levels BEFORE the
3m candle starts. Every candidate pivot is fully confirmed by its right
3m candle at that time. First potential closed cross is known ONLY at
the break candle close. It does NOT certify author BOS nor permit orders.

The LATEST variant is a regression oracle for frozen C21 research geometry;
the other three cannot borrow a C21-selected break timestamp.
PAPER ONLY / NOT_TRADE_READY.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21b_original_3m_raid_break_geometry import (
    _source,_hours,_swings,observe_native3m_raid_break,THREE,SEPT_START)
from c20b_hourly_fractal_source_observer import observe_fractals_and_first_breach
from c36_adapted_pivot_hypotheses import VARIANTS
from c36_adapted_slot_registry import ACADEMIC_CORE_ID,FROZEN_C33_SHA

@dataclass(frozen=True)
class AdaptedClosedBreak:
    hypothesis_id:str
    symbol:str
    raid_fractal_kind:str
    raid_fractal_center_ms:int
    raid_first_breach_ms:int
    raid_confirmed_ms:int
    raid_level:str
    raid_extreme:str
    side:str
    swing_center_ms:int
    swing_confirmed_ms:int
    swing_level:str
    swing_center_native3m_row_id:str
    break_bar_start_ms:int
    break_bar_closed_known_ms:int
    break_close:str
    break_original_native3m_row_id:str
    status:str="ADAPTED_RESEARCH_CLOSED_BREAK_NOT_AUTHOR_BOS"
    author_bos_approved:bool=False
    paper_trade_allowed:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class RouteScan:
    hypothesis_id:str
    events:tuple[AdaptedClosedBreak,...]
    no_trade_author_status:str="NEEDS_AUTHOR_BOS_GOLDENS"
    readiness:str="NOT_TRADE_READY"
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class RouteComparison:
    symbol:str
    as_of_ms:int
    source_closed_original3m_bars:int
    source_1h_closed_bars:int
    source_confirmed_wick_raids:int
    academic_core_sha256:str
    frozen_academic_source_git_blob:str
    routes:tuple[RouteScan,...]
    original_C21_research_event_count:int
    latest_replays_frozen_C21:bool
    author_bos_approved:int=0
    paper_signals:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _key(s):
    return (s.known_ms,s.center_ms,s.native3m_ids[1])

def _choose(current,candidate,variant,short):
    if current is None:return candidate
    if variant=="LATEST_CONFIRMED_V1":
        return candidate if _key(candidate)>_key(current) else current
    if variant=="EARLIEST_CONFIRMED_V1":
        return candidate if _key(candidate)<_key(current) else current
    if variant=="DEEP_RAID_SIDE_V1":
        cur=(current.level,-current.known_ms,-current.center_ms)
        nxt=(candidate.level,-candidate.known_ms,-candidate.center_ms)
        better=nxt<cur if short else nxt>cur
        return candidate if better else current
    if variant=="NEAREST_RAID_SIDE_V1":
        cur=(current.level,current.known_ms,current.center_ms) if short else (
            current.level,-current.known_ms,-current.center_ms)
        nxt=(candidate.level,candidate.known_ms,candidate.center_ms) if short else (
            candidate.level,-candidate.known_ms,-candidate.center_ms)
        better=nxt>cur if short else nxt<cur
        return candidate if better else current
    raise ValueError("C37_UNREGISTERED_VARIANT")

def _eligible(raid,s,short):
    return (s.kind==("LOW" if short else "HIGH") and
            s.center_ms>=raid.first_breach_ms and
            s.known_ms>=raid.first_breach_close_ms and
            (s.level<raid.fractal.level if short else
             s.level>raid.fractal.level))

def _scan_one(raid,rows,swings,variant):
    if variant not in VARIANTS:raise ValueError("C37_UNKNOWN_ROUTE")
    if raid.confirmed_at_ms is None:return None
    short=raid.fractal.kind=="BSL"
    eligible=tuple(s for s in swings if _eligible(raid,s,short))
    if not eligible:return None
    first=max(0,(raid.confirmed_at_ms-SEPT_START)//THREE)
    chosen=None
    pointer=0
    for index in range(first,len(rows)):
        bar=rows[index]
        # OHLC bar extremes only known at this candle CLOSE. Fail closed:
        # any violation of raided wick extreme invalidates breakout at same
        # bar, not an inferred intrabar event sequence.
        if bar.high>raid.extreme if short else bar.low<raid.extreme:
            break
        while pointer<len(eligible) and eligible[pointer].known_ms<=bar.start_ms:
            chosen=_choose(chosen,eligible[pointer],variant,short)
            pointer+=1
        if chosen is None:continue
        previous=rows[index-1].close
        crossed=(bar.close<chosen.level and previous>=chosen.level if short
                 else bar.close>chosen.level and previous<=chosen.level)
        if not crossed:continue
        return AdaptedClosedBreak(variant,bar.symbol,raid.fractal.kind,
            raid.fractal.center_ms,raid.first_breach_ms,
            raid.confirmed_at_ms,str(raid.fractal.level),
            str(raid.extreme),"SHORT" if short else "LONG",
            chosen.center_ms,chosen.known_ms,str(chosen.level),
            chosen.native3m_ids[1],bar.start_ms,bar.known_ms,
            str(bar.close),bar.raw_id)
    return None

def _c21_event_key(e):
    return (e.pivot_kind,e.pivot_center_ms,e.raid_start_ms,
        e.raid_confirmed_ms,e.side,e.swing.center_ms,
        str(e.swing.level),e.break_start_ms,e.break_known_ms,
        str(e.break_close),e.source_original_3m_row_id)

def _adapted_event_key(e):
    return (e.raid_fractal_kind,e.raid_fractal_center_ms,
        e.raid_first_breach_ms,e.raid_confirmed_ms,e.side,
        e.swing_center_ms,e.swing_level,e.break_bar_start_ms,
        e.break_bar_closed_known_ms,e.break_close,
        e.break_original_native3m_row_id)

def scan_original_3m_adapted(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    hours=_hours(rows)
    _,raids=observe_fractals_and_first_breach(hours)
    swings=_swings(rows)
    events={v:[] for v in VARIANTS}
    for raid in raids:
        if raid.confirmed_at_ms is None:continue
        for variant in VARIANTS:
            e=_scan_one(raid,rows,swings,variant)
            if e is not None:events[variant].append(e)
    routes=tuple(RouteScan(v,tuple(events[v])) for v in VARIANTS)
    frozen=observe_native3m_raid_break(source,as_of_ms=as_of_ms)
    original=tuple(_c21_event_key(e) for e in frozen.potential_breaks)
    adapted=tuple(_adapted_event_key(e) for e in routes[0].events)
    # Require literal event order too: no silent missing or extra
    # C21 source-parent event allowed.
    if adapted!=original:
        raise ValueError("C37_LATEST_ROUTE_DOES_NOT_EXACTLY_REPRODUCE_C21")
    if any(e.paper_trade_allowed or e.orders or e.trades or e.author_bos_approved
           or e.break_bar_closed_known_ms>as_of_ms or
           e.swing_confirmed_ms>e.break_bar_start_ms
           for route in routes for e in route.events):
        raise ValueError("C37_FUTURE_OR_ORDER_FORGERY")
    return RouteComparison(source.symbol,as_of_ms,len(rows),len(hours),
        sum(raid.confirmed_at_ms is not None for raid in raids),
        ACADEMIC_CORE_ID,FROZEN_C33_SHA,routes,len(original),True)
