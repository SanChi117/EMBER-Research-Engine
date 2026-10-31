#!/usr/bin/env python3
"""A203: immutable independent 2025 genuine Binance USD-M 5m+1h+mark+settled funding.
Fail closed if monthly source is absent, duplicated or discontinuous.
Source family matches audited A195/A196 2026 without copy/pasting future candles.
PAPER research, no exchange APIs/orders. All input ZIPs record SHA256.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile

SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","LINKUSDT")
MONTHS=(5,6,7,8,9)
START=int(datetime(2025,5,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2025,10,1,tzinfo=timezone.utc).timestamp()*1000)
MIN5=300000
HOUR=3600000
N5=(END-START)//MIN5
N1H=(END-START)//HOUR
BASE="https://data.binance.vision/data/futures/um/monthly"
def millis(x):
    t=int(x)
    if t>100_000_000_000_000:
        assert t%1000==0,("MICRO_NOT_WHOLE",t)
        t//=1000
    assert 1_500_000_000_000<t<1_900_000_000_000,t
    return t

def load_zip(url):
    request=urllib.request.Request(url,headers={"User-Agent":"EMBER-A203-2025-INDEPENDENT-FUTURES-RESEARCH"})
    with urllib.request.urlopen(request,timeout=100) as response:
        raw=response.read(22_000_000)
        assert response.status==200 and 100<len(raw)<22_000_000,(url,len(raw))
    with ZipFile(io.BytesIO(raw)) as z:
        paths=[f for f in z.namelist() if f.endswith(".csv") and not f.startswith("__")]
        assert len(paths)==1,(url,paths)
        b=z.read(paths[0])
    decoded=list(csv.reader(io.StringIO(b.decode("utf-8-sig"))))
    return decoded,{"url":url,"zip_sha256":hashlib.sha256(raw).hexdigest(),
      "csv_sha256":hashlib.sha256(b).hexdigest(),"raw_csv_lines":len(decoded)}

def get(job):
    sym,kind,month=job
    stamp=f"2025-{month:02d}"
    if kind=="5m":
        url=f"{BASE}/klines/{sym}/5m/{sym}-5m-{stamp}.zip"
    elif kind=="1h":
        url=f"{BASE}/klines/{sym}/1h/{sym}-1h-{stamp}.zip"
    elif kind=="mark":
        url=f"{BASE}/markPriceKlines/{sym}/1h/{sym}-1h-{stamp}.zip"
    elif kind=="funding":
        url=f"{BASE}/fundingRate/{sym}/{sym}-fundingRate-{stamp}.zip"
    else: raise RuntimeError(kind)
    rows,receipt=load_zip(url)
    return job,rows,receipt

def parse_ohlcv(rows,sym,kind):
    out=[]
    for line in rows:
        if not line or line[0].lower().startswith(("open","timestamp","time")):continue
        assert len(line)>=6,(sym,kind,line)
        t=millis(line[0])
        if START<=t<END:
            o,h,l,c,v=map(float,line[1:6])
            assert l>0 and l<=min(o,c)<=max(o,c)<=h and v>=0,(sym,kind,line)
            out.append([t,o,h,l,c,v])
    return out

def validate_ohlcv(rows,step,expected,kind,sym):
    assert len(rows)==expected,("WRONG_CANDLE_COUNT",sym,kind,len(rows),expected)
    for i,row in enumerate(rows):
        assert row[0]==START+i*step,("GAP_DUP_OUT_OF_ORDER",sym,kind,i,row[0])
    return rows

def funding_month(rows,sym):
    assert rows and any("funding" in x.lower() for x in rows[0]),(sym,"NO_FUNDING_HEADER",rows[:2])
    header=[x.lower().strip().replace("_","") for x in rows[0]]
    def get_col(keys):
        for key in keys:
            if key in header:return header.index(key)
        return None
    ti=get_col(("calctime","fundingtime","time","timestamp"))
    ri=get_col(("lastfundingrate","fundingrate"))
    assert ti is not None and ri is not None,(sym,header)
    rates=[]
    for x in rows[1:]:
        if not x:continue
        t=millis(x[ti])
        if START<=t<END:
            v=float(x[ri])
            assert abs(v)<=0.03,(sym,t,v)
            rates.append((t,v))
    return rates

def fill_mark_from_daily(mark,sym,receipts):
    indexed={r[0]:r for r in mark}
    assert len(indexed)==len(mark),("MONTHLY_MARK_DUPLICATE",sym)
    expected=set(START+i*HOUR for i in range(N1H))
    missing=expected-set(indexed)
    if missing:
        days=sorted({datetime.fromtimestamp(t/1000,timezone.utc).strftime("%Y-%m-%d") for t in missing})
        assert len(days)<=12,("TOO_MANY_MARK_GAPS",sym,days)
        for day in days:
            url=f"https://data.binance.vision/data/futures/um/daily/markPriceKlines/{sym}/1h/{sym}-1h-{day}.zip"
            csvrows,receipt=load_zip(url)
            receipts[f"mark_daily_{day}"]=receipt
            for row in parse_ohlcv(csvrows,sym,"mark_daily"):
                if row[0] in indexed:assert row==indexed[row[0]],("DAILY_MONTHLY_CONFLICT",sym,day,row[0])
                else:indexed[row[0]]=row
    assert set(indexed)==expected,("MARK_MISSING_AFTER_REPAIR",sym,len(expected-set(indexed)))
    return [indexed[t] for t in sorted(indexed)]

def make_funding(rates,sym):
    fixed={}
    for t,v in rates:
        offset=t%HOUR
        assert 0<=offset<=1000,("FUNDING_SETTLEMENT_NOT_ON_HOUR",sym,t)
        hour=t-offset
        assert hour not in fixed,("FUNDING_DUP",sym,t)
        fixed[hour]=v
    assert len(fixed)>200,("NOT_ENOUGH_GENUINE_FUNDING",sym,len(fixed))
    assert all(START<=t<END for t in fixed)
    return [[START+i*HOUR,*([fixed.get(START+i*HOUR,0.0)]*4),0.] for i in range(N1H)]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--datadir",required=True)
    a=ap.parse_args()
    out=Path(a.datadir)/"futures";out.mkdir(parents=True,exist_ok=True)
    jobs=[(s,kind,m) for s in SYMBOLS for kind in ("5m","1h","mark","funding") for m in MONTHS]
    data={}
    with ThreadPoolExecutor(max_workers=10) as pool:
        tasks=[pool.submit(get,j) for j in jobs]
        for fut in as_completed(tasks):
            key,rows,receipt=fut.result()
            data[key]=(rows,receipt)
    manifest={"schema":"EMBER_A203_REAL_BINANCE_VISION_2025_HOLDOUT","year":2025,
       "source_begin":"2025-05-01","source_end_exclusive":"2025-10-01",
       "evaluate_begin":"2025-05-13","evaluate_end_exclusive":"2025-10-01",
       "source_shas":{},"data":{}}
    for sym in SYMBOLS:
        portions={};sha={}
        for kind in ("5m","1h","mark","funding"):
            arr=[]
            for m in MONTHS:
                rows,receipt=data[sym,kind,m]
                sha[f"{kind}_{m:02d}"]=receipt
                if kind=="funding":arr.extend(funding_month(rows,sym))
                else:arr.extend(parse_ohlcv(rows,sym,kind))
            portions[kind]=arr
        five=validate_ohlcv(portions["5m"],MIN5,N5,"5m",sym)
        onehour=validate_ohlcv(portions["1h"],HOUR,N1H,"1h",sym)
        marks=validate_ohlcv(fill_mark_from_daily(portions["mark"],sym,sha),
                             HOUR,N1H,"mark",sym)
        fund=make_funding(portions["funding"],sym)
        prefix=sym[:-4]+"_USDT_USDT"
        files={
          f"{prefix}-5m-futures.json":five,
          f"{prefix}-1h-futures.json":onehour,
          f"{prefix}-1h-mark.json":marks,
          f"{prefix}-1h-funding_rate.json":fund}
        for name,rows in files.items():
            (out/name).write_text(json.dumps(rows,separators=(",",":")))
        manifest["source_shas"][sym]=sha
        manifest["data"][sym]={"5m":len(five),"1h":len(onehour),"mark_h":len(marks),
          "funding_settlements":len(portions["funding"]),
          "first5m":five[0][0],"last5m":five[-1][0],
          "all_sources_genuine_continuous":True}
        print("A203_SOURCE_VERIFIED",sym,manifest["data"][sym],flush=True)
    (out.parent/"A203_2025_SOURCE_SHA_MANIFEST.json").write_text(
       json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    print("A203_ALL_4_REAL_2025_BINANCE_MARK_FUNDING_5M_1H_CONTINUITY_PASS",len(jobs),flush=True)
if __name__=="__main__":
    main()
