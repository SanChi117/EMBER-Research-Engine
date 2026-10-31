"""A237 author BTC/ETH/SOL/BNB single-account TrendFollowing replay.
The original source remains SHA-verified and unchanged. Freqtrade model only.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
from research.a235_timeframe_parity import a235_run_originals as a235
from research.a228_five_original import a228_prepare_pinned_originals_and_real_futures as prep

AUTHOR_REPO = "krantikaridev/freqtrade"
AUTHOR_COMMIT = "11d7d66c60cf49a148cb61619b8061dc40d2510c"
AUTHOR_CONFIG_BLOB = "965193dbe93e65389c0ce8b5669229667e9fd846"
AUTHOR_PATH = "config/config.dryrun.json"
FOUR_PAIRS = ("BTC/USDT:USDT","ETH/USDT:USDT","SOL/USDT:USDT","BNB/USDT:USDT")
A237_DIR = a235.GEN/"native_backtests_a237"
A237_DIR.mkdir(parents=True, exist_ok=True)

def load_original_author_config():
    url = f"https://raw.githubusercontent.com/{AUTHOR_REPO}/{AUTHOR_COMMIT}/{AUTHOR_PATH}"
    raw = prep.genuine.fetch(url)
    sha = prep.genuine.blob_sha(raw)
    if sha != AUTHOR_CONFIG_BLOB:
        raise ValueError(f"A237_AUTHOR_CONFIG_SHA_MISMATCH {sha}")
    data = json.loads(raw)
    assert data["strategy"] == "TrendFollowing"
    assert data["timeframe"] == "4h"
    assert data["max_open_trades"] == 3
    assert data["stake_amount"] == "unlimited"
    assert data["dry_run_wallet"] == 1000
    assert data["trading_mode"] == "futures"
    assert data["margin_mode"] == "isolated"
    assert data["tradable_balance_ratio"] == 0.95
    assert tuple(data["exchange"]["pair_whitelist"]) == FOUR_PAIRS
    print("A237_AUTHOR_COMMON_ACCOUNT_SOURCE_PIN_OK", sha, flush=True)
    return data

author = load_original_author_config()

def author_config_for_run():
    # Begin with vetted research-only testnet-metadata adapter.
    cfg = a235.config_for_run_original()
    # Exact original portfolio, sizing and signal timeframe; no credential upload.
    for field in ("bot_name","dry_run_wallet","max_open_trades","stake_currency",
                  "stake_amount","tradable_balance_ratio","fiat_display_currency",
                  "cancel_open_orders_on_exit","trading_mode","margin_mode",
                  "unfilledtimeout","entry_pricing","exit_pricing","timeframe",
                  "startup_candle_count"):
        if field in author:
            cfg[field] = copy.deepcopy(author[field])
    cfg["exchange"]["pair_whitelist"] = list(FOUR_PAIRS)
    cfg["exchange"]["pair_blacklist"] = copy.deepcopy(author["exchange"].get("pair_blacklist",[]))
    cfg["pairlists"] = copy.deepcopy(author["pairlists"])
    # Prevent the A228 generic adapter from replacing original author's
    # strategy-defined stoploss_on_exchange=True with False.
    cfg.pop("order_types",None)
    cfg["bot_name"] = "EMBER_A237_AUTHOR_SINGLE_ACCOUNT_NO_ORDERS"
    cfg["dry_run"] = True
    assert cfg["stake_amount"] == "unlimited"
    assert "order_types" not in cfg
    return cfg

# All source/timeframe asserts in A235 still execute; restrict economics to the
# single author's original TrendFollowing class and 6 predetermined windows.
a235.config_for_run_original = a235.config_for_run
a235.config_for_run = author_config_for_run
a235.STRATEGIES = ("TrendFollowing",)
a235.REPLAY = A237_DIR


def main():
    a235.main()
    path = A237_DIR/"A228_FIVE_NATIVE_REPLAY_STATUS.json"
    state = json.loads(path.read_text("utf8"))
    state["cycle"] = "A237"
    state["author_config_ref"] = {"repo":AUTHOR_REPO,"commit":AUTHOR_COMMIT,
                                  "path":AUTHOR_PATH,"git_blob":AUTHOR_CONFIG_BLOB}
    state["author_account"] = {"pairs":list(FOUR_PAIRS),"stake_amount":"unlimited",
                               "max_open_trades":3,"wallet":1000,"balance_ratio":0.95}
    state["limitations_added"] = [
        "Native author's stoploss_on_exchange=True restored from original source; backtesting simulates fills, not real exchange stop placement",
        "Historical Binance mainnet price/funding/mark; testnet contract metadata",
        "2024/2025/Jan-May2026 already seen; this is author-account parity, not untouched OOS"
    ]
    if len(state["strategy_runs"]) != 6:
        raise ValueError("A237_EXPECTED_6_AUTHOR_CONFIG_TRADES")
    path2 = A237_DIR/"A237_TRENDFOLLOWING_AUTHOR_ACCOUNT_STATUS.json"
    path2.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n","utf8")
    print("A237_AUTHOR_ACCOUNT_RESULTS",json.dumps({
        "expected":6,"complete":sum(x["state"]=="NATIVE_FREQTRADE_BACKTEST_COMPLETE" for x in state["strategy_runs"]),
        "outcomes":[{key:r.get(key) for key in
         ("year","cost_model","state","native_profit_total_pct","native_trade_count","native_max_drawdown_account")}
         for r in state["strategy_runs"]]
    },ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
