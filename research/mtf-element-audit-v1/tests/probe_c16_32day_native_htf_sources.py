#!/usr/bin/env python3
"""C16 independent 32-day source replay: Sept monthly and Oct1-2 daily C08.

30 original Binance USD-M Futures archives, each full D04 ZIP+CSV SHA
checked against previous immutable C08 receipts. Source types native 15m
AND native 1d, derive 1h and 4h and compare 160 native 1d exact OHLCV.
Never claim certified HTF academic POI, volume strategy or live orders.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for d in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):
    sys.path.insert(0,str(d))
from c08_source_bound_poi_b1 import _locked_receipt
from verify_d04_full_manifest_c08 import checked_download
from c16_c08_monthly_daily_htf_lineage import (
 c08_bound_archive,extended_32day_prefix,SEPT_START,OCT_START,END,DAY)
EVIDENCE=ROOT/"evidence"/"c08"
SYMS=("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT")
DATES=("2026-09","2026-10-01","2026-10-02")
STARTS=(SEPT_START,OCT_START,OCT_START+DAY)

def load_original(symbol,tf,date,start):
    receipt,info=_locked_receipt(symbol,tf,start,EVIDENCE)
    expected=f"https://data.binance.vision/data/futures/um/"+(
        "monthly" if date=="2026-09" else "daily"
    )+f"/klines/{symbol}/{tf}/{symbol}-{tf}-{date}.zip"
    assert info["url"]==expected and receipt["url"]==expected
    blob=checked_download(expected,25_000_000,40)
    remote=checked_download(expected+".CHECKSUM",1024,40)
    obj=c08_bound_archive(expected,blob,remote,receipt)
    assert obj.archive_url==expected and obj.symbol==symbol and obj.tf==tf
    assert obj.zip_sha256==receipt["zip_sha256"]
    assert obj.raw_csv_sha256==receipt["raw_csv_sha256"]
    return obj,{"tf":tf,"date":date,"source_url":expected,
                "zip_sha256":obj.zip_sha256,"raw_csv_sha256":obj.raw_csv_sha256,
                "native_rows":len(obj.rows)}

def main(out=None):
    observations=[]
    for symbol in SYMS:
        pieces={}
        sources=[]
        for tf in ("15m","1d"):
            proof=[]
            for date,start in zip(DATES,STARTS):
                item,origin=load_original(symbol,tf,date,start)
                proof.append(item)
                sources.append(origin)
            pieces[tf]=tuple(proof)
        review=extended_32day_prefix(pieces["15m"],pieces["1d"],END)
        assert review.symbol==symbol
        assert review.crosschecked_native_1d==32
        assert len(review.native_15m_closed)==3072
        assert len(review.derived_1h_closed)==768
        assert len(review.derived_4h_closed)==192
        assert len(review.native_1d_closed)==32
        assert review.readiness=="NOT_TRADE_READY"
        # Exact as-of: Oct2 1AM can use Oct1 closed daily but NOT Oct2.
        mid=extended_32day_prefix(pieces["15m"],pieces["1d"],OCT_START+DAY+3600000)
        assert mid.crosschecked_native_1d==31
        assert len(mid.derived_4h_closed)==186
        assert mid.native_1d_closed[-1].known_at_ms==OCT_START+DAY
        observations.append({
          "symbol":symbol,
          "original_futures_sources":sources,
          "original_native_15m_bars":len(review.native_15m_closed),
          "derived_closed_1h_bars":len(review.derived_1h_closed),
          "derived_closed_4h_bars":len(review.derived_4h_closed),
          "verified_native_1d_bars":review.crosschecked_native_1d,
          "earlier_asof_second_oct_plus_1h_native_1d_count":mid.crosschecked_native_1d,
          "author_1d_4h_poi_approved":False,
          "readiness":"NOT_TRADE_READY"
        })
        print(f"{symbol}: 6 verified C08 archives, 32 native 1d matched to 15m, 192 derived 4h",flush=True)
    result={
      "cycle":"B1_C16_NATIVE_C08_32_CONSECUTIVE_UTC_DAYS_HTF",
      "source_market":"BINANCE_USDM_FUTURES",
      "original_15m_sources":15,
      "original_1d_sources":15,
      "source_15m_native_bars":sum(x["original_native_15m_bars"] for x in observations),
      "derived_1h_bars":sum(x["derived_closed_1h_bars"] for x in observations),
      "derived_4h_bars":sum(x["derived_closed_4h_bars"] for x in observations),
      "crosschecked_original_native_1d_bars":sum(x["verified_native_1d_bars"] for x in observations),
      "symbols":list(SYMS),
      "period_utc":["2026-09-01","2026-10-02"],
      "continuous_days_per_symbol":32,
      "observations":observations,
      "provenance":"ALL_30_SEPARATE_BINANCE_USDM_NATIVE_15M_AND_NATIVE_1D_ZIPS_CHECKED_WITH_SAME_HOST_CHECKSUM_AND_ORIGINAL_FROZEN_C08_RECEIPTS",
      "limitations":"32 days is longer HTF price context, but no author labels for 1d/4h POI, no native 4h archive and no author-golden StrongHL/VC, same-host CHECKSUM not external signature",
      "author_approved_stronghl":0,"author_approved_vc":0,"author_approved_trades":0,
      "readiness":"NOT_TRADE_READY"
    }
    assert result["source_15m_native_bars"]==15360
    assert result["derived_1h_bars"]==3840
    assert result["derived_4h_bars"]==960
    assert result["crosschecked_original_native_1d_bars"]==160
    fixed=json.loads((ROOT/"evidence"/"c16"/"C16_32DAY_NATIVE_15M_1D_RECEIPT.json").read_text(encoding="utf8"))
    assert fixed["schema"]=="EMBER_B1_C16_NATIVE_C08_SEP2026_MONTH_PLUS_OCT2_SOURCE_MTF_V1"
    assert fixed["original_c08_receipts_git_blob"]=="4205ad3118a30bbd69c412e165c7c5ce3560195d"
    assert fixed["required_sources"]==30
    assert fixed["original_native_15m_sources"]==result["original_15m_sources"]==15
    assert fixed["original_native_1d_sources"]==result["original_1d_sources"]==15
    assert fixed["days_per_symbol"]==result["continuous_days_per_symbol"]==32
    assert fixed["original_native_15m_candles"]==result["source_15m_native_bars"]==15360
    assert fixed["derived_1h_candles"]==result["derived_1h_bars"]==3840
    assert fixed["derived_4h_candles"]==result["derived_4h_bars"]==960
    assert fixed["independent_native_1d_decimal_ohlcv_equalities"]==result["crosschecked_original_native_1d_bars"]==160
    assert fixed["trade_approved"]==fixed["author_approved_vc"]==fixed["author_approved_stronghl"]==0
    assert fixed["author_approved_1d_4h_poi"]==0 and fixed["readiness"]=="NOT_TRADE_READY"
    for observed,pinned in zip(result["observations"],fixed["sources"]):
        assert pinned["symbol"]==observed["symbol"]
        assert pinned["sources"]==observed["original_futures_sources"]
        assert pinned["original_native_15m_bars"]==observed["original_native_15m_bars"]
        assert pinned["derived_closed_1h_bars"]==observed["derived_closed_1h_bars"]
        assert pinned["derived_closed_4h_bars"]==observed["derived_closed_4h_bars"]
        assert pinned["exact_matched_native_1d_bars"]==observed["verified_native_1d_bars"]
        assert pinned["asof_oct2_01_native1d_count"]==observed["earlier_asof_second_oct_plus_1h_native_1d_count"]==31
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    if out:Path(out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0
if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
