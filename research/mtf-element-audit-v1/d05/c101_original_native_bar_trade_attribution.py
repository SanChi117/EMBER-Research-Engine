#!/usr/bin/env python3
"""C101: original pinned Binance 3m/5m forensic replay of *already known* C98 trades.

Descriptive post-hoc work only. Not a new holdout, not a strategy or live order.
OHLC cannot prove the within-candle ordering: STOP is conservatively prioritized.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
from statistics import median
import argparse
import json

from c98_new_oct_original_forward_paper import (
    START_MS, END_MS, daily_zip, STEP, THREE, EXPECTED_SYMBOLS, C98Rejected)
from c100_frozen_c98_loss_forensics import inspect_trade

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"evidence/c98/C98_NEW_OCT_SOURCE_ABC_CLOSED_HOLDOUT.json"
SOURCE_SHA="9b95735407465c46b1a2fdb6e4e8875bfdd2c428588f6205bf1212d35c0b9e97"
DAY=86400000
COST_BPS=14
HOLD_LIMIT={"A":None,"B":None,"C":None}
class C101Rejected(ValueError):pass

def day_label(at):
    return datetime.fromtimestamp(at/1000,tz=timezone.utc).strftime("%Y-%m-%d")

def asbar(row,tf):
    if tf=="3m":
        return (row.start_ms,row.known_ms,row.open,row.high,row.low,row.close,row.volume)
    return (row.open_ms,row.close_ms,row.o,row.h,row.l,row.c,row.volume)

def required_manifest(doc):
    if type(doc) is not dict or doc.get("new_archive_count")!=240:
        raise C101Rejected("NOT_ORIGINAL_C98_240_ARCHIVES")
    pinned={(v["symbol"],v["timeframe"],v["date"]):v
           for v in doc["new_source_manifest"]}
    if len(pinned)!=240:
        raise C101Rejected("MISSING_OR_DUPLICATE_BINANCE_SOURCE_MANIFEST")
    needed=set()
    for route,model in doc["research_models"].items():
        tf="3m" if route=="C" else "5m"
        for t in model["trades"]:
            inspect_trade(t,route)
            entry=t["entry_ms"]
            # Include one previous historical day for as-of preentry context.
            first=max(START_MS,(entry//DAY-1)*DAY)
            last=(t["exit_ms"]-1)//DAY*DAY
            for day in range(first,last+1,DAY):
                key=(t["symbol"],tf,day_label(day))
                if key not in pinned:
                    raise C101Rejected("SOURCE_OUTSIDE_C98_PINNED_MANIFEST")
                needed.add(key)
    return pinned,sorted(needed)

def retrieve_original(doc,*,fetch=None):
    pinned,needed=required_manifest(doc)
    def one(k):
        sym,tf,date=k
        kw={} if fetch is None else {"fetch":fetch}
        rows,meta=daily_zip(sym,tf,date,**kw)
        expectation=pinned[k]
        if (meta["zip_sha256"]!=expectation["zip_sha256"] or
            meta["csv_sha256"]!=expectation["csv_sha256"] or
            meta["bars"]!=expectation["bars"] or
            meta["url"]!=expectation["url"]):
            raise C101Rejected("FROZEN_C98_ORIGINAL_BINANCE_ZIP_OR_CSV_SHA_CHANGED")
        return k,rows,meta
    with ThreadPoolExecutor(max_workers=8) as pool:
        retrieved=list(pool.map(one,needed))
    source={};receipts=[]
    for (sym,tf,date),part,meta in retrieved:
        source.setdefault((sym,tf),[]).extend(asbar(r,tf) for r in part)
        receipts.append(meta)
    for k,arr in source.items():
        arr.sort(key=lambda x:x[0])
        step=THREE if k[1]=="3m" else STEP
        if any(a[1]!=z[0] or z[0]-a[0]!=step for a,z in zip(arr,arr[1:])):
            # A missing whole no-trade day between selected days is allowed, but a
            # full interval from preentry through exit MUST later be continuous.
            pass
    return {k:tuple(v) for k,v in source.items()}, receipts

def find_entry(rows,t,tf):
    step=THREE if tf=="3m" else STEP
    match=[i for i,b in enumerate(rows) if b[0]==t["entry_ms"]]
    if len(match)!=1:
        raise C101Rejected("ENTRY_OPEN_CLOCK_NOT_FOUND_IN_PINNED_NATIVE_HISTORY")
    i=match[0]
    if rows[i][1]-rows[i][0]!=step:
        raise C101Rejected("FAKE_NATIVE_BAR_CLOCK")
    if tf=="3m" or not t.get("limit_filled"):
        if rows[i][2]!=D(t["entry"]):
            raise C101Rejected("A_OR_C_ENTRY_NOT_NATIVE_OPEN")
    else:
        price=D(t["entry"])
        if not rows[i][4]<=price<=rows[i][3]:
            raise C101Rejected("B_LIMIT_NOT_TOUCHED_ON_FROZEN_FILL_BAR")
    return i

def validate_historical_path(rows,t,route):
    tf="3m" if route=="C" else "5m"
    i=find_entry(rows,t,tf)
    info=inspect_trade(t,route)
    entry=D(t["entry"]);stop=D(t["stop"]);target=D(t["target"])
    risk=abs(entry-stop);side=info["side"]
    if route=="B":
        if not t["signal_ms"]<=t["entry_ms"] or (
                t["signal_ms"]%STEP or t["entry_ms"]%STEP):
            raise C101Rejected("IDM_LIMIT_SIGNAL_NOT_PREKNOWN")
    upper_fav=D(0);upper_adv=D(0);outcome=None
    exit_at=t["exit_ms"]; dual_touches=0;bars=0
    j=i
    for j in range(i,len(rows)):
        start,end,o,h,l,c,_=rows[j]
        if j>i and start!=rows[j-1][1]:
            raise C101Rejected("MISSING_NATIVE_CANDLE_INSIDE_TRADE")
        if end>exit_at:
            raise C101Rejected("TRADE_EXIT_NOT_REPRODUCIBLE_ON_NATIVE_BAR")
        bars+=1
        if side=="LONG":
            upper_fav=max(upper_fav,(h-entry)/risk)
            upper_adv=max(upper_adv,(entry-l)/risk)
            sl_hit=l<=stop;tp_hit=h>=target
            gap_sl=o<=stop;gap_tp=o>=target
        else:
            upper_fav=max(upper_fav,(entry-l)/risk)
            upper_adv=max(upper_adv,(h-entry)/risk)
            sl_hit=h>=stop;tp_hit=l<=target
            gap_sl=o>=stop;gap_tp=o<=target
        if sl_hit and tp_hit:
            dual_touches+=1
        reason=None;price=None
        # B limit may fill only during this candle; pre-touch high/low path unknown.
        # Original C94 does NOT credit TP on fill candle, but may stop immediately.
        if not(route=="B" and j==i):
            if gap_sl:reason="STOP_GAP";price=o
            elif gap_tp:reason="FTA_AT_OPEN" if route=="C" else "FTA_OPEN";price=target
        if reason is None and sl_hit:
            reason={"A":"STOP_FIRST_AMBIGUOUS",
                    "B":"STOP_FIRST_AFTER_LIMIT_TOUCH",
                    "C":"STOP_FIRST_SAME_3M"}[route]
            price=stop
        if reason is None and tp_hit and not(route=="B" and j==i):
            reason={"A":"STRUCTURAL_FTA","B":"STRUCTURAL_4H_FTA",
                    "C":"1H_FTA"}[route];price=target
        if reason is not None:
            outcome=(reason,price,end)
            break
        if end==exit_at:
            reason={"A":"TIME_OUT","B":"TIME_LIMIT","C":"TIME_OUT"}[route]
            outcome=(reason,c,end)
            break
    if outcome is None or outcome[2]!=exit_at or outcome[0]!=t["exit_reason"]:
        raise C101Rejected("FROZEN_TRADE_EXIT_REASON_OR_CLOCK_NOT_REPRODUCED")
    reason,price,end=outcome
    net=((price-entry) if side=="LONG" else (entry-price))/risk
    net-=D(COST_BPS)/D(10000)*entry/risk
    if abs(D(str(round(float(net),6)))-D(str(t["net_r"])))>D("0.000001"):
        raise C101Rejected("FROZEN_14BPS_NET_R_NOT_REPRODUCED")
    pre=rows[max(0,i-20):i]
    if len(pre)!=20 or any(a[1]!=z[0] for a,z in zip(pre,pre[1:])) or pre[-1][1]!=rows[i][0]:
        range_r=None
    else:
        tr=[max(x[3]-x[4],abs(x[3]-old[5]),abs(x[4]-old[5]))
            for old,x in zip(pre[:-1],pre[1:])]
        range_r=float(risk/median(tr)) if median(tr)>0 else None
    # This trajectory envelope uses the WHOLE exit candle (known only afterwards).
    # It is descriptive, NOT attainable fill PnL or a pre-entry signal.
    return {
        "entry_ms":t["entry_ms"],"exit_ms":end,"symbol":t["symbol"],
        "route":route,"source_tf":"NATIVE_"+tf.upper(),"exit_reason":reason,
        "entry":t["entry"],"stop":t["stop"],"target":t["target"],
        "net_14bps_r":t["net_r"],"source_candles_during_position":bars,
        "same_bar_both_sl_tp_count":dual_touches,
        "same_bar_ambiguous":dual_touches>0,
        "preentry_risk_over_native_true_range_median20":(
            round(range_r,6) if range_r is not None else None),
        "preentry_last_known_ms":rows[i-1][1] if i else None,
        "post_entry_ohlc_upper_envelope_mfe_r":round(float(upper_fav),6),
        "post_entry_ohlc_upper_envelope_mae_r":round(float(upper_adv),6),
        "max_ohcl_envelope_not_executable":True,
        "post_hoc_not_fresh_oos":True
    }

def signal_snapshot(rows,t,route):
    # These are observations at entry, never training features from future candles.
    side="LONG" if D(t["stop"])<D(t["entry"]) else "SHORT"
    if route=="C":
        known=t["entry_ms"]
        signal=[x for x in rows if x[1]==t["bos_close_ms"]]
        if len(signal)!=1 or signal[0][1]!=known:
            raise C101Rejected("MISSING_NATIVE3M_CLOSED_BOS")
        x=signal[0];lev=D(t["bos_level"])
        if (side=="LONG" and not x[5]>lev) or (
                side=="SHORT" and not x[5]<lev):
            raise C101Rejected("BOS_NOT_CLOSED_BEYOND_PREKNOWN_LEVEL")
        if not (t["bos_confirmed_ms"]<=t["raid_closed_ms"]<
                t["bos_close_ms"]==known and
                t["raid_fractal_known_ms"]<=t["raid_closed_ms"]):
            raise C101Rejected("NONCAUSAL_C_BOS_OR_RAID_TIMESTAMP")
        width=x[3]-x[4]
        ratio=float(abs(x[5]-x[2])/width) if width else 0
        start=t["raid_closed_ms"]-3600000
        raid=[bar for bar in rows if start<=bar[0]<t["raid_closed_ms"]]
        raid_verified=False
        if len(raid)==20 and raid[0][0]==start and raid[-1][1]==t["raid_closed_ms"]:
            hi=max(q[3] for q in raid);lo=min(q[4] for q in raid)
            lastclose=raid[-1][5];swept=D(t["raid_fractal_level"])
            extreme=D(t["raid_extreme"])
            if side=="SHORT":
                raid_verified=hi==extreme and hi>swept and lastclose<swept
            else:
                raid_verified=lo==extreme and lo<swept and lastclose>swept
            if not raid_verified:
                raise C101Rejected("1H_RAID_WICK_RECLAIM_NOT_SUPPORTED_BY_NATIVE3M")
        return {
            "bos_body_to_range":round(ratio,6),
            "bos_candle_known_ms":x[1],
            "bos_level_preknown_ms":t["bos_confirmed_ms"],
            "raid_reconstructed_from_native3m":raid_verified,
            "raid_context_left_censored":not raid_verified,
            "raid_to_bos_minutes":(t["bos_close_ms"]-t["raid_closed_ms"])//60000}
    if route=="B":
        if not(t["idm_confirmed_ms"]<=t["signal_ms"]<=t["entry_ms"] and
               t["stronghl_confirmed_ms"]<=t["entry_ms"]):
            raise C101Rejected("FUTURE_IDM_OR_STRONGHL")
        return {"idm_to_fill_minutes":(t["entry_ms"]-t["idm_confirmed_ms"])//60000,
                "limit_wait_minutes":(t["entry_ms"]-t["signal_ms"])//60000,
                "idm_confirmed_asof_ms":t["idm_confirmed_ms"]}
    if not(t["poi_created_ms"]<=t["poi_first_test_ms"]<=t["entry_ms"] and
           t["vc_close_ms"]==t["entry_ms"] and
           t["stronghl_confirmed_ms"]<=t["entry_ms"]):
        raise C101Rejected("FUTURE_POI_VC_OR_STRONGHL")
    return {"poi_first_touch_to_entry_minutes":(t["entry_ms"]-t["poi_first_test_ms"])//60000,
            "fta_known_age_minutes":(t["entry_ms"]-t["fta_confirmed_ms"])//60000,
            "vc_known_at_entry_ms":t["vc_close_ms"]}

def analyze(doc,raw,receipts):
    if doc["new_archive_count"]!=240:
        raise C101Rejected("SOURCE_NOT_240_ARCHIVES")
    _,need=required_manifest(doc)
    got={(v["symbol"],v["timeframe"],v["date"]) for v in receipts}
    if got!=set(need) or len(receipts)!=len(need):
        raise C101Rejected("INCOMPLETE_OR_EXTRA_ORIGINAL_SHA_RECEIPTS")
    evidence=[];counts=Counter();exit_counts=Counter();dual=Counter()
    for route in ("A","B","C"):
        tf="3m" if route=="C" else "5m"
        for t in doc["research_models"][route]["trades"]:
            source=raw.get((t["symbol"],tf))
            if not source:
                raise C101Rejected("MISSING_NATIVE_CANDLE_COLLECTION")
            trade=validate_historical_path(source,t,route)
            trade["asof_features"]=signal_snapshot(source,t,route)
            evidence.append(trade);counts[route]+=1
            exit_counts[(route,t["exit_reason"])]+=1
            dual[route]+=int(trade["same_bar_ambiguous"])
    if dict(counts)!={"A":7,"B":3,"C":38} or len(evidence)!=48:
        raise C101Rejected("FROZEN_48_REPLAY_INCOMPLETE")
    return {
        "schema":"C101_ORIGINAL_NATIVE_BAR_FROZEN_C98_REPLAY",
        "source_sha256":SOURCE_SHA,"original_c98_archives_total":240,
        "native_sha_verified_selected_zip_count":len(receipts),
        "native_selected_sha_manifest":receipts,
        "source_c98_trades":48,
        "exact_replayed_trades":len(evidence),"by_route":dict(counts),
        "exit_reasons":{f"{k[0]}:{k[1]}":v for k,v in sorted(exit_counts.items())},
        "dual_touch_trades_by_route":dict(dual),
        "trade_evidence":evidence,
        "classification":"POST_HOC_DIAGNOSTIC_NOT_NEW_OOS",
        "actual_orderbook_spread_verified":False,
        "not_author_semantics_certified":True,
        "sl_tp_from_structure_not_fixed_rr":True,
        "strategy_changed":False,"real_orders":[],"fills":[],"live_trades":[],
        "conclusion":"SOURCE_REPLAY_ONLY_NOT_PROOF_OF_CAUSAL_LOSS_OR_PROFITABILITY",
    }

def execute(*,fetch=None):
    raw_bytes=SOURCE.read_bytes()
    if sha256(raw_bytes).hexdigest()!=SOURCE_SHA:
        raise C101Rejected("ORIGINAL_C98_SHA_MISMATCH")
    doc=json.loads(raw_bytes)
    raw,receipts=retrieve_original(doc,fetch=fetch)
    return analyze(doc,raw,receipts)

def dumps(z):
    return (json.dumps(z,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    payload=dumps(execute())
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_bytes(payload)
    print(json.dumps({"source_trades":48,
           "payload_bytes":len(payload),"sha256":sha256(payload).hexdigest(),
           "output":str(args.output) if args.output else None},sort_keys=True))
if __name__=="__main__":
    main()
