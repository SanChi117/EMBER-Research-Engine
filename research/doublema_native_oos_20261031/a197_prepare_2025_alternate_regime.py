#!/usr/bin/env python3
"""A197 2025 alternate-regime original source market input; 2025 belongs to
author's *in-sample* development, so evidence is historical robustness only.
Reuses A195 raw validation/resampling and authentic daily mark repair code.
Native Binance 1h/4h/1d, mark/funding full Jan-Dec; 5m detail Apr-Dec.
No interpolated candles, no signals, no order placement.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,io,json,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile

SYMS=("BTCUSDT","ETHUSDT","SOLUSDT","LINKUSDT")
SOURCE_YEAR=2025
MONTHS=tuple(range(1,13))
START=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)
TEST=int(datetime(2025,4,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
H=3600000
DETAIL=300000
LEN_H=(END-START)//H
LEN_5=(END-TEST)//DETAIL
BASE="https://data.binance.vision/data/futures/um/monthly"
OLD_PATH=Path(__file__).with_name("a195_prepare_crosspair.py")

def reference_module():
    spec=importlib.util.spec_from_file_location("a195_reference_validators",OLD_PATH)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.START=START;m.END=END;m.EXPECTED=LEN_H
    return m

def fetch(job):
    symbol,kind,month=job
    mo=f"{SOURCE_YEAR}-{month:02d}"
    if kind=="klines_5m":
        file=f"{symbol}-5m-{mo}.zip"
        url=f"{BASE}/klines/{symbol}/5m/{file}"
    elif kind=="fundingRate":
        file=f"{symbol}-fundingRate-{mo}.zip"
        url=f"{BASE}/fundingRate/{symbol}/{file}"
    elif kind=="klines":
        file=f"{symbol}-1h-{mo}.zip"
        url=f"{BASE}/klines/{symbol}/1h/{file}"
    else:
        assert kind=="markPriceKlines"
        file=f"{symbol}-1h-{mo}.zip"
        url=f"{BASE}/markPriceKlines/{symbol}/1h/{file}"
    req=urllib.request.Request(url,headers={"User-Agent":"EMBER-A197-SOURCE-PINNED-RESEARCH-ONLY"})
    with urllib.request.urlopen(req,timeout=100) as response:
        b=response.read(16_000_000)
        assert response.status==200 and 100<len(b)<16_000_000,(url,len(b))
    with ZipFile(io.BytesIO(b)) as z:
        names=[p for p in z.namelist() if p.endswith(".csv") and not p.startswith("__")]
        assert len(names)==1,(url,names)
        csvbytes=z.read(names[0])
    rows=list(csv.reader(io.StringIO(csvbytes.decode("utf-8-sig"))))
    assert rows,(url,"zero_rows")
    return job,rows,{"url":url,"zip_sha256":hashlib.sha256(b).hexdigest(),
                     "csv_sha256":hashlib.sha256(csvbytes).hexdigest(),"csv_rows":len(rows)}

def main():
    p=argparse.ArgumentParser();p.add_argument("--datadir",required=True)
    args=p.parse_args()
    root=Path(args.datadir);target=root/"futures";target.mkdir(parents=True,exist_ok=True)
    validator=reference_module()
    jobs=[(sym,kind,m) for sym in SYMS for kind in ("klines","markPriceKlines","fundingRate") for m in MONTHS]
    jobs +=[(sym,"klines_5m",m) for sym in SYMS for m in range(4,13)]
    loaded={}
    with ThreadPoolExecutor(max_workers=9) as ex:
        fs=[ex.submit(fetch,job) for job in jobs]
        for f in as_completed(fs):
            job,rows,receipt=f.result()
            loaded[job]=(rows,receipt)
    manifest={"schema":"EMBER_A197_REAL_BINANCE_USDM_2025_ALTERNATE_REGIME",
       "source_span":"[2025-01-01,2026-01-01)","evaluation":"[2025-04-01,2026-01-01)",
       "original_author_may_2026_IN_SAMPLE":True,
       "comparability":"Original May12 2026 author strategy; this is prior known historical regime NOT unseen OOS",
       "sources":{},"counts":{}}
    for sym in SYMS:
        entry={};rows_by={};funding=[]
        for kind in ("klines","markPriceKlines","fundingRate","klines_5m"):
            months=MONTHS if kind!="klines_5m" else range(4,13)
            combined=[]
            for m in months:
                csvrows,receipt=loaded[sym,kind,m]
                entry[f"{kind}_{m:02d}"]=receipt
                if kind=="fundingRate":
                    combined.extend(validator.parse_funding(csvrows,sym))
                else:
                    combined.extend(validator.klines(csvrows,sym,kind))
            if kind=="fundingRate":funding=combined;continue
            if kind=="markPriceKlines":
                combined=validator.repair_genuine_mark_gaps(combined,sym,entry)
            if kind=="klines_5m":
                combined=[r for r in combined if TEST<=r[0]<END]
                assert len(combined)==LEN_5,(sym,"5m_missing",len(combined),LEN_5)
                for i,row in enumerate(combined):
                    assert row[0]==TEST+i*DETAIL,(sym,"5m_gap_dup",i,row[0])
            else:validator.assert_hourly(combined,sym,kind)
            rows_by[kind]=combined
        native=rows_by["klines"];mark=rows_by["markPriceKlines"]
        funds,nfund=validator.funding_rate_1h(funding)
        assert len(native)==len(mark)==len(funds)==LEN_H
        fmt=sym[:-4]+"_USDT_USDT"
        output={
            f"{fmt}-1h-futures.json":native,
            f"{fmt}-4h-futures.json":validator.create_4h_1d(native,4),
            f"{fmt}-1d-futures.json":validator.create_4h_1d(native,24),
            f"{fmt}-1h-mark.json":mark,
            f"{fmt}-1h-funding_rate.json":funds,
            f"{fmt}-5m-futures.json":rows_by["klines_5m"]
        }
        for name,data in output.items():
            (target/name).write_text(json.dumps(data,separators=(",",":")))
        manifest["counts"][sym]={"h1":len(native),"h4":len(output[f"{fmt}-4h-futures.json"]),
            "daily":len(output[f"{fmt}-1d-futures.json"]), "5m":len(rows_by["klines_5m"]),
            "mark1h":len(mark),"funding_settlements":nfund}
        manifest["sources"][sym]=entry
        print("A197_2025_ALTERNATE_REAL_MARKET",sym,manifest["counts"][sym],flush=True)
    (root/"A197_2025_AUTHENTIC_SOURCE_SHA_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("A197_2025_FOUR_COINS_RAW_SOURCE_QA_AND_SHA_PASS",len(jobs),flush=True)
if __name__=="__main__":main()
