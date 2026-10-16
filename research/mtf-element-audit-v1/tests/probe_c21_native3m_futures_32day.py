#!/usr/bin/env python3
"""C21A independent 15 new original 3m + 30 pinned C08 USD-M ZIP sources.

All 76,800 native 3m bars must reconstruct all 15,360 C08 native 15m
OHLCV exactly. No academic author 3m BOS label / trade is inferred.
"""
from __future__ import annotations
import json,sys,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):sys.path.insert(0,str(p))
from strict_vision_d04 import _SingleHostRedirect
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import (
    checked_url,verified_name,read_original_3m,reconcile_native_3m,
    PERIODS,THREE)

def native_3m(symbol,period):
    url=checked_url(symbol,period)
    verified_name(url,symbol,period)
    opener=urllib.request.build_opener(_SingleHostRedirect())
    def get(target,limit):
        with opener.open(urllib.request.Request(target,headers={
            "User-Agent":"EMBER-C21A-original-3m-read-only/1.0"}),timeout=40) as r:
            final=urllib.parse.urlsplit(r.geturl())
            if final.scheme!="https" or final.netloc!="data.binance.vision":
                raise RuntimeError("FORBIDDEN_ORIGINAL_3M_REDIRECT")
            data=r.read(limit+1)
        if not 0<len(data)<=limit:raise RuntimeError("MISSING_OR_OVERSIZE_SOURCE_3M")
        return data
    checksum=get(url+".CHECKSUM",1024)
    original_zip=get(url,30000000)
    x=read_original_3m(url,original_zip,checksum,symbol=symbol,period=period)
    return x,{"period":period,"url":url,"original_zip_sha256":x.zip_sha,
              "original_csv_sha256":x.csv_sha,"original_native_3m_rows":len(x.rows)}

def main(path=None):
    out=[]
    for symbol in SYMS:
        native={}
        for tf in ("15m","1d"):
            native[tf]=tuple(load_original(symbol,tf,d,start)[0]
                             for d,start in zip(DATES,STARTS))
        original15=extended_32day_prefix(native["15m"],native["1d"],END)
        fresh=[native_3m(symbol,p) for p in PERIODS]
        source=tuple(x[0] for x in fresh)
        full=reconcile_native_3m(source,original15,as_of_ms=END)
        cut=OCT_START+DAY+THREE
        earlier=reconcile_native_3m(source,original15,as_of_ms=cut)
        assert len(earlier.original_3m_closed)==31*480+1
        assert earlier.original_3m_closed==full.original_3m_closed[:len(earlier.original_3m_closed)]
        assert len(full.original_3m_closed)==15360
        assert full.native_15m_ohlcv_equalities==3072 and full.native_1d_equalities==32
        assert full.author_bos_approved==full.trade_approved==0
        assert full.readiness=="NOT_TRADE_READY"
        out.append({
            "symbol":symbol,
            "native_3m_closed":len(full.original_3m_closed),
            "exact_3m_to_c08_native15m_ohlcv":full.native_15m_ohlcv_equalities,
            "original_native1d_equalities":full.native_1d_equalities,
            "asof_prefix_stable":True,
            "new_original_source_zip":list(y[1] for y in fresh),
            "author_bos_approved":0,"trades":0
        })
        print(f"{symbol}: 15360 original 3m -> 3072 exact C08 15m",flush=True)
    result={
        "schema":"EMBER_C21A_ORIGINAL_BINANCE_USDM_3M_32DAY_NATIVE15M_PARITY_V1",
        "period_utc":["2026-09-01","2026-10-02"],
        "new_original_3m_zip_count":15,
        "previous_C08_original_zip_count":30,
        "verified_total_original_zip_count":45,
        "native_3m_closed":sum(x["native_3m_closed"] for x in out),
        "original_15m_decimal_equalities":sum(x["exact_3m_to_c08_native15m_ohlcv"] for x in out),
        "native_1d_equalities":sum(x["original_native1d_equalities"] for x in out),
        "observations":out,
        "author_3m_bos_goldens":0,
        "author_approved_trades":0,
        "readiness":"NOT_TRADE_READY",
        "limitations":"Original 3m price lineage only; no author-annotated BOS pivot, FTA, session timezone, 3m trade entry, or PNL."
    }
    assert result["native_3m_closed"]==76800
    assert result["original_15m_decimal_equalities"]==15360
    assert result["native_1d_equalities"]==160
    pinned=ROOT/"evidence"/"c21"/"C21A_NATIVE3M_C08_PARITY_RECEIPT.json"
    if pinned.exists():
        expected=json.loads(pinned.read_text(encoding="utf8"))
        assert expected==result,"PINNED_ORIGINAL_3M_SOURCE_COUNT_DRIFT"
    if path:Path(path).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    return 0

if __name__=="__main__":raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
