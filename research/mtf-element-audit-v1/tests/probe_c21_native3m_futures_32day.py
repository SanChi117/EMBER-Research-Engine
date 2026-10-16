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
