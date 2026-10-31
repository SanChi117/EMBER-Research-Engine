#!/usr/bin/env python3
"""A203 independent native Freqtrade ZIP receipt and frozen research gate."""
from __future__ import annotations
import argparse,hashlib,json,math,zipfile
from pathlib import Path
import numpy as np
PAIRS=("BTC","ETH","SOL","LINK")
FEES=("5","12p5")
NAME="dip_catcher"
def inspect(p):
    assert p.is_file() and zipfile.is_zipfile(p),p
    with zipfile.ZipFile(p) as z:
        names=[n for n in z.namelist() if n.endswith(".json") and "_config" not in n]
        assert len(names)==1,(p,names)
        obj=json.loads(z.read(names[0]))
    assert NAME in obj["strategy"]
    x=obj["strategy"][NAME]
    trs=x["trades"]
    assert len(trs)==x["total_trades"]
    assert all("2025-05-13"<=t["open_date"][:10]<"2025-10-01" for t in trs)
    assert abs(sum(t["profit_abs"] for t in trs)-x["profit_total_abs"])<0.05
    assert all(float(t["leverage"])==1.0 for t in trs),(p,"NONORIGINAL_LEVERAGE")
    wins=sorted((t["profit_abs"] for t in trs if t["profit_abs"]>0),reverse=True)
    dur=[t["trade_duration"] for t in trs]
    return {
       "trades":len(trs),"net_USDT":round(x["profit_total_abs"],6),
       "wallet_return_pct":round(x["profit_total"]*100,6),
       "profit_factor":round(float(x["profit_factor"]),5),
       "max_wallet_drawdown_pct":round(float(x["max_drawdown_account"])*100,5),
       "win_rate_pct":round(len(wins)*100/max(1,len(trs)),5),
       "top3_gross_wins_share":round(sum(wins[:3])/sum(wins),5) if wins else None,
       "long_n":sum(not t["is_short"] for t in trs),
       "short_n":sum(t["is_short"] for t in trs),
       "stops":sum(t["exit_reason"]=="stop_loss" for t in trs),
       "exits_roi":sum(t["exit_reason"]=="roi" for t in trs),
       "median_hold_hours":round(float(np.median(dur))/60,5) if dur else None,
       "p90_hold_hours":round(float(np.percentile(dur,90))/60,5) if dur else None,
       "max_hold_hours":round(float(max(dur))/60,5) if dur else None,
       "over24h":sum(t["trade_duration"]>1440 for t in trs),
       "funding_USDT":round(sum(float(t.get("funding_fees",0) or 0) for t in trs),6),
       "zip_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
    }
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--results",required=True)
    a=ap.parse_args()
    root=Path(a.results);out={}
    for sym in PAIRS:
        out[sym]={}
        for fee in FEES:
            d=inspect(root/f"{NAME}-{sym}-fee{fee}.zip")
            out[sym][fee]=d
            print("A203_GENUINE_NATIVE",sym,fee,d["trades"],d["wallet_return_pct"],d["profit_factor"],d["median_hold_hours"],flush=True)
    passed={}
    fast={}
    for sym in PAIRS:
        x=out[sym]
        passed[sym]=all(
          r["trades"]>=35 and r["net_USDT"]>0 and r["profit_factor"]>=1.2
          and r["max_wallet_drawdown_pct"]<15 and r["top3_gross_wins_share"] is not None
          and r["top3_gross_wins_share"]<0.6
          for r in x.values())
        fast[sym]=passed[sym] and all(
          r["median_hold_hours"] is not None and r["median_hold_hours"]<=6
          and r["p90_hold_hours"]<=24 for r in x.values())
    n={fee:sum(out[sym][fee]["trades"] for sym in PAIRS) for fee in FEES}
    econ=sum(passed.values())>=2 and min(n.values())>=141
    fastok=econ and sum(fast.values())>=2
    data={"schema":"A203_DIP_CATCHER_FRESH_2025_HOLDOUT_8_NATIVE_FREQTRADE_ZIPS",
      "original_repo":"viktors1982/trading",
      "original_commit":"e572140b1b8cb550cb244c67d363087b81bd4ab8",
      "original_git_blob":"76ab2b3f91dc7beaa0be8021a245caa2b3f4186f",
      "engine":"freqtrade==2026.4","window":"[2025-05-13,2025-10-01)",
      "source_prices":"authentic independent A203 2025 Binance futures OHLCV and funding",
      "fees_per_order":{"5":0.0005,"12p5":0.00125},
      "one_wallet_per_coin_USDT":1000,"fixed_proposed_stake_USDT":100,"leverage":1,
      "outcomes":out,"economically_qualifying_pair":passed,
      "frequency_qualifying_pair":fast,"completed_trades":n,
      "economic_research_gate":econ,"rapid_scalper_research_gate":fastok,
      "execution_risk_gate":False,
      "execution_approval":False,
      "limitations":["Original -8% stop too wide for user even if research gate passes",
        "Zero external slippage, maker/taker model imperfect",
        "Not pristine OOS and not one combined portfolio"]}
    (root/"A203_EIGHT_NATIVE_DIPCATCHER_TRADE_RECEIPTS_VERIFIED.json").write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    print("A203_EIGHT_TRUE_NATIVE_ORIGINAL_SOURCE_TRADE_ARCHIVES_VERIFIED",json.dumps({
      "economic":econ,"rapid_scalper":fastok,"risk_gate":False,"passed_pairs":passed,"N":n}),flush=True)
if __name__=="__main__":
    main()
