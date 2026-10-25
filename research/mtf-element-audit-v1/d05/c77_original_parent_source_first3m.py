"""C77 source-only review: original C62 1H RB/SNR/IMB vs C73 first 3m contact.
Course has priority: RB wick raid/IMB interaction; SNR confirmed; first POI
test precedes lower TF analysis. Geometry is NEVER author VC/Trigger/trade.
"""
from collections import Counter
from decimal import Decimal
from bisect import bisect_left
from c62_academic_snr_rb_imb_liquidity_source_separation import SourceBlockCase,PreknownGap
from c21_native3m_source_bridge import Original3mRow,THREE
class C77Rejected(ValueError):pass
KINDS={"1H_NEW_VC_RB_SOURCE":"RB","1H_NEW_VC_SNR_SOURCE":"SNR","1H_NEW_VC_IMB_SOURCE":"IMB"}
RB=("RB_WICK_ONLY_LIQUIDITY_SOURCE_PROXY","RB_WICK_ONLY_IMB_SOURCE_PROXY")
SNR=("SNR_ACCEPTED_CLOSE_WITH_SOURCE_LIQUIDITY_PROXY","SNR_ACCEPTED_CLOSE_WITH_SOURCE_IMB_PROXY")
def inspect(case,blocks,gaps,bars,asof):
    if not isinstance(case,dict) or type(blocks)!=tuple or type(gaps)!=tuple or type(bars)!=tuple or not bars:
        raise C77Rejected("BAD_SOURCE_INPUT")
    sym=case.get("symbol");side=case.get("side");kind=case.get("source_1h_poi_kind")
    if sym not in ("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT") or side not in ("LONG","SHORT"):
        raise C77Rejected("BAD_SYMBOL_SIDE")
    if case.get("readiness")!="NOT_TRADE_READY" or any(case.get(k)!=[] for k in ("orders","fills","trades")) or any(case.get(k)!=False for k in ("author_15m_trigger","author_15m_vc","author_5m_vc","author_entry","author_stronghl","author_structural_sl","author_1h_poi_valid_first_test","route_b_idm_used","route_c_raid_bos_used")):
        raise C77Rejected("FORGED_AUTHOR_OR_TRADE")
    if type(asof)!=int or any(type(x)!=Original3mRow or x.symbol!=sym or x.known_ms!=x.start_ms+THREE or x.known_ms>asof for x in bars) or any(b.start_ms!=a.start_ms+THREE for a,b in zip(bars,bars[1:])):
        raise C77Rejected("BAD_NATIVE3_SOURCE")
    if any(type(x)!=SourceBlockCase or x.author_classified_poi or x.author_volume_confirmation or x.author_stronghl or x.orders or x.trades for x in blocks) or any(type(x)!=PreknownGap or x.status!="TECHNICAL_ORIGINAL1H_CLASSIC_3CANDLE_WICK_GAP_NOT_AUTHOR_POI" for x in gaps):
        raise C77Rejected("FORGED_C62_SOURCE")
    if kind is None:
        if case.get("state")!="NOT_NEW_1H_POI_SOURCE_BRANCH":
            raise C77Rejected("MISSING_PARENT_WRONG_STATE")
        return "NO_PARENT","NO_SOURCE_NEW_POI",None,None,0
    if kind not in KINDS:raise C77Rejected("UNKNOWN_SOURCE_PARENT")
    t=case.get("source_1h_poi_created_at_ms")
    try:lo=Decimal(case["source_1h_poi_bottom"]);hi=Decimal(case["source_1h_poi_top"])
    except (ValueError,TypeError,KeyError) as ex:raise C77Rejected("BAD_PARENT_ZONE") from ex
    if type(t)!=int or t<=0 or t>asof or not lo.is_finite() or not hi.is_finite() or not 0<lo<hi:
        raise C77Rejected("BAD_PARENT_ZONE_OR_TIME")
    if kind=="1H_NEW_VC_IMB_SOURCE":
        match=[x for x in gaps if x.side==side and x.known_ms==t and Decimal(x.bottom)==lo and Decimal(x.top)==hi]
        status="SOURCE_1H_IMB_GAP_ONLY"
    else:
        types="RB" if KINDS[kind]=="RB" else "SNR_OR_MB"
        classes=RB if types=="RB" else SNR
        match=[x for x in blocks if x.side==side and x.type==types and x.fully_known_ms==t and x.source_class in classes]
        status="SOURCE_RB_WICK_WORK" if types=="RB" else "SOURCE_SNR_CONFIRMED_WORK"
    if len(match)!=1:raise C77Rejected("C62_SOURCE_PARENT_MATCH_"+str(len(match)))
    times=[x.start_ms for x in bars]
    i=bisect_left(times,t)
    if i>=len(bars) or bars[i].start_ms!=t:raise C77Rejected("UNALIGNED_PARENT_CREATION")
    overlap=lambda x:x.low<=hi and x.high>=lo
    first=next((j for j in range(i,len(bars)) if overlap(bars[j])),None)
    touch=case.get("original_first_source3m_touch_closed_ms")
    rawid=case.get("original_first_source3m_touch_id")
    if touch is None:
        if first is not None or rawid is not None or case.get("state")!="NEW_1H_POI_SOURCE_NO_ORIGINAL3M_FIRST_TOUCH":
            raise C77Rejected("MISSING_FIRST_TOUCH_WRONG")
        return KINDS[kind],status,None,None,len(bars)-i
    if type(touch)!=int or first is None or touch!=bars[first].known_ms or rawid!=bars[first].raw_id:
        raise C77Rejected("FIRST_ORIGINAL3M_SOURCE_DRIFT")
    pattern=case.get("first_source15m_event_pattern_start_ms")
    if pattern is None:
        if case.get("state")!="NEW_1H_POI_FIRST_ANY_RAW3M_TOUCH_NO_UNAMBIGUOUS_15M_CHAIN":
            raise C77Rejected("UNEXPECTED_MISSING_PATTERN")
        return KINDS[kind],status,rawid,None,len(bars)-i
    if type(pattern)!=int or pattern<=touch or pattern>asof:
        raise C77Rejected("INVALID_FUTURE_PATTERN")
    end=bisect_left(times,pattern);n=0;inside=False;repeat=None
    for bar in bars[first:end]:
        o=overlap(bar)
        if o and not inside:
            n+=1
            if n==2:repeat=bar.raw_id
        inside=o
    if n!=case.get("episodes_before_first_15m_pattern") or repeat!=case.get("second_visit_original3m_id"):
        raise C77Rejected("C73_VISIT_EPISODE_DRIFT")
    expected=("NEW_1H_POI_FIRST_15M_PATTERN_SINGLE_SOURCE_VISIT_NOT_OWNER_VALID" if n==1 else
              "NEW_1H_POI_FIRST_15M_PATTERN_REVISITED_SOURCE_POI_NOT_OWNER_VALID")
    if case.get("state")!=expected:raise C77Rejected("C73_SOURCE_STATE_DRIFT")
    return KINDS[kind],status,rawid,n,len(bars)-i

def summarize(rows):
    if type(rows)!=list or any(type(r)!=tuple or len(r)!=5 for r in rows):
        raise C77Rejected("BAD_SOURCE_SUMMARY")
    return {"contexts":len(rows),"types":dict(sorted(Counter(x[0] for x in rows).items())),
            "eligibility":dict(sorted(Counter(x[1] for x in rows).items())),
            "first_source_touches":sum(x[2] is not None for x in rows),
            "known_source_episodes":dict(sorted(Counter(str(x[3]) for x in rows).items())),
            "author_certified":0,"orders":0,"fills":0,"trades":0,"readiness":"NOT_TRADE_READY"}
