#!/usr/bin/env python3
"""A198 extend SOL/BTC genuine 1h and 4h warmup to Jan01 2026.
A195 audit data starts Mar15 and has insufficient 4h history for original V9
signal_history=600/regime_history=600 at May13. Extend ONLY genuine source
using Jan/Feb/Mar real Binance Vision USD-M original 1h; preserve overlap.
"""
from __future__ import annotations
import csv,hashlib,io,json,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile
import argparse

START=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
SEAM=int(datetime(2026,3,15,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,10,1,tzinfo=timezone.utc).timestamp()*1000)
H=3600000
N=(END-START)//H
SYMS=("SOLUSDT","BTCUSDT")

def pull(sym,mo):
    month=f"2026-{mo:02d}"
    filename=f"{sym}-1h-{month}.zip"
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/1h/{filename}"
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"EMBER-A198-V9-NO-LIVE"}),timeout=100) as resp:
        data=resp.read(10_000_000)
        assert resp.status==200 and 100<len(data)<10_000_000
    with ZipFile(io.BytesIO(data)) as zip:
        f=[a for a in zip.namelist() if a.endswith(".csv")]
        assert len(f)==1
        b=zip.read(f[0])
    rows=[]
    for vals in csv.reader(io.StringIO(b.decode("utf-8-sig"))):
        if not vals or vals[0].lower().startswith("open"):continue
        assert len(vals)>=6
        t=int(vals[0])
        if t>10**14:
            assert t%1000==0
            t//=1000
        assert START<=t<END,t
        row=[t,*[float(v) for v in vals[1:6]]]
        assert row[3]>0 and row[3]<=min(row[1],row[4])<=max(row[1],row[4])<=row[2]
        rows.append(row)
    return (sym,mo),rows,{"url":url,"zip_sha256":hashlib.sha256(data).hexdigest(),
             "csv_sha256":hashlib.sha256(b).hexdigest(),"n":len(rows)}

def roll(data,n):
    assert len(data)%n==0
    assert data[0][0]%(n*H)==0
    return [[part[0][0],part[0][1],max(z[2] for z in part),
             min(z[3] for z in part),part[-1][4],sum(z[5] for z in part)]
             for i in range(0,len(data),n) if (part:=data[i:i+n])]

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--datadir",required=True)
    a=ap.parse_args()
    root=Path(a.datadir);d=root/"futures";assert d.is_dir()
    manifest={"schema":"A198_REAL_BINANCE_2026_JAN_SEP_SOL_BTC_FULL_600_BAR_4H_WARMUP",
       "source":"Binance Vision USD-M genuine monthly 1h, original A195 Mar15-Sep30 1h",
       "begin":"2026-01-01","end_exclusive":"2026-10-01","checks":{}}
    loaded={}
    with ThreadPoolExecutor(max_workers=6) as pool:
        fs=[pool.submit(pull,s,m) for s in SYMS for m in (1,2,3)]
        for job in as_completed(fs):
            key,rows,rec=job.result();loaded[key]=(rows,rec)
    for sym in SYMS:
        name=f"{sym[:-4]}_USDT_USDT"
        original=json.loads((d/f"{name}-1h-futures.json").read_text())
        assert len(original)==4800 and original[0][0]==SEAM and original[-1][0]==END-H
        pre=[];receipts={}
        overlap=[]
        for m in (1,2,3):
            rows,rec=loaded[sym,m]
            receipts[f"janfebmarch_{m:02d}"]=rec
            pre.extend([x for x in rows if x[0]<SEAM])
            overlap.extend([x for x in rows if x[0]>=SEAM])
        original_overlap=[x for x in original if x[0]<int(datetime(2026,4,1,tzinfo=timezone.utc).timestamp()*1000)]
        assert overlap==original_overlap,(sym,"original March 15-31 mismatch vs genuine monthly Binance",len(overlap),len(original_overlap))
        data=pre+original
        assert len(data)==N,(sym,"missing_janfeb",len(data),N)
        assert all(row[0]==START+i*H for i,row in enumerate(data)),(sym,"historical_1h_gap_or_duplicate")
        h4=roll(data,4);day=roll(data,24)
        for file,rows in ((f"{name}-1h-futures.json",data),
                          (f"{name}-4h-futures.json",h4),
                          (f"{name}-1d-futures.json",day)):
            (d/file).write_text(json.dumps(rows,separators=(",",":")))
        march_at_may13=int(datetime(2026,5,13,tzinfo=timezone.utc).timestamp()*1000)
        back4=sum(x[0]<march_at_may13 for x in h4)
        assert back4>=600,(sym,"author 600*4h regime lookback unavailable",back4)
        manifest["checks"][sym]={"h1":len(data),"h4":len(h4),"day":len(day),
           "pre_eval_4h_warmup_candles":back4,"author_600_bars_4h_fully_present":True,
           "March_overlap_audit":len(overlap),"sources":receipts}
        print("A198_V9_TRUE_600_4H_CONTEXT_SOURCE_OK",sym,manifest["checks"][sym]["pre_eval_4h_warmup_candles"],flush=True)
    (root/"A198_2026_SOL_BTC_JAN_SEP_TRUE_WARMUP_SOURCE_SHA.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("A198_2026_TRUE_SOL_BTC_1H_4H_WARMUP_GAPLESS_PASS",flush=True)

if __name__=="__main__":main()
