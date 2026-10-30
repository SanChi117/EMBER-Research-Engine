#!/usr/bin/env python3
"""C109 independent core PAPER hypothesis vs faithful C105 baseline across new 64d.
New necessary formation only: closed H1 FVG-exit reclaim + preconfirmed 15m pivot
close-cross OR closed 15m IMB. Hard 4H source SL + TP unchanged. No live orders.
"""
import argparse
import hashlib
import json
from bisect import bisect_right
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
from pathlib import Path

import c104_native3m_source as rawprovider
import c105_parent4h_structural_geometry as p4
import c105_parent4h_native3m_research as c105
import c93_native3m_raid_bos_route_c_research as oldpivots
from c91_continuous_causal_route_a_paper import _fvg,WEEK_ANCHOR

class C109Error(ValueError):pass
LABEL="C109_SINGLE_CORE_UNCHANGED_4H_PARENT_EXIT_VS_C105_SOURCE_BASELINE"
SYMBOLS=("BNBUSDT","XLMUSDT","HBARUSDT","INJUSDT","OPUSDT","ALGOUSDT",
         "CHZUSDT","ICPUSDT","SEIUSDT","PENDLEUSDT","LINKUSDT","UNIUSDT")
BEGIN=datetime(2026,5,1,tzinfo=timezone.utc)
END=datetime(2026,7,4,tzinfo=timezone.utc)
BEGIN_MS=int(BEGIN.timestamp()*1000)
END_MS=int(END.timestamp()*1000)
DAY_MS=86400000
DAYS=tuple((BEGIN+timedelta(days=i)).strftime("%Y-%m-%d") for i in range((END-BEGIN).days))
WARMUP_END=BEGIN_MS+7*DAY_MS
LAST_ENTRY=END_MS-48*p4.H
FOLD_MS=int(datetime(2026,6,2,tzinfo=timezone.utc).timestamp()*1000)
ZIPS=len(SYMBOLS)*len(DAYS)
BARS_PER_SYMBOL=len(DAYS)*480
ORIGINAL_SHA={
 "c105_parent4h_structural_geometry.py":"b86623b8a7bb8f2580c129e70edbc0dfcf0f68bafc90f94e726d999f0e5db7ac",
 "c105_parent4h_native3m_research.py":"f04b58b998bc1a4bbc531202f241eb476395457765c68189eabf0344f5bd370f",
 "c104_native3m_source.py":"c23598b95616af96c45741eeca140b30fd0c2aa6f2053c33e4ee5ecdd80322eb",
}
ARM_BASE="B0_ORIGINAL_4H_FVG_H1_MIDPOINT_15M_WEAK_VC"
ARM_CORE="B1_4H_FVG_H1_FULL_RECLAIM_15M_CONFIRMED_SWING_OR_IMB"
ARMS=(ARM_BASE,ARM_CORE)
BARS_MODEL_4H_ONLY=True
LIFECYCLE="CLOSED_4H_ZONE_INVALIDATION_SEPARATE_FROM_INTRABAR_PROTECTIVE_4H_SL"

def frozen():
    here=Path(__file__).resolve().parent
    for name,expected in ORIGINAL_SHA.items():
        if hashlib.sha256((here/name).read_bytes()).hexdigest()!=expected:
            raise C109Error("MUTATED_ORIGINAL_4H_ENGINE_"+name)
    c105.frozen_source_checks()
    if len(SYMBOLS)!=12 or len(set(SYMBOLS))!=12 or len(DAYS)!=64:
        raise C109Error("CHANGED_PRECOMMITTED_UNIVERSE")
    if ZIPS!=768 or BARS_PER_SYMBOL!=30720:
        raise C109Error("CHANGED_SOURCE_SIZE")
    return True

def provider_3m(*,fetch=None):
    """Reuses exactly the immutable strict SHA source parser, temporarily scopes
    symbols & days. Restore BOTH if exception, no hidden database or fallback.
    """
    frozen()
    oldsymbols=rawprovider.SYMBOLS;olddays=rawprovider.DAYS
    work=[(s,d) for s in SYMBOLS for d in DAYS]
    try:
        rawprovider.SYMBOLS=SYMBOLS
        rawprovider.DAYS=DAYS
        def task(item):
            s,d=item
            rows,receipt=(rawprovider.daily(s,d) if fetch is None else
                          rawprovider.daily(s,d,fetch=fetch))
            return item,rows,receipt
        with ThreadPoolExecutor(max_workers=12) as pool:
            fetched=list(pool.map(task,work))
    finally:
        rawprovider.SYMBOLS=oldsymbols
        rawprovider.DAYS=olddays
    if len(fetched)!=ZIPS:raise C109Error("SOURCE_ZIP_768_INCOMPLETE")
    all_source={s:[] for s in SYMBOLS};manifest=[]
    for (symbol,day),rows,receipt in fetched:
        if (len(rows)!=480 or receipt["symbol"]!=symbol or
            receipt["date"]!=day or receipt["bars"]!=480 or
            rows[0].symbol!=symbol):
            raise C109Error("INVALID_PROVIDER_DAILY_SOURCE")
        v=all_source[symbol]
        if v and v[-1].known_ms!=rows[0].start_ms:
            raise C109Error("MISSING_NATIVE3M_DAY")
        v.extend(rows);manifest.append(receipt)
    if len({(p["symbol"],p["date"]) for p in manifest})!=ZIPS:
        raise C109Error("DUPLICATE_DAILY_SOURCE")
    for s,v in all_source.items():
        if len(v)!=BARS_PER_SYMBOL or v[0].start_ms!=BEGIN_MS or v[-1].known_ms!=END_MS:
            raise C109Error("BAD_SOURCE_CLOCK_"+s)
    return {k:tuple(v) for k,v in all_source.items()},manifest

def full_reclaim(zone,hour):
    """The real reason to enter: H1 candle closed entirely back OUTSIDE
    the parent gap near edge, rather than merely above/below gap midpoint.
    This is a research definition, NOT a guarantee of a meaningful reversal.
    """
    if zone.state!="WAIT_1H_REJECTION" or hour.close_ms<=zone.first_touch_ms:
        return False
    if hour.h<zone.lower or hour.l>zone.upper:return False
    if zone.side=="LONG":return hour.c>zone.upper and hour.c>hour.o
    return hour.c<zone.lower and hour.c<hour.o

def new_signal_type(side,known15,last_four,swings15):
    """Return 15m IMB or a close break through *preconfirmed* 15m swing.
    No single prior-15m-candle high/low is renamed a BOS or SNR.
    Both 15m entry signal and swing pivot must be causally available.
    """
    if side not in ("LONG","SHORT") or len(last_four)!=4:
        return None
    a,b,old,cur=last_four
    if not (a.close_ms==b.start_ms and b.close_ms==old.start_ms and
            old.close_ms==cur.start_ms):
        raise C109Error("NONCONSECUTIVE_COMPLETED_15M")
    if _fvg(last_four[-3:]) and _fvg(last_four[-3:])[0]==side:
        return ("IMB",None)
    want="HIGH" if side=="LONG" else "LOW"
    for swing in reversed(swings15):
        if (swing.kind!=want or swing.tf_ms!=p4.M15 or
            swing.confirmed_ms>cur.start_ms):
            continue
        crossing=(old.c<=swing.price<cur.c if side=="LONG"
                  else old.c>=swing.price>cur.c)
        directional=(cur.c>cur.o if side=="LONG" else cur.c<cur.o)
        if crossing and directional:
            return ("CONFIRMED_15M_PIVOT_CLOSE_BREAK",swing)
    return None

def replay_per_symbol(rows,symbol):
    if symbol not in SYMBOLS or type(rows) is not tuple or len(rows)!=BARS_PER_SYMBOL:
        raise C109Error("UNREGISTERED_SOURCE")
    if rows[0].start_ms!=BEGIN_MS or rows[-1].known_ms!=END_MS:
        raise C109Error("WRONG_ORIGINAL_WINDOW")
    fifteen=p4.aggregate(rows,p4.M15)
    hours=p4.aggregate(rows,p4.H)
    four=p4.aggregate(rows,p4.H4)
    days=p4.aggregate(rows,p4.D1)
    weeks=p4.aggregate(rows,p4.W1,WEEK_ANCHOR)
    if not(len(fifteen)==len(DAYS)*96 and len(hours)==len(DAYS)*24
           and len(four)==len(DAYS)*6 and len(days)==len(DAYS)):
        raise C109Error("INCOMPLETE_ASOF_MTF")
    h1_by_close={b.close_ms:b for b in hours}
    h4_by_close={b.close_ms:i for i,b in enumerate(four)}
    idx3={b.start_ms:i for i,b in enumerate(rows)}
    starts=[b.start_ms for b in rows]
    closed4ms=[b.close_ms for b in four]
    sw4=oldpivots._confirmed(four,p4.H4,END_MS)
    sw15=oldpivots._confirmed(fifteen,p4.M15,END_MS)
    states={arm:{"active":[],"seen":set(),"events":Counter(),
        "rejections":Counter(),"trades":[],"busy":0} for arm in ARMS}
    for k,bar in enumerate(fifteen):
        now=bar.close_ms
        if now in h4_by_close:
            i=h4_by_close[now]
            if i>=2:
                initial,reason=p4.zone_from_three(four[i-2:i+1],days,weeks)
                for arm in ARMS:
                    s=states[arm]
                    if initial is not None:
                        if initial.parent_id in s["seen"]:
                            raise C109Error("DUPLICATE_PARENT_ID")
                        s["seen"].add(initial.parent_id)
                        z=p4.Parent(initial.side,initial.lower,initial.upper,
                                    initial.created_ms,initial.parent_id)
                        s["active"].append(z)
                        s["events"]["CLOSED_4H_PARENT_FVG"]+=1
                    elif reason!="NO_4H_FVG":
                        s["rejections"][reason]+=1
        for arm in ARMS:
            st=states[arm]
            for zone in st["active"]:
                if zone.done or now<=zone.created_ms:continue
                if now-zone.created_ms>p4.MAX_AGE:
                    zone.done=True;st["rejections"]["PARENT_48H_EXPIRED"]+=1;continue
                if zone.first_touch_ms and now-zone.first_touch_ms>p4.TTL:
                    zone.done=True;st["rejections"]["PARENT_TOUCH_8H_TTL"]+=1;continue
                if now in h4_by_close:
                    b4=four[h4_by_close[now]]
                    if (zone.side=="LONG" and b4.c<zone.lower) or (
                        zone.side=="SHORT" and b4.c>zone.upper):
                        zone.done=True;st["rejections"]["PARENT_4H_CLOSED_INVALID"]+=1;continue
                if zone.state=="WAIT_FIRST_TOUCH":
                    if p4.first_touch(zone,bar):
                        zone.first_touch_ms=now;zone.state="WAIT_1H_REJECTION"
                        st["events"]["4H_PARENT_FIRST_TEST"]+=1
                    continue
                if zone.state=="WAIT_1H_REJECTION":
                    if now in h1_by_close:
                        hour=h1_by_close[now]
                        reaction=(p4.rejection(zone,hour) if arm==ARM_BASE else
                                  full_reclaim(zone,hour))
                        if reaction:
                            zone.rejection_ms=now;zone.state="WAIT_15M_VC"
                            st["events"]["CLOSED_1H_REACTION"]+=1
                    continue
                if zone.state!="WAIT_15M_VC":
                    raise C109Error("UNREGISTERED_4H_STATE")
                if k<3 or now<=zone.rejection_ms:
                    continue
                confirmation=(("LEGACY_IMB_OR_SINGLE_BAR_SNR",None)
                    if arm==ARM_BASE and p4.vc(zone,fifteen[k-3:k+1])
                    else (new_signal_type(zone.side,(),fifteen[k-3:k+1],sw15)
                          if arm==ARM_CORE else None))
                if confirmation is None:continue
                kind,swing=confirmation
                zone.done=True
                st["events"]["CLOSED_15M_CONFIRMED"]+=1
                st["events"]["VC_KIND_"+kind]+=1
                if not WARMUP_END<=now<LAST_ENTRY:
                    st["rejections"]["WARMUP_OR_FINAL_48H_EMBARGO"]+=1;continue
                idx=idx3.get(now)
                if idx is None:raise C109Error("NATIVE3M_NEXT_OPEN_MISSING")
                if now<st["busy"]:
                    st["rejections"]["SYMBOL_ALREADY_BUSY"]+=1;continue
                upto=bisect_right(closed4ms,now)
                closed4=four[:upto]
                plan,reason=p4.parent_plan(zone,now,rows[idx].open,
                                           closed4,sw4,rows,starts)
                if plan is None:
                    st["rejections"][reason]+=1;continue
                tr=p4.simulate(rows,idx,zone.side,plan,bps=14)
                if tr["exit_ms"]>END_MS:raise C109Error("RIGHT_CENSORED_AFTER_SOURCE")
                if not (zone.created_ms<zone.first_touch_ms<zone.rejection_ms<
                        now==tr["entry_ms"]):
                    raise C109Error("MISSING_ASOF_EVENT_ORDER")
                if tr["parent_tf"]!=tr["stop_source_tf"] or (
                    tr["stop_source_tf"]!=tr["target_source_tf"] or tr["parent_tf"]!="4H"):
                    raise C109Error("LOWER_TF_STOP_OR_TP_LEAK")
                tr.update({"symbol":symbol,"arm":arm,
                  "first_4h_parent_touch_ms":zone.first_touch_ms,
                  "closed_1h_confirmation_ms":zone.rejection_ms,
                  "confirmed_15m_vc_ms":now,
                  "confirmed_15m_vc_kind":kind,
                  "15m_pivot_confirmed_ms":(swing.confirmed_ms if swing else None),
                  "15m_pivot_price":(str(swing.price) if swing else None),
                  "risk_stop_policy":"PHYSICAL_NATIVE3M_H4_FVG_EDGE_ATR4H_DO_NOT_WIDEN",
                  "4h_parent_invalidation_policy":"H4_CLOSE_INDEPENDENT_OF_PROTECTIVE_SL"})
                st["trades"].append(tr)
                st["busy"]=tr["exit_ms"]
                st["events"]["Genuine_NATIVE3M_PAPER_TRADE"]+=1
            st["active"]=[z for z in st["active"] if not z.done]
    return {"symbol":symbol,"by_arm":{arm:{
        "events":dict(sorted(states[arm]["events"].items())),
        "rejections":dict(sorted(states[arm]["rejections"].items())),
        "trades":states[arm]["trades"]} for arm in ARMS},
        "confirmed_bars":{"native3m":len(rows),"15m":len(fifteen),
                          "1h":len(hours),"4h":len(four),
                          "1d":len(days),"1w":len(weeks)}}

def score(all_trades):
    flat=sorted(all_trades,key=lambda t:(t["entry_ms"],t["symbol"]))
    early=[t for t in flat if t["entry_ms"]<FOLD_MS]
    late=[t for t in flat if t["entry_ms"]>=FOLD_MS]
    sc={str(b):c105.metric(flat,b) for b in p4.BPS}
    sc.update({"fold_early_n":len(early),"fold_late_n":len(late)})
    folds={"early":{str(b):c105.metric(early,b) for b in p4.BPS},
           "late":{str(b):c105.metric(late,b) for b in p4.BPS}}
    return {"scores":sc,"folds":folds,"admission":c105.admission(sc)}

def analyze(market,manifest):
    frozen()
    if set(market)!=set(SYMBOLS) or len(manifest)!=ZIPS:
        raise C109Error("REQUIRES_FULL_PRECOMMITTED_768_ORIGINAL_ZIPS")
    by={s:replay_per_symbol(market[s],s) for s in SYMBOLS}
    result={}
    for arm in ARMS:
        alltrades=sorted((trade for s in SYMBOLS
            for trade in by[s]["by_arm"][arm]["trades"]),
            key=lambda t:(t["entry_ms"],t["symbol"]))
        result[arm]={"trades":alltrades,**score(alltrades)}
    return {"schema":LABEL,
        "precommit":"cycles/B1_C109_PRECOMMIT_SINGLE_P4_CORE_VS_FROZEN_BASELINE_RU.md",
        "source":"ORIGINAL_BINANCE_VISION_USDM_PROVIDER_SHA_ZIP_AND_CSV",
        "begin_utc":BEGIN.strftime("%Y-%m-%d"),
        "end_exclusive_utc":END.strftime("%Y-%m-%d"),
        "symbols":list(SYMBOLS),
        "source_zip_count":len(manifest),"native3m_bars":sum(len(x) for x in market.values()),
        "source_manifest":manifest,"per_symbol":by,
        "arms":result,"economic_conditions":"PREDECLARED_NOT_HINDSIGHT_OPTIMIZED",
        "historical_prior_period_not_prospective_forward_OOS":True,
        "only_4h_parent_stop_and_tp":True,"fixed_rr_target":False,
        "new_luxalgo_indicators":0,"orders":[],"fills":[],"live_trades":[],
        "status":"PAPER_ONLY_NON_PROVEN_ALPHA"}

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    market,manifest=provider_3m()
    z=analyze(market,manifest)
    raw=(json.dumps(z,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(raw)
    print(json.dumps({"zips":len(manifest),"bars":z["native3m_bars"],
      "by_arm":{arm:{"n":len(z["arms"][arm]["trades"]),
         "score25":z["arms"][arm]["scores"]["25"],
         "score40":z["arms"][arm]["scores"]["40"],
         "gate":z["arms"][arm]["admission"],
         "events":dict(sum((Counter(z["per_symbol"][sym]["by_arm"][arm]["events"])
                               for sym in SYMBOLS),Counter()))}
         for arm in ARMS},
       "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()},
       ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
