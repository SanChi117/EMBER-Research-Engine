"""C23 source-only first-intact 3m pivot arbitration; NEVER author-certified BOS.

Source author requires 1H wick fractal raid, 3m BOS in correct direction and
location, but does not specify which of competing eligible 3m swings is BOS.
A swing already crossed by closed price before the observed bar cannot have
its *first* closed structural break on that bar. Separate wick-first state.
Preserve all rival surviving swings. PAPER ONLY, no exchange access.
"""
from dataclasses import dataclass
from c21b_original_3m_raid_break_geometry import _source, _swings, observe_native3m_raid_break
from c21_native3m_source_bridge import THREE, SEPT_START

@dataclass(frozen=True)
class FirstIntactResult:
    symbol: str
    as_of_ms: int
    original_parent_edges: int
    total_eligible_before_first_break_test: int
    previously_close_broken_levels: int
    previously_wick_breached_levels: int
    still_close_intact_levels: int
    first_close_crossing_levels: int
    first_close_single_candidate_edges: int
    first_close_multiple_candidate_edges: int
    no_first_close_candidate_edges: int
    chosen_latest_proxy_previously_close_broken: int
    first_close_multiple_parent_bar_edges: int
    examples: tuple
    author_selected_pivots: int = 0
    approved_trades: int = 0
    readiness: str = "NOT_TRADE_READY"
    adjudication: str = "RESEARCH_FIRST_INTACT_PIVOT_NOT_AUTHOR_BOS"

def _direction_broken(bar, level, side, field):
    price=getattr(bar, field)
    return price<level if side=="SHORT" else price>level

def inspect_first_intact_pivots(source, *, as_of_ms):
    bars=_source(source,as_of_ms)
    swings=_swings(bars)
    events=observe_native3m_raid_break(source,as_of_ms=as_of_ms)
    out=[]
    for e in events.potential_breaks:
        i=(e.break_start_ms-SEPT_START)//THREE
        if i<1 or i>=len(bars) or bars[i].raw_id!=e.source_original_3m_row_id:
            raise ValueError("SOURCE_OR_BREAK_BAR_MISMATCH")
        if not (e.raid_confirmed_ms<=e.break_start_ms
                and e.swing.known_ms<=e.break_start_ms):
            raise ValueError("FUTURE_PIVOT_AT_BREAK")
        previous,current=bars[i-1],bars[i]
        eligible=[]
        for s in swings:
            if s.kind!=e.swing.kind:continue
            if s.center_ms<e.raid_start_ms:continue
            if s.known_ms<e.raid_start_ms+3600000:continue
            if s.known_ms>e.break_start_ms:continue
            if e.side=="SHORT" and s.level>=e.raid_level:continue
            if e.side=="LONG" and s.level<=e.raid_level:continue
            eligible.append(s)
        if not eligible or eligible[-1]!=e.swing:
            raise ValueError("C22B_SOURCE_ELIGIBLE_PIVOT_PARITY")
        retired_close,retired_wick,survivors,first_close=[],[],[],[]
        for s in eligible:
            past=bars[(s.known_ms-SEPT_START)//THREE:i]
            was_closed=any(_direction_broken(x,s.level,e.side,"close") for x in past)
            was_wick=any(_direction_broken(x,s.level,e.side,
                              "low" if e.side=="SHORT" else "high") for x in past)
            if was_closed:retired_close.append(s)
            if was_wick:retired_wick.append(s)
            if not was_closed:
                survivors.append(s)
                previous_ok=previous.close>=s.level if e.side=="SHORT" else previous.close<=s.level
                if previous_ok and _direction_broken(current,s.level,e.side,"close"):
                    first_close.append(s)
        out.append({
          "symbol":source.symbol, "raid_ms":e.raid_start_ms,
          "break_start_ms":e.break_start_ms, "break_original_row_id":current.raw_id,
          "eligible_count":len(eligible), "prior_close_broken_count":len(retired_close),
          "prior_wick_breached_count":len(retired_wick),
          "intact_count":len(survivors), "first_close_count":len(first_close),
          "first_close_pivot_centers":[s.center_ms for s in first_close],
          "latest_proxy_center_ms":e.swing.center_ms,
          "latest_proxy_already_broken":e.swing in retired_close,
          "first_close_status":(
            "RESEARCH_SINGLE_NOT_AUTHOR_BOS" if len(first_close)==1 else
            "RESEARCH_MULTIPLE_FIRST_CLOSE_ABSTAIN" if len(first_close)>1 else
            "NO_FIRST_CLOSE_LEVEL_ABSTAIN")
        })

    from collections import Counter
    bars_per=Counter(x["break_start_ms"] for x in out)
    return FirstIntactResult(
        symbol=source.symbol,as_of_ms=as_of_ms,original_parent_edges=len(out),
        total_eligible_before_first_break_test=sum(x["eligible_count"] for x in out),
        previously_close_broken_levels=sum(x["prior_close_broken_count"] for x in out),
        previously_wick_breached_levels=sum(x["prior_wick_breached_count"] for x in out),
        still_close_intact_levels=sum(x["intact_count"] for x in out),
        first_close_crossing_levels=sum(x["first_close_count"] for x in out),
        first_close_single_candidate_edges=sum(x["first_close_count"]==1 for x in out),
        first_close_multiple_candidate_edges=sum(x["first_close_count"]>1 for x in out),
        no_first_close_candidate_edges=sum(x["first_close_count"]==0 for x in out),
        chosen_latest_proxy_previously_close_broken=sum(x["latest_proxy_already_broken"] for x in out),
        first_close_multiple_parent_bar_edges=sum(bars_per[x["break_start_ms"]]>1 for x in out),
        examples=tuple(out[:10]))
