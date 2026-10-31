#!/usr/bin/env python3
"""Parse A197 alternate 2025 regime actual Freqtrade 2026.4 original-source native ZIPs;
exact frozen economic gate; no interpolation, selection, or post-hoc optimization."""
import argparse,hashlib,json,zipfile
from pathlib import Path
from statistics import mean
SYMS=("BTC","ETH","SOL","LINK")
FEES=("5","12p5")
def parse_zip(p):
    assert p.is_file() and zipfile.is_zipfile(p),p
    raw=p.read_bytes()
    with zipfile.ZipFile(p) as z:
        files=[i for i in z.namelist() if i.endswith('.json') and "_config" not in i]
        assert len(files)==1,files
        d=json.loads(z.read(files[0]))["strategy"]["VideoDoubleMaFuturesStrategy"]
    t=d['trades']
    assert d["total_trades"]==len(t)
    assert all("2025-04-01"<=x["open_date"][:10]<"2026-01-01" for x in t)
    gain=sorted((float(x["profit_abs"]) for x in t if x["profit_abs"]>0),reverse=True)
    net=float(d["profit_total_abs"])
    assert abs(sum(float(x["profit_abs"]) for x in t)-net)<.001
    return {"n":len(t),"net_pct":round(float(d["profit_total"])*100,5),
      "PF":round(float(d["profit_factor"]),5),
      "DD_pct":round(float(d["max_drawdown_account"])*100,5),
      "PnL_USDT":round(net,5),
      "win_pct":round(sum(x["profit_abs"]>0 for x in t)*100/max(1,len(t)),4),
      "long_n":sum(not x["is_short"] for x in t),"short_n":sum(x["is_short"] for x in t),
      "long_USDT":round(sum(x["profit_abs"] for x in t if not x["is_short"]),4),
      "short_USDT":round(sum(x["profit_abs"] for x in t if x["is_short"]),4),
      "top3_fraction_all_wins":round(sum(gain[:3])/sum(gain),5) if gain else None,
      "top3_fraction_NET":round(sum(gain[:3])/net,5) if net>0 else None,
      "mean_trade_h":round(mean(t0["trade_duration"] for t0 in t)/60,3) if t else None,
      "funding_USDT":round(sum(float(x.get("funding_fees",0) or 0) for x in t),4),
      "sha256_native_zip":hashlib.sha256(raw).hexdigest(),
      "first_trade":min((x["open_date"] for x in t),default=None),
      "last_trade":max((x["open_date"] for x in t),default=None)}
def main():
    p=argparse.ArgumentParser();p.add_argument("--root",required=True)
    args=p.parse_args();d=Path(args.root)
    source=json.loads((d/"data/A197_2025_AUTHENTIC_SOURCE_SHA_MANIFEST.json").read_text())
    assert source['original_author_may_2026_IN_SAMPLE'] is True
    assert len(source["counts"])==4
    for sym in (s+"USDT" for s in SYMS):
        z=source["counts"][sym]
        assert z["h1"]==8760 and z["h4"]==2190 and z["daily"]==365
        assert z["mark1h"]==8760
        assert z["funding_settlements"]>700
        assert z["5m"]==79200,(sym,z["5m"])
        assert len(source["sources"][sym])>=48
    outcomes={}
    for s in SYMS:
        outcomes[s]={}
        for fee in FEES:
            v=parse_zip(d/f"2025-{s}-fee{fee}-5m.zip")
            outcomes[s][fee]=v
            print("A197_2025_ALTERNATE_ORIGINAL_NATIVE",s,fee,"N",v["n"],"NET",v["net_pct"],"PF",v["PF"],"DD",v["DD_pct"],"TOP3",v["top3_fraction_all_wins"],flush=True)
    gate={}
    for s in ("ETH","SOL","LINK"):
        v=[outcomes[s][fee] for fee in FEES]
        gate[s]=all(x["n"]>=30 and x["net_pct"]>0 and x["PF"]>=1.25 and x["DD_pct"]<15
                and x["top3_fraction_all_wins"] is not None and x["top3_fraction_all_wins"]<.6 for x in v)
    o={"schema":"EMBER_A197_ALTERNATE_2025_NATIVE_EIGHT_ORIGINAL_5M_DETAIL_RESULTS",
       "source_original_commit":"40af5c7c1c44253766428cfb06babf22f9817aa4",
       "source_original_blob":"22ca6588bbd056e671783f676f1a4010cbfc1bb6",
       "engine":"freqtrade==2026.4",
       "window":"[2025-04-01,2026-01-01)",
       "source_warmup":"[2025-01-01,2025-04-01)",
       "original_author_developed_through_May2026":True,
       "not_genuine_post_publication_OOS":True,
       "costs_per_fill":{"5":.0005,"12p5":.00125},
       "execution":"Native Freqtrade original source with 5m detailed Binance futures OHLC, 1h original signals & 4h context, real mark/funding, fixed synthetic Binance metadata",
       "account":"four separate 10000USDT accounts each 2x near-full stake, NOT shared portfolio nor risk1percent",
       "outcomes":outcomes,"pre_registered_gate":gate,
       "pre_registered_gate_pass_2_of_3":sum(gate.values())>=2,
       "limitations":["Author may have optimized his 2026 strategy using 2025; different regime but not unseen OOS",
          "5m simulation no real orderbook/limit queue, 1m sequence, or added slippage",
          "Original 2x near full equity stake cannot be converted by profit ratio to safe 1% risk without new backtest",
          "Native Freqtrade fee changes callback exit paths; do not interpret increasing fee as edge",
          "Paper only; zero real orders; strategy untouched"]}
    (d/"A197_2025_NATIVE_ALTERNATE_MACHINE.json").write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n")
    print("A197_2025_ALL_EIGHT_EXACT_ORIGINAL_NATIVE_RESULTS_RECEIPTS_VERIFIED",json.dumps(gate),flush=True)
if __name__=="__main__":main()
