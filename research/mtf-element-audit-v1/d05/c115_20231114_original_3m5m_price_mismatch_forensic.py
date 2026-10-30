#!/usr/bin/env python3
"""C115 source-only original 3m/5m exact OHLC forensic: Nov 14 2023.

One previously source-exposed date and the frozen 12 assets; checks all
24 provider ZIP receipts. Not a trading replay or basis for changing C115.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from decimal import Decimal as D
from pathlib import Path
from contextlib import contextmanager
import argparse,hashlib,json

import c104_native3m_source as r3
import c114_original_native5m_daily_source as r5
import c115_4h_poi_native5m_price_only_blind_replay as c115

DATE="2023-11-14"
DAY_MS=int(datetime(2023,11,14,tzinfo=timezone.utc).timestamp()*1000)
TARGET_MS=1699961400000

@contextmanager
def source_scope():
    a,b=r3.SYMBOLS,r3.DAYS
    try:
        r3.SYMBOLS,r3.DAYS=c115.original.SYMBOLS,(DATE,)
        yield
    finally:
        r3.SYMBOLS,r3.DAYS=a,b

def compare(symbol, threes, fives):
    if len(threes)!=480 or len(fives)!=288:raise ValueError("UNEXPECTED_PROVIDER_DAILY_BAR_COUNTS")
    if (threes[0].start_ms!=DAY_MS or threes[-1].known_ms!=DAY_MS+86400000 or
        fives[0].open_ms!=DAY_MS or fives[-1].close_ms!=DAY_MS+86400000):
        raise ValueError("NATIVE_SOURCE_CLOCK_MISMATCH")
    outcomes=[]
    for i in range(96):
        x=threes[5*i:5*i+5];y=fives[3*i:3*i+3]
        p=(x[0].start_ms,x[-1].known_ms,x[0].open,
           max(z.high for z in x),min(z.low for z in x),x[-1].close)
        q=(y[0].open_ms,y[-1].close_ms,y[0].o,
           max(z.h for z in y),min(z.l for z in y),y[-1].c)
        if p!=q:
            outcomes.append({
                "symbol":symbol,"index":i,"timestamp_ms":p[0],
                "utc":datetime.fromtimestamp(p[0]/1000,timezone.utc).isoformat(),
                "original_3m_15m_OHLC":[str(z) for z in p[2:]],
                "original_5m_15m_OHLC":[str(z) for z in q[2:]],
                "price_3m_5m_max_abs_difference":str(max(abs(a-b) for a,b in zip(p[2:],q[2:]))),
                "volume_3m":str(sum((z.volume for z in x),D(0))),
                "volume_5m":str(sum((z.volume for z in y),D(0)))})
    return {"symbol":symbol,"15m_count":96,
            "price_mismatch_count":len(outcomes),
            "original_15m_price_mismatches":outcomes}

def run():
    c115.frozen()
    with source_scope():
        def worker(symbol):
            a,ma=r3.daily(symbol,DATE)
            b,mb=r5.daily(symbol,DATE)
            return symbol,ma,mb,compare(symbol,a,b)
        with ThreadPoolExecutor(max_workers=8) as pool:
            parts=list(pool.map(worker,c115.original.SYMBOLS))
    problems=[e for sym,ma,mb,r in parts for e in r["original_15m_price_mismatches"]]
    exact=[e for e in problems if e["timestamp_ms"]==TARGET_MS and
           e["original_3m_15m_OHLC"][1]=="0.11935" and
           e["original_5m_15m_OHLC"][1]=="0.11940"]
    return {
        "type":"C115_ORIGINAL_BINANCE_USDM_FROZEN_DATE_3M5M_CROSS_OHLC_FORENSIC",
        "date":DATE,"symbols":list(c115.original.SYMBOLS),
        "sources":{"3m":[ma for sym,ma,mb,r in parts],"5m":[mb for sym,ma,mb,r in parts]},
        "per_symbol":{sym:r for sym,ma,mb,r in parts},
        "total_mismatched_15m":len(problems),
        "all_price_mismatches":problems[:100],
        "exact_1699961400000_original_price_incident":exact,
        "paper_only":True,"live_approved":False,
        "economic_trades_computed":False,"source_only_block_not_economic_retest":True,
    }
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    b=(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode()
    args.output.write_bytes(b)
    print(json.dumps({"sha256":hashlib.sha256(b).hexdigest(),
                      "source_zip_count":24,"price_mismatches":result["total_mismatched_15m"],
                      "incident":result["exact_1699961400000_original_price_incident"],
                      "live_approved":False},ensure_ascii=False))
