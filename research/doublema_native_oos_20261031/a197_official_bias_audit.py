#!/usr/bin/env python3
"""A197: Official Freqtrade==2026.4 LookaheadAnalysis and RecursiveAnalysis classes
against EXACT original DoubleMA author strategy and real Binance USD-M historical data.
We only supply same immutable static offline Binance market metadata as A195/A196.
No trading accounts, no paper order creation. Not a substitute for native exchange fills.
"""
import argparse,json,sys
from pathlib import Path
from freqtrade.commands.arguments import Arguments
from freqtrade.configuration import setup_utils_configuration
from freqtrade.enums import RunMode
from freqtrade.resolvers.exchange_resolver import ExchangeResolver
from freqtrade.optimize.analysis.lookahead import LookaheadAnalysis
from freqtrade.optimize.analysis.lookahead_helpers import LookaheadAnalysisSubFunctions
from freqtrade.optimize.analysis.recursive import RecursiveAnalysis
from freqtrade.optimize.analysis.recursive_helpers import RecursiveAnalysisSubFunctions

PREC={"BTC":(0.001,0.1),"ETH":(0.001,0.01),"SOL":(0.01,0.001),"LINK":(0.1,0.001)}
def static_exchange(config,pair):
    sym=pair.split("/")[0]
    assert sym in PREC,(pair,sym)
    amount,price=PREC[sym]
    market={"id":sym+"USDT","symbol":pair,"base":sym,"quote":"USDT",
            "settle":"USDT","type":"swap","spot":False,"margin":False,
            "swap":True,"future":False,"option":False,"contract":True,
            "linear":True,"inverse":False,"active":True,"contractSize":1.0,
            "expiry":None,"expiryDatetime":None,"strike":None,"optionType":None,
            "precision":{"amount":amount,"price":price,"cost":0.01},
            "limits":{"leverage":{"min":1.0,"max":50.0},
                      "amount":{"min":amount,"max":1e9},
                      "price":{"min":price,"max":1e9},
                      "cost":{"min":5.0,"max":1e14}},
            "maker":0.0002,"taker":0.0005,"percentage":True,
            "tierBased":False,"info":{"symbol":sym+"USDT","contractType":"PERPETUAL","status":"TRADING"}}
    tier={"tier":1,"symbol":pair,"minNotional":0.0,"maxNotional":1e12,
          "maintenanceMarginRate":0.005,"maxLeverage":50.0,"maintAmt":0.0,"info":{}}
    exchange=ExchangeResolver.load_exchange(config,validate=False,load_leverage_tiers=False)
    exchange._markets={pair:market}
    exchange._api.set_markets({pair:market})
    exchange._leverage_tiers={pair:[tier]}
    def deny(*args,**kwargs):raise RuntimeError("A197_OFFLINE_EXCHANGE_NETWORK_CALL_DENIED")
    exchange.reload_markets=deny
    exchange._api.load_markets=lambda *args,**kwargs:exchange._api.markets
    return exchange

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--mode",required=True,choices=("lookahead","recursive"))
    pa.add_argument("--config",required=True)
    pa.add_argument("--userdir",required=True)
    pa.add_argument("--datadir",required=True)
    pa.add_argument("--time",required=True)
    pa.add_argument("--fee",type=float,default=0.0005)
    pa.add_argument("--out",required=True)
    args=pa.parse_args()
    cmd="lookahead-analysis" if args.mode=="lookahead" else "recursive-analysis"
    aa=Arguments([cmd,"-c",args.config,"--userdir",args.userdir,
                  "--datadir",args.datadir,
                  "--strategy","VideoDoubleMaFuturesStrategy",
                  "--timeframe","1h","--timerange",args.time,
                  "--fee",str(args.fee),
                  "--data-format-ohlcv","json"]).get_parsed_arg()
    config=setup_utils_configuration(aa,RunMode.UTIL_NO_EXCHANGE)
    assert config["exchange"]["name"]=="binance"
    assert config["dry_run"] is True
    assert config["trading_mode"]=="futures" and config["margin_mode"]=="isolated"
    pair=config["exchange"]["pair_whitelist"][0]
    assert len(config["exchange"]["pair_whitelist"])==1
    config["pairs"]=[pair]
    config["backtest_cache"]="none"
    config["fee"]=args.fee
    config["dry_run"]=True
    config["exchange"]["ccxt_config"]={}
    config["exchange"]["ccxt_async_config"]={}
    assert not config["exchange"].get("key")
    assert not config["exchange"].get("secret")
    o={"schema":"EMBER_A197_OFFICIAL_FREQTRADE_CLASS_BIAS_AUDIT",
       "mode":args.mode,"pair":pair,"engine":"freqtrade==2026.4",
       "frozen_original_commit":"40af5c7c1c44253766428cfb06babf22f9817aa4",
       "window":args.time,
       "offline_metadata_only":True,"official_freqtrade_classes":True}
    path=Path(args.userdir)/"strategies/VideoDoubleMaFuturesStrategy.py"
    assert path.is_file(),path
    strategy_info={"name":"VideoDoubleMaFuturesStrategy","location":path}
    if args.mode=="lookahead":
        # Native Freqtrade lookahead routine itself changes simulation to unlimited
        # wallet and market orders unless allow-limit-orders True. Keep both
        # semantics documented rather than report resulting PnL as portfolio PnL.
        config["minimum_trade_amount"]=3
        config["targeted_trade_amount"]=10
        config["lookahead_allow_limit_orders"]=False
        config=LookaheadAnalysisSubFunctions.calculate_config_overrides(config)
        exchange=static_exchange(config,pair)
        instance=LookaheadAnalysis(config,strategy_info)
        instance.exchange=exchange
        instance.start()
        a=instance.current_analysis
        o.update({"native_lookahead_forces_market_entry_exit":True,
                  "note":"Official Freqtrade lookahead test changes max trades, wallet, stake and uses market orders to avoid false bias from limits; this is NOT original strategy economic backtest.",
                  "minimum_trade_amount":config["minimum_trade_amount"],
                  "targeted_trade_amount":config["targeted_trade_amount"],
                  "analyzed_signals":a.total_signals,
                  "biased_entries":a.false_entry_signals,
                  "biased_exits":a.false_exit_signals,
                  "biased_indicator_names":a.false_indicators,
                  "has_bias":a.has_bias,
                  "failed_bias_check":instance.failed_bias_check,
                  "verdict":"DETECTED" if a.has_bias else "NO_DETECTED_BIAS" if not instance.failed_bias_check else "INSUFFICIENT_OR_ERROR"})
        assert not instance.failed_bias_check,("OFFICIAL_FREQTRADE_BIAS_NO_POWER_OR_FAILURE",o)
    else:
        config["startup_candle"]=[199,399,499,999]
        config=RecursiveAnalysisSubFunctions.calculate_config_overrides(config)
        exchange=static_exchange(config,pair)
        instance=RecursiveAnalysis(config,strategy_info)
        instance.exchange=exchange
        instance.start()
        o.update({"startup_candles_tested":instance._startup_candle,
                  "recursive_differences":instance.dict_recursive,
                  "indicators_with_recursive_variation":len(instance.dict_recursive),
                  "note":"Native RecursiveAnalysis compares same ending indicators with different warmup lengths and one very short historical end for lookahead; log records the upstream official analyzer check."})
    Path(args.out).write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n")
    print("A197_OFFICIAL_FREQTRADE_ANALYSIS_COMPLETED",json.dumps(o,ensure_ascii=False)[:9000],flush=True)
if __name__=="__main__":main()
