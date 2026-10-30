#!/usr/bin/env python3
"""C114-F third source: ORIGINAL Binance USD-M aggTrades, BNB Jan14 2025.

Resolve base-asset volume 1m/3m versus 5m/15m without guessing.
No trading signals, no strategy parameter changes, no economic replay.
"""
import argparse,csv,hashlib,json
from datetime import datetime,timezone
from decimal import Decimal as D
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import c114_volume_discrepancy_forensic as d
class TradeEvidenceError(ValueError):pass

START=int(datetime(2025,1,14,tzinfo=timezone.utc).timestamp()*1000)
END=START+86400000
FOCUS_START=START+13*3600000+30*60000
FOCUS_END=FOCUS_START+15*60000
BASE="https://data.binance.vision/data/futures/um/daily/aggTrades/"
STEM="BNBUSDT-aggTrades-2025-01-14"

def source(fetch=d._safe_http):
    url=f"{BASE}BNBUSDT/{STEM}.zip"
    zip_bytes=fetch(url);checksum=fetch(url+".CHECKSUM")
    if not isinstance(zip_bytes,bytes) or not isinstance(checksum,bytes):
        raise TradeEvidenceError("AGGTRADES_ORIGINAL_BYTES_ONLY")
    digest=hashlib.sha256(zip_bytes).hexdigest()
    parts=checksum.decode("ascii").strip().split()
    if len(parts)!=2 or parts[0].lower()!=digest or parts[1].split("/")[-1]!=STEM+".zip":
        raise TradeEvidenceError("AGGTRADES_PROVIDER_SHA_MISMATCH")
    with ZipFile(BytesIO(zip_bytes)) as z:
        names=z.namelist()
        if names!=[STEM+".csv"]:
            raise TradeEvidenceError("BAD_AGGTRADES_CSV_ARCHIVE")
        raw=z.read(names[0])
    rows=csv.reader(raw.decode("utf-8-sig").splitlines())
    buckets=[{"agg_rows":0,"quantity":D(0),"first_trade_count_approx":0} for _ in range(96)]
    total=0
    last_time=-1
    last_id=-1
    count_future=0
    focus_sample=[]
    for line in rows:
        if not line:continue
        if total==0 and not line[0].lstrip("+-").isdigit():
            continue
        if len(line)!=7:raise TradeEvidenceError("WRONG_AGGTRADES_FORMAT")
        a=int(line[0]);price=D(line[1]);qty=D(line[2])
        first,last=int(line[3]),int(line[4]);stamp=int(line[5])
        if (not (START<=stamp<END) or not price.is_finite() or not qty.is_finite()
            or price<=0 or qty<=0 or first>last or a<=last_id or stamp<last_time):
            raise TradeEvidenceError("AGGTRADES_SOURCE_ORDER_PRICE_OR_CLOCK_CORRUPT")
        last_id=a;last_time=stamp;total+=1
        k=(stamp-START)//900000
        bucket=buckets[k]
        bucket["agg_rows"]+=1
        bucket["quantity"]+=qty
        bucket["first_trade_count_approx"]+=last-first+1
        if FOCUS_START<=stamp<FOCUS_END and len(focus_sample)<5:
            focus_sample.append({"ms":stamp,"id":a,"price":str(price),"base_qty":str(qty),"first_trade_id":first,"last_trade_id":last})
    if not total:raise TradeEvidenceError("EMPTY_ORIGINAL_AGGTRADES")
    return buckets,{"zip_sha256":digest,"csv_sha256":hashlib.sha256(raw).hexdigest(),
        "source_url":url,"provider_checksum_verified":True,"original_agg_trade_rows":total,
        "first_timestamp_ms":None if last_time<0 else START,
        "last_timestamp_ms":last_time,"sample_rows_in_focus_first_five":focus_sample}

def run(fetch=d._safe_http):
    aggs,receipt=source(fetch=fetch)
    native={}
    other={}
    for tf,step in d.TIMEFRAMES.items():
        xs,meta=d.original_interval(tf,fetch=fetch)
        native[tf]=d.aggregate_15m(xs,step)
        other[tf]=meta
    result=[]
    for i in range(96):
        a=aggs[i]
        values={tf:D(native[tf][i]["base_volume"]) for tf in d.TIMEFRAMES}
        gaps={tf:str(a["quantity"]-v) for tf,v in values.items()}
        if any(x!=0 for x in gaps.values()):
            result.append({"bucket":i,"utc":native["1m"][i]["utc"],
                           "agg_trade_base_qty":str(a["quantity"]),
                           "agg_row_count":a["agg_rows"],
                           "aggregated_matched_trade_count":a["first_trade_count_approx"],
                           "native_bases":{k:str(v) for k,v in values.items()},
                           "signed_agg_minus_interval":gaps})
    return {"type":"C114_FORENSIC_AGGTRADES_INDEPENDENT_TRADE_ARCHIVE_ARBITRATION",
        "day":"2025-01-14","symbol":"BNBUSDT",
        "original_aggtrades_receipt":receipt,
        "original_kline_receipts":other,
        "source_qualification":"UNCHANGED_C114_SOURCE_BLOCKED",
        "price_only_hypothesis_unchanged":True,
        "original_aggtrades_total_base_qty":str(sum((v["quantity"] for v in aggs),D(0))),
        "focus_1330":{"utc":datetime.fromtimestamp(FOCUS_START/1000,timezone.utc).isoformat(),
            "agg_rows":aggs[54]["agg_rows"],"agg_base_qty":str(aggs[54]["quantity"]),
            "agg_matched_trade_count_approx":aggs[54]["first_trade_count_approx"],
            "comparison_native_base":{tf:native[tf][54]["base_volume"] for tf in d.TIMEFRAMES}},
        "15m_base_volume_agg_vs_native_mismatch_count":len(result),
        "mismatch_examples":result[:30],
        "no_trade_simulation":True,"live_approved":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    report=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    b=(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode()
    args.output.write_bytes(b)
    print(json.dumps({"report_sha256":hashlib.sha256(b).hexdigest(),
        "aggtrades_rows":report["original_aggtrades_receipt"]["original_agg_trade_rows"],
        "focus":report["focus_1330"],
        "agg_native_15m_mismatches":report["15m_base_volume_agg_vs_native_mismatch_count"],
        "no_trade_simulation":True,"live_approved":False}))
