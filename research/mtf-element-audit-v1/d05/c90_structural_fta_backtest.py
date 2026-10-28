"""C90: STRUCTURAL FTA/StrongHL experimental replay. PAPER ONLY.

Replaces C89 fixed-RR TP completely. Owner course:
1H POI -> 15m VC -> target earliest 1H FTA; SL behind local StrongHL.
Missing semantics are explicit ADAPTED_HYPOTHESIS:
  - FTA: closest UNRAIDED confirmed 1H swing high/low in trade direction.
  - 15m StrongHL: nearest confirmed 15m pivot behind price and 1H POI edge.
  - Confirmation: left/right closed 2 or 3 bars (frozen candidate variants).
  - SL/FTA buffer 0.15*past native5m ATR, using only closed bars.
No fixed RR *ever* constructs TP. Structural RR is derived AFTER entry/SL/FTA,
with 1.25 minimum only an optional rejection criterion.
These P0 cases are preselected and therefore NOT strategy-wide unbiased OOS.
"""
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from bisect import bisect_left
import json
from c89_original_native5m_adaptation_backtest import (
 Bar,STEP,SPLIT,COST_BPS,HORIZON_BARS,MIN_RISK_PCT,MAX_RISK_PCT,
 C89Rejected,load_original_native5m,_decimal,SOURCES)
from c83_owner_course_text_crosswalk import source_matched_queue
from c86_original153_first_test_receipts import audit_stored_bytes
from c87_adapted_route_a_shadow_gate import audit_witness

class C90Rejected(ValueError):pass
STATUS="ADAPTED_HYPOTHESIS_SOURCE_CONDITIONED_PAPER_ONLY"
PIVOT_WIDTHS=(2,3)
MIN_RR_FILTER=Decimal("1.25")
ATR_PAD=Decimal("0.15")
ATR_BARS=14

@dataclass(frozen=True)
class ClosedBar:
    start_ms:int
    close_ms:int
    high:Decimal
    low:Decimal
    close:Decimal

@dataclass(frozen=True)
class Swing:
    tf_ms:int
    kind:str
    price:Decimal
    pivot_closed_ms:int
    confirmed_ms:int
    left_right:int

def closed_tfs(source,signal,tf_ms):
    """Build ONLY complete 1h/15m bars from contiguous original closed 5m."""
    if type(source) is not tuple or any(type(b) is not Bar for b in source):
        raise C90Rejected("EXACT_NATIVE5M_REQUIRED")
    if type(signal) is not int or signal%STEP or tf_ms not in (900000,3600000):
        raise C90Rejected("SIGNAL_OR_TIMEFRAME_INVALID")
    count=tf_ms//STEP
    if not source:return ()
    result=[]
    current=[]
    for b in source:
        if b.close_ms>signal:break
        if b.open_ms%tf_ms==0:
            current=[]
        if current or b.open_ms%tf_ms==0:
            if current and current[-1].close_ms!=b.open_ms:
                raise C90Rejected("SOURCE_GAP_OR_MIXED_TIMEFRAME")
            current.append(b)
            if len(current)==count:
                result.append(ClosedBar(current[0].open_ms,
                  current[-1].close_ms,max(v.h for v in current),
                  min(v.l for v in current),current[-1].c))
                current=[]
    return tuple(result)

def confirmed_swings(candles,tf_ms,width,asof_ms):
    if type(candles) is not tuple or tf_ms not in (900000,3600000) or type(width) is not int or width not in PIVOT_WIDTHS:
        raise C90Rejected("PIVOT_INPUT_INVALID")
    if type(asof_ms) is not int or asof_ms<0:
        raise C90Rejected("ASOF_TIME_INVALID")
    if any(type(x) is not ClosedBar or x.close_ms>asof_ms or x.close_ms-x.start_ms!=tf_ms for x in candles):
        raise C90Rejected("PARTIAL_OR_FUTURE_HTF_CANDLE")
    if any(b.start_ms!=a.close_ms for a,b in zip(candles,candles[1:])):
        raise C90Rejected("NONCONTIGUOUS_HTF_BARS")
    result=[]
    for i in range(width,len(candles)-width):
        cur=candles[i]
        left=candles[i-width:i];right=candles[i+1:i+width+1]
        conf=right[-1].close_ms
        if conf>asof_ms:raise C90Rejected("PIVOT_LOOKAHEAD")
        if all(cur.high>x.high for x in left) and all(cur.high>=x.high for x in right):
            result.append(Swing(tf_ms,"HIGH",cur.high,cur.close_ms,conf,width))
        if all(cur.low<x.low for x in left) and all(cur.low<=x.low for x in right):
            result.append(Swing(tf_ms,"LOW",cur.low,cur.close_ms,conf,width))
    return tuple(result)

def atr5m(past):
    if type(past) is not tuple or len(past)<ATR_BARS+1 or any(type(b) is not Bar for b in past):
        raise C90Rejected("ATR_PAST_ONLY_REQUIRED")
    seq=past[-(ATR_BARS+1):]
    if any(a.close_ms!=b.open_ms for a,b in zip(seq,seq[1:])):
        raise C90Rejected("ATR_SOURCE_GAP")
    tr=[max(b.h-b.l,abs(b.h-a.c),abs(b.l-a.c)) for a,b in zip(seq,seq[1:])]
    value=sum(tr)/Decimal(len(tr))
    if value<=0:raise C90Rejected("ZERO_ATR")
    return value

def structure_at_signal(source,event,*,width=2):
    """Stop behind 15m confirmed structural extremum/POI; target 1h FTA."""
    if type(source) is not tuple or not source or any(type(b) is not Bar for b in source):
        raise C90Rejected("NATIVE_DATA_REQUIRED")
    if type(event) is not dict or event.get("priority")!=0 or event.get("readiness")!="NOT_TRADE_READY":
        raise C90Rejected("SOURCE_P0_EVENT_REQUIRED")
    if width not in PIVOT_WIDTHS or type(width) is not int:
        raise C90Rejected("UNREGISTERED_ADAPTED_WIDTH")
    signal=event["first5m_known_ms"]
    if type(signal) is not int or signal%STEP:
        raise C90Rejected("SOURCE_5M_CLOSE_REQUIRED")
    opens=[b.open_ms for b in source]
    i=bisect_left(opens,signal)
    if i>=len(source) or source[i].open_ms!=signal:
        return {"status":"NO_NEXT_OPEN","case":event["case_key"]}
    if i<ATR_BARS+1:
        return {"status":"ATR_WARMUP_MISSING","case":event["case_key"]}
    if source[i-1].close_ms!=signal:
        raise C90Rejected("CLOSED5M_NOT_AT_SIGNAL")
    past=source[:i]       # no source[i] included in STRUCTURE!
    atr=atr5m(past)
    entry=source[i].o
    if entry<=0:raise C90Rejected("INVALID_ENTRY")
    side=event["side"]
    if side not in ("LONG","SHORT"):
        raise C90Rejected("INVALID_SIDE")
    try:
        lower=_decimal(event["poi_low"]);upper=_decimal(event["poi_high"])
    except C89Rejected as exc:
        raise C90Rejected("NONFINITE_OR_INVALID_SOURCE_POI") from exc
    if not 0<lower<upper:
        raise C90Rejected("INVALID_1H_POI")
    h1=closed_tfs(past,signal,3600000)
    m15=closed_tfs(past,signal,900000)
    s1=confirmed_swings(h1,3600000,width,signal)
    s15=confirmed_swings(m15,900000,width,signal)
    # FTA is the closest UNCONSUMED opposing liquidity high/low. A pivot
    # already swept by any CLOSED 5m bar before signal cannot act as fresh FTA.
    target_kind="HIGH" if side=="LONG" else "LOW"
    ftas=[]
    for s in s1:
        if s.kind!=target_kind or (side=="LONG" and s.price<=entry) or (side=="SHORT" and s.price>=entry):
            continue
        if any((b.h>=s.price if side=="LONG" else b.l<=s.price)
               for b in past if b.open_ms>=s.confirmed_ms):
            continue
        ftas.append(s)
    if not ftas:
        return {"case":event["case_key"],"status":"NO_UNCONSUMED_1H_FTA"}
    first=min(ftas,key=lambda s:s.price-entry) if side=="LONG" else max(ftas,key=lambda s:s.price-entry)
    fta=first.price
    target=fta-ATR_PAD*atr if side=="LONG" else fta+ATR_PAD*atr
    if (side=="LONG" and target<=entry) or (side=="SHORT" and target>=entry):
        return {"case":event["case_key"],"status":"FTA_ALREADY_TOO_CLOSE"}
    stopkind="LOW" if side=="LONG" else "HIGH"
    local=[s for s in s15 if s.kind==stopkind and
           (s.price<entry if side=="LONG" else s.price>entry)]
    if not local:
        return {"case":event["case_key"],"status":"NO_CONFIRMED_15M_STRONGHL_PROXY"}
    recent=max(local,key=lambda s:s.confirmed_ms)
    anchor=min(lower,recent.price) if side=="LONG" else max(upper,recent.price)
    stop=anchor-ATR_PAD*atr if side=="LONG" else anchor+ATR_PAD*atr
    risk=entry-stop if side=="LONG" else stop-entry
    if risk<=0:raise C90Rejected("STRUCTURE_STOP_WRONG_SIDE")
    risk_pct=risk/entry
    if risk_pct<MIN_RISK_PCT or risk_pct>MAX_RISK_PCT:
        return {"case":event["case_key"],"status":"STRUCTURAL_STOP_OUTSIDE_RISK_BOUNDS",
                "risk_pct":round(float(risk_pct)*100,6)}
    reward=target-entry if side=="LONG" else entry-target
    derived_rr=reward/risk
    # This gate NEVER changes target. The output contains actual structural RR.
    if derived_rr<MIN_RR_FILTER:
        return {"case":event["case_key"],"status":"STRUCTURAL_RR_BELOW_MIN_FILTER",
            "entry":str(entry),"stop":str(stop),"fta":str(fta),"target":str(target),
            "derived_rr":round(float(derived_rr),6),
            "fta_confirmed_ms":first.confirmed_ms,
            "stronghl_confirmed_ms":recent.confirmed_ms,
            "risk_pct":round(float(risk_pct)*100,6)}
    return {"case":event["case_key"],"status":"STRUCTURAL_PLAN_PAPER",
        "side":side,"entry":str(entry),"stop":str(stop),"fta":str(fta),
        "target":str(target),"fta_tf":"1h","stronghl_tf":"15m",
        "fta_pivot_closed_ms":first.pivot_closed_ms,
        "fta_confirmed_ms":first.confirmed_ms,
        "stronghl_pivot_closed_ms":recent.pivot_closed_ms,
        "stronghl_confirmed_ms":recent.confirmed_ms,
        "signal_ms":signal,"entry_open_ms":source[i].open_ms,
        "derived_rr":round(float(derived_rr),6),
        "risk_pct":round(float(risk_pct)*100,6),
        "atr_past_5m":str(atr),"evidence_class":"ADAPTED_HYPOTHESIS"}

def replay_plan(source,plan,*,cost_bps):
    if plan["status"]!="STRUCTURAL_PLAN_PAPER":
        raise C90Rejected("NO_ENTRY_FROM_REJECTED_PLAN")
    if cost_bps not in COST_BPS or type(cost_bps) is not int:
        raise C90Rejected("COST_MODEL_NOT_FROZEN")
    sig=plan["entry_open_ms"]
    i=next((j for j,b in enumerate(source) if b.open_ms==sig),None)
    if i is None:raise C90Rejected("SOURCE_ENTRY_NOT_FOUND")
    entry=_decimal(plan["entry"]);stop=_decimal(plan["stop"]);target=_decimal(plan["target"])
    side=plan["side"]
    if entry!=source[i].o or (side=="LONG" and not stop<entry<target) or (side=="SHORT" and not target<entry<stop):
        raise C90Rejected("NONSTRUCTURAL_OR_FORGED_EXECUTION_PLAN")
    exit_price=None;reason=None;end=min(i+HORIZON_BARS,len(source));j=None
    for j in range(i,end):
        b=source[j]
        if b.open_ms!=sig+(j-i)*STEP:
            raise C90Rejected("FORWARD_NATIVE5M_GAP")
        if side=="LONG":
            if b.o<=stop:exit_price=b.o;reason="GAP_THROUGH_STRUCTURAL_STOP";break
            if b.o>=target:exit_price=target;reason="FTA_AT_OPEN";break
            hit_sl=b.l<=stop;hit_tp=b.h>=target
        else:
            if b.o>=stop:exit_price=b.o;reason="GAP_THROUGH_STRUCTURAL_STOP";break
            if b.o<=target:exit_price=target;reason="FTA_AT_OPEN";break
            hit_sl=b.h>=stop;hit_tp=b.l<=target
        if hit_sl:exit_price=stop;reason="STRUCTURAL_STOP_PRIORITY_AMBIGUOUS";break
        if hit_tp:exit_price=target;reason="STRUCTURAL_FTA";break
    if exit_price is None:
        if j is None:raise C90Rejected("NO_FORWARD_BARS")
        exit_price=source[j].c;reason="CLOSED_12H_TIME_LIMIT"
    risk=abs(entry-stop)
    gross=(exit_price-entry if side=="LONG" else entry-exit_price)/risk
    net=gross-Decimal(cost_bps)/Decimal(10000)*entry/risk
    return {**plan,"exit":str(exit_price),"exit_close_ms":source[j].close_ms,
      "exit_reason":reason,"gross_r":round(float(gross),6),
      "net_r":round(float(net),6),
      "cost_roundtrip_bps":cost_bps,"status":"CLOSED_HYPOTHETICAL_PAPER"}

def _stats(xs):
    results=[r["net_r"] for r in xs]
    pos=sum(max(0,x) for x in results)
    neg=-sum(min(0,x) for x in results)
    return {"trades":len(xs),"net_total_r":round(sum(results),6),
        "mean_net_r":round(sum(results)/len(xs),6) if xs else None,
        "win_rate_pct":round(100*sum(x>0 for x in results)/len(xs),3) if xs else None,
        "profit_factor":round(pos/neg,5) if neg else None,
        "derived_rr_distribution":[r["derived_rr"] for r in xs]}

def diagnostic(c73,c72,c81,c86,c87,markets,manifest):
    audit_stored_bytes(c73,c72,c81,c86)
    audit_witness(c73,c72,c81,c86,c87)
    source=source_matched_queue(c73,c72,c81)
    if len(source)!=153 or set(markets)!=SOURCES or len(manifest)!=15:
        raise C90Rejected("PINNED_CRYPTO_SOURCE_UNIVERSE_REQUIRED")
    for sym,b in markets.items():
        if len(b)!=9216 or any(x.close_ms!=y.open_ms for x,y in zip(b,b[1:])):
            raise C90Rejected("CONTIGUOUS_32DAY_NATIVE5M_REQUIRED")
    q=[{"case_key":x.source_key,"priority":x.priority,"symbol":x.symbol,"side":x.side,
        "first5m_known_ms":x.first5m_known_ms,"poi_low":x.poi_low,"poi_high":x.poi_high,
        "readiness":x.readiness} for x in source if x.priority==0]
    if len(q)!=12:raise C90Rejected("P0_PRESELECTED_COUNT_CHANGED")
    cases={}
    for width in PIVOT_WIDTHS:
        plans=[structure_at_signal(markets[x["symbol"]],x,width=width) for x in q]
        if len(plans)!=12:raise C90Rejected("SOURCE_CASES_DROPPED")
        cases[f"confirmed_pivot_{width}"]={
            "all_plans":plans,
            "rejections":dict(sorted(Counter(p["status"] for p in plans if p["status"]!="STRUCTURAL_PLAN_PAPER").items())),
            "results":{}}
        for cost in COST_BPS:
            executed=[replay_plan(markets[p["case"].split("/")[0]],p,cost_bps=cost)
                      for p in plans if p["status"]=="STRUCTURAL_PLAN_PAPER"]
            early=[x for x in executed if x["entry_open_ms"]<SPLIT]
            late=[x for x in executed if x["entry_open_ms"]>=SPLIT]
            cases[f"confirmed_pivot_{width}"]["results"][f"roundtrip_{cost}bps"]={
                "early_preselected":_stats(early),
                "late_preselected_NOT_OOS":_stats(late),
                "all_preselected":_stats(executed),"hypothetical_trades":executed}
    return {"schema":"EMBER_C90_STRUCTURAL_FTA_FIRST_RESEARCH_BACKTEST",
        "supersedes":"C89_FIXED_RR_RESULTS_NOT_VALID_EMBER_STRATEGY_BACKTEST",
        "author_owner_rule":"1H POI -> 1H FTA; stop behind Strong High/Low",
        "adapted_first_trade_obstacle":"Closest unconsumed confirmed 1H high/low swing",
        "adapted_stop":"15m confirmed StrongHL proxy plus 1H POI edge and 0.15 ATR pad",
        "never_fixed_rr_to_construct_target":True,
        "derived_rr_is_filter_only":True,
        "minimum_rr_filter":"1.25",
        "source_153_contexts":153,"preselected_events":12,
        "verification":"15 pinned native5m ZIP + original C73/C72/C81/C86/C87",
        "market_archive_manifest":manifest,
        "selection_bias":"C73 preselected historical P0; NOT unbiased strategy-wide OOS",
        "models":cases,"orders":[],"fills":[],"live_trades":[],
        "readiness":"PAPER_RESEARCH_NOT_TRADE_READY"}

def dumps(x):
    return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf8")
