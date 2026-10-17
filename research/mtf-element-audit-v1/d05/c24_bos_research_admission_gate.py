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

def audit_route_admission(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    swings=_swings(rows)
    events=observe_native3m_raid_break(source,as_of_ms=as_of_ms).potential_breaks
    parent_counts=Counter(e.break_start_ms for e in events)
    outputs=[]
    for e in events:
        i=(e.break_start_ms-SEPT_START)//THREE
        current,prior=rows[i],rows[i-1]
        if current.raw_id!=e.source_original_3m_row_id:
            raise ValueError("SOURCE_C24_ROW_ID_MISMATCH")
        eligible=[]
        for s in swings:
            if s.kind!=e.swing.kind:continue
            if not (e.raid_start_ms<=s.center_ms):continue
            if not (e.raid_start_ms+3600000<=s.known_ms<=e.break_start_ms):continue
            if e.side=="SHORT" and s.level>=e.raid_level:continue
            if e.side=="LONG" and s.level<=e.raid_level:continue
            eligible.append(s)
        if not eligible or eligible[-1]!=e.swing:
            raise ValueError("C24_C21B_RESEARCH_PIVOT_DRIFT")
        first=[]
        for s in eligible:
            old=rows[(s.known_ms-SEPT_START)//THREE:i]
            short=e.side=="SHORT"
            if any(x.close<s.level if short else x.close>s.level for x in old):
                continue
            if (prior.close>=s.level and current.close<s.level if short
                else prior.close<=s.level and current.close>s.level):
                first.append(s)

        parents=parent_counts[e.break_start_ms]
        if not first:
            reason="REJECT_NO_FIRST_INTACT_3M_PIVOT"
        elif len(first)>1:
            reason="REJECT_MULTIPLE_FIRST_INTACT_3M_PIVOTS"
        elif parents>1:
            reason="REJECT_MULTIPLE_1H_RAID_PARENTS"
        else:
            reason="RESEARCH_SINGLE_CANDIDATE_AUTHOR_SESSION_FTA_SL_UNVERIFIED"
        outputs.append(GateCase(e.pivot_center_ms,e.raid_start_ms,current.raw_id,
            e.break_start_ms,len(first),tuple(s.center_ms for s in first),
            parents,reason))
    cases=tuple(outputs)
    return AdmissionAudit(source.symbol,as_of_ms,len(cases),
        sum(x.first_intact_pivot_count==1 and x.same_break_bar_htf_parent_edges==1 for x in cases),
        sum(x.reason=="REJECT_MULTIPLE_FIRST_INTACT_3M_PIVOTS" for x in cases),
        sum(x.reason=="REJECT_NO_FIRST_INTACT_3M_PIVOT" for x in cases),
        sum(x.reason=="REJECT_MULTIPLE_1H_RAID_PARENTS" for x in cases),
        sum(x.reason=="RESEARCH_SINGLE_CANDIDATE_AUTHOR_SESSION_FTA_SL_UNVERIFIED" for x in cases),
        cases)
