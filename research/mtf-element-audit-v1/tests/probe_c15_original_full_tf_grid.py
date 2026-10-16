#!/usr/bin/env python3
"""B1/C15: ten original native 5m vs ten native C08 15m, derive 1h/4h/1d.

15m is ORIGINAL Binance USD-M archive independently source and SHA checked;
1h, 4h and 1d are strictly DERIVED from original native 15m and original 5m
(no claim of native 1d/4h archives). ALL are CLOSED with exact Decimal OHLCV.
Two days do not certify author HTF context or any market setup. PAPER ONLY.
"""
from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
for mod in (ROOT/"d05",ROOT/"tools",ROOT/"tests",ROOT.parent/"mtf-course-v05"/"src"):
    sys.path.insert(0,str(mod))

from f03_5m_original_source import download_source_5m,DAY
from c15_closed_multi_tf_source_grid import closed_mtf_prefix
from c08_source_bound_poi_b1 import _locked_receipt
from verify_d04_full_manifest_c08 import checked_download
from strict_vision_d04 import verify_raw_zip

F06=ROOT/"evidence"/"f06"/"F06_FIVE_SYMBOL_TWO_DAY_5M_SOURCE_RECEIPTS.json"
START={"2026-10-01":1790812800000,"2026-10-02":1790899200000}
COUNTS={"5m":576,"15m":192,"1h":48,"4h":12,"1d":2}
WIDTHS={"15m":1,"1h":4,"4h":16,"1d":96}
DURATION={"15m":900000,"1h":3600000,"4h":14400000,"1d":DAY}

def original_native_15m(symbol,date,utc_start,expected):
    url=f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/15m/{symbol}-15m-{date}.zip"
    native,meta=_locked_receipt(symbol,"15m",utc_start,ROOT/"evidence"/"c08")
    if native["url"]!=url:
        raise AssertionError("WRONG_PREVIOUSLY_ATTESTED_C08_URL")
    raw=checked_download(url,25_000_000,40)
    checksum=checked_download(url+".CHECKSUM",1024,40)
    matched=verify_raw_zip(url,raw,checksum)
    for field,want in (("zip_sha256",expected["c08_original_15m_zip_sha256"]),
                       ("raw_csv_sha256",expected["c08_original_15m_csv_sha256"])):
        if matched[field]!=want or matched[field]!=native[field]:
            raise AssertionError("C08_ORIGINAL_15M_SHA_CHANGED_"+symbol+"_"+date)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        with z.open(meta["filename"][:-4]+".csv") as file:
            arr=list(csv.reader(io.TextIOWrapper(file,encoding="utf-8-sig",newline="")))
    if arr and arr[0][0].strip().lower()=="open_time":arr=arr[1:]
    if len(arr)!=96:
        raise AssertionError("C08_NATIVE_15M_NOT_COMPLETE_UTC_DAY")
    items=[]
    for n,v in enumerate(arr):
        if len(v)!=12 or int(v[0])!=utc_start+n*900000 or int(v[6])!=utc_start+(n+1)*900000-1:
            raise AssertionError("C08_NATIVE_15M_WRONG_UTC_GRID")
        values=tuple(Decimal(v[k]) for k in (1,2,3,4,5))
        items.append((int(v[0]),int(v[6])+1,*values))
    return items,matched["zip_sha256"]

def native_15m_to_derived(items,width,tf):
    result=[]
    duration=DURATION[tf]
    for i in range(len(items)//width):
        chunk=items[width*i:width*(i+1)]
        start,end=chunk[0][0],chunk[-1][1]
        if start%duration or end!=start+duration:
            raise AssertionError("NATIVE_15M_INCORRECT_AGGREGATE_BOUNDARY")
        result.append((start,end,chunk[0][2],
                       max(x[3] for x in chunk),min(x[4] for x in chunk),
                       chunk[-1][5],sum((x[6] for x in chunk),Decimal(0))))
    return result

def main(output_file=None):
    r=json.loads(F06.read_text(encoding="utf8"))
    assert r["schema"]=="EMBER_B1_C10_TWO_CONSECUTIVE_DAYS_FIVE_SYMBOL_ORIGINAL_5M_RECEIPTS_V1"
    assert r["readiness"]=="NOT_TRADE_READY" and r["academy_entry_approved"]==0
    assert len(r["source_days"])==10 and r["source_ohlcv_native_c08_15m_groups_equal"]==960
    result=[]
    for symbol in r["symbols"]:
        five_days=[]
        native15=[]
        proof_days=[]
        for day in r["dates"]:
            expected=next(x for x in r["source_days"] if x["symbol"]==symbol and x["date"]==day)
            base=f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/5m/{symbol}-5m-{day}.zip"
            p=download_source_5m(base,40)
            if (p.symbol!=symbol or p.day_start_ms!=START[day]
                or p.zip_sha256!=expected["original_5m_zip_sha256"]
                or p.raw_csv_sha256!=expected["original_5m_csv_sha256"]):
                raise AssertionError("ORIGINAL_5M_SOURCE_SHA_CHANGED_"+symbol+"_"+day)
            rows,original_15m_zip_sha=original_native_15m(symbol,day,START[day],expected)
            five_days.append(p)
            native15.extend(rows)
            proof_days.append({"day":day,"original_5m_zip_sha256":p.zip_sha256,
                               "original_15m_zip_sha256":original_15m_zip_sha})
        grid=closed_mtf_prefix(five_days[0],five_days[1],START["2026-10-02"]+DAY)
        assert grid.daily_coverage=="TWO_DAILY_CANDLES_INSUFFICIENT_AUTHOR_HTF_CONTEXT"
        assert grid.readiness=="NOT_TRADE_READY"
        # Two independent source streams: 5m source and native 15m source.
        verified_counts={}
        for tf,width in WIDTHS.items():
            from_15m=native_15m_to_derived(native15,width,tf)
            from_5m=grid.candles(tf)
            if len(from_15m)!=len(from_5m) or len(from_5m)!=COUNTS[tf]:
                raise AssertionError("DIFFERENT_NATIVE_SOURCE_TIMEFRAME_COUNTS_"+tf)
            for source,derived in zip(from_15m,from_5m):
                obs=(derived.start_ms,derived.known_at_ms,derived.open,
                     derived.high,derived.low,derived.close,derived.volume)
                if source!=obs:
                    raise AssertionError("NATIVE_15M_C08_VS_ORIGINAL_5M_OHLCV_MISMATCH_"+symbol+"_"+tf)
                if len(derived.source_5m_ids)!=DURATION[tf]//300000:
                    raise AssertionError("MISSING_RAW_BAR_SOURCE_LINEAGE_"+tf)
            verified_counts[tf]=len(from_15m)
        # Past as_of cannot see the next 1D close or unfinished 4h.
        past=closed_mtf_prefix(*five_days,START["2026-10-02"]+3600000)
        assert len(past.candles("1d"))==1
        assert len(past.candles("4h"))==6
        assert len(past.candles("1h"))==25
        result.append({
            "symbol":symbol,"source_5m_candles":len(grid.candles("5m")),
            "matched_native_15m_and_derived_tf_ohlcv":verified_counts,
            "first_1d_count_as_of_second_day_plus_1h":len(past.candles("1d")),
            "source_receipts":proof_days,"author_1d_4h_poi_context_certified":False,
            "readiness":"NOT_TRADE_READY"
        })
    totals={tf:sum(one["matched_native_15m_and_derived_tf_ohlcv"][tf] for one in result)
            for tf in WIDTHS}
    summary={
        "cycle":"B1_C15_FUTURES_TWO_DAY_NATIVE_15M_DERIVED_1D_4H_1H_GRID",
        "source_market":"BINANCE_USDM_FUTURES","symbols":r["symbols"],"days":r["dates"],
        "source_5m_zip_archives":10,"source_native_15m_c08_zip_archives":10,
        "raw_original_5m_bars":sum(x["source_5m_candles"] for x in result),
        "original_15m_parity_checks":totals["15m"],
        "derived_1h_vs_original_15m_checks":totals["1h"],
        "derived_4h_vs_original_15m_checks":totals["4h"],
        "derived_1d_vs_original_15m_checks":totals["1d"],
        "all_timeframe_ohlcv_checks":sum(totals.values()),
        "native_1d_4h_archive_claims":0,
        "author_goldens_for_1d_4h_source_context":0,"trade_ready":False,
        "observations":result,
        "scope_limit":"All 1d/4h/1h candles DERIVED, not native 1d/4h/1h Binance ZIPs. Two days cannot establish author HTF POI, FTA or complete daily structure. Same-host .CHECKSUM is not independent publisher signature."
    }
    assert summary["raw_original_5m_bars"]==2880
    assert [totals[t] for t in WIDTHS]==[960,240,60,10]
    assert summary["all_timeframe_ohlcv_checks"]==1270
    receipt=json.loads((ROOT/"evidence"/"c15"/"C15_F06_5M_NATIVE_15M_DERIVED_1D_4H_SOURCE_RECEIPT.json").read_text(encoding="utf8"))
    assert receipt["schema"]=="EMBER_B1_C15_ORIGINAL_5M_NATIVE_C08_15M_DERIVED_MTF_PRICE_GRID_V1"
    assert receipt["preserved_f06_source_receipt_blob"]=="a5bf2105d1c611517a8d127d5e1f8cb622720162"
    assert receipt["preserved_c08_archive_aggregate_blob"]=="4205ad3118a30bbd69c412e165c7c5ce3560195d"
    assert receipt["original_5m_zip_count"]==summary["source_5m_zip_archives"]==10
    assert receipt["original_native_15m_c08_zip_count"]==summary["source_native_15m_c08_zip_archives"]==10
    assert receipt["original_5m_bars"]==summary["raw_original_5m_bars"]==2880
    assert receipt["total_exact_ohlcv_equalities"]==summary["all_timeframe_ohlcv_checks"]==1270
    assert receipt["independently_crosschecked_closed_tf_candles"]==totals
    assert receipt["native_higher_tf_1d_4h_1h_zip_claims"]==0
    assert receipt["academic_author_labelled_daily_parent_poi"]==0
    assert receipt["academic_entry_ready"]==0 and receipt["readiness"]=="NOT_TRADE_READY"
    for case,review in zip(receipt["observations"],summary["observations"]):
        assert case["symbol"]==review["symbol"]
        assert case["full_prefix_closed_candles"]==review["matched_native_15m_and_derived_tf_ohlcv"]
        assert case["closed_daily_count_at_second_day_plus_1h"]==review["first_1d_count_as_of_second_day_plus_1h"]==1
        assert case["author_1d_4h_poi_context_certified"] is False
    for frozen in receipt["source_days"]:
        previous=next(x for x in r["source_days"] if x["symbol"]==frozen["symbol"] and x["date"]==frozen["date"])
        for a,b in (("original_5m_zip_sha256","original_5m_zip_sha256"),
                    ("original_5m_csv_sha256","original_5m_csv_sha256"),
                    ("original_15m_zip_sha256","c08_original_15m_zip_sha256"),
                    ("original_15m_csv_sha256","c08_original_15m_csv_sha256")):
            assert frozen[a]==previous[b]
    print(json.dumps(summary,indent=2,sort_keys=True))
    if output_file:Path(output_file).write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
