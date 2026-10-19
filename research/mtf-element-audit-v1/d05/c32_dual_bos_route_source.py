"""C32 two separate BOS route observers over ORIGINAL closed Binance 3m source.

Author academy says market entry when BOS *price crosses*, OR wait for BOS
candle close and use limit. Original 3m OHLC has no tick-time, bid/ask,
author-selected 3m swing, limit price or fill. This module never upgrades
either route to an order, an execution, an author BOS, or a trade.

All price crossing facts are observed only AFTER the corresponding full 3m
source bar closes; that observation does not tell when within the bar a level
was touched, nor whether stop and entry had a safe ordering. PAPER ONLY.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21b_original_3m_raid_break_geometry import (
    ThreeBreak,observe_native3m_raid_break,_source,THREE)
from c31_bos_entry_semantic_disagreement import inspect_c31_bos,audit_single_bos

@dataclass(frozen=True)
class MarketCrossObservation:
    first_source_wick_reach_bar_ms:int
    first_source_wick_reach_known_ms:int
    first_source_wick_reach_3m_row_id:str
    first_wick_reach_was_before_research_close_bar:bool
    first_source_bar_open_side:str
    first_source_bar_closed_beyond_selected_pivot:bool
    first_source_bar_also_exceeded_raid_extreme:bool
    first_wick_reach_was_already_touched_at_bar_open:bool
    original3m_candle_extreme:str
    status:str="SOURCE_OHLC_REACH_ONLY_MARKET_TICK_CROSS_NOT_PROVEN"
    author_selected_pivot:str="NOT_ATTESTED"
    actual_tick_cross_ms:None=None
    simulated_fill_price:None=None
    market_order_allowed:bool=False
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class CloseThenLimitObservation:
    selected_close_bar_ms:int
    selected_close_known_ms:int
    selected_close_3m_row_id:str
    selected_close_price:str
    original_bos_swing_level:str
    source_close_beyond_pivot:bool
    earliest_possible_order_after_ms:int
    status:str="CLOSE_SOURCE_CONFIRMED_LIMIT_PRICE_AND_RETEST_UNKNOWN"
    author_limit_price:None=None
    author_limit_expiry:None=None
    inferred_retest_fill:None=None
    limit_order_allowed:bool=False
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class DualRouteObservation:
    symbol:str
    research_pivot_ms:int
    research_raid_start_ms:int
    research_bos_start_ms:int
    source_selected_swing_center_ms:int
    source_selected_swing_known_ms:int
    side:str
    source_pivot_level:str
    source_raid_extreme:str
    market_cross:MarketCrossObservation
    close_then_limit:CloseThenLimitObservation
    original_closed3m_rows_used:int
    chosen_route:str="NONE_UNTIL_AUTHOR_SOURCE_ATTESTED"
    author_route_approved:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class DualRouteAudit:
    symbol:str
    as_of_ms:int
    original3m_source_rows:int
    strict_c21_parent_edges:int
    c31_research_single_cases:int
    prior_wick_reach_before_3m_bos_close:int
    prior_wick_reach_before_3m_bos_bar:int
    cross_bar_also_exceeded_raid_extreme:int
    first_cross_bar_did_not_close_beyond_pivot:int
    closed_3m_bos_observed:int
    author_market_cross_approved:int
    author_limit_retest_approved:int
    orders_created:int
    trades_created:int
    cases:tuple[DualRouteObservation,...]
    readiness:str="NOT_TRADE_READY"

def _side_beyond(side,price,level):
    return price<level if side=="SHORT" else price>level

def _first_reach(event, rows):
    if not isinstance(event,ThreeBreak) or not isinstance(rows,tuple):
        raise ValueError("C32_UNTRUSTED_BOS_OR_ORIGINAL_ROWS")
    # C31 enforces source original-bar ID, strict 3m swing, raid, and close
    # invariants. Never accept caller-selected "author approved" switches.
    audited=audit_single_bos(event,rows)
    if audited.readiness!="NOT_TRADE_READY":
        raise ValueError("C32_FORGED_C31_AUTHOR_APPROVAL")
    begin=max(event.raid_confirmed_ms,event.swing.known_ms)
    if begin>event.break_start_ms or event.break_known_ms!=event.break_start_ms+THREE:
        raise ValueError("C32_FUTURE_BOS_SWING_OR_RAID")
    first=None
    last=None
    for x in rows:
        if x.start_ms<begin:continue
        if x.start_ms>event.break_start_ms:break
        if x.known_ms>event.break_known_ms:
            raise ValueError("C32_FUTURE_3M_SOURCE")
        if last is not None and x.start_ms!=last+THREE:
            raise ValueError("C32_MISSING_3M_SOURCE_BARS")
        last=x.start_ms
        wick=x.low if event.side=="SHORT" else x.high
        if _side_beyond(event.side,wick,event.swing.level):
            first=x
            break
    if first is None:
        raise ValueError("C32_C21_CLOSE_BOS_WITHOUT_ANY_3M_WICK_REACH")
    # A distinct structural price event and a legitimate market fill are
    # NOT equivalent; if open is already through pivot, one cannot claim
    # a new crossing happened within the closed bar.
    opening_beyond=_side_beyond(event.side,first.open,event.swing.level)
    return audited,first,opening_beyond

def study_bos_routes(event, rows):
    a,b,opened_beyond=_first_reach(event,rows)
    if b.symbol!=rows[0].symbol or b.raw_id!=(
        next(x.raw_id for x in rows if x.start_ms==b.start_ms)):
        raise ValueError("C32_ORIGINAL_SOURCE_WICK_ROW_ID_DRIFT")
    exceeded=(b.high>event.raid_extreme if event.side=="SHORT"
              else b.low<event.raid_extreme)
    m=MarketCrossObservation(
        b.start_ms,b.known_ms,b.raw_id,b.start_ms<event.break_start_ms,
        "OPEN_ALREADY_BEYOND_SELECTED_PIVOT" if opened_beyond
            else "OPEN_NOT_BEYOND_SELECTED_PIVOT",
        _side_beyond(event.side,b.close,event.swing.level),exceeded,
        opened_beyond,str(b.low if event.side=="SHORT" else b.high))
    c=CloseThenLimitObservation(
        event.break_start_ms,event.break_known_ms,
        event.source_original_3m_row_id,str(event.break_close),
        str(event.swing.level),True,event.break_known_ms)
    return DualRouteObservation(
        rows[0].symbol,event.pivot_center_ms,event.raid_start_ms,
        event.break_start_ms,event.swing.center_ms,event.swing.known_ms,
        event.side,str(event.swing.level),str(event.raid_extreme),
        m,c,1+sum(x.start_ms<event.break_start_ms for x in rows
            if x.start_ms>=max(event.raid_confirmed_ms,event.swing.known_ms)))

def inspect_c32(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    prior=inspect_c31_bos(source,as_of_ms=as_of_ms)
    c21=observe_native3m_raid_break(source,as_of_ms=as_of_ms)
    if len(c21.potential_breaks)!=prior.strict_closed_3m_research_edges:
        raise ValueError("C32_C31_SOURCE_PARENT_COUNT_DRIFT")
    # C21 original selected BOS bar requires exact closed source row;
    # inspect_c32 must never accept a source suffix after as_of_ms.
    cases=tuple(study_bos_routes(e,rows) for e in c21.potential_breaks)
    before=sum(x.market_cross.first_wick_reach_was_before_research_close_bar
               for x in cases)
    if before!=prior.edges_with_prior_strict_wick_cross:
        raise ValueError("C32_C31_PREVIOUS_WICK_LINK_DRIFT")
    if any(x.orders or x.trades or x.author_route_approved or
           x.market_cross.market_order_allowed or
           x.close_then_limit.limit_order_allowed for x in cases):
        raise ValueError("C32_UNAUTHORIZED_ORDER_OR_AUTHOR_APPROVAL")
    return DualRouteAudit(
        source.symbol,as_of_ms,len(rows),len(cases),
        prior.research_single_case_count,before,before,
        sum(x.market_cross.first_source_bar_also_exceeded_raid_extreme for x in cases),
        sum(not x.market_cross.first_source_bar_closed_beyond_selected_pivot
            for x in cases),len(cases),
        0,0,0,0,cases)
