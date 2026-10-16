#!/usr/bin/env python3
"""Independent original 2026-09 MONTHLY+Oct1/2 DAILY native USD-M 5m sources.

Re-download each same-host SHA CHECKSUM + ZIP (15 new native 5m originals),
plus the 30 unmodified frozen C08 original 15m and 1d archives.
Crosscheck all 3,072 native 15m OHLCV against 9,216 native 5m Decimal triples
per symbol. No author-labelled 1H raid / BOS signals or live trades.
"""
from __future__ import annotations
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for d in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):sys.path.insert(0,str(d))
from verify_d04_full_manifest_c08 import checked_download
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c20_original_32day_native5m_lineage import (
    parse_original_native5m,reconcile_32day_native5m)

def original_5m(symbol,period):
    group="monthly" if period=="2026-09" else "daily"
    url=f"https://data.binance.vision/data/futures/um/{group}/klines/{symbol}/5m/{symbol}-5m-{period}.zip"
    binary=checked_download(url,25_000_000,40)
    checksum=checked_download(url+".CHECKSUM",1024,40)
    a=parse_original_native5m(url,binary,checksum,symbol=symbol,period=period)
    assert a.symbol==symbol and a.readiness=="NOT_TRADE_READY"
    return a,{"date":period,"url":url,"original_zip_sha256":a.zip_sha256,
              "original_raw_csv_sha256":a.raw_csv_sha256,"rows":len(a.rows)}

def main(output=None):
    result=[]
    for symbol in SYMS:
        old={}
        for tf in ("15m","1d"):
            old[tf]=tuple(load_original(symbol,tf,date,start)[0]
                          for date,start in zip(DATES,STARTS))
        original=extended_32day_prefix(old["15m"],old["1d"],END)
        fresh=[original_5m(symbol,p) for p in DATES]
        pieces=tuple(x[0] for x in fresh)
        full=reconcile_32day_native5m(pieces,original,as_of_ms=END)
        cut=OCT_START+DAY+300_000
        earlier=reconcile_32day_native5m(pieces,original,as_of_ms=cut)
        assert earlier.original_5m_closed==full.original_5m_closed[:len(earlier.original_5m_closed)]
        assert len(earlier.original_5m_closed)==31*288+1
        assert len(full.original_5m_closed)==32*288==9216
        assert full.original_15m_equalities==3072 and full.verified_original_1d_equalities==32
        assert full.author_source_status=="AUTHOR_GOLDEN_SOURCE_UNAVAILABLE"
        assert full.readiness=="NOT_TRADE_READY" and full.bos_status=="BOS_5M_NOT_YET_AUTHOR_CERTIFIED"
        row={"symbol":symbol,"source_5m":list(x[1] for x in fresh),
             "native_5m_rows":len(full.original_5m_closed),
             "exact_native_15m_equalities":full.original_15m_equalities,
             "original_native_1d_equalities":full.verified_original_1d_equalities,
             "known_asof_2026_oct2_0005_utc":len(earlier.original_5m_closed),
             "no_future_suffix_leak":True,"author_approved_bos":0,
             "author_approved_trade":0}
        result.append(row)
        print(f"{symbol}: 3 verified new 5m originals; 9216 native 5m -> 3072 original C08 15m OHLCV exact, native daily=32",flush=True)
    report={"cycle":"B1_C20A_ORIGINAL_MONTHLY_DAILY_32DAY_5M_SOURCE_LINEAGE",
            "market":"BINANCE_USDM_FUTURES",
            "period_utc":["2026-09-01","2026-10-02"],
            "new_original_native_5m_archives":15,
            "previous_original_C08_15m_1d_archives":30,
            "total_native_zip_sources_checked":45,
            "native_5m_rows":sum(x["native_5m_rows"] for x in result),
            "exact_native_15m_decimal_ohlcv_equalities":sum(x["exact_native_15m_equalities"] for x in result),
            "original_native_1d_parities":sum(x["original_native_1d_equalities"] for x in result),
            "observations":result,
            "author_golden_source_status":"AUTHOR_GOLDEN_SOURCE_UNAVAILABLE",
            "bos_source_status":"BOS_5M_NOT_YET_AUTHOR_CERTIFIED",
            "trades":0,"readiness":"NOT_TRADE_READY",
            "limitations":"Only 5m source and exact cross-timeframe OHLCV parity; no 3m archive; 1H Raid->5m BOS course geometry not yet independently author-labelled; no trade execution or win-rate."}
    assert len(result)==5 and report["native_5m_rows"]==46080
    assert report["exact_native_15m_decimal_ohlcv_equalities"]==15360
    assert report["original_native_1d_parities"]==160
    path=ROOT/"evidence"/"c20"/"C20_ORIGINAL_5M_32DAY_LINEAGE_RESULT.json"
    if path.is_file():
        fixed=json.loads(path.read_text(encoding="utf8"))
        assert fixed["schema"]=="EMBER_B1_C20_ORIGINAL_MONTHLY_DAILY_5M_NATIVE_15M_PARITY_V1"
        assert fixed["observations"]==report["observations"],"PINNED_NATIVE_5M_SOURCE_CHANGED"
        assert fixed["new_original_native_5m_archives"]==15
        assert fixed["native_5m_rows"]==46080
        assert fixed["exact_native_15m_decimal_ohlcv_equalities"]==15360
        assert fixed["original_native_1d_parities"]==160
        assert fixed["author_approved_trade"]==fixed["author_approved_bos"]==0
        assert fixed["readiness"]=="NOT_TRADE_READY"
    if output:Path(output).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    return 0
if __name__=="__main__":raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
