#!/usr/bin/env python3
"""B1/C05 real Binance Futures full-prefix completeness demonstration.

Pull one original archived BTCUSDT 15m 2026-10-01 Futures ZIP/checksum,
bind all rows by frozen C08 ZIP+CSV SHA, then observe level-touch sequence.
The zone is deliberately CONSTRUCTED from the *second* bar. Consequently
this is a SOURCE-CONTRACT test, not author-defined POI detection, not a setup.
"""
from __future__ import annotations
import csv
import io
import json
import sys
import zipfile
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT/"tools",ROOT/"tests",ROOT/"d05",ROOT.parent/"mtf-course-v05"/"src"):
    sys.path.insert(0,str(path))
from verify_d04_full_manifest_c08 import checked_download
from strict_vision_d04 import verify_raw_zip
from c08_source_bound_poi_b1 import _locked_receipt
from course_primitives_v05 import Bar,POI
from poi_complete_prefix_reaction_b1 import inspect_complete_poi_prefix

URL="https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/15m/BTCUSDT-15m-2026-10-01.zip"
FILE="BTCUSDT-15m-2026-10-01.csv"

def main(output=None):
    receipt,info=_locked_receipt("BTCUSDT","15m",1790812800000,ROOT/"evidence"/"c08")
    assert receipt["url"]==URL
    blob=checked_download(URL,25_000_000,40)
    checksum=checked_download(URL+".CHECKSUM",1024,40)
    verified=verify_raw_zip(URL,blob,checksum)
    assert verified["zip_sha256"]==receipt["zip_sha256"]
    assert verified["raw_csv_sha256"]==receipt["raw_csv_sha256"]
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        with z.open(FILE) as handle:
            data=list(csv.reader(io.TextIOWrapper(handle,encoding="utf-8-sig",newline="")))
    if data and data[0][0].lower()=="open_time":
        data=data[1:]
    assert len(data)==96 and verified["bars"]==96
    bars=[]
    for cells in data:
        assert len(cells)==12
        start=int(cells[0]);end=int(cells[6])+1
        bars.append(Bar(start,end,*[float(Decimal(cells[i])) for i in (1,2,3,4)],"15m"))
    assert all(a.end==b.start for a,b in zip(bars,bars[1:]))
    # First source bar precedes known parent; POI is an explicitly artificial
    # research fixture anchored to next candle, NEVER an academic pattern.
    nextbar=bars[1]
    poi=POI("constructed-b1-c05-prefix-poi","15m","LONG",
            nextbar.l*0.999,nextbar.l*1.00001,bars[0].end)
    first=inspect_complete_poi_prefix(poi,bars[1:],bars[1].end)
    complete=inspect_complete_poi_prefix(poi,bars[1:],bars[-1].end)
    assert first.first_contact_at_ms==bars[1].end
    assert complete.first_contact_at_ms==first.first_contact_at_ms
    assert complete.order_readiness=="NOT_TRADE_READY"
    assert complete.academy_level_status=="LEVEL_AUTHOR_SEMANTICS_UNKNOWN"
    report={
        "cycle":"B1_C05_BINANCE_ORIGINAL_PREFIX_REACTION_SOURCE_PROBE",
        "archive_url":URL,
        "zip_sha256":verified["zip_sha256"],
        "raw_csv_sha256":verified["raw_csv_sha256"],
        "archive_rows":len(bars),
        "post_known_prefix_bars":len(bars)-1,
        "first_contact_at_ms":first.first_contact_at_ms,
        "future_suffix_stable":first.first_contact_at_ms==complete.first_contact_at_ms,
        "later_separated_contacts":sum(e.type=="LATER_CONTACT_UNCLASSIFIED" for e in complete.event_log),
        "has_later_directional_close_observation":any(e.type=="LATER_FAVORABLE_CLOSE_OBSERVED_NOT_VC" for e in complete.event_log),
        "level_source":"ARTIFICIAL_POI_DELIBERATELY_DERIVED_FROM_NEXT_BAR_FOR_INFRA_TEST",
        "data_quality":"REAL_BINANCE_USDM_FUTURES_ARCHIVE_MATCHES_FROZEN_C08_RECEIPTS",
        "test_result":"SOURCE_PREFIX_TECHNICAL_PASS",
        "academy_reaction_rule_approved":False,
        "orders_or_trades_created":False,
        "readiness":complete.order_readiness,
    }
    print(json.dumps(report,sort_keys=True,indent=2))
    if output:Path(output).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0
if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
