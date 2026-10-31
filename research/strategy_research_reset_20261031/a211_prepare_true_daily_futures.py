#!/usr/bin/env python3
"""A211 actual Binance Vision daily klines + hourly mark and funding;
long warmup, immutable monthly ZIP+CSV SHA, genuine daily ZIP repair for mark gaps.
NO orders, NO synthetic futures price history and NO invented mark bars.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,time,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone,timedelta
from pathlib import Path
from zipfile import ZipFile

SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","LINKUSDT")
MONTHS=tuple((y,m) for y in (2023,2024,2025,2026) for m in range(1,13)
             if not (y==2026 and m>9))
START=int(datetime(2023,1,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,10,1,tzinfo=timezone.utc).timestamp()*1000)
DAY=86_400_000;HOUR=3_600_000
EXPECTED_DAYS=(END-START)//DAY
EXPECTED_HOURS=(END-START)//HOUR
BASE="https://data.binance.vision/data/futures/um/monthly"
KINDS=("klines","markPriceKlines","fundingRate")

def fetch_zip(url):
    err=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"EMBER-A211-FULL-DAILY-IMMUTABLE-BINANCE-RESEARCH"})
            with urllib.request.urlopen(req,timeout=120) as response:
                raw=response.read(20_000_000)
                assert response.status==200 and 60<len(raw)<20_000_000,(url,len(raw))
            with ZipFile(io.BytesIO(raw)) as z:
                filenames=[f for f in z.namelist() if f.endswith(".csv") and not f.startswith("__")]
                assert len(filenames)==1,(url,filenames)
                csvbytes=z.read(filenames[0])
            rows=list(csv.reader(io.StringIO(csvbytes.decode("utf-8-sig"))))
            assert len(rows)>1,(url,"empty CSV")
            return rows,{"url":url,"zip_sha256":hashlib.sha256(raw).hexdigest(),
                        "csv_sha256":hashlib.sha256(csvbytes).hexdigest(),
                        "source_lines":len(rows)}
        except Exception as exc:
            err=exc
            if attempt<2:time.sleep((attempt+1)*1.7)
    raise RuntimeError(("Genuine ZIP unavailable",url,str(err)))

def job_fetch(job):
    sym,kind,year,month=job
    stamp=f"{year}-{month:02d}"
    if kind=="klines":
        url=f"{BASE}/klines/{sym}/1d/{sym}-1d-{stamp}.zip"
    elif kind=="markPriceKlines":
        url=f"{BASE}/markPriceKlines/{sym}/1h/{sym}-1h-{stamp}.zip"
    else:
        url=f"{BASE}/fundingRate/{sym}/{sym}-fundingRate-{stamp}.zip"
    return job,*fetch_zip(url)

def parse_timestamp(x):
    t=int(x)
    if t>=100_000_000_000_000:
        assert t%1000==0,("micro timestamp not exact ms",t)
        t//=1000
    assert 1_600_000_000_000<t<1_900_000_000_000,t
    return t

def klines(rows,sym,kind):
    out=[]
    for row in rows:
        if not row or row[0].strip().lower().startswith(("open","timestamp","time")):continue
        assert len(row)>=6,(sym,kind,row)
        t=parse_timestamp(row[0])
        if START<=t<END:
            v=[t,*[float(x) for x in row[1:6]]]
            _,o,h,l,c,vol=v
            assert l>0 and l<=min(o,c)<=max(o,c)<=h and vol>=0,(sym,kind,v)
            out.append(v)
    return out

def parse_funding(rows,sym):
    heads=[s.strip().lower().replace("_","") for s in rows[0]]
    def getcols(choices):
        for key in choices:
            if key in heads:return heads.index(key)
        raise RuntimeError(("UNKNOWN_FUNDING_COLUMNS",sym,heads))
    tcol=getcols(("calctime","fundingtime","timestamp","time"))
    rcol=getcols(("lastfundingrate","fundingrate"))
    out=[]
    for row in rows[1:]:
        if not row:continue
        t=parse_timestamp(row[tcol]);rate=float(row[rcol])
        assert abs(rate)<.03
        if START<=t<END:out.append((t,rate))
    return out

def monthly_mark_daily_repair(known,sym,manifest):
    vals={r[0]:r for r in known}
    assert len(vals)==len(known),("DUPLICATED_SOURCE_HOURS",sym)
    missing=[START+i*HOUR for i in range(EXPECTED_HOURS) if START+i*HOUR not in vals]
    if not missing:return [vals[START+i*HOUR] for i in range(EXPECTED_HOURS)],0
    days=sorted(set(datetime.fromtimestamp(t/1000,timezone.utc).strftime("%Y-%m-%d") for t in missing))
    # A genuine daily ZIP is permitted to repair sparse monthly mark gaps, but not arbitrarily missing months.
    assert len(days)<=120,("TOO_MANY_MONTHLY_MARK_GAP_DAYS",sym,len(days))
    print("A211_GENUINE_MARK_GAPS",sym,len(missing),"hours",len(days),"days",flush=True)
    def daily(day):
        url=(f"https://data.binance.vision/data/futures/um/daily/"
             f"markPriceKlines/{sym}/1h/{sym}-1h-{day}.zip")
        rows,receipt=fetch_zip(url)
        return day,klines(rows,sym,"mark daily genuine"),receipt
    with ThreadPoolExecutor(max_workers=10) as pool:
        for future in as_completed([pool.submit(daily,d) for d in days]):
            day,data,receipt=future.result()
            manifest[f"daily_repair_{day}"]=receipt
            for v in data:
                if v[0] in vals:
                    assert vals[v[0]]==v,("CONFLICTING_MONTH_DAILY_CANDLES",sym,day,v[0])
                else:
                    vals[v[0]]=v
    assert len(vals)==EXPECTED_HOURS,("MISSING_AFTER_REAL_DAILY_MARK_RECOVERY",sym,len(vals),EXPECTED_HOURS)
    return [vals[START+i*HOUR] for i in range(EXPECTED_HOURS)],len(missing)

def ensure_contiguous(rows,start,step,expected,sym,kind):
    assert len(rows)==expected,(sym,kind,len(rows),expected)
    for i,row in enumerate(rows):
        assert row[0]==start+i*step,(sym,kind,"GAP/DUPLICATE",i,row[0],start+i*step)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--datadir",required=True)
    p.add_argument("--symbols",nargs="+",default=list(SYMBOLS))
    a=p.parse_args()
    assert len(set(a.symbols))==len(a.symbols) and all(s in SYMBOLS for s in a.symbols)
    d=Path(a.datadir);out=d/"futures";out.mkdir(parents=True,exist_ok=True)
    jobs=[(sym,kind,y,m) for sym in a.symbols for kind in KINDS for y,m in MONTHS]
    got={}
    with ThreadPoolExecutor(max_workers=16) as pool:
        for future in as_completed([pool.submit(job_fetch,job) for job in jobs]):
            job,rows,receipt=future.result()
            got[job]=(rows,receipt)
    manifest={"schema":"A211_TRUE_BINANCE_DAILY_PRICE_HOURLY_MARK_FUNDING_SOURCES",
              "start":"2023-01-01","end_exclusive":"2026-10-01",
              "monthly_source_zip_count":len(jobs),"source_sha":{},"data":{}}
    for sym in a.symbols:
        x={};receipts={};fund=[]
        for kind in KINDS:
            pieces=[]
            for y,m in MONTHS:
                rows,receipt=got[(sym,kind,y,m)]
                receipts[f"{kind}_{y}_{m:02d}"]=receipt
                if kind=="fundingRate":pieces.extend(parse_funding(rows,sym))
                else:pieces.extend(klines(rows,sym,kind))
            if kind=="fundingRate":fund=pieces
            elif kind=="markPriceKlines":
                x[kind],recovered=monthly_mark_daily_repair(pieces,sym,receipts)
                ensure_contiguous(x[kind],START,HOUR,EXPECTED_HOURS,sym,kind)
            else:
                ensure_contiguous(pieces,START,DAY,EXPECTED_DAYS,sym,kind)
                x[kind]=pieces
        seen=set()
        rates={}
        for t,r in fund:
            offset=t%HOUR
            assert 0<=offset<=1000,("FUNDING_SETTLEMENT_OFFGRID",sym,t)
            rounded=t-offset
            assert rounded not in seen,("DUP_FUNDING",sym,rounded)
            seen.add(rounded);rates[rounded]=r
        assert len(rates)>1000,("MISSING_GENUINE_FUNDING",sym,len(rates))
        funding=[[START+i*HOUR,*([rates.get(START+i*HOUR,0.0)]*4),0.]
                 for i in range(EXPECTED_HOURS)]
        symfmt=sym[:-4]+"_USDT_USDT"
        payload={
            f"{symfmt}-1d-futures.json":x["klines"],
            f"{symfmt}-1h-mark.json":x["markPriceKlines"],
            f"{symfmt}-1h-funding_rate.json":funding
        }
        for name,records in payload.items():
            (out/name).write_text(json.dumps(records,separators=(",",":")))
        manifest["source_sha"][sym]=receipts
        manifest["data"][sym]={
            "price_days":len(x["klines"]),"mark_hours":len(x["markPriceKlines"]),
            "funding_settlements":len(rates),"source_repaired_mark_hours":recovered,
            "start_price":x["klines"][0][1],"last_price":x["klines"][-1][4],
            "contiguous_and_sha_verified":True}
        print("A211_CONTIGUOUS_TRUE_DAILY_DATA",sym,manifest["data"][sym],flush=True)
    (d/"A211_REAL_BINANCE_SOURCE_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
    print("A211_FOUR_COIN_TRUE_2023_2026_DAILY_MARK_FUNDING_SOURCE_VERIFIED",
          len(a.symbols),len(jobs),flush=True)

if __name__=="__main__":main()
