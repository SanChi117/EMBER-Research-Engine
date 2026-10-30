#!/usr/bin/env python3
"""C114-F independent market-source forensic; NOT trading, NOT rule relaxation.

One fixed previously exposed case: BNBUSDT USD-M 2025-01-14.
Compare native 1m/3m/5m/15m daily originals. SHA256 of Binance ZIP and
independent CSV receipt for each. Pure diagnostic: never changes C114 gates.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal as D
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from c89_original_native5m_adaptation_backtest import _safe_http

SYMBOL="BNBUSDT"
DATE="2025-01-14"
TIMEFRAMES={"1m":60000,"3m":180000,"5m":300000,"15m":900000}
BASE="https://data.binance.vision/data/futures/um/daily/klines/"
FIELDS=("base_volume","quote_volume","trades","taker_buy_base","taker_buy_quote")
class ForensicError(ValueError):pass

def original_interval(tf, *, fetch=_safe_http):
    if tf not in TIMEFRAMES:raise ForensicError("ONLY_FROZEN_INTERVALS")
    step=TIMEFRAMES[tf]
    stem=f"{SYMBOL}-{tf}-{DATE}"
    url=f"{BASE}{SYMBOL}/{tf}/{stem}.zip"
    blob=fetch(url)
    checksum=fetch(url+".CHECKSUM")
    if not isinstance(blob,bytes) or not isinstance(checksum,bytes):
        raise ForensicError("ORIGINAL_BINARY_REQUIRED")
    zip_sha=hashlib.sha256(blob).hexdigest()
    parts=checksum.decode("ascii").strip().split()
    if len(parts)!=2 or parts[0].lower()!=zip_sha or parts[1].split("/")[-1]!=stem+".zip":
        raise ForensicError("ORIGINAL_PROVIDER_SHA_MISMATCH")
    with ZipFile(BytesIO(blob)) as archive:
        names=archive.namelist()
        if names!=[stem+".csv"]:raise ForensicError("NONCANONICAL_ONE_CSV_ARCHIVE")
        raw=archive.read(names[0])
    rows=list(csv.reader(raw.decode("utf-8-sig").splitlines()))
    if rows and rows[0][0].strip().lower() in ("open_time","open time"):
        rows=rows[1:]
    expected=86400000//step
    if len(rows)!=expected:raise ForensicError("MISSING_OR_EXTRA_NATIVE_BARS")
    day=int(datetime.strptime(DATE,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
    parsed=[]
    for i,row in enumerate(rows):
        if len(row)!=12:raise ForensicError("WRONG_CSV_FORMAT")
        at=day+i*step
        if int(row[0])!=at or int(row[6])!=at+step-1:
            raise ForensicError("BAD_TIMESTAMP_OR_NONCONTIGUOUS")
        p=[D(row[n]) for n in (1,2,3,4)]
        q={field:D(row[n]) for field,n in zip(FIELDS,(5,7,8,9,10))}
        if (any(not x.is_finite() for x in p+list(q.values())) or
            not 0<p[2]<=min(p[0],p[3])<=max(p[0],p[3])<=p[1] or
            any(x<0 for x in q.values())):
            raise ForensicError("BAD_ORIGINAL_PRICE_OR_VOLUME")
        parsed.append({"start_ms":at, "end_ms":at+step,
                       "o":p[0],"h":p[1],"l":p[2],"c":p[3],**q})
    receipt={"symbol":SYMBOL,"date":DATE,"interval":tf,"zip_sha256":zip_sha,
             "csv_sha256":hashlib.sha256(raw).hexdigest(),"native_rows":len(parsed),
             "provider_checksum_verified":True,"source_url":url}
    return tuple(parsed),receipt

def aggregate_15m(rows,step):
    size=900000//step
    if 900000%step or len(rows)%size:raise ForensicError("INCOMPATIBLE_15M")
    out=[]
    for k in range(len(rows)//size):
        z=rows[k*size:(k+1)*size]
        if z[-1]["end_ms"]-z[0]["start_ms"]!=900000:
            raise ForensicError("GAPPED_15M_GROUP")
        p=(z[0]["o"],max(t["h"] for t in z),min(t["l"] for t in z),z[-1]["c"])
        quantities={field:sum((r[field] for r in z),D(0)) for field in FIELDS}
        out.append({"start_ms":z[0]["start_ms"],"utc":datetime.fromtimestamp(z[0]["start_ms"]/1000,timezone.utc).isoformat(),
                    "ohlc":[str(x) for x in p],**{key:str(val) for key,val in quantities.items()}})
    return out

def compare_15m(series):
    if set(series)!=set(TIMEFRAMES) or any(len(t)!=96 for t in series.values()):
        raise ForensicError("MISSING_INDEPENDENT_INTERVAL")
    divergence=[]
    max_relative={field:{"pct":"0","bucket":None} for field in FIELDS}
    field_mismatch_counts=Counter()
    ohlc_mismatch=[]
    for i in range(96):
        z={tf:bars[i] for tf,bars in series.items()}
        if len({tuple(bar["ohlc"]) for bar in z.values()})!=1:
            ohlc_mismatch.append({"index":i,"utc":z["1m"]["utc"],
                                  "ohlc":{t:b["ohlc"] for t,b in z.items()}})
        disagreement={}
        for f in FIELDS:
            vals={tf:D(bar[f]) for tf,bar in z.items()}
            if len(set(vals.values()))>1:
                field_mismatch_counts[f]+=1
                m=max(vals.values());diff=max(vals.values())-min(vals.values())
                rel=100*diff/m if m else D(0)
                if rel>D(max_relative[f]["pct"]):
                    max_relative[f]={"pct":str(rel),"bucket":i}
                disagreement[f]={"raw":{tf:str(v) for tf,v in vals.items()},
                                 "spread_pct":str(rel),
                                 "one_minute_agrees_with":[tf for tf,v in vals.items() if tf!="1m" and v==vals["1m"]]}
        if disagreement:
            divergence.append({"bucket":i,"utc":z["1m"]["utc"],
                               "fields":disagreement})
    return {"total_15m_buckets":96,"strict_ohlc_equal_all_four":not bool(ohlc_mismatch),
            "ohlc_mismatches":ohlc_mismatch[:30],
            "ohlc_mismatch_count":len(ohlc_mismatch),
            "metric_mismatch_bucket_counts":dict(field_mismatch_counts),
            "max_relative_metric_spreads":max_relative,
            "anomalous_bucket_count":len(divergence),
            "first_anomalies":divergence[:25],
            "known_incident_bucket_1330":next((d for d in divergence if d["utc"].endswith("13:30:00+00:00")),None)}

def run(*,fetch=_safe_http):
    raw={}
    receipts={}
    for tf,step in TIMEFRAMES.items():
        z,receipt=original_interval(tf,fetch=fetch)
        raw[tf]=aggregate_15m(z,step)
        receipts[tf]=receipt
    report=compare_15m(raw)
    return {"type":"C114_SOURCE_FORENSIC_NO_ECONOMIC_REPLAY",
            "can_authorize_modified_c114_gate":False,
            "source_qualification": "UNCHANGED_PRECOMMIT_SOURCE_BLOCKED",
            "receipts":receipts,
            "diagnostics":report,
            "known_1330":{tf:raw[tf][54] for tf in TIMEFRAMES},
            "paper_only":True,"live_approved":False,"computed_strategy_trades":0}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    d=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    payload=(json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    args.output.write_bytes(payload)
    print(json.dumps({"report_sha256":hashlib.sha256(payload).hexdigest(),
                      "source_files":len(d["receipts"]),
                      "receipt_zip_sha256":{k:v["zip_sha256"] for k,v in d["receipts"].items()},
                      "strict_ohlc_equal_all_four":d["diagnostics"]["strict_ohlc_equal_all_four"],
                      "ohlc_mismatch_count":d["diagnostics"]["ohlc_mismatch_count"],
                      "metric_mismatch_bucket_counts":d["diagnostics"]["metric_mismatch_bucket_counts"],
                      "known_incident":d["diagnostics"]["known_incident_bucket_1330"],
                      "live_approved":False},sort_keys=True,ensure_ascii=False))
