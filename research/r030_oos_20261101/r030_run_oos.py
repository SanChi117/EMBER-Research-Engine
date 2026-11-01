"""Run original pinned R030 VolatilitySystem without changing entry or exit logic.

Identical controlled A245 wallet/pairs/costs; NEW previously unseen 2026-06
to 2026-10 Futures holdout. Original signals, 2x leverage, DCA and 100%
source stop intact. Every blocked scenario is recorded, not converted to zero.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

from research.a245_other_originals.a245_run import config_for_run

ROOT=Path(__file__).resolve().parents[2]
DIR=ROOT/"research/r030_oos_20261101"
OUT=DIR/"generated"
SOURCE=OUT/"strategies/VolatilitySystem.py"
BLOB="15ce2473f3f60bd33c4a67b0b8b228e379850f19"


def git_blob(raw: bytes)->str:
    return hashlib.sha1(
        b"blob "+str(len(raw)).encode()+b"\x00"+raw
    ).hexdigest()


def result_json(root: Path) -> tuple[dict,str]:
    for path in sorted(root.glob("*.zip"),key=lambda x:x.stat().st_mtime,reverse=True):
        with zipfile.ZipFile(path) as z:
            files=[x for x in z.namelist()
                   if x.endswith(".json") and ".meta." not in x]
            for file in files:
                try:
                    o=json.loads(z.read(file))
                except (ValueError,UnicodeDecodeError):
                    continue
                if isinstance(o,dict) and "strategy" in o:
                    return o,str(path)+":"+file
    for path in sorted(root.glob("*.json"),key=lambda x:x.stat().st_mtime,reverse=True):
        data=json.loads(path.read_text("utf-8"))
        if isinstance(data,dict) and "strategy" in data:
            return data,str(path)
    raise ValueError("no native Freqtrade strategy result JSON")


def trades_of(data: dict) -> list[dict]:
    s=data["strategy"]["VolatilitySystem"]
    # Native Freqtrade exports the actual order/position data in the strategy
    # result's trades list. Do not infer fills if field is absent.
    raw=s.get("trades",[])
    if not isinstance(raw,list):
        raise ValueError("native Freqtrade trades missing as structured list")
    return raw


def summarize(data:dict,source:str,fee:float) -> dict:
    s=data["strategy"]["VolatilitySystem"]
    trades=trades_of(data)
    declared=s.get("total_trades")
    if declared is None or len(trades)!=int(declared):
        raise ValueError(
            f"full native trade evidence missing: summary={declared}, records={len(trades)}"
        )
    levers=[t.get("leverage") for t in trades]
    fills=[t.get("orders") for t in trades]
    result={
        "status":"NATIVE_2026_JUN_OCT_OOS_COMPLETED_UNVERIFIED_LIQUIDATION",
        "period":"2026-06-01 UTC to 2026-11-01 UTC",
        "source_pin_blob":BLOB,
        "native_data_source":source,
        "strategy":"VolatilitySystem",
        "timeframe":"1h",
        "intrabar_detail":"5m genuine Binance USD-M",
        "fee_each_side":fee,
        "starting_wallet":1000,"stake":100,"max_open_trades":3,
        "native_trade_count":declared,
        "native_after_fee_return_pct":100*float(s["profit_total_abs"])/1000,
        "native_after_fee_profit_abs_usdt":float(s["profit_total_abs"]),
        "native_max_drawdown_account":s.get("max_drawdown_account"),
        "native_max_drawdown_abs":s.get("max_drawdown_abs"),
        "native_profit_factor":s.get("profit_factor"),
        "native_win_count":s.get("wins"),
        "native_loss_count":s.get("losses"),
        "native_exit_reason_summary":s.get("exit_reason_summary"),
        "native_rejected_signals":s.get("rejected_signals"),
        "full_trade_count":len(trades),
        "declared_leverage_values":sorted({str(x) for x in levers}),
        "trades_with_order_details":sum(isinstance(x,list) and bool(x) for x in fills),
        "trades_missing_order_details":sum(not isinstance(x,list) or not x for x in fills),
        "all_original_source_stops":"stoploss=-1, futures 2x, max2 fills",
        "proof_limit":"Native Freqtrade backtest includes real 8H mark/funding inputs "
                      "but no audited official live maintenance margin tiers, "
                      "mark intrabar liquidation order path, L2 spreads, queue or fill slippage.",
    }
    return result


def main()->None:
    if git_blob(SOURCE.read_bytes())!=BLOB:
        raise ValueError("original source bytes changed")
    if not (OUT/"R030_OOS_SOURCE_RECEIPTS.json").exists():
        raise ValueError("unverified original source market receipts")
    results=OUT/"backtests"
    results.mkdir(parents=True,exist_ok=True)
    cfg=config_for_run()
    cfg["user_data_dir"]=str(OUT)
    config=OUT/"r030_same_controlled_wallet_config.json"
    config.write_text(json.dumps(cfg,indent=2)+"\n",encoding="utf-8")
    status={}
    for mode,fee in (("BASE",0.0005),("STRESS",0.0011)):
        dest=results/mode
        dest.mkdir(exist_ok=True)
        command=[
            sys.executable,"-m","freqtrade","backtesting",
            "--config",str(config),
            "--datadir",str(OUT/"binance"),
            "--strategy-path",str(OUT/"strategies"),
            "--strategy","VolatilitySystem",
            "--timeframe","1h","--timeframe-detail","5m",
            "--timerange","20260601-20261101",
            "--fee",str(fee),"--max-open-trades","3",
            "--export","trades","--backtest-directory",str(dest),"--cache","none",
        ]
        print("R030_INDEPENDENT_OOS_NATIVE_START",mode,flush=True)
        cp=subprocess.run(command,capture_output=True,text=True,timeout=900,
                          env={**os.environ,"PYTHONUNBUFFERED":"1"})
        (dest/"native_freqtrade.log").write_text(
            (cp.stdout+"\n"+cp.stderr)[-300000:],encoding="utf-8"
        )
        if cp.returncode:
            status[mode]={
                "status":"BLOCKED_NATIVE_RUNTIME",
                "returncode":cp.returncode,
                "tail":(cp.stdout+"\n"+cp.stderr).splitlines()[-35:],
            }
            print("R030_OOS_BLOCKED",mode,json.dumps(status[mode]),flush=True)
            continue
        try:
            raw,where=result_json(dest)
            status[mode]=summarize(raw,where,fee)
        except (ValueError,KeyError,TypeError) as exc:
            status[mode]={"status":"BLOCKED_INCOMPLETE_NATIVE_EVIDENCE",
                          "error":repr(exc)}
        print("R030_OOS_RESULT",mode,json.dumps(status[mode],sort_keys=True),flush=True)
    (OUT/"R030_OOS_NATIVE_RESULTS.json").write_text(
        json.dumps(status,indent=2,sort_keys=True)+"\n",encoding="utf-8"
    )
    if any(v["status"].startswith("BLOCKED") for v in status.values()):
        raise SystemExit("R030_OOS_NATIVE_RUN_BLOCKED")


if __name__=="__main__":
    main()
