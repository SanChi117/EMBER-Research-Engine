"""A225: TEST 3 frozen market-behavior hypotheses BEFORE finding strategy repositories.

NOT an existing strategy, NOT a proof of deployable edge. Uses genuine Binance
USDT-M 1h OHLCV/funding, checked against A217 pinned SHA manifest.
Hard pre-registration: research/a225_edge_first/PREREG_EVIDENCE_FIRST_4H_LEVELS.md
No orders. No data-derived optimisation. Pessimistic stop-first OHLC fills,
actual funding snapshots, modeled cost base/stress. Official mark/liquidation
not reproduced; even a pass is only research evidence.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "research/a221_wide_futures_screen"))
import a221_tsmom_genuine_futures as genuine  # noqa: E402

HYPOTHESES = ("E1_REJECTION", "E2_BREAK_RETEST", "E3_COMPRESSION")
PERIODS = (("2024","2024-01-01","2025-01-01"),
           ("2025","2025-01-01","2026-01-01"),
           ("2026JANSEP","2026-01-01","2026-10-01"))
COSTS = {"base":0.00105,"stress":0.00225} # per side, fraction of notional
START_EQUITY = 1000.0
ONE_TRADE_RISK = 0.005
MAX_EXPOSURE = 1.0


def base_4h(df: pd.DataFrame) -> pd.DataFrame:
    b = df.resample("4h", closed="left", label="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    if not (df.index[0].hour==0 and (df.index.to_series().diff().iloc[1:] == pd.Timedelta(hours=1)).all()):
        raise ValueError("Noncontinuous UTC 1h bars")
    if (df["open"].resample("4h").count()!=4).any() or b.isna().any().any():
        raise ValueError("Genuine 4h aggregation incomplete")
    prev = b["close"].shift(1)
    tr = pd.concat([(b.high-b.low), (b.high-prev).abs(), (b.low-prev).abs()],axis=1).max(axis=1)
    b["atr"] = tr.rolling(14,min_periods=14).mean()
    b["s20"] = b.low.rolling(20,min_periods=20).min()
    b["r20"] = b.high.rolling(20,min_periods=20).max()
    b["s3"] = b.low.rolling(3,min_periods=3).min()
    b["r3"] = b.high.rolling(3,min_periods=3).max()
    b["small3"] = (b.high-b.low).rolling(3,min_periods=3).mean()
    b["median20"] = (b.high-b.low).rolling(20,min_periods=20).median()
    return b


def events_1h(df: pd.DataFrame) -> dict:
    b = base_4h(df)
    n=len(df)
    o=df.open.to_numpy(float); h=df.high.to_numpy(float)
    l=df.low.to_numpy(float); c=df.close.to_numpy(float)
    out={k:[] for k in HYPOTHESES}
    pending=None
    last_break=(None,None)
    for i in range(160,n-25):
        # +1 hour is when full hourly candle and (possibly) full 4h close become known.
        k=(i+1)//4-1
        if k < 20 or k >= len(b):
            continue
        bk=b.iloc[k]
        atr=float(bk.atr)
        if not np.isfinite(atr) or atr<=0:
            continue
        sup,res=float(bk.s20),float(bk.r20)
        if not (0<sup<res):
            continue
        cl=float(c[i]); prev=float(c[i-1])
        # Hypothesis E1: structural reaction; 4h stop and opposite 4h target predate signal.
        direct=0
        if l[i]<=sup+0.1*atr and cl>=sup+0.3*atr and cl>o[i]:
            direct=1
        if h[i]>=res-0.1*atr and cl<=res-0.3*atr and cl<o[i]:
            direct=-1 if direct==0 else 0
        if direct:
            stop=(sup-0.35*atr) if direct==1 else (res+0.35*atr)
            tp=res if direct==1 else sup
            out["E1_REJECTION"].append((i,direct,float(stop),float(tp)))

        # Hypothesis E2: source signal breakout, then a *different, later* 1h retest.
        if pending is not None:
            first_i, side, level, fixedatr=pending
            if i-first_i>6:
                pending=None
            elif i>first_i:
                if side==1 and l[i]<=level+0.20*fixedatr and cl>=level+0.10*fixedatr:
                    stop=float(bk.s3)-0.20*atr
                    out["E2_BREAK_RETEST"].append((i,1,stop,None))
                    pending=None
                elif side==-1 and h[i]>=level-0.20*fixedatr and cl<=level-0.10*fixedatr:
                    stop=float(bk.r3)+0.20*atr
                    out["E2_BREAK_RETEST"].append((i,-1,stop,None))
                    pending=None
        if pending is None:
            if prev<=res+0.20*atr and cl>res+0.20*atr:
                pending=(i,1,res,atr)
            elif prev>=sup-0.20*atr and cl<sup-0.20*atr:
                pending=(i,-1,sup,atr)

        # Hypothesis E3: price breakout of prior completed 4h tight channel;
        # do NOT extrapolate volatility clustering into directional edge.
        if (bk.r3-bk.s3 < 2.25*atr and bk.small3 < 0.75*bk.median20):
            if prev<=bk.r3+0.10*atr and cl>bk.r3+0.10*atr:
                out["E3_COMPRESSION"].append((i,1,float(bk.s3)-0.20*atr,None))
            elif prev>=bk.s3-0.10*atr and cl<bk.s3-0.10*atr:
                out["E3_COMPRESSION"].append((i,-1,float(bk.r3)+0.20*atr,None))
    return out


def simulate(df, fund, signals, start, end, cost):
    idx=df.index
    first=int(idx.searchsorted(pd.Timestamp(start,tz="UTC")))
    last=int(idx.searchsorted(pd.Timestamp(end,tz="UTC")))
    o=df.open.to_numpy(float); hi=df.high.to_numpy(float)
    lo=df.low.to_numpy(float); closes=df.close.to_numpy(float)
    rates={t:float(v) for t,v in fund.items()}
    equity=START_EQUITY
    high_water=START_EQUITY
    max_dd=0.0
    worst_wick=0.0
    last_exit=first-1
    records=[]
    counts=Counter()
    for signal_i,side,stop,target in signals:
        if signal_i<first-1 or signal_i>=last-25:
            continue
        ent_i=signal_i+1
        if ent_i<=last_exit:
            counts["overlapping_signals"]+=1
            continue
        entry=o[ent_i]
        dist=side*(entry-stop)
        if dist<=0 or not np.isfinite(dist) or not (entry>0):
            counts["entry_beyond_structural_stop"]+=1
            continue
        if target is not None and side*(target-entry)<=0:
            counts["entry_beyond_structural_target"]+=1
            continue
        qty=min(equity*ONE_TRADE_RISK/dist,equity*MAX_EXPOSURE/entry)
        if qty<=0:
            continue
        beginning=equity
        infee=qty*entry*cost
        cash=0.0
        peak_local=equity
        adverse_pct=0
        exit_price=None; exit_i=None; reason=None
        # Earliest entry is next open. Stop can hit on the *entry* candle.
        for j in range(ent_i,min(ent_i+25,last)):
            t=idx[j]
            if j>ent_i and t in rates:
                cash+= -side*qty*o[j]*rates[t]
            # For reported worst intra-hour equity stress, use adverse wick.
            worst_price=lo[j] if side==1 else hi[j]
            wick_eq=beginning-infee+cash+side*qty*(worst_price-entry)
            worst_wick=min(worst_wick,(wick_eq-START_EQUITY)/START_EQUITY)
            adverse_pct=min(adverse_pct,side*(worst_price-entry)/entry)
            if j==ent_i+24 or j==last-1:
                exit_price=o[j];exit_i=j;reason="time_close"
                break
            # Adverse open gap worse than stop, no supernatural stop fill.
            if side*(o[j]-stop)<=0:
                exit_price=o[j];exit_i=j;reason="stop_gap_open"
                break
            if side*(worst_price-stop)<=0:
                exit_price=stop;exit_i=j;reason="structural_stop"
                break
            if target is not None:
                best_price=hi[j] if side==1 else lo[j]
                # SL evaluated first whenever OHLC simultaneously reaches both.
                if side*(best_price-target)>=0:
                    exit_price=target;exit_i=j;reason="opposite_4h_zone"
                    break
            opening_mark=beginning-infee+cash+side*qty*(o[j]-entry)
            peak_local=max(peak_local,opening_mark)
            high_water=max(high_water,opening_mark)
            max_dd=min(max_dd,wick_eq/high_water-1)
        if exit_i is None:
            raise ValueError("Unclosed trade")
        exitfee=qty*exit_price*cost
        pnl=side*qty*(exit_price-entry)+cash-infee-exitfee
        equity=beginning+pnl
        high_water=max(high_water,equity,peak_local)
        max_dd=min(max_dd,equity/high_water-1)
        last_exit=exit_i
        counts[reason]+=1
        records.append({
            "signal":idx[signal_i].isoformat(),"entry":idx[ent_i].isoformat(),
            "exit":idx[exit_i].isoformat(),"side":side,"entry_price":round(float(entry),7),
            "stop_price":round(float(stop),7),"target_price":None if target is None else round(float(target),7),
            "qty":round(float(qty),9),"net_pnl":round(float(pnl),6),
            "fee":round(float(infee+exitfee),6),"funding":round(float(cash),6),
            "equity_after":round(float(equity),6),"reason":reason,
            "original_stop_dist_pct":round(100*float(dist/entry),4),
            "max_adverse_intrabar_px_pct":round(100*float(adverse_pct),4),
        })
        if equity<=0:
            break
    return {
        "net_pct":round(100*(equity/START_EQUITY-1),5),
        "completed_trades":len(records),
        "wins":sum(t["net_pnl"]>0 for t in records),
        "net_profit_factor":round(sum(max(0,t["net_pnl"]) for t in records)/
          max(1e-12,-sum(min(0,t["net_pnl"]) for t in records)),4),
        "worst_trade_usdt":round(min((x["net_pnl"] for x in records),default=0),4),
        "max_mark_wick_dd_pct_approx":round(max_dd*100,5),
        "fees_usdt":round(sum(t["fee"] for t in records),5),
        "funding_usdt":round(sum(t["funding"] for t in records),5),
        "exit_reason_counts":dict(counts),
        "fills_are_real":False,
        "actual_mark_margin_liquidation_audited":False,
    },records


def main():
    mandate=json.loads((ROOT/"config/research_mandate.lock.json").read_text("utf8"))
    assert mandate["state"]=="LOCKED_USER_ONLY" and mandate["scope"]=="BINANCE_USDT_M_FUTURES"
    manifest=json.loads((ROOT/"research/a217_trendrider_original/evidence/source_manifest.json").read_text("utf8"))
    print("A225: source-attested 204 genuine Binance USDT-M monthly price+funding archives",flush=True)
    candles,funding,receipts=genuine.load_all(manifest)
    events={coin:events_1h(candles[coin]) for coin in genuine.COINS}
    summary={}
    ledgers={}
    for hypothesis in HYPOTHESES:
        summary[hypothesis]={};ledgers[hypothesis]={}
        for label,start,end in PERIODS:
            by_cost={};event_records={}
            for cname,cost in COSTS.items():
                asset_results={}
                event_records[cname]={}
                for coin in genuine.COINS:
                    metrics,trades=simulate(candles[coin],funding[coin],
                        events[coin][hypothesis],start,end,cost)
                    asset_results[coin]=metrics
                    event_records[cname][coin]=trades
                portfolio_pct=round(sum(v["net_pct"] for v in asset_results.values())/3,5)
                max_sleeve_dd=min(v["max_mark_wick_dd_pct_approx"] for v in asset_results.values())
                by_cost[cname]={
                    "3_sleeve_portfolio_return_pct":portfolio_pct,
                    "total_trades":sum(v["completed_trades"] for v in asset_results.values()),
                    "worst_symbol_wick_dd_pct_approx":max_sleeve_dd,
                    "per_coin":asset_results
                }
            summary[hypothesis][label]=by_cost
            ledgers[hypothesis][label]=event_records
    gate={}
    for hyp in HYPOTHESES:
        good=[year for year in ("2024","2025","2026JANSEP")
              if summary[hyp][year]["stress"]["3_sleeve_portfolio_return_pct"]>0
              and summary[hyp][year]["stress"]["total_trades"]>=40
              and summary[hyp][year]["stress"]["worst_symbol_wick_dd_pct_approx"]>=-20]
        gate[hyp]={
            "predefined_fast_stress_gate_pass":len(good)>=2,
            "qualifying_stress_periods":good,
            "source_original_strategy_implemented":False,
            "verified_deployable_edge":False
        }
    target=HERE/"evidence"
    target.mkdir(parents=True,exist_ok=True)
    output={
        "scope":"hypothesis_only_before_original_strategy_search",
        "periods":"2024, 2025, 2026-Jan-Sep; 2023-Nov warmup",
        "pre_registered_protocol":"research/a225_edge_first/PREREG_EVIDENCE_FIRST_4H_LEVELS.md",
        "source_sha_verified_zip_count":len(receipts),
        "source_market":"Binance USD-M futures BTCUSDT ETHUSDT SOLUSDT, genuine 1h OHLCV and fundingRate",
        "archive_receipts":sorted(receipts,key=lambda x:x["key"]),
        "source_coin_event_counts":{coin:{h:len(e[h]) for h in HYPOTHESES} for coin,e in events.items()},
        "hypothesis_results":summary,"gates":gate,
        "caveat":"Not a frozen original authored strategy, NOT official mark, potential optimistic OHLC stop fills; no real orders, no liquidation engine, no untouched future OOS.",
        "not_for_live_or_paper":True
    }
    (target/"A225_EVENT_EDGE_ECONOMIC_SCREEN.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n","utf8")
    (target/"A225_EVENT_EDGE_TRADE_LEDGER.json").write_text(json.dumps(ledgers,ensure_ascii=False)+"\n","utf8")
    print(json.dumps({"zip":len(receipts),"fast_gates":gate,
        "metric_table":{h:{y:{c:[summary[h][y][c]["3_sleeve_portfolio_return_pct"],
           summary[h][y][c]["total_trades"],summary[h][y][c]["worst_symbol_wick_dd_pct_approx"]]
            for c in COSTS} for y,_,_ in PERIODS} for h in HYPOTHESES}},ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
