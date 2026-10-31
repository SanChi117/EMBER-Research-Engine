"""A228: source-authenticated five ORIGINAL Freqtrade algorithms and Binance USD-M futures archive preparation.

NO changes to any strategy algorithms, no trading/broker keys, no orders.
Data comes exclusively from genuine Binance Vision USD-M OHLCV, mark and
funding sources, with signed funding receipts validated against A217.
Market '5m' aggregated to 15m, 1h, 4h strictly from complete 5-minute bars.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=HERE/"generated"
sys.path.insert(0,str(ROOT/"research/a221_wide_futures_screen"))
import a221_tsmom_genuine_futures as genuine  # noqa

PINS={
 "DualTrendCompressionRestartShortV1Strategy":{
  "repo":"wangc-joker/ft_userdata","commit":"6833cb9b4bc5bfb01c3f5829ff11cc02b0814fd9",
  "path":"user_data/strategies/DualTrendCompressionRestartShortV1Strategy.py",
  "git_blob":"36cfb029cd7dc871160b037548db2c57de852969"},
 "TrendFollowing":{
  "repo":"krantikaridev/freqtrade","commit":"11d7d66c60cf49a148cb61619b8061dc40d2510c",
  "path":"strategies/TrendFollowing.py","git_blob":"ee2293e19f3cdecb082525f6d55a166249f74eb2"},
 "NASOSv7LongShort":{
  "repo":"remiotore/ccxt-freqtrade","commit":"44beaeb6a420cd8e9f2e4ea93e11d6cfa192ee03",
  "path":"strategies/NASOSv7_FuturesC.py","git_blob":"172fd2b5e76cb1b14d4c9547b6046bff7f19ba7a"},
 "BearRegimeShortV1":{
  "repo":"IvPalmer/Master-Trader","commit":"8e29d170982c36a502de2c6ed14a80c6510c4921",
  "path":"ft_userdata/user_data/strategies/BearRegimeShortV1.py",
  "git_blob":"a6c62639e60a28b050a462f646241e7a2ba9076c"},
 "Risk_Stair_S5":{
  "repo":"linhuang1212-coder/crypto-quant-trading",
  "commit":"63c012a0329a280f99fe57896456d4b9363c9c71",
  "path":"user_data/strategies/risk_exp/Risk_Stair_S5.py",
  "git_blob":"9b6ba1f5466727da1e9446f4e283b1c555fca59b"}
}
COINS=("BTCUSDT","ETHUSDT","SOLUSDT")
TFS=("5m","15m","1h","4h")
MONTH_START=(2023,11)
MONTH_END_EXCL=(2026,6)  # valid Jan-May 2026 only, June mark data has missing full day


def month_iter():
    y,m=MONTH_START
    while (y,m)<MONTH_END_EXCL:
        yield y,m
        y,m=(y+1,1) if m==12 else (y,m+1)


def validate_pin():
    d=OUT/"strategies"
    d.mkdir(parents=True,exist_ok=True)
    result={}
    for name,p in PINS.items():
        url=f"https://raw.githubusercontent.com/{p['repo']}/{p['commit']}/{p['path']}"
        raw=genuine.fetch(url)
        actual=genuine.blob_sha(raw)
        if actual!=p["git_blob"]:
            raise ValueError(f"Original SHA drift {name} {actual}")
        # preserve exact original bytes incl CRLF rather than rewriting
        filename=d/(name+".py")
        filename.write_bytes(raw)
        result[name]={"repo":p["repo"],"commit":p["commit"],"git_blob":actual,
                       "source_sha256":hashlib.sha256(raw).hexdigest(),
                       "path":p["path"],"lines":len(raw.splitlines())}
    print("PINNED_STRATEGIES_OK",json.dumps(result,ensure_ascii=False),flush=True)
    return result


def csv_zip_content(url):
    raw=genuine.fetch(url)
    sha=hashlib.sha256(raw).hexdigest()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=[n for n in z.namelist() if n.endswith(".csv")]
        if len(entries)!=1:
            raise ValueError(f"Expected 1 Binance monthly CSV {url}: {entries}")
        csvraw=z.read(entries[0])
    return list(csv.reader(io.StringIO(csvraw.decode("utf8")))),{
      "url":url,"zip_sha256":sha,"csv_sha256":hashlib.sha256(csvraw).hexdigest(),
      "raw_csv_rows":len(csvraw.splitlines())}


def month_fetch(job,receipt_manifest):
    kind,sym,y,m=job
    if kind=="kline":
        url=f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/5m/{sym}-5m-{y}-{m:02}.zip"
    elif kind=="mark":
        url=f"https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{sym}/8h/{sym}-8h-{y}-{m:02}.zip"
    else:
        # Genuine funding from A217 SHA when available (2024+).
        # For 2023 warmup only, verify official ZIP and CSV SHA directly;
        # source contains actual funding settlements, never guessed rates.
        if (y,m)>=(2024,1):
            _,rows,receipt=genuine.load_one((sym,"funding",y,m),receipt_manifest)
            return (job,rows,receipt)
        url=f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{sym}/{sym}-fundingRate-{y}-{m:02}.zip"
        raw,receipt=csv_zip_content(url)
        names=[x.strip().lower().replace("_","") for x in raw[0]]
        it,ir=names.index("calctime"),names.index("lastfundingrate")
        rows=[(genuine.as_ms(x[it]),float(x[ir])) for x in raw[1:] if x and x[it].isdigit()]
        if len(rows)<75:
            raise ValueError("Insufficient actual 2023 warmup funding "+url)
        receipt["source_only_warmup"]=True
        receipt["parsed_rows"]=len(rows)
        return (job,rows,receipt)
    raw,receipt=csv_zip_content(url)
    rows=[]
    for rec in raw:
        if not rec or not rec[0].isdigit():
            continue
        stamp=genuine.as_ms(rec[0])
        v=tuple(map(float,rec[1:6]))
        if not (0<v[2]<=min(v[0],v[3])<=max(v[0],v[3])<=v[1] and v[4]>=0):
            raise ValueError(f"Invalid official {kind} OHLCV {sym} {y}-{m}")
        rows.append((stamp,*v))
    days=pd.Period(f"{y}-{m:02}",freq="M").days_in_month
    expected=int(days*24*(12 if kind=="kline" else 1/8))
    if kind=="mark" and len(rows)!=expected:
        # Binance Vision 8h 2026-06 published 87/90 native rows.
        # NEVER fabricate missing mark; instead source genuine 1h mark
        # snapshots and aggregate only if all original 1h hours exist.
        backup=f"https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{sym}/1h/{sym}-1h-{y}-{m:02}.zip"
        hr_csv,hr_receipt=csv_zip_content(backup)
        hourly=[]
        for rec in hr_csv:
            if not rec or not rec[0].isdigit():
                continue
            stamp=genuine.as_ms(rec[0]);val=tuple(map(float,rec[1:6]))
            if not (0<val[2]<=min(val[0],val[3])<=max(val[0],val[3])<=val[1]):
                raise ValueError(f"Bad genuine mark 1h fallback {backup}")
            hourly.append((stamp,*val))
        hourly.sort()
        if len(hourly)!=days*24 or any(b[0]-a[0]!=3_600_000 for a,b in zip(hourly,hourly[1:])):
            raise ValueError(f"OFFICIAL_MARK_SOURCE_INCOMPLETE 8h={len(rows)}/{expected}, 1h={len(hourly)}/{days*24}: {sym}/{y}-{m}")
        merged=[]
        for idx in range(0,len(hourly),8):
            pack=hourly[idx:idx+8]
            assert len(pack)==8 and pack[0][0]%(8*3_600_000)==0
            merged.append((pack[0][0],pack[0][1],max(v[2] for v in pack),
                          min(v[3] for v in pack),pack[-1][4],sum(v[5] for v in pack)))
        receipt["source_8h_original_partial_zip_sha256"]=receipt["zip_sha256"]
        receipt["recovered_from_genuine_1h_mark_archive"]=hr_receipt
        receipt["reconstruction"]="8 fully observed consecutive genuine 1h mark candles per 8h bar, no synthetic imputation"
        rows=merged
        receipt["url"]=backup
        receipt["zip_sha256"]=hr_receipt["zip_sha256"]
        receipt["csv_sha256"]=hr_receipt["csv_sha256"]
    if len(rows)!=expected:
        raise ValueError(f"Missing {kind} monthly values {sym}/{y}-{m} n={len(rows)} expected={expected}")
    receipt["parsed_rows"]=len(rows)
    return job,rows,receipt


def to_candle_frame(rows,tf,origin):
    rows=sorted(rows)
    stamps=np.asarray([r[0] for r in rows],dtype=np.int64)
    if len(stamps)!=len(set(stamps)):
        raise ValueError(f"Duplicate raw bars: {origin}")
    resolution=300_000 if tf=="5m" else 28_800_000
    if np.any(np.diff(stamps)!=resolution):
        raise ValueError(f"Gaps/overlap native {origin} data")
    times=pd.to_datetime(stamps,unit="ms",utc=True)
    frame=pd.DataFrame([r[1:] for r in rows],
       index=times,columns=["open","high","low","close","volume"])
    frame.index.name="date"
    return frame


def aggregate_5m(frame,timeframe):
    if timeframe=="5m":
        return frame.copy()
    rules={"15m":3,"1h":12,"4h":48}
    pandas_rule={"15m":"15min","1h":"1h","4h":"4h"}
    if timeframe not in rules:raise ValueError(timeframe)
    freq=pandas_rule[timeframe]
    count=frame.open.resample(freq,closed="left",label="left").count()
    if (count!=rules[timeframe]).any():
        raise ValueError(f"Aggregation not from complete {timeframe} UTC bins")
    return frame.resample(freq,closed="left",label="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum"
    })


def store_native_market(candles,marks,settlements):
    from freqtrade.data.history.datahandlers.featherdatahandler import FeatherDataHandler
    from freqtrade.enums import CandleType
    datadir=OUT/"binance"
    (datadir/"futures").mkdir(parents=True,exist_ok=True)
    dh=FeatherDataHandler(datadir)
    sizes={}
    for sym in COINS:
        pair=sym.replace("USDT","/USDT:USDT")
        frame=to_candle_frame(candles[sym],"5m",sym)
        if frame.index[0]!=pd.Timestamp("2023-11-01T00:00:00Z") or frame.index[-1]!=pd.Timestamp("2026-05-31T23:55:00Z"):
            raise ValueError(f"Unexpected study source window {sym}")
        for tf in TFS:
            tfdata=aggregate_5m(frame,tf).reset_index()
            dh.ohlcv_store(pair,tf,tfdata,CandleType.FUTURES)
            sizes[f"{sym}_{tf}"]=len(tfdata)
        marksdf=to_candle_frame(marks[sym],"8h","mark "+sym).reset_index()
        dh.ohlcv_store(pair,"8h",marksdf,CandleType.MARK)
        fundrows=sorted(settlements[sym])
        if len(fundrows)!=len(set(k for k,_ in fundrows)):
            raise ValueError(f"Duplicate real funding timestamps {sym}")
        fundingdf=pd.DataFrame({"date":pd.to_datetime([k for k,_ in fundrows],unit="ms",utc=True),
                                "funding_rate":[float(v) for _,v in fundrows]})
        dh.ohlcv_store(pair,"8h",fundingdf,CandleType.FUNDING_RATE)
        sizes[f"{sym}_mark_8h"]=len(marksdf)
        sizes[f"{sym}_actual_funding"]=len(fundingdf)
    print("NATIVE_FUTURES_DATA_READY",json.dumps(sizes),flush=True)
    return sizes


def main():
    doc=json.loads((ROOT/"config/research_mandate.lock.json").read_text("utf8"))
    assert doc["state"]=="LOCKED_USER_ONLY" and doc["scope"]=="BINANCE_USDT_M_FUTURES"
    OUT.mkdir(parents=True,exist_ok=True)
    original_pins=validate_pin()
    manifest=json.loads((ROOT/"research/a217_trendrider_original/evidence/source_manifest.json").read_text("utf8"))
    tasks=[(typ,sym,y,m) for y,m in month_iter() for sym in COINS for typ in ("kline","mark","funding")]
    candles={s:[] for s in COINS}
    marks={s:[] for s in COINS}
    settlements={s:[] for s in COINS}
    receipts=[]
    with ThreadPoolExecutor(max_workers=14) as pool:
        jobs=[pool.submit(month_fetch,t,manifest) for t in tasks]
        for n,future in enumerate(as_completed(jobs),1):
            job,raw,receipt=future.result()
            kind,sym,_,_=job
            {"kline":candles,"mark":marks,"funding":settlements}[kind][sym].extend(raw)
            receipt["type"]=kind
            receipts.append(receipt)
            if n%45==0:
                print(f"GENUINE_USDM_SOURCE_DONE {n}/{len(jobs)}",flush=True)
    sizes=store_native_market(candles,marks,settlements)
    if len(receipts)!=len(tasks):raise ValueError("Archive count mismatch")
    data={"scope":"PINNED_FIVE_UNMODIFIED_BINANCE_USDM_NATIVE_SOURCE",
          "original_pins":original_pins,"market_n":len(receipts),
          "price_mark_funding_count":{"5m":len([x for x in receipts if x["type"]=="kline"]),
             "mark":len([x for x in receipts if x["type"]=="mark"]),
             "funding":len([x for x in receipts if x["type"]=="funding"])},
          "dataframe_rows":sizes,"archive_receipts":sorted(receipts,key=lambda x:x.get("url",x.get("key")))}
    (OUT/"A228_ORIGINAL_AND_MARKET_RECEIPTS.json").write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n","utf8")
    print("A228_DATA_PREP_OK",json.dumps({k:v for k,v in data.items() if k!="archive_receipts"}),flush=True)


if __name__=="__main__":
    main()
