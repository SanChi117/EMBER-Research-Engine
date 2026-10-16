#!/usr/bin/env python3
"""B1/C10 and D05/F06: Oct 1-2 continuous five-symbol 5m original Futures replay.

Two days * five symbols = ten original 5m ZIP/CHECKSUM from Binance;
cross-check 960 native original C08 15m bars, then compare day boundary
1h raid + 5m BOS candidates with source-native and known-at. No orders.
"""
from __future__ import annotations
import csv,io,json,sys,zipfile
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/"tools",ROOT/"tests",ROOT/"d05",ROOT.parent/"mtf-course-v05"/"src"):
    sys.path.insert(0,str(p))
from f03_5m_original_source import download_source_5m,Verified5m,DAY
from c08_source_bound_poi_b1 import _locked_receipt
from verify_d04_full_manifest_c08 import checked_download
from strict_vision_d04 import verify_raw_zip
from c10_two_day_original_5m_context import review_two_day_5m

START=1790812800000
SYMS=("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT")
DATES=("2026-10-01","2026-10-02")
F04=ROOT/"evidence"/"f04"/"F04_FIVE_5M_FUTURES_2026-10-02_RECEIPTS.json"

def fetch_day(symbol,date,start,pinned):
    base=f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/"
    url5=base+f"5m/{symbol}-5m-{date}.zip"
    url15=base+f"15m/{symbol}-15m-{date}.zip"
    five=download_source_5m(url5,40)
    assert five.symbol==symbol and five.day_start_ms==start and len(five.rows)==288
    if pinned is not None:
        assert five.zip_sha256==pinned["original_5m_zip_sha256"]
        assert five.raw_csv_sha256==pinned["original_5m_csv_sha256"]
    rec,info=_locked_receipt(symbol,"15m",start,ROOT/"evidence"/"c08")
    assert rec["url"]==url15
    raw15=checked_download(url15,25_000_000,40)
    cs15=checked_download(url15+".CHECKSUM",1024,40)
    source15=verify_raw_zip(url15,raw15,cs15)
    assert source15["zip_sha256"]==rec["zip_sha256"]
    assert source15["raw_csv_sha256"]==rec["raw_csv_sha256"]
    with zipfile.ZipFile(io.BytesIO(raw15)) as archive:
        with archive.open(info["filename"][:-4]+".csv") as fd:
            items=list(csv.reader(io.TextIOWrapper(fd,encoding="utf-8-sig",newline="")))
    if items[0][0].strip().lower()=="open_time":
        items=items[1:]
    if len(items)!=96:raise AssertionError("INVALID_ORIGINAL_15M_KLINES")
    matched=0
    for n,raw in enumerate(items):
        row5=five.rows[3*n:3*n+3]
        from5=(Decimal(row5[0].original_csv_row[1]),
               max(Decimal(r.original_csv_row[2]) for r in row5),
               min(Decimal(r.original_csv_row[3]) for r in row5),
               Decimal(row5[-1].original_csv_row[4]),
               sum((r.volume for r in row5),Decimal("0")))
        from15=tuple(Decimal(raw[k]) for k in (1,2,3,4,5))
        if (from5!=from15 or row5[0].bar.start!=int(raw[0])
            or row5[-1].bar.end!=int(raw[6])+1):
            raise AssertionError("RAW_5M_15M_PARITY_MISMATCH_"+symbol+"_"+date+"_"+str(n))
        matched+=1
    return five,{
        "date":date,"native_5m_zip_sha256":five.zip_sha256,
        "native_5m_csv_sha256":five.raw_csv_sha256,
        "native_original_c08_15m_zip_sha256":source15["zip_sha256"],
        "native_original_c08_15m_csv_sha256":source15["raw_csv_sha256"],
        "five_minute_rows":len(five.rows),"c08_original_15m_groups_checked":matched,
        "source_status":"HTTPS_CHECKSUM_AND_FULL_C08_15M_CROSSCHECK"
    }

def main(outpath=None):
    receipt=json.loads(F04.read_text(encoding="utf8"))
    if receipt["schema"]!="EMBER_D05_F04_FIVE_ORIGINAL_5M_BINANCE_FUTURES_RECEIPTS_V1":
        raise AssertionError("F04_RECEIPT_NOT_PINNED_SCHEMA")
    per={r["symbol"]:r for r in receipt["sources"]}
    assert set(per)==set(SYMS)
    new=json.loads((ROOT/"evidence"/"f06"/"F06_FIVE_SYMBOL_TWO_DAY_5M_SOURCE_RECEIPTS.json").read_text(encoding="utf8"))
    assert new["schema"]=="EMBER_B1_C10_TWO_CONSECUTIVE_DAYS_FIVE_SYMBOL_ORIGINAL_5M_RECEIPTS_V1"
    assert new["readiness"]=="NOT_TRADE_READY" and new["academy_entry_approved"]==0
    frozen={(x["symbol"],x["date"]):x for x in new["source_days"]}
    assert len(frozen)==10
    results=[]
    for symbol in SYMS:
        days=[]
        proofs=[]
        for n,date in enumerate(DATES):
            five,proof=fetch_day(symbol,date,START+n*DAY,per[symbol] if n==1 else None)
            fixed=frozen[(symbol,date)]
            assert proof["native_5m_zip_sha256"]==fixed["original_5m_zip_sha256"]
            assert proof["native_5m_csv_sha256"]==fixed["original_5m_csv_sha256"]
            assert proof["native_original_c08_15m_zip_sha256"]==fixed["c08_original_15m_zip_sha256"]
            assert proof["native_original_c08_15m_csv_sha256"]==fixed["c08_original_15m_csv_sha256"]
            days.append(five);proofs.append(proof)
        atmid=review_two_day_5m(days[0],days[1],START+DAY)
        whole=review_two_day_5m(days[0],days[1],START+2*DAY)
        assert atmid.closed_5m_count==288 and atmid.closed_1h_count==24
        assert whole.closed_5m_count==576 and whole.closed_1h_count==48
        assert whole.readiness=="NOT_TRADE_READY"
        results.append({
           "symbol":symbol,"original_days":proofs,
           "whole_2d_source_5m_rows":whole.closed_5m_count,
           "whole_2d_1h_bars":whole.closed_1h_count,
           "before_midnight_1h_raid_candidates":atmid.confirmed_1h_raids,
           "after_48h_1h_raid_candidates":whole.confirmed_1h_raids,
           "after_48h_5m_bos_candidates":len(whole.source_raid_bos),
           "bos_witnesses":[{
             "source_id":b.original_bar_id,"parent_raid":b.raid_id,
             "raid_known":b.raid_known,"bos_known":b.bos_known,
             "zip_sha256":b.original_day_zip_sha256
           } for b in whole.source_raid_bos],
           "academy_stronghl_vc_approved":False,"readiness":"NOT_TRADE_READY"
        })
    q={
       "cycle":"B1_C10_F06_5_SYMBOL_2_CONSECUTIVE_ORIGINAL_5M_DAYS",
       "market":"BINANCE_USDM_FUTURES","dates":list(DATES),
       "symbols":list(SYMS),"original_5m_archives":10,
       "original_5m_bars":sum(r["whole_2d_source_5m_rows"] for r in results),
       "original_15m_c08_ohlcv_equal_groups":sum(sum(
            p["c08_original_15m_groups_checked"] for p in r["original_days"])
            for r in results),
       "complete_1h_bars":sum(r["whole_2d_1h_bars"] for r in results),
       "results":results,
       "unchanged_original_315_c08_archive_set":True,
       "academic_vc_certified":False,"approved_trades":0,
       "readiness":"NOT_TRADE_READY",
       "limitations":"2 days, 5 symbols, same-host CHECKSUM not publisher digital signature; v05 fractal and freshness thresholds unapproved"
    }
    assert q["original_5m_bars"]==2880
    assert q["original_15m_c08_ohlcv_equal_groups"]==960
    assert q["complete_1h_bars"]==240
    print(json.dumps(q,sort_keys=True,indent=2))
    if outpath:Path(outpath).write_text(json.dumps(q,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0
if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
