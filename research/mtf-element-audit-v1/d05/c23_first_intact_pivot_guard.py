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
