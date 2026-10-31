#!/usr/bin/env python3
"""A201 audit: verify 16 actual native Freqtrade trade archives and predeclared gate."""
import argparse,hashlib,json,math,zipfile
from pathlib import Path
from statistics import mean
PAIRS=("BTC","ETH","SOL","LINK")
FEES=("5","12p5")
STRATS=("momentum_wick","momentum_rsi")
def read_zip(path,strategy):
    assert zipfile.is_zipfile(path),path
    with zipfile.ZipFile(path) as archive:
        matches=[n for n in archive.namelist() if n.endswith(".json") and "_config" not in n]
        assert len(matches)==1,(path,matches)
        data=json.loads(archive.read(matches[0]))
    assert strategy in data["strategy"],(path,list(data["strategy"]))
    r=data["strategy"][strategy];t=r["trades"]
    assert len(t)==r["total_trades"]
    assert all("2026-05-13"<=v["open_date"][:10]<"2026-10-01" for v in t)
    assert math.isclose(sum(v["profit_abs"] for v in t),r["profit_total_abs"],abs_tol=0.05)
    wins=sorted([v["profit_abs"] for v in t if v["profit_abs"]>0],reverse=True)
    out=dict(trades=len(t),net_USDT=round(r["profit_total_abs"],6),
        net_pct=round(r["profit_total"]*100,6),
        profit_factor=round(float(r["profit_factor"]),5),
        max_drawdown_pct=round(float(r["max_drawdown_account"])*100,5),
        winrate_pct=round(len(wins)*100/max(1,len(t)),4),
        top3_share=round(sum(wins[:3])/sum(wins),5) if wins else None,
        long_n=sum(not v["is_short"] for v in t),short_n=sum(v["is_short"] for v in t),
        stop_n=sum(v["exit_reason"] in ("stop_loss","trailing_stop_loss") for v in t),
        funding_USDT=round(sum(float(v.get("funding_fees",0) or 0) for v in t),6),
        mean_duration_min=round(mean(v["trade_duration"] for v in t),2) if t else None,
        zip_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    if strategy=="momentum_rsi":assert out["long_n"]==0,"Original momentum_rsi LONG=0 contract violated"
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument("--results",required=True)
    a=p.parse_args();root=Path(a.results)
    results={};gates={}
    for st in STRATS:
        outcomes={}
        for sym in PAIRS:
            outcomes[sym]={}
            for fee in FEES:
                entry=read_zip(root/f"{st}-{sym}-fee{fee}.zip",st)
                outcomes[sym][fee]=entry
                print("A201_TRUE_NATIVE",st,sym,fee,entry["trades"],entry["net_pct"],entry["profit_factor"],flush=True)
        pairs={sym:all((v["trades"]>=35 and v["net_pct"]>0 and v["profit_factor"]>=1.2
             and v["max_drawdown_pct"]<15 and v["top3_share"] is not None
             and v["top3_share"]<0.6) for v in outcomes[sym].values()) for sym in PAIRS}
        counts={fee:sum(outcomes[s][fee]["trades"] for s in PAIRS) for fee in FEES}
        gates[st]=dict(qualifying_pairs=pairs,passed_pairs=sum(pairs.values()),
             base_stress_trade_counts=counts,
             economic_pass=sum(pairs.values())>=2 and min(counts.values())>=141,
             execution_approval=False)
        results[st]=outcomes
    o=dict(schema="A201_ORIGINAL_MOMENTUM_WICK_RSI_FREQTRADE2026_4_NATIVE",
      source_commit="c9def379b1036064d592c3a0518a07811f5a9a76",
      source_repo="TheoBrigitte/freqtrade",engine="freqtrade==2026.4",
      timerange="[2026-05-13,2026-10-01)",symbols=PAIRS,fee_scenarios={"5":0.0005,"12p5":0.00125},
      real_data="genuine Binance Vision 5m 2026May-Sep and Binance funding+mark 1h",
      wallet_per_symbol_strategy_USDT=1000,stake_per_trade_USDT=100,nominal_leverage=1,
      conservative_note="No extra slippage; native candle fill not order book; not untouched OOS",
      outcomes=results,preregistered_gates=gates)
    (root/"A201_16_ACTUAL_NATIVE_TRADE_ARCHIVES_VERIFIED.json").write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n")
    print("A201_SIXTEEN_NATIVE_4PAIR_2ORIGINAL_2FEE_TRADE_ARCHIVES_VERIFIED",
          json.dumps(gates,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
