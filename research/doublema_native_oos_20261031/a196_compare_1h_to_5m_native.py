#!/usr/bin/env python3
"""A196 compare full original native Freqtrade 2026.4 1h vs 5m detail trade receipts.
Paper only. No 15m adaptation, no strategy parameters altered.
"""
from __future__ import annotations
import json,sys,zipfile,hashlib
from pathlib import Path
from statistics import mean

SYMBOLS=("BTC","ETH","SOL","LINK")
FEES=("5","12p5")
STRATEGY="VideoDoubleMaFuturesStrategy"

def load(p):
    assert p.is_file() and zipfile.is_zipfile(p),("MISSING_REAL_NATIVE_ZIP",str(p))
    with zipfile.ZipFile(p) as z:
        docs=[n for n in z.namelist() if n.endswith(".json") and "_config" not in n]
        assert len(docs)==1,docs
        data=json.loads(z.read(docs[0]))
    return data["strategy"][STRATEGY],hashlib.sha256(p.read_bytes()).hexdigest()

def sumstat(d):
    t=d["trades"]
    assert len(t)==d["total_trades"]
    return {"n":len(t),"return_pct":round(d["profit_total"]*100,5),
     "pnl_usd":round(d["profit_total_abs"],5),
     "PF":round(d["profit_factor"],5),
     "dd_pct":round(d["max_drawdown_account"]*100,5),
     "longs":sum(not x["is_short"] for x in t),
     "shorts":sum(x["is_short"] for x in t),
     "long_pnl":round(sum(x["profit_abs"] for x in t if not x["is_short"]),3),
     "short_pnl":round(sum(x["profit_abs"] for x in t if x["is_short"]),3),
     "top3_of_all_gains":round(sum(sorted((x["profit_abs"] for x in t if x["profit_abs"]>0),reverse=True)[:3])/sum(x["profit_abs"] for x in t if x["profit_abs"]>0),6) if any(x["profit_abs"]>0 for x in t) else None,
     "top3_of_net":round(sum(sorted((x["profit_abs"] for x in t if x["profit_abs"]>0),reverse=True)[:3])/d["profit_total_abs"],6) if d["profit_total_abs"]>0 else None,
     "stop_exit_count":sum(x["exit_reason"] in ("stop_loss","trailing_stop_loss") for x in t),
     "mean_duration_hours":round(mean(x["trade_duration"] for x in t)/60,3) if t else None,
     "sum_funding":round(sum(float(x.get("funding_fees",0) or 0) for x in t),4)}

def chronology(base,detail):
    b={(x["open_timestamp"],x["is_short"]):x for x in base}
    d={(x["open_timestamp"],x["is_short"]):x for x in detail}
    overlap=set(b)&set(d)
    exits=[{"entry":str(k[0]),"direction":"SHORT" if k[1] else "LONG",
       "old_close":b[k]["close_date"],"detail_close":d[k]["close_date"],
       "old_exit_reason":b[k]["exit_reason"],"detail_exit_reason":d[k]["exit_reason"],
       "old_pnl_usdt":round(b[k]["profit_abs"],4),"detail_pnl_usdt":round(d[k]["profit_abs"],4)}
       for k in sorted(overlap) if b[k]["close_timestamp"]!=d[k]["close_timestamp"]
       or b[k]["exit_reason"]!=d[k]["exit_reason"]]
    return {"matched_entry_timestamps":len(overlap),
            "baseline_exclusive":len(set(b)-set(d)),
            "5m_exclusive":len(set(d)-set(b)),
            "changed_exit_count":len(exits),"changed_exit_receipts":exits}

def main():
    root=Path(sys.argv[1]);base_dir=Path(sys.argv[2])
    oldfile=base_dir/"A195_ORIGINAL_NATIVE_CROSSPAIR_RESULTS.json"
    assert oldfile.is_file()
    old=json.loads(oldfile.read_text())
    manifest=json.loads((root/"data/A196_REAL_5M_SHA_MANIFEST.json").read_text())
    assert len(manifest["symbols"])==4
    outcomes={};receipts={}
    for sym in SYMBOLS:
        item=manifest["symbols"][sym+"USDT"]
        assert item["candles"]>40000
        assert len(item["sources"])==5
        assert all(len(z["zip_sha256"])==64 for z in item["sources"].values())
        outcomes[sym]={};receipts[sym]={}
        for f in FEES:
            n,ns=load(root/f"5m-detail-{sym}-fee{f}.zip")
            o,os=load(base_dir/f"native-{sym}-fee{f}.zip")
            expected=old["outcomes"][sym][f]
            baseline=sumstat(o);detail=sumstat(n)
            assert baseline["n"]==expected["n"],(sym,f,"BASE_N")
            assert abs(baseline["pnl_usd"]-expected["profit_usd"])<0.001,(sym,f,"BASE_PNL")
            assert abs(baseline["return_pct"]-expected["return_pct"])<0.0001
            changes=chronology(o["trades"],n["trades"])
            outcomes[sym][f]={"one_hour":baseline,"five_minute":detail,"diff":changes,
              "detail_to_baseline_gain_ratio":round(detail["return_pct"]/baseline["return_pct"],5) if baseline["return_pct"]>0 else None,
              "source_baseline_zip_sha256":os,"source_detail_zip_sha256":ns}
            receipts[f"{sym}-{f}"]={"baseN":baseline["n"],"detailN":detail["n"],"changed_exits":changes["changed_exit_count"],"baseReturn":baseline["return_pct"],"detailReturn":detail["return_pct"]}
            print("A196_NATIVE_5M_COMPARE",sym,f,"N",baseline["n"],detail["n"],
                 "NET_PCT",baseline["return_pct"],detail["return_pct"],
                 "PF",baseline["PF"],detail["PF"],
                 "DD",baseline["dd_pct"],detail["dd_pct"],
                 "CHANGED_EXITS",changes["changed_exit_count"],flush=True)
    gate={}
    for sym in ("ETH","SOL","LINK"):
        scenarios=[outcomes[sym][f] for f in FEES]
        gate[sym]=bool(all((z["five_minute"]["n"]>=20 and z["five_minute"]["return_pct"]>0 and
             z["five_minute"]["PF"]>=1.25 and z["five_minute"]["dd_pct"]<15 and
             z["detail_to_baseline_gain_ratio"] is not None and z["detail_to_baseline_gain_ratio"]>=0.7 and
             z["five_minute"]["top3_of_all_gains"] is not None and z["five_minute"]["top3_of_all_gains"]<0.6)
             for z in scenarios))
    m={"schema":"EMBER_A196_ORIGINAL_DOUBLEMA_1H_VS_5M_DETAIL_NATIVE",
       "source_strategy_commit":"40af5c7c1c44253766428cfb06babf22f9817aa4",
       "source_blob":"22ca6588bbd056e671783f676f1a4010cbfc1bb6",
       "freqtrade":"2026.4","window":"[2026-05-13,2026-10-01)",
       "base_source_run":41147367668,"fee_labels":{"5":0.0005,"12p5":0.00125},
       "5m_data_source":"real Binance Vision USD-M 5m July-Sep + May/June, no interpolation, SHA in manifest",
       "outcomes":outcomes,"frozen_gate_per_coin":gate,"frozen_gate_at_least_2_of_3":sum(gate.values())>=2,
       "limitations":["5m candles do not reveal intra-5m order path","limit fills approximated by Freqtrade no orderbook","NO explicit extra slippage added","full Freqtrade lookahead-analysis and recursive-analysis NOT performed","original near-full stake 2x exposure not 1pct-equity risk sizing","one regime not future prospective OOS","no real or simulated PAPER orders opened"]}
    (root/"A196_5M_NATIVE_DETAIL_COMPARISON.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n")
    print("A196_EIGHT_NATIVE_SOURCE_EXECUTION_COMPARISONS_COMPLETED",flush=True)
    print(json.dumps({"gate":gate,"summaries":receipts},indent=2),flush=True)
if __name__=="__main__":main()
