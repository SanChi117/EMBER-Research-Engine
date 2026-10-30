#!/usr/bin/env python3
"""Independent immutable native Freqtrade double run verification (stdlib).
DO NOT execute archived third-party Python. Read only the nested JSON receipts.
"""
import hashlib
import io
import json
from pathlib import Path
import sys
from zipfile import ZipFile

STRATEGY="VideoDoubleMaFuturesStrategy"

def parse_native(path):
    raw=Path(path).read_bytes()
    with ZipFile(io.BytesIO(raw)) as z:
        matched=[f for f in z.namelist() if f.endswith(".json") and "_config" not in f]
        if len(matched)!=1:
            raise AssertionError(f"WRONG_OR_MISSING_NATIVE_RESULTS_JSON:{path}:{matched}")
        body=json.loads(z.read(matched[0]))
    assert list(body["strategy"])==[STRATEGY]
    x=body["strategy"][STRATEGY]
    assert x["total_trades"]==len(x["trades"])==27
    return x,hashlib.sha256(raw).hexdigest()

def metrics_fixed_exits(trades,bps):
    delta=(bps-10)/20000
    vals=[x["profit_abs"]-delta*x["amount"]*(x["open_rate"]+x["close_rate"]) for x in trades]
    profit=sum(v for v in vals if v>0)
    loss=-sum(v for v in vals if v<0)
    return {"return_pct_initial_10k":round(sum(vals)/100,6),
            "profit_factor":round(profit/loss,6) if loss else None,
            "winning_trades":sum(v>0 for v in vals)}

def inspect(remote_path,offline_path):
    a,sha_a=parse_native(remote_path)
    b,sha_b=parse_native(offline_path)
    for xa,xb in zip(a["trades"],b["trades"]):
        assert xa["open_timestamp"]==xb["open_timestamp"]
        assert xa["close_timestamp"]==xb["close_timestamp"]
        assert xa["is_short"]==xb["is_short"]
        assert abs(xa["profit_abs"]-xb["profit_abs"])<1e-6
        assert xa["exit_reason"]==xb["exit_reason"]
    assert abs(a["profit_total_abs"]-b["profit_total_abs"])<1e-6
    return a,{"remote_native_zip_sha256":sha_a,"offline_native_zip_sha256":sha_b,
              "exactly_reproduced_trade_count":len(a["trades"])}

def main(root_original,root_offline,output):
    r=Path(root_original);o=Path(root_offline)
    a,pr=inspect(r/"doublema-native-fee5bps-side.zip",o/"dma-fee5bps-side.zip")
    b,pq=inspect(r/"doublema-native-fee12p5bps-side.zip",o/"dma-fee12p5bps-side.zip")
    assert abs(a["profit_total_abs"]-3986.42174889)<1e-4
    assert abs(b["profit_total_abs"]-4337.97113124)<1e-4
    assert 2.23 < a["profit_factor"] < 2.25
    assert 2.17 < b["profit_factor"] < 2.18
    assert a["max_drawdown_account"]<0.075
    assert 0.08 < b["max_drawdown_account"] < 0.083
    assert a["trade_count_long"]==14 and a["trade_count_short"]==13
    assert a["backtest_start"]==b["backtest_start"]
    assert a["backtest_end"]==b["backtest_end"]
    opens=sum(t["open_timestamp"]==u["open_timestamp"] and t["is_short"]==u["is_short"] for t,u in zip(a["trades"],b["trades"]))
    exits=sum(t["close_timestamp"]==u["close_timestamp"] for t,u in zip(a["trades"],b["trades"]))
    differences=[
       {"open":t["open_date"],"low_fee_close":t["close_date"],
        "high_fee_close":u["close_date"],"low_fee_exit":t["exit_reason"],
        "high_fee_exit":u["exit_reason"],
        "low_fee_profit":round(t["profit_abs"],2),"high_fee_profit":round(u["profit_abs"],2)}
       for t,u in zip(a["trades"],b["trades"])
       if t["close_timestamp"]!=u["close_timestamp"]
    ]
    assert opens==27 and exits==26 and len(differences)==1
    assert differences[0]["open"].startswith("2026-07-10 06:00")
    fixed={str(x):metrics_fixed_exits(a["trades"],x) for x in (10,25,40,60)}
    assert 31.76 < fixed["25"]["return_pct_initial_10k"] < 31.79
    assert 23.67 < fixed["40"]["return_pct_initial_10k"] < 23.70
    out={
      "schema":"EMBER_DOUBLEMA_EXACT_NATIVE_VALIDATION_R01",
      "source_upstream_commit":"40af5c7c1c44253766428cfb06babf22f9817aa4",
      "source_strategy_blob":"22ca6588bbd056e671783f676f1a4010cbfc1bb6",
      "engine":"Freqtrade==2026.4",
      "market":"Binance USD-M ETHUSDT original historical prices via OKX data adapter",
      "validation_window":"[2026-05-13,2026-10-30) UTC",
      "remote_CI_run":41138713727,
      "offline_metadata_CI_run":41139485118,
      "primary":{"n":a["total_trades"],"profit_pct":round(a["profit_total"]*100,6),
                 "profit_factor":round(a["profit_factor"],6),
                 "max_account_dd_pct":round(a["max_drawdown_account"]*100,6),
                 "fees_per_side":0.0005,**pr},
      "higher_fee":{"n":b["total_trades"],"profit_pct":round(b["profit_total"]*100,6),
                    "profit_factor":round(b["profit_factor"],6),
                    "max_account_dd_pct":round(b["max_drawdown_account"]*100,6),
                    "fees_per_side":0.00125,**pq},
      "cost_policy_fixed_exits_overlay_bps_roundtrip":fixed,
      "entry_times_same_across_fee_runs":opens,
      "exit_times_same_across_fee_runs":exits,
      "exit_path_difference":differences,
      "outcome":"PRELIMINARY_POSITIVE_NO_POWER_AND_EXIT_SENSITIVITY_NOT_APPROVED_FOR_LIVE",
      "limitations":["Only 27 trades, less than prereg 30 threshold",
                     "Known source posted May12 and tested May13-Oct29; not lookahead/recursive-analysis certified",
                     "Historical Binance candles and funding with OKX metadata used; not executable bid/ask proof",
                     "No maker limit order queue / gap fill independent verification",
                     "No causal claim that higher fees improve returns; one exit diverged"] }
    Path(output).write_text(json.dumps(out,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("EXACT_NATIVE_REMOTE_AND_OFFLINE_27_OF_27_REPRODUCIBLE")
    print(json.dumps({"primary":out["primary"],"higher_fee":out["higher_fee"],
                      "matched_exit_count":exits,"divergence":differences,
                      "fixed_exit_cost25":fixed["25"],"fixed_exit_cost40":fixed["40"]},
                      ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: python verifier.py extracted_remote extracted_offline report.json")
    main(sys.argv[1],sys.argv[2],sys.argv[3])
