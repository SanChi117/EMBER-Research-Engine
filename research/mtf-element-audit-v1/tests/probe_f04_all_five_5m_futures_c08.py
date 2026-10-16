#!/usr/bin/env python3
"""D05/F04: all five C08 symbols, original daily 5m vs original 15m OHLCV.

Only Oct 2 2026; no 5m source existed in frozen C08, so F04 is separate.
Reports geometry from original v05 as provisional (not academy certified).
"""
from __future__ import annotations
import csv,io,json,sys,zipfile
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/"tools",ROOT/"tests",ROOT/"d05",ROOT.parent/"mtf-course-v05"/"src"):
    sys.path.insert(0,str(p))
from strict_vision_d04 import verify_raw_zip
from verify_d04_full_manifest_c08 import checked_download
from c08_source_bound_poi_b1 import _locked_receipt
from f03_5m_original_source import download_source_5m,source_5m_imbs
from c09_source_5m_raid_bos_geometry import inspect_source_raid_bos_5m

SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT")
DAY=1790899200000
DATE="2026-10-02"
F03_RECEIPT=ROOT/"evidence"/"f03"/"F03_BTCUSDT_5M_2026-10-02_ORIGINAL_RECEIPT.json"
def run_one(symbol):
    base=f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/"
    url5=base+f"5m/{symbol}-5m-{DATE}.zip"
    url15=base+f"15m/{symbol}-15m-{DATE}.zip"
    source5=download_source_5m(url5)
    receipt15,info=_locked_receipt(symbol,"15m",DAY,ROOT/"evidence"/"c08")
    assert receipt15["url"]==url15
    raw=checked_download(url15,25_000_000,40)
    checksum=checked_download(url15+".CHECKSUM",1024,40)
    proof15=verify_raw_zip(url15,raw,checksum)
    assert proof15["zip_sha256"]==receipt15["zip_sha256"]
    assert proof15["raw_csv_sha256"]==receipt15["raw_csv_sha256"]
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        with archive.open(info["filename"][:-4]+".csv") as handle:
            records=list(csv.reader(io.TextIOWrapper(handle,encoding="utf-8-sig",newline="")))
    if records[0][0].lower()=="open_time":records=records[1:]
    assert len(source5.rows)==288 and len(records)==96
    matches=0
    for idx,rawbar in enumerate(records):
        three=source5.rows[3*idx:3*idx+3]
        from5=(Decimal(three[0].original_csv_row[1]),
               max(Decimal(t.original_csv_row[2]) for t in three),
               min(Decimal(t.original_csv_row[3]) for t in three),
               Decimal(three[-1].original_csv_row[4]),
               sum((t.volume for t in three),Decimal("0")))
        from15=tuple(Decimal(rawbar[i]) for i in (1,2,3,4,5))
        if from5!=from15 or three[0].bar.start!=int(rawbar[0]) or three[-1].bar.end!=int(rawbar[6])+1:
            raise AssertionError(f"ORIGINAL_5M_15M_OHLCV_MISMATCH_{symbol}_{idx}")
        matches+=1
    if symbol=="BTCUSDT":
        old=json.loads(F03_RECEIPT.read_text(encoding="utf8"))
        assert old["original_zip_sha256"]==source5.zip_sha256
        assert old["original_raw_csv_sha256"]==source5.raw_csv_sha256
    geometry=inspect_source_raid_bos_5m(source5,DAY+86400000)
    classic=source_5m_imbs(source5,DAY+86400000)
    assert geometry.five_minute_closed_count==288
    assert geometry.hourly_closed_count==24
    assert matches==96 and geometry.readiness=="NOT_TRADE_READY"
    return {
       "symbol":symbol,"date":DATE,
       "original_5m_url":url5,
       "original_5m_zip_sha256":source5.zip_sha256,
       "original_5m_csv_sha256":source5.raw_csv_sha256,
       "original_15m_c08_url":url15,
       "original_15m_c08_zip_sha256":proof15["zip_sha256"],
       "source_5m_rows":288,"source_15m_rows":96,
       "exact_ohlcv_5m_to_15m_match_count":matches,
       "5m_classic_imb_candidate_count":len(classic),
       "1h_closed_from_5m":geometry.hourly_closed_count,
       "1h_v05_liquidity_raid_candidate_count":geometry.hourly_raid_candidates,
       "5m_v05_bos_after_raid_candidate_count":geometry.five_minute_bos_candidates,
       "academy_5m_volume_confirmation_certified":False,
       "academy_raid_bos_certified":False,
       "readiness":"NOT_TRADE_READY"
    }
def main(outpath=None):
    rows=[run_one(s) for s in SYMBOLS]
    q={
       "cycle":"D05_F04_FIVE_SYMBOLS_ONE_DAY_ORIGINAL_5M_SOURCE",
       "market":"BINANCE_USDM_FUTURES","utc_date":DATE,
       "symbols":list(SYMBOLS),"verified_5m_archives":len(rows),
       "native_original_5m_rows":sum(x["source_5m_rows"] for x in rows),
       "independent_original_c08_15m_rows":sum(x["source_15m_rows"] for x in rows),
       "exact_15m_ohlcv_groups_checked":sum(x["exact_ohlcv_5m_to_15m_match_count"] for x in rows),
       "source_results":rows,
       "original_frozen_c08_315_unchanged":True,
       "academic_5m_vc_signals":0,"trade_ready":False,
       "status":"INDEPENDENT_5_SYMBOL_5M_PRICE_SOURCE_NOT_ACADEMIC_ROUTE"
    }
    print(json.dumps(q,sort_keys=True,indent=2))
    if outpath:Path(outpath).write_text(json.dumps(q,sort_keys=True,indent=2)+"\n",encoding="utf8")
    assert q["verified_5m_archives"]==5
    assert q["native_original_5m_rows"]==1440
    assert q["exact_15m_ohlcv_groups_checked"]==480
    assert q["academic_5m_vc_signals"]==0
    return 0
if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
