#!/usr/bin/env python3
"""A199 strict real native Freqtrade 2026.4 trade archive parser and frozen gate.
Per-strategy, 4 pairs x two fees. Does not select symbols post hoc or sum
separate wallet returns as a common portfolio; zero trades is a failure.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path
from statistics import mean
PAIRS=("BTC","ETH","SOL","LINK")
FEES=("5","12p5")
def load(path,strategy):
    assert path.is_file() and zipfile.is_zipfile(path),path
    blob=path.read_bytes()
    with zipfile.ZipFile(path) as z:
        candidates=[n for n in z.namelist() if n.endswith(".json") and "_config" not in n]
        assert len(candidates)==1,candidates
        obj=json.loads(z.read(candidates[0]))
    assert strategy in obj["strategy"],(strategy,list(obj["strategy"]))
    x=obj["strategy"][strategy]
    trades=x["trades"]
    assert x["total_trades"]==len(trades)
    assert all("2026-05-13"<=t["open_date"][:10]<"2026-10-01" for t in trades)
    gross_wins=sorted((t["profit_abs"] for t in trades if t["profit_abs"]>0),reverse=True)
    net=x["profit_total_abs"]
    assert abs(sum(t["profit_abs"] for t in trades)-net)<0.05,(path,"pnl mismatch",net)
    return {
      "trades":len(trades),
      "net_pct":round(float(x["profit_total"])*100,6),
      "net_USDT":round(net,6),
      "profit_factor":round(float(x["profit_factor"]),5),
      "wallet_max_dd_pct":round(float(x["max_drawdown_account"])*100,5),
      "winrate_pct":round(sum(t["profit_abs"]>0 for t in trades)*100/max(1,len(trades)),3),
      "avg_duration_min":round(mean(t["trade_duration"] for t in trades),2) if trades else None,
      "top3_gross_wins_share":round(sum(gross_wins[:3])/sum(gross_wins),5) if gross_wins else None,
      "top3_vs_net":round(sum(gross_wins[:3])/net,5) if net>0 else None,
      "long_n":sum(not t["is_short"] for t in trades),
      "short_n":sum(t["is_short"] for t in trades),
      "long_USDT":round(sum(t["profit_abs"] for t in trades if not t["is_short"]),4),
      "short_USDT":round(sum(t["profit_abs"] for t in trades if t["is_short"]),4),
      "funding_USDT":round(sum(float(t.get("funding_fees",0) or 0) for t in trades),5),
      "stops":sum(t["exit_reason"] in ("stop_loss","trailing_stop_loss") for t in trades),
      "first_open":min((t["open_date"] for t in trades),default=None),
      "last_open":max((t["open_date"] for t in trades),default=None),
      "native_zip_sha256":hashlib.sha256(blob).hexdigest(),
    }
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--results",required=True)
    ap.add_argument("--strategy",required=True,choices=("FReinforcedStrategy","FAdxSmaStrategy"))
    args=ap.parse_args()
    root=Path(args.results)
    items={}
    for sym in PAIRS:
        items[sym]={}
        for fee in FEES:
            path=root/f"{args.strategy}-{sym}-fee{fee}.zip"
            row=load(path,args.strategy)
            items[sym][fee]=row
            print("A199_GENUINE_NATIVE_FREQTRADE_RESULT",args.strategy,sym,fee,
              "n",row["trades"],"net_pct",row["net_pct"],"PF",row["profit_factor"],
              "DD",row["wallet_max_dd_pct"],
              "top3",row["top3_gross_wins_share"],flush=True)
    gate={}
    for sym in PAIRS:
        gate[sym]=all((x["trades"]>=35 and x["net_pct"]>0 and x["profit_factor"]>=1.2
            and x["wallet_max_dd_pct"]<15 and x["top3_gross_wins_share"] is not None
            and x["top3_gross_wins_share"]<.6)
            for x in (items[sym]["5"],items[sym]["12p5"]))
    lowN=sum(items[s]["5"]["trades"] for s in PAIRS)
    hiN=sum(items[s]["12p5"]["trades"] for s in PAIRS)
    o={"schema":"EMBER_A199_ORIGINAL_PUBLISHED_FUTURES_FREQTRADE_NATIVE_EIGHT_RECEIPTS",
      "strategy":args.strategy,
      "original_repository":"freqtrade/freqtrade-strategies",
      "original_source_commit":"f3340ce11f5bdf62f598522e64d1f5638eaa13f5",
      "engine":"freqtrade==2026.4","window":"[2026-05-13,2026-10-01)",
      "wallet_each_pair":1000,"stake_USDT":100,"max_open_each_pair":1,
      "futures_isolated":True,"nominal_leverage":"1x original strategy class no leverage override",
      "5m_data_real":"Binance Vision USD-M 5m May-Sep, plus A195 genuine mark and settled funding",
      "initial_stress":"5bps and 12.5bps per fill, no additional bidask or slippage model",
      "outcomes":items,"predeclared_pair_gate":gate,"passes_two_pairs":sum(gate.values())>=2,
      "base_trades_across_four_separate_pair_wallets":lowN,
      "stress_trades_across_four_separate_pair_wallets":hiN,
      "predeclared_frequency_gate_1_per_day_four":lowN>=141 and hiN>=141,
      "overall_initial_advancement":sum(gate.values())>=2 and lowN>=141 and hiN>=141,
      "limitations":["Original repo example strategies, not verified profitable systems",
        "2026 May-Sep data used before and not truly fresh OOS",
        "Each symbol separately has independent wallet; four returns cannot be summed as shared portfolio",
        "Static market metadata and native candle-based limit fills, not exchange order book",
        "No extra slippage, no risk-correlation portfolio tests, no live orders",
        "If original sources use 5m resampling verify informative data causality before promotion",
        "Successful two-pair gate still not evidence of 3-5 executable independent trades/day"]}
    (root/f"A199_{args.strategy}_EIGHT_NATIVE_RESULTS.json").write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n")
    print("A199_EIGHT_ACTUAL_NATIVE_SOURCE_TRADE_ARCHIVES_VERIFIED",args.strategy,
      json.dumps({"gate":gate,"low_fee_total_trades":lowN,"stress_total_trades":hiN,
                  "advancement":o["overall_initial_advancement"]}),flush=True)
if __name__=="__main__":main()
