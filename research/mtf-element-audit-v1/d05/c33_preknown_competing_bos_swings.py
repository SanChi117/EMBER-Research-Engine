"""C33: enumerate source-preknown competing C21 3m BOS swings without choosing author swing.

Frozen C21 chooses latest strict 1+1 native3m swing, NOT proven author model.
This module shows ALL eligible swings known at the original BOS bar START,
with native SHA source ID and first source OHLC wick price-reach provenance.

PAPER ONLY / NOT_TRADE_READY: no author labels, entries, FTA, order or fill.
"""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from c21b_original_3m_raid_break_geometry import (
    ThreeBreak,ThreeSwing,_source,_swings,observe_native3m_raid_break,THREE)
from c31_bos_entry_semantic_disagreement import inspect_c31_bos,audit_single_bos

@dataclass(frozen=True)
class CompetingSwing:
    kind:str
    level:str
    center_ms:int
    known_ms:int
    original_left3m_sha_row_id:str
    original_center3m_sha_row_id:str
    original_right3m_sha_row_id:str
    selected_by_frozen_c21_proxy:bool
    first_wick_source_bar_ms:int|None
    first_wick_source_known_ms:int|None
    first_wick_original_row_id:str|None
    first_wick_closed_beyond:bool|None
    chosen_by_author:bool=False
    route_status:str="SOURCE_ONLY_AUTHOR_BOS_CHOICE_UNKNOWN"

@dataclass(frozen=True)
class CasePivotAudit:
    symbol:str
    side:str
    raid_1h_pivot_center_ms:int
    raid_start_ms:int
    raid_confirmed_ms:int
    raid_level:str
    raid_extreme:str
    break_3m_bar_start_ms:int
    break_3m_close_known_ms:int
    original_break3m_source_row_id:str
    frozen_c21_proxy_swing_center_ms:int
    frozen_c21_proxy_swing_level:str
    competing_preknown_swing_count:int
    alternative_preknown_swings:int
    proxy_is_latest_preknown:bool
    known_eligible_swing_set_sha256:str
    competing_swings:tuple[CompetingSwing,...]
    instructor_bos_status:str="NEEDS_AUTHOR_1H_3M_POSITIVE_NEGATIVE_GOLDENS"
    order_allowed:bool=False
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class ResearchAudit:
    symbol:str
    as_of_ms:int
    source3m_rows:int
    original_c21_parent_edges:int
    c31_research_singletons:int
    parents_with_multiple_preknown_swings:int
    parents_with_only_one_preknown_swing:int
    total_competing_preknown_swings:int
    max_preknown_competing_swings:int
    proxy_not_latest_preknown:int
    author_approved_bos:int
    orders_created:int
    trades_created:int
    cases:tuple[CasePivotAudit,...]
    readiness:str="NOT_TRADE_READY"

def _eligible_swing(event,s):
    if not isinstance(event,ThreeBreak) or not isinstance(s,ThreeSwing):
        raise ValueError("C33_UNTRUSTED_C21_SWING_OR_EVENT")
    if (event.side not in ("SHORT","LONG") or event.pivot_kind not in ("BSL","SSL")
        or (event.side=="SHORT" and event.pivot_kind!="BSL")
        or (event.side=="LONG" and event.pivot_kind!="SSL")):
        raise ValueError("C33_WRONG_RAID_SIDE")
    if (s.kind not in ("LOW","HIGH") or type(s.level)!=Decimal
        or not s.level.is_finite() or s.level<=0):
        raise ValueError("C33_BAD_SWING_SOURCE_PRICE")
    if s.kind!=("LOW" if event.side=="SHORT" else "HIGH"):
        return False
    if (s.center_ms<event.raid_start_ms or
        s.known_ms<event.raid_start_ms+THREE or
        s.known_ms>event.break_start_ms or
        s.center_ms>=event.break_start_ms):
        return False
    if (s.level>=event.raid_level if event.side=="SHORT"
        else s.level<=event.raid_level):
        return False
    return True

def _native_provenance(s,raw):
    if len(s.native3m_ids)!=3:
        raise ValueError("C33_SWING_NOT_THREE_ORIGINAL_3M_ROWS")
    left,center,right=s.native3m_ids
    ids=[raw.get(s.center_ms+(k-1)*THREE) for k in range(3)]
    if any(x is None for x in ids) or tuple(x.raw_id for x in ids)!=(left,center,right):
        raise ValueError("C33_SOURCE_SWING_SHA_ROW_MISMATCH")
    if s.known_ms!=ids[2].known_ms:
        raise ValueError("C33_SOURCE_SWING_RIGHT_CONFIRM_TIME_DRIFT")
    if s.kind=="LOW":
        valid=(s.level==ids[1].low and ids[1].low<ids[0].low and
               ids[1].low<ids[2].low)
    else:
        valid=(s.level==ids[1].high and ids[1].high>ids[0].high and
               ids[1].high>ids[2].high)
    if not valid:
        raise ValueError("C33_NOT_AN_ORIGINAL_STRICT_1PLUS1_PIVOT")
    return ids

def _first_source_wick(s,event,rows):
    """Touch or price reach is only known at original3m bar CLOSE, not tick."""
    start=max(s.known_ms,event.raid_confirmed_ms)
    for x in rows:
        if x.start_ms<start:continue
        if x.start_ms>event.break_start_ms:break
        if (x.low<s.level if event.side=="SHORT" else x.high>s.level):
            if x.known_ms>event.break_known_ms:
                raise ValueError("C33_FUTURE_WICK_SOURCE")
            closed=(x.close<s.level if event.side=="SHORT" else x.close>s.level)
            return (x.start_ms,x.known_ms,x.raw_id,closed)
    return (None,None,None,None)

def enumerate_original_competitors(event,rows,all_swings):
    """Get every source-eligible swing, ordered by confirmed-known then center."""
    # Reuse full original price, 1H raid and 3m BAR identity checks from
    # C31; otherwise an attacker could substitute a fabricated pivot.
    research=audit_single_bos(event,rows)
    if research.readiness!="NOT_TRADE_READY":
        raise ValueError("C33_FORGED_AUTHOR_RESEARCH_READY")
    raw={x.start_ms:x for x in rows}
    if len(raw)!=len(rows):
        raise ValueError("C33_DUPLICATED_SOURCE_BAR")
    selected=event.swing
    if not _eligible_swing(event,selected):
        raise ValueError("C33_SELECTED_SWING_NOT_CAUSALLY_ELIGIBLE")
    chosen=[]
    for s in all_swings:
        if not _eligible_swing(event,s):continue
        _native_provenance(s,raw)
        ms,known,row_id,closed=_first_source_wick(s,event,rows)
        chosen.append(CompetingSwing(s.kind,str(s.level),s.center_ms,s.known_ms,
            s.native3m_ids[0],s.native3m_ids[1],s.native3m_ids[2],
            s==selected,ms,known,row_id,closed))
    chosen.sort(key=lambda x:(x.known_ms,x.center_ms,x.kind,x.level))
    selected_matches=sum(x.selected_by_frozen_c21_proxy for x in chosen)
    if selected_matches!=1:
        raise ValueError("C33_ORIGINAL_C21_SELECTED_SWING_NOT_UNIQUE")
    if any(s.known_ms>event.break_start_ms or s.center_ms>=event.break_start_ms for s in chosen):
        raise ValueError("C33_FUTURE_SWING_INCLUDED")
    latest=max(x.known_ms for x in chosen)
    valid_latest=any(x.selected_by_frozen_c21_proxy and x.known_ms==latest for x in chosen)
    digest=sha256(json.dumps([x.__dict__ for x in chosen],sort_keys=True,
        separators=(",",":")).encode()).hexdigest()
    return CasePivotAudit(rows[0].symbol,event.side,event.pivot_center_ms,
        event.raid_start_ms,event.raid_confirmed_ms,str(event.raid_level),
        str(event.raid_extreme),event.break_start_ms,event.break_known_ms,
        event.source_original_3m_row_id,selected.center_ms,str(selected.level),
        len(chosen),len(chosen)-1,valid_latest,digest,tuple(chosen))

def inspect_c33(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    preceding=inspect_c31_bos(source,as_of_ms=as_of_ms)
    original=observe_native3m_raid_break(source,as_of_ms=as_of_ms)
    if len(original.potential_breaks)!=preceding.strict_closed_3m_research_edges:
        raise ValueError("C33_FROZEN_C21_C31_PARENT_DRIFT")
    swings=_swings(rows)
    observations=tuple(enumerate_original_competitors(e,rows,swings)
                       for e in original.potential_breaks)
    if any(x.order_allowed or x.trades or x.readiness!="NOT_TRADE_READY"
           for x in observations):
        raise ValueError("C33_AUTHOR_UNVERIFIED_TRADE_FORBIDDEN")
    return ResearchAudit(source.symbol,as_of_ms,len(rows),len(observations),
        preceding.research_single_case_count,
        sum(x.alternative_preknown_swings>0 for x in observations),
        sum(x.alternative_preknown_swings==0 for x in observations),
        sum(x.competing_preknown_swing_count for x in observations),
        max((x.competing_preknown_swing_count for x in observations),default=0),
        sum(not x.proxy_is_latest_preknown for x in observations),
        0,0,0,observations)
