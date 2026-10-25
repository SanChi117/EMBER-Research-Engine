"""C73: first ANY ORIGINAL 3m POI source touch, repeated *separate* visits,
and Route A 15m Trigger vs 15m VC strict fail-closed semantic split.

Owner '2. Entry by IMB & SNR.txt': original new 1H POI (RB,SNR,IMB)
needs actual POI test; only if real 15m trigger SSL/BSL/eligible IMB
may proceed to real 5m VC [IMB,SNR]. If absent, direct real 15m VC.
Neither C71 source 15m geometry nor C72 source 5m geometry proves an
owner trigger, VC, valid first test, StrongHL, SL, TP or trade.

First raw source wick and source revisit episodes are facts about price.
Count a revisit only after >=1 COMPLETE original3m candle with NO wick
overlap: staying inside for ten candles is ONE visit, not ten tests.
Bound visit measurement BEFORE the start of the first C71 15m pattern.
Recompute C71 and C72 from original source, no forged downstream states.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21_native3m_source_bridge import Original3mRow,THREE
from c67_route_a_1h_trigger_vs_new_poi_source_fork import RouteAForkSource
from c69_exact_native15m_first_liquidity_raid_vs_poi_test import C69SourceContact
from c70_exact_native3m_first_raid_or_poi_source_wick import Original3mFirstSourceWick
from c71_post_contact_closed_15m_vc_1h_bos_semantic_gate import (
    PostContactSourceGate,classify_after_original3m_contact)
from c72_original_native5m_source_vc_after15m_gate import (
    C72RouteA5mSource,Original5mReview,first_any_5m_after_provisional15m)

ALIGNED=(
 "FIRST_ANY_NEW1H_POI_15M_IMB_TRIGGER_VS_VC_UNRESOLVED",
 "FIRST_ANY_NEW1H_POI_15M_SNR_TRIGGER_VS_VC_UNRESOLVED")
STATES=(
 "NOT_NEW_1H_POI_SOURCE_BRANCH",
 "NEW_1H_POI_SOURCE_NO_ORIGINAL3M_FIRST_TOUCH",
 "NEW_1H_POI_FIRST_ANY_RAW3M_TOUCH_NO_UNAMBIGUOUS_15M_CHAIN",
 "NEW_1H_POI_FIRST_15M_PATTERN_SINGLE_SOURCE_VISIT_NOT_OWNER_VALID",
 "NEW_1H_POI_FIRST_15M_PATTERN_REVISITED_SOURCE_POI_NOT_OWNER_VALID"
)
class C73Rejected(ValueError):pass
@dataclass(frozen=True)
class C73OriginalSourcePoiDecision:
    symbol:str
    side:str
    source_1h_poi_kind:str|None
    source_1h_poi_created_at_ms:int|None
    source_1h_poi_bottom:str|None
    source_1h_poi_top:str|None
    original_first_source3m_touch_id:str|None
    original_first_source3m_touch_closed_ms:int|None
    first_source15m_event_pattern_start_ms:int|None
    first_source15m_event_fully_known_ms:int|None
    episodes_before_first_15m_pattern:int|None
    second_visit_original3m_id:str|None
    last_visit_first_original3m_id:str|None
    source_continuous_visit_right_censored:bool|None
    source_first_5m_after_candidate_state:str
    c71_first_any_15m_source_state:str
    state:str
    author_1h_poi_valid_first_test:bool=False
    author_15m_trigger:bool=False
    author_15m_vc:bool=False
    author_5m_vc:bool=False
    author_stronghl:bool=False
    author_entry:bool=False
    author_structural_sl:bool=False
    route_b_idm_used:bool=False
    route_c_raid_bos_used:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def evaluate_new1h_source_poi_first_visit_and_route(
    fork,c69,c70,c71,c72,original3m,native15m,hours,
    source15_events,source1_events,original5m,source5_events,*,as_of_ms):
    if (not isinstance(fork,RouteAForkSource) or
        not isinstance(c69,C69SourceContact) or
        not isinstance(c70,Original3mFirstSourceWick) or
        not isinstance(c71,PostContactSourceGate) or
        not isinstance(c72,C72RouteA5mSource) or
        not isinstance(original5m,Original5mReview) or
        any(x.readiness!="NOT_TRADE_READY" for x in
            (fork,c69,c70,c71,c72,original5m)) or
        any((c71.author_4h_poi_valid_test,c71.author_1h_poi_valid_test,
             c71.author_1h_trigger,c71.author_15m_trigger,c71.author_15m_vc,
             c71.author_5m_vc,c71.author_1h_bos,c71.author_stronghl,
             c71.route_b_idm_approved,c71.route_c_raid_bos_approved,
             c72.author_valid_first_1h_poi_test,c72.author_15m_trigger,
             c72.author_5m_vc,c72.author_5m_stronghl,
             c72.author_structural_sl,c72.route_b_idm_used,
             c72.route_c_raid_bos_used,original5m.author_5m_vc)) or
        any((fork.orders,fork.fills,fork.trades,c69.orders,c69.fills,
             c69.trades,c70.orders,c70.fills,c70.trades,
             c71.orders,c71.fills,c71.trades,c72.orders,c72.fills,
             c72.trades,original5m.fills,original5m.trades)) or
        fork.symbol!=c69.symbol or fork.symbol!=c70.symbol or
        fork.symbol!=c71.symbol or fork.symbol!=c72.symbol or
        fork.symbol!=original5m.symbol or
        c71.original_4h_source_side!=fork.original_4h_source_side or
        c72.side!=fork.original_4h_source_side or
        c70.side!=fork.original_4h_source_side or
        as_of_ms!=original5m.as_of_ms):
        raise C73Rejected("C73_UNTRUSTED_PARENT_SOURCE_OR_AUTHOR_PROMOTION")
    # Independent *full* downstream recomputation verifies source 3m
    # raw price and SHA + 15m/1h event clock and 5m first ANY source.
    recreated71=classify_after_original3m_contact(
        fork,c69,c70,native15m,original3m,hours,
        source15_events,source1_events,as_of_ms=as_of_ms)
    if recreated71!=c71:
        raise C73Rejected("C73_C71_SOURCE_FIRST_ANY_SHA_OR_TIMESTAMP_DRIFT")
    recreated72=first_any_5m_after_provisional15m(c71,original5m,source5_events)
    if recreated72!=c72:
        raise C73Rejected("C73_C72_FIRST_ANY_5M_SOURCE_OR_BRANCH_DRIFT")
    def out(state,f=None,pattern=None,visits=None,second=None,last=None,ongoing=None):
        return C73OriginalSourcePoiDecision(
            fork.symbol,fork.original_4h_source_side,
            f.kind if f else None,
            f.fully_known_ms if f else None,
            str(f.zone_bottom) if f and f.zone_bottom is not None else None,
            str(f.zone_top) if f and f.zone_top is not None else None,
            c70.actual_first_native3m_id,
            c70.actual_first_native3m_closed_ms,
            pattern.pattern_start_ms if pattern else None,
            pattern.known_ms if pattern else None,
            visits,second,last,ongoing,c72.state,c71.state,state)
    if fork.first_source_1h_category!="NEW_1H_VC_POI":
        return out(STATES[0])
    f=fork.source_first_1h_event
    if f is None or f.zone_bottom is None or f.zone_top is None:
        raise C73Rejected("C73_MISSING_NEW_1H_POI_SOURCE_GEOMETRY")
    lo,hi=Decimal(f.zone_bottom),Decimal(f.zone_top)
    if not (lo.is_finite() and hi.is_finite() and 0<lo<hi and
            f.fully_known_ms<=as_of_ms):
        raise C73Rejected("C73_BAD_1H_SOURCE_POI_CREATION_OR_PRICE")
    if c70.actual_first_native3m_id is None:
        return out(STATES[1],f)
    if (c70.actual_first_native3m_start_ms is None or
        c70.actual_first_native3m_start_ms<f.fully_known_ms or
        c70.actual_first_native3m_closed_ms!=c70.actual_first_native3m_start_ms+THREE):
        raise C73Rejected("C73_FIRST_TOUCH_BEFORE_SOURCE_POI_EXISTS")
    if not isinstance(original3m,tuple) or not original3m:
        raise C73Rejected("C73_MISSING_ORIGINAL3M_SOURCE")
    def overlap(z):
        return z.low<=hi and z.high>=lo
    # The first source 3m touch must really be the first since f
    # fully existed: cannot start a later arbitrary visit as FIRST.
    prefix=tuple(z for z in original3m if
                 f.fully_known_ms<=z.start_ms<=c70.actual_first_native3m_start_ms)
    if (not prefix or not isinstance(prefix[-1],Original3mRow) or
        prefix[-1].raw_id!=c70.actual_first_native3m_id or
        not overlap(prefix[-1]) or any(overlap(z) for z in prefix[:-1])):
        raise C73Rejected("C73_SOURCE_FIRST_3M_TOUCH_NOT_PHYSICAL_FIRST")
    # Only an aligned *single* C71 source pattern can propose the Route
    # A fork; remaining source traces are not owner-labelled cases.
    if c71.state not in ALIGNED:
        return out(STATES[2],f)
    first_ms=c71.first_any_confirmed_event_ms
    candidates=tuple(z for z in source15_events if
           z.known_ms==first_ms and
           z.side==c71.original_4h_source_side and
           z.kind in c71.first_any_source_event_kinds)
    if len(candidates)!=1 or not candidates[0].pattern_start_ms>=c70.actual_first_native3m_closed_ms:
        raise C73Rejected("C73_NO_SINGLE_SOURCE15_PATTERN_AFTER_FIRST_TOUCH")
    e=candidates[0]
    if (first_ms!=c72.c71_provisional_15m_known_ms or
        first_ms!=e.known_ms or
        e.pattern_start_ms<f.fully_known_ms):
        raise C73Rejected("C73_FALSE_ROUTE_A_BRANCH_AFTER_SOURCE15M")
    # Episode counting uses ONLY bars strictly before future pattern
    # begins. Future reaction bars may not retroactively recategorize
    # the status of the FIRST source POI contact.
    observed=tuple(z for z in original3m if
         c70.actual_first_native3m_start_ms<=z.start_ms<e.pattern_start_ms)
    if (not observed or observed[0].raw_id!=c70.actual_first_native3m_id or
        observed[0].start_ms!=c70.actual_first_native3m_start_ms):
        raise C73Rejected("C73_INVALID_SOURCE_PRE_PATTERN_WINDOW")
    visits=0;inside=False;second=None;last=None
    for z in observed:
        now=overlap(z)
        if now and not inside:
            visits+=1
            last=z.raw_id
            if visits==2:second=z.raw_id
        inside=now
    if visits<1:
        raise C73Rejected("C73_MISSING_FIRST_SOURCE_VISIT")
    return out(STATES[4] if visits>1 else STATES[3],f,e,visits,second,last,inside)
