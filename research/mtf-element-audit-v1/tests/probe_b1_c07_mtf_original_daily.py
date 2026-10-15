#!/usr/bin/env python3
"""B1/C07 independent C08 15m→1H/4H/1D OHLCV verification.

Separately fetch original Binance USD-M BTCUSDT 15m and 1d ZIPs for the
same UTC day and same-host CHECKSUMs. Require C08-pinned SHA for each.
No MTF Daily Bias or POI semantics are inferred, and no orders are created.
"""
from __future__ import annotations
import csv,io,json,sys,zipfile
from pathlib import Path
from decimal import Decimal
R=Path(__file__).resolve().parents[1]
for p in (R/"tools",R/"tests",R/"d05",R.parent/"mtf-course-v05"/"src"):
    sys.path.insert(0,str(p))
from strict_vision_d04 import verify_raw_zip
from verify_d04_full_manifest_c08 import checked_download
from c08_source_bound_poi_b1 import _locked_receipt
from mtf_c08_aggregation_b1 import Source15m,derive_closed_mtf_from_15m
from course_primitives_v05 import Bar

DAY_START=1790812800000
URL_BASE="https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/"
def load(tf):
    url=URL_BASE+tf+"/BTCUSDT-"+tf+"-2026-10-01.zip"
    receipt,_=_locked_receipt("BTCUSDT",tf,DAY_START,R/"evidence"/"c08")
    assert receipt["url"]==url
    rawzip=checked_download(url,25_000_000,40)
    checksum=checked_download(url+".CHECKSUM",1024,40)
    checked=verify_raw_zip(url,rawzip,checksum)
    assert checked["zip_sha256"]==receipt["zip_sha256"]
    assert checked["raw_csv_sha256"]==receipt["raw_csv_sha256"]
    with zipfile.ZipFile(io.BytesIO(rawzip)) as z:
        with z.open("BTCUSDT-"+tf+"-2026-10-01.csv") as f:
            rows=list(csv.reader(io.TextIOWrapper(f,encoding="utf-8-sig",newline="")))
    if rows[0][0].lower()=="open_time":rows=rows[1:]
    return checked,rows

def main(path=None):
    finer,r15=load("15m")
    daily,r1d=load("1d")
    assert len(r15)==96 and len(r1d)==1
    sources=[]
    for cells in r15:
        b=Bar(int(cells[0]),int(cells[6])+1,
              *(float(Decimal(cells[i])) for i in (1,2,3,4)),"15m")
        sources.append(Source15m(b,Decimal(cells[5]),
                     finer["zip_sha256"]+":"+cells[0],"BTCUSDT"))
    before=derive_closed_mtf_from_15m(sources[:95],sources[94].bar.end)
    out=derive_closed_mtf_from_15m(sources,sources[-1].bar.end)
    assert len(before.bars_1d)==0 and before.pending_1d_slots==95
    assert len(out.bars_1h)==24 and len(out.bars_4h)==6 and len(out.bars_1d)==1
    b=out.bars_1d[0]
    real=r1d[0]
    derived=[Decimal(str(v)) for v in (b.bar.o,b.bar.h,b.bar.l,b.bar.c)]+[b.volume]
    native=[Decimal(real[i]) for i in (1,2,3,4,5)]
    matches=[x==y for x,y in zip(derived,native)]
    report={
        "cycle":"B1_C07_DERIVED_MTF_VS_NATIVE_1D",
        "symbol":"BTCUSDT","market":"BINANCE_USDM_FUTURES",
        "date":"2026-10-01",
        "source_15m_rows":len(r15),"source_1d_rows":len(r1d),
        "complete_1h":len(out.bars_1h),"complete_4h":len(out.bars_4h),"complete_1d":len(out.bars_1d),
        "partial_day_95_does_not_emit_daily":len(before.bars_1d)==0,
        "15m_zip_sha256":finer["zip_sha256"],
        "1d_zip_sha256":daily["zip_sha256"],
        "derived_1d_ohlcv":[str(x) for x in derived],
        "native_1d_ohlcv":[str(x) for x in native],
        "ohlcv_exact_match":all(matches),
        "comparison_match_by_field":dict(zip(["open","high","low","close","volume"],matches)),
        "source_label":"TWO_INDEPENDENT_C08_RECEIPT_PINNED_SAME_HOST_BINANCE_ZIPS",
        "derived_1h_4h_label":"AGGREGATED_FROM_15M_NOT_NATIVE_EXCHANGE_KLINES",
        "academy_mtf_bias_approved":False,
        "course_poi_approved":False,
        "trade_plan_created":False,
        "readiness":"NOT_TRADE_READY",
    }
    print(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2))
    if path:Path(path).write_text(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if not all(matches):raise SystemExit("B1_C07_ORIGINAL_DAILY_SOURCE_NOT_EXACTLY_EQUAL_DERIVED_15M_OHLCV")
    return 0
if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
