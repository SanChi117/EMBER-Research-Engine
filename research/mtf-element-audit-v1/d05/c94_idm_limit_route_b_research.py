"""C94 independent Route B IDM limit-order PAPER replay, not Route A or C.

Owner Entry by Inducement: 4H VC/POI -> 1H IDM limit OR 1H new VC/POI
-> 15m IDM limit, WITHOUT a late 5m/15m VC trigger. SL behind protected
4H/1H StrongHL; TP earliest same-origin 4H FTA. No fixed RR target.

Adaptations explicitly inferred: 4H/1H IMB as POI, 1H/15m confirmed
fractal BSL/SSL as IDM, structural pivot width2, first official calendar
5m limit fill, 8h entry TTL, conservative same-bar stop-first.
All outcomes are hypotheses; NEVER send exchange orders.
"""
from collections import Counter
from bisect import bisect_left
from decimal import Decimal as D
from c89_original_native5m_adaptation_backtest import (
    Bar,STEP,SPLIT,SOURCES,MIN_RISK_PCT,MAX_RISK_PCT)
from c90_structural_fta_backtest import Swing,ATR_PAD,MIN_RR_FILTER,atr5m
from c91_continuous_causal_route_a_paper import (
    _aggregate,_fvg,_weekly_daily_context,H4,HOUR,D1,WEEK,WEEK_ANCHOR,_metrics)
import json
class C94Rejected(ValueError):pass
PIVOT=2
TTL=96                     # 8h limit validity; research assumption
HOLD=144                    # 12h max post fill
EVIDENCE="ADAPTED_HYPOTHESIS"
MODEL_B1="B_4H_IMB_POI_TO_1H_IDM_LIMIT"
MODEL_B2="B_1H_NEW_VC_TO_15M_IDM_LIMIT"

def _pivots(candles,tf):
    out=[]
    for k in range(PIVOT,len(candles)-PIVOT):
        s=candles[k];l=candles[k-PIVOT:k];r=candles[k+1:k+PIVOT+1]
        at=r[-1].close_ms
        if all(s.h>x.h for x in l) and all(s.h>=x.h for x in r):
            out.append(Swing(tf,"HIGH",s.h,s.close_ms,at,PIVOT))
        if all(s.l<x.l for x in l) and all(s.l<=x.l for x in r):
            out.append(Swing(tf,"LOW",s.l,s.close_ms,at,PIVOT))
    return tuple(out)

def _unswept(source,pivot,asof_ms,side):
    if pivot.confirmed_ms>asof_ms:return False
    # A preknown BSL/SSL level is invalid after any physical sweep.
    start=bisect_left([b.open_ms for b in source],pivot.confirmed_ms)
    end=bisect_left([b.open_ms for b in source],asof_ms)
    return not any((x.h>=pivot.price if side=="HIGH" else x.l<=pivot.price)
                   for x in source[start:end])

def _plan(source,signal_ms,side,zone,parent,liquidity_swings,structure_swings,
          fta_swings,model):
    """Limit entry level, SL and FTA all known BEFORE first eligible fill."""
    if side not in ("LONG","SHORT") or model not in (MODEL_B1,MODEL_B2):
        raise C94Rejected("B_SIDE_OR_MODEL")
    at=bisect_left([b.open_ms for b in source],signal_ms)
    if at>=len(source) or source[at].open_ms!=signal_ms or at<15:
        return None,"NO_CLOSED_LIMIT_SIGNAL"
    atr=atr5m(source[at-15:at])
    close=source[at-1].c
    idm_kind="LOW" if side=="LONG" else "HIGH"
    candidates=[]
    for s in liquidity_swings:
        if s.kind!=idm_kind or s.confirmed_ms>signal_ms:continue
        if not (zone[0]-atr<=s.price<=zone[1]+atr):continue
        if side=="LONG" and s.price>=close:continue
        if side=="SHORT" and s.price<=close:continue
        if not _unswept(source,s,signal_ms,idm_kind):continue
        candidates.append(s)
    if not candidates:return None,"NO_FRESH_FRACTAL_IDM_LIMIT"
    idm=max(candidates,key=lambda x:x.price) if side=="LONG" else min(candidates,key=lambda x:x.price)
    limit=idm.price
    # source-author SL is behind StrongHL; no ATR-based standalone stop.
    protected=[s for s in structure_swings if s.kind==idm_kind and
               s.confirmed_ms<=signal_ms and
               ((s.price<limit) if side=="LONG" else (s.price>limit))]
    if not protected:return None,"NO_CONFIRMED_PARENT_STRONGHL"
    p=max(protected,key=lambda s:s.confirmed_ms)
    anchor=min(p.price,zone[0]) if side=="LONG" else max(p.price,zone[1])
    stop=anchor-ATR_PAD*atr if side=="LONG" else anchor+ATR_PAD*atr
    opposite="HIGH" if side=="LONG" else "LOW"
    ftas=[s for s in fta_swings if s.kind==opposite and s.confirmed_ms<=signal_ms and
          ((s.price>limit) if side=="LONG" else (s.price<limit))
          and _unswept(source,s,signal_ms,opposite)]
    if not ftas:return None,"NO_PREKNOWN_4H_FTA"
    fta=min(ftas,key=lambda s:s.price) if side=="LONG" else max(ftas,key=lambda s:s.price)
    target=fta.price-ATR_PAD*atr if side=="LONG" else fta.price+ATR_PAD*atr
    if not ((stop<limit<target) if side=="LONG" else (target<limit<stop)):
        return None,"IDM_STOP_OR_FTA_WRONG_SIDE"
    risk=abs(limit-stop)
    if not MIN_RISK_PCT<=risk/limit<=MAX_RISK_PCT:
        return None,"IDM_STOP_CRYPTO_BOUNDS"
    rr=abs(target-limit)/risk
    if rr<MIN_RR_FILTER:return None,"IDM_DERIVED_RR_ONLY_FILTER"
    return {"signal_ms":signal_ms,"limit":limit,"stop":stop,"target":target,
        "fta":fta.price,"fta_confirmed_ms":fta.confirmed_ms,
        "stronghl":p.price,"stronghl_confirmed_ms":p.confirmed_ms,
        "idm_confirmed_ms":idm.confirmed_ms,
        "side":side,"route":model,"rr":round(float(rr),6),
        "parent":"4H_FTA","no_fixed_rr":True,"evidence":EVIDENCE}, "OK"

def _fill_limit(source,plan,cost_bps=14):
    """Never count unfilled limit as trade. Same-bar post-touch STOP wins."""
    if type(plan) is not dict or plan.get("evidence")!=EVIDENCE or cost_bps!=14:
        raise C94Rejected("FAKE_PLAN_OR_COST")
    idx=bisect_left([b.open_ms for b in source],plan["signal_ms"])
    side=plan["side"];limit=plan["limit"];stop=plan["stop"];target=plan["target"]
    if idx>=len(source) or source[idx].open_ms!=plan["signal_ms"]:
        raise C94Rejected("NO_NEXT_CANDLE")
    first=None
    for i in range(idx,min(idx+TTL,len(source))):
        b=source[i]
        if (side=="LONG" and b.o<=stop) or (side=="SHORT" and b.o>=stop):
            return None,"PREENTRY_STOP_GAP_CANCEL"
        if (b.l<=limit if side=="LONG" else b.h>=limit):
            first=i;break
    if first is None:return None,"IDM_LIMIT_NOT_FILLED_TTL"
    end=min(first+HOLD,len(source));exit_price=None;reason="";j=first
    for j in range(first,end):
        b=source[j]
        if side=="LONG":
            if j>first and b.o<=stop:exit_price=b.o;reason="STOP_GAP";break
            if j>first and b.o>=target:exit_price=target;reason="FTA_OPEN";break
            sl=b.l<=stop;tp=b.h>=target
        else:
            if j>first and b.o>=stop:exit_price=b.o;reason="STOP_GAP";break
            if j>first and b.o<=target:exit_price=target;reason="FTA_OPEN";break
            sl=b.h>=stop;tp=b.l<=target
        if sl:exit_price=stop;reason="STOP_FIRST_AFTER_LIMIT_TOUCH";break
        if j>first and tp:exit_price=target;reason="STRUCTURAL_4H_FTA";break
    if exit_price is None:exit_price=source[j].c;reason="TIME_LIMIT"
    risk=abs(limit-stop)
    net=((exit_price-limit) if side=="LONG" else (limit-exit_price))/risk
    net-=D(cost_bps)/D(10000)*limit/risk
    return {"route":plan["route"],"entry_ms":source[first].open_ms,
         "exit_ms":source[j].close_ms,"signal_ms":plan["signal_ms"],
         "side":side,"entry":str(limit),"stop":str(stop),
         "target":str(target),"fta":str(plan["fta"]),"fta_tf":"4h",
         "derived_rr":plan["rr"],"net_r":round(float(net),6),
         "exit_reason":reason,"limit_filled":True,"source_tf":"NATIVE_5M",
         "fta_confirmed_ms":plan["fta_confirmed_ms"],
         "stronghl_confirmed_ms":plan["stronghl_confirmed_ms"],
         "idm_confirmed_ms":plan["idm_confirmed_ms"],
         "evidence":EVIDENCE,"readiness":"PAPER_ONLY"}, "OK"

def discover(source,symbol):
    if symbol not in SOURCES or type(source) is not tuple or len(source)<1000 or any(
            type(b) is not Bar or
            (i and source[i-1].close_ms!=b.open_ms)
            for i,b in enumerate(source)):
        raise C94Rejected("BAD_FULL_NATIVE5M_SOURCE")
    hour=_aggregate(source,HOUR)
    four=_aggregate(source,H4)
    fifteen=_aggregate(source,3*STEP)
    days=_aggregate(source,D1)
    weeks=_aggregate(source,WEEK,WEEK_ANCHOR)
    s1=_pivots(hour,HOUR);s4=_pivots(four,H4);s15=_pivots(fifteen,3*STEP)
    events=[];count=Counter();reject=Counter()
    # Different Route B models are alternate distinct limit hypotheses.
    for k in range(2,len(four)):
        b=four[k];z=_fvg(four[k-2:k+1])
        if not z:continue
        side,low,high=z
        if not _weekly_daily_context(days,weeks,side,b.close_ms):
            reject["CONTEXT_W1_D1_NOT_ALIGNED"]+=1;continue
        count["4H_VC_POI_CREATED"]+=1
        # B1: once 4h VC/POI exists, 1h IDM limit needs no final raid/VC.
        plan,reason=_plan(source,b.close_ms,side,(low,high),H4,s1,s4,s4,MODEL_B1)
        if plan:events.append((plan,b.close_ms));count["B1_IDM_LIMIT_PLANNED"]+=1
        else:reject["B1_"+reason]+=1
        # B2: 4h POI is *tested*, 1h new VC IMB formed after first touch.
        left=bisect_left([r.open_ms for r in source],b.close_ms)
        end=min(left+12*48,len(source)-1)
        first=None
        for j in range(left,end):
            x=source[j]
            if (side=="LONG" and x.c<low) or (side=="SHORT" and x.c>high):break
            if x.h>=low and x.l<=high:
                first=x.close_ms;break
        if first is None:
            reject["B2_4H_FIRST_TEST_ABSENT"]+=1;continue
        for i in range(2,len(hour)):
            hb=hour[i]
            if hb.close_ms<=first:continue
            if hb.close_ms>first+8*HOUR:break
            q=_fvg(hour[i-2:i+1])
            if not q or q[0]!=side:continue
            _,child_low,child_high=q
            if child_low>=low and child_high<=high:
                reject["B2_NESTED_1H_IMB_INSIDE_4H_IMB"]+=1;break
            plan,reason=_plan(source,hb.close_ms,side,(child_low,child_high),
                   HOUR,s15,s1,s4,MODEL_B2)
            if plan:events.append((plan,hb.close_ms));count["B2_IDM_LIMIT_PLANNED"]+=1
            else:reject["B2_"+reason]+=1
            break
    events.sort(key=lambda x:(x[1],x[0]["route"]))
    out=[];busy_until=0;parent_activated=set()
    for plan,signal in events:
        t,why=_fill_limit(source,plan)
        if t is None:
            reject[why]+=1;continue
        if t["entry_ms"]<busy_until:
            reject["OVERLAPPING_B_TRADE"]+=1;continue
        out.append({"symbol":symbol,**t})
        busy_until=t["exit_ms"];count["B_IDM_LIMIT_FILLED_PAPER"]+=1
    return {"symbol":symbol,"native5m_bars":len(source),
       "states":dict(sorted(count.items())),"rejections":dict(sorted(reject.items())),
       "trades":out}

def analyze(markets,manifest):
    if set(markets)!=SOURCES or len(manifest) not in (15,40):
        raise C94Rejected("ONLY_ORIGINAL_MARKETS_ALLOWED")
    by={k:discover(v,k) for k,v in sorted(markets.items())}
    rows=sorted((x for d in by.values() for x in d["trades"]),
                key=lambda a:(a["entry_ms"],a["symbol"]))
    train=[x for x in rows if x["entry_ms"]<SPLIT and x["exit_ms"]<=SPLIT]
    late=[x for x in rows if x["entry_ms"]>=SPLIT]
    return {"schema":"C94_INDEPENDENT_ROUTE_B_IDM_5M_LIMIT_PAPER",
      "owner_rule":"4H VC ->1H IDM limit /1H new VC->15m IDM limit, protected StrongHL SL, 4H FTA",
      "route_status":"ADAPTED_HYPOTHESIS_IDM_NO_LTF_FINAL_VC",
      "original_archive_manifest":manifest,"original_bars":sum(len(v) for v in markets.values()),
      "all":_metrics(rows),"early":_metrics(train),"late_time_not_pristine_OOS":_metrics(late),
      "route_counts":dict(sorted(Counter(r["route"] for r in rows).items())),
      "by_symbol":by,"fixed_rr_target":False,"limit_fill_mandatory":True,
      "orders":[],"fills":[],"live_trades":[],"readiness":"PAPER_RESEARCH_NOT_TRADE_READY"}
def dumps(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf8")
