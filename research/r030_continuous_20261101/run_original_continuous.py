"""R030 original Freqtrade 2026.9 one-wallet continuous account 2023-06 to 2026-06.

Never resets wallet or closes positions in 2023/2024/2025. Native strategy
unmodified. Full .zip trade/order ledgers are retained as CI artifacts.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from research.a245_other_originals.a245_run import config_for_run

OUT=Path(__file__).resolve().parent/"generated"
BLOB="15ce2473f3f60bd33c4a67b0b8b228e379850f19"
PERIOD="20230601-20260601"
FEES={"BASE":0.0005,"STRESS":0.0011}


def git_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()


def read_native_result(directory:Path)->tuple[dict,str]:
    for zpath in sorted(directory.glob("*.zip"),reverse=True):
        with zipfile.ZipFile(zpath) as z:
            for member in z.namelist():
                if not member.endswith(".json") or ".meta." in member:
                    continue
                try:
                    obj=json.loads(z.read(member))
                except (ValueError,UnicodeDecodeError):
                    continue
                if "strategy" in obj and "VolatilitySystem" in obj["strategy"]:
                    return obj,str(zpath)+":"+member
    raise ValueError("native original strategy result export missing")


def parse_time(value):
    if not value:
        return None
    if isinstance(value,(int,float)):
        return datetime.fromtimestamp(float(value),timezone.utc)
    try:
        dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def report_from_original(obj,filename,mode,fee):
    source=obj["strategy"]["VolatilitySystem"]
    trades=source.get("trades")
    expected=source.get("total_trades")
    if not isinstance(trades,list) or expected is None or len(trades)!=expected:
        raise ValueError(f"native full trade records missing {len(trades or [])}/{expected}")
    sumprofit=float(source["profit_total_abs"])
    exit_summary=source.get("exit_reason_summary")
    if not isinstance(exit_summary,list):
        raise ValueError("native exit reason breakdown missing")
    itemized={}
    for e in exit_summary:
        key=e.get("key")
        if key and key!="TOTAL":
            itemized[key]={"count":int(e["trades"]),
                           "pnl_abs_usdt":float(e["profit_total_abs"])}
    if sum(x["count"] for x in itemized.values())!=expected:
        raise ValueError("native exit count does not reconcile")
    if abs(sum(x["pnl_abs_usdt"] for x in itemized.values())-sumprofit)>.1:
        raise ValueError("native exit PnL does not reconcile")
    boundaries=(datetime(2023,12,31,tzinfo=timezone.utc),
                datetime(2024,12,31,tzinfo=timezone.utc),
                datetime(2025,12,31,tzinfo=timezone.utc))
    crossed={b.year:0 for b in boundaries}
    per_close_year={}
    with_orders=0
    missing_orders=0
    abnormal_leverage=[]
    force_dates=[]
    max_profit_trade=None
    for t in trades:
        if not isinstance(t,dict):
            raise ValueError("trade not structured dict")
        start=parse_time(t.get("open_date"))
        end=parse_time(t.get("close_date"))
        if start is None or end is None:
            raise ValueError("native trade open/close date missing")
        for b in boundaries:
            if start<=b<end:
                crossed[b.year]+=1
        reason=t.get("exit_reason")
        if reason=="force_exit":
            force_dates.append(str(t.get("close_date")))
            if end<datetime(2026,5,30,tzinfo=timezone.utc):
                raise ValueError("FORCED_EXIT_INSIDE_CONTINUOUS_ACCOUNT")
        profit=t.get("profit_abs")
        if not isinstance(profit,(int,float)):
            raise ValueError("native trade profit_abs not numeric")
        stat=per_close_year.setdefault(str(end.year),{"n":0,"pnl_abs_usdt":0.0})
        stat["n"]+=1
        stat["pnl_abs_usdt"]+=float(profit)
        if max_profit_trade is None or float(profit)>float(max_profit_trade["profit_abs"]):
            max_profit_trade={"open_date":t.get("open_date"),
                              "close_date":t.get("close_date"),
                              "pair":t.get("pair"),"profit_abs":profit,
                              "exit_reason":reason}
        lev=t.get("leverage")
        if not isinstance(lev,(int,float)) or abs(float(lev)-2.)>1e-5:
            abnormal_leverage.append({"date":t.get("open_date"),"value":lev})
        orders=t.get("orders")
        if isinstance(orders,list) and orders:with_orders+=1
        else:missing_orders+=1
    if missing_orders:
        raise ValueError(f"native orders missing for {missing_orders} trades")
    force=itemized.get("force_exit",{"count":0,"pnl_abs_usdt":0.})
    result={
        "status":"NATIVE_CONTINUOUS_RESEARCH_ONLY_NOT_VERIFIED_LIQUIDATION",
        "original_source_sha":BLOB,"native_result":filename,
        "native_strategy":"VolatilitySystem","version":"Freqtrade 2026.9",
        "period_inclusive_utc":"2023-06-01..2026-05-31",
        "no_annual_wallet_reset":True,
        "fee_model":mode,"fee_each_side":fee,
        "original_source_stoploss":-1.0,
        "original_leverage":2.,
        "wallet_start_usdt":1000,
        "same_controlled_wallet_2023_2026":True,
        "net_account_pnl_usdt":sumprofit,
        "net_account_return_pct":sumprofit/10.,
        "account_max_drawdown":source.get("max_drawdown_account"),
        "account_max_drawdown_abs_usdt":source.get("max_drawdown_abs"),
        "profit_factor":source.get("profit_factor"),
        "trade_count":expected,
        "wins":source.get("wins"),"losses":source.get("losses"),
        "exit_reasons":itemized,
        "only_final_end_force_exit_count":force["count"],
        "only_final_end_force_exit_pnl_usdt":force["pnl_abs_usdt"],
        "non_terminal_exits_pnl_usdt":sumprofit-force["pnl_abs_usdt"],
        "end_force_close_dates":force_dates,
        "positions_open_across_dec31_2023_2024_2025":crossed,
        "pnl_by_close_year_including_fees_and_funding":
            {k:{"n":v["n"],"pnl_abs_usdt":round(v["pnl_abs_usdt"],7)}
             for k,v in per_close_year.items()},
        "native_trades_with_original_order_list":with_orders,
        "native_trades_without_original_order_list":missing_orders,
        "any_nonoriginal_2x_trades":abnormal_leverage,
        "largest_profit_trade":max_profit_trade,
        "native_funding_genuine_from_binance_vision":True,
        "source_limit":"Historical mark source 8h does not prove actual stop/liquidation intrabar; "
                       "maintenance tier and L2 fills/order-book queue not recreated. "
                       "Positive native returns are not deployable edge, not a new OOS.",
    }
    return result


def main():
    source=OUT/"strategies/VolatilitySystem.py"
    if git_sha(source.read_bytes())!=BLOB:
        raise ValueError("pinned original drift")
    if not (OUT/"R030_CONTINUOUS_SOURCE_SHA_RECEIPTS.json").is_file():
        raise ValueError("missing original 333 archive receipts")
    cfg=config_for_run()
    cfg["user_data_dir"]=str(OUT)
    config=OUT/"R030_NATIVE_SINGLE_ACCOUNT_CONFIG.json"
    config.write_text(json.dumps(cfg,indent=2)+"\n",encoding="utf-8")
    outputs={}
    results=OUT/"continuous_backtests"
    results.mkdir(exist_ok=True)
    for mode,fee in FEES.items():
        folder=results/mode
        folder.mkdir(exist_ok=True)
        cmd=[
            sys.executable,"-m","freqtrade","backtesting",
            "--config",str(config),
            "--datadir",str(OUT/"binance"),
            "--strategy-path",str(OUT/"strategies"),
            "--strategy","VolatilitySystem",
            "--timeframe","1h","--timeframe-detail","5m",
            "--timerange",PERIOD,
            "--fee",str(fee),"--max-open-trades","3",
            "--export","trades","--backtest-directory",str(folder),"--cache","none",
        ]
        print("R030_CONTINUOUS_NATIVE_START",mode,PERIOD,flush=True)
        try:
            cp=subprocess.run(cmd,capture_output=True,text=True,timeout=1600,
                              env={**os.environ,"PYTHONUNBUFFERED":"1"})
            combined=cp.stdout+"\n"+cp.stderr
            (folder/"native_original_freqtrade.log").write_text(
                combined[-350000:],encoding="utf-8")
            if cp.returncode:
                outputs[mode]={"status":"BLOCKED_NATIVE_RUNTIME","return_code":cp.returncode,
                               "tail":combined.splitlines()[-35:]}
            else:
                raw,filename=read_native_result(folder)
                outputs[mode]=report_from_original(raw,filename,mode,fee)
        except (ValueError,KeyError,TypeError,subprocess.TimeoutExpired) as exc:
            outputs[mode]={"status":"BLOCKED_EVIDENCE_OR_RUNTIME",
                           "error":repr(exc)}
        print("R030_CONTINUOUS_NATIVE_RESULT",mode,json.dumps(outputs[mode],
              ensure_ascii=False,sort_keys=True),flush=True)
        (OUT/"R030_CONTINUOUS_NATIVE_FINAL_RESULTS.json").write_text(
            json.dumps(outputs,indent=2,ensure_ascii=False,sort_keys=True)+"\n",
            encoding="utf-8",
        )
    if any(x["status"].startswith("BLOCKED") for x in outputs.values()):
        raise SystemExit("CONTINUOUS R030 BLOCKED, not a loss nor profit")
    print("R030_CONTINUOUS_DONE",json.dumps({
        k:{"account_net_pct":v["net_account_return_pct"],
           "trades":v["trade_count"],
           "terminal_forced_pnl_usdt":v["only_final_end_force_exit_pnl_usdt"],
           "ordinary_pnl_usdt":v["non_terminal_exits_pnl_usdt"]}
        for k,v in outputs.items()}),flush=True)


if __name__=="__main__":
    main()
