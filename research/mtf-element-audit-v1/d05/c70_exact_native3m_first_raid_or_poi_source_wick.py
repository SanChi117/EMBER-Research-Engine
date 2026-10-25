"""C70 original Binance native3m first source wick within C69 original15m.

FIRST original3m bar is source-proven, not guessed from 1H final candle
or 15m OHLCV. Original 5 x 3m must exactly equal source 15m OHLCV,
using distinct signed ZIP bar SHA:time. 1H raid is not known / admitted
until 1H closes, even though 3m first wick occurred earlier. NEW 1H
POI technical wick retest on 3m is NOT the owner's first VALID POI test.
Route A research only. Route B IDM and Route C raid BOS untouched.
"""
from dataclasses import dataclass
from decimal import Decimal
import re
from c16_c08_monthly_daily_htf_lineage import NativeKline,TF_MS,SEPT_START
from c21_native3m_source_bridge import Original3mRow,THREE
from c66_native15m_route_a_source_event_chain import _check15
from c67_route_a_1h_trigger_vs_new_poi_source_fork import RouteAForkSource
from c69_exact_native15m_first_liquidity_raid_vs_poi_test import C69SourceContact
Q=TF_MS["15m"];H=TF_MS["1h"]
SOURCE_OK=("RAID_FIRST_NATIVE15M_BAR_CLOSE_BEYOND_LEVEL_RECLAIM_LATER_1H",
           "RAID_FIRST_NATIVE15M_BAR_WICK_ONLY_RECLAIM_1H",
           "NEW_1H_POI_SOURCE_FIRST15M_WICK_TEST_NOT_AUTHOR_VALID")
STATES=(
 "NO_C69_UNAMBIGUOUS_SOURCE_CONTACT",
 "C69_SOURCE_15M_BAR_MISSING",
 "NO_ORIGINAL3M_WICK_CROSS",
 "RAID_FIRST_ORIGINAL3M_CLOSE_THROUGH_LEVEL_NOT_AUTHOR",
 "RAID_FIRST_ORIGINAL3M_WICK_ONLY_NOT_AUTHOR",
 "NEW1H_POI_FIRST_ORIGINAL3M_WICK_TEST_NOT_AUTHOR_VALID"
)
@dataclass(frozen=True)
class Original3mFirstSourceWick:
    symbol:str
    side:str
    source_15m_context:str
    source_15m_id:str|None
    actual_first_native3m_id:str|None
    actual_first_native3m_start_ms:int|None
    actual_first_native3m_closed_ms:int|None
    actual_first_native3m_wick_only:bool|None
    c69_parent_1h_fully_known_ms:int|None
    earliest_source_claim_eligible_ms:int|None
    five_original3m_to_native15m_ohlcv_equal:bool
    source_status:str
    author_first_valid_poi_test:bool=False
    author_liquidity_raid:bool=False
    author_stronghl:bool=False
    author_volume_confirmation:bool=False
    route_b_idm_used:bool=False
    route_c_raid_bos_used:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def original3m_first_wick_within_c69(fork,c69,native15m,original3m,*,as_of_ms):
    if (not isinstance(fork,RouteAForkSource) or not isinstance(c69,C69SourceContact)
        or fork.symbol!=c69.symbol or fork.original_4h_source_side!=c69.side
        or fork.author_4h_poi_first_valid_test or fork.author_1h_trigger
        or fork.author_new_1h_vc_poi or fork.author_new_1h_poi_first_valid_test
        or fork.author_15m_volume_confirmation or fork.author_5m_volume_confirmation
        or fork.author_stronghl or fork.route_b_idm_used or fork.route_c_raid_bos_used
        or fork.orders or fork.fills or fork.trades or fork.readiness!="NOT_TRADE_READY"
        or c69.author_first_valid_poi_test or c69.author_liquidity_raid_confirmed
        or c69.author_stronghl_confirmed or c69.author_sl_level
        or c69.orders or c69.fills or c69.trades or c69.readiness!="NOT_TRADE_READY"
        or not isinstance(original3m,tuple) or not original3m):
        raise ValueError("C70_FORGED_PARENT_OR_AUTHOR_CLAIM")
    source15=_check15(native15m,as_of_ms=as_of_ms)
    if (as_of_ms%H or as_of_ms!=source15[-1].known_at_ms or
        source15[0].symbol!=fork.symbol or c69.c67_fork_state!=fork.state):
        raise ValueError("C70_SOURCE_CONTEXT_OR_ASOF_MISMATCH")
    if original3m[0].start_ms!=SEPT_START or original3m[-1].known_ms!=as_of_ms:
        raise ValueError("C70_INCOMPLETE_OR_FUTURE_NATIVE3M_SOURCE")
    prev=None
    for z in original3m:
        if (not isinstance(z,Original3mRow) or z.symbol!=fork.symbol
            or z.known_ms!=z.start_ms+THREE or z.start_ms%THREE
            or (prev is not None and z.start_ms!=prev) or
            not isinstance(z.zip_sha,str) or not re.fullmatch(r"[a-f0-9]{64}",z.zip_sha)
            or z.raw_id!=z.zip_sha+":"+str(z.start_ms) or
            not all(isinstance(v,Decimal) and v.is_finite()
                    for v in (z.open,z.high,z.low,z.close,z.volume))
            or not(0<z.low<=min(z.open,z.close)<=max(z.open,z.close)<=z.high and z.volume>=0)):
            raise ValueError("C70_FORGED_OR_GAPPED_ORIGINAL3M_SOURCE")
        prev=z.known_ms
    def out(status,candle=None,wick=None,eligible=None,parity=False):
        return Original3mFirstSourceWick(fork.symbol,fork.original_4h_source_side,
            c69.source_status,c69.first_exact_original15m_contact_id,
            candle.raw_id if candle else None,
            candle.start_ms if candle else None,
            candle.known_ms if candle else None,wick,
            c69.source_event_fully_known_ms,eligible,parity,status)
    if c69.source_status not in SOURCE_OK:
        return out(STATES[0])
    start=c69.first_exact_original15m_contact_start_ms
    if (type(start) is not int or start%Q or
        c69.first_exact_original15m_contact_closed_ms!=start+Q):
        raise ValueError("C70_C69_UNTRUSTED_FIRST15M_CONTACT_TIME")
    original15={x.start_ms:x for x in source15}
    candle15=original15.get(start)
    if not candle15:
        return out(STATES[1])
    if c69.first_exact_original15m_contact_id!=candle15.origin_raw_row_id:
        raise ValueError("C70_C69_UNTRUSTED_FIRST15M_RAW_SHA_ID")
    firstidx=(start-SEPT_START)//THREE
    five=original3m[firstidx:firstidx+5]
    if (len(five)!=5 or any(x.start_ms!=start+i*THREE for i,x in enumerate(five))):
        raise ValueError("C70_MISSING_OR_UNALIGNED_5_ORIGINAL3M")
    orig=(five[0].open,max(x.high for x in five),
          min(x.low for x in five),five[-1].close,
          sum((x.volume for x in five),Decimal(0)))
    expected=(candle15.open,candle15.high,candle15.low,
              candle15.close,candle15.volume)
    if orig!=expected:
        raise ValueError("C70_ORIGINAL_3M_TO_NATIVE15M_DECIMAL_PARITY_FAILED")
    if c69.source_status.startswith("RAID_"):
        if (c69.preknown_level_price is None or
            c69.preknown_level_known_ms is None or
            c69.source_event_fully_known_ms is None or
            c69.source_event_fully_known_ms<start+Q):
            raise ValueError("C70_RAID_LEVEL_UNKNOWN_OR_NOT_CONFIRMED_1H")
        level=Decimal(c69.preknown_level_price)
        if not level.is_finite() or level<=0:
            raise ValueError("C70_BAD_PREKNOWN_SOURCE_RAID_LEVEL")
        hit=next((z for z in five if (
            z.low<level if fork.original_4h_source_side=="LONG" else z.high>level)),None)
        if hit is None:return out(STATES[2],parity=True)
        wick=(hit.open>=level and hit.close>=level
            if fork.original_4h_source_side=="LONG"
            else hit.open<=level and hit.close<=level)
        # Cannot act on the 3m wick before confirming the original1H raid.
        eligible=max(hit.known_ms,c69.source_event_fully_known_ms)
        return out(STATES[4] if wick else STATES[3],hit,wick,eligible,True)
    f=fork.source_first_1h_event
    if (f is None or fork.first_source_1h_category!="NEW_1H_VC_POI"
        or f.zone_bottom is None or f.zone_top is None or
        c69.source_event_fully_known_ms!=f.fully_known_ms or
        start<f.fully_known_ms):
        raise ValueError("C70_FORGED_OR_NOT_FULLY_KNOWN_NEW1H_POI")
    bottom,top=Decimal(f.zone_bottom),Decimal(f.zone_top)
    if not (bottom.is_finite() and top.is_finite() and 0<bottom<top):
        raise ValueError("C70_INVALID_SOURCE_NEW1H_POI_BOUNDS")
    hit=next((z for z in five if z.low<=top and z.high>=bottom),None)
    if hit is None:return out(STATES[2],parity=True)
    return out(STATES[5],hit,None,max(hit.known_ms,f.fully_known_ms),True)
