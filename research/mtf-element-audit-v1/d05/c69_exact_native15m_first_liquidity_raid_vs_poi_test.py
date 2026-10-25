"""C69 exact original native15m first raid/first 1H source POI wick contact.

No upgrade to author FIRST VALID POI test or StrongHL. For 1H
source SSL/BSL raid, recover all PREKNOWN, unswept strict 1H pivot
levels and scan the FOUR original native15m bars of that exact hour:
first bar through liquidity, never assume 1H last 15m bar is first.
Keep 1H wick-only reclaim distinct from 15m wick-only and from
15m close beyond liquidity. If two preknown levels first touched
on same bar, leave level ambiguous. For NEW 1H VC source POI,
replay entire original15m timeline after fully known 1H context and
verify first ANY wick test, not author-valid test. PAPER ONLY.
"""
from dataclasses import dataclass
from decimal import Decimal
from c16_c08_monthly_daily_htf_lineage import TF_MS
from c62_academic_snr_rb_imb_liquidity_source_separation import _validate,_preknown_unswept_levels_schedule
from c66_native15m_route_a_source_event_chain import _check15
from c67_route_a_1h_trigger_vs_new_poi_source_fork import RouteAForkSource
H=TF_MS["1h"];Q=TF_MS["15m"]
STATES=(
 "NO_UNAMBIGUOUS_C67_CONTEXT",
 "1H_IMB_TRIGGER_NOT_RAID_OR_POI_FIRST_TEST",
 "MISSING_OR_FAKE_ORIGINAL15M_HOUR",
 "NO_PREKNOWN_SOURCE_LIQUIDITY_LEVEL",
 "NO_REAL_NATIVE15M_LIQUIDITY_CROSS",
 "AMBIGUOUS_MULTIPLE_PREKNOWN_LIQUIDITY_LEVELS_SAME_FIRST_BAR",
 "RAID_FIRST_NATIVE15M_BAR_CLOSE_BEYOND_LEVEL_RECLAIM_LATER_1H",
 "RAID_FIRST_NATIVE15M_BAR_WICK_ONLY_RECLAIM_1H",
 "NEW_1H_POI_NO_SOURCE_FIRST_TEST",
 "NEW_1H_POI_SOURCE_FIRST15M_WICK_TEST_NOT_AUTHOR_VALID"
)
@dataclass(frozen=True)
class C69SourceContact:
    symbol:str
    side:str
    c67_fork_state:str
    source_event_kind:str|None
    source_event_fully_known_ms:int|None
    preknown_level_price:str|None
    preknown_level_known_ms:int|None
    number_of_levels_first_crossed_at_same_15m_bar:int
    first_exact_original15m_contact_id:str|None
    first_exact_original15m_contact_start_ms:int|None
    first_exact_original15m_contact_closed_ms:int|None
    first_15m_wick_only_reclaim:bool|None
    containing_1h_wick_only_reclaim:bool|None
    compared_four_original15m_to_derived1h:bool
    source_status:str
    author_first_valid_poi_test:bool=False
    author_liquidity_raid_confirmed:bool=False
    author_stronghl_confirmed:bool=False
    author_sl_level:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def first_original_native15m_source_contact(fork,hours,native15m,*,as_of_ms):
    if (not isinstance(fork,RouteAForkSource) or fork.readiness!="NOT_TRADE_READY"
        or fork.author_4h_poi_first_valid_test or fork.author_1h_trigger
        or fork.author_new_1h_vc_poi or fork.author_new_1h_poi_first_valid_test
        or fork.author_15m_volume_confirmation or fork.author_5m_volume_confirmation
        or fork.author_stronghl or fork.route_b_idm_used or fork.route_c_raid_bos_used
        or fork.orders or fork.fills or fork.trades
        or fork.original_4h_source_side not in ("LONG","SHORT")):
        raise ValueError("C69_FORGED_AUTHOR_GRADE_OR_ROUTE")
    bars=_validate(hours,as_of_ms)
    natives=_check15(native15m,as_of_ms=as_of_ms)
    if (as_of_ms%H or bars[0].symbol!=natives[0].symbol or
        bars[0].symbol!=fork.symbol or
        bars[-1].known_at_ms!=natives[-1].known_at_ms):
        raise ValueError("C69_UNALIGNED_SOURCE_1H15M")
    by15={x.start_ms:x for x in natives}
    by1={x.start_ms:x for x in bars}
    side=fork.original_4h_source_side
    f=fork.source_first_1h_event
    def out(state,level=None,known=None,ties=0,contact=None,wick=None,
            reclaim=None,parity=False):
        return C69SourceContact(fork.symbol,side,fork.state,
            f.kind if f else None,f.fully_known_ms if f else None,
            str(level) if level is not None else None,known,ties,
            contact.origin_raw_row_id if contact else None,
            contact.start_ms if contact else None,
            contact.known_at_ms if contact else None,
            wick,reclaim,parity,state)
    if (f is None or fork.first_source_1h_category not in
            ("TRIGGER","NEW_1H_VC_POI") or
        f.owner_trigger_approved or f.owner_new_vc_poi_approved or
        fork.state in ("FIRST_ANY_1H_TWO_SIDES_AMBIGUOUS",
                       "FIRST_ANY_1H_TRIGGER_AND_VC_AMBIGUOUS",
                       "FIRST_ANY_1H_SOURCE_OPPOSITE_SIDE") or
        len(fork.source_first_1h_conflict_kinds)>1 or
        f.side!=side):
        return out(STATES[0])
    if f.fully_known_ms>as_of_ms or f.fully_known_ms<=f.pattern_start_ms:
        raise ValueError("C69_FUTURE_OR_INVALID_C67_PARENT")
    if fork.first_source_1h_category=="NEW_1H_VC_POI":
        if (f.zone_bottom is None or f.zone_top is None or
            not Decimal(f.zone_bottom).is_finite() or
            not Decimal(f.zone_top).is_finite() or
            Decimal(f.zone_bottom)>=Decimal(f.zone_top) or
            Decimal(f.zone_bottom)<=0):
            raise ValueError("C69_INVALID_NEW_1H_SOURCE_POI_BOUNDS")
        low=Decimal(f.zone_bottom);high=Decimal(f.zone_top)
        candidates=tuple(x for x in natives if
           x.start_ms>=f.fully_known_ms and x.low<=high and x.high>=low)
        if not candidates:
            if fork.source_first_new_1h_poi_test_native15m_id is not None:
                raise ValueError("C69_C67_CLAIMS_NONEXISTENT_SOURCE_FIRST_TEST")
            return out(STATES[8])
        first=candidates[0]
        if (fork.source_first_new_1h_poi_test_native15m_id!=first.origin_raw_row_id or
            fork.source_first_new_1h_poi_test_closed_ms!=first.known_at_ms):
            raise ValueError("C69_C67_SOURCE_FIRST_TOUCH_ID_OR_TIME_DRIFT")
        return out(STATES[9],contact=first)
    if f.kind not in ("1H_SSL_RAID_SOURCE","1H_BSL_RAID_SOURCE"):
        return out(STATES[1])
    if (f.pattern_start_ms+H!=f.fully_known_ms or
        f.first_original15m_id!=(
            by1[f.pattern_start_ms].source_native_15m_rows[0]
            if f.pattern_start_ms in by1 else None)):
        raise ValueError("C69_FAKE_SOURCE_RAID_PARENT_1H_OR_15M_ID")
    hour=by1[f.pattern_start_ms]
    four=tuple(by15.get(f.pattern_start_ms+j*Q) for j in range(4))
    if any(x is None for x in four):
        return out(STATES[2])
    if (tuple(x.origin_raw_row_id for x in four)!=hour.source_native_15m_rows
        or four[0].open!=hour.open or four[-1].close!=hour.close
        or max(x.high for x in four)!=hour.high
        or min(x.low for x in four)!=hour.low
        or sum((x.volume for x in four),Decimal(0))!=hour.volume):
        raise ValueError("C69_ORIGINAL15M_TO_1H_OHLCV_PARITY_FAILURE")
    schedule=_preknown_unswept_levels_schedule(bars)
    index=(f.pattern_start_ms-bars[0].start_ms)//H
    if index<0 or index>=len(schedule):
        raise ValueError("C69_SOURCE_RAID_OUTSIDE_CLOSED_HOURS")
    typ="SSL" if side=="LONG" else "BSL"
    levels=[(val,known) for kind,val,known in schedule[index]
             if kind==typ and known<=f.pattern_start_ms and
             (hour.low<val and hour.open>=val and hour.close>=val
              if side=="LONG" else
              hour.high>val and hour.open<=val and hour.close<=val)]
    if not levels:
        return out(STATES[3],parity=True)
    firsts=[]
    for level,known in levels:
        crossed=next((x for x in four if (x.low<level if side=="LONG" else x.high>level)),None)
        if crossed is not None:
            firsts.append((crossed.start_ms,level,known,crossed))
    if not firsts:
        return out(STATES[4],parity=True)
    first_time=min(x[0] for x in firsts)
    first_at=tuple(x for x in firsts if x[0]==first_time)
    if len(first_at)>1:
        return out(STATES[5],ties=len(first_at),contact=first_at[0][3],
                   reclaim=True,parity=True)
    _,level,known,candle=first_at[0]
    wick=(candle.open>=level and candle.close>=level if side=="LONG"
          else candle.open<=level and candle.close<=level)
    oneh=(hour.open>=level and hour.close>=level if side=="LONG"
          else hour.open<=level and hour.close<=level)
    if not oneh:
        raise ValueError("C69_PREKNOWN_SOURCE_1H_RAID_NOT_RECLAIMED")
    return out(STATES[7] if wick else STATES[6],level,known,1,
               candle,wick,oneh,True)
