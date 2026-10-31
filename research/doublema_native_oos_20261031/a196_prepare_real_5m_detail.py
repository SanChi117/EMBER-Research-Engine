#!/usr/bin/env python3
"""A196 original DoubleMA 5m-fidelity input, public Binance Vision USD-M.
Pure candle downloader. No strategy signals, no orders, no retuning.
Futures 5m on May-Sep 2026, 4 coins. Fail closed on missing/unordered candles.
"""
from __future__ import annotations
import csv,hashlib,io,json,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile
import argparse

SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","LINKUSDT")
MONTHS=(5,6,7,8,9)
BEGIN=int(datetime(2026,5,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,10,1,tzinfo=timezone.utc).timestamp()*1000)
STEP=5*60*1000
EXPECTED=(END-BEGIN)//STEP

def fetch(job):
    s,m=job
    file=f"{s}-5m-2026-{m:02d}.zip"
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{s}/5m/{file}"
    request=urllib.request.Request(url,headers={"User-Agent":"EMBER-A196-ORIGINAL-FREQTRADE-DETAIL-PAPER"})
    with urllib.request.urlopen(request,timeout=100) as response:
        b=response.read(16_000_000)
        assert response.status==200 and 2000<len(b)<16_000_000
    with ZipFile(io.BytesIO(b)) as z:
        names=[n for n in z.namelist() if n.endswith(".csv") and not n.startswith("__")]
        assert len(names)==1,names
        contents=z.read(names[0])
    rows=[]
    for rec in csv.reader(io.StringIO(contents.decode("utf-8-sig"))):
        if not rec or rec[0].lower().startswith("open"):continue
        assert len(rec)>=6,(s,m,rec)
        t=int(rec[0])
        if t>10**14:
            assert t%1000==0
            t//=1000
        assert 1_700_000_000_000<t<1_900_000_000_000,t
        row=[t,*[float(x) for x in rec[1:6]]]
        _,o,h,l,c,v=row
        assert l>0 and l<=min(o,c)<=max(o,c)<=h and v>=0,(s,m,row)
        rows.append(row)
    return job,rows,{"url":url,"csv_sha256":hashlib.sha256(contents).hexdigest(),"zip_sha256":hashlib.sha256(b).hexdigest(),"candles":len(rows)}

def main():
    p=argparse.ArgumentParser();p.add_argument("--datadir",required=True)
    a=p.parse_args()
    d=Path(a.datadir)/"futures";d.mkdir(parents=True,exist_ok=True)
    receipts={}
    with ThreadPoolExecutor(max_workers=7) as pool:
        fs=[pool.submit(fetch,(s,m)) for s in SYMBOLS for m in MONTHS]
        for future in as_completed(fs):
            job,rows,sha=future.result()
            receipts[job]=(rows,sha)
    manifest={"schema":"EMBER_A196_REAL_BINANCE_5M_DETAIL","begin":"2026-05-01",
              "end_exclusive":"2026-10-01","symbols":{}}
    for sym in SYMBOLS:
        combined=[]
        sources={}
        for m in MONTHS:
            rows,sha=receipts[sym,m]
            combined.extend(rows)
            sources[f"2026-{m:02d}"]=sha
        assert len(combined)==EXPECTED,(sym,len(combined),EXPECTED)
        for i,r in enumerate(combined):
            assert r[0]==BEGIN+i*STEP,("GAP_DUP",sym,i,r[0])
        name=f"{sym[:-4]}_USDT_USDT-5m-futures.json"
        (d/name).write_text(json.dumps(combined,separators=(",",":")))
        manifest["symbols"][sym]={"candles":len(combined),"sources":sources,
                                  "first_ms":combined[0][0],"last_ms":combined[-1][0],
                                  "file":name}
        print("A196_REAL_BINANCE_5M_SOURCE_QA",sym,len(combined),flush=True)
    (d.parent/"A196_REAL_5M_SHA_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("A196_FOUR_TRUE_5M_BINANCE_DATASETS_INTEGRITY_PASS",EXPECTED,flush=True)

if __name__=="__main__":main()
