#!/usr/bin/env python3
"""A205 fail-closed verifier for 16 untouched native Freqtrade 2026.4 trade ZIPs.
BTC/ETH/SOL/LINK x two fees x two chronological source windows.
No post-hoc tuning, no mixing four single-pair independent wallets.
"""
from __future__ import annotations
import argparse,hashlib,json,math,zipfile
from pathlib import Path
from statistics import median,mean
from datetime import datetime,timezone
PAIRS=("BTC","ETH","SOL","LINK")
FEES=("5","12p5")
YEARS=(2025,2026)
STRAT="AggressiveSupportResistanceScalper"
START={y:datetime(y,5,13,tzinfo=timezone.utc).timestamp() for y in YEARS}
END={y:datetime(y,10,1,tzinfo=timezone.utc).timestamp() for y in YEARS}
DAYS=141
def dt(s):
    return datetime.fromisoformat(s.replace("Z","+00:00")).replace(tzinfo=timezone.utc).timestamp()
def parse(path,year):
    assert path.is_file() and zipfile.is_zipfile(path),path
    blob=path.read_bytes()
    with zipfile.ZipFile(path) as z:
        names=[n for n in z.namelist() if n.endswith(".json") and "_config" not in n]
        assert len(names)==1,(path,names)
        obj=json.loads(z.read(names[0]))
    assert STRAT in obj["strategy"],(path,list(obj["strategy"]))
    x=obj["strategy"][STRAT]
    trades=x["trades"]
    assert len(trades)==x["total_trades"]
    assert abs(sum(float(t["profit_abs"]) for t in trades)-float(x["profit_total_abs"]))<.06
    assert all(START[year]<=dt(t["open_date"])<END[year] for t in trades)
    assert all(1<=float(t["leverage"])<=10.00001 for t in trades)
    assert all(float(t["leverage"])>=9.999 for t in trades),(path,"non-original leverage")
    assert all(t["open_date"]<=t["close_date"] for t in trades)
    assert len(trades)==len({(t["open_date"],t["close_date"],t["is_short"]) for t in trades}),(path,"duplicate entries")
    positives=sorted([float(t["profit_abs"]) for t in trades if t["profit_abs"]>0],reverse=True)
    durations=[float(t["trade_duration"]) for t in trades]
    ordered=sorted(trades,key=lambda t:dt(t["open_date"]))
    gaps=[(dt(ordered[i]["open_date"])-dt(ordered[i-1]["close_date"]))/60.0 for i in range(1,len(ordered))]
    assert all(g>=0 for g in gaps),(path,"two trades overlap one position per coin")
    pnl=float(x["profit_total_abs"])
    # Freqtrade profit ratio includes 10x and fees, so DO NOT multiply by leverage again.
    return {
       "trades":len(trades),"net_USDT":round(pnl,6),
       "wallet_return_pct":round(float(x["profit_total"])*100,6),
       "profit_factor":round(float(x["profit_factor"]),5),
       "max_wallet_dd_pct":round(float(x["max_drawdown_account"])*100,5),
       "win_rate_pct":round(100*len(positives)/max(1,len(trades)),5),
       "top3_gross_win_share":round(sum(positives[:3])/sum(positives),5) if positives else None,
       "long_n":sum(not t["is_short"] for t in trades),
       "short_n":sum(t["is_short"] for t in trades),
       "mean_hold_minutes":round(mean(durations),3) if durations else None,
       "median_hold_minutes":round(median(durations),3) if durations else None,
       "p90_hold_minutes":sorted(durations)[math.ceil(.90*len(durations))-1] if durations else None,
       "max_hold_minutes":max(durations) if durations else None,
       "held_gt_120m_n":sum(d>120 for d in durations),
       "held_gt_1440m_n":sum(d>1440 for d in durations),
       "reentry_gap_count":len(gaps),"reentry_gap_le_5m_n":sum(g<=5 for g in gaps),
       "reentry_gap_median_min":round(median(gaps),3) if gaps else None,
       "stops":sum(t["exit_reason"] in ("stop_loss","trailing_stop_loss") for t in trades),
       "roi_exits":sum(t["exit_reason"]=="roi" for t in trades),
       "time_exit_n":sum(t["exit_reason"]=="scalp_time_limit" for t in trades),
       "fast_rotation_n":sum(t["exit_reason"]=="fast_profit_rotation" for t in trades),
       "other_exit_reasons":sorted({t["exit_reason"] for t in trades}),
       "funding_USDT":round(sum(float(t.get("funding_fees",0) or 0) for t in trades),6),
       "worst_trade_profit_ratio_pct":round(100*min((float(t["profit_ratio"]) for t in trades),default=0),4),
       "sum_stake_USDT":round(sum(float(t["stake_amount"]) for t in trades),4),
       "zip_sha256":hashlib.sha256(blob).hexdigest(),
       "intervals":[[dt(t["open_date"]),min(END[year],dt(t["close_date"]))] for t in ordered],
    }
def occupancy(rows,year):
    ev=[]
    for pair,r in rows.items():
        for start,finish in r["intervals"]:
            if finish>start:ev.extend(((start,+1),(finish,-1)))
    ev.sort(key=lambda t:(t[0],t[1]))
    buckets={i:0.0 for i in range(5)}
    cursor=START[year];current=0
    for at,diff in ev:
        assert START[year]<=at<=END[year]
        buckets[current]+=max(0,at-cursor)
        current+=diff
        assert 0<=current<=4
        cursor=at
    buckets[current]+=max(0,END[year]-cursor)
    total=END[year]-START[year]
    return {
        "all_four_occupied_pct":round(buckets[4]/total*100,4),
        "at_least_one_slot_free_pct":round((total-buckets[4])/total*100,4),
        "mean_open_positions":round(sum(n*v for n,v in buckets.items())/total,4),
        "by_concurrency_pct":{str(k):round(v/total*100,3) for k,v in buckets.items()},
    }
def economics(r):
    return (r["trades"]>=35 and r["wallet_return_pct"]>0 and r["profit_factor"]>=1.20
        and r["max_wallet_dd_pct"]<15 and r["top3_gross_win_share"] is not None
        and r["top3_gross_win_share"]<0.6)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--results",required=True)
    a=p.parse_args();root=Path(a.results)
    results={}
    for y in YEARS:
        results[str(y)]={}
        for sym in PAIRS:
            results[str(y)][sym]={}
            for fee in FEES:
                path=root/f"{y}-{STRAT}-{sym}-fee{fee}.zip"
                row=parse(path,y)
                results[str(y)][sym][fee]=row
                print("A205_TRUE_NATIVE",y,sym,fee,
                      "N",row["trades"],"net",row["wallet_return_pct"],
                      "PF",row["profit_factor"],"heldp90",row["p90_hold_minutes"],flush=True)
    pair_pass={sym:all(economics(results[str(y)][sym][fee])
                      for y in YEARS for fee in FEES) for sym in PAIRS}
    year_fee_n={str(y):{fee:sum(results[str(y)][s][fee]["trades"] for s in PAIRS) for fee in FEES} for y in YEARS}
    freq_pass=all(n>=DAYS for counts in year_fee_n.values() for n in counts.values())
    econ=sum(pair_pass.values())>=2 and freq_pass
    fast={}
    for y in YEARS:
        fast[str(y)]={}
        for fee in FEES:
            rows={sym:results[str(y)][sym][fee] for sym in PAIRS}
            occup=occupancy(rows,y)
            gaps=sum(r["reentry_gap_count"] for r in rows.values())
            immediate=sum(r["reentry_gap_le_5m_n"] for r in rows.values())
            held=sum(r["trades"] for r in rows.values())
            slow=sum(r["held_gt_120m_n"] for r in rows.values())
            fast[str(y)][fee]={
                **occup,
                "closed_trades_per_day":round(held/DAYS,5),
                "within_5m_reentry_pct":round(100*immediate/gaps,3) if gaps else None,
                "held_gt_2h_pct":round(100*slow/max(1,held),3),
                "time_limit_parity_pass":slow<=0.1*max(1,held),
                "tempo_gate_3_per_day":held>=DAYS*3,
                "reentry_event_gate":(gaps==0 or immediate/gaps<.30),
                "free_slot_gate":occup["at_least_one_slot_free_pct"]>=20,
                "p90_hold_le_24h":all((r["p90_hold_minutes"] is None or r["p90_hold_minutes"]<=1440) for r in rows.values())
            }
    execution_gate=econ and all(
         f["time_limit_parity_pass"] and f["tempo_gate_3_per_day"]
         and f["reentry_event_gate"] and f["free_slot_gate"] and f["p90_hold_le_24h"]
         for row in fast.values() for f in row.values())
    # Never approve execution automatically; additional real slippage and liquidation risk checks are mandatory.
    output={
        "schema":"A205_SOURCE_PINNED_NATIVE_16_ZIPS_TWO_INDEPENDENT_YEARS",
        "strategy":STRAT,"original_repo":"Meszqt/freqtrade-test",
        "commit":"7062cdd465f30acb480f6ad8f678f958a8a0e554",
        "source_gitblob":"4e3084865a95a694be5178fe60d9130ecd24c002",
        "engine":"freqtrade==2026.4",
        "years":[2025,2026],"timeranges":[f"{y}-05-13/{y}-10-01" for y in YEARS],
        "fees_per_side":{"5":.0005,"12p5":.00125},
        "initial_wallet_each_symbol_USDT":1000,"stake_margin_each_trade_USDT":100,
        "leverage_original":10,"max_open_each_symbol":1,
        "data":"genuine Binance Vision futures five minute OHLCV and hourly mark/funding A195,A196,A203",
        "results":results,
        "economic_pair_pass_both_years_both_fees":pair_pass,
        "year_fee_closed_trade_counts":year_fee_n,
        "independent_frequency_min_1_per_day":freq_pass,
        "economic_research_gate":econ,
        "tempo_execution_gate":execution_gate,
        "execution_approval":False,
        "tempo_by_year_fee":fast,
        "limitations":["This already used market years for multiple prior research projects, not pristine OOS",
          "Source levered 10x: a 6% stoploss is 6% of margin (roughly 0.6% price), not 6% price",
          "No extra bid-ask/slippage/nonfill beyond Freqtrade native limit simulation",
          "Four independent wallets cannot be summated into a single portfolio",
          "Even research gate passing would require separate forward PAPER and execution quality controls"]
    }
    # intervals are machine-readable raw trade durations, keep in main outcome only if needed
    (root/"A205_16_NATIVE_SR_REJECTION_TWO_YEAR_VERIFIED.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    print("A205_SIXTEEN_ACTUAL_NATIVE_ORIGINAL_SOURCE_TRADE_ARCHIVES_VERIFIED",
          json.dumps({"pair_pass":pair_pass,"n":year_fee_n,"economic":econ,"tempo":execution_gate},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
