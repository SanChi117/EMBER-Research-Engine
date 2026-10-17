"""C24: fail-closed research route admission after original C23 first-intact proof.

Distinct from an author-certified 1H/3m BOS trade. Refuse any order
or READY state; even a single first-intact candidate lacks author labels,
session/FTA/SL and tick-entry proof. PAPER ONLY.
"""
from dataclasses import dataclass
from collections import Counter
from c21b_original_3m_raid_break_geometry import _source,_swings,observe_native3m_raid_break
from c21_native3m_source_bridge import THREE,SEPT_START

@dataclass(frozen=True)
class GateCase:
    raid_fractal_ms:int
    raid_start_ms:int
    original_break_row_id:str
    break_start_ms:int
    first_intact_pivot_count:int
    first_intact_pivot_centers:tuple[int,...]
    same_break_bar_htf_parent_edges:int
    reason:str
    author_approved:bool=False

@dataclass(frozen=True)
class AdmissionAudit:
    symbol:str
    as_of_ms:int
    total_original_research_edges:int
    source_single_pivot_single_parent:int
    multiple_pivot_refused:int
    no_intact_pivot_refused:int
    multiple_parent_refused:int
    single_research_without_author_labels:int
    cases:tuple[GateCase,...]
    readiness:str="NOT_TRADE_READY"
    author_approved_bos:int=0
    approved_trades:int=0
