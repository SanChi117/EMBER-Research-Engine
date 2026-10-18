"""C30: source-known 1H liquidity wick raids and prior classic IMB wick touches
linked to C29 opposite-color pairs. Research predicates, NOT author RB/SNR.

Deliberately no RB/SNR recognition, FTA ranking, TP, entry, RR or signal.
Fractal pivot must be right-confirmed before pair's first interacting hour.
Strict equality != sweep; strict wick vs body; earlier strict crossing means
NOT first liquidity raid. FVG must be fully formed before interaction and
earlier wick tests are tracked. Author wick zone and IMB-settlement unknown.
Original C21-C29 receipts remain unchanged. PAPER ONLY.
"""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from c21b_original_3m_raid_break_geometry import _source,_hours
from c20b_hourly_fractal_source_observer import observe_fractals_and_first_breach
from c28_source_fta_inventory import classic_1h_imb
from c29_rb_snr_source_guards import observe_opposite_pairs,inspect_c29

@dataclass(frozen=True)
class Interaction:
    pair_first_ms:int
    pair_second_ms:int
    pair_known_ms:int
    pair_direction:str
    hour_position:str
    hour_start_ms:int
    hour_source_original3m_id:str
    family:str
    source_level_or_zone:str
    source_known_ms:int
    source_first_original3m_id:str
    geometric_class:str
    previous_touch_class:str
    author_rule_status:str="NOT_AUTHOR_CONFIRMED"

@dataclass(frozen=True)
class SourcePairEvidence:
    pair_first_ms:int
    pair_second_ms:int
    known_ms:int
    original_first_id:str
    original_second_id:str
    direction:str
    distinct_liquidity_wick_interactions:int
    first_cross_liquidity_wick_interactions:int
    liquidity_body_cross_observations:int
    source_imb_wick_interactions:int
    imb_wick_first_tests:int
    source_imb_body_observations:int
    selected_technical_examples:tuple[Interaction,...]
    full_interactions_sha256:str
    academic_rb_status:str="NEEDS_AUTHOR_VALID_RAID_IMB_AND_RB_WICK_BOUNDARY"
    academic_snr_status:str="NEEDS_AUTHOR_SNR_LEVEL_THIRD_CLOSE_AND_FIRST_TEST"
    first_fta_status:str="AUTHOR_FTA_PRIORITY_UNKNOWN"
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class Case:
    symbol:str
    original_research_break_row_id:str
    research_break_start_ms:int
    preknown_opposing_pair_relations:int
    preknown_pairs_with_prior_liquidity_wick:int
    preknown_pairs_with_first_liquidity_wick:int
    preknown_pairs_with_prior_imb_wick:int
    preknown_pairs_with_first_imb_wick:int
    source_preknown_pairs_with_any_wick_interaction:int
    source_case_evidence_sha256:str
    latest_three_unranked_pairs:tuple[SourcePairEvidence,...]
    author_rb_approved:int=0
    author_snr_approved:int=0
    first_fta_approved:int=0
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class Review:
    symbol:str
    as_of_ms:int
    original_parent_edges:int
    research_single_cases:int
    original_closed_1h:int
    source_known_fractals:int
    source_classic_1h_imb:int
    opposite_1h_pairs:int
    pairs_with_known_liquidity_wick:int
    pairs_with_first_liquidity_wick:int
    pairs_with_known_imb_wick:int
    pairs_with_first_imb_wick:int
    pairs_with_any_wick_interaction:int
    case_preknown_pair_links:int
    cases_with_any_source_wick_link:int
    cases_with_first_liquidity_wick_link:int
    cases_with_first_imb_wick_link:int
    cases:tuple[Case,...]
    readiness:str="NOT_TRADE_READY"
    approved_trades:int=0

def _cross(hour,kind,level):
    if (kind not in ("BSL","SSL") or not isinstance(level,Decimal)
        or not level.is_finite() or not (hour.low<=hour.open<=hour.high
        and hour.low<=hour.close<=hour.high)):
        raise ValueError("C30_INVALID_LEVEL_OR_CANDLE")
    if kind=="BSL":
        wick=hour.high>level
        body=max(hour.open,hour.close)>level
        equal=hour.high==level or hour.open==level or hour.close==level
    else:
        wick=hour.low<level
        body=min(hour.open,hour.close)<level
        equal=hour.low==level or hour.open==level or hour.close==level
    return ("BODY_THROUGH" if body else "WICK_ONLY" if wick else
            "EQUALITY_ONLY" if equal else "NO_CROSS")

def _imb_cross(hour,gap):
    if (gap.kind not in ("BULL_CLASSIC_IMB","BEAR_CLASSIC_IMB")
        or gap.bottom>=gap.top or gap.known_ms>hour.start_ms):
        raise ValueError("C30_GAP_NOT_KNOWN_BEFORE_INTERACTION")
    # A bearish FVG is approached from below and bullish FVG from above.
    # A body touching ANY gap interior disqualifies wick-only.
    if gap.kind=="BULL_CLASSIC_IMB":
        # Wick approach from ABOVE: both open/close on or above top.
        near=min(hour.open,hour.close)
        if hour.low<gap.top and near>=gap.top:
            return "WICK_ONLY"
        if hour.low==gap.top and near>=gap.top:
            return "BOUNDARY_ONLY"
        # Body occupies at least some strict FVG interior.
        if near<gap.top and max(hour.open,hour.close)>gap.bottom:
            return "BODY_INTERACTION"
    else:
        # Wick approach from BELOW: both open/close on or below bottom.
        near=max(hour.open,hour.close)
        if hour.high>gap.bottom and near<=gap.bottom:
            return "WICK_ONLY"
        if hour.high==gap.bottom and near<=gap.bottom:
            return "BOUNDARY_ONLY"
        if near>gap.bottom and min(hour.open,hour.close)<gap.top:
            return "BODY_INTERACTION"
    return "NO_INTERACTION"

def _first_pivot_cross(pivot,hours):
    """Earliest true strict break after pivot is author-unselected but observable."""
    return next((h.start_ms for h in hours if h.start_ms>=pivot.known_ms
        and _cross(h,pivot.kind,pivot.level) in ("WICK_ONLY","BODY_THROUGH")),None)

def _first_gap_touch(gap,hours):
    return next((h.start_ms for h in hours if h.start_ms>=gap.known_ms
        and _imb_cross(h,gap) in ("WICK_ONLY","BODY_INTERACTION")),None)

def _interaction(pair,slot,hour,p,kind,level,klass,previous,source_id):
    return Interaction(pair.first_ms,pair.second_ms,pair.pair_known_ms,
        pair.direction,slot,hour.start_ms,hour.native_rows[0],kind,
        str(level),p.known_ms,source_id,klass,previous)

def source_pair_wick_evidence(hours,pivots,gaps):
    """Calculate real source-known prerequisite events, not academic RB labels."""
    pairs=observe_opposite_pairs(hours,as_of_ms=hours[-1].close_ms if hours else 0)
    valid_hours={h.start_ms:h for h in hours}
    for p in pivots:
        if (p.kind not in ("BSL","SSL") or type(p.level)!=Decimal or
            not p.level.is_finite() or not p.source_rows or
            p.known_ms<=p.center_ms):
            raise ValueError("C30_CORRUPTED_PIVOT")
    liquidity_first={ (p.kind,p.center_ms,p.level):
                      _first_pivot_cross(p,hours) for p in pivots}
    gap_first={(g.kind,g.first_hour_start_ms,g.bottom,g.top):
               _first_gap_touch(g,hours) for g in gaps}
    out=[]
    for pair in pairs:
        first,second=valid_hours[pair.first_ms],valid_hours[pair.second_ms]
        ev=[]
        for slot,h in (("FIRST",first),("SECOND",second)):
            for pivot in pivots:
                if pivot.known_ms>h.start_ms:continue
                klass=_cross(h,pivot.kind,pivot.level)
                if klass not in ("WICK_ONLY","BODY_THROUGH"):continue
                first_ms=liquidity_first[(pivot.kind,pivot.center_ms,pivot.level)]
                if first_ms is None or first_ms>h.start_ms:
                    raise ValueError("C30_WRONG_PIVOT_FIRST_BREACH")
                state="FIRST_STRICT_BREACH" if first_ms==h.start_ms else "EARLIER_STRICT_BREACH"
                ev.append(_interaction(pair,slot,h,pivot,"PRIOR_1H_"+pivot.kind,
                    pivot.level,klass,state,pivot.source_rows[0]))
            for gap in gaps:
                if gap.known_ms>h.start_ms:continue
                klass=_imb_cross(h,gap)
                if klass not in ("WICK_ONLY","BODY_INTERACTION"):continue
                first_ms=gap_first[(gap.kind,gap.first_hour_start_ms,gap.bottom,gap.top)]
                if first_ms is None or first_ms>h.start_ms:
                    raise ValueError("C30_WRONG_IMB_FIRST_TOUCH")
                state="FIRST_STRICT_TOUCH" if first_ms==h.start_ms else "PREVIOUS_TOUCH"
                ev.append(_interaction(pair,slot,h,gap,"PRIOR_"+gap.kind,
                    (str(gap.bottom)+".."+str(gap.top)),klass,state,gap.original_1h_row_ids[0]))
        ev.sort(key=lambda e:(e.hour_start_ms,e.family,e.source_known_ms,
                               e.source_level_or_zone,e.previous_touch_class))
        first_wick=sum(e.family.startswith("PRIOR_1H_") and e.geometric_class=="WICK_ONLY"
                       and e.previous_touch_class=="FIRST_STRICT_BREACH" for e in ev)
        n_liq=sum(e.family.startswith("PRIOR_1H_") and e.geometric_class=="WICK_ONLY" for e in ev)
        n_imb=sum("IMB" in e.family and e.geometric_class=="WICK_ONLY" for e in ev)
        first_imb=sum("IMB" in e.family and e.geometric_class=="WICK_ONLY"
                      and e.previous_touch_class=="FIRST_STRICT_TOUCH" for e in ev)
        records=[e.__dict__ for e in ev]
        digest=sha256(json.dumps(records,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        out.append(SourcePairEvidence(pair.first_ms,pair.second_ms,pair.pair_known_ms,
            pair.first_row_id,pair.second_row_id,pair.direction,
            n_liq,first_wick,
            sum(e.family.startswith("PRIOR_1H_") and e.geometric_class=="BODY_THROUGH" for e in ev),
            n_imb,first_imb,
            sum("IMB" in e.family and e.geometric_class=="BODY_INTERACTION" for e in ev),
            tuple(ev[:3]),digest))
    return tuple(out)

def inspect_c30(source,*,as_of_ms):
    rows=_source(source,as_of_ms)
    prev=inspect_c29(source,as_of_ms=as_of_ms)
    hours=_hours(rows)
    pivots,_=observe_fractals_and_first_breach(hours)
    gaps=classic_1h_imb(hours)
    pairs=source_pair_wick_evidence(hours,pivots,gaps)
    byknown=tuple(sorted(pairs,key=lambda p:p.known_ms))
    cases=[]
    for case in prev.cases:
        if case.readiness!="NOT_TRADE_READY":
            raise ValueError("C30_FORGED_PREVIOUS_READY")
        eligible=tuple(p for p in byknown if p.known_ms<=case.research_break_ms)
        if len(eligible)!=case.paired_opposite_closed_1h_count:
            raise ValueError("C30_C29_FROZEN_PAIR_COUNT_DRIFT")
        # Pair interaction hours are BOTH fully closed before research
        # break BAR START. Cannot backdate to the pair first candle.
        if any(p.known_ms>case.research_break_ms for p in eligible):
            raise ValueError("C30_FUTURE_PAIR_LEAK")
        def any_liq(p):return p.distinct_liquidity_wick_interactions>0
        def first_liq(p):return p.first_cross_liquidity_wick_interactions>0
        def any_imb(p):return p.source_imb_wick_interactions>0
        def first_imb(p):return p.imb_wick_first_tests>0
        brief=[{
            "ms":p.second_ms,"liquidity_wick":p.distinct_liquidity_wick_interactions,
            "first_liquidity_wick":p.first_cross_liquidity_wick_interactions,
            "imb_wick":p.source_imb_wick_interactions,"first_imb_wick":p.imb_wick_first_tests,
            "sha":p.full_interactions_sha256} for p in eligible]
        cases.append(Case(source.symbol,case.original_break_row_id,case.research_break_ms,
            len(eligible),sum(map(any_liq,eligible)),sum(map(first_liq,eligible)),
            sum(map(any_imb,eligible)),sum(map(first_imb,eligible)),
            sum(any_liq(p) or any_imb(p) for p in eligible),
            sha256(json.dumps(brief,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
            eligible[-2:]))
    result=tuple(cases)
    if len(result)!=prev.research_single_cases:
        raise ValueError("C30_SOURCE_RESEARCH_CASE_COUNT_DRIFT")
    return Review(source.symbol,as_of_ms,prev.original_parent_edges,
        len(result),len(hours),len(pivots),len(gaps),len(pairs),
        sum(p.distinct_liquidity_wick_interactions>0 for p in pairs),
        sum(p.first_cross_liquidity_wick_interactions>0 for p in pairs),
        sum(p.source_imb_wick_interactions>0 for p in pairs),
        sum(p.imb_wick_first_tests>0 for p in pairs),
        sum(p.distinct_liquidity_wick_interactions>0 or p.source_imb_wick_interactions>0
            for p in pairs),sum(c.preknown_opposing_pair_relations for c in result),
        sum(c.source_preknown_pairs_with_any_wick_interaction>0 for c in result),
        sum(c.preknown_pairs_with_first_liquidity_wick>0 for c in result),
        sum(c.preknown_pairs_with_first_imb_wick>0 for c in result),
        result)
