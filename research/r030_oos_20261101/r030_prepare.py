"""R030 original Binance USD-M June-Oct 2026 holdout preparation.

NO strategy modification; only original pinned source, and genuine monthly
5m trades-price klines, 8h mark-index kline, 8h signed fundingRate.
No fabricated data or SPOT source, no exchange orders or credentials.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from research.a221_wide_futures_screen.a221_tsmom_genuine_futures import (
    blob_sha,
    fetch,
)
from research.a228_five_original.a228_prepare_pinned_originals_and_real_futures import (
    aggregate_5m,
    to_candle_frame,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/"research/r030_oos_20261101/generated"
SYMS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
MONTHS = tuple((2026,m) for m in range(5,11))
SRC_REPO="freqtrade/freqtrade-strategies"
SRC_COMMIT="f3340ce11f5bdf62f598522e64d1f5638eaa13f5"
SRC_PATH="user_data/strategies/futures/VolatilitySystem.py"
SRC_BLOB="15ce2473f3f60bd33c4a67b0b8b228e379850f19"


def verify_original():
    url=f"https://raw.githubusercontent.com/{SRC_REPO}/{SRC_COMMIT}/{SRC_PATH}"
    raw=fetch(url)
    sha=blob_sha(raw)
    if sha!=SRC_BLOB:
        raise ValueError(f"original code SHA mismatch {sha}")
    target=OUT/"strategies/VolatilitySystem.py"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw)
    return {"original":url,"blob_sha":sha,
            "sha256":hashlib.sha256(raw).hexdigest(),"unchanged_bytes":True}


def csv_from_binance(url: str):
    raw=fetch(url)
    checksum=fetch(url+".CHECKSUM").decode("utf-8-sig").strip().split()[0].lower()
    zip_sha=hashlib.sha256(raw).hexdigest()
    if zip_sha!=checksum:
        raise ValueError(f"Binance published checksum mismatch {url}")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[name for name in z.namelist() if name.endswith(".csv")]
        if len(names)!=1:
            raise ValueError(f"expected exactly one CSV {url}")
        member=z.read(names[0])
    return list(csv.reader(io.StringIO(member.decode("utf-8-sig")))), {
        "url":url,"zip_sha256":zip_sha,"official_sha256":checksum,
        "raw_csv_sha256":hashlib.sha256(member).hexdigest(),
    }


def rows_candles(raw, spec):
    typ,sym,year,month=spec
    out=[]
    for r in raw:
        if not r or not r[0].isdigit():
            continue
        ts=int(r[0])
        if ts >= 10**15:
            ts//=1000
        values=tuple(map(float,r[1:6]))
        op,hi,lo,close,vol=values
        if not (lo>0 and lo<=min(op,close)<=max(op,close)<=hi and vol>=0):
            raise ValueError(f"original candle invalid {spec} {ts}")
        period=pd.Timestamp(ts,unit="ms",tz="UTC")
        if (period.year,period.month)!=(year,month):
            raise ValueError(f"unexpected candle month {spec}: {period}")
        out.append((ts,*values))
    if not out:
        raise ValueError(f"missing real Binance candles {spec}")
    return out


def rows_funding(raw, spec):
    names=[x.strip().lower().replace("_","") for x in raw[0]]
    ti,rate_i=names.index("calctime"),names.index("lastfundingrate")
    out=[]
    for r in raw[1:]:
        if not r or not r[ti].isdigit():
            continue
        ts=int(r[ti])
        if ts>=10**15:
            ts//=1000
        t=pd.Timestamp(ts,unit="ms",tz="UTC")
        if (t.year,t.month)!=(spec[2],spec[3]):
            raise ValueError(f"funding source month mismatch {spec} {t}")
        val=float(r[rate_i])
        if not -1<val<1:
            raise ValueError(f"implausible funding {spec} {t}")
        out.append((ts//3_600_000*3_600_000,val))
    if not out:
        raise ValueError(f"empty genuine funding {spec}")
    return out


def download(spec):
    typ,sym,y,m=spec
    month=f"{y}-{m:02}"
    if typ=="kline":
        rel=f"klines/{sym}/5m/{sym}-5m-{month}.zip"
    elif typ=="mark":
        rel=f"markPriceKlines/{sym}/8h/{sym}-8h-{month}.zip"
    else:
        rel=f"fundingRate/{sym}/{sym}-fundingRate-{month}.zip"
    url="https://data.binance.vision/data/futures/um/monthly/"+rel
    data,receipt=csv_from_binance(url)
    if typ=="funding":
        parsed=rows_funding(data,spec)
    else:
        parsed=rows_candles(data,spec)
    expected_days=pd.Period(month,freq="M").days_in_month
    expected_n=expected_days*(288 if typ=="kline" else 3 if typ=="mark" else 3)
    if typ=="mark" and len(parsed)!=expected_n:
        # Only real complete 1h mark, NEVER interpolate mark price.
        backup=("https://data.binance.vision/data/futures/um/monthly/"
                f"markPriceKlines/{sym}/1h/{sym}-1h-{month}.zip")
        hourly,backup_receipt=csv_from_binance(backup)
        hours=rows_candles(hourly,("mark",sym,y,m))
        if len(hours)!=expected_days*24:
            raise ValueError(f"missing official 8h/1h mark {sym} {month}")
        if any(b[0]-a[0]!=3_600_000 for a,b in zip(hours,hours[1:])):
            raise ValueError(f"gapped official 1h mark {sym} {month}")
        merged=[]
        for i in range(0,len(hours),8):
            candles=hours[i:i+8]
            if len(candles)!=8 or candles[0][0]%(8*3_600_000)!=0:
                raise ValueError(f"bad 1h->8h mark group {sym}")
            merged.append((candles[0][0],candles[0][1],
                           max(x[2] for x in candles),
                           min(x[3] for x in candles),
                           candles[-1][4],sum(x[5] for x in candles)))
        receipt["partial_eighthour"]=receipt.copy()
        receipt.update(backup_receipt)
        receipt["reconstructed_from_genuine_complete_1h_mark"]=True
        parsed=merged
    if typ=="funding":
        if len(parsed)<expected_days*2:
            raise ValueError(f"funding settlement count inadequate {sym} {month} {len(parsed)}")
    elif len(parsed)!=expected_n:
        raise ValueError(f"missing original {typ} candles {sym} {month}: {len(parsed)}/{expected_n}")
    receipt.update({"type":typ,"symbol":sym,"month":month,"parsed_rows":len(parsed)})
    return spec,parsed,receipt


def store_data(grouped):
    from freqtrade.data.history.datahandlers.featherdatahandler import FeatherDataHandler
    from freqtrade.enums import CandleType
    datadir=OUT/"binance"
    (datadir/"futures").mkdir(parents=True,exist_ok=True)
    h=FeatherDataHandler(datadir)
    sizes={}
    for sym in SYMS:
        pair=sym.replace("USDT","/USDT:USDT")
        source=to_candle_frame(grouped[sym]["kline"],"5m",sym)
        if source.index.min()!=pd.Timestamp("2026-05-01T00:00:00Z") or source.index.max()!=pd.Timestamp("2026-10-31T23:55:00Z"):
            raise ValueError(f"frozen period differs {sym}")
        for tf in ("5m","1h","4h"):
            b=aggregate_5m(source,tf).reset_index()
            h.ohlcv_store(pair,tf,b,CandleType.FUTURES)
            sizes[f"{sym}_{tf}"]=len(b)
        mark=to_candle_frame(grouped[sym]["mark"],"8h",sym).reset_index()
        h.ohlcv_store(pair,"8h",mark,CandleType.MARK)
        funding=sorted(grouped[sym]["funding"])
        if len({t for t,_ in funding})!=len(funding):
            raise ValueError(f"duplicate funding settlements {sym}")
        f=pd.DataFrame({
            "date":pd.to_datetime([t for t,_ in funding],unit="ms",utc=True),
            "funding_rate":[rate for _,rate in funding],
        })
        h.ohlcv_store(pair,"8h",f,CandleType.FUNDING_RATE)
        sizes[f"{sym}_mark_8h"]=len(mark)
        sizes[f"{sym}_funding"]=len(f)
    return sizes


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pinned=verify_original()
    tasks=[(typ,sym,y,m) for typ in ("kline","mark","funding")
           for sym in SYMS for y,m in MONTHS]
    grouped={sym:{typ:[] for typ in ("kline","mark","funding")} for sym in SYMS}
    receipts=[]
    with ThreadPoolExecutor(max_workers=12) as pool:
        future_map={pool.submit(download,job):job for job in tasks}
        for future in as_completed(future_map):
            job,rows,receipt=future.result()
            grouped[job[1]][job[0]].extend(rows)
            receipts.append(receipt)
    sizes=store_data(grouped)
    result={
        "status":"R030_REAL_BINANCE_USDM_PINNED_ORIGINAL_SOURCE",
        "original":pinned,
        "months":[f"{y}-{m:02}" for y,m in MONTHS],
        "instruments":list(SYMS),
        "archives":len(receipts),
        "archive_receipts":sorted(receipts,key=lambda x:(x["symbol"],x["type"],x["month"])),
        "timeframes_and_sizes":sizes,
        "safety":"real futures archive and modelled native engine only; no verified execution or liquidation",
    }
    (OUT/"R030_OOS_SOURCE_RECEIPTS.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8",
    )
    print("R030_OOS_MARKET_READY",json.dumps({
        "archives":len(receipts),"source_blob":pinned["blob_sha"],
        "bars":sizes,
    },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
