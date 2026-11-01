"""A248 / R030: prepare genuine continuous 2023-05 through 2026-05 Binance USD-M native candles.

Verification source: Binance Vision monthly zip plus published .CHECKSUM for all
333 market archives. No SPOT, no guessed mark/funding, no exchange credentials.
Original VolatilitySystem unchanged SHA.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from research.a228_five_original.a228_prepare_pinned_originals_and_real_futures import (
    aggregate_5m, to_candle_frame,
)

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research/r030_continuous_20261101/generated"
COINS=("BTCUSDT","ETHUSDT","SOLUSDT")
START=(2023,5)
END_EXCL=(2026,6)
SOURCE_REPO="freqtrade/freqtrade-strategies"
SOURCE_COMMIT="f3340ce11f5bdf62f598522e64d1f5638eaa13f5"
SOURCE_PATH="user_data/strategies/futures/VolatilitySystem.py"
SOURCE_BLOB="15ce2473f3f60bd33c4a67b0b8b228e379850f19"
MARKET="https://data.binance.vision/data/futures/um/monthly"


def blob_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()


def fetch(url):
    if not url.startswith(("https://data.binance.vision/","https://raw.githubusercontent.com/")):
        raise ValueError("not approved source "+url)
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":"EMBER-Continuous-R030-Research/1.0"
            })
            with urllib.request.urlopen(req,timeout=55) as r:
                return r.read()
        except OSError as exc:
            last=exc
            time.sleep(1+attempt)
    raise ValueError(f"BLOCKED_OFFICIAL_SOURCE {url}: {last}")


def month_iterator():
    year,month=START
    while (year,month)<END_EXCL:
        yield year,month
        year,month=(year+1,1) if month==12 else (year,month+1)


def pinned_source():
    url=f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/{SOURCE_PATH}"
    raw=fetch(url)
    actual=blob_sha(raw)
    if actual!=SOURCE_BLOB:
        raise ValueError(f"original VolatilitySystem Git SHA mismatch {actual}")
    output=OUT/"strategies/VolatilitySystem.py"
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(raw)
    return {"url":url,"git_blob_sha":actual,"source_sha256":hashlib.sha256(raw).hexdigest()}


def real_csv_zip(url):
    raw=fetch(url)
    digest=hashlib.sha256(raw).hexdigest()
    checksum=fetch(url+".CHECKSUM").decode("utf-8-sig").split()[0].lower()
    if len(checksum)!=64 or checksum!=digest:
        raise ValueError("Binance published SHA mismatch "+url)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        member=[m for m in z.namelist() if m.endswith(".csv")]
        if len(member)!=1:
            raise ValueError(f"bad original ZIP members {url}")
        csvraw=z.read(member[0])
    return list(csv.reader(io.StringIO(csvraw.decode("utf-8-sig")))),{
        "url":url,"zip_sha256":digest,"publisher_sha256":checksum,
        "csv_sha256":hashlib.sha256(csvraw).hexdigest(),
    }


def as_ms(x):
    v=int(x)
    if v>=10**15:
        v//=1000
    if not 1_670_000_000_000 < v < 1_800_000_000_000:
        raise ValueError("original UTC timestamp out of range")
    return v


def read_one(job):
    typ,sym,year,month=job
    ym=f"{year}-{month:02d}"
    if typ=="price":
        rel=f"klines/{sym}/5m/{sym}-5m-{ym}.zip"
    elif typ=="mark":
        rel=f"markPriceKlines/{sym}/8h/{sym}-8h-{ym}.zip"
    else:
        rel=f"fundingRate/{sym}/{sym}-fundingRate-{ym}.zip"
    url=f"{MARKET}/{rel}"
    source,receipt=real_csv_zip(url)
    rows=[]
    if typ=="funding":
        header=[x.lower().strip().replace("_","") for x in source[0]]
        it,iv=header.index("calctime"),header.index("lastfundingrate")
        for r in source[1:]:
            if not r or not r[it].isdigit():
                continue
            t=as_ms(r[it])
            v=float(r[iv])
            if not -0.1<v<0.1:
                raise ValueError(f"implausible original settlement {sym}/{ym}")
            rows.append((t,v))
    else:
        for r in source:
            if not r or not r[0].isdigit():
                continue
            t=as_ms(r[0])
            op,hi,lo,cl,vol=map(float,r[1:6])
            if not 0<lo<=min(op,cl)<=max(op,cl)<=hi or vol<0:
                raise ValueError(f"invalid original USD-M {sym}/{ym}/{typ}")
            rows.append((t,op,hi,lo,cl,vol))
    rows.sort()
    days=pd.Period(ym,freq="M").days_in_month
    expected=days*(288 if typ=="price" else 3)
    if typ=="mark" and len(rows)!=expected:
        # Only original complete 1h Binance mark data can reconstruct 8h;
        # never interpolate a missing interval or use trade/spot price.
        uri=f"{MARKET}/markPriceKlines/{sym}/1h/{sym}-1h-{ym}.zip"
        raw1h,receipt1h=real_csv_zip(uri)
        hours=[]
        for r in raw1h:
            if r and r[0].isdigit():
                h=as_ms(r[0]);ohlcv=tuple(map(float,r[1:6]))
                hours.append((h,*ohlcv))
        hours.sort()
        if len(hours)!=days*24 or any(b[0]-a[0]!=3_600_000 for a,b in zip(hours,hours[1:])):
            raise ValueError(f"BLOCKED_MARK_INCOMPLETE {sym}/{ym} native={len(rows)}, 1h={len(hours)}")
        repaired=[]
        for i in range(0,len(hours),8):
            pack=hours[i:i+8]
            if len(pack)!=8 or pack[0][0]%(8*3_600_000):
                raise ValueError(f"invalid 1h to 8h alignment {sym}/{ym}")
            repaired.append((pack[0][0],pack[0][1],max(h[2] for h in pack),
                             min(h[3] for h in pack),pack[-1][4],sum(h[5] for h in pack)))
        rows=repaired
        receipt["original_partial_8h"]={"url":url,"sha256":receipt["zip_sha256"]}
        receipt["complete_real_1h_fallback"]=receipt1h
    if typ=="funding":
        if len(rows)<days*2:
            raise ValueError(f"BLOCKED_MISSING_FUNDING {sym}/{ym}: {len(rows)}")
    elif len(rows)!=expected:
        raise ValueError(f"BLOCKED_MISSING_SOURCE {sym}/{ym}/{typ}: {len(rows)}/{expected}")
    for row in rows:
        t=pd.Timestamp(row[0],unit="ms",tz="UTC")
        if (t.year,t.month)!=(year,month):
            raise ValueError(f"source date outside month {url} {t}")
    times=[x[0] for x in rows]
    if len(set(times))!=len(times):
        raise ValueError(f"source duplicate timestamps {sym}/{ym}/{typ}")
    if typ!="funding":
        interval=300_000 if typ=="price" else 28_800_000
        first=int(pd.Timestamp(f"{ym}-01T00:00:00Z").timestamp()*1000)
        if times[0]!=first or any(b-a!=interval for a,b in zip(times,times[1:])):
            raise ValueError(f"source gaps/offset {sym}/{ym}/{typ}")
    receipt.update({"kind":typ,"symbol":sym,"month":ym,"rows":len(rows)})
    return job,rows,receipt


def write_feather(raw):
    from freqtrade.data.history.datahandlers.featherdatahandler import FeatherDataHandler
    from freqtrade.enums import CandleType
    root=OUT/"binance"
    (root/"futures").mkdir(parents=True,exist_ok=True)
    handler=FeatherDataHandler(root)
    counts={}
    for sym in COINS:
        pair=sym.replace("USDT","/USDT:USDT")
        price=to_candle_frame(raw[sym,"price"],"5m",sym)
        assert price.index[0]==pd.Timestamp("2023-05-01T00:00:00Z")
        assert price.index[-1]==pd.Timestamp("2026-05-31T23:55:00Z")
        for tf in ("5m","15m","1h","4h"):
            data=aggregate_5m(price,tf).reset_index()
            handler.ohlcv_store(pair,tf,data,CandleType.FUTURES)
            counts[f"{sym}_{tf}"]=len(data)
        mark=to_candle_frame(raw[sym,"mark"],"8h",sym).reset_index()
        handler.ohlcv_store(pair,"8h",mark,CandleType.MARK)
        funding=sorted(raw[sym,"funding"])
        funding_times=[x[0] for x in funding]
        if len(set(funding_times))!=len(funding_times):
            raise ValueError("duplicate native funding "+sym)
        if any(b-a>86_400_000 for a,b in zip(funding_times,funding_times[1:])):
            raise ValueError(f"funding settlements have >24h gap {sym}")
        data=pd.DataFrame({
            "date":pd.to_datetime(funding_times,unit="ms",utc=True),
            "funding_rate":[r for _,r in funding],
        })
        handler.ohlcv_store(pair,"8h",data,CandleType.FUNDING_RATE)
        counts[f"{sym}_8h_mark"]=len(mark)
        counts[f"{sym}_actual_funding"]=len(data)
    return counts


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    src=pinned_source()
    tasks=[(kind,sym,y,m) for y,m in month_iterator() for sym in COINS
           for kind in ("price","mark","funding")]
    grouped={(s,k):[] for s in COINS for k in ("price","mark","funding")}
    receipts=[]
    with ThreadPoolExecutor(max_workers=16) as pool:
        jobs=[pool.submit(read_one,t) for t in tasks]
        for i,job in enumerate(as_completed(jobs),1):
            spec,rows,receipt=job.result()
            grouped[spec[1],spec[0]].extend(rows)
            receipts.append(receipt)
            if i%45==0:
                print(f"R030_OFFICIAL_USDM_ARCHIVES {i}/{len(tasks)}",flush=True)
    # The shared parser already validates gaps and complete native 5m bins.
    counts=write_feather(grouped)
    if len(receipts)!=3*3*37:
        raise ValueError("archive count changed")
    manifest={
        "status":"SOURCE_SHA_PINNED_REAL_MAINNET_BINANCE_USDM",
        "continuous_native_calendar":"2023-05-01 through 2026-05-31 UTC",
        "source":src,"original_market_archive_count":len(receipts),
        "receipts":sorted(receipts,key=lambda x:(x["symbol"],x["month"],x["kind"])),
        "counts":counts,
        "warnings":["Monthly prices/mark/funding are real public futures/um, "
                    "but mark is 8h for Freqtrade and does not prove true intrabar liquidation.",
                    "Metadata for CCXT in native test fetched from Binance FUTURES TESTNET due HTTP451; "
                    "original mainnet contract precision/MMR not proved."],
    }
    (OUT/"R030_CONTINUOUS_SOURCE_SHA_RECEIPTS.json").write_text(
        json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
    )
    print("R030_CONTINUOUS_SOURCE_READY",json.dumps({
        "archives":len(receipts),"source_blob":src["git_blob_sha"],
        "counts":counts,
    }),flush=True)


if __name__=="__main__":
    main()
