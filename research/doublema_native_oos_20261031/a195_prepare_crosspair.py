#!/usr/bin/env python3
"""A195: original frozen DoubleMA cross-market source preparation, public Binance Vision.
Use native 1h trade and mark klines, real monthly fundingRate, 4h+1d exactly
resampled from *complete* native 1h bars. Validate all continuity. No keys, no trading.
All symbols are from SAME 2026-03-15..2026-10-01 UTC window as A187 ETH proof.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile

SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","LINKUSDT")
MONTHS=tuple(range(3,10))
START=int(datetime(2026,3,15,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,10,30,tzinfo=timezone.utc).timestamp()*1000)
H=3_600_000
EXPECTED=(END-START)//H
BASE="https://data.binance.vision/data/futures/um/monthly"

def one_zip(job):
    sym,kind,month=job
    mn=f"2026-{month:02d}"
    if kind=="klines":
        file=f"{sym}-1h-{mn}.zip"
        url=f"{BASE}/klines/{sym}/1h/{file}"
    elif kind=="markPriceKlines":
        file=f"{sym}-1h-{mn}.zip"
        url=f"{BASE}/markPriceKlines/{sym}/1h/{file}"
    elif kind=="fundingRate":
        file=f"{sym}-fundingRate-{mn}.zip"
        url=f"{BASE}/fundingRate/{sym}/{file}"
    else: raise RuntimeError("unknown kind")
    request=urllib.request.Request(url,headers={"User-Agent":"EMBER-A195-IMMUTABLE-PUBLIC-OHLCV-RESEARCH"})
    with urllib.request.urlopen(request,timeout=100) as response:
        compressed=response.read(10_000_000)
        assert response.status==200 and 100<len(compressed)<10_000_000,(url,len(compressed))
    with ZipFile(io.BytesIO(compressed)) as z:
        files=[f for f in z.namelist() if f.endswith(".csv") and not f.startswith("__")]
        assert len(files)==1,(url,files)
        b=z.read(files[0])
    contents=list(csv.reader(io.StringIO(b.decode("utf-8-sig"))))
    assert contents
    return job,contents,{"url":url,"zip_sha256":hashlib.sha256(compressed).hexdigest(),
                           "csv_sha256":hashlib.sha256(b).hexdigest(),"lines":len(contents)}

def tsms(value):
    val=int(value)
    if val>100_000_000_000_000:
        assert val%1000==0,("unexpected_micro",val)
        val//=1000
    assert 1_600_000_000_000<val<1_900_000_000_000,("unexpected_timestamp",val)
    return val

def klines(rows,sym,kind):
    out=[]
    for row in rows:
        if not row or row[0].lower().startswith(("open","timestamp","time")):continue
        assert len(row)>=6,(sym,kind,row)
        t=tsms(row[0])
        if START<=t<END:
            vals=[t,*[float(v) for v in row[1:6]]]
            _,o,h,l,c,v=vals
            assert l>0 and l<=min(o,c)<=max(o,c)<=h and v>=0,(sym,kind,vals)
            out.append(vals)
    return out

def assert_hourly(rows,sym,kind):
    assert len(rows)==EXPECTED,("MISSING_CONTIGUOUS_1H",sym,kind,len(rows),EXPECTED)
    for i,row in enumerate(rows):
        assert row[0]==START+i*H,("GAP_DUP_OR_ORDER",sym,kind,i,row[0])

def create_4h_1d(hourly,interval):
    out=[]
    assert len(hourly)%interval==0
    assert (START//H)%interval==0
    for i in range(0,len(hourly),interval):
        part=hourly[i:i+interval]
        out.append([part[0][0],part[0][1],max(x[2] for x in part),
                    min(x[3] for x in part),part[-1][4],sum(x[5] for x in part)])
    return out

def parse_funding(rows,sym):
    assert rows and any("funding" in x.lower() for x in rows[0]),(sym,"unfamiliar_header",rows[:2])
    headers=[s.strip().lower().replace("_","") for s in rows[0]]
    def col(candidates):
        for x in candidates:
            if x in headers: return headers.index(x)
        return -1
    tcol=col(("calctime","fundingtime","time","timestamp"))
    rcol=col(("lastfundingrate","fundingrate"))
    assert tcol>=0 and rcol>=0,(sym,headers)
    seen=set();out=[]
    for row in rows[1:]:
        if not row:continue
        t=tsms(row[tcol]);r=float(row[rcol])
        assert abs(r)<=0.03,(sym,"unexpected_funding_rate",r)
        if START<=t<END:
            assert t not in seen,(sym,"duplicate_funding",t)
            seen.add(t)
            out.append((t,r))
    return out

def funding_rate_1h(parts):
    data=[];seen=set()
    for t,r in sorted(parts):
        # Binance Vision monthly fundingRate calc_time ordinarily EXACT h UTC.
        # Fail closed if unavailable / malformed settlements.
        assert t%H==0,("non_h_funding_timestamp",t)
        assert t not in seen,("duplicate_funding_across_months",t)
        seen.add(t);data.append((t,r))
    assert len(data)>300,("missing_settled_funding_events",len(data))
    # One 1h row per candle; ZERO between actual settlement hours, not a proxy for future rates.
    rates={t:r for t,r in data}
    return [[START+i*H,*([rates.get(START+i*H,0.0)]*4),0.] for i in range(EXPECTED)],len(data)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--datadir",required=True)
    a=p.parse_args()
    destination=Path(a.datadir)
    out=destination/"futures";out.mkdir(parents=True,exist_ok=True)
    jobs=[(s,k,m) for s in SYMBOLS for k in ("klines","markPriceKlines","fundingRate") for m in MONTHS]
    loaded={}
    with ThreadPoolExecutor(max_workers=9) as executor:
        fs=[executor.submit(one_zip,job) for job in jobs]
        for f in as_completed(fs):
            job,csvrows,receipt=f.result()
            loaded[job]=(csvrows,receipt)
    manifest={"schema":"EMBER_A195_REAL_BINANCE_USDM_2026_CROSS_PAIR","from":"2026-03-15",
              "end_exclusive":"2026-10-30","test_start":"2026-05-13",
              "note":"4h and 1d exactly resampled from complete Binance original futures 1h OHLCV",
              "source_shas":{},"data":{}}
    for sym in SYMBOLS:
        data={};shas={};rates=[]
        for kind in ("klines","markPriceKlines","fundingRate"):
            combined=[]
            for m in MONTHS:
                csvrows,receipt=loaded[sym,kind,m]
                shas[f"{kind}_{m:02d}"]=receipt
                if kind=="fundingRate":
                    combined.extend(parse_funding(csvrows,sym))
                else:combined.extend(klines(csvrows,sym,kind))
            if kind!="fundingRate":
                assert_hourly(combined,sym,kind)
                data[kind]=combined
        native_1h=data["klines"]
        mark_1h=data["markPriceKlines"]
        funding,nfund=funding_rate_1h(rates)
        assert len(native_1h)==len(mark_1h)==len(funding)==EXPECTED
        fmt=sym[:-4]+"_USDT_USDT"
        payload={
          f"{fmt}-1h-futures.json":native_1h,
          f"{fmt}-4h-futures.json":create_4h_1d(native_1h,4),
          f"{fmt}-1d-futures.json":create_4h_1d(native_1h,24),
          f"{fmt}-1h-mark.json":mark_1h,
          f"{fmt}-1h-funding_rate.json":funding
        }
        for filename,rows in payload.items():
            (out/filename).write_text(json.dumps(rows,separators=(",",":")))
        manifest["source_shas"][sym]=shas
        manifest["data"][sym]={"hours":len(native_1h),"h4":len(payload[f"{fmt}-4h-futures.json"]),
             "daily":len(payload[f"{fmt}-1d-futures.json"]),
             "mark_hours":len(mark_1h),"funding_settlements":nfund}
        print("A195_REPRODUCIBLE_ACTUAL_MARKET",sym,manifest["data"][sym],flush=True)
    (destination/"A195_DATA_SHA_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
    print("A195_ALL_4_SYMBOLS_CONTINUOUS_SOURCE_QUALITY_OK",len(jobs),flush=True)

if __name__=="__main__":main()
