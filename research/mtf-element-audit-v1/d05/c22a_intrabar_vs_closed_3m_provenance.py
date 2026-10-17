"""C22A: forensic uncertainty of price-level crossing vs closed 3m BOS geometry.

Author's Entry by BOS allows crossing directly OR later confirmation.
Original OHLCV (even authentic) cannot timestamp intrabar price/tick order,
verify execution at threshold, or select correct academic structural pivot.
Never create orders or promote author BOS. All observations PAPER ONLY.
"""
from dataclasses import dataclass
from c21_native3m_source_bridge import THREE,SEPT_START
from c21b_original_3m_raid_break_geometry import _source,observe_native3m_raid_break

@dataclass(frozen=True)
class CrossingUncertainty:
    symbol:str
    side:str
    parent_fractal_ms:int
    raid_start_ms:int
    raid_confirmed_ms:int
    structural_swing_origin_ms:int
    structural_swing_known_ms:int
    structural_swing_native3m_ids:tuple[str,str,str]
    structural_swing_level:str
    close_break_native3m_id:str
    close_break_start_ms:int
    close_break_known_ms:int
    first_reachable_cross_native3m_id:str
    first_reachable_cross_start_ms:int
    first_reachable_cross_known_ms:int
    first_reachable_cross_close_confirmed:bool
    earlier_pre_close_reach:bool
    earlier_reach_bars:int
    break_bar_open_beyond_level:bool
    label:str="RESEARCH_NATIVE3M_OHLC_BOUNDS_NOT_AUTHOR_BOS"
    tick_timestamp:str="UNOBSERVABLE_WITH_3M_OHLC"
    market_fill:str="UNPROVEN_WITH_OHLC"

@dataclass(frozen=True)
class CrossingAudit:
    symbol:str
    as_of_ms:int
    observations:tuple[CrossingUncertainty,...]
    candidate_parent_edges:int
    first_reach_prior_to_closed_break:int
    earlier_reach_without_close:int
    earlier_reach_already_closed_beyond_level:int
    break_bar_open_already_beyond_level:int
    candle_time_unknown_order:int
    author_approved_bos:int=0
    author_approved_trades:int=0
    readiness:str="NOT_TRADE_READY"
    author_structural_pivot_status:str="AUTHOR_TIMESTAMPED_BOS_GOLDEN_UNAVAILABLE"

def examine_crossing_bounds(line,*,as_of_ms:int)->CrossingAudit:
    rows=_source(line,as_of_ms)
    baselines=observe_native3m_raid_break(line,as_of_ms=as_of_ms)
    result=[]
    for e in baselines.potential_breaks:
        start=max(e.raid_confirmed_ms,e.swing.known_ms)
        if not (start<=e.break_start_ms<e.break_known_ms<=as_of_ms):
            raise ValueError("PREMATURE_C21B_BOS_OR_SWING_LOOKAHEAD")
        if e.source_original_3m_row_id!=rows[(e.break_start_ms-SEPT_START)//THREE].raw_id:
            raise ValueError("ALTERED_C21B_BREAK_ROW_SOURCE")
        short=e.side=="SHORT"
        first=None
        prior_count=0
        for i in range((start-SEPT_START)//THREE,
                       (e.break_start_ms-SEPT_START)//THREE+1):
            bar=rows[i]
            reaches=(bar.low<e.swing.level if short else bar.high>e.swing.level)
            if reaches and first is None:
                first=bar
            if reaches and bar.start_ms<e.break_start_ms:
                prior_count+=1
        if first is None:raise ValueError("CLOSED_BREAK_WITHOUT_OHLC_PRICE_REACH")
        confirmed=(first.close<e.swing.level if short else first.close>e.swing.level)
        break_bar=rows[(e.break_start_ms-SEPT_START)//THREE]
        already_open=(break_bar.open<e.swing.level if short else break_bar.open>e.swing.level)
        result.append(CrossingUncertainty(
            line.symbol,e.side,e.pivot_center_ms,e.raid_start_ms,e.raid_confirmed_ms,
            e.swing.center_ms,e.swing.known_ms,e.swing.native3m_ids,
            str(e.swing.level),e.source_original_3m_row_id,
            e.break_start_ms,e.break_known_ms,first.raw_id,
            first.start_ms,first.known_ms,confirmed,
            first.start_ms<e.break_start_ms,prior_count,already_open))
    t=tuple(result)
    return CrossingAudit(
        line.symbol,as_of_ms,t,len(t),
        sum(x.earlier_pre_close_reach for x in t),
        sum(x.earlier_pre_close_reach and not x.first_reachable_cross_close_confirmed for x in t),
        sum(x.earlier_pre_close_reach and x.first_reachable_cross_close_confirmed for x in t),
        sum(x.break_bar_open_beyond_level for x in t),
        len(t))
