#!/usr/bin/env python3
"""A207: independent fixed-parameter replay of exact author's 5m taker flow signals.
No trade APIs, no fitting, no inherited author's OOS-selected stop/take values.
All candles and funding downloaded from genuine Binance Vision ZIP CSV, SHA256 logged.
"""
from __future__ import annotations
import argparse,bisect,csv,hashlib,importlib.util,io,json,math,statistics,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone,timedelta
from pathlib import Path
import numpy as np
import pandas as pd

YEARS=(2024,2025,2026)
COINS=("BTC","ETH","SOL","LINK")
START_MONTH=5
END_MONTH=9
BASE="https://data.binance.vision/data/futures/um/monthly"
SOURCE_BLOB="b8a2840618c4fb02a2d90120deed5771b34bdbd6"
SOURCE_COMMIT="5ed0d6e39d8a3e951bea40c66e2638c213012e1b"
PARAMS={"ma_period":15,"confirm_bars":3,"threshold_high":0.62,"atr_period":14}
HOLD_BARS=16
STOP_PRICE_FRACTION=.01
TAKE_PRICE_FRACTION=.02
NOTIONAL=100.0
WALLET=1000.0
FEE_SCENARIOS={"base":{"fee_each_side":.0005,"slippage_each_side":.0001},
               "stress":{"fee_each_side":.00125,"slippage_each_side":.0003}}
BAR_MS=300000

def timestamp(v):
    t=int(v)
    if t>100_000_000_000_000:
        assert t%1000==0,("NON_WHOLE_MICRO",t)
        t//=1000
    assert 1_600_000_000_000<t<1_900_000_000_000,t
    return t

def get(job):
    yr,coin,kind,mo=job
    sym=coin+"USDT";stamp=f"{yr}-{mo:02d}"
    if kind=="kline":
        url=f"{BASE}/klines/{sym}/5m/{sym}-5m-{stamp}.zip"
    else:
        url=f"{BASE}/fundingRate/{sym}/{sym}-fundingRate-{stamp}.zip"
    req=urllib.request.Request(url,headers={"User-Agent":"EMBER-A207-CAUSAL-RESEARCH-PAPER-ONLY"})
    with urllib.request.urlopen(req,timeout=100) as f:
        raw=f.read(40_000_000)
        assert f.status==200 and 50<len(raw)<40_000_000,(url,len(raw))
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[x for x in z.namelist() if x.endswith(".csv") and not x.startswith("__")]
        assert len(names)==1,(url,names)
        b=z.read(names[0])
    rows=list(csv.reader(io.StringIO(b.decode("utf-8-sig"))))
    assert len(rows)>10,(url,"FEW_ROWS")
    receipt={"source_url":url,"zip_sha256":hashlib.sha256(raw).hexdigest(),
             "csv_sha256":hashlib.sha256(b).hexdigest(),"source_rows":len(rows)}
    return job,rows,receipt

def read_funding(rows,coin,year):
    header=[str(x).lower().strip().replace("_","") for x in rows[0]]
    assert any("funding" in x for x in header),("MISSING_FUNDING_HEADER",coin,header)
    def col(*options):
        for name in options:
            if name in header:return header.index(name)
        raise ValueError(("HEADER_COLUMN_MISSING",options,header))
    ti=col("calctime","fundingtime","timestamp","time")
    ri=col("lastfundingrate","fundingrate")
    out=[]
    for x in rows[1:]:
        if not x:continue
        t=timestamp(x[ti])
        rate=float(x[ri])
        assert -0.03<rate<0.03,(coin,year,t,rate)
        out.append((t,rate))
    return out

def read_kline(rows,coin,year):
    out=[]
    for x in rows:
        if not x or x[0].lower().startswith(("open","timestamp","time")):continue
        assert len(x)>=11,(coin,year,len(x))
        t=timestamp(x[0])
        o,h,l,c,v=map(float,x[1:6])
        taker=float(x[9])
        assert all(math.isfinite(z) for z in (o,h,l,c,v,taker))
        assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0,(coin,year,t,o,h,l,c,v)
        assert -1e-6<=taker<=v+max(1e-6,v*1e-7),(coin,year,t,taker,v)
        out.append((t,o,h,l,c,v,max(0.,min(taker,v))))
    return out

def collect_data(root):
    jobs=[(y,c,kind,m) for y in YEARS for c in COINS
          for kind in ("kline","funding") for m in range(START_MONTH,END_MONTH+1)]
    d={};receipts={}
    with ThreadPoolExecutor(max_workers=12) as pool:
        for future in as_completed([pool.submit(get,j) for j in jobs]):
            j,rows,receipt=future.result()
            d[j]=rows;receipts["-".join(map(str,j))]=receipt
    out={};summary={}
    for year in YEARS:
        for coin in COINS:
            five=[];fund=[]
            for month in range(START_MONTH,END_MONTH+1):
                five.extend(read_kline(d[(year,coin,"kline",month)],coin,year))
                fund.extend(read_funding(d[(year,coin,"funding",month)],coin,year))
            lo=int(datetime(year,5,1,tzinfo=timezone.utc).timestamp()*1000)
            hi=int(datetime(year,10,1,tzinfo=timezone.utc).timestamp()*1000)
            expected=(hi-lo)//BAR_MS
            assert len(five)==expected,(year,coin,"CANDLE_TOTAL",len(five),expected)
            for i,rec in enumerate(five):
                assert rec[0]==lo+i*BAR_MS,(year,coin,"GAP_DUP_CANDLE",i,rec[0],lo+i*BAR_MS)
            fund=sorted(set(fund))
            assert len(fund)>=200,(year,coin,"NO_GENUINE_FUNDING",len(fund))
            assert all(lo<=t<hi for t,_ in fund)
            assert len({t for t,_ in fund})==len(fund),(year,coin,"FUNDING_TIMESTAMP_DUP")
            # Genuine buy ratio from Binance taker base volume, NOT reconstructed from close direction.
            idx=pd.to_datetime([r[0] for r in five],unit="ms",utc=True)
            df=pd.DataFrame([r[1:] for r in five],
                index=idx,columns=("open","high","low","close","volume","taker_buy_volume"))
            df["buy_ratio"]=df["taker_buy_volume"]/df["volume"].replace(0,np.nan)
            out[(year,coin)]=(df,fund)
            summary[f"{year}-{coin}"]={
                "source_rows":len(df),"first_open_utc":idx[0].isoformat(),
                "last_open_utc":idx[-1].isoformat(),
                "funding_settlements":len(fund),
                "taker_volume_from_genuine_binance_csv_column_9":True,
                "input_candles_contiguous_no_gap":True,
                "last_open_price":round(float(df["open"].iloc[-1]),8)}
            print("A207_GENUINE_SOURCE_OK",year,coin,len(df),len(fund),flush=True)
    return out,receipts,summary

def get_author(path):
    raw=path.read_bytes()
    blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    assert blob==SOURCE_BLOB,("ORIGINAL_SIGNALS_SOURCE_BYTES_CHANGED",blob)
    spec=importlib.util.spec_from_file_location("a207_author_frozen_taker",path)
    assert spec is not None and spec.loader is not None
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.generate_signals,blob

def causal_signals(fn,df,year,coin):
    result=fn(df,PARAMS)
    sig=np.asarray(result,dtype=np.int8)
    assert len(sig)==len(df) and np.isin(sig,[-1,0,1]).all()
    # Prefix test for leaked future rows: dynamic history must not rewrite past signals.
    for limit in (300,1600,4200,7500):
        assert np.array_equal(sig[:limit],np.asarray(fn(df.iloc[:limit].copy(),PARAMS),dtype=np.int8)),(
            "A207_NONCAUSAL_HISTORIC_SIGNAL",year,coin,limit)
    return sig

def position_replay(df,signs,funding,year,coin,label,cost):
    opens=df["open"].to_numpy(dtype=float); highs=df["high"].to_numpy(dtype=float)
    lows=df["low"].to_numpy(dtype=float)
    start=int(datetime(year,5,13,tzinfo=timezone.utc).timestamp()*1000)
    end=int(datetime(year,10,1,tzinfo=timezone.utc).timestamp()*1000)
    times=(df.index.astype("int64")//1_000_000).to_numpy(dtype=np.int64)
    eventimes=[t for t,r in funding]
    rates=[r for t,r in funding]
    events_raw=sum(int(signs[i]!=0 and start<=times[i]<end) for i in range(len(signs)))
    event_onset=sum(int(signs[i]!=0 and signs[i-1]!=signs[i] and start<=times[i]<end) for i in range(1,len(signs)))
    cursor=max(0,int(np.searchsorted(times,start)))
    last_exit_idx=-1; trade_rows=[];wallet=WALLET;peak=WALLET;dd=0.;fund_cash=0
    signals_when_flat=0; available_enter_events=0
    while cursor<len(signs)-1 and times[cursor]<end:
        idx=cursor
        if signs[idx]==0:
            cursor+=1;continue
        signals_when_flat+=1
        if signs[idx]!=signs[idx-1]:available_enter_events+=1
        enter_i=idx+1
        if times[enter_i]>=end:break
        side=int(signs[idx])
        slip=cost["slippage_each_side"];fee=cost["fee_each_side"]
        entry=float(opens[enter_i])*(1+side*slip)
        stop=entry*(1-side*STOP_PRICE_FRACTION)
        target=entry*(1+side*TAKE_PRICE_FRACTION)
        exit_i=None;raw_exit=None;why=None;exittime=None
        expiration=min(enter_i+HOLD_BARS,len(signs)-1)
        for j in range(enter_i,expiration):
            if times[j]>=end:break
            # If bar gaps through stop, stop execution cannot fill at better stop price.
            if (side==1 and opens[j]<=stop) or (side==-1 and opens[j]>=stop):
                raw_exit=float(opens[j]);why="stop_gap"
            elif (side==1 and lows[j]<=stop) or (side==-1 and highs[j]>=stop):
                raw_exit=stop;why="stop"
            elif (side==1 and highs[j]>=target) or (side==-1 and lows[j]<=target):
                raw_exit=target;why="take"
            if why:
                exit_i=j;exittime=int(times[j]+BAR_MS)
                break
        if exit_i is None:
            exit_i=expiration
            if times[exit_i]>=end:break
            raw_exit=float(opens[exit_i]);why="timeout"
            exittime=int(times[exit_i])
        exit_price=raw_exit*(1-side*slip)
        size=NOTIONAL/entry
        fee_in=NOTIONAL*fee
        fee_out=size*exit_price*fee
        raw_pnl=size*side*(exit_price-entry)
        # Funding cash on actual settled timestamps between entry and exit.
        ib=bisect.bisect_right(eventimes,int(times[enter_i]))
        ie=bisect.bisect_right(eventimes,exittime)
        funding_cash=-side*sum(rates[ib:ie])*NOTIONAL
        pnl=raw_pnl-fee_in-fee_out+funding_cash
        before=wallet;wallet+=pnl;peak=max(peak,wallet);dd=max(dd,(peak-wallet)/peak)
        trade_rows.append({
            "year":year,"coin":coin,"fee_scenario":label,
            "signal_open_ms":int(times[idx]),"entry_open_ms":int(times[enter_i]),
            "exit_ms":exittime,"side":side,"entry":entry,
            "exit":exit_price,"entry_idx":int(enter_i),"exit_idx":int(exit_i),
            "nominal_USDT":NOTIONAL,"pnl_USDT":pnl,
            "commission_USDT":fee_in+fee_out,
            "funding_USDT":funding_cash,"exit_reason":why,
            "hold_min":round((exittime-int(times[enter_i]))/60000,3),
            "wallet_before":before,"wallet_after":wallet})
        cursor=exit_i+1
    wins=sorted([r["pnl_USDT"] for r in trade_rows if r["pnl_USDT"]>0],reverse=True)
    losses=[-r["pnl_USDT"] for r in trade_rows if r["pnl_USDT"]<0]
    totalgross=sum(wins);total_loss=sum(losses)
    pf=totalgross/total_loss if total_loss>0 else None
    duration=[r["hold_min"] for r in trade_rows]
    gaps=[(trade_rows[i]["entry_open_ms"]-trade_rows[i-1]["exit_ms"])/60000
          for i in range(1,len(trade_rows))]
    assert all(x>=0 for x in gaps),(coin,year,"OVERLAPPING_SINGLE_SLOT")
    exposure=sum(x["hold_min"] for x in trade_rows)/((end-start)/60000)
    return {
        "trades":len(trade_rows),"long_n":sum(r["side"]==1 for r in trade_rows),
        "short_n":sum(r["side"]==-1 for r in trade_rows),
        "raw_signal_bars":events_raw,"transition_signal_events":event_onset,
        "signal_bars_encountered_when_flat":signals_when_flat,
        "new_transition_events_while_flat":available_enter_events,
        "raw_persistent_signal_ratio":round(1-event_onset/max(1,events_raw),6),
        "net_USDT":round(wallet-WALLET,6),"wallet_return_pct":round((wallet/WALLET-1)*100,6),
        "profit_factor":round(pf,6) if pf is not None else None,
        "wallet_realized_dd_pct":round(dd*100,6),
        "win_rate_pct":round(len(wins)/max(1,len(trade_rows))*100,5),
        "top3_gross_win_share":round(sum(wins[:3])/totalgross,6) if totalgross else None,
        "median_hold_min":round(statistics.median(duration),3) if duration else None,
        "p90_hold_min":round(float(np.percentile(duration,90)),3) if duration else None,
        "max_hold_min":max(duration) if duration else None,
        "position_exposure_pct":round(exposure*100,4),
        "reenter_within_5m_pct":round(sum(g<=5 for g in gaps)/len(gaps)*100,4) if gaps else None,
        "exit_reasons":dict(sorted((k,sum(x["exit_reason"]==k for x in trade_rows))
                               for k in ("stop","stop_gap","take","timeout"))),
        "commission_total_USDT":round(sum(r["commission_USDT"] for r in trade_rows),6),
        "funding_total_USDT":round(sum(r["funding_USDT"] for r in trade_rows),6),
        "trade_rows":trade_rows,
    }

def pass_coin(r):
    return (r["trades"]>=35 and r["net_USDT"]>0 and r["profit_factor"] is not None
        and r["profit_factor"]>=1.2 and r["wallet_realized_dd_pct"]<15
        and r["top3_gross_win_share"] is not None and r["top3_gross_win_share"]<.60)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--author",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args();folder=Path(a.out);folder.mkdir(parents=True,exist_ok=True)
    fn,sha=get_author(Path(a.author))
    source,receipts,manifest=collect_data(folder)
    outcomes={};trade_receipts={}
    for year in YEARS:
        outcomes[str(year)]={}
        for coin in COINS:
            df,fund=source[(year,coin)]
            sig=causal_signals(fn,df,year,coin)
            outcomes[str(year)][coin]={}
            for label,cost in FEE_SCENARIOS.items():
                result=position_replay(df,sig,fund,year,coin,label,cost)
                trades=result.pop("trade_rows")
                # Per-trade independent ledger; hash the on-disk payload and re-open.
                f=folder/f"A207_{year}_{coin}_{label}_GENUINE_TRADE_LOG.json"
                f.write_text(json.dumps(trades,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
                assert json.loads(f.read_text())==trades
                assert abs(sum(r["pnl_USDT"] for r in trades)-result["net_USDT"])<.000001
                trade_receipts[f.name]={"sha256":hashlib.sha256(f.read_bytes()).hexdigest(),
                     "trade_rows":len(trades)}
                outcomes[str(year)][coin][label]=result
                print("A207_REAL_REPLAY",year,coin,label,
                      result["trades"],result["wallet_return_pct"],
                      result["profit_factor"],flush=True)
    pair_pass={coin:all(pass_coin(outcomes[str(year)][coin][label])
                        for year in YEARS for label in FEE_SCENARIOS)
               for coin in COINS}
    counts={str(year):{label:sum(outcomes[str(year)][c][label]["trades"] for c in COINS)
                          for label in FEE_SCENARIOS} for year in YEARS}
    economics=sum(pair_pass.values())>=2 and all(v>=141 for x in counts.values() for v in x.values())
    tempo={str(year):{label:{
      "closed_per_day":round(counts[str(year)][label]/141,5),
      "all_four_occupied_lower_bound_pct":None,
      "median_position_exposure_fraction_sum":round(sum(outcomes[str(year)][coin][label]["position_exposure_pct"] for coin in COINS)/100,5),
      "passes_trade_count":counts[str(year)][label]>=423,
      "passes_no_instant_reentry":all(
        outcomes[str(year)][coin][label]["reenter_within_5m_pct"] is None or
        outcomes[str(year)][coin][label]["reenter_within_5m_pct"]<30 for coin in COINS),
      "passes_p90_hold":all(
        outcomes[str(year)][coin][label]["p90_hold_min"] is None or
        outcomes[str(year)][coin][label]["p90_hold_min"]<=1440 for coin in COINS),
      "passes_no_persistent_4h_signal":all(
        outcomes[str(year)][coin][label]["raw_persistent_signal_ratio"]<.7
        for coin in COINS)
    } for label in FEE_SCENARIOS}for year in YEARS}
    tempo_pass=all(t["passes_trade_count"] and t["passes_no_instant_reentry"]
                   and t["passes_p90_hold"] and t["passes_no_persistent_4h_signal"]
                   for yy in tempo.values() for t in yy.values())
    output={
      "schema":"A207_ORIGINAL_TAKER_SIGNAL_FIXED_PARAMETER_INDEPENDENT_REPLAY",
      "original_signal_repo":"Gotodataru/binance-futures-backtest",
      "source_commit":SOURCE_COMMIT,"source_blob":sha,
      "source_file":"strategy_2_taker_momentum/signals.py",
      "NOT_NATIVE_FREQTRADE":True,
      "source_trade_engine_used":False,
      "fix_vs_author":"Exact original signal function imported; fixed SL/TP source grid values used; new audited execution replaces OOS-selected source backtest",
      "params":{"source":PARAMS,"hold_bars":HOLD_BARS,"stop_price":STOP_PRICE_FRACTION,
                "target_price":TAKE_PRICE_FRACTION,"notional_USDT":NOTIONAL,"wallet_USDT":WALLET,
                "fee_scenarios":FEE_SCENARIOS},
      "years":list(YEARS),"period_each_year":"[May13,Oct01) UTC",
      "source_zip_and_csv_sha256":receipts,"source_data_integrity":manifest,
      "individual_trade_ledger_sha256":trade_receipts,
      "outcomes":outcomes,"economic_pair_pass_all_three_years_both_fees":pair_pass,
      "total_trades_per_year_fee":counts,"economic_research_gate":economics,
      "tempo":tempo,"tempo_research_gate":tempo_pass,
      "execution_approval":False,
      "caveats":[
        "Signal values are from original source; fixed parameters chosen before backtest, not selected by searching OOS",
        "First 2024 history is fresh to EMBER as of prereg; May-Sep2025 and 2026 previously used by EMBER",
        "5m OHLC SL-first cannot guarantee actual tick sequence; no real order book, maker queue or real spreads",
        "Funding applied to genuine settled event timestamps during position; same-stop-bar funding timestamp uncertain",
        "Wallet DD is realized trades only, not complete mark-to-market peak margin risk",
        "No high leverage; raw 5m signal may persist over several candles; no after-test rewrites permitted",
        "Even economic pass cannot approve trading before 1m execution and forward PAPER"]
    }
    receipt_file=folder/"A207_FROZEN_TAKER_2024_2025_2026_VERIFIED.json"
    receipt_file.write_text(json.dumps(output,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print("A207_GENUINE_BINANCE_THREE_YEARS_ORIGINAL_SIGNALS_FIXED_RISK_VERIFIED",
          json.dumps({"economic":economics,"tempo":tempo_pass,"N":counts,
                      "pairs":pair_pass},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
