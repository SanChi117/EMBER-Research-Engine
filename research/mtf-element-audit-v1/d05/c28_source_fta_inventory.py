"""C28 source-native 1H classic 3-candle IMB inventory before research BOS.

Directly sourced: primary Fair Value Gap / Imbalance lesson: classic three
candle gap between first and third wicks. Primary Context/TDA defines IMB,
RB, SNR and BSL/SSL as *different* potential first trouble areas (FTA).
RB/SNR are NOT approximated from two candle color reversal. Their complete
causal interaction and ranking require author labels (UNKNOWN).

This is a retrospective technical inventory on C26 original native3m data.
The C26 break CLOSE is known only at break_known_ms, not at break_start_ms;
we do NOT pretend the trade-side interval was known at break_start_ms.
No trading, approved FTA, TP, RR or SL. PAPER ONLY / NOT_TRADE_READY.
"""
from dataclasses import dataclass
from decimal import Decimal
import hashlib,json
from c21b_original_3m_raid_break_geometry import _source,_hours
from c26_unswept_1h_fta_source import inspect_c26
from c20b_hourly_fractal_source_observer import HourSource

HOUR=3600000
THREE=180000

@dataclass(frozen=True)
class Gap:
    kind:str
    bottom:Decimal
    top:Decimal
    first_hour_start_ms:int
    third_hour_start_ms:int
    known_ms:int
    original_1h_row_ids:tuple[str,str,str]

@dataclass(frozen=True)
class GapHistory:
    first_touch_ms:int|None
    first_touch_original_3m_row_id:str|None
    first_full_traversal_ms:int|None
    state:str

@dataclass(frozen=True)
class IntervalWitness:
    kind:str
    bottom:str
    top:str
    known_ms:int
    first_hour_start_ms:int
    third_hour_start_ms:int
    first_hour_original_3m_row_id:str
    third_hour_original_3m_row_id:str
    history:GapHistory

@dataclass(frozen=True)
class Case:
    symbol:str
    raid_ms:int
    break_start_ms:int
    break_known_ms:int
    original_break_row_id:str
    side:str
    retrospective_break_close:str
    c26_historical_nearest_target:str|None
    c26_nearest_target_cross_state:str|None
    total_preknown_1h_classic_imb:int
    overlaps_entry_to_original_target:int
    overlaps_never_touched_before_break:int
    overlaps_first_touched_before_break:int
    overlaps_fully_traversed_before_break:int
    nearest_three_overlap_samples:tuple[IntervalWitness,...]
    all_overlap_witnesses_sha256:str
    candidate_ranking_status:str="AUTHOR_FTA_PRIORITY_UNKNOWN"
    other_families_status:str="RB_SNR_EQ_SESSION_AUTHOR_SEMANTICS_NOT_ADJUDICATED"
    readiness:str="NOT_TRADE_READY"
    author_approved:bool=False

@dataclass(frozen=True)
class Review:
    symbol:str
    as_of_ms:int
    original_parent_edges:int
    research_single_cases:int
    source_hours:int
    full_source_1h_classic_imb:int
    case_preknown_imb_edges:int
    case_overlap_imb_edges:int
    cases_with_overlap:int
    cases_with_previously_untouched_overlap:int
    case_overlap_previously_touched_edges:int
    case_overlap_prior_full_traversals:int
    cases:tuple[Case,...]
    readiness:str="NOT_TRADE_READY"
    author_approved_trades:int=0

def classic_1h_imb(hours):
    """Only primary textbook FVG inequality: h[i-2] vs h[i] wick gap."""
    if not isinstance(hours,tuple):
        raise ValueError("C28_HOURS_TUPLE_REQUIRED")
    prev=None
    for h in hours:
        if not isinstance(h,HourSource) or not h.native_rows or len(h.native_rows)!=20:
            raise ValueError("C28_HOUR_MISSING_SOURCE_PROVENANCE")
        if h.close_ms!=h.start_ms+HOUR or (
                prev is not None and h.start_ms!=prev+HOUR):
            raise ValueError("C28_NONCONTIGUOUS_OR_UNCLOSED_1H")
        if any(not isinstance(x,Decimal) or not x.is_finite() for x in
               (h.open,h.high,h.low,h.close)):
            raise ValueError("C28_BAD_1H_PRICE")
        if not (0<h.low<=min(h.open,h.close)<=max(h.open,h.close)<=h.high):
            raise ValueError("C28_IMPOSSIBLE_1H_PRICE")
        prev=h.start_ms
    found=[]
    for i in range(2,len(hours)):
        a,b,c=hours[i-2:i+1]
        if a.high<c.low:
            kind,low,high="BULL_CLASSIC_IMB",a.high,c.low
        elif a.low>c.high:
            kind,low,high="BEAR_CLASSIC_IMB",c.high,a.low
        else:
            continue
        found.append(Gap(kind,low,high,a.start_ms,c.start_ms,c.close_ms,
                         (a.native_rows[0],b.native_rows[0],c.native_rows[0])))
    return tuple(found)

def gap_history(gap,rows,*,before_ms):
    if (gap.kind not in ("BULL_CLASSIC_IMB","BEAR_CLASSIC_IMB") or
        gap.bottom>=gap.top or gap.known_ms>before_ms):
        raise ValueError("C28_UNPREKNOWN_OR_INVALID_GAP")
    first_touch=first_id=first_full=None
    last=-1
    for b in rows:
        if b.start_ms<=last or b.known_ms<=b.start_ms:
            raise ValueError("C28_UNORDERED_OR_UNCLOSED_NATIVE3M")
        last=b.start_ms
        if b.known_ms<=gap.known_ms:
            continue
        if b.known_ms>before_ms:
            break
        # Price range overlap (including boundary touch), no intrabar order inference.
        touched=b.low<=gap.top and b.high>=gap.bottom
        # Full zone traversal measured on a closed 3m wick range, NOT fill.
        traversed=b.low<=gap.bottom and b.high>=gap.top
        if touched and first_touch is None:
            first_touch=b.start_ms
            first_id=b.raw_id
        if traversed and first_full is None:
            first_full=b.start_ms
    state=("FULL_WICK_TRAVERSAL_OBSERVED" if first_full is not None
           else "PRIOR_WICK_TOUCH_OBSERVED" if first_touch is not None
           else "NO_PRIOR_WICK_TOUCH_OBSERVED")
    return GapHistory(first_touch,first_id,first_full,state)

def price_interval_overlap(gap,side,entry,target):
    if (side not in ("SHORT","LONG") or
        not isinstance(entry,Decimal) or not entry.is_finite()):
        raise ValueError("C28_INVALID_SIDE_OR_ENTRY")
    if target is None:return False
    if not isinstance(target,Decimal) or not target.is_finite():
        raise ValueError("C28_INVALID_HISTORICAL_TARGET")
    if not (target<entry if side=="SHORT" else target>entry):
        raise ValueError("C28_TARGET_WRONG_SIDE")
    bottom=min(entry,target);top=max(entry,target)
    # Positive-width strict intersection only: boundary alone cannot become a FTA.
    return gap.bottom<top and gap.top>bottom

def _witness(gap,history):
    return IntervalWitness(gap.kind,str(gap.bottom),str(gap.top),
        gap.known_ms,gap.first_hour_start_ms,gap.third_hour_start_ms,
        gap.original_1h_row_ids[0],gap.original_1h_row_ids[2],history)

def _sha_all(witnesses):
    data=[{
        "kind":w.kind,"bottom":w.bottom,"top":w.top,
        "known_ms":w.known_ms,"first_hour_start_ms":w.first_hour_start_ms,
        "third_hour_start_ms":w.third_hour_start_ms,
        "first_source":w.first_hour_original_3m_row_id,
        "third_source":w.third_hour_original_3m_row_id,
        "history":{"touch":w.history.first_touch_ms,
                   "touch_row":w.history.first_touch_original_3m_row_id,
                   "full":w.history.first_full_traversal_ms,
                   "state":w.history.state}} for w in witnesses]
    blob=json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()

def inspect_c28(source,*,as_of_ms):
    original=_source(source,as_of_ms)
    previous=inspect_c26(source,as_of_ms=as_of_ms)
    hours=_hours(original)
    gaps=classic_1h_imb(hours)
    output=[]
    for case in previous.cases:
        if case.author_approved or case.readiness!="NOT_TRADE_READY":
            raise ValueError("C28_FORGED_C26_APPROVAL")
        break_ms=case.break_start_ms
        i=(break_ms-original[0].start_ms)//THREE
        if i<0 or i>=len(original) or original[i].raw_id!=case.break_original_row_id:
            raise ValueError("C28_ORIGINAL_BREAK_ROW_DRIFT")
        break_known_ms=original[i].known_ms
        if break_known_ms>as_of_ms:
            raise ValueError("C28_BREAK_BAR_NOT_CLOSED")
        # No current-break candle is allowed in history, while break-close price
        # is deliberately labelled retrospective.
        prefix=original[:i]
        available=tuple(g for g in gaps if g.known_ms<=break_ms)
        entry=Decimal(case.research_entry_close)
        target=Decimal(case.nearest_historical_target) if case.nearest_historical_target is not None else None
        matching=tuple(g for g in available if price_interval_overlap(g,case.side,entry,target))
        witnesses=tuple(_witness(g,gap_history(g,prefix,before_ms=break_ms)) for g in matching)
        sorted_w=tuple(sorted(witnesses,key=lambda w:(
            max(Decimal(w.bottom)-entry,entry-Decimal(w.top),Decimal(0)),
            w.known_ms,w.first_hour_start_ms)))
        output.append(Case(source.symbol,case.raid_ms,break_ms,break_known_ms,
            case.break_original_row_id,case.side,case.research_entry_close,
            case.nearest_historical_target,
            case.nearest_target_history.state if case.nearest_target_history else None,
            len(available),len(witnesses),
            sum(w.history.state=="NO_PRIOR_WICK_TOUCH_OBSERVED" for w in witnesses),
            sum(w.history.first_touch_ms is not None for w in witnesses),
            sum(w.history.first_full_traversal_ms is not None for w in witnesses),
            sorted_w[:3],_sha_all(sorted_w)))
    cases=tuple(output)
    if len(cases)!=previous.research_single_cases:
        raise ValueError("C28_C26_FROZEN_CASE_COUNT_DRIFT")
    return Review(source.symbol,as_of_ms,previous.original_parent_edges,len(cases),
        len(hours),len(gaps),
        sum(c.total_preknown_1h_classic_imb for c in cases),
        sum(c.overlaps_entry_to_original_target for c in cases),
        sum(c.overlaps_entry_to_original_target>0 for c in cases),
        sum(c.overlaps_never_touched_before_break>0 for c in cases),
        sum(c.overlaps_first_touched_before_break for c in cases),
        sum(c.overlaps_fully_traversed_before_break for c in cases),cases)
