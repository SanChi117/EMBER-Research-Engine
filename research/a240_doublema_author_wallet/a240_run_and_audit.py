"""A240 native shared-wallet original Double MA BTC/ETH, after-cost accounting.
No signal code changed. Creates explicit BLOCKED receipts on every failure.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

EXPECTED_ORIGINAL="40af5c7c1c44253766428cfb06babf22f9817aa4"
EXPECTED_SOURCE_BLOB="22ca6588bbd056e671783f676f1a4010cbfc1bb6"
EXPECTED_CONFIG_BLOB="b16e6695673c58d8b7a712fd329994b3a85313f4"
PAIRS=["BTC/USDT:USDT","ETH/USDT:USDT"]
PERIODS={"2025":"20250401-20260101","2026":"20260513-20261001"}
FEES={"base":0.0005,"stress":0.00125}

def blob_hash(payload: bytes):
    return hashlib.sha1(b"blob "+str(len(payload)).encode()+b"\x00"+payload).hexdigest()

def author_config(root:Path, result_dir:Path):
    src=root/"user_data/strategies/VideoDoubleMaFuturesStrategy.py"
    conf=root/"config/config_binance_futures.json"
    sb=blob_hash(src.read_bytes())
    cb=blob_hash(conf.read_bytes())
    assert sb==EXPECTED_SOURCE_BLOB,(sb,"ORIGINAL_STRATEGY_DRIFT")
    assert cb==EXPECTED_CONFIG_BLOB,(cb,"ORIGINAL_CONFIG_DRIFT")
    c=json.loads(conf.read_text("utf8"))
    assert c["exchange"]["name"]=="binance"
    assert c["exchange"]["pair_whitelist"]==PAIRS
    assert c["trading_mode"]=="futures" and c["margin_mode"]=="isolated"
    assert c["dry_run_wallet"]==10000 and c["stake_amount"]=="unlimited"
    assert c["max_open_trades"]==1 and c["tradable_balance_ratio"]==1
    assert c["timeframe"]=="1h" and c["order_types"]["stoploss_on_exchange"] is False
    assert c["entry_pricing"]["price_side"]=="other"
    assert c["exit_pricing"]["price_side"]=="other"
    # STRICTLY operational offline only, no leverage/ROI/stop/entry/signal modifications.
    c["exchange"]["ccxt_config"]={}
    c["exchange"]["ccxt_async_config"]={}
    for k in ("key","secret","password"):
        c["exchange"][k]=""
    if isinstance(c.get("telegram"),dict): c["telegram"]["enabled"]=False
    if isinstance(c.get("api_server"),dict): c["api_server"]["enabled"]=False
    c["dry_run"]=True
    c["bot_name"]="EMBER_A240_DOUBLEMA_ORIGINAL_RESEARCH_NO_ORDERS"
    output=result_dir/"a240_original_binance_author_onewallet_config.json"
    output.write_text(json.dumps(c,ensure_ascii=False,indent=2)+"\n","utf8")
    return output,{"source_git_blob":sb,"config_git_blob":cb}

def parse_native(path:Path):
    with zipfile.ZipFile(path) as z:
        keys=[]
        for file in z.namelist():
            if not file.endswith(".json") or ".meta." in file: continue
            try: data=json.loads(z.read(file))
            except (ValueError,UnicodeDecodeError):continue
            if isinstance(data,dict) and "strategy" in data and "VideoDoubleMaFuturesStrategy" in data["strategy"]:
                keys.append((file,data))
        assert len(keys)==1,("A240_NATIVE_ARCHIVE_LAYOUT_NOT_UNIQUE",len(keys),str(path))
        filename,data=keys[0]
        model=data["strategy"]["VideoDoubleMaFuturesStrategy"]
    trades=model["trades"]
    assert model["starting_balance"]==10000,("A240_WALLET_CHANGED",model["starting_balance"])
    assert model.get("timeframe_detail")=="5m"
    assert model["trading_mode"]=="futures" and model["margin_mode"]=="isolated"
    assert len(trades)==model["total_trades"]
    profit=sum(float(x["profit_abs"]) for x in trades)
    assert math.isclose(profit,float(model["profit_total_abs"]),rel_tol=0,abs_tol=0.00001)
    positive=[]
    for t in trades:
        assert t["pair"] in PAIRS and not t["is_open"]
        assert float(t["leverage"])==2.0
        assert math.isfinite(t["profit_abs"])
        if int(t["close_timestamp"])>int(t["open_timestamp"]):
            positive.append((int(t["open_timestamp"]),int(t["close_timestamp"]),t["pair"]))
    positive.sort()
    for (begin,end,pair),(next_begin,next_end,next_pair) in zip(positive,positive[1:]):
        assert end<=next_begin,("A240_ONE_SLOT_OVERLAP",pair,next_pair,end,next_begin)
    gross_winners=math.fsum(max(0,t["profit_abs"]) for t in trades)
    gross_losers=-math.fsum(min(0,t["profit_abs"]) for t in trades)
    top3=math.fsum(sorted((t["profit_abs"] for t in trades),reverse=True)[:3])
    return {
        "native_embedded_file":filename,
        "trade_count":len(trades),
        "native_profit_abs_usdt":model["profit_total_abs"],
        "ledger_profit_abs_usdt":profit,
        "return_pct_of_author_10000":float(model["profit_total_abs"])/100,
        "native_max_drawdown_account":model.get("max_drawdown_account"),
        "native_max_drawdown_abs_usdt":model.get("max_drawdown_abs"),
        "native_profit_factor":model.get("profit_factor"),
        "native_rejected_signals":model.get("rejected_signals"),
        "sum_positive_profit_abs":gross_winners,
        "sum_negative_profit_abs":gross_losers,
        "cash_profit_factor_recomputed":gross_winners/gross_losers if gross_losers else None,
        "top3_winners_usdt":top3,
        "balance_sum_without_top3_not_executable":profit-top3,
        "pair_trade_counts":{p:sum(t["pair"]==p for t in trades) for p in PAIRS},
        "zero_duration_trades":sum(t["close_timestamp"]==t["open_timestamp"] for t in trades),
        "positive_duration_overlap_found":False,
        "funding_fees_reported_sum_do_not_double_count":math.fsum(t.get("funding_fees",0) for t in trades)
    }

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--period",choices=PERIODS,required=True)
    a.add_argument("--datadir",required=True)
    a.add_argument("--original",required=True)
    a.add_argument("--outdir",required=True)
    args=a.parse_args()
    original=Path(args.original).resolve()
    data=Path(args.datadir).resolve()
    out=Path(args.outdir).resolve()
    out.mkdir(parents=True,exist_ok=True)
    config,pins=author_config(original,out)
    if (original/".git").exists():
        sha=subprocess.check_output(["git","-C",str(original),"rev-parse","HEAD"],text=True).strip()
        assert sha==EXPECTED_ORIGINAL,("A240_SOURCE_COMMIT_DRIFT",sha)
    state={"cycle":"A240","period":args.period,"model":"unchanged original strategy, full Freqtrade2026.4 one-wallet BTC ETH futures",
           "periods_UTC":{"2025":"[2025-04-01,2026-01-01)","2026":"[2026-05-13,2026-10-01)"},
           "author_config_pins":pins,"source_commit":EXPECTED_ORIGINAL,"results":[],
           "limitations":["Contract metadata and 0.005 tier from historical A195 adapter TEST FIXTURE not Binance official liquidation parity.",
                          "Freqtrade OHLC modeled limit queue and stop gaps; fee stress not actual order book slippage.",
                          "No untouched OOS or forward PAPER; 2025 source window is pre-publication."]}
    results_path=out/"A240_NATIVE_RESULTS.json"
    status=0
    for scenario,fee in FEES.items():
        cmd=[sys.executable,"research/a240_doublema_author_wallet/a240_offline_native.py",
             "-c",str(config),"--userdir",str(original/"user_data"),"--datadir",str(data),
             "--strategy","VideoDoubleMaFuturesStrategy","--timeframe","1h","--timeframe-detail","5m",
             "--timerange",PERIODS[args.period],"--data-format-ohlcv","json",
             "--fee",str(fee),"--export","trades","--cache","none"]
        target=out/f"{args.period}-{scenario}-shared-btc-eth-original.zip"
        print("A240_ORIGINAL_AUTHOR_SINGLE_WALLET_BEGIN",args.period,scenario,flush=True)
        for old in (original/"user_data/backtest_results").glob("backtest-result*.zip"):
            old.unlink()
        try:
            cp=subprocess.run(cmd,text=True,capture_output=True,timeout=720,env={
                **os.environ,"FREQTRADE__EXCHANGE__KEY":"","FREQTRADE__EXCHANGE__SECRET":"","PYTHONUNBUFFERED":"1"
            })
            combined=cp.stdout+"\n"+cp.stderr
            (out/f"{args.period}-{scenario}.log").write_text(combined[-350000:],"utf8")
            if cp.returncode!=0:
                raise RuntimeError(f"NATIVE_NONZERO_EXIT={cp.returncode} TAIL={combined[-1800:]}")
            zips=list((original/"user_data/backtest_results").glob("backtest-result*.zip"))
            assert len(zips)==1,("A240_ARCHIVE_COUNT",len(zips))
            shutil.copy2(zips[0],target)
            metrics=parse_native(target)
            rec={"state":"COMPLETE_NATIVE_AUTHOR_ACCOUNT",
                 "period":args.period,"scenario":scenario,"fee_each_side":fee,
                 "native_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
                 "zip_name":target.name,**metrics}
            state["results"].append(rec)
            print("A240_NATIVE_AUTHOR_BTC_ETH_SHARED_ACCOUNT_RESULT",json.dumps({
                k:rec[k] for k in ("period","scenario","return_pct_of_author_10000",
                    "native_max_drawdown_account","trade_count","native_profit_factor","pair_trade_counts")},sort_keys=True),flush=True)
        except Exception as e:
            status=1
            state["results"].append({"state":"BLOCKED_NATIVE_ORIGINAL","period":args.period,
                                     "scenario":scenario,"fee_each_side":fee,"error":str(e)[:3000]})
            print("A240_NATIVE_ORIGINAL_BLOCKED",args.period,scenario,str(e)[:1000],flush=True)
        results_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n","utf8")
    if status:sys.exit(1)
    assert len(state["results"])==2 and all(x["state"]=="COMPLETE_NATIVE_AUTHOR_ACCOUNT" for x in state["results"])
    print("A240_TWO_AUTHOR_ACCOUNT_COST_SCENARIOS_NATIVE_COMPLETED",args.period,flush=True)

if __name__=="__main__":
    main()
