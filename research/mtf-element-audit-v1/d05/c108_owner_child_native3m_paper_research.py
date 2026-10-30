#!/usr/bin/env python3
"""C108: frozen minimal owner-derived 4H parent + new H1 IMB child + FIRST TEST.
Only existing elements, no generic 15m previous-bar SNR, 4H-only SL/FTA TP.
Original Binance USD-M 3m per-day provider CHECKSUM; PAPER ONLY.
This is an adapted research hypothesis, NOT author-verified or live-ready.
"""
import argparse,hashlib,json
from concurrent.futures import ThreadPoolExecutor
from bisect import bisect_left
from collections import Counter
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
from pathlib import Path
import c104_native3m_source as provider
import c105_parent4h_native3m_research as original
import c105_parent4h_structural_geometry as h4
import c108_parent_h1_child_first_test_geometry as semantics
import c93_native3m_raid_bos_route_c_research as pivots
import c102_c103_native3m_new_symbol_transfer as costs
from c91_continuous_causal_route_a_paper import WEEK_ANCHOR

class C108Error(ValueError):pass
UNIVERSE=("BNBUSDT","XLMUSDT","HBARUSDT","INJUSDT","OPUSDT",
          "ALGOUSDT","CHZUSDT","ICPUSDT","SEIUSDT","PENDLEUSDT")
BEG=datetime(2026,8,20,tzinfo=timezone.utc)
END=datetime(2026,9,21,tzinfo=timezone.utc)
BEG_MS=int(BEG.timestamp()*1000)
END_MS=int(END.timestamp()*1000)
DAYS=tuple((BEG+timedelta(days=i)).strftime("%Y-%m-%d") for i in range((END-BEG).days))
DAY_MS=86400000
BEGIN_ELIGIBLE_MS=BEG_MS+7*DAY_MS
END_ELIGIBLE_MS=END_MS-48*h4.H
SPLIT_MS=int(datetime(2026,9,5,tzinfo=timezone.utc).timestamp()*1000)
EXPECTED_ZIPS=320
SOURCE_FILENAME="B1_C108_PRECOMMIT_MINIMAL_OWNER_CHILD_FIRST_TEST_NATIVE3M_RU.md"
FROZEN_C105_SHA="f04b58b998bc1a4bbc531202f241eb476395457765c68189eabf0344f5bd370f"
FROZEN_C105_GEOMETRY_SHA="b86623b8a7bb8f2580c129e70edbc0dfcf0f68bafc90f94e726d999f0e5db7ac"

def check_freeze():
    root=Path(__file__).resolve().parent
    for name,expected in (
      ("c105_parent4h_native3m_research.py",FROZEN_C105_SHA),
      ("c105_parent4h_structural_geometry.py",FROZEN_C105_GEOMETRY_SHA)):
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise C108Error("C105_SOURCED_POLICY_MUTATED_"+name)
    original.frozen_source_checks()
    if len(DAYS)!=32 or len(UNIVERSE)!=10 or len(set(UNIVERSE))!=10:
        raise C108Error("UNREGISTERED_SOURCE_UNIVERSE")

def load_native_original(*,fetch=None):
    """Use immutable provider.daily parser, scoped allowlist restored even on error.
    Do not reuse legacy load() because its hardcoded Sep26-Oct27 clock differs.
    """
    check_freeze()
    old_symbols=provider.SYMBOLS;old_days=provider.DAYS
    tasks=[(symbol,day) for symbol in UNIVERSE for day in DAYS]
    try:
        provider.SYMBOLS=UNIVERSE
        provider.DAYS=DAYS
        def one(item):
            symbol,day=item
            if fetch is None:bars,proof=provider.daily(symbol,day)
            else:bars,proof=provider.daily(symbol,day,fetch=fetch)
            return item,bars,proof
        with ThreadPoolExecutor(max_workers=10) as pool:
            downloaded=list(pool.map(one,tasks))
    finally:
        provider.SYMBOLS=old_symbols
        provider.DAYS=old_days
    by={s:[] for s in UNIVERSE}
    manifest=[]
    if len(downloaded)!=EXPECTED_ZIPS:raise C108Error("320_ORIGINAL_BINANCE_ZIP_REQUIRED")
    for (sym,day),rows,receipt in downloaded:
        if len(rows)!=480 or receipt["symbol"]!=sym or receipt["date"]!=day:
            raise C108Error("INVALID_NATIVE3M_SOURCE_RECEIPT")
        if by[sym] and by[sym][-1].known_ms!=rows[0].start_ms:
            raise C108Error("DAILY_NATIVE3M_JOIN_GAP")
        by[sym].extend(rows)
        manifest.append(receipt)
    if len({(p["symbol"],p["date"]) for p in manifest})!=320:
        raise C108Error("ORIGINAL_SOURCE_DUPLICATE")
    for sym in UNIVERSE:
        x=by[sym]
        if not(len(x)==15360 and x[0].start_ms==BEG_MS and x[-1].known_ms==END_MS):
            raise C108Error("NOT_32_UTC_DAYS_ORIGINAL_3M")
    return {s:tuple(x) for s,x in by.items()},manifest

def one_market(rows,symbol):
    """Event loop evaluates strictly fully CLOSED higher-TF bars at the 15m close."""
    if symbol not in UNIVERSE or len(rows)!=15360 or rows[0].start_ms!=BEG_MS or rows[-1].known_ms!=END_MS:
        raise C108Error("SOURCE_SYMBOL_CALENDAR_NOT_REGISTERED")
    fifteen=h4.aggregate(rows,h4.M15)
    hours=h4.aggregate(rows,h4.H)
    four=h4.aggregate(rows,h4.H4)
    days=h4.aggregate(rows,h4.D1)
    weeks=h4.aggregate(rows,h4.W1,WEEK_ANCHOR)
    if not(len(fifteen)==3072 and len(hours)==768 and len(four)==192 and len(days)==32):
        raise C108Error("WRONG_NATIVE3M_AGGREGATION")
    by_4h={x.close_ms:i for i,x in enumerate(four)}
    by_1h={x.close_ms:i for i,x in enumerate(hours)}
    first_orig={x.start_ms:i for i,x in enumerate(rows)}
    native_start=tuple(x.start_ms for x in rows)
    h4_close=[x.close_ms for x in four]
    swings4=pivots._confirmed(four,h4.H4,END_MS)
    events=Counter();reject=Counter();active=[];trades=[];busy_until=0;ids=set()
    for k,bar in enumerate(fifteen):
        now=bar.close_ms
        if now in by_4h:
            zidx=by_4h[now]
            if zidx>=2:
                z,reason=semantics.build_parent(four[zidx-2:zidx+1],days,weeks)
                if z is not None:
                    if z.parent_id in ids:raise C108Error("DUPLICATE_4H_PARENT")
                    ids.add(z.parent_id);active.append(z)
                    events["PARENT_4H_FVG_CREATED"]+=1
                elif reason!="NO_4H_FVG":reject[reason]+=1
        for z in active:
            if z.done or now<=z.created_ms:continue
            expired=semantics.eligible_ttl(z,now)
            if expired:z.done=True;reject[expired]+=1;continue
            if now in by_4h and semantics.parent_invalidated(z,four[by_4h[now]]):
                z.done=True;reject["4H_PARENT_INVALIDATED_ON_CLOSED_H4"]+=1;continue
            if z.state=="WAIT_PARENT_FIRST_TEST":
                if semantics.parent_touch(z,bar):
                    z.first_touch_ms=now;z.state="WAIT_1H_CHILD"
                    events["PARENT_4H_FIRST_PHYSICAL_TEST"]+=1
                continue
            if z.state=="WAIT_1H_CHILD":
                if now in by_1h:
                    hi=by_1h[now]
                    if hi>=2:
                        item,reason=semantics.child_from_closed_h1(z,hours[hi-2:hi+1])
                        if item:
                            semantics.adopt_child(z,item)
                            events["1H_CHILD_FVG_CREATED"]+=1
                        elif reason=="NESTED_4H_IMB_1H_IMB_VETO":
                            reject[reason]+=1
                continue
            if z.state=="WAIT_CHILD_FIRST_TEST":
                if semantics.child_first_touch(z,bar):
                    semantics.adopt_child_first_test(z,bar)
                    events["1H_CHILD_FIRST_PHYSICAL_TEST"]+=1
                continue
            if z.state!="WAIT_15M_DIRECT_IMB":
                raise C108Error("UNKNOWN_LINKED_PARENT_CHILD_STATE")
            if k<2 or not semantics.direct_15m_imb(z,fifteen[k-2:k+1]):
                continue
            z.vc_ms=now;z.done=True
            events["15M_DIRECT_CLOSED_IMB_AFTER_CHILD_FIRST_TEST"]+=1
            if not BEGIN_ELIGIBLE_MS<=now<END_ELIGIBLE_MS:
                reject["OUTSIDE_7D_WARMUP_OR_48H_EMBARGO"]+=1;continue
            idx=first_orig.get(now)
            if idx is None:raise C108Error("NO_SOURCE_NEXT_NATIVE3M_OPEN")
            if now<busy_until:
                reject["ONE_PAPER_TRADE_PER_SYMBOL_WHILE_BUSY"]+=1;continue
            at4=bisect_left(h4_close,now+1)
            full4=four[:at4]
            plan,reason=h4.parent_plan(z,now,rows[idx].open,full4,swings4,rows,native_start)
            if plan is None:reject[reason]+=1;continue
            outcome=h4.simulate(rows,idx,z.side,plan,bps=14)
            if outcome["exit_ms"]>END_MS:raise C108Error("UNEXPECTED_RIGHT_CENSORED_EXIT")
            outcome.update({
              "symbol":symbol,
              "4h_parent_first_touch_ms":z.first_touch_ms,
              "1h_child_created_ms":z.child_created_ms,
              "1h_child_lower":str(z.child_low),"1h_child_upper":str(z.child_high),
              "1h_child_id":z.child_id,
              "1h_child_first_test_ms":z.child_first_test_ms,
              "15m_direct_imb_vc_ms":now,
              "rule_semantics":"ADAPTED_OWNER_LINKED_4H_TO_1H_CHILD_FIRST_TEST_DIRECT_15M_IMB",
              "stop_policy":"EXECUTABLE_NATIVE3M_PROTECTIVE_4H_ZONE_EDGE_ATR4H",
              "setup_invalidation_policy":"4H_CLOSE_FAR_FVG_EDGE_SEPARATE_FROM_RISK_STOP"})
            if not (z.created_ms<z.first_touch_ms<z.child_created_ms<
                    z.child_first_test_ms<now==outcome["entry_ms"]):
                raise C108Error("CAUSAL_4H_PARENT_H1_CHILD_15M_IMB_ORDER_BROKEN")
            if not(outcome["parent_tf"]==outcome["stop_source_tf"]==
                    outcome["target_source_tf"]=="4H"):
                raise C108Error("NON_4H_STOP_OR_TARGET")
            if outcome["exit_reason"] in ("STOP_FIRST_SAME_3M","STOP_GAP"):
                exit_close_ms=((outcome["exit_ms"]+h4.H4-1)//h4.H4)*h4.H4
                if exit_close_ms not in by_4h:raise C108Error("MISSING_LATER_4H_STOP_CLOSE")
                outcome.update(semantics.protective_stop_semantics(z,outcome["exit_reason"],
                     four[by_4h[exit_close_ms]]))
            else:
                outcome.update({"protective_stop_triggered":False,
                   "parent_validity_at_4h_close":"NOT_A_STOP"})
            trades.append(outcome);events["PAPER_TRADE_4H_STOP_AND_TP"]+=1
            busy_until=outcome["exit_ms"]
        active=[z for z in active if not z.done]
    return {"symbol":symbol,"bars":{"native3m":len(rows),"15m":len(fifteen),"1h":len(hours),
        "4h":len(four),"1d":len(days),"1w":len(weeks)},
        "events":dict(sorted(events.items())),
        "rejects":dict(sorted(reject.items())),
        "trades":trades}

def metric(trades,bps):
    from c102_c103_native3m_new_symbol_transfer import _score,price_stress
    rows=sorted((price_stress(t,bps) for t in trades),key=lambda x:(x["entry_ms"],x["symbol"]))
    return _score(rows)

def analysis(markets,manifest):
    check_freeze()
    if set(markets)!=set(UNIVERSE) or len(manifest)!=EXPECTED_ZIPS:
        raise C108Error("EXACT_320_AUTHENTIC_SOURCE_REQUIRED")
    by={s:one_market(markets[s],s) for s in UNIVERSE}
    alltrades=sorted([t for x in by.values() for t in x["trades"]],
         key=lambda x:(x["entry_ms"],x["symbol"]))
    early=[t for t in alltrades if t["entry_ms"]<SPLIT_MS]
    late=[t for t in alltrades if t["entry_ms"]>=SPLIT_MS]
    scores={str(b):metric(alltrades,b) for b in h4.BPS}
    scores.update({"fold_early_n":len(early),"fold_late_n":len(late)})
    folds={"early":{str(b):metric(early,b) for b in h4.BPS},
           "late":{str(b):metric(late,b) for b in h4.BPS}}
    return {
      "schema":"EMBER_C108_MINIMAL_LINKED_H4_PARENT_H1_CHILD_FIRST_TEST_15M_IMB",
      "precommit":SOURCE_FILENAME,
      "source_zip_count":len(manifest),
      "native3m_bars":sum(len(r) for r in markets.values()),
      "original_source_manifest":manifest,
      "symbols":list(UNIVERSE),
      "utc_start":BEG.strftime("%Y-%m-%d"),"utc_end_exclusive":END.strftime("%Y-%m-%d"),
      "historical_second_period_not_future_prospective_oos":True,
      "per_symbol":by,"trades":alltrades,"scores":scores,"folds":folds,
      "admission":original.admission(scores),
      "only_parent_stop_and_target":True,"fixed_rr_target":False,
      "new_luxalgo_indicators":0,
      "owner_source_semantic_completeness":"ONE_LINKED_1H_FVG_CHILD_BRANCH_ONLY_NOT_ALL_ROUTE_A",
      "orders":[],"fills":[],"live_trades":[],
      "readiness":"PAPER_RESEARCH_NOT_LIVE_READY"}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    markets,manifest=load_native_original()
    out=analysis(markets,manifest)
    raw=(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(raw)
    print(json.dumps({"n":len(out["trades"]),"zips":out["source_zip_count"],
          "bars":out["native3m_bars"],"events":dict(sum(
             (Counter(x["events"]) for x in out["per_symbol"].values()),Counter())),
          "reject":dict(sum((Counter(x["rejects"]) for x in out["per_symbol"].values()),Counter())),
          "score25":out["scores"]["25"],"admission":out["admission"],
          "witness_sha256":hashlib.sha256(raw).hexdigest(),
          "witness_bytes":len(raw)},sort_keys=True))
if __name__=="__main__":main()
