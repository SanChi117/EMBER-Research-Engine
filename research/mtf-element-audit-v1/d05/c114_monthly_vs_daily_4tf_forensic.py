#!/usr/bin/env python3
"""C114-F second independent source forensics: archived JAN2025 monthly vs daily.

Only previously disclosed BNB/2025-01-14. No trading simulation or changes
to C114 preregistration. A provider checksum verifies bytes, not consensus.
"""
import argparse, csv, hashlib, json
from datetime import datetime,timezone
from decimal import Decimal as D
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import c114_volume_discrepancy_forensic as one

class MonthlyForensicError(ValueError):pass

def monthly(tf,fetch=one._safe_http):
    if tf not in one.TIMEFRAMES:raise MonthlyForensicError("INTERVAL_NOT_FROZEN")
    step=one.TIMEFRAMES[tf]
    stem=f"{one.SYMBOL}-{tf}-2025-01"
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{one.SYMBOL}/{tf}/{stem}.zip"
    blob=fetch(url);chk=fetch(url+".CHECKSUM")
    sha=hashlib.sha256(blob).hexdigest()
    parts=chk.decode("ascii").strip().split()
    if len(parts)!=2 or parts[0].lower()!=sha or parts[1].split("/")[-1]!=stem+".zip":
        raise MonthlyForensicError("MONTHLY_ORIGINAL_PROVIDER_SHA_DRIFT")
    with ZipFile(BytesIO(blob)) as z:
        names=z.namelist()
        if names!=[stem+".csv"]:raise MonthlyForensicError("MONTHLY_NONCANONICAL_CSV")
        raw=z.read(names[0])
    lines=list(csv.reader(raw.decode("utf-8-sig").splitlines()))
    if lines and lines[0][0].strip().lower() in ("open_time","open time"):
        lines=lines[1:]
    if len(lines)!=31*86400000//step:raise MonthlyForensicError("MISSING_MONTHLY_KLINES")
    start=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)
    oneday=int(datetime(2025,1,14,tzinfo=timezone.utc).timestamp()*1000)
    stop=oneday+86400000
    subset=[]
    for i,r in enumerate(lines):
        at=start+i*step
        if (len(r)!=12 or int(r[0])!=at or int(r[6])!=at+step-1):
            raise MonthlyForensicError("MONTHLY_CLOCK_DRIFT")
        if not oneday<=at<stop:continue
        p=[D(r[k]) for k in (1,2,3,4)]
        q={field:D(r[k]) for field,k in zip(one.FIELDS,(5,7,8,9,10))}
        if (any(not x.is_finite() for x in p+list(q.values())) or
            not 0<p[2]<=min(p[0],p[3])<=max(p[0],p[3])<=p[1] or
            any(x<0 for x in q.values())):
            raise MonthlyForensicError("MONTHLY_CORRUPT_OHLCV")
        subset.append({"start_ms":at,"end_ms":at+step,
                      "o":p[0],"h":p[1],"l":p[2],"c":p[3],**q})
    if len(subset)!=86400000//step:raise MonthlyForensicError("MONTHLY_DAY_GAP")
    receipt={"source_url":url,"timeframe":tf,
             "csv_sha256":hashlib.sha256(raw).hexdigest(),
             "zip_sha256":sha,"provider_checksum_verified":True,
             "month_rows":len(lines),"selected_day_rows":len(subset)}
    return tuple(subset),receipt

def run(fetch=one._safe_http):
    daily15={};monthly15={}
    d_receipts={};m_receipts={}
    for tf,step in one.TIMEFRAMES.items():
        d,dr=one.original_interval(tf,fetch=fetch)
        m,mr=monthly(tf,fetch=fetch)
        daily15[tf]=one.aggregate_15m(d,step)
        monthly15[tf]=one.aggregate_15m(m,step)
        d_receipts[tf]=dr;m_receipts[tf]=mr
    result={}
    for tf in one.TIMEFRAMES:
        changes={}
        for field in ("ohlc",)+one.FIELDS:
            bad=[i for i in range(96) if daily15[tf][i][field]!=monthly15[tf][i][field]]
            changes[field]={"different_15m_buckets":len(bad),"first_mismatch":bad[:15]}
        result[tf]=changes
    return {"type":"C114_MONTHLY_VS_DAILY_NATIVE_4TF_FORENSIC_NO_STRATEGY",
            "symbol":one.SYMBOL,"date":one.DATE,
            "daily_4tf_diagnostics":one.compare_15m(daily15),
            "monthly_4tf_diagnostics":one.compare_15m(monthly15),
            "daily_provider_receipts":d_receipts,
            "monthly_provider_receipts":m_receipts,
            "daily_vs_monthly_15m_diff_by_source":result,
            "known_1330_daily":{tf:daily15[tf][54] for tf in one.TIMEFRAMES},
            "known_1330_monthly":{tf:monthly15[tf][54] for tf in one.TIMEFRAMES},
            "no_trade_outcomes":True,"c114_original_source_gate_unmodified":True,
            "live_approved":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    blob=(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()
    args.output.write_bytes(blob)
    print(json.dumps({"sha256":hashlib.sha256(blob).hexdigest(),
        "monthly_4tf_ohlc_equal":result["monthly_4tf_diagnostics"]["strict_ohlc_equal_all_four"],
        "monthly_4tf_volume_mismatches":result["monthly_4tf_diagnostics"]["metric_mismatch_bucket_counts"],
        "daily_vs_monthly_changes":result["daily_vs_monthly_15m_diff_by_source"],
        "known_1330_monthly":result["known_1330_monthly"],
        "live_approved":False},sort_keys=True))
