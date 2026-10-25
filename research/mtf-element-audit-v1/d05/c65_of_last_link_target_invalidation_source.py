"""C65 — source-only OF last structural link + HTF target invalidation audit.

Owner Order Flow.txt: OF link requires liquidity AND IMB work. Reversal
requires HTF target then either CLOSE beyond the LAST OF STRUCTURAL LINK
(BOS) OR an opposite POI formed on the SAME TF. Without actual owner
labeled links, liquidity or opposite POI these are ADAPTED PRICE SOURCE
witnesses only, NEVER author OF invalidation, StrongHL, entry or SL.

Source context: original preknown unswept strict 1H pivot, earlier 1H
liquidity-working C62 case, earlier IMB-working C62 case, original closed
previous 1D target. FIRST ANY subsequent invalidation mechanism, including
equal-time ties. Wicks don't invalidate an OF link. No future candle use.
"""
from dataclasses import dataclass
from decimal import Decimal
import re
from c16_c08_monthly_daily_htf_lineage import (
    DerivedClosedTF,NativeKline,TF_MS,DAY,SEPT_START)
from c62_academic_snr_rb_imb_liquidity_source_separation import (
    _validate,_preknown_unswept_levels_schedule,SourceBlockCase)
from c64_original3m_source_protected_extreme_invalidation import SourceProtectedExtremeAudit
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    SourceReactionEvent,KINDS)
HOUR=TF_MS["1h"]
WINDOW=48*HOUR
STATES=(
  "NO_C64_CONFIRMED_SOURCE_ANCHOR",
  "NO_EARLIER_SOURCE_LIQUIDITY_WORK",
  "NO_EARLIER_SOURCE_IMB_WORK",
  "NO_PREKNOWN_1H_LAST_LINK_PIVOT",
  "NO_PREKNOWN_OR_AHEAD_1D_TARGET",
  "SOURCE_OF_PREREQUISITES_NOT_AUTHOR_CERTIFIED",
  "SOURCE_TARGET_NOT_REACHED_WITHIN_WINDOW",
  "SOURCE_TARGET_REACHED_NO_INVALIDATION_FULL_WINDOW",
  "SOURCE_TARGET_REACHED_NO_INVALIDATION_RIGHT_CENSORED",
  "SOURCE_FIRST_INVALIDATION_LINK_CLOSE_PROXY",
  "SOURCE_FIRST_INVALIDATION_OPPOSITE_POI_PROXY",
  "SOURCE_SIMULTANEOUS_TWO_INVALIDATION_PROXIES")
@dataclass(frozen=True)
class SourceOFLifecycle:
    symbol:str
    original_parent_side:str
    source_reaction_side:str|None
    source_reaction_known_ms:int|None
    state:str
    prior_liquidity_source_case_known_ms:int|None
    prior_imb_source_case_known_ms:int|None
    source_last_strict_fractal_pivot_known_ms:int|None
    source_last_link_price:str|None
    source_original1d_htf_target_known_ms:int|None
    source_original1d_htf_target_price:str|None
    source_htf_target_first_wick_reached_ms:int|None
    source_first_any_invalidation_known_ms:int|None
    source_first_any_invalidation_kind:str|None
    close_beyond_last_link_first_original15m_id:str|None
    opposite_source_poi_first_original15m_id:str|None
    source_window_end_ms:int|None
    full_source_48h_window:bool
    author_last_of_link_verified:bool=False
    author_htf_target_verified:bool=False
    author_opposite_poi_verified:bool=False
    author_of_invalidation_verified:bool=False
    author_stronghl_verified:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _out(anchor,state,*,liq=None,imb=None,pivot=None,price=None,day=None,
         target=None,hit=None,first=None,kind=None,bos=None,poi=None,end=None,
         full=False):
    return SourceOFLifecycle(anchor.symbol,anchor.original_4h_parent_side,
        anchor.event_side,anchor.source_event_known_ms,state,
        liq,imb,pivot,str(price) if price is not None else None,
        day,str(target) if target is not None else None,
        hit,first,kind,bos,poi,end,full)

def _original_daily(days,symbol,asof):
    if not isinstance(days,tuple):raise ValueError("C65_UNTRUSTED_DAILY_SOURCE")
    last=None
    for z in days:
        if (not isinstance(z,NativeKline) or z.tf!="1d" or z.symbol!=symbol or
            z.known_at_ms!=z.start_ms+DAY or z.start_ms%DAY or
            (last is not None and z.start_ms!=last)
            or z.known_at_ms>asof or
            not isinstance(z.origin_raw_row_id,str) or
            z.origin_raw_row_id!=z.origin_zip_sha256+":"+str(z.start_ms) or
            not isinstance(z.origin_zip_sha256,str) or
            not re.fullmatch(r"[0-9a-f]{64}",z.origin_zip_sha256)
            or not all(isinstance(v,Decimal) and v.is_finite()
              for v in (z.open,z.high,z.low,z.close,z.volume))
            or not (0<z.low<=min(z.open,z.close)<=max(z.open,z.close)<=z.high
                    and z.volume>=0)):
            raise ValueError("C65_FORGED_OR_FUTURE_NATIVE_1D")
        last=z.known_at_ms
    return days

def _source_work(blocks,symbol,first_contact,known,side,bars):
    if not isinstance(blocks,tuple):raise ValueError("C65_UNTRUSTED_C62_BLOCKS")
    liquidity=[];imb=[]
    row_by_start={x.start_ms:x for x in bars}
    for x in blocks:
        if (not isinstance(x,SourceBlockCase) or
            x.type not in ("RB","SNR_OR_MB") or x.side not in ("LONG","SHORT") or
            x.author_classified_poi or x.author_volume_confirmation or
            x.author_stronghl or x.orders or x.trades or
            x.fully_known_ms<=x.pair_first_known_ms or
            x.pair_first_known_ms<SEPT_START or
            x.fully_known_ms%HOUR):
            raise ValueError("C65_C62_BLOCK_FORGED_AUTHOR_OR_TIME")
        if x.fully_known_ms>known:continue
        if x.side!=side:continue
        if x.pair_first_known_ms-HOUR<max(first_contact,known-WINDOW):continue
        first=x.pair_first_known_ms-HOUR
        if (first not in row_by_start or first+HOUR not in row_by_start or
            x.pair_first_native15m_id!=row_by_start[first].source_native_15m_rows[0] or
            x.pair_second_native15m_id!=row_by_start[first+HOUR].source_native_15m_rows[0] or
            (x.type=="SNR_OR_MB" and (first+2*HOUR not in row_by_start or
             x.confirmation_first_native15m_id!=row_by_start[first+2*HOUR].source_native_15m_rows[0]))):
            raise ValueError("C65_C62_ORIGINAL_BLOCK_ID_MISMATCH")
        if x.source_liquidity_reference is not None and x.source_class in (
            "RB_WICK_ONLY_LIQUIDITY_SOURCE_PROXY",
            "SNR_ACCEPTED_CLOSE_WITH_SOURCE_LIQUIDITY_PROXY"):
            liquidity.append(x.fully_known_ms)
        if x.preknown_imb_reference_ms is not None and x.source_class in (
            "RB_WICK_ONLY_IMB_SOURCE_PROXY",
            "SNR_ACCEPTED_CLOSE_WITH_SOURCE_IMB_PROXY"):
            if x.preknown_imb_reference_ms>x.pair_first_known_ms-HOUR:
                raise ValueError("C65_FUTURE_IMB_WORK")
            imb.append(x.fully_known_ms)
    return (max(liquidity,default=None),max(imb,default=None))

def source_of_last_link_target_invalidation(anchor,hours,days,blocks,events,*,as_of_ms):
    if (not isinstance(anchor,SourceProtectedExtremeAudit) or
        anchor.author_labeled_stronghl or anchor.author_labeled_OF_invalidation or
        anchor.author_labeled_stop_loss or anchor.author_selected_poi or
        anchor.orders or anchor.fills or anchor.trades or
        anchor.readiness!="NOT_TRADE_READY"):
        raise ValueError("C65_UNTRUSTED_C64_SOURCE_ANCHOR")
    bars=_validate(hours,as_of_ms)
    if bars[-1].known_at_ms!=as_of_ms or bars[0].symbol!=anchor.symbol:
        raise ValueError("C65_PHYSICAL_CLOSED_1H_SOURCE_REQUIRED")
    dates=_original_daily(days,anchor.symbol,as_of_ms)
    if anchor.source_status!="SOURCE_ANCHOR_KNOWN_AT_REACTION_CLOSE":
        return _out(anchor,STATES[0])
    known=anchor.source_event_known_ms
    if (type(known) is not int or known%HOUR or known>as_of_ms or
        anchor.source_extreme_frozen_at_ms!=known or
        anchor.source_preactivation_breach_first3m_id is not None or
        anchor.event_side not in ("LONG","SHORT") or
        anchor.first_contact_native3m_id is None or
        anchor.source_candidate_direction_extreme is None):
        raise ValueError("C65_C64_PREACTIVATION_OR_FUTURE_FRAUD")
    contact=int(anchor.first_contact_native3m_id.split(":")[-1])+TF_MS["15m"]//5
    if contact>=known:raise ValueError("C65_ANCHOR_PREDATES_CONTACT")
    liq,imb=_source_work(blocks,anchor.symbol,contact,known,anchor.event_side,bars)
    if liq is None:return _out(anchor,STATES[1])
    if imb is None:return _out(anchor,STATES[2],liq=liq)
    # Pivot is independently selected from source structure. Do NOT
    # use C64 "protected source extreme" as the OF last link!
    i=next((i for i,x in enumerate(bars) if x.known_at_ms==known),None)
    if i is None:raise ValueError("C65_NO_ORIGINAL_REACTION_1H")
    schedule=_preknown_unswept_levels_schedule(bars[:i+1])
    wanted="SSL" if anchor.event_side=="LONG" else "BSL"
    pivots=[x for x in schedule[i] if x[0]==wanted]
    if not pivots:return _out(anchor,STATES[3],liq=liq,imb=imb)
    typ,pivot,pk=max(pivots,key=lambda x:x[2])
    # Pivot cannot be preknown, unbreached until the event bar and then
    # secretly breached during that very confirmation candle.
    if (bars[i].low<pivot if anchor.event_side=="LONG" else bars[i].high>pivot):
        return _out(anchor,STATES[3],liq=liq,imb=imb)
    earlier=[x for x in dates if x.known_at_ms<=known]
    if not earlier:return _out(anchor,STATES[4],liq=liq,imb=imb,pivot=pk,price=pivot)
    d=earlier[-1]
    target=d.high if anchor.event_side=="LONG" else d.low
    at=bars[i].close
    if ((anchor.event_side=="LONG" and target<=at) or
        (anchor.event_side=="SHORT" and target>=at)):
        return _out(anchor,STATES[4],liq=liq,imb=imb,pivot=pk,price=pivot,
                    day=d.known_at_ms,target=target)
    if not isinstance(events,tuple):raise ValueError("C65_UNTRUSTED_OPPOSITE_SOURCE_EVENTS")
    hour_map={h.start_ms:h for h in bars}
    for e in events:
        duration=(HOUR if getattr(e,"kind",None)=="BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE" else
                  2*HOUR if getattr(e,"kind",None)=="RB_1H_SOURCE" else 3*HOUR)
        if (not isinstance(e,SourceReactionEvent) or e.kind not in KINDS or
            e.side not in ("LONG","SHORT") or
            e.is_author_vc or e.is_author_bos or e.is_author_stronghl or
            e.orders or e.trades or
            e.first_pattern_bar_start_ms>=e.fully_known_ms or
            e.fully_known_ms-e.first_pattern_bar_start_ms!=duration or
            e.first_pattern_bar_start_ms not in hour_map or
            e.raw_first_original15m_id!=hour_map[e.first_pattern_bar_start_ms].source_native_15m_rows[0] or
            e.fully_known_ms>as_of_ms or e.fully_known_ms%HOUR):
            raise ValueError("C65_FORGED_OR_FUTURE_C63_EVENTS")
    full=as_of_ms>=known+WINDOW
    end=min(as_of_ms,known+WINDOW)
    post=[x for x in bars if x.start_ms>=known and x.known_at_ms<=end]
    hit=next((x for x in post if (
        x.high>=target if anchor.event_side=="LONG" else x.low<=target)),None)
    base=dict(liq=liq,imb=imb,pivot=pk,price=pivot,
              day=d.known_at_ms,target=target,end=end,full=full)
    if hit is None:
        return _out(anchor,STATES[6],**base)
    # Invalidation happens only AFTER target reach; source direction
    # may CONTINUE, so no "automatic reversal on target touch".
    finish=[]
    for x in post:
        if x.start_ms<hit.known_at_ms:continue
        closed=(x.close<pivot if anchor.event_side=="LONG" else x.close>pivot)
        if closed:
            finish.append((x.known_at_ms,"SOURCE_CLOSE_BEYOND_LAST_PIVOT_PROXY",
                           x.source_native_15m_rows[0]))
    for ev in events:
        if (ev.side==anchor.event_side or
            ev.first_pattern_bar_start_ms<hit.known_at_ms or
            ev.fully_known_ms>end or
            ev.kind not in ("SNR_1H_SOURCE","RB_1H_SOURCE","CLASSIC_1H_IMB_SOURCE")):
            continue
        finish.append((ev.fully_known_ms,"OPPOSITE_SOURCE_POI_PROXY",ev.raw_first_original15m_id))
    if not finish:
        return _out(anchor,STATES[7] if full else STATES[8],
                    hit=hit.known_at_ms,**base)
    first=min(x[0] for x in finish)
    found=[x for x in finish if x[0]==first]
    kinds={x[1] for x in found}
    kind="BOTH_SOURCE_PROXIES" if len(kinds)>1 else next(iter(kinds))
    status=(STATES[11] if len(kinds)>1 else
            STATES[9] if kind=="SOURCE_CLOSE_BEYOND_LAST_PIVOT_PROXY" else STATES[10])
    return _out(anchor,status,hit=hit.known_at_ms,first=first,kind=kind,
                bos=next((x[2] for x in found if x[1]=="SOURCE_CLOSE_BEYOND_LAST_PIVOT_PROXY"),None),
                poi=next((x[2] for x in found if x[1]=="OPPOSITE_SOURCE_POI_PROXY"),None),
                **base)
