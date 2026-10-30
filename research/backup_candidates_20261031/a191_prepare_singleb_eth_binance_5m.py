#!/usr/bin/env python3
"""A191 pinned post-publication Binance USD-M ETH 5m native Freqtrade data.
Fetch historical PUBLIC Binance Vision monthly ZIP; no account keys; fail closed.
Reuse immutable ETH 1h mark and SETTLED funding source from EMBER A187.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile

HERE=Path(__file__).resolve().parents[1]/"doublema_native_oos_20261031"/"data"
BEGIN=int(datetime(2026,7,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,10,1,tzinfo=timezone.utc).timestamp()*1000)
M5=300_000
H=3_600_000
SYMBOL="ETHUSDT"

def fetch_month(month):
    name=f"{SYMBOL}-5m-2026-{month:02d}.zip"
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/5m/{name}"
    req=urllib.request.Request(url,headers={"User-Agent":"EMBER-A191-public-monthly-klines"})
    with urllib.request.urlopen(req,timeout=80) as r:
        data=r.read(32_000_000)
        assert r.status==200 and 10000<len(data)<32_000_000,("EMPTY_OR_LARGE",url,len(data))
    with ZipFile(io.BytesIO(data)) as z:
        files=[x for x in z.namelist() if x.endswith(".csv") and not x.startswith("__")]
        assert len(files)==1,files
        csvbytes=z.read(files[0])
    rows=[]
    for rec in csv.reader(io.StringIO(csvbytes.decode("utf-8-sig"))):
        if not rec: continue
        if rec[0].lower().startswith("open"): continue
        assert len(rec)>=6,(name,rec)
        timestamp=int(rec[0])
        if timestamp>100_000_000_000_000:
            assert timestamp%1000==0,("UNEXPECTED_MICROSECONDS",timestamp)
            timestamp//=1000
        rows.append([timestamp,*map(float,rec[1:6])])
    return rows,{"url":url,"zip_sha256":hashlib.sha256(data).hexdigest(),
                 "csv_sha256":hashlib.sha256(csvbytes).hexdigest(),"count":len(rows)}

def check_ohlcv(rows,start,end,step):
    assert len(rows)==(end-start)//step,(len(rows),(end-start)//step)
    for i,r in enumerate(rows):
        t,o,h,l,c,v=r
        assert t==start+i*step,("GAP_OR_DUP",i,t,start+i*step)
        assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0,("BAD_OHLC",i,r)

def mark():
    files=sorted(HERE.glob("ETHUSDT_mark_1h_part*.json"))
    assert len(files)>0,"MISSING_A187_MARK"
    rows=[];shas={}
    for p in files:
        b=p.read_bytes();d=json.loads(b)
        assert d["interval"]=="1h" and d["symbol"]==SYMBOL
        rows.extend(d["rows"])
        shas[str(p.relative_to(HERE))]=hashlib.sha256(b).hexdigest()
    data=[[int(r[0]),*map(float,r[1:])] for r in rows if BEGIN<=int(r[0])<END]
    check_ohlcv(data,BEGIN,END,H)
    return data,shas

def funding():
    p=HERE/"ETHUSDT_funding_history.json"
    raw=p.read_bytes();a=json.loads(raw)
    assert a["symbol"]==SYMBOL
    out=[[BEGIN+i*H,0.,0.,0.,0.,0.] for i in range((END-BEGIN)//H)]
    seen=set()
    for rec in a["records"]:
        t=int(rec["fundingTime"])
        if not BEGIN<=t<END: continue
        index=(t-BEGIN)//H
        assert index not in seen,("FUNDING_DUP",index)
        seen.add(index)
        rate=float(rec["fundingRate"])
        assert abs(rate)<0.03,("FUNDING_OUTLIER",rate)
        out[index]=[BEGIN+index*H,rate,rate,rate,rate,0.]
    assert len(seen)>=200,("MISSING_FUNDING_HISTORY",len(seen))
    return out,hashlib.sha256(raw).hexdigest(),len(seen)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--datadir",required=True);args=ap.parse_args()
    data=[];sources={}
    for month in (7,8,9):
        rows,receipt=fetch_month(month)
        data.extend(rows);sources[str(month)]=receipt
    check_ohlcv(data,BEGIN,END,M5)
    markrows,markshas=mark()
    fundingrows,fr_sha,nfund=funding()
    d=Path(args.datadir)/"futures"
    d.mkdir(parents=True,exist_ok=True)
    for filename,rows in (
        ("ETH_USDT_USDT-5m-futures.json",data),
        ("ETH_USDT_USDT-1h-mark.json",markrows),
        ("ETH_USDT_USDT-1h-funding_rate.json",fundingrows),
    ):
        (d/filename).write_text(json.dumps(rows,separators=(",",":")))
    manifest={
        "schema":"EMBER_A191_BINANCE_ETH_5M_SOURCE_R01",
        "market":"Binance USD-M ETHUSDT",
        "source_klines":"Binance Vision PUBLIC monthly",
        "source_mark_funding":"EMBER A187 pinned original Binance USD-M",
        "begin_ms":BEGIN,"end_exclusive_ms":END,
        "source_period":"2026-07-01..2026-10-01 exclusive, July warmup",
        "target_test":"[2026-08-01,2026-10-01) UTC, no parameter fit",
        "candles_5m":len(data),"mark_1h":len(markrows),
        "funding_events":nfund,"klines_zip_sha":sources,
        "mark_1h_sha":markshas,"funding_source_sha256":fr_sha,
        "important":"OHLCV is public historical data, not executable bid/ask order fills; unrealistically perfect limit fills and intra-5m excursion unverified."
    }
    (d.parent/"A191_SOURCE_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
    print("A191_REAL_BINANCE_MONTHLY_5M_CONTINUITY_PASS",len(data),nfund,flush=True)
if __name__=="__main__":main()
