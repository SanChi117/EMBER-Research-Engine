"""A227: pre-registered 5-minute PROXY of academic quarter-hour imbalance.

True Binance USD-M Futures, never Spot, no fabricated source receipts.
This is NOT the paper's first-10-second raw trade model. No orders.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"research/a221_wide_futures_screen"))
import a221_tsmom_genuine_futures as source  # noqa: E402

SYMS=("BTCUSDT","ETHUSDT","SOLUSDT")
START=(2024,1)
END=(2026,10)
PERIODS=(("2024","2024-01-01","2025-01-01"),
         ("2025","2025-01-01","2026-01-01"),
         ("2026_JAN_SEP","2026-01-01","2026-10-01"))
HORIZONS={"Q1_4H":48,"Q2_8H":96}  # 5min bars
COSTS={"base":0.00105,"stress":0.00225}


def months():
    y,m=START
    while (y,m)<END:
        yield y,m
        y,m=(y+1,1) if m==12 else (y,m+1)


def download_month(sym,y,m):
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/5m/{sym}-5m-{y}-{m:02}.zip"
    raw=source.fetch(url)
    sha=hashlib.sha256(raw).hexdigest()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members=[n for n in z.namelist() if n.endswith(".csv")]
        if len(members)!=1:
            raise ValueError(f"Expected exactly 1 kline CSV {url}")
        content=z.read(members[0])
    csv_sha=hashlib.sha256(content).hexdigest()
    rows=[]
    for row in csv.reader(io.StringIO(content.decode("utf8"))):
        if not row or not row[0].isdigit():
            continue
        ts=source.as_ms(row[0])
        o,h,l,c,vol=map(float,row[1:6])
        takerbuy=float(row[9])
        if not (0<l<=min(o,c)<=max(o,c)<=h and 0<=takerbuy<=vol+1e-7 and vol>=0):
            raise ValueError(f"Malformed USD-M kline or taker flow {sym}/{y}/{m}")
        rows.append((ts,o,h,l,c,vol,takerbuy))
    days=pd.Period(f"{y}-{m:02}",freq="M").days_in_month
    if len(rows)!=days*24*12:
        raise ValueError(f"Unexpected missing 5m source bars {url} expected={days*24*12} got={len(rows)}")
    return sym,rows,{"url":url,"zip_sha256":sha,"csv_sha256":csv_sha,"rows":len(rows)}


def get_data(manifest):
    jobs=[]
    for y,m in months():
        for sym in SYMS:
            jobs.append(("price",sym,y,m))
            jobs.append(("funding",sym,y,m))
    candles={s:[] for s in SYMS};funding={s:[] for s in SYMS}
    receipts=[]
    with ThreadPoolExecutor(max_workers=14) as pool:
        fut=[]
        for kind,s,y,m in jobs:
            if kind=="price":
                fut.append(pool.submit(download_month,s,y,m))
            else:
                fut.append(pool.submit(source.load_one,(s,"funding",y,m),manifest))
        for completed in as_completed(fut):
            result=completed.result()
            if len(result)==3 and isinstance(result[0],str):
                s,rows,receipt=result
                candles[s].extend(rows)
            else:
                job,rows,receipt=result
                funding[job[0]].extend(rows)
            receipts.append(receipt)
    data={};funds={}
    for sym in SYMS:
        r=sorted(candles[sym])
        times=np.asarray([a[0] for a in r],dtype=np.int64)
        if times.size!=len(set(times)) or np.any(np.diff(times)!=300_000):
            raise ValueError(f"5m market missing data {sym}")
        idx=pd.to_datetime(times,unit="ms",utc=True)
        if idx[0]!=pd.Timestamp("2024-01-01T00:00:00Z") or idx[-1]!=pd.Timestamp("2026-09-30T23:55:00Z"):
            raise ValueError(f"Unexpected UTC start-end for {sym}")
        data[sym]=pd.DataFrame([x[1:] for x in r],
            columns=["open","high","low","close","volume","takerbuy"],
            index=idx)
        f=sorted(funding[sym])
        if len(set(x[0] for x in f))!=len(f):
            raise ValueError(f"Funding duplicate prints {sym}")
        funds[sym]={pd.Timestamp(t,unit="ms",tz="UTC"):rate for t,rate in f}
    return data,funds,receipts


def trades_for_year(df,funding,horizon,start,end,fee):
    idx=df.index
    arr=df[["open","high","low","close","volume","takerbuy"]].to_numpy(float)
    lo=int(idx.searchsorted(pd.Timestamp(start,tz="UTC")))
    end_i=int(idx.searchsorted(pd.Timestamp(end,tz="UTC")))
    eq=hwm=1000.0
    dd=0.0
    next_free=lo
    items=[];rejects=Counter()
    for i in range(lo+12,end_i-2):
        if i<next_free:
            continue
        stamp=idx[i]
        if stamp.minute%15!=0:
            continue
        vol=arr[i,4]
        if vol<=0:continue
        imbalance=2*arr[i,5]/vol-1
        if abs(imbalance)<=1e-12:
            continue
        side=1 if imbalance>0 else -1
        entry_i=i+1  # completed first 5min candle only
        entry=float(arr[entry_i,0])
        stop=float(np.min(arr[i-11:i+1,2])) if side==1 else float(np.max(arr[i-11:i+1,1]))
        dist=side*(entry-stop)
        if dist<=0:
            rejects["next_open_beyond_stop"]+=1
            continue
        qty=min(eq*0.005/dist,eq/entry)
        if qty<=0:
            continue
        beginning=eq
        in_fee=qty*entry*fee
        paid=0.0
        reason="";exitprice=None;exit_i=None
        # Time-box no future-period data: flat before year changes.
        until=min(entry_i+horizon,end_i-1)
        for j in range(entry_i,until+1):
            t=idx[j]
            p_open,p_high,p_low=map(float,arr[j,:3])
            if j>entry_i and t in funding:
                paid+=-side*qty*p_open*funding[t]
            mark=beginning-in_fee+paid+side*qty*(p_open-entry)
            hwm=max(hwm,mark)
            if j==until:
                reason="time_exit";exitprice=p_open;exit_i=j;break
            adverse=p_low if side==1 else p_high
            wick_eq=beginning-in_fee+paid+side*qty*(adverse-entry)
            dd=min(dd,wick_eq/hwm-1)
            if side*(p_open-stop)<=0:
                reason="gap_through_stop";exitprice=p_open;exit_i=j;break
            if side*(adverse-stop)<=0:
                reason="stop_model";exitprice=stop;exit_i=j;break
        if exit_i is None:
            raise RuntimeError("position unresolved")
        fee_out=qty*exitprice*fee
        pnl=side*qty*(exitprice-entry)+paid-in_fee-fee_out
        eq=beginning+pnl
        hwm=max(hwm,eq)
        dd=min(dd,eq/hwm-1)
        next_free=exit_i+1
        items.append({"signal_utc":stamp.isoformat(),"entry_utc":idx[entry_i].isoformat(),
            "exit_utc":idx[exit_i].isoformat(),"side":side,
            "observed_5m_imbalance":round(float(imbalance),7),
            "entry_px":round(entry,7),"stop_px":round(stop,7),
            "exit_px":round(exitprice,7),"qty":round(qty,9),
            "pnl_usdt":round(pnl,6),
            "fee_usdt":round(in_fee+fee_out,6),"funding_usdt":round(paid,6),
            "exit":reason,"equity":round(eq,6)})
        if eq<=0:
            raise ValueError("No leverage but equity has been lost entirely")
    return {"return_pct":round((eq/1000-1)*100,5),"count":len(items),
        "win_pct":round(100*sum(z["pnl_usdt"]>0 for z in items)/len(items),3) if items else None,
        "max_hourly_wick_dd_pct_approx":round(dd*100,5),
        "worst_trade_usdt":round(min((x["pnl_usdt"] for x in items),default=0),5),
        "sum_funding_usdt":round(sum(x["funding_usdt"] for x in items),5),
        "sum_fees_usdt":round(sum(x["fee_usdt"] for x in items),5),
        "rejections":dict(rejects)},items


def main():
    mandate=json.loads((ROOT/"config/research_mandate.lock.json").read_text())
    assert mandate["state"]=="LOCKED_USER_ONLY" and mandate["scope"]=="BINANCE_USDT_M_FUTURES"
    manifest=json.loads((ROOT/"research/a217_trendrider_original/evidence/source_manifest.json").read_text())
    print("A227 authentic Binance 5m opening flow proxy and funding (99 price+99 signed funding ZIP)",flush=True)
    prices,funding,receipts=get_data(manifest)
    summ={};trade_logs={}
    for label,horizon in HORIZONS.items():
        summ[label]={};trade_logs[label]={}
        for y,a,b in PERIODS:
            summ[label][y]={};trade_logs[label][y]={}
            for name,cost in COSTS.items():
                coin={};trade_logs[label][y][name]={}
                for sym in SYMS:
                    res,logs=trades_for_year(prices[sym],funding[sym],horizon,a,b,cost)
                    coin[sym]=res;trade_logs[label][y][name][sym]=logs
                summ[label][y][name]={
                    "three_equal_sleeve_net_pct":round(sum(v["return_pct"] for v in coin.values())/3,5),
                    "ntrades":sum(v["count"] for v in coin.values()),
                    "worst_coin_hourly_wick_dd_pct":min(v["max_hourly_wick_dd_pct_approx"] for v in coin.values()),
                    "coins":coin
                }
    gates={}
    for h in HORIZONS:
        pass_years=[y for y in ("2025","2026_JAN_SEP")
            if summ[h][y]["stress"]["three_equal_sleeve_net_pct"]>0
            and summ[h][y]["stress"]["ntrades"]>=50
            and summ[h][y]["stress"]["worst_coin_hourly_wick_dd_pct"]>=-20]
        gates[h]={"two_later_years_pass_stress":len(pass_years)==2,"passed_later":pass_years,
                  "verified_original_strategy":False,"paper_or_live_allowed":False}
    folder=HERE/"evidence";folder.mkdir(exist_ok=True)
    result={
        "scope":"paper-grounded proxy research hypothesis, not author 10sec original",
        "paper":"Kim Hansen (2026) arxiv:2607.09426",
        "market":"actual Binance USD-M Futures BTC ETH SOL 5m OHLCV and funding",
        "genuine_archive_receipts":len(receipts),
        "archive_sha256":sorted(receipts,key=lambda x:x.get("url",x.get("key"))),
        "cost_bp_one_side":{"base":10.5,"stress":22.5},
        "years":summ,"gates":gates,"no_real_orders":True,"no_official_mark_liq_or_10sec_flow":True
    }
    (folder/"A227_NATIVE_QUARTER_HOUR_PROXY_ECONOMICS.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    (folder/"A227_NATIVE_5M_PROXY_TRADE_LEDGER.json").write_text(json.dumps(trade_logs,ensure_ascii=False)+"\n")
    print(json.dumps({"archives":len(receipts),"gates":gates,
        "results":{h:{y:{c:[summ[h][y][c]["three_equal_sleeve_net_pct"],
                            summ[h][y][c]["ntrades"],summ[h][y][c]["worst_coin_hourly_wick_dd_pct"]]
                         for c in COSTS} for y,_,_ in PERIODS} for h in HORIZONS}},
        ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
