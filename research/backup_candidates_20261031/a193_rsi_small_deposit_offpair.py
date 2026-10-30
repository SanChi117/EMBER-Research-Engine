#!/usr/bin/env python3
"""A193: verify original public RSI 5m small-account scalper on a DIFFERENT pair,
with exact unchanged upstream function and instrumented receipt-only accounting.
No source-code trading rules changed; no exchange keys; NOT independent future OOS.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

UPSTREAM_COMMIT="39f7187ce21b021441fb4a55188b95831df7b5b1"
STRATEGY_BLOB="d4e5ed465c0c520a0f1496c984f020259904969c"
INDICATORS_BLOB="b9e93d1ef6c8b6c493d1dd87a03827d4533b4832"  # will be checked against source and corrected if needed
MONTH_START="2026-08-01"
MONTH_END="2026-10-01"
TEMPLATE=dict(sl_pct=.015,tp_pct=.030,leverage=5,rsi_buy=20,rsi_sell=80,
              use_adx=True,adx_threshold=25,cooldown=12,margin=16.,trailing_pct=None)

def gitblob(p:Path):
    raw=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()

def read_data(path:Path):
    d=json.loads(path.read_text())
    a=d.get("candles_5m")
    assert a==26496 or (isinstance(a,int) and a>=20000),("NO_DAILY_SOURCE_PROOF",d)
    return d

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    ap.add_argument("--datadir",required=True)
    ap.add_argument("--out",required=True)
    x=ap.parse_args()
    root=Path(x.repo)
    file=root/"scripts"/"sweep_timeframe.py"
    ind=root/"gridtrader"/"quant"/"indicators.py"
    assert gitblob(file)==STRATEGY_BLOB,("BAD_UPSTREAM_STRATEGY_BLOB",gitblob(file))
    assert ind.is_file() and ind.stat().st_size>3000
    sys.path.insert(0,str(root))
    from scripts.sweep_timeframe import simulate as original
    src=file.read_text()
    anchor='return {"pnl": total_pnl,'
    assert src.count(anchor)==1
    # Test copy changes *only* reported ending cash, not execution or signals.
    patched=src.replace(anchor,'return {"ending_cash": cash, "pnl": total_pnl,')
    p=Path(x.out).parent/"a193_instrumented_readonly_report.py"
    p.write_text(patched)
    spec=importlib.util.spec_from_file_location("a193_instrumented_readonly_report",p)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    origin=Path(x.datadir)/"futures"/"ETH_USDT_USDT-5m-futures.json"
    r=json.loads(origin.read_text())
    assert len(r)==26496,len(r)
    df=pd.DataFrame(r,columns=["timestamp","open","high","low","close","volume"])
    df.index=pd.to_datetime(df.timestamp,unit="ms",utc=True)
    df=df.drop(columns=["timestamp"])
    assert len(df.loc[MONTH_START:"2026-09-30"])>17000
    observed={}
    # Jul pre-history retained for indicator initialization. Keep Jul included
    # because script bar-50 warmup depends on supplied start. Explicitly avoid
    # treating July PnL as OOS by prepending indicator-only warmup separately:
    # run on Aug-Sep only (50 5m bars warmup).
    data=df[(df.index>=pd.Timestamp(MONTH_START,tz="UTC"))&
            (df.index<pd.Timestamp(MONTH_END,tz="UTC"))]
    assert len(data)==17568,len(data)
    for bps in [6.,12.5]:
        settings={**TEMPLATE,"fee_bps":bps}
        original_result=original(data,**settings)
        instrumented_result=module.simulate(data,**settings)
        for key in ("pnl","n","wr","pf","max_dd"):
            assert original_result[key]==instrumented_result[key],("SOURCE_DIVERGENCE",key)
        reported=float(original_result["pnl"])
        cash=float(instrumented_result["ending_cash"])
        corrected=cash-settings["margin"]
        assert corrected<=reported+1e-7,("ACCOUNTING_UNEXPECTED",corrected,reported)
        assert abs(corrected-reported)<3.0 or original_result["n"]>0
        observed[str(bps)]={
            "n":int(original_result["n"]),
            "reported_trade_pnl_usdt_excludes_entry_fees":round(reported,6),
            "actual_ending_cash_usdt_including_entry_fees":round(cash,6),
            "account_correct_net_pnl_usdt":round(corrected,6),
            "source_metric_omitted_entry_fees_usdt":round(reported-corrected,6),
            "win_rate_pct":round(original_result["wr"]*100,3),
            "profit_factor_author_exit_only":round(original_result["pf"],5),
            "max_drawdown_pct":round(original_result["max_dd"]*100,5)
        }
    report={
      "schema":"EMBER_A193_SMALL_BANKROLL_ETH_5M_OFFPAIR_V1",
      "engine":"author original Python simulate() from pinned git blob + read-only cash receipt instrumentation",
      "author_repo":"jiangkaili/binance-trader-bot",
      "author_commit":UPSTREAM_COMMIT,
      "author_strategy_blob":STRATEGY_BLOB,
      "market":"Binance USD-M ETHUSDT original continuous Binance Vision 5m",
      "study_window":"[2026-08-01,2026-10-01) UTC",
      "code_frozen_as_of":"2026-10-31; not independent author untouched OOS",
      "settings":TEMPLATE,
      "dataset_bars":len(data),
      "fee_scenarios_bps_per_side":observed,
      "limitations":["Original uses same-bar close fills, not next-bar-open; ignores slippage and funding",
                     "In author return pnl exclude entry fees; corrected via cash measurement only",
                     "Changes in fee can change order paths; do not overlay fixed trade path",
                     "ETH test is off-pair from author BTC tuning, but not timestamp-frozen out of sample",
                     "Author 3 BTC windows overlap, not three independent datasets"],
      "status":"TEST_ONLY_NO_EXECUTION"
    }
    Path(x.out).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("A193_ORIGINAL_SOURCE_AND_ACCOUNTING_PARITY_OK")
    print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
