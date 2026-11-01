"""EMBER: independent source-logic coverage audit, no profitability computations.

Recreate original P07 PerpLab and P10 crypto-trade H1 signals on the
frozen genuine Binance USDT-M closed candles. Compare signal co-occurrence
on the same SYMBOL and DIRECTION in fixed 0/3/6/12/24H prior windows.

NOT an adaptation, optimization, performance test, or new strategy.
Data and source receipts are pinned and asserted. No new orders or PnL.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import pstdev

HERE = Path(__file__).resolve().parent
CSV = HERE / "binance_usdtm_closed_20261101.csv"
DATA_SHA256 = "b885da6dc7e80ea81c7bfb97ec1fb3da615e31824af48625f81cdd376d9a7ee7"
SOURCE_BLOBS = {"P07":"4b04c1834bbf0a3e69d9e67542aea204718550c8",
                "P10":"7568c60cbef2157065d2d1b8944ca5a4c965f39b"}
WINDOWS = (0,3,6,12,24)
SYMBOLS = ("BTCUSDT","ETHUSDT","SOLUSDT")


def load():
    assert hashlib.sha256(CSV.read_bytes()).hexdigest()==DATA_SHA256
    charts=defaultdict(list)
    with CSV.open(newline="") as f:
        for item in csv.DictReader(f):
            if item["interval"]!="1h" or item["symbol"] not in SYMBOLS:
                continue
            charts[item["symbol"]].append({
                "t":int(item["open_time"]),
                "close_time":int(item["close_time"]),
                "h":float(item["high"]),"l":float(item["low"]),
                "c":float(item["close"]),"v":float(item["volume"]),
            })
    assert all(len(charts[s])==1499 for s in SYMBOLS)
    for s in SYMBOLS:
        assert all(charts[s][i+1]["t"]-charts[s][i]["t"]==3600000
                   for i in range(len(charts[s])-1))
    return charts


def p07_source_equivalent(bars, symbol):
    """Mirror the exact ordering from original P07 vectorized Python.

    Critically, REBREAK and RETEST are checked before timeout. This deliberately
    retains observed original late triggers rather than silently fixing them.
    """
    long = None
    short = None
    events=[]
    for i in range(20,len(bars)):
        c=bars[i]["c"]
        upper=max(z["h"] for z in bars[i-20:i])
        lower=min(z["l"] for z in bars[i-20:i])
        side=0
        if long is None:
            if c>upper:
                long={"level":upper,"age":0,"retested":False}
        else:
            long["age"]+=1
            if c>long["level"]*1.0001 and long["retested"]:
                side=1
                events.append({"symbol":symbol,"i":i,"t":bars[i]["t"],
                               "side":side,"late_age":long["age"]})
                long=None
            elif abs(c-long["level"])/long["level"]<=.005:
                long["retested"]=True
            elif long["age"]>5:
                long=None
        if short is None:
            if c<lower:
                short={"level":lower,"age":0,"retested":False}
        else:
            short["age"]+=1
            if c<short["level"]*.9999 and short["retested"]:
                if side==0:
                    events.append({"symbol":symbol,"i":i,"t":bars[i]["t"],
                                   "side":-1,"late_age":short["age"]})
                short=None
            elif abs(c-short["level"])/short["level"]<=.005:
                short["retested"]=True
            elif short["age"]>5:
                short=None
    return events


def bb_feature(bars, i):
    values=[r["c"] for r in bars[i-19:i+1]]
    m=sum(values)/20
    return m,4*pstdev(values)/m


def p10_source_equivalent(bars, symbol):
    events=[]
    for i in range(20,len(bars)):
        mid,bw=bb_feature(bars,i)
        prev_mid,prev_bw=bb_feature(bars,i-1)
        if not(prev_bw<.02 and bw>.02):
            continue
        avg_volume=sum(x["v"] for x in bars[i-9:i+1])/10
        if not bars[i]["v"] > 1.5*avg_volume:
            continue
        side=1 if bars[i]["c"]>mid else -1 if bars[i]["c"]<mid else 0
        if side:
            events.append({"symbol":symbol,"i":i,"t":bars[i]["t"],"side":side})
    return events


def audit():
    charts=load()
    per_symbol={}
    all07=[]
    all10=[]
    for symbol in SYMBOLS:
        x=charts[symbol]
        a=p07_source_equivalent(x,symbol)
        b=p10_source_equivalent(x,symbol)
        all07.extend(a)
        all10.extend(b)
        per_symbol[symbol]={
            "native_parity_expected_P07":len(a),
            "native_parity_expected_P10":len(b),
            "late_P07_source_signals_gt_5":sum(r["late_age"]>5 for r in a),
            "matching_P10_before_or_at_P07":{
                str(hours):sum(any(z["side"]==y["side"]
                                and y["i"]-hours<=z["i"]<=y["i"] for z in b)
                               for y in a)
                for hours in WINDOWS
            }
        }
    assert [len(all07),len(all10)]==[134,54]
    assert [per_symbol[s]["native_parity_expected_P07"] for s in SYMBOLS]==[53,39,42]
    assert [per_symbol[s]["native_parity_expected_P10"] for s in SYMBOLS]==[18,21,15]
    assert sum(v["late_P07_source_signals_gt_5"] for v in per_symbol.values())==16
    totals={str(hours):sum(per_symbol[s]["matching_P10_before_or_at_P07"][str(hours)]
                           for s in SYMBOLS) for hours in WINDOWS}
    assert totals=={"0":4,"3":18,"6":24,"12":31,"24":36},totals
    return {
        "status":"SOURCE_LOGIC_PRE_GATE_COVERAGE_ONLY",
        "no_profitability_or_trade_outcomes":True,
        "raw_data_sha256":DATA_SHA256,
        "original_source_blob_sha":SOURCE_BLOBS,
        "timeframe":"1h",
        "P10_native_default_timeframe":"15m_NOT_VERIFIED_IN_THIS_AUDIT",
        "original_counts":{"P07":len(all07),"P10":len(all10)},
        "same_symbol_same_direction_P10_prior_or_same_P07_by_hours":totals,
        "P07_signals_absent_P10_prior_3h":134-totals["3"],
        "P07_signals_absent_P10_prior_12h":134-totals["12"],
        "source_P07_expired_signals_preserved":16,
        "per_symbol":per_symbol,
        "caution":"P10 as a mandatory gate would discard many P07 ORIGINAL events. This says nothing about whether the retained subset is better; pre/post signal outcome must be audited separately; windows descriptive, not tuned.",
    }


if __name__=="__main__":
    print("EMBER_P07_P10_COVERAGE="+json.dumps(audit(),ensure_ascii=False,allow_nan=False))
