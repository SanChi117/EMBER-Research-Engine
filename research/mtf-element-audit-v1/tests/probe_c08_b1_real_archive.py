#!/usr/bin/env python3
"""B1/C04 independent *real original* Binance Vision USD-M archive probe.

Uses BTCUSDT 2026-10-01 daily 15m Futures ZIP, paired same-host .CHECKSUM and
Git-pinned prior C08 receipts. Builds an intentionally CONSTRUCTED toy POI
around real observed bars to prove source-binding only; not a course setup.
"""
from __future__ import annotations
import csv,io,json,sys,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"d05"))
sys.path.insert(0,str(ROOT.parent/"mtf-course-v05"/"src"))
from verify_d04_full_manifest_c08 import checked_download
from course_primitives_v05 import Bar
from strict_event_lineage_d03 import EventLedger,CausalEvent
from poi_price_lineage_b1 import BarWitness,ZoneReference,bar_digest
from c08_source_bound_poi_b1 import _locked_receipt,link_c08_test,link_c08_vc

URL="https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/15m/BTCUSDT-15m-2026-10-01.zip"
RULE="https://drive.google.com/file/d/1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R/view"

def create_event(uid,kind,bar,parents=(),evidence=()):
    return CausalEvent(uid,kind,"BTCUSDT","BINANCE","USDM_FUTURES",
                       bar.tf,bar.start,bar.end,bar.end,parents,evidence or (uid,))

def main():
    from strict_vision_d04 import parse_url
    metadata=parse_url(URL)
    receipt,_=_locked_receipt("BTCUSDT","15m",metadata["start_ms"],
                             ROOT/"evidence"/"c08")
    assert receipt["url"]==URL
    checksum=checked_download(URL+".CHECKSUM",1024,40)
    zip_bytes=checked_download(URL,25_000_000,40)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        with z.open("BTCUSDT-15m-2026-10-01.csv") as fi:
            rows=list(csv.reader(io.TextIOWrapper(fi,encoding="utf-8-sig",newline="")))
    if rows[0][0].lower()=="open_time":rows=rows[1:]
    def to_bar(row):
        return Bar(int(row[0]),int(row[6])+1,float(row[1]),float(row[2]),
                   float(row[3]),float(row[4]),"15m")
    first,second,third=map(to_bar,rows[:3])
    assert first.end==second.start and second.end==third.start
    g=EventLedger()
    g.add(create_event("first-source","SOURCE",first,evidence=(bar_digest(first),)))
    g.add(create_event("constructed-poi","POI",first,("first-source",),("academic-rule-uri",)))
    g.add(create_event("second-source","SOURCE",second,evidence=(bar_digest(second),)))
    g.add(create_event("test","TEST",second,("constructed-poi",),("second-source",)))
    g.add(create_event("third-source","SOURCE",third,evidence=(bar_digest(third),)))
    g.add(create_event("vc","VC",third,("test",),("third-source",)))
    # PURELY CONSTRUCTED diagnostic interval centered near next observed bar.
    low=second.l*0.99
    high=second.h
    zone=ZoneReference("constructed-poi","first-source",RULE,"LONG","15m",
                       low,high,first.end,"BTCUSDT","BINANCE","USDM_FUTURES")
    tw=BarWitness("second-source","test",second,"BTCUSDT","BINANCE","USDM_FUTURES","LONG")
    vw=BarWitness("third-source","vc",third,"BTCUSDT","BINANCE","USDM_FUTURES","LONG")
    a=link_c08_test(g,zone,tw,second.end,zip_bytes,checksum)
    b=link_c08_vc(g,zone,tw,vw,third.end,zip_bytes,checksum,zip_bytes,checksum)
    assert a.readiness=="NOT_TRADE_READY"
    assert b.readiness=="NOT_TRADE_READY"
    report={
        "cycle":"B1_C04_REAL_SOURCE_INTEGRATION_PROBE",
        "source_market":"BINANCE_USDM_FUTURES",
        "archive_url":URL,"zip_sha256":receipt["zip_sha256"],
        "raw_csv_sha256":receipt["raw_csv_sha256"],
        "observed_bar_times":[first.start,second.start,third.start],
        "source_quality":"HTTPS_TLS_AND_C08_RECEIPT_MATCH_SAME_HOST_CHECKSUM_NOT_SIGNATURE",
        "parent_zone_source":"ARTIFICIAL_ZONE_CONSTRUCTED_FROM_BAR_FOR_TECHNICAL_TEST_ONLY",
        "test_link":a.event.relation,"vc_link":b.event.relation,
        "technical_replay":"PASS",
        "academic_formation_approved":False,
        "order_or_trade_plan_created":False,
        "readiness":"NOT_TRADE_READY",
    }
    print(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2))
    if len(sys.argv)>1:
        Path(sys.argv[1]).write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
