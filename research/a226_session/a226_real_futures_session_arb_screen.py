"""A226: original pre-registered SESSION opening-range hypotheses, Binance USD-M.

Research hypothesis (not original existing trading strategy), no orders.
Archive SHA from A217; 3 market regimes, base/stress costs, actual funding cash.
Entry next hourly open, non-guaranteed optimistic stop fill, no leverage.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/"research/a221_wide_futures_screen"))
import a221_tsmom_genuine_futures as market  # noqa: E402

PERIODS=(("2024","2024-01-01","2025-01-01"),
         ("2025","2025-01-01","2026-01-01"),
         ("2026_JAN_SEP","2026-01-01","2026-10-01"))
SCENARIOS={
    "S1_ASIA_TO_LONDON":{"range_start":0,"range_end":8,"signal_start":8,"signal_end":15,"exit_hour":16},
    "S2_NEWYORK_OPEN":{"range_start":13,"range_end":15,"signal_start":15,"signal_end":20,"exit_hour":21}
}
COSTS={"base":0.00105,"stress":0.00225}


def prepare_signals(df,config):
    if not (df.index[0].hour==0 and df.index[0].minute==0
            and (df.index.to_series().diff().iloc[1:]==pd.Timedelta(hours=1)).all()):
        raise ValueError("Incomplete genuine hourly UTC history")
    out=[]
    vals=df[["open","high","low","close"]].to_numpy(float)
    idx=df.index
    for off in range(0,len(df)-24+1,24):
        date=idx[off]
        if date.hour!=0:
            raise ValueError("Incorrect UTC day alignment")
        if off+config["exit_hour"] >=len(df):
            break
        rng=vals[off+config["range_start"]:off+config["range_end"]]
        hi=float(rng[:,1].max());lo=float(rng[:,2].min())
        if not (lo>0 and hi>lo):
            continue
        for hour in range(config["signal_start"],config["signal_end"]):
            i=off+hour
            curr=vals[i];prev=vals[i-1]
            if not (lo<=prev[3]<=hi):
                continue
            side=1 if curr[3]>hi else (-1 if curr[3]<lo else 0)
            if side:
                en_i=i+1
                stop=lo if side==1 else hi
                out.append((date.isoformat(),i,en_i,off+config["exit_hour"],side,stop,hi,lo))
                break
    return out


def run_period(df,funding,sigs,start,end,fee):
    lo_date=pd.Timestamp(start,tz="UTC")
    hi_date=pd.Timestamp(end,tz="UTC")
    bars=df[["open","high","low","close"]].to_numpy(float)
    dates=df.index
    frates={t:float(r) for t,r in funding.items()}
    capital=1000.0;hwm=1000.0;dd=0.0
    trades=[];reasons=Counter()
    for date,i,en,terminal,side,stop,rhi,rlo in sigs:
        ts=dates[en]
        if ts<lo_date or ts>=hi_date:
            continue
        entry=float(bars[en,0])
        structural=side*(entry-stop)
        if not np.isfinite(structural) or structural<=0:
            reasons["next_open_beyond_stop"]+=1;continue
        qty=min(capital*0.005/structural,capital/entry)
        initial=capital
        initial_fee=qty*entry*fee
        funding_cash=0.0
        exit_price=None
        exit_i=None
        outcome=None
        # From the entry hourly OPEN to session end hourly OPEN.
        for j in range(en,terminal+1):
            o,h,l,c=map(float,bars[j])
            stamp=dates[j]
            if j>en and stamp in frates:
                funding_cash-=side*qty*o*frates[stamp]
            current_mark=initial-initial_fee+funding_cash+side*qty*(o-entry)
            hwm=max(hwm,current_mark)
            if j==terminal:
                exit_price=o;exit_i=j;outcome="session_end_open"
                break
            adverse=l if side==1 else h
            wick_equity=initial-initial_fee+funding_cash+side*qty*(adverse-entry)
            dd=min(dd,wick_equity/hwm-1.0)
            # adverse open gap executes at open, not imaginary perfect stop
            if side*(o-stop)<=0:
                exit_price=o;exit_i=j;outcome="stop_gap"
                break
            if side*(adverse-stop)<=0:
                exit_price=stop;exit_i=j;outcome="structural_stop_model"
                break
        if exit_i is None:
            raise ValueError("Position failed terminal exit")
        finalfee=qty*exit_price*fee
        net=qty*side*(exit_price-entry)+funding_cash-initial_fee-finalfee
        capital=initial+net
        hwm=max(hwm,capital)
        dd=min(dd,capital/hwm-1)
        reasons[outcome]+=1
        trades.append({
            "date":date,"entry_utc":ts.isoformat(),
            "exit_utc":dates[exit_i].isoformat(),
            "side":"LONG" if side==1 else "SHORT",
            "range_high":round(rhi,7),"range_low":round(rlo,7),
            "entry_px":round(entry,7),"stop_px":round(stop,7),"exit_px":round(exit_price,7),
            "qty":round(qty,9),"fees_usdt":round(initial_fee+finalfee,7),
            "funding_usdt":round(funding_cash,7),
            "net_usdt":round(net,7),"capital_usdt":round(capital,7),
            "outcome":outcome
        })
        if capital<=0:
            raise ValueError("Catastrophic ruin without permitted leverage")
    return {
        "net_return_pct":round((capital/1000-1)*100,5),
        "n_trades":len(trades),
        "win_rate_pct":round(100*sum(x["net_usdt"]>0 for x in trades)/len(trades),3) if trades else None,
        "max_drawdown_hourly_wick_pct_approx":round(dd*100,5),
        "worst_trade_usdt":round(min((x["net_usdt"] for x in trades),default=0),5),
        "fees_usdt":round(sum(x["fees_usdt"] for x in trades),5),
        "funding_usdt":round(sum(x["funding_usdt"] for x in trades),5),
        "exit_reason":dict(reasons),
        "no_real_fills_or_mark_liquidation":True
    },trades


def main():
    mandate=json.loads((ROOT/"config/research_mandate.lock.json").read_text())
    assert mandate["state"]=="LOCKED_USER_ONLY" and mandate["scope"]=="BINANCE_USDT_M_FUTURES"
    manifest=json.loads((ROOT/"research/a217_trendrider_original/evidence/source_manifest.json").read_text())
    candles,funding,zipreceipts=market.load_all(manifest)
    assert len(zipreceipts)==204
    results={};ledgers={}
    for rule_name,cfg in SCENARIOS.items():
        raw={coin:prepare_signals(candles[coin],cfg) for coin in market.COINS}
        results[rule_name]={};ledgers[rule_name]={}
        for y,start,end in PERIODS:
            results[rule_name][y]={};ledgers[rule_name][y]={}
            for name,fee in COSTS.items():
                metrics={};ledgers[rule_name][y][name]={}
                for sym in market.COINS:
                    summ, trades=run_period(candles[sym],funding[sym],raw[sym],start,end,fee)
                    metrics[sym]=summ
                    ledgers[rule_name][y][name][sym]=trades
                results[rule_name][y][name]={
                    "net_return_combined_three_equal_sleeves_pct":
                        round(sum(z["net_return_pct"] for z in metrics.values())/3,5),
                    "n_trades":sum(z["n_trades"] for z in metrics.values()),
                    "worst_coin_mark_wick_dd_pct":
                        min(z["max_drawdown_hourly_wick_pct_approx"] for z in metrics.values()),
                    "by_symbol":metrics
                }
    gates={}
    for r in SCENARIOS:
        winners=[y for y,_,_ in PERIODS if
            results[r][y]["stress"]["net_return_combined_three_equal_sleeves_pct"]>0
            and results[r][y]["stress"]["n_trades"]>=40
            and results[r][y]["stress"]["worst_coin_mark_wick_dd_pct"]>=-20]
        gates[r]={"fast_economic_pass":len(winners)>=2,"qualifying_years":winners,
                  "ready_original_strategy":False,"verified_trading_edge":False}
    outdir=HERE/"evidence";outdir.mkdir(exist_ok=True)
    receipt={
        "scope":"research hypothesis screening only",
        "original_historical_strategy_tested":False,
        "dataset":"genuine Binance USDT-M BTC ETH SOL 1h and actual fundingRate",
        "source_archives_sha_verified":len(zipreceipts),
        "preregistration":"research/a226_session/PREREG_SESSION_RANGE_PRICE_ACTION.md",
        "rules":SCENARIOS,"years":results,"gates":gates,
        "source_receipts":sorted(zipreceipts,key=lambda x:x["key"]),
        "no_real_orders":True,"no_verified_mark_margin_liquidation":True,
        "note":"OHLC stop execution uses optimistic stop price; no maker queue/official mark. Not live or paper."
    }
    (outdir/"A226_NATIVE_SESSION_RANGE_STRESS.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    (outdir/"A226_ALL_MODEL_TRADES.json").write_text(json.dumps(ledgers,ensure_ascii=False)+"\n")
    print(json.dumps({"sha_receipts":len(zipreceipts),"gates":gates,
        "summary":{k:{y:{sc:[
          results[k][y][sc]["net_return_combined_three_equal_sleeves_pct"],
          results[k][y][sc]["n_trades"],
          results[k][y][sc]["worst_coin_mark_wick_dd_pct"]] for sc in COSTS}
          for y,_,_ in PERIODS} for k in SCENARIOS}},ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
