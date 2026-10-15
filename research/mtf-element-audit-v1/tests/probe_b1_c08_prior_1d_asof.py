#!/usr/bin/env python3
"""B1/C08 independent real previous 1D + next-day 15m/1H/4H as-of probe.

Downloads Oct 1 ORIGINAL UTC daily and Oct 2 original 15m C08-pinned raw
Binance Futures archives; deliberately NEVER loads Oct 2 daily OHLCV.
A previous known daily price bar is context data, NOT academic Daily Bias.
"""
from __future__ import annotations
import csv,io,json,sys,zipfile
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT/"tools",ROOT/"tests",ROOT/"d05",ROOT.parent/"mtf-course-v05"/"src"):
    sys.path.insert(0,str(path))
from verify_d04_full_manifest_c08 import checked_download
from strict_vision_d04 import verify_raw_zip
from c08_source_bound_poi_b1 import _locked_receipt
from mtf_c08_aggregation_b1 import Source15m
from mtf_prior_daily_asof_b1 import PreviousDayEvidence,join_previous_closed_daily
from course_primitives_v05 import Bar

OCT1=1790812800000
OCT2=OCT1+86_400_000
BASE="https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/"
def load(tf,date,start):
    url=BASE+tf+"/BTCUSDT-"+tf+"-"+date+".zip"
    rec,_=_locked_receipt("BTCUSDT",tf,start,ROOT/"evidence"/"c08")
    assert rec["url"]==url
    z=checked_download(url,25_000_000,40)
    check=checked_download(url+".CHECKSUM",1024,40)
    receipt=verify_raw_zip(url,z,check)
    assert receipt["zip_sha256"]==rec["zip_sha256"]
    assert receipt["raw_csv_sha256"]==rec["raw_csv_sha256"]
    with zipfile.ZipFile(io.BytesIO(z)) as archive:
        with archive.open("BTCUSDT-"+tf+"-"+date+".csv") as fd:
            rows=list(csv.reader(io.TextIOWrapper(fd,encoding="utf-8-sig",newline="")))
    if rows[0][0].lower()=="open_time":rows=rows[1:]
    return receipt,rows
def convert(row,tf):
    return Bar(int(row[0]),int(row[6])+1,
               *(float(Decimal(row[i])) for i in (1,2,3,4)),tf)

def main(outfile=None):
    prev,priorrows=load("1d","2026-10-01",OCT1)
    current,rows15=load("15m","2026-10-02",OCT2)
    assert len(priorrows)==1 and len(rows15)==96
    day=convert(priorrows[0],"1d")
    assert day.end==OCT2
    previous=PreviousDayEvidence(day,"BTCUSDT",prev["zip_sha256"]+":1d:"+str(day.start))
    rows=[Source15m(convert(r,"15m"),Decimal(r[5]),current["zip_sha256"]+":"+r[0],"BTCUSDT") for r in rows15]
    early=join_previous_closed_daily(previous,rows,OCT2+900_000)
    hour=join_previous_closed_daily(previous,rows,OCT2+3_600_000)
    h4=join_previous_closed_daily(previous,rows,OCT2+4*3_600_000)
    late=join_previous_closed_daily(previous,rows,OCT2+95*900_000)
    pre=join_previous_closed_daily(previous,rows[:16],OCT2+4*3_600_000)
    assert early.last_closed_1h is None and early.last_closed_4h is None
    assert hour.last_closed_1h and hour.last_closed_1h.known_at_ms==OCT2+3_600_000
    assert hour.last_closed_4h is None
    assert h4.last_closed_4h and h4.last_closed_4h.known_at_ms==OCT2+4*3_600_000
    assert h4==pre
    assert late.prior_daily_known_at_ms==OCT2 and late.current_1d is None
    report={
        "cycle":"B1_C08_PREVIOUS_NATIVE_1D_JOIN_CURRENT_DERIVED_1H_4H",
        "market":"BINANCE_USDM_FUTURES","symbol":"BTCUSDT",
        "previous_1d_date":"2026-10-01",
        "current_15m_date":"2026-10-02",
        "previous_1d_raw_zip_sha256":prev["zip_sha256"],
        "current_15m_raw_zip_sha256":current["zip_sha256"],
        "previous_1d_known_at_ms":day.end,
        "asof_0015_1h_available":early.last_closed_1h is not None,
        "asof_0100_1h_available":hour.last_closed_1h is not None,
        "asof_0100_4h_available":hour.last_closed_4h is not None,
        "asof_0400_4h_available":h4.last_closed_4h is not None,
        "asof_0400_future_suffix_stable":h4==pre,
        "asof_2345_previous_daily_remains_known":late.prior_daily_bar.end==OCT2,
        "current_day_native_1d_archive_loaded":False,
        "daily_bias_source_verified":False,
        "mtf_course_poi_approved":False,
        "orders_created":False,
        "readiness":"NOT_TRADE_READY",
        "status":"PREVIOUS_DAILY_ASOF_TIMING_VERIFIED_NOT_MTF_SEMANTICS"
    }
    print(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2))
    if outfile:Path(outfile).write_text(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return 0
if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
