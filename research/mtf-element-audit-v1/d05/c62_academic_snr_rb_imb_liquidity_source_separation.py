"""C62 original crypto SOURCE observations: strict academic SNR vs RB vs IMB.

Owner original lessons: 5. Support And Resistance .txt and
3. Rejection Block.txt plus Fair Value Gap Imbalance.txt.
Source-only mechanical adaptations (NOT author-labelled):
 SNR  = opposite two candles plus third full close past pair extreme;
        SNR with liquidity OR preknown IMB test; without either -> weaker
        MITIGATION_BLOCK_PROXY, NOT owner Volume Confirmation.
 RB   = opposite two candles with wick-only raid of PREKNOWN unswept
        1H BSL/SSL OR wick-only preknown IMB test with body acceptance;
        wick-based marking; body raid is NOT RB wick raid.
 IMB  = 3-candle wick gap confirmed only after THIRD bar closed.
 PREKNOWN 1H swing is strict three-bar fractal, not Strong High/Low.
No author market-screenshot goldens. No signal, orders, SL/TP, PnL.
"""
from dataclasses import dataclass
from decimal import Decimal
from c16_c08_monthly_daily_htf_lineage import DerivedClosedTF,TF_MS,SEPT_START
from c59_academic_stronghl_first_test_semantic_gate import _num

HOUR=TF_MS["1h"]
@dataclass(frozen=True)
class PreknownGap:
    side:str
    bottom:str
    top:str
    known_ms:int
    three_first_native15m_ids:tuple[str,str,str]
    status:str="TECHNICAL_ORIGINAL1H_CLASSIC_3CANDLE_WICK_GAP_NOT_AUTHOR_POI"

@dataclass(frozen=True)
class SourceBlockCase:
    type:str
    side:str
    pair_first_known_ms:int
    fully_known_ms:int
    pair_first_native15m_id:str
    pair_second_native15m_id:str
    confirmation_first_native15m_id:str|None
    source_liquidity_reference:str|None
    preknown_imb_reference_ms:int|None
    liquidity_or_imb_condition:str
    source_class:str
    author_classified_poi:bool=False
    author_volume_confirmation:bool=False
    author_stronghl:bool=False
    orders:tuple=()
    trades:tuple=()

def _validate(hours,as_of_ms):
    if not isinstance(hours,tuple) or not hours or type(as_of_ms) is not int or as_of_ms%HOUR:
        raise ValueError("C62_UNTRUSTED_1H_SOURCE_PREFIX")
    if as_of_ms<SEPT_START or as_of_ms>hours[-1].known_at_ms:
        raise ValueError("C62_INVALID_ASOF_OUTSIDE_ORIGINAL_SOURCE")
    last=None
    for h in hours:
        if (not isinstance(h,DerivedClosedTF) or h.tf!="1h"
            or h.known_at_ms!=h.start_ms+HOUR
            or (last is not None and h.start_ms!=last)
            or h.start_ms%HOUR or h.symbol!=hours[0].symbol
            or h.author_status!="ACADEMIC_HTF_POI_NOT_CERTIFIED"
            or len(h.source_native_15m_rows)!=4
            or not all(isinstance(v,Decimal) and v.is_finite() for v in
                       (h.open,h.high,h.low,h.close,h.volume))
            or not (0<h.low<=min(h.open,h.close)<=max(h.open,h.close)<=h.high and h.volume>=0)
            or any(not isinstance(s,str) or ":" not in s for s in h.source_native_15m_rows)):
            raise ValueError("C62_FORGED_OR_UNCLOSED_1H_SOURCE")
        last=h.known_at_ms
    return tuple(h for h in hours if h.known_at_ms<=as_of_ms)

def _gaps(hours):
    result=[]
    for i in range(2,len(hours)):
        a,_,z=hours[i-2:i+1]
        if a.high<z.low:side="LONG";lower=a.high;upper=z.low
        elif z.high<a.low:side="SHORT";lower=z.high;upper=a.low
        else:continue
        result.append(PreknownGap(side,str(lower),str(upper),z.known_at_ms,
           (a.source_native_15m_rows[0],
            hours[i-1].source_native_15m_rows[0],
            z.source_native_15m_rows[0])))
    return tuple(result)

def _known_levels(hours,first_start):
    """Only already-confirmed 1H fractals, unswept until pair start."""
    levels=[]
    for j in range(1,len(hours)-1):
        a,p,z=hours[j-1:j+2]
        if z.known_at_ms>first_start:break
        if p.high>a.high and p.high>z.high:
            if all(t.high<=p.high for t in hours[j+2:] if t.known_at_ms<=first_start):
                levels.append(("BSL",p.high,z.known_at_ms))
        if p.low<a.low and p.low<z.low:
            if all(t.low>=p.low for t in hours[j+2:] if t.known_at_ms<=first_start):
                levels.append(("SSL",p.low,z.known_at_ms))
    return tuple(levels)

def _work(side,pair,knownlevels,knownGaps,*,wick_only):
    """Return SOURCE witness only; NOT academic author liquidity/IMB."""
    for cand in pair:
        for kind,level,known in reversed(knownlevels):
            if side=="LONG" and kind=="SSL" and cand.low<level:
                if not wick_only or (cand.open>=level and cand.close>=level):
                    return "PREKNOWN_1H_SSL_STRICT_PIVOT","LIQUIDITY_SOURCE_PROXY"
            if side=="SHORT" and kind=="BSL" and cand.high>level:
                if not wick_only or (cand.open<=level and cand.close<=level):
                    return "PREKNOWN_1H_BSL_STRICT_PIVOT","LIQUIDITY_SOURCE_PROXY"
    for gap in reversed(knownGaps):
        if gap.side!=side or gap.known_ms>pair[0].start_ms:continue
        a,b=_num(gap.bottom),_num(gap.top)
        for cand in pair:
            if not (cand.high>=a and cand.low<=b):continue
            if not wick_only:
                return str(gap.known_ms),"CLASSIC_1H_IMB_SOURCE_PROXY"
            if side=="LONG" and cand.open>=b and cand.close>=b and pair[-1].close>b:
                return str(gap.known_ms),"WICK_ONLY_PREKNOWN_IMB_TEST_PROXY"
            if side=="SHORT" and cand.open<=a and cand.close<=a and pair[-1].close<a:
                return str(gap.known_ms),"WICK_ONLY_PREKNOWN_IMB_TEST_PROXY"
    return None,"NO_PREKNOWN_SOURCE_LIQUIDITY_OR_IMB_WORK"

def _side(a,b):
    if a.close<a.open and b.close>b.open:return "LONG"
    if a.close>a.open and b.close<b.open:return "SHORT"
    return None

def observe_hourly_source_poi_split(hours,*,as_of_ms):
    bars=_validate(hours,as_of_ms)
    gaps=_gaps(bars)
    cases=[]
    for i in range(1,len(bars)):
        first,second=bars[i-1:i+1]
        direction=_side(first,second)
        if direction is None:continue
        levels=_known_levels(bars,first.start_ms)
        preknown=tuple(z for z in gaps if z.known_ms<=first.start_ms)
        ref,source=_work(direction,(first,second),levels,preknown,wick_only=True)
        if source=="LIQUIDITY_SOURCE_PROXY":status="RB_WICK_ONLY_LIQUIDITY_SOURCE_PROXY"
        elif source=="WICK_ONLY_PREKNOWN_IMB_TEST_PROXY":status="RB_WICK_ONLY_IMB_SOURCE_PROXY"
        else:status="RB_TWO_OPPOSITE_HOURLY_CANDLES_WITHOUT_VERIFIED_WICK_RAID"
        cases.append(SourceBlockCase(
            "RB",direction,first.known_at_ms,second.known_at_ms,
            first.source_native_15m_rows[0],second.source_native_15m_rows[0],None,
            ref if source=="LIQUIDITY_SOURCE_PROXY" else None,
            int(ref) if source=="WICK_ONLY_PREKNOWN_IMB_TEST_PROXY" else None,
            source,status))
        if i+1==len(bars):continue
        confirm=bars[i+1]
        if direction=="LONG" and not (confirm.close>confirm.open and confirm.close>max(first.high,second.high)):continue
        if direction=="SHORT" and not (confirm.close<confirm.open and confirm.close<min(first.low,second.low)):continue
        snrref,snrsource=_work(direction,(first,second),levels,preknown,wick_only=False)
        if snrsource=="LIQUIDITY_SOURCE_PROXY":snr="SNR_ACCEPTED_CLOSE_WITH_SOURCE_LIQUIDITY_PROXY"
        elif snrsource=="CLASSIC_1H_IMB_SOURCE_PROXY":snr="SNR_ACCEPTED_CLOSE_WITH_SOURCE_IMB_PROXY"
        else:snr="MB_WEAKER_SOURCE_ONLY_NO_RAID_OR_IMB_NOT_VOLUME_CONFIRMATION"
        cases.append(SourceBlockCase(
          "SNR_OR_MB",direction,first.known_at_ms,confirm.known_at_ms,
          first.source_native_15m_rows[0],second.source_native_15m_rows[0],
          confirm.source_native_15m_rows[0],
          snrref if snrsource=="LIQUIDITY_SOURCE_PROXY" else None,
          int(snrref) if snrsource=="CLASSIC_1H_IMB_SOURCE_PROXY" else None,
          snrsource,snr))
    assert all(not(x.author_classified_poi or x.author_volume_confirmation
        or x.author_stronghl or x.orders or x.trades) for x in cases)
    return {"symbol":bars[0].symbol,
      "as_of_ms":as_of_ms,"closed_1h_bars":len(bars),
      "technical_original_1h_imb_gaps":gaps,
      "technical_1h_snr_rb_separate_cases":tuple(cases),
      "author_goldens":0,"orders":0,"trades":0,"readiness":"NOT_TRADE_READY"}
