"""Run FIVE pinned original Freqtrade strategies. Not authored trading logic.

Must be invoked after A228 source+genuine Binance futures native feather stage.
Records every failure explicitly; NEVER converts missing/failed run to 0% or PASS.
No real orders, API credentials or modification to the source strategies.
"""
from __future__ import annotations
import json
import os
import platform
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
GEN=HERE/"generated"
SOURCE_RECEIPT=GEN/"A228_ORIGINAL_AND_MARKET_RECEIPTS.json"
REPLAY=GEN/"native_backtests"
STRATEGIES=(
    "DualTrendCompressionRestartShortV1Strategy",
    "TrendFollowing",
    "NASOSv7LongShort",
    "BearRegimeShortV1",
    "Risk_Stair_S5",
)
YEARS={"2025":"20250101-20260101"}  # 2026 blocked: genuine Binance 8h mark June missing 3 bars; genuine 1h mark 24 bars
COSTS={"base":0.0005,"stress":0.0011}


def config_for_run():
    return {
      "$schema":"https://schema.freqtrade.io/schema.json",
      "bot_name":"EMBER_A228_OFFLINE_FIVE_PINNED_RESEARCH",
      "dry_run":True,
      "dry_run_wallet":1000,
      "trading_mode":"futures",
      "margin_mode":"isolated",
      "exchange":{
        "name":"binance",
        "key":"",
        "secret":"",
        "ccxt_config":{
          "enableRateLimit":True,
          "options":{"fetchMarkets":["linear"],"fetchCurrencies":False},
          "urls":{"api":{
            "fapiPublic":"https://testnet.binancefuture.com/fapi/v1",
            "fapiPublicV2":"https://testnet.binancefuture.com/fapi/v2",
            "fapiPublicV3":"https://testnet.binancefuture.com/fapi/v3"
          }}
        },
        "ccxt_async_config":{
          "options":{"fetchMarkets":["linear"],"fetchCurrencies":False},
          "urls":{"api":{
            "fapiPublic":"https://testnet.binancefuture.com/fapi/v1",
            "fapiPublicV2":"https://testnet.binancefuture.com/fapi/v2",
            "fapiPublicV3":"https://testnet.binancefuture.com/fapi/v3"
          }}
        },
        "pair_whitelist":["BTC/USDT:USDT","ETH/USDT:USDT","SOL/USDT:USDT"],
        "pair_blacklist":[]
      },
      "pairlists":[{"method":"StaticPairList"}],
      "stake_currency":"USDT",
      "stake_amount":100,
      "tradable_balance_ratio":0.99,
      "fiat_display_currency":"USD",
      "max_open_trades":3,
      "timeframe":"1h",
      "cancel_open_orders_on_exit":False,
      "unfilledtimeout":{"entry":10,"exit":10,"exit_timeout_count":0,"unit":"minutes"},
      "entry_pricing":{"price_side":"same","use_order_book":True,"order_book_top":1},
      "exit_pricing":{"price_side":"same","use_order_book":True,"order_book_top":1},
      "order_types":{"entry":"limit","exit":"limit","stoploss":"market","stoploss_on_exchange":False},
      "user_data_dir":str(GEN),
      "dataformat_ohlcv":"feather",
      "dataformat_trades":"feather"
    }


def recent_result(path):
    result_candidates=sorted(path.glob("*.json"),key=lambda f:f.stat().st_mtime,reverse=True)
    for result in result_candidates:
        if ".meta." in result.name:continue
        try:
            data=json.loads(result.read_text("utf8"))
        except (UnicodeDecodeError,ValueError):
            continue
        if isinstance(data,dict) and "strategy" in data:
            return data, str(result)
    # The default modern freqtrade - export is zip
    for z in sorted(path.glob("*.zip"),key=lambda f:f.stat().st_mtime,reverse=True):
        with zipfile.ZipFile(z) as bundle:
            for member in bundle.namelist():
                if not member.endswith(".json") or "meta" in member:continue
                try:d=json.loads(bundle.read(member))
                except (UnicodeDecodeError,ValueError):continue
                if isinstance(d,dict) and "strategy" in d:
                    return d,f"{z}:{member}"
    return None,None


def run_one(year,timerange,cost_name,fee,strategy,config_file):
    dest=REPLAY/year/cost_name/strategy
    dest.mkdir(parents=True,exist_ok=True)
    command=[
        sys.executable,"-m","freqtrade","backtesting",
        "--config",str(config_file),
        "--datadir",str(GEN/"binance"),
        "--strategy-path",str(GEN/"strategies"),
        "--strategy",strategy,
        "--timerange",timerange,
        "--fee",str(fee),
        "--max-open-trades","3",
        "--export","trades",
        "--backtest-directory",str(dest),
        "--cache","none",
    ]
    print("A228_NATIVE_START",year,cost_name,strategy,flush=True)
    try:
        run=subprocess.run(command,capture_output=True,text=True,timeout=540,
                           env={**os.environ,"PYTHONUNBUFFERED":"1"})
    except subprocess.TimeoutExpired as e:
        return {"state":"BLOCKED_TIMEOUT","error":str(e),"year":year,
                "cost_model":cost_name,"strategy":strategy}
    combined=run.stdout+"\n"+run.stderr
    (dest/"native_freqtrade.log").write_text(combined[-200000:],"utf8")
    data,path=recent_result(dest)
    if run.returncode!=0 or data is None:
        lines=[l.strip() for l in combined.splitlines() if l.strip()]
        failure=lines[-16:]
        print("A228_NATIVE_BLOCKED",year,cost_name,strategy,
              "returncode",run.returncode,"tail",str(failure)[-900:],flush=True)
        return {"state":"BLOCKED_NATIVE_RUNTIME","year":year,"cost_model":cost_name,
                "strategy":strategy,"return_code":run.returncode,"log":str(dest/"native_freqtrade.log"),
                "error_tail":failure}
    metrics=data["strategy"].get(strategy)
    if not metrics:
        return {"state":"BLOCKED_MISSING_STRATEGY_RESULTS","year":year,
                "cost_model":cost_name,"strategy":strategy,"file":path}
    result={
        "state":"NATIVE_FREQTRADE_BACKTEST_COMPLETE",
        "strategy":strategy,"year":year,"cost_model":cost_name,
        "fee_each_side":fee,"result_file":path,
        "native_profit_total_pct":metrics.get("profit_total_pct"),
        "native_profit_total_abs_usdt":metrics.get("profit_total_abs"),
        "native_max_drawdown_account":metrics.get("max_drawdown_account"),
        "native_max_drawdown_abs":metrics.get("max_drawdown_abs"),
        "native_trade_count":metrics.get("total_trades"),
        "native_wins":metrics.get("wins"),"native_losses":metrics.get("losses"),
        "native_profit_factor":metrics.get("profit_factor"),
        "native_sharpe":metrics.get("sharpe"),
        "native_rejected_signals":metrics.get("rejected_signals"),
        "trade_exit_reasons":metrics.get("exit_reason_summary"),
        "native_original_source_only":True,"trade_orders":False,
        "assumptions":"Binance genuine USD-M 5m UTC candles resampled; true mark/funding datasets, native Freqtrade OHLC fills; higher fee used as cost stress NOT actual slippage; no verified maintenance margin/liquidation; 3 pairs not 33 Freqle league."
    }
    print("A228_NATIVE_RESULT",json.dumps({k:v for k,v in result.items() if k in
        ("strategy","year","cost_model","native_profit_total_pct","native_trade_count",
        "native_max_drawdown_account")},ensure_ascii=False),flush=True)
    return result


def main():
    if not SOURCE_RECEIPT.exists():
        raise ValueError("No authentic receipts produced by A228 pre-stage")
    receipts=json.loads(SOURCE_RECEIPT.read_text("utf8"))
    if len(receipts["original_pins"])!=5 or receipts["market_n"]<100:
        raise ValueError("Source validation required")
    REPLAY.mkdir(parents=True,exist_ok=True)
    config_file=GEN/"a228_replay_config.json"
    config_file.write_text(json.dumps(config_for_run(),indent=2),"utf8")
    status={"source_and_market_receipts":"A228_ORIGINAL_AND_MARKET_RECEIPTS.json",
            "python":sys.version,"platform":platform.platform(),
            "strategy_runs":[],"warnings":["There is no independent orderbook/slippage fill replay",
                "Funding and mark are genuine input; fill prices are modelled by Freqtrade",
                "One-year runs reset wallet; 3 majors differ from Freqle 33-pair league",
                "IMPORTANT: official Binance FUTURES TESTNET public exchangeInfo only for CCXT contract metadata due to mainnet HTTP451; prices/mark/funding remain genuine mainnet USD-M archives; precision/limits require later mainnet parity",
                "Risk_Stair S5 native 5x can liquidate; OHLC backtest is insufficient margin-tier verification"]}
    for year,timerange in YEARS.items():
        for scenario,fee in COSTS.items():
            for name in STRATEGIES:
                record=run_one(year,timerange,scenario,fee,name,config_file)
                status["strategy_runs"].append(record)
                (REPLAY/"A228_FIVE_NATIVE_REPLAY_STATUS.json").write_text(
                    json.dumps(status,indent=2,ensure_ascii=False)+"\n","utf8")
    completed=sum(x["state"]=="NATIVE_FREQTRADE_BACKTEST_COMPLETE" for x in status["strategy_runs"])
    print("A228_ALL_RESULTS",json.dumps({"expected":len(YEARS)*len(COSTS)*len(STRATEGIES),
       "complete":completed,"blocked":len(status["strategy_runs"])-completed,
       "summary":[{k:v for k,v in x.items() if k in
       ("strategy","year","cost_model","state","native_profit_total_pct","native_trade_count","native_max_drawdown_account")}
       for x in status["strategy_runs"]]},ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
