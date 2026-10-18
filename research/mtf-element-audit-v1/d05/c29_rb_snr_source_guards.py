"""C29 source-only opposite 1H candle pair and follow-up observation.

This does NOT detect author RB, SNR, MB, POI, FTA or actual trades.
Academic source prerequisites:
- RB: opposite candles PLUS wick-only liquidity raid / IMB interaction;
- SNR: opposite candles PLUS raid or FVG test AND a subsequent new
  fully formed candle settling across a source-defined level;
- MB: lacks the strong SNR liquidity/FVG basis, cannot claim SNR VC;
- first POI test requires a source-certified zone, not any candle color flip.
The author-selected raid/FVG interaction, POI boundaries and settlement
level are not grounded by these native OHLC bars alone, so stay UNKNOWN.
C28/C27/C26 original source evidence remains unchanged.
"""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from c20b_hourly_fractal_source_observer import HourSource
from c21b_original_3m_raid_break_geometry import _source,_hours
from c28_source_fta_inventory import inspect_c28

HOUR=3600000

@dataclass(frozen=True)
class SourcePair:
    first_ms:int
    second_ms:int
    pair_known_ms:int
    direction:str
    first_row_id:str
    second_row_id:str
    technical_wick_envelope_bottom:str
    technical_wick_envelope_top:str
    next_hour_ms:int|None
    next_hour_known_ms:int|None
    next_hour_row_id:str|None
    stricter_envelope_follow_through:bool|None
    rb_gate:str="NEEDS_AUTHOR_WICK_RAID_OR_IMB_INTERACTION"
    snr_gate:str="NEEDS_AUTHOR_LIQ_OR_FVG_AND_ZONE_SETTLEMENT"
    first_test_gate:str="NEEDS_SOURCE_CERTIFIED_POI_ZONE"
    author_approved:bool=False

@dataclass(frozen=True)
class Case:
    symbol:str
    research_break_ms:int
    original_break_row_id:str
    paired_opposite_closed_1h_count:int
    paired_with_later_closed_hour:int
    technical_extreme_envelope_follow_through:int
    paired_missing_later_closed_hour:int
    author_rb_confirmed:int
    author_snr_confirmed:int
    author_mb_as_snr_confirmed:int
    unranked_research_sample:tuple[SourcePair,...]
    complete_preknown_pairs_sha256:str
    status:str="NEEDS_AUTHOR_RB_SNR_WICK_RAID_AND_ZONE_LABELS"
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class Review:
    symbol:str
    as_of_ms:int
    original_parent_edges:int
    research_single_cases:int
    source_hours:int
    source_opposite_pairs:int
    source_followed_pairs:int
    source_extreme_envelope_follow_through:int
    case_preknown_pair_relations:int
    cases_with_pair_relation:int
    case_preknown_technical_follow_through_relations:int
    cases_with_technical_follow_through:int
    cases:tuple[Case,...]
    status:str="AUTHOR_FIRST_FTA_PRIORITY_UNKNOWN"
    readiness:str="NOT_TRADE_READY"
    author_approved_trades:int=0

def _validate(hours):
    if not isinstance(hours,tuple):
        raise ValueError("C29_REQUIRES_TUPLE_HOURS")
    prev=None
    for h in hours:
        if not isinstance(h,HourSource) or len(h.native_rows)!=20:
            raise ValueError("C29_MISSING_20_NATIVE3M_ROWS")
        if h.close_ms!=h.start_ms+HOUR or (prev is not None and h.start_ms!=prev+HOUR):
            raise ValueError("C29_OPEN_OR_NONCONTIGUOUS_HOUR")
        if not all(type(x)==Decimal and x.is_finite() for x in
                   (h.open,h.high,h.low,h.close)):
            raise ValueError("C29_NONFINITE_DECIMAL_PRICE")
        if not (0<h.low<=min(h.open,h.close)<=max(h.open,h.close)<=h.high):
            raise ValueError("C29_IMPOSSIBLE_OHLC")
        if any(not isinstance(x,str) or not x for x in h.native_rows):
            raise ValueError("C29_MISSING_RAW_ROW_ID")
        prev=h.start_ms

def _side(h):
    if h.close>h.open:return "BUY"
    if h.close<h.open:return "SELL"
    return "DOJI"

def _pair_record(a,b,third=None):
    if b.start_ms!=a.close_ms or (third and third.start_ms!=b.close_ms):
        raise ValueError("C29_NONCONTIGUOUS_PAIR")
    sa,sb=_side(a),_side(b)
    if sa=="DOJI" or sb=="DOJI" or sa==sb:
        raise ValueError("C29_NOT_OPPOSING_NONDOJI_PAIR")
    bottom=min(a.low,b.low);top=max(a.high,b.high)
    # Strict EXTREME envelope is research counterfactual only: author SNR
    # "level" is not proved to equal this wick bound.
    following=(third.close>top if sb=="BUY" else third.close<bottom) if third else None
    return SourcePair(a.start_ms,b.start_ms,b.close_ms,
        sa+"_THEN_"+sb,a.native_rows[0],b.native_rows[0],
        str(bottom),str(top),
        third.start_ms if third else None,
        third.close_ms if third else None,
        third.native_rows[0] if third else None,following)

def observe_opposite_pairs(hours,*,as_of_ms):
    if type(as_of_ms)!=int:
        raise ValueError("C29_INVALID_ASOF")
    _validate(hours)
    if hours and as_of_ms>hours[-1].close_ms:
        # Requesting time past the source is not allowed.
        raise ValueError("C29_FUTURE_ASOF_SOURCE")
    closed=tuple(h for h in hours if h.close_ms<=as_of_ms)
    out=[]
    for i in range(1,len(closed)):
        a,b=closed[i-1:i+1]
        if _side(a)=="DOJI" or _side(b)=="DOJI" or _side(a)==_side(b):
            continue
        nxt=closed[i+1] if i+1<len(closed) else None
        out.append(_pair_record(a,b,nxt))
    return tuple(out)

def _digest(pairs):
    raw=[{
        "a":x.first_ms,"b":x.second_ms,"known":x.pair_known_ms,
        "direction":x.direction,"araw":x.first_row_id,"braw":x.second_row_id,
        "bounds":[x.technical_wick_envelope_bottom,x.technical_wick_envelope_top],
        "c":x.next_hour_ms,"c_known":x.next_hour_known_ms,
        "craw":x.next_hour_row_id,"follow_through":x.stricter_envelope_follow_through,
        "rb":x.rb_gate,"snr":x.snr_gate,"first_test":x.first_test_gate
    } for x in pairs]
    return sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def structural_gates(pair,*,wick_raid_evidence=None,fvg_test_evidence=None,
                     author_zone_level=None,author_labeled=False):
    """Fail closed; non-empty caller hints never constitute source-certified labels.

    Never infer wick-vs-body raid from opposing candle colors or pass a
    nominal third candle through as author SNR price-level settlement.
    """
    if not isinstance(pair,SourcePair) or pair.author_approved:
        raise ValueError("C29_FORGED_SOURCE_PAIR")
    if author_labeled:
        raise ValueError("C29_AUTHOR_GOLDEN_NOT_PROVIDED")
    if wick_raid_evidence is not None and not isinstance(wick_raid_evidence,str):
        raise ValueError("C29_UNVERIFIABLE_WICK_EVIDENCE")
    if fvg_test_evidence is not None and not isinstance(fvg_test_evidence,str):
        raise ValueError("C29_UNVERIFIABLE_FVG_EVIDENCE")
    if author_zone_level is not None and (
        not isinstance(author_zone_level,Decimal) or not author_zone_level.is_finite()):
        raise ValueError("C29_UNVERIFIABLE_SNR_SETTLEMENT_LEVEL")
    return {
        "rb":"NEEDS_AUTHOR_WICK_RAID_OR_IMB_SOURCE_LABEL",
        "snr":"NEEDS_AUTHOR_LIQ_FVG_CONTEXT_AND_AUTHORED_SETTLEMENT_LEVEL",
        "mitigation_block":"MB_NOT_SNR_VOLUME_CONFIRMATION",
        "first_test":"NEEDS_AUTHOR_POI_WICK_BOUNDS_AND_FIRST_TEST_LABEL",
        "first_fta":"AUTHOR_FTA_PRIORITY_UNKNOWN",
        "author_approved_trades":0,
        "readiness":"NOT_TRADE_READY"
    }

def inspect_c29(source,*,as_of_ms):
    bars=_source(source,as_of_ms)
    prev=inspect_c28(source,as_of_ms=as_of_ms)
    hours=_hours(bars)
    _validate(hours)
    allpairs=observe_opposite_pairs(hours,as_of_ms=hours[-1].close_ms if hours else as_of_ms)
    cases=[]
    for c in prev.cases:
        if c.readiness!="NOT_TRADE_READY" or c.author_approved:
            raise ValueError("C29_FORGED_C28_SOURCE_APPROVAL")
        # STRICT break BAR START cutoff, never future 1H or the later
        # 3m break CLOSE. A pair with an unclosed confirming third hour
        # has no third-hour evidence.
        cutoff=c.break_start_ms
        available=tuple(p for p in allpairs if p.pair_known_ms<=cutoff)
        known=[]
        for p in available:
            if p.next_hour_known_ms is not None and p.next_hour_known_ms>cutoff:
                known.append(_pair_record(
                    next(h for h in hours if h.start_ms==p.first_ms),
                    next(h for h in hours if h.start_ms==p.second_ms),None))
            else:
                known.append(p)
        included=tuple(known)
        if any(p.next_hour_known_ms is not None and p.next_hour_known_ms>cutoff
               for p in included):
            raise ValueError("C29_FUTURE_THIRD_CONFIRM_LEAK")
        if any(p.author_approved for p in included):
            raise ValueError("C29_FALSE_AUTHOR_APPROVAL")
        cases.append(Case(source.symbol,cutoff,c.original_break_row_id,
            len(included),sum(p.next_hour_ms is not None for p in included),
            sum(p.stricter_envelope_follow_through is True for p in included),
            sum(p.next_hour_ms is None for p in included),0,0,0,
            included[-3:],_digest(included)))
    result=tuple(cases)
    if len(result)!=prev.research_single_cases:
        raise ValueError("C29_C28_SINGLETON_DRIFT")
    return Review(source.symbol,as_of_ms,prev.original_parent_edges,len(result),
        len(hours),len(allpairs),
        sum(p.next_hour_ms is not None for p in allpairs),
        sum(p.stricter_envelope_follow_through is True for p in allpairs),
        sum(x.paired_opposite_closed_1h_count for x in result),
        sum(x.paired_opposite_closed_1h_count>0 for x in result),
        sum(x.technical_extreme_envelope_follow_through for x in result),
        sum(x.technical_extreme_envelope_follow_through>0 for x in result),
        result)
