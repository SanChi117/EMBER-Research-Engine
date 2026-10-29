#!/usr/bin/env python3
"""C105 Route P4 independent main 4H-parent MTF PAPER hypothesis, not C93.
Original USD-M native3m + 4H FVG POI / 4H FTA/SL structural-only geometry.
"""
import argparse,hashlib,json
from bisect import bisect_left
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from decimal import Decimal as D
import c93_native3m_raid_bos_route_c_research as oldc93
import c91_continuous_causal_route_a_paper as olda
import c102_c103_native3m_new_symbol_transfer as costs
import c105_parent4h_native3m_source as source
import c105_parent4h_structural_geometry as struct

class C105Rejected(ValueError):pass
FOLD_MS=int(datetime(2026,10,15,tzinfo=timezone.utc).timestamp()*1000)
BEGIN_MS=costs.BEGIN_MS+7*costs.DAY_MS
END_MS=costs.END_MS-struct.MAX_AGE
ORIGINAL_IMMUTABLE={
    "c93_native3m_raid_bos_route_c_research.py":"a241d8de2691bca6247afbfe5e92b0a6e7df25b10f8a4c71f340b815e515bda0",
    "c102_c103_native3m_new_symbol_transfer.py":"853e5ee613e00cddbdf39b933c57bab6b6a6a695f1b549e69f29f52a97a01aed",
    "c104_native3m_source.py":"c23598b95616af96c45741eeca140b30fd0c2aa6f2053c33e4ee5ecdd80322eb"
}
def frozen_source_checks():
    base=Path(__file__).resolve().parent
    for name,sha in ORIGINAL_IMMUTABLE.items():
        if hashlib.sha256((base/name).read_bytes()).hexdigest()!=sha:
            raise C105Rejected("FROZEN_PRIOR_ENGINE_SOURCE_SHA_CHANGED_"+name)

def event_per_coin(rows,sym):
    """Fully chronological 15m event clock, only native3m original; all future 3m prices are for exit replay only."""
    if sym not in source.SYMBOLS or type(rows) is not tuple or len(rows)!=15360:
        raise C105Rejected("UNKNOWN_10CRYPTO_OR_FULL_SOURCE_MISSING")
    if rows[0].start_ms!=costs.BEGIN_MS or rows[-1].known_ms!=costs.END_MS:
        raise C105Rejected("NOT_32_FULL_UTC_DAYS")
    fifteen=struct.aggregate(rows,struct.M15)
    hours=struct.aggregate(rows,struct.H)
    four=struct.aggregate(rows,struct.H4)
    days=struct.aggregate(rows,struct.D1)
    weeks=struct.aggregate(rows,struct.W1,olda.WEEK_ANCHOR)
    if not(len(fifteen)==3072 and len(hours)==768 and len(four)==192 and len(days)==32):
        raise C105Rejected("BAD_COMPLETED_TIMEFRAME_AGGREGATES")
    confirmed=oldc93._confirmed(four,struct.H4,rows[-1].known_ms)
    hour_close={x.close_ms:x for x in hours}
    four_close={x.close_ms:i for i,x in enumerate(four)}
    starts=[x.start_ms for x in rows]
    start_index={v:i for i,v in enumerate(starts)}
    created=[];trades=[];events=Counter();reject=Counter()
    active=[];busy=0;all_parent_ids=set()
    for k,bar in enumerate(fifteen):
        now=bar.close_ms
        if now in four_close:
            i=four_close[now]
            if i>=2:
                parent,why=struct.zone_from_three(four[i-2:i+1],days,weeks)
                if parent:
                    if parent.parent_id in all_parent_ids:
                        raise C105Rejected("DUPLICATE_4H_PARENT")
                    all_parent_ids.add(parent.parent_id)
                    active.append(parent);created.append(parent)
                    events["CLOSED_4H_FVG_PARENT_CREATED"]+=1
                elif why!="NO_4H_FVG":reject[why]+=1
        for zone in active:
            if zone.done or now<=zone.created_ms:continue
            if now-zone.created_ms>struct.MAX_AGE:
                zone.done=True;reject["PARENT_EXPIRED_48H"]+=1;continue
            if zone.first_touch_ms and now-zone.first_touch_ms>struct.TTL:
                zone.done=True;reject["FIRST_TOUCH_TTL_8H"]+=1;continue
            if now in four_close:
                full4=four[four_close[now]]
                if (zone.side=="LONG" and full4.c<zone.lower) or (
                    zone.side=="SHORT" and full4.c>zone.upper):
                    zone.done=True;reject["4H_PARENT_INVALIDATED"]+=1;continue
            if zone.state=="WAIT_FIRST_TOUCH":
                if struct.first_touch(zone,bar):
                    zone.first_touch_ms=now;zone.state="WAIT_1H_REJECTION"
                    events["FIRST_4H_PARENT_TEST"]+=1
                continue
            if zone.state=="WAIT_1H_REJECTION":
                if now in hour_close and struct.rejection(zone,hour_close[now]):
                    zone.rejection_ms=now;zone.state="WAIT_15M_VC"
                    events["1H_CLOSED_REJECTION"]+=1
                continue
            if zone.state!="WAIT_15M_VC":raise C105Rejected("BROKEN_4H_ZONE_LIFECYCLE")
            if not struct.vc(zone,fifteen[:k+1]):continue
            zone.done=True
            events["15M_CLOSED_VC_SIGNAL"]+=1
            if not BEGIN_MS<=now<END_MS:
                reject["OUTSIDE_WARMUP_OR_48H_EMBARGO"]+=1;continue
            idx=start_index.get(now)
            if idx is None:
                raise C105Rejected("NO_GENUINE_NEXT_NATIVE3M_OPEN")
            if now<busy:
                reject["ONE_BUSY_PAPER_POSITION_PER_SYMBOL"]+=1;continue
            last_4h_close=four_close.get(now)
            if last_4h_close is not None:
                closed4=four[:last_4h_close+1]
            else:
                # only fully CLOSED 4h; never include partial current 4h
                last=bisect_left([b.close_ms for b in four],now+1)
                closed4=four[:last]
            entry=rows[idx].open
            plan,why=struct.parent_plan(zone,now,entry,
                closed4,confirmed,rows,starts)
            if plan is None:
                reject[why]+=1;continue
            t=struct.simulate(rows,idx,zone.side,plan)
            if t["exit_ms"]>costs.END_MS:
                raise C105Rejected("RIGHT_CENSORED_48H_HORIZON")
            t.update({"symbol":sym,"first_4h_poi_touch_ms":zone.first_touch_ms,
              "one_hour_rejection_close_ms":zone.rejection_ms,
              "fifteen_minute_vc_close_ms":now})
            if not (zone.created_ms<zone.first_touch_ms<
                    zone.rejection_ms<now==t["entry_ms"]):
                raise C105Rejected("BROKEN_CAUSAL_4H_1H_15M_CHAIN")
            if not(t["stop_source_tf"]=="4H" and t["target_source_tf"]=="4H"
                   and t["parent_tf"]=="4H" and t["zone_lower"]==str(zone.lower)
                   and t["zone_upper"]==str(zone.upper)):
                raise C105Rejected("FOREIGN_TF_SL_OR_TP")
            trades.append(t);busy=t["exit_ms"]
            events["P4_NATIVE3M_PAPER_CLOSED"]+=1
        active=[z for z in active if not z.done]
    return {"symbol":sym,
        "confirmed_tf_bars":{"native3m":len(rows),"15m":len(fifteen),
            "1h":len(hours),"4h":len(four),"1d":len(days),"1w":len(weeks)},
        "events":dict(sorted(events.items())),
        "rejects":dict(sorted(reject.items())),
        "trades":trades}

def metric(trades,bps):
    zz=sorted((costs.price_stress(t,bps) for t in trades),
        key=lambda t:(t["entry_ms"],t["symbol"]))
    return costs._score(zz)

def summarize(trades):
    sorted_t=sorted(trades,key=lambda x:(x["entry_ms"],x["symbol"]))
    first=[t for t in sorted_t if t["entry_ms"]<FOLD_MS]
    late=[t for t in sorted_t if t["entry_ms"]>=FOLD_MS]
    scores={str(b):metric(sorted_t,b) for b in struct.BPS}
    scores.update({"fold_early_n":len(first),"fold_late_n":len(late)})
    folds={"early":{str(b):metric(first,b) for b in struct.BPS},
           "late":{str(b):metric(late,b) for b in struct.BPS}}
    return scores,folds

def admission(scores):
    z=scores["25"];s=scores["40"]
    reasons=[]
    if z["n"]<30:reasons.append("NO_POWER_N_LT_30")
    if scores["fold_early_n"]<10 or scores["fold_late_n"]<10:
        reasons.append("NO_POWER_TEMPORAL_FOLD")
    if z["sum_r"]<=0:reasons.append("NONPOSITIVE_NETR25")
    if z["pf"] is None or z["pf"]<=1.2:reasons.append("PF25_NOT_GT_1_2")
    if s["pf"] is None or s["pf"]<=1.1:reasons.append("PF40_NOT_GT_1_1")
    if z["dd_1pct_risk_pct"]>=10:reasons.append("MODELED_DD25_NOT_LT_10PCT")
    return {"passes_historical_screen":not reasons,
        "reasons":reasons,"live_approved":False,
        "status":"PAPER_ONLY_HISTORICAL_NOT_PROSPECTIVE_OOS"}

def analyze(markets,manifest):
    frozen_source_checks()
    if set(markets)!=set(source.SYMBOLS) or len(manifest)!=source.EXPECTED:
        raise C105Rejected("UNREGISTERED_320_ORIGINAL_ARCHIVES")
    if len({(m["symbol"],m["date"]) for m in manifest})!=320:
        raise C105Rejected("MANIFEST_DUPLICATE")
    bysym={s:event_per_coin(markets[s],s) for s in source.SYMBOLS}
    trades=sorted([t for x in bysym.values() for t in x["trades"]],
        key=lambda x:(x["entry_ms"],x["symbol"]))
    scores,folds=summarize(trades)
    return {"schema":"EMBER_C105_MAIN_4H_PARENT_NATIVE3M_1H_REACTION_15M_VC",
      "precommit":"B1_C105_PRECOMMIT_PARENT_4H_POI_SL_TP_NATIVE3M_RU.md",
      "sample":"HISTORICAL_NEW_SYMBOL_C105_4H_MODEL_NOT_PROSPECTIVE_OOS",
      "symbols":list(source.SYMBOLS),"source_zip_count":len(manifest),
      "native3m_bars":sum(len(v) for v in markets.values()),
      "source_manifest":manifest,"per_symbol":bysym,
      "trades":trades,"scores":scores,"folds":folds,
      "admission":admission(scores),
      "only_parent_stop_and_target":True,
      "fixed_rr_target":False,
      "orders":[],"fills":[],"live_trades":[],
      "readiness":"PAPER_RESEARCH_ONLY_NOT_LIVE_READY"}

def dumps(x):
    return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    frozen_source_checks()
    market,receipt=source.original_all()
    x=analyze(market,receipt)
    raw=dumps(x)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(raw)
    print(json.dumps({"archive_count":x["source_zip_count"],"native3m_bars":x["native3m_bars"],
      "total_trades":len(x["trades"]),"all_event_counts":dict(sum((Counter(m["events"]) for m in x["per_symbol"].values()),Counter())),
      "all_reject_counts":dict(sum((Counter(m["rejects"]) for m in x["per_symbol"].values()),Counter())),
      "netR25":x["scores"]["25"]["sum_r"],"pf25":x["scores"]["25"]["pf"],
      "witness_bytes":len(raw),"witness_sha256":hashlib.sha256(raw).hexdigest(),
      "admission":x["admission"]},sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
