"""TCFI prereg Binance USD-M 1D/4H trend-continuation + 1H failed counterinitiative.

Research-only diagnostic, no orders, no post-hoc tuning. See PRE_REGISTERED.
Original Binance Vision 1H and actual funding archives verified against .CHECKSUM.
Baseline candidates share SAME trade outcome and execution with conditional tag;
1H is exclusively information available before next-4H-open entry.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import time
import urllib.request
import zipfile
from bisect import bisect_left, bisect_right
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

SYMS = (
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "LINKUSDT",
    "AVAXUSDT", "ADAUSDT", "OPUSDT", "ARBUSDT", "LDOUSDT", "NEARUSDT",
    "INJUSDT", "SUIUSDT", "DOGEUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT",
    "FILUSDT", "AAVEUSDT", "UNIUSDT", "ATOMUSDT", "ETCUSDT", "TRXUSDT",
)
YEARS = (2024, 2025)
MONTHS = tuple(range(3,12))
START_MONTH = 3
COHORT_MONTHS = (7,8,9)
COSTS = {"BASE":.004, "STRESS":.0065}
BASE_URL = "https://data.binance.vision/data/futures/um/monthly"
BAR_COLS = ("open","high","low","close","volume")
MSH = 3_600_000
STOP_BUF_ATR = .3
TRAIL_LOOKBACK = 3
ATR_N = 14
IMPULSE_ATR = 1.5
PULL_MIN_ATR = .4
PULL_MAX_ATR = 2.5
MAX_DISTANCE_ATR = 5.
WEEK_BOOTSTRAPS = 1000


def get(url: str) -> bytes:
    err = None
    for attempt in range(3):
        try:
            r = urllib.request.Request(url,headers={"User-Agent":"EMBER-TCFI-PreRegistered-20261101"})
            with urllib.request.urlopen(r, timeout=45) as response:
                return response.read()
        except (OSError,TimeoutError) as e:
            err=e
            time.sleep(attempt+1)
    raise RuntimeError(f"source unavailable {url}: {err}")


def original(spec:tuple[str,int,int,str]):
    sym,year,month,kind=spec
    ym=f"{year}-{month:02d}"
    if kind=="1h":
        part=f"klines/{sym}/1h/{sym}-1h-{ym}.zip"
    else:
        part=f"fundingRate/{sym}/{sym}-fundingRate-{ym}.zip"
    url=f"{BASE_URL}/{part}"
    zipped=get(url)
    published=get(url+".CHECKSUM").decode("utf-8-sig").split()[0].lower()
    digest=hashlib.sha256(zipped).hexdigest()
    if published!=digest:
        raise ValueError(f"official Binance SHA mismatch {url}")
    with zipfile.ZipFile(io.BytesIO(zipped)) as z:
        members=[n for n in z.namelist() if n.endswith(".csv")]
        if len(members)!=1:
            raise ValueError(f"ambiguous monthly original {url}")
        raw=z.read(members[0])
    src=list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    result=[]
    if kind=="1h":
        for row in src:
            if not row or not row[0].isdigit():
                continue
            stamp=int(row[0])
            o,hi,lo,cl,vol=map(float,row[1:6])
            if stamp%MSH or not(0<lo<=min(o,cl)<=max(o,cl)<=hi and vol>=0):
                raise ValueError(f"bad USD-M 1h candle {url} {stamp}")
            if datetime.fromtimestamp(stamp/1000,timezone.utc).strftime("%Y-%m")!=ym:
                raise ValueError(f"wrong month in raw USD-M {url} {stamp}")
            result.append((stamp,o,hi,lo,cl,vol))
        days=pd.Period(ym,freq="M").days_in_month
        if len(result)!=24*days:
            raise ValueError(f"USD-M monthly bars missing {url} {len(result)} vs {24*days}")
    else:
        hdr=[x.lower().strip().replace("_","") for x in src[0]]
        it,ir=hdr.index("calctime"),hdr.index("lastfundingrate")
        for row in src[1:]:
            if not row or not row[it].isdigit():
                continue
            stamp=int(row[it])
            if stamp>=10**15:
                stamp//=1000
            value=float(row[ir])
            if not math.isfinite(value) or abs(value)>.1:
                raise ValueError(f"bad funding {url} {stamp}")
            if datetime.fromtimestamp(stamp/1000,timezone.utc).strftime("%Y-%m")!=ym:
                raise ValueError(f"funding date wrong month {url} {stamp}")
            result.append((stamp,value))
        if len(result)<pd.Period(ym,freq="M").days_in_month*2:
            raise ValueError(f"missing settled Binance funding in {url} n={len(result)}")
    result.sort()
    if len({x[0] for x in result})!=len(result):
        raise ValueError(f"duplicate source timestamp {url}")
    receipt={"url":url,"official_checksum_sha256":published,"zip_sha256":digest,
             "csv_sha256":hashlib.sha256(raw).hexdigest(),"rows":len(result),
             "symbol":sym,"year":year,"month":month,"type":kind}
    return spec,result,receipt


def fetch_sources(out_dir:Path,workers:int):
    jobs=[(s,y,m,k) for s in SYMS for y in YEARS for m in MONTHS for k in ("1h","funding")]
    raw={(s,y,k):[] for s in SYMS for y in YEARS for k in ("1h","funding")}
    receipts=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(original,j):j for j in jobs}
        for count,f in enumerate(as_completed(futures),1):
            spec,rows,receipt=f.result()
            raw[(spec[0],spec[1],spec[3])].extend(rows)
            receipts.append(receipt)
            if count%100==0:
                print(f"OFFICIAL_USDM_VERIFIED {count}/{len(jobs)}",flush=True)
    source_summary=[]
    for sym in SYMS:
        for year in YEARS:
            for kind in ("1h","funding"):
                rows=raw[sym,year,kind]
                rows.sort()
                if kind=="1h":
                    begin=int(datetime(year,3,1,tzinfo=timezone.utc).timestamp()*1000)
                    end=int(datetime(year,12,1,tzinfo=timezone.utc).timestamp()*1000)
                    if rows[0][0]!=begin or rows[-1][0]!=end-MSH:
                        raise ValueError(f"wrong study clock {sym} {year}")
                    if any(b[0]-a[0]!=MSH for a,b in zip(rows,rows[1:])):
                        raise ValueError(f"USD-M source gap/overlap {sym} {year}")
                else:
                    if any(b[0]<=a[0] for a,b in zip(rows,rows[1:])):
                        raise ValueError(f"funding source disorder {sym} {year}")
                source_summary.append({"symbol":sym,"year":year,"kind":kind,
                                       "rows":len(rows)})
    out_dir.mkdir(parents=True,exist_ok=True)
    meta={"source":"Official Binance Vision USD-M monthly + companion .CHECKSUM",
          "dataset":"2024+2025 March-Nov predeclared 24 symbols 1h/funding",
          "receipts":sorted(receipts,key=lambda x:(x["year"],x["month"],x["symbol"],x["type"])),
          "counts":source_summary,"archives":len(receipts)}
    (out_dir/"ORIGINAL_BINANCE_FUTURES_SHA_RECEIPTS.json").write_text(
        json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("VERIFIED_SOURCE_ARCHIVES",len(receipts),flush=True)
    return raw,meta


def frame(rows):
    idx=pd.to_datetime([x[0] for x in rows],unit="ms",utc=True)
    return pd.DataFrame([x[1:] for x in rows],index=idx,columns=BAR_COLS)


def aggregate(hourly:pd.DataFrame,period:str,n:int):
    if period=="4h":
        freq="4h"
    elif period=="1D":
        freq="1D"
    else:
        raise ValueError(period)
    counts=hourly["open"].resample(freq,closed="left",label="left").count()
    if counts.empty or (counts!=n).any():
        raise ValueError(f"incomplete original hourly aggregation {period}")
    return hourly.resample(freq,closed="left",label="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum",
    })


def seeded_ema(values:list[float],n:int)->list[float|None]:
    result=[None]*len(values)
    if len(values)<n:return result
    result[n-1]=sum(values[:n])/n
    alpha=2/(n+1)
    for k in range(n,len(values)):
        result[k]=alpha*values[k]+(1-alpha)*result[k-1]
    return result


def atr_of(bars:pd.DataFrame)->list[float|None]:
    highs=bars.high.tolist()
    lows=bars.low.tolist()
    closes=bars.close.tolist()
    tr=[hi-lo if k==0 else max(hi-lo,abs(hi-closes[k-1]),abs(lo-closes[k-1]))
        for k,(hi,lo) in enumerate(zip(highs,lows))]
    out=[None]*len(tr)
    for k in range(ATR_N-1,len(tr)):
        out[k]=sum(tr[k+1-ATR_N:k+1])/ATR_N
    return out


def daily_direction(daily:pd.DataFrame,candidate_end:pd.Timestamp,ema20,ema50)->int:
    # daily INDEX is candle start; its CLOSE is only known after full 24h.
    positions=daily.index.searchsorted(candidate_end-pd.Timedelta(days=1),side="right")-1
    k=int(positions)
    if k<80 or k-5<0:return 0
    a,b,old=ema20[k],ema50[k],ema20[k-5]
    if a is None or b is None or old is None:return 0
    close=float(daily.close.iloc[k])
    if close>a>b and a>old:return 1
    if close<a<b and a<old:return -1
    return 0


def failed_counterinitiative(hourly:pd.DataFrame,end:pd.Timestamp,side:int)->bool:
    # Last 12 closed hours, and 6 prior hours per candidate. End never included.
    end_pos=int(hourly.index.searchsorted(end,side="left"))
    start=max(6,end_pos-12)
    for j in range(start,end_pos-1):
        prior=hourly.iloc[j-6:j]
        curr=hourly.iloc[j]
        follow=hourly.iloc[j+1:end_pos]
        if side==1:
            level=float(prior.low.min())
            fail=float(curr.low)<level and float(curr.close)>level
            continuation=bool((follow.close>float(curr.high)).any())
        else:
            level=float(prior.high.max())
            fail=float(curr.high)>level and float(curr.close)<level
            continuation=bool((follow.close<float(curr.low)).any())
        if fail and continuation:
            return True
    return False


def candidate_at(bars:pd.DataFrame,k:int,atr:list,daily:pd.DataFrame,ema20,ema50):
    if k<max(ATR_N+2,11):return None
    end=bars.index[k]+pd.Timedelta(hours=4)
    direction=daily_direction(daily,end,ema20,ema50)
    if not direction:return None
    a=atr[k-1]
    if a is None or a<=0:return None
    closes=bars.close
    lows=bars.low
    highs=bars.high
    impulse=direction*(float(closes.iloc[k-3])-float(closes.iloc[k-11]))
    if impulse<IMPULSE_ATR*a:return None
    p1=direction*(float(closes.iloc[k-2])-float(closes.iloc[k-3]))
    p2=direction*(float(closes.iloc[k-1])-float(closes.iloc[k-2]))
    recovery=direction*(float(closes.iloc[k])-float(closes.iloc[k-1]))
    if not(p1<0 and p2<0 and recovery>0):return None
    if direction==1:
        ext=float(lows.iloc[k-2:k].min())
        depth=float(closes.iloc[k-3])-ext
        stop=min(ext,float(lows.iloc[k]))-STOP_BUF_ATR*a
    else:
        ext=float(highs.iloc[k-2:k].max())
        depth=ext-float(closes.iloc[k-3])
        stop=max(ext,float(highs.iloc[k]))+STOP_BUF_ATR*a
    if not PULL_MIN_ATR*a<=depth<=PULL_MAX_ATR*a:return None
    return {"event_time":bars.index[k],"entry_time":end,
            "direction":direction,"stop":stop,"atr":a,"depth_atr":depth/a,
            "impulse_atr":impulse/a}


def settle_funding(stamps:list[int],rates:list[float],enter:int,exit:int,side:int)->float:
    lo=bisect_left(stamps,enter)
    hi=bisect_right(stamps,exit)
    return -side*sum(rates[lo:hi])


def replay(bars:pd.DataFrame,hourly:pd.DataFrame,entry:dict,
           funding_times:list[int],funding_rates:list[float],study_end:pd.Timestamp):
    start=entry["entry_time"]
    loc=hourly.index.searchsorted(start)
    if loc>=len(hourly) or hourly.index[loc]!=start:
        raise ValueError("entry next fully closed 4H open missing")
    px=float(hourly.open.iloc[loc])
    initial=float(entry["stop"])
    side=int(entry["direction"])
    risk=side*(px-initial)
    if risk<=0 or risk>MAX_DISTANCE_ATR*entry["atr"]:
        return None
    current_stop=initial
    end_pos=int(hourly.index.searchsorted(study_end,side="left"))
    for i in range(int(loc),end_pos):
        t=hourly.index[i]
        # At UTC 4H boundary, previous 3 bars are already complete.
        if t.hour%4==0:
            k=int(bars.index.searchsorted(t,side="left"))
            if k>=TRAIL_LOOKBACK and bars.index[k] == t:
                recent=bars.iloc[k-TRAIL_LOOKBACK:k]
                if side==1:
                    updated=float(recent.low.min())-STOP_BUF_ATR*entry["atr"]
                    current_stop=max(current_stop,updated)
                else:
                    updated=float(recent.high.max())+STOP_BUF_ATR*entry["atr"]
                    current_stop=min(current_stop,updated)
        candle=hourly.iloc[i]
        touched=(float(candle.low)<=current_stop if side==1
                 else float(candle.high)>=current_stop)
        if touched:
            price=min(current_stop,float(candle.open)) if side==1 else max(current_stop,float(candle.open))
            exit_stamp=int(t.value//1_000_000)
            entry_stamp=int(start.value//1_000_000)
            fund=settle_funding(funding_times,funding_rates,entry_stamp,exit_stamp,side)
            return {"exit_time":t,"exit_price":price,"entry_price":px,
                    "initial_stop":initial,"exit_type":"STRUCTURAL_TRAIL",
                    "risk_fraction":risk/px,"gross_pct":100*side*(price/px-1),
                    "funding_pct":100*fund,"closed":True}
    last=hourly.iloc[end_pos-1]
    terminal=hourly.index[end_pos-1]+pd.Timedelta(hours=1)
    entry_stamp=int(start.value//1_000_000)
    exit_stamp=int(terminal.value//1_000_000)
    fund=settle_funding(funding_times,funding_rates,entry_stamp,exit_stamp,side)
    return {"exit_time":terminal,"exit_price":float(last.close),"entry_price":px,
            "initial_stop":initial,"exit_type":"OPEN_MARK_TO_MARKET",
            "risk_fraction":risk/px,"gross_pct":100*side*(float(last.close)/px-1),
            "funding_pct":100*fund,"closed":False}


def simulate_symbol(sym,year,ohlc:list,funding:list):
    hourly=frame(ohlc)
    four=aggregate(hourly,"4h",4)
    daily=aggregate(hourly,"1D",24)
    atr=atr_of(four)
    dclose=daily.close.tolist()
    e20=seeded_ema(dclose,20)
    e50=seeded_ema(dclose,50)
    fund_stamps=[int(t) for t,_ in funding]
    fund_rates=[float(v) for _,v in funding]
    start=pd.Timestamp(f"{year}-07-01T00:00:00Z")
    last_entry=pd.Timestamp(f"{year}-10-01T00:00:00Z")
    last_replay=pd.Timestamp(f"{year}-12-01T00:00:00Z")
    h0=hourly.index[0]
    if hourly.index[-1]!=last_replay-pd.Timedelta(hours=1):
        raise ValueError(f"missing future execution bars {sym} {year}")
    events=[]
    candidates=0
    invalid_stops=0
    overlaps=0
    busy_until=h0
    for k in range(len(four)-1):
        t=four.index[k]
        if not(start<=t<last_entry):
            continue
        cand=candidate_at(four,k,atr,daily,e20,e50)
        if cand is None:
            continue
        candidates+=1
        if cand["entry_time"]<busy_until:
            overlaps+=1
            continue
        result=replay(four,hourly,cand,fund_stamps,fund_rates,last_replay)
        if result is None:
            invalid_stops+=1
            continue
        flag=failed_counterinitiative(hourly,cand["entry_time"],cand["direction"])
        record={
            "symbol":sym,"year":year,"entry_time":cand["entry_time"].isoformat(),
            "exit_time":result["exit_time"].isoformat(),
            "side":"LONG" if cand["direction"]==1 else "SHORT",
            "confirmed_1h":flag,
            "exit_type":result["exit_type"],"closed":result["closed"],
            "initial_stop":result["initial_stop"],"entry_price":result["entry_price"],
            "exit_price":result["exit_price"],"risk_fraction":result["risk_fraction"],
            "depth_atr":cand["depth_atr"],"impulse_atr":cand["impulse_atr"],
            "gross_pct":result["gross_pct"],"funding_pct":result["funding_pct"],
        }
        for scenario,cost in COSTS.items():
            net=result["gross_pct"]+result["funding_pct"]-100*cost
            record[scenario+"_net_pct"]=net
            record[scenario+"_net_R"]=net/(100*result["risk_fraction"])
        events.append(record)
        busy_until=result["exit_time"]
    return events,{"symbol":sym,"year":year,"all_4h_candidates":candidates,
                   "overlapping_candidates_rejected":overlaps,
                   "invalid_initial_stop":invalid_stops,"accepted":len(events),
                   "candidate_entry_without_lookahead":True}


def summary(events:list[dict],cost:str,closed_only:bool):
    sample=[e for e in events if not closed_only or e["closed"]]
    if not sample:return {"n":0,"mean_net_pct":None,"mean_R":None,"pf":None}
    returns=[e[cost+"_net_pct"] for e in sample]
    rvals=[e[cost+"_net_R"] for e in sample]
    wins=sum(v>0 for v in returns)
    gross_win=sum(max(0,x) for x in returns)
    gross_loss=-sum(min(0,x) for x in returns)
    return {
        "n":len(sample),"closed":sum(e["closed"] for e in sample),
        "censored_open":sum(not e["closed"] for e in sample),
        "mean_net_pct":round(sum(returns)/len(sample),7),
        "mean_net_R":round(sum(rvals)/len(rvals),7),
        "win_rate":round(wins/len(sample),6),
        "profit_factor":round(gross_win/gross_loss,6) if gross_loss else None,
        "sum_net_pct_over_separate_notional_positions":round(sum(returns),7),
        "note":"Per-trade statistics only, NOT total shared-wallet ROI",
    }


def boot_week_difference(events:list[dict],cost:str)->dict:
    d={}
    for e in events:
        if not e["closed"]:continue
        wk=e["entry_time"][:10]
        dt=datetime.fromisoformat(wk)
        iso=dt.isocalendar()
        key=f"{e['year']}-W{iso.week:02d}"
        d.setdefault(key,[]).append(e)
    keys=list(d)
    pos=[e[cost+"_net_pct"] for e in events if e["closed"] and e["confirmed_1h"]]
    neg=[e[cost+"_net_pct"] for e in events if e["closed"] and not e["confirmed_1h"]]
    if len(pos)<5 or len(neg)<5 or len(keys)<6:
        return {"status":"LOW_POWER","n_week_clusters":len(keys),
                "delta_mean_pct":None,"ci95":None}
    delta=sum(pos)/len(pos)-sum(neg)/len(neg)
    rng=random.Random(20261101)
    draws=[]
    for _ in range(WEEK_BOOTSTRAPS):
        sample=[e for w in (rng.choice(keys) for j in keys) for e in d[w]]
        a=[e[cost+"_net_pct"] for e in sample if e["confirmed_1h"]]
        b=[e[cost+"_net_pct"] for e in sample if not e["confirmed_1h"]]
        if a and b:
            draws.append(sum(a)/len(a)-sum(b)/len(b))
    if len(draws)<WEEK_BOOTSTRAPS*.8:
        return {"status":"LOW_POWER_BOOTSTRAP","n_week_clusters":len(keys)}
    draws.sort()
    return {"status":"COMPUTED","n_week_clusters":len(keys),
            "delta_mean_pct":round(delta,7),
            "ci95":[round(draws[int(.025*len(draws))],7),
                    round(draws[int(.975*len(draws))-1],7)],
            "causal_warning":"Selection groups share same entry-clock/risk, but this observational filter test does NOT prove mechanistic causation or portfolio edge."}



def pnl_mechanism_diagnostics(events:list[dict],cost:str):
    """Secondary descriptive diagnostics, NOT another signal/threshold optimization."""
    confirmed=[e for e in events if e["closed"] and e["confirmed_1h"]]
    values=sorted((e[cost+"_net_pct"] for e in confirmed),reverse=True)
    winners=[v for v in values if v>0]
    top5=sum(winners[:5])
    whole=sum(values)
    pair_rows=[]
    for sym in SYMS:
        x=[e for e in events if e["closed"] and e["symbol"]==sym]
        c=[e[cost+"_net_pct"] for e in x if e["confirmed_1h"]]
        u=[e[cost+"_net_pct"] for e in x if not e["confirmed_1h"]]
        pair_rows.append({
            "symbol":sym,"confirmed_n":len(c),"unconfirmed_n":len(u),
            "confirmed_mean_net_pct":round(sum(c)/len(c),7) if c else None,
            "unconfirmed_mean_net_pct":round(sum(u)/len(u),7) if u else None,
            "pair_delta_mean_pct":round(sum(c)/len(c)-sum(u)/len(u),7)
                                   if c and u else None,
        })
    matched=[p for p in pair_rows if p["confirmed_n"]>=2 and p["unconfirmed_n"]>=2]
    positive=sum(p["pair_delta_mean_pct"]>0 for p in matched)
    side_metrics={
        side:summary([e for e in confirmed if e["side"]==side],cost,True)
        for side in ("LONG","SHORT")
    }
    gross_conc=top5/sum(winners) if winners else None
    return {
        "confirmed_top5_winners_total_net_pct_notional_sum":round(top5,7),
        "confirmed_total_net_pct_notional_sum":round(whole,7),
        "confirmed_top5_share_of_gross_positive_trade_pnl":round(gross_conc,7)
                                                         if gross_conc is not None else None,
        "confirmed_median_net_pct":values[len(values)//2] if values else None,
        "confirmed_top5_withheld_pnl_mean_pct":round(
            (whole-top5)/(len(values)-min(5,len(winners))),7
        ) if len(values)>min(5,len(winners)) else None,
        "matched_pairs_min2_per_arm":len(matched),
        "matched_pairs_positive_filter_delta":positive,
        "per_symbol_groups":pair_rows,
        "by_direction_confirmed":side_metrics,
        "warning":"Top-five-withheld is a descriptive stress check on outcome concentration, "
                  "NOT a separate executable strategy. Number of symbols is NOT independent "
                  "evidence because contracts share BTC/systemic market trends.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",type=Path,required=True)
    ap.add_argument("--workers",type=int,default=20)
    a=ap.parse_args()
    raw,meta=fetch_sources(a.out_dir,a.workers)
    results=[]
    accounting=[]
    for y in YEARS:
        for idx,sym in enumerate(SYMS,1):
            events,counts=simulate_symbol(sym,y,raw[sym,y,"1h"],raw[sym,y,"funding"])
            results.extend(events)
            accounting.append(counts)
            print(f"CAUSAL_COHORT_REPLAY {y} {idx}/{len(SYMS)} {sym}: {len(events)}",flush=True)
    ordered=sorted(results,key=lambda e:(e["year"],e["entry_time"],e["symbol"]))
    result={
        "market":"BINANCE_USDT_M_FUTURES_ONLY",
        "status":"EXPLORATORY_CAUSAL_COMPARISON_NOT_VERIFIED",
        "source_archives":meta["archives"],"symbols":SYMS,
        "source_warning":"As-of OHLC + true settled funding, but NOT true historical L2 fills, mark-price liquidation, MMR or shared cash account.",
        "candidate_counts":accounting,"results":{},
    }
    for y in YEARS:
        group=[e for e in ordered if e["year"]==y]
        result["results"][str(y)]={}
        for cost in COSTS:
            result["results"][str(y)][cost]={
                "baseline_realized":summary(group,cost,True),
                "baseline_including_open_mtm":summary(group,cost,False),
                "confirmed_realized":summary([e for e in group if e["confirmed_1h"]],cost,True),
                "unconfirmed_realized":summary([e for e in group if not e["confirmed_1h"]],cost,True),
                "week_bootstrap_confirmed_minus_unconfirmed":boot_week_difference(group,cost),
                "mechanism_and_symbol_diagnostics":pnl_mechanism_diagnostics(group,cost),
            }
    a.out_dir.mkdir(parents=True,exist_ok=True)
    with (a.out_dir/"ALL_ORIGINAL_EVENT_TRADE_LEDGER.csv").open("w",newline="",encoding="utf-8") as fd:
        if ordered:
            writer=csv.DictWriter(fd,fieldnames=ordered[0].keys())
            writer.writeheader()
            writer.writerows(ordered)
    led=(a.out_dir/"ALL_ORIGINAL_EVENT_TRADE_LEDGER.csv").read_bytes() if ordered else b""
    result["ledger_sha256"]=hashlib.sha256(led).hexdigest()
    (a.out_dir/"COMPARATIVE_ECONOMIC_RESULTS.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True,default=list)+"\n",encoding="utf-8")
    print("TCFI_FINAL_RESULTS",json.dumps(result["results"],ensure_ascii=False,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
