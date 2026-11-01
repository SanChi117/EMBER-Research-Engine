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
import urllib.error
import urllib.request
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
MONTHS = tuple((2023,m) for m in range(5,11))
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
        # Source recovery is purely data integrity, not strategy tuning.
        # Keep each complete published 8h bar. For a missing 8h bucket,
        # accept ONLY exact 8 complete original 1h candles OR 96 complete
        # original 5m mark candles. No interpolation, last-price, SPOT or
        # trading-price substitution.
        partial={x[0]:x for x in parsed}
        backups=[]
        step=8*3_600_000
        start=int(pd.Timestamp(f"{month}-01T00:00:00Z").timestamp()*1000)
        wanted=[start+i*step for i in range(expected_n)]
        for smaller,period_ms,count in (("1h",3_600_000,8),("5m",300_000,96)):
            missing=[t for t in wanted if t not in partial]
            if not missing:
                break
            backup=("https://data.binance.vision/data/futures/um/monthly/"
                    f"markPriceKlines/{sym}/{smaller}/{sym}-{smaller}-{month}.zip")
            raw_fallback, source_receipt=csv_from_binance(backup)
            samples=rows_candles(raw_fallback,("mark",sym,y,m))
            sample_map={b[0]:b for b in samples}
            count_filled=0
            for t in missing:
                segment=[sample_map.get(t+j*period_ms) for j in range(count)]
                if any(x is None for x in segment):
                    continue
                merged=(t,segment[0][1],max(x[2] for x in segment),
                        min(x[3] for x in segment),segment[-1][4],
                        sum(x[5] for x in segment))
                partial[t]=merged
                count_filled+=1
            backups.append({
                "verified_original_backup":source_receipt,
                "raw_mark_resolution":smaller,
                "complete_8h_groups_reconstructed":count_filled,
                "archive_rows":len(samples),
            })
        # One additional original source path, without interpolation:
        # an exact UTC-day original Binance Vision daily MARK archive, or
        # the official historical USD-M markPriceKlines REST endpoint.
        missing_now=[t for t in wanted if t not in partial]
        if missing_now:
            days=sorted({pd.Timestamp(t,unit="ms",tz="UTC").strftime("%Y-%m-%d")
                         for t in missing_now})
            official_recovery=[]
            for day in days:
                day_start=pd.Timestamp(day+"T00:00:00Z")
                day_ms=int(day_start.timestamp()*1000)
                # Prefer daily ZIP from same official Binance Vision, when
                # the monthly archive has an omitted day.
                day_rows=None
                for timeframe,interval,count in (("1h",3_600_000,8),
                                                  ("5m",300_000,96)):
                    daily=("https://data.binance.vision/data/futures/um/daily/"
                           f"markPriceKlines/{sym}/{timeframe}/"
                           f"{sym}-{timeframe}-{day}.zip")
                    try:
                        raw_daily,receipt_daily=csv_from_binance(daily)
                    except (OSError,ValueError,urllib.error.HTTPError) as exc:
                        official_recovery.append({"daily_source_blocked":daily,
                                                  "type":type(exc).__name__})
                        continue
                    source=rows_candles(raw_daily,("mark",sym,y,m))
                    lookup={z[0]:z for z in source}
                    complete=True
                    recon={}
                    for k in range(3):
                        bucket_start=day_ms+k*8*3_600_000
                        group=[lookup.get(bucket_start+j*interval) for j in range(count)]
                        if any(z is None for z in group):
                            complete=False
                            break
                        recon[bucket_start]=(
                            bucket_start,group[0][1],max(z[2] for z in group),
                            min(z[3] for z in group),group[-1][4],
                            sum(z[5] for z in group),
                        )
                    if complete:
                        partial.update({t:r for t,r in recon.items() if t in wanted})
                        official_recovery.append({
                            "full_day_from_original_daily_mark":daily,
                            "sha256":receipt_daily["zip_sha256"],
                            "native_resolution":timeframe,
                        })
                        day_rows=source
                        break
                if day_rows is not None:
                    continue
                # Official futures API, raw payload SHA saved. If REST access
                # is blocked this remains explicit DATA_BLOCKED.
                api=("https://fapi.binance.com/fapi/v1/markPriceKlines?"
                     f"symbol={sym}&interval=1h&startTime={day_ms}"
                     f"&endTime={day_ms+86_400_000-1}&limit=100")
                try:
                    req=urllib.request.Request(api,headers={
                        "User-Agent":"EMBER-original-futures-data-audit/1.0"
                    })
                    with urllib.request.urlopen(req,timeout=25) as response:
                        api_bytes=response.read()
                    api_raw=json.loads(api_bytes)
                    if not isinstance(api_raw,list) or len(api_raw)!=24:
                        raise ValueError("official mark API not 24 complete hourly bars")
                    api_lookup={}
                    for z in api_raw:
                        t=int(z[0])
                        op,high,low,cl=map(float,z[1:5])
                        if not(low>0 and low<=min(op,cl)<=max(op,cl)<=high):
                            raise ValueError("invalid official futures mark OHLC")
                        api_lookup[t]=(t,op,high,low,cl,0.)
                    if set(api_lookup)!=set(day_ms+j*3_600_000 for j in range(24)):
                        raise ValueError("API mark archive incomplete UTC day")
                    for k in range(3):
                        t=day_ms+k*8*3_600_000
                        group=[api_lookup[t+j*3_600_000] for j in range(8)]
                        if t in wanted:
                            partial[t]=(t,group[0][1],max(z[2] for z in group),
                                        min(z[3] for z in group),
                                        group[-1][4],0.)
                    official_recovery.append({
                        "genuine_usdm_mark_historical_api":api,
                        "raw_response_sha256":hashlib.sha256(api_bytes).hexdigest(),
                        "all_24_hourly_bars_validated":True,
                    })
                except (OSError,ValueError,urllib.error.HTTPError) as exc:
                    official_recovery.append({"api_source_blocked":api,
                                              "error":str(exc)[:300]})
            backups.extend(official_recovery)
        if len(partial)!=expected_n:
            missing=[str(pd.Timestamp(t,unit="ms",tz="UTC"))
                     for t in wanted if t not in partial]
            raise ValueError(
                f"INCOMPLETE_OFFICIAL_MARK_NO_IMPUTATION {sym} {month} "
                f"native={len(parsed)} after_fallback={len(partial)}/{expected_n} "
                f"missing={missing[:20]} receipt={backups}"
            )
        parsed=[partial[t] for t in wanted]
        receipt["source_native_8h_original"]={
            "url":receipt["url"],"sha":receipt["zip_sha256"],
            "rows":len(data),
        }
        receipt["genuine_complete_smaller_mark_backups"]=backups
        receipt["mark_source_recovery"]="native if available, else complete 1h/5m only"
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
        if source.index.min()!=pd.Timestamp("2023-05-01T00:00:00Z") or source.index.max()!=pd.Timestamp("2023-10-31T23:55:00Z"):
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
