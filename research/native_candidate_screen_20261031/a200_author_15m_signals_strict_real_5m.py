#!/usr/bin/env python3
"""A200: import ACTUAL original public 15m signal detectors and author's original
run_book + simulator on genuine independently downloaded Binance Futures candles.
Compare deterministic ten seeds of the published 15m random same-bar fills with
INDEPENDENT strict stop-first historical genuine 5m fills, two fee stress models.
No parameter optimization. No live/API execution. No leverage. Research only.
"""
from __future__ import annotations
import argparse,hashlib,importlib,json,math,sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO="genia503/mean-reversion-backtester"
COMMIT="2325ebac97056e6a4f1f98483713513e86239074"
GIT_BLOBS={
 "multicoin_backtest.py":"e33000063b93b825af720791b8282372b6460fdc",
 "tpsl_backtest.py":"fe1ffc3b58d28f844667d1889c30161b38b36e6c"}
SOURCES=("BTC","ETH","SOL","LINK")
CASES=("bigbear","bigbull")
EVAL_START=pd.Timestamp("2026-05-13",tz="UTC")
EVAL_END=pd.Timestamp("2026-10-01",tz="UTC")
FEES={"base":{"entry":0.0005,"tp":0.0002,"stop":0.0005,"slip":0.0},
      "stress":{"entry":0.00125,"tp":0.0005,"stop":0.00125,"slip":0.0005}}
MODEL_WALLET=1000.0
STAKE=100.0

def gitsha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def original_author(repo_path):
    root=Path(repo_path)
    for name,blob in GIT_BLOBS.items():
        p=root/"backtest"/name
        assert p.is_file()
        assert gitsha(p.read_bytes())==blob,("CHANGED_AUTHOR_SOURCE",p,gitsha(p.read_bytes()))
    sys.path.insert(0,str(root.resolve()))
    from backtest import multicoin_backtest as source
    from backtest import tpsl_backtest as mechanics
    assert abs(source.TP_PCT-0.004)<1e-12 and abs(source.SL_PCT-0.0015)<1e-12
    assert mechanics.BAD_HOURS=={6,7,8,9,10}
    assert mechanics.HOLD_LIMIT==96
    assert abs(mechanics.STAKE-100.0)<1e-12
    assert mechanics.TRAIL_ACTIVATE==mechanics.TRAIL_DIST==0.0
    assert abs(mechanics.FEE_ENTRY-0.05)<1e-12 and abs(mechanics.FEE_TP-0.02)<1e-12
    assert abs(mechanics.FEE_SL-0.05)<1e-12
    return source,mechanics

def load_binance_5m(data,symbol):
    p=Path(data)/"futures"/f"{symbol}_USDT_USDT-5m-futures.json"
    raw=json.loads(p.read_text())
    assert len(raw)==44064,(symbol,len(raw))
    arr=np.asarray(raw,dtype=np.float64)
    times=arr[:,0].astype(np.int64)
    assert times[0]==int(pd.Timestamp("2026-05-01",tz="UTC").timestamp()*1000),symbol
    assert np.all(np.diff(times)==300000),("5M_SOURCE_NOT_GAPLESS",symbol)
    assert times[-1]==int((EVAL_END-pd.Timedelta(minutes=5)).timestamp()*1000)
    df=pd.DataFrame({"open":arr[:,1],"high":arr[:,2],"low":arr[:,3],
        "close":arr[:,4],"volume":arr[:,5]},index=pd.to_datetime(times,unit="ms",utc=True))
    assert (df["low"]<=df[["open","close"]].min(axis=1)).all()
    assert (df["high"]>=df[["open","close"]].max(axis=1)).all()
    assert (df["low"]>0).all() and (df["volume"]>=0).all()
    return df,hashlib.sha256(p.read_bytes()).hexdigest()

def to_15m(five):
    agg=five.resample("15min",closed="left",label="left").agg({
       "open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    count=five["close"].resample("15min",closed="left",label="left").count()
    assert len(agg)==14688 and count.eq(3).all()
    assert agg.index[0].hour==0 and agg.index[0].minute==0
    return agg

def funding_for(data,symbol):
    path=Path(data)/"futures"/f"{symbol}_USDT_USDT-1h-funding_rate.json"
    original=json.loads(path.read_text())
    rates={}
    for row in original:
        t=int(row[0]);v=float(row[1])
        if v!=0:
            assert abs(v)<0.03
            rates[t]=v
    assert len(rates)>300,(symbol,len(rates))
    return rates

def source_original_seed(source,df,pattern,coin,seed):
    # Original run_book uses 15m 50/50 rng when high and low hit TP&SL.
    # Preserve original function and default thresholds; author test only.
    np.random.seed(seed)
    rows=source.run_book(df,{"name":pattern,"type":pattern},coin,df_1m=None)
    result=[r for r in rows if EVAL_START<=pd.Timestamp(r["signal_time"])<EVAL_END]
    return {"seed":seed,"n":len(result),
      "net_USDT":round(sum(float(r["net_pnl"]) for r in result),5),
      "winrate":round(sum(int(r["win"]) for r in result)/max(len(result),1),5),
      "first":str(result[0]["signal_time"]) if result else None,
      "note":"ORIGINAL_AUTHOR_15M_RANDOM_SAME_BAR_50_50_REPLAY, seed fixed only for audit"}

def strict_5m(source,five,fifteen,rates,pattern,fee_spec):
    if pattern=="bigbear":
        original_signals=source.detect_bigbear(fifteen)
    else:
        original_signals=source.detect_bigbull(fifteen)
    assert len(original_signals)==len(fifteen)
    # Source rule: entry next 15m bar 6-10 UTC excluded.
    tmap={t:i for i,t in enumerate(five.index)}
    rows=five[["open","high","low","close"]].to_numpy(dtype=float)
    records=[]
    equity=MODEL_WALLET
    peak=MODEL_WALLET;drawdown=0.
    next_free=-1
    raw_total=int(original_signals[(fifteen.index>=EVAL_START)&(fifteen.index<EVAL_END)].sum())
    window=0
    ambiguous=0
    for pos in np.flatnonzero(original_signals.to_numpy(dtype=bool)):
        entry_pos=pos+1
        if entry_pos>=len(fifteen):continue
        time=fifteen.index[entry_pos]
        if not(EVAL_START<=time<EVAL_END):continue
        if time.hour in {6,7,8,9,10}:continue
        window+=1
        if pos<next_free:continue
        t0=tmap[time]
        e0=float(rows[t0,0])
        slip=fee_spec["slip"]
        price_in=e0*(1-slip) # sell SHORT at adverse lower execution
        qty=STAKE/price_in
        tp=price_in*(1-source.TP_PCT)
        sl=price_in*(1+source.SL_PCT)
        entry_fee=qty*price_in*fee_spec["entry"]
        equity-=entry_fee
        entry_equity=equity
        total_funding=0.
        profit=0.;exit_fee=0.
        exitreason=None
        exit_index=None
        entry_stored=None
        max_steps=min(96*3,len(rows)-t0)
        for k in range(max_steps):
            j=t0+k
            open_,high,low,close=rows[j,:]
            t=five.index[j]
            if k>0 and int(t.timestamp()*1000) in rates:
                # SHORT receives positive funding, pays negative funding
                amount=qty*open_*rates[int(t.timestamp()*1000)]
                total_funding+=amount
                equity+=amount
            # Count DD at 5m adverse high before fill, conservative envelope.
            unrealized=qty*(price_in-high)
            mark_eq=equity+unrealized-qty*high*fee_spec["stop"]
            peak=max(peak,mark_eq)
            drawdown=max(drawdown,(peak-mark_eq)/peak)
            stop_hit=high>=sl
            tp_hit=low<=tp
            if stop_hit and tp_hit:ambiguous+=1
            if stop_hit:
                exit_price=max(open_,sl)*(1+slip)
                exit_fee=qty*exit_price*fee_spec["stop"]
                exitreason="STOP"
            elif tp_hit:
                # no better fill than resting TP limit even after gap
                exit_price=tp*(1+slip)
                exit_fee=qty*exit_price*fee_spec["tp"]
                exitreason="TP"
            elif k==max_steps-1:
                exit_price=close*(1+slip)
                exit_fee=qty*exit_price*fee_spec["stop"]
                exitreason="TIMEOUT"
            else:
                continue
            profit=qty*(price_in-exit_price)-exit_fee-entry_fee+total_funding
            equity+=qty*(price_in-exit_price)-exit_fee
            exit_index=j
            break
        assert exitreason is not None
        peak=max(peak,equity)
        drawdown=max(drawdown,(peak-equity)/peak)
        elapsed=(five.index[exit_index]-time).total_seconds()/60
        # replicate original next_free conservative ceil(5m to 15m)
        held=max(1,int(math.ceil(elapsed/15)))
        next_free=entry_pos+held
        records.append({"coin":pattern,"signal_time":str(fifteen.index[pos]),
          "entry_time":str(time),"exit_time":str(five.index[exit_index]),
          "direction":"SHORT","entry":round(price_in,8),
          "exit":round(exit_price,8),"TP":round(tp,8),"SL":round(sl,8),
          "exit_reason":exitreason,"hold_minutes":int(elapsed),
          "gross_pnl":round(qty*(price_in-exit_price),8),
          "fees":round(entry_fee+exit_fee,8),"funding_net":round(total_funding,8),
          "net_pnl":round(profit,8),"wallet":round(equity,8)})
    assert len(records)>0,(pattern,"no completed trades")
    net=sum(r["net_pnl"] for r in records)
    assert abs(MODEL_WALLET+net-equity)<.005
    wins=sorted([r["net_pnl"] for r in records if r["net_pnl"]>0],reverse=True)
    losses=-sum(r["net_pnl"] for r in records if r["net_pnl"]<0)
    n=len(records)
    pf=sum(wins)/losses if losses>0 else (float("inf") if wins else 0.)
    summary={"n":n,"net_USDT":round(net,6),
       "wallet_return_pct":round(net/MODEL_WALLET*100,6),
       "PF":round(pf,5),
       "max_5m_adverse_mark_wallet_DD_pct":round(drawdown*100,5),
       "winning_trades":len(wins),"winrate_pct":round(len(wins)/n*100,4),
       "top3_gross_wins_share":round(sum(wins[:3])/sum(wins),5) if wins else None,
       "total_fees_USDT":round(sum(x["fees"] for x in records),5),
       "total_funding_USDT":round(sum(x["funding_net"] for x in records),5),
       "stops":sum(x["exit_reason"]=="STOP" for x in records),
       "TPs":sum(x["exit_reason"]=="TP" for x in records),
       "TIMEOUTs":sum(x["exit_reason"]=="TIMEOUT" for x in records),
       "original_signal_events":raw_total,
       "eligible_nonbusy_signals_before_exclusions":window,
       "stop_and_target_same_5m_bar_conflicts_conservatively_stop_first":ambiguous,
       "first_trade":records[0]["entry_time"] if records else None,
       "last_trade":records[-1]["entry_time"] if records else None}
    return summary,records

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original-repo",required=True)
    parser.add_argument("--datadir",required=True)
    parser.add_argument("--output",required=True)
    a=parser.parse_args()
    source,original=original_author(a.original_repo)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    machine={"schema":"EMBER_A200_SOURCE_PINNED_GENIA_BIGBEAR_BIGBULL_15M_AUTHOR_BACKTEST_AND_GENUINE_5M_CONSERVATIVE_FILLS",
      "source_repo":REPO,"source_git_commit":COMMIT,
      "original_file_blobs":GIT_BLOBS,
      "signal_methods_directly_author_code":True,"original_author_backtest_method_directly_called":True,
      "original_author_backtest_has_RANDOM_50_50_same_bar_order":True,
      "independent_5m_trading_executor_not_author_native":True,
      "time_window":"[2026-05-13,2026-10-01)",
      "original_author_published":"2026-08-06",
      "all_May_Sep_history_NOT_pristine_OOS":True,
      "one_wallet_per_pattern_pair_no_combination":True,
      "sim_wallet_USDT":MODEL_WALLET,"fixed_stake_USDT":STAKE,
      "price_data":"genuine Binance Vision USD-M 5m all four symbols source-audited A196",
      "patterns":{},"limitations":["Original author 2025-03 to 2026-03 candles not present, so 2025 claimed results not reproduced directly",
        "Author published original multicoin logic has stochastic 50/50 ambiguous 15m TP/SL bars; 10 seeds audited",
        "Independent strict stop-first uses genuine 5m trade-price bars, not 1m exchange order book",
        "TP maker fill on touch is optimistic; limit queue not modeled",
        "Funding settlement only when genuine 1h source record says non-zero; no 5m mark-price STOP trigger",
        "Four 1000USDT separate model wallets, not one combined practical portfolio",
        "No 15m multi-source library live execution equivalence or live fees confirmed",
        "Only SHORT author patterns, not desired both LONG and SHORT"],
      "fees":FEES}
    for symbol in SOURCES:
        five,sha=load_binance_5m(a.datadir,symbol)
        fifteen=to_15m(five)
        rate=funding_for(a.datadir,symbol)
        machine["patterns"][symbol]={"real_5m_file_sha256":sha,
           "native_5m_candles":len(five),"real_15m_grouped_candles":len(fifteen),
           "source_author_seed_random_baseline":{},"independent_strict_5m":{}}
        # Author must get fully identical source 15m history and we document
        # output limited to May13. No author data/network reads needed.
        for pattern in CASES:
            seed_runs=[]
            for seed in range(10):
                seed_runs.append(source_original_seed(source,fifteen,pattern,symbol,seed))
            machine["patterns"][symbol]["source_author_seed_random_baseline"][pattern]=seed_runs
            for model,spec in FEES.items():
                item,trades=strict_5m(source,five,fifteen,rate,pattern,spec)
                machine["patterns"][symbol]["independent_strict_5m"][f"{pattern}_{model}"]=item
                name=f"A200_{pattern}_{symbol}_{model}_CONSERVATIVE_5M_TRADES.json"
                (out/name).write_text(json.dumps(trades,indent=2,ensure_ascii=False)+"\n")
                print("A200_REAL_5M_AUTHOR_SIGNAL_STRICT_STOP_FIRST",pattern,symbol,model,
                     "N",item["n"],"NET_PCT",item["wallet_return_pct"],"PF",item["PF"],
                     "DD",item["max_5m_adverse_mark_wallet_DD_pct"],"AUTHOR_ORIG_SEED0_N",
                     seed_runs[0]["n"],"AUTHOR_ORIG_SEED0_PNL",seed_runs[0]["net_USDT"],flush=True)
    gate={}
    for pattern in CASES:
        status={}
        for symbol in SOURCES:
            q=machine["patterns"][symbol]["independent_strict_5m"]
            status[symbol]=all(
              q[f"{pattern}_{mode}"]["n"]>=25
              and q[f"{pattern}_{mode}"]["net_USDT"]>0
              and q[f"{pattern}_{mode}"]["PF"]>=1.2
              and q[f"{pattern}_{mode}"]["max_5m_adverse_mark_wallet_DD_pct"]<=10
              and q[f"{pattern}_{mode}"]["top3_gross_wins_share"] is not None
              and q[f"{pattern}_{mode}"]["top3_gross_wins_share"]<0.60
              for mode in FEES)
        total=sum(machine["patterns"][symbol]["independent_strict_5m"][f"{pattern}_base"]["n"] for symbol in SOURCES)
        gate[pattern]={"qualifying_pairs":status,"count":sum(status.values()),
          "completed_4_pair_separate_wallet_trades_base":total,
          "trades_per_day_4_wallet_separate":round(total/141,4),
          "predeclared_gate_pass":sum(status.values())>=2 and total>=141}
    machine["predeclared_gate"]=gate
    machine["any_candidate_economic_pass"]=any(x["predeclared_gate_pass"] for x in gate.values())
    (out/"A200_AUTHOR_SOURCE_SIGNALS_16_REAL_5M_COST_RISK_RUNS.json").write_text(json.dumps(machine,indent=2,ensure_ascii=False)+"\n")
    print("A200_SOURCE_ORIGINAL_4PAIRS_2PATTERNS_2COSTS_16_TRUE_5M_RUNS_COMPLETED",
           json.dumps(gate,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
