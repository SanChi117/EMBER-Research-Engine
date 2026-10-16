#!/usr/bin/env python3
"""D05/F03: Binance Futures raw 5m vs independently original C08 15m parity.

1-day research sample, single BTC symbol. Does NOT upgrade frozen C08
historical 315/315 manifest or self-certify 5m VC for GREEN/BLUE TDA.
"""
from __future__ import annotations
import csv,io,json,sys,zipfile
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/"tools",ROOT/"tests",ROOT/"d05",ROOT.parent/"mtf-course-v05"/"src"):
    sys.path.insert(0,str(p))
from f03_5m_original_source import download_source_5m,source_5m_imbs
from verify_d04_full_manifest_c08 import checked_download
from strict_vision_d04 import verify_raw_zip
from c08_source_bound_poi_b1 import _locked_receipt

DAY=1790899200000
URL5="https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/5m/BTCUSDT-5m-2026-10-02.zip"
URL15="https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/15m/BTCUSDT-15m-2026-10-02.zip"
FIELDS=(1,2,3,4,5)

def main(path=None):
    five=download_source_5m(URL5,40)
    receipt=json.loads((ROOT/"evidence"/"f03"/"F03_BTCUSDT_5M_2026-10-02_ORIGINAL_RECEIPT.json").read_text(encoding="utf8"))
    assert receipt["schema"]=="EMBER_D05_F03_5M_SOURCE_RECEIPT_V1"
    assert receipt["original_zip_url"]==URL5
    assert receipt["original_zip_sha256"]==five.zip_sha256
    assert receipt["original_raw_csv_sha256"]==five.raw_csv_sha256
    assert receipt["academic_vc_certified"] is False and receipt["5m_under_frozen_c08_315"] is False
    assert len(five.rows)==288 and five.day_start_ms==DAY
    c08,_=_locked_receipt("BTCUSDT","15m",DAY,ROOT/"evidence"/"c08")
    assert c08["url"]==URL15
    assert c08["zip_sha256"]==receipt["cross_checked_original_c08_15m_zip_sha256"]
    raw15=checked_download(URL15,25_000_000,40)
    checksum15=checked_download(URL15+".CHECKSUM",1024,40)
    verified=verify_raw_zip(URL15,raw15,checksum15)
    assert verified["zip_sha256"]==c08["zip_sha256"]
    assert verified["raw_csv_sha256"]==c08["raw_csv_sha256"]
    with zipfile.ZipFile(io.BytesIO(raw15)) as archive:
        with archive.open("BTCUSDT-15m-2026-10-02.csv") as handle:
            rows15=list(csv.reader(io.TextIOWrapper(handle,encoding="utf-8-sig",newline="")))
    if rows15[0][0].strip().lower()=="open_time":
        rows15=rows15[1:]
    if len(rows15)!=96:
        raise AssertionError("C08_15M_RAW_SOURCE_NOT_96_BARS")
    match=0
    for i,raw in enumerate(rows15):
        q=five.rows[3*i:3*i+3]
        actual=(Decimal(q[0].original_csv_row[1]),
                max(Decimal(r.original_csv_row[2]) for r in q),
                min(Decimal(r.original_csv_row[3]) for r in q),
                Decimal(q[-1].original_csv_row[4]),
                sum((r.volume for r in q),Decimal("0")))
        reference=tuple(Decimal(raw[j]) for j in FIELDS)
        if (actual!=reference or q[0].bar.start!=int(raw[0])
            or q[-1].bar.end!=int(raw[6])+1):
            raise AssertionError("5M_AND_ORIGINAL_15M_OHLCV_SOURCE_MISMATCH_AT_"+str(i))
        match+=1
    prefix=source_5m_imbs(five,DAY+15*60*1000)
    all_found=source_5m_imbs(five,DAY+86400000)
    assert all(x.known<=DAY+15*60*1000 for x in prefix)
    assert len(all_found)>=len(prefix)
    report={
        "cycle":"D05_F03_ORIGINAL_5M_FUTURES_ONE_DAY_INDEPENDENT_SOURCE",
        "market":"BINANCE_USDM_FUTURES","symbol":"BTCUSDT","utc_day":"2026-10-02",
        "original_5m_url":five.archive_url,
        "original_5m_zip_sha256":five.zip_sha256,
        "original_5m_raw_csv_sha256":five.raw_csv_sha256,
        "original_15m_c08_url":URL15,
        "original_15m_c08_zip_sha256":verified["zip_sha256"],
        "source_5m_rows":len(five.rows),
        "source_15m_rows":len(rows15),
        "five_to_fifteen_minute_ohlcv_parity":match==96,
        "fifteen_minute_candles_exact_5m_ohlcv_matches":match,
        "initial_prefix_5m_imb_count":len(prefix),
        "whole_day_5m_classic_imb_candidates":len(all_found),
        "self_certified_author_vc":False,
        "covered_original_5m_days":1,
        "frozen_c08_315_coverage_modified":False,
        "green_blue_5m_routes_academically_ready":False,
        "ready":"NOT_TRADE_READY",
        "verification_limit":"TLS_PLUS_SAME_HOST_CHECKSUM_NO_BINANCE_DIGITAL_SIGNATURE"
    }
    print(json.dumps(report,sort_keys=True,indent=2))
    if path:Path(path).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0
if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
