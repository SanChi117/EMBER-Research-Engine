#!/usr/bin/env python3
"""A206 source-pinned original signal vs native filled positions audit.
Outputs no economic backtest or orders. Genuine 2025+2026 OHLCV. Fail closed.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,math
from pathlib import Path
import numpy as np
import pandas as pd

SOURCE_SHA="4e3084865a95a694be5178fe60d9130ecd24c002"
STRAT="AggressiveSupportResistanceScalper"
PAIRS=("BTC","ETH","SOL","LINK")
YEARS=(2025,2026)
PREF_LENGTHS=(1000,3000,7000,14000)
def sha256(x):return hashlib.sha256(x).hexdigest()
def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def load_author(path):
    data=path.read_bytes()
    assert blob(data)==SOURCE_SHA,("ORIGINAL_SOURCE_MISMATCH",blob(data))
    spec=importlib.util.spec_from_file_location("a206_exact_original_sr",path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod,STRAT)
def get_data(path,year):
    raw=path.read_bytes()
    records=json.loads(raw)
    assert records and len(records)>40000,("CANDLES_MISSING",year,len(records))
    for i in range(1,len(records)):
        assert records[i][0]-records[i-1][0]==300000,("GAP_OR_DUP",year,i)
    df=pd.DataFrame(records,columns=["date","open","high","low","close","volume"])
    df["date"]=pd.to_datetime(df["date"],unit="ms",utc=True)
    assert df["date"].dt.year.eq(year).all()
    assert df["volume"].ge(0).all()
    return df,sha256(raw)
def signals(strategy,df,sym):
    metadata={"pair":f"{sym}/USDT:USDT"}
    x=strategy.populate_indicators(df.copy(),metadata)
    x=strategy.populate_entry_trend(x,metadata)
    a=np.column_stack((
      np.nan_to_num(x.get("enter_long",pd.Series(np.zeros(len(x)))).to_numpy(dtype=float),nan=0).astype("int8"),
      np.nan_to_num(x.get("enter_short",pd.Series(np.zeros(len(x)))).to_numpy(dtype=float),nan=0).astype("int8")
    ))
    assert np.isin(a,[0,1]).all() and not np.any(a[:,0]&a[:,1])
    return a
def ms(date):
    return int(pd.Timestamp(date).value//1_000_000)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--data2025",required=True)
    p.add_argument("--data2026",required=True)
    p.add_argument("--trades",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    cls=load_author(Path(a.source))
    strategy=cls.__new__(cls)
    native=json.loads(Path(a.trades).read_text())
    assert native["schema"]=="A205_SOURCE_PINNED_NATIVE_16_ZIPS_TWO_INDEPENDENT_YEARS"
    assert native["source_gitblob"]==SOURCE_SHA
    result={}
    for year in YEARS:
        rows={}
        directory=Path(a.data2025 if year==2025 else a.data2026)
        start=pd.Timestamp(f"{year}-05-13T00:00:00Z").value//1_000_000
        finish=pd.Timestamp(f"{year}-10-01T00:00:00Z").value//1_000_000
        for sym in PAIRS:
            path=directory/"futures"/f"{sym}_USDT_USDT-5m-futures.json"
            df,h=get_data(path,year)
            complete=signals(strategy,df,sym)
            for length in PREF_LENGTHS:
                if length>=len(df):continue
                shorter=signals(strategy,df.iloc[:length].copy(),sym)
                assert np.array_equal(shorter,complete[:length]),(
                   "FUTURE_CHANGED_HISTORICAL_SIGNAL",year,sym,length)
            included=(df["date"].astype("int64").to_numpy()//1_000_000>=start)&(
                df["date"].astype("int64").to_numpy()//1_000_000<finish)
            # Only count candidate signal state from evaluation window; first bar onset inherits preceding warmup state.
            present=complete[included]
            times=(df.loc[included,"date"].astype("int64")//1_000_000).to_numpy()
            # Avoid extra false transition on May13 boundary, use predecessor (warmup Apr-May) if one exists.
            idx=np.flatnonzero(included)
            prior=complete[idx[0]-1] if idx[0]>0 else np.array([0,0])
            previous=np.vstack((prior,present[:-1]))
            rises=((present==1)&(previous==0))
            active=np.any(present==1,axis=1)
            fill=native["results"][str(year)][sym]["5"]["intervals"]
            filled_open=[int(round(pair[0]*1000)) for pair in fill]
            assert len(filled_open)==native["results"][str(year)][sym]["5"]["trades"]
            opens=np.array(filled_open,dtype=np.int64)
            matched_previous=0;matched_24h=0
            for t in opens:
                one=np.any((times>=t-600000)&(times<t)&active)
                daily=np.any((times>=t-86_400_000)&(times<t)&active)
                matched_previous+=int(one)
                matched_24h+=int(daily)
            # Count only raw signals while position NOT yet open; a signal during a trade isn't a fresh opportunity.
            in_trade=np.zeros(len(times),dtype=bool)
            for t0,t1 in fill:
                begin=int(round(t0*1000));end=int(round(t1*1000))
                in_trade|=(times>=begin)&(times<end)
            rows[sym]={
                "original_source_git_blob":SOURCE_SHA,
                "input_5m_file_sha256":h,
                "original_raw_signal_bars_long":int(present[:,0].sum()),
                "original_raw_signal_bars_short":int(present[:,1].sum()),
                "original_raw_signal_bars_both_total":int(present.sum()),
                "unique_transition_events_long":int(rises[:,0].sum()),
                "unique_transition_events_short":int(rises[:,1].sum()),
                "unique_transition_events_both_total":int(rises.sum()),
                "signal_bars_during_open_position":int(np.sum(active&in_trade)),
                "signal_bars_when_flat":int(np.sum(active&~in_trade)),
                "signal_events_while_flat":int(np.sum(np.any(rises,axis=1)&~in_trade)),
                "filled_native_trades":len(fill),
                "fills_with_raw_signal_previous_5m_candle":matched_previous,
                "fills_with_any_raw_signal_prior_24h":matched_24h,
                "total_5m_bars_evaluation":int(included.sum()),
                "causal_prefix_lengths_passed":list(PREF_LENGTHS),
                "is_exact_original_source":True,
            }
            print("A206_ORIGINAL_SIGNAL_COUNTS",year,sym,
                  rows[sym]["original_raw_signal_bars_both_total"],
                  rows[sym]["unique_transition_events_both_total"],
                  rows[sym]["filled_native_trades"],flush=True)
        result[str(year)]=rows
    out={
        "schema":"A206_SOURCE_PINNED_SIGNAL_TO_NATIVE_FILLED_AUDIT",
        "original_commit":"7062cdd465f30acb480f6ad8f678f958a8a0e554",
        "git_blob":SOURCE_SHA,
        "native_a205_market_ledger_source":"A205_SR_ORIGINAL_TWO_YEAR_NATIVE_VERIFIED.json",
        "years":list(YEARS),
        "source_signal_causal_prefix_pass":True,
        "results":result,
        "limitations":[
          "Signal candle count is not submitted order count; some signals occur during existing positions.",
          "Each filled limit may occur after an older order; 5m and 24h matches only approximate correspondence.",
          "Cannot calculate actual limit fill rate without order lifecycle from the engine.",
          "A205 source is rejected regardless of this diagnostic, no parameter fitting authorized."
        ],
        "execution_approval":False
    }
    Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print("A206_TWO_REAL_YEARS_FOUR_PAIRS_ORIGINAL_RAW_SIGNALS_PREFIX_AUDITED",flush=True)
if __name__=="__main__":main()
