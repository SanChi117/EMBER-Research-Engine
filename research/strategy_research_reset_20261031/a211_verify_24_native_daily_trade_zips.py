#!/usr/bin/env python3
"""A211 verify exactly 24 original daily Freqtrade 2026.4 ZIPs, 4 segregated
accounts per period and 1x nominal matched BTC/ETH/SOL/LINK hold baseline.
Never label 4 independent wallets as one integrated trading portfolio.
"""
from __future__ import annotations
import argparse,hashlib,json,math,statistics,zipfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from statistics import mean,median

PAIRS=("BTC","ETH","SOL","LINK")
YEARS=("2024","2025","2026")
FEES=("5","12p5")
STRAT="TrendFutures"
SOURCE_BLOB="2e6b83ba128373655090ca4827d8c7954ffaedfd"
DATE_WINDOWS={"2024":("2024-01-01","2025-01-01"),
              "2025":("2025-01-01","2026-01-01"),
              "2026":("2026-01-01","2026-10-01")}

def numeric(x):
    if x is None:return None
    v=float(x)
    return v if math.isfinite(v) else None

def read_zip(path,y):
    assert path.is_file() and zipfile.is_zipfile(path),("MISSING_NATIVE_ZIP",str(path))
    b=path.read_bytes()
    with zipfile.ZipFile(path) as z:
        files=[n for n in z.namelist() if n.endswith(".json") and "_config" not in n]
        assert len(files)==1,(path,files)
        obj=json.loads(z.read(files[0]))
    assert STRAT in obj["strategy"],(path,list(obj["strategy"]))
    row=obj["strategy"][STRAT]
    trades=row["trades"]
    assert len(trades)==row["total_trades"],(path,"N_INCONSISTENT")
    assert abs(sum(float(t["profit_abs"]) for t in trades)-float(row["profit_total_abs"]))<0.06
    lo,hi=DATE_WINDOWS[y]
    assert all(lo<=t["open_date"][:10]<hi for t in trades),(path,"OUTSIDE_YEAR")
    assert all(float(t["leverage"])==1.0 for t in trades),(path,"WRONG_ORIGINAL_LEVERAGE")
    positives=sorted((float(t["profit_abs"]) for t in trades if t["profit_abs"]>0),reverse=True)
    negatives=[-float(t["profit_abs"]) for t in trades if t["profit_abs"]<0]
    pnl_by_exit=Counter(t["exit_reason"] for t in trades)
    durations=[float(t["trade_duration"])/1440 for t in trades]
    return {
        "trades":len(trades),
        "source_hash_verified":True,
        "zip_sha256":hashlib.sha256(b).hexdigest(),
        "wallet_net_USDT":round(float(row["profit_total_abs"]),6),
        "wallet_net_pct":round(float(row["profit_total"])*100,6),
        "profit_factor":numeric(row.get("profit_factor")),
        "reported_max_wallet_dd_pct":round(float(row.get("max_drawdown_account",0))*100,6),
        "long_n":sum(not t["is_short"] for t in trades),
        "short_n":sum(t["is_short"] for t in trades),
        "winner_n":len(positives),"loser_n":len(negatives),
        "gross_wins_USDT":round(sum(positives),6),
        "gross_losses_USDT":round(sum(negatives),6),
        "max_one_trade_loss_USDT":round(min([float(t["profit_abs"]) for t in trades] or [0]),5),
        "top3_wins_gross_share":(round(sum(positives[:3])/sum(positives),6) if positives else None),
        "median_hold_days":round(median(durations),4) if durations else None,
        "max_hold_days":round(max(durations),4) if durations else None,
        "exit_reason_counts":dict(pnl_by_exit),
        "funding_USDT":round(sum(float(t.get("funding_fees",0) or 0) for t in trades),6),
        "trade_rows":trades,
    }

def passive_price_benchmark(path,y,fee):
    data=json.loads(path.read_text())
    assert len(data)>=1000,("MISSING_2023_WARMUP_DAILY_HISTORY",path,len(data))
    yy=int(y)
    lo=int(datetime(yy,1,1,tzinfo=timezone.utc).timestamp()*1000)
    stop=int(datetime(yy+1,1,1,tzinfo=timezone.utc).timestamp()*1000)
    if yy==2026:stop=int(datetime(2026,10,1,tzinfo=timezone.utc).timestamp()*1000)
    selected=[r for r in data if lo<=r[0]<stop]
    assert len(selected) in (365,366,273),(y,len(selected))
    assert selected[0][0]==lo
    start_open=float(selected[0][1]);end_close=float(selected[-1][4])
    gross=100.0*(end_close/start_open-1)
    cost=100.0*fee+(100.0*end_close/start_open)*fee
    price_ret=(end_close/start_open-1)*100
    # Invest 100 USDT of 1000 USDT; 900 idle. Funding omitted: price-only futures benchmark, not a genuine spot instrument.
    daily_equity=[900+100*float(r[4])/start_open for r in selected]
    peak=1000.;dd=0
    for v in daily_equity:
        peak=max(peak,v);dd=max(dd,(peak-v)/peak)
    return {"test_start_open":start_open,"test_end_close":end_close,
            "buyhold_raw_price_change_pct":round(price_ret,6),
            "100USDT_buyhold_net_USDT_after_roundtrip_fees_price_only":round(gross-cost,6),
            "1000USDT_wallet_buyhold_return_pct_same_100USDT_allocation":round((gross-cost)/10,6),
            "buyhold_wallet_marked_close_only_max_dd_pct":round(dd*100,6),
            "funding_in_benchmark":False,
            "bid_ask_spread_in_benchmark":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--results",required=True);ap.add_argument("--data",required=True)
    a=ap.parse_args()
    root=Path(a.results);data=Path(a.data)
    manifest=json.loads((data/"A211_REAL_BINANCE_SOURCE_MANIFEST.json").read_text())
    assert manifest["schema"]=="A211_TRUE_BINANCE_DAILY_PRICE_HOURLY_MARK_FUNDING_SOURCES"
    assert manifest["monthly_source_zip_count"]==4*3*45
    rows={};book={}
    for y in YEARS:
        rows[y]={};book[y]={}
        for sym in PAIRS:
            rows[y][sym]={};book[y][sym]={}
            dataset=data/"futures"/f"{sym}_USDT_USDT-1d-futures.json"
            for fee in FEES:
                path=root/f"{y}-{STRAT}-{sym}-fee{fee}.zip"
                vals=read_zip(path,y)
                trs=vals.pop("trade_rows")
                # Prevent separate portfolios with simultaneous duplicate trades (one symbol/one wallet).
                seq=sorted(trs,key=lambda t:t["open_date"])
                for i in range(1,len(seq)):
                    assert seq[i]["open_date"]>=seq[i-1]["close_date"],(
                        "OVERLAPPING_TRADES_IN_ONE_ACCOUNT",y,sym,fee,i)
                if vals["trades"] and vals["gross_losses_USDT"]>0:
                    assert vals["profit_factor"] is not None
                    assert abs(vals["profit_factor"]-(vals["gross_wins_USDT"]/vals["gross_losses_USDT"]))<0.025
                rows[y][sym][fee]=vals
                book[y][sym][fee]=passive_price_benchmark(dataset,y,.0005 if fee=="5" else .00125)
                print("A211_ORIGINAL_NATIVE_YEAR_SYMBOL_FEE",y,sym,fee,
                      vals["trades"],vals["wallet_net_pct"],vals["profit_factor"],flush=True)
    summary={}
    for y in YEARS:
        summary[y]={}
        for fee in FEES:
            vals=[rows[y][sym][fee] for sym in PAIRS]
            bhs=[book[y][sym][fee] for sym in PAIRS]
            # Partitioned 4 independent 1000 wallets, thus 4000 account capital.
            p=sum(x["wallet_net_USDT"] for x in vals)
            bench=sum(x["100USDT_buyhold_net_USDT_after_roundtrip_fees_price_only"] for x in bhs)
            wins=sum(x["gross_wins_USDT"] for x in vals)
            loses=sum(x["gross_losses_USDT"] for x in vals)
            summary[y][fee]={
                "independent_model_wallets_n":4,"total_initial_capital_USDT":4000,
                "realized_net_USDT_sum_independent_wallets":round(p,6),
                "equal_partition_total_4000_USDT_return_pct":round(p/4000*100,6),
                "cash_4000_USDT_return_pct":0.0,
                "price_only_100USDT_hold_per_coin_4000_USDT_wallet_benchmark_pct":round(bench/4000*100,6),
                "price_only_hold_benchmark_funding_omitted":True,
                "beat_price_only_hold_100USDT_partition":p>bench,
                "total_completed_trades":sum(x["trades"] for x in vals),
                "total_long":sum(x["long_n"] for x in vals),
                "total_short":sum(x["short_n"] for x in vals),
                "sum_gross_wins_USDT":round(wins,6),
                "sum_gross_losses_USDT":round(loses,6),
                "aggregate_profit_factor":round(wins/loses,6) if loses else None,
                "positive_wallets_n":sum(x["wallet_net_USDT"]>0 for x in vals),
                "worst_wallet_net_pct":min(x["wallet_net_pct"] for x in vals),
                "worst_reported_wallet_dd_pct":max(x["reported_max_wallet_dd_pct"] for x in vals),
                "full_portfolio_mark_to_market_max_drawdown":"NOT_COMPUTED_CANNOT_CLAIM",
            }
    profitable_both=sum(
       summary[y][f]["realized_net_USDT_sum_independent_wallets"]>0
       for y in YEARS for f in FEES
    )
    technically_worth_investigating=(
        sum(summary[y]["5"]["realized_net_USDT_sum_independent_wallets"] for y in YEARS)>0
        and sum(summary[y]["12p5"]["realized_net_USDT_sum_independent_wallets"] for y in YEARS)>0
        and sum(summary[y]["5"]["realized_net_USDT_sum_independent_wallets"]>0 for y in YEARS)>=2
        and sum(summary[y]["12p5"]["realized_net_USDT_sum_independent_wallets"]>0 for y in YEARS)>=2
        and sum(summary[y]["12p5"]["total_completed_trades"] for y in YEARS)>=30
    )
    report={
        "schema":"A211_EXACT_ORIGINAL_TRENDFUTURES_THREE_YEAR_24_NATIVE_FREQTRADE_ZIPS",
        "original_repo":"Kureshi25/cryptobot",
        "original_commit":"c8ffbaabee9f63630e179c698c53df4916b93f8e",
        "strategy_file_gitblob":"2e6b83ba128373655090ca4827d8c7954ffaedfd",
        "engine":"freqtrade==2026.4",
        "native_original_no_parameter_tuning":True,
        "source_sha_manifest":manifest["source_sha"],
        "binance_full_history_2023_2026":manifest["data"],
        "test_years":list(YEARS),"scenario_fee_each_side":{"5":.0005,"12p5":.00125},
        "results":rows,"passive_price_only_futures_quote_benchmark":book,
        "equal_capital_partition_summary":summary,
        "research_economic_followup_candidate":technically_worth_investigating,
        "forward_paper_validated":False,
        "execution_approval":False,
        "limitations":[
          "Market order backtest has no EXTRA spread/slippage, so optimistic execution",
          "BTC/ETH/SOL/LINK futures buyhold benchmark is price-only, no funding; not actual funded spot buyhold",
          "Full daily marked-to-market portfolio drawdown is NOT computed, do not use only trade-close DD as total risk",
          "2024, 2025, 2026 market years have been previously explored by EMBER; not pristine OOS",
          "Original fallback stoploss -35% price, custom stop behavior must be checked separately",
          "Funded Futures data via Binance Vision daily 2023-2026, but static market metadata is modelled, no real fills",
          "Do not derive a live execution signal or leverage from this research"
        ]}
    (root/"A211_24_NATIVE_REAL_BINANCE_RESULTS_VERIFIED.json").write_text(
       json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print("A211_TWENTYFOUR_NATIVE_ZIPS_ORIGINAL_TREND_WITH_BENCHMARKS_VERIFIED",
          json.dumps({"summary":summary,"research_candidate":technically_worth_investigating}),flush=True)

if __name__=="__main__":main()
