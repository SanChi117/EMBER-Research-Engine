#!/usr/bin/env python3
"""Machine receipt check for original unchanged DoubleMA Freqtrade 2026.4 crosspair.
Native Freqtrade ZIPs, no homemade signal. Source+fee+concentration crosschecks.
"""
from __future__ import annotations
import argparse,json,math,statistics,zipfile
from pathlib import Path
SYMBOLS=("BTC","ETH","SOL","LINK")
FEES=("5","12p5")
SOURCE_SHA="40af5c7c1c44253766428cfb06babf22f9817aa4"
BLOB="22ca6588bbd056e671783f676f1a4010cbfc1bb6"
START="2026-05-13";END="2026-10-01"
def open_native(path):
    assert zipfile.is_zipfile(path),("missing_freqtrade_zip",str(path))
    with zipfile.ZipFile(path) as z:
        items=[p for p in z.namelist() if p.endswith(".json") and "_config" not in p]
        assert len(items)==1,items
        body=json.loads(z.read(items[0]))
    assert "VideoDoubleMaFuturesStrategy" in body["strategy"]
    return body["strategy"]["VideoDoubleMaFuturesStrategy"]
def result(stat,sym,fee):
    trades=stat["trades"]
    assert len(trades)==stat["total_trades"],(sym,fee,"countmismatch")
    for t in trades:
        assert t["open_date"][:10]>=START and t["open_date"][:10]<END,(sym,fee,"out_of_time",t["open_date"])
        assert t["is_short"] in (True,False)
    wins=sorted((float(t["profit_abs"]) for t in trades if t["profit_abs"]>0),reverse=True)
    longs=[t for t in trades if not t["is_short"]]
    shorts=[t for t in trades if t["is_short"]]
    net=float(stat["profit_total_abs"])
    profit_abs=sum(float(t["profit_abs"]) for t in trades)
    assert abs(net-profit_abs)<max(1e-3,abs(net)*1e-5),(sym,fee,net,profit_abs)
    result={"n":len(trades),"longs":len(longs),"shorts":len(shorts),
      "long_profit_usd":round(sum(t["profit_abs"] for t in longs),4),
      "short_profit_usd":round(sum(t["profit_abs"] for t in shorts),4),
      "profit_usd":round(net,4),
      "return_pct":round(float(stat["profit_total"])*100,4),
      "profit_factor":round(float(stat.get("profit_factor",0) or 0),4),
      "max_wallet_dd_pct":round(float(stat.get("max_drawdown_account",0) or 0)*100,4),
      "win_pct":round(sum(float(t["profit_abs"])>0 for t in trades)*100/max(1,len(trades)),3),
      "top3_wins_fraction_of_all_wins":round(sum(wins[:3])/sum(wins),4) if wins else None,
      "top3_wins_fraction_of_NET_profit":round(sum(wins[:3])/net,4) if net>0 else None,
      "mean_trade_hours":round(statistics.mean((float(t["trade_duration"]) / 60 for t in trades)),3) if trades else None,
      "sum_native_funding_fees_usd":round(sum(float(t.get("funding_fees",0) or 0) for t in trades),4),
      "first_entry":min((x["open_date"] for x in trades),default=None),
      "last_entry":max((x["open_date"] for x in trades),default=None),
      "trade_receipts_sha":"stored in artifact ZIP for this exact pair+fee",
      "exit_reasons":{reason:sum(t["exit_reason"]==reason for t in trades) for reason in sorted(set(t["exit_reason"] for t in trades))},
      "net_trade_usd":sum(float(t["profit_abs"]) for t in trades)}
    return result,[{"entry":t["open_date"],"exit":t["close_date"],"short":t["is_short"],"pnl":round(float(t["profit_abs"]),4),"reason":t["exit_reason"]} for t in trades]
def main():
    p=argparse.ArgumentParser();p.add_argument("--report-dir",required=True)
    args=p.parse_args()
    d=Path(args.report_dir)
    src=json.loads((d/"data/A195_DATA_SHA_MANIFEST.json").read_text())
    assert len(src["source_shas"])==4
    assert src["test_start"]==START
    assert all(src["data"][sym+"USDT"]["funding_settlements"]>300 for sym in SYMBOLS)
    results={};receipts={}
    for sym in SYMBOLS:
        results[sym]={};receipts[sym]={}
        for fee in FEES:
            x=open_native(d/f"native-{sym}-fee{fee}.zip")
            o,trades=result(x,sym,fee)
            results[sym][fee]=o;receipts[sym][fee]=trades
            print("A195_ORIGINAL_NATIVE_REPLAY",sym,fee,"N",o["n"],"NET_PCT",o["return_pct"],
                "PF",o["profit_factor"],"DD_PCT",o["max_wallet_dd_pct"],"TOP3_NET",o["top3_wins_fraction_of_NET_profit"],flush=True)
    # Inspect fee-conditioned paths, do not naively claim 12.5bps improvement is an edge.
    diffs={}
    for sym in SYMBOLS:
        low={(x["entry"],x["short"]):x for x in receipts[sym]["5"]}
        high={(x["entry"],x["short"]):x for x in receipts[sym]["12p5"]}
        common=set(low)&set(high)
        changed=[{"entry":k[0],"old_exit":low[k]["exit"],"new_exit":high[k]["exit"],
                  "old_profit":low[k]["pnl"],"new_profit":high[k]["pnl"]}
                 for k in sorted(common) if low[k]["exit"]!=high[k]["exit"]]
        diffs[sym]={"matched_entries":len(common),"added_high_fee":len(high.keys()-low.keys()),
                    "removed_high_fee":len(low.keys()-high.keys()),
                    "changed_exit_date_samples":changed[:100],"changed_exit_count":len(changed)}
    control=results["ETH"]["5"]
    baseline={"n":27,"return_pct":39.864217,"profit_usd":3986.421749,"profit_factor":2.23859}
    parity=None # A187 covers 29 extra October days, cannot compare direct equity/trade parity
    strict_gate={}
    for sym in ("BTC","SOL","LINK"):
        z=[results[sym][fee] for fee in FEES]
        strict_gate[sym]=bool(all(x["n"]>=20 and x["profit_factor"]>=1.25 and x["profit_usd"]>0
          and x["max_wallet_dd_pct"]<15 and x["top3_wins_fraction_of_all_wins"] is not None
          and x["top3_wins_fraction_of_all_wins"]<0.60 for x in z))
    out={"schema":"EMBER_A195_ORIGINAL_DOUBLEMA_4_PAIR_NATIVE_8_RECEIPTS","date":"2026-10-31",
       "original_commit":SOURCE_SHA,"original_blob":BLOB,"engine":"freqtrade==2026.4",
       "window":"[2026-05-13,2026-10-01)","initial_usdt":10000,"leverage":2,
       "mode":"one pair per run Binance USD-M historical, synthetic STATIC metadata Binance, isolated",
       "data_manifest":"A195_DATA_SHA_MANIFEST.json",
       "resampling":"4h/1d native equivalent rollup from contiguous real Binance USD-M1h",
       "costs":"0.0005 and 0.00125 trading fee per fill side, no extra adverse slippage; native actual Binance Vision settled funding and mark klines",
       "prior_A187_control":"A187 uses same original class but OKX offline market metadata; compare ETH 5bps carefully; original source pin frozen May12",
       "original_ETH_A187_reference":baseline,"ETH_5bps_matches_A187_within_10c":parity,
       "ETH_A187_control_noncomparable_October_not_yet_monthly_published":True,
       "outcomes":results,"fee_path_parity":diffs,"gate_per_NEW_coin":strict_gate,
       "total_new_coins_passing":sum(strict_gate.values()),
       "mechanical_gate_pass":bool(sum(strict_gate.values())>=2),
       "limitations":["Original 2x/near-full-account stake not 1pct risk sizing","Current source has not passed lookahead-analysis / recursive-analysis",
          "Original limit fill model, no orderbook/real market slippage, no 5m execution detail",
          "Exact source, no parameter retune, but Binance market metadata differs A187 OKX",
          "Only one 2026 historical window crossmarket; BTC author previously tested 2021-2026",
          "Research team has already inspected historical 2026 data: not prospective unseen to entire research team",
          "No live, no autotrading, no SMOKE or PAPER scheduler modification"]}
    (d/"A195_ORIGINAL_NATIVE_CROSSPAIR_RESULTS.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print("A195_ALL_EIGHT_GENUINE_NATIVE_ORIGINAL_TESTS_COMPLETED",flush=True)
    print(json.dumps({"control_parity":parity,"gate":strict_gate,"metrics":results},ensure_ascii=False,indent=2),flush=True)
if __name__=="__main__":main()
