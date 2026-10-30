"""Run EXACT pinned user strategy with genuine Freqtrade Backtesting engine.

OFFLINE OKX market/tiers fixture: price signals/stop/portfolio logic are not
modified. Exchange-market metadata is simulated, hence venue execution is NOT
validated. Never use real keys or launch real trading.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from freqtrade.commands.arguments import Arguments
from freqtrade.commands.optimize_commands import setup_optimize_configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting
from freqtrade.resolvers.exchange_resolver import ExchangeResolver


PAIR="ETH/USDT:USDT"
STATIC_MARKET={
    "id":"ETH-USDT-SWAP","symbol":PAIR,"base":"ETH","quote":"USDT",
    "settle":"USDT","type":"swap","spot":False,"margin":False,
    "swap":True,"future":False,"option":False,"contract":True,
    "linear":True,"inverse":False,"active":True,
    "contractSize":0.1,"expiry":None,"expiryDatetime":None,
    "strike":None,"optionType":None,
    "precision":{"amount":0.01,"price":0.01,"cost":0.01},
    "limits":{"leverage":{"min":1.0,"max":50.0},
              "amount":{"min":0.01,"max":1e8},
              "price":{"min":0.01,"max":1e8},
              "cost":{"min":1.0,"max":1e12}},
    "maker":0.0002,"taker":0.0005,"percentage":True,
    "tierBased":False,"info":{"instId":"ETH-USDT-SWAP"}
}

STATIC_TIER={
    "tier":1,"symbol":PAIR,"minNotional":0.0,"maxNotional":1e10,
    "maintenanceMarginRate":0.005,"maxLeverage":50.0,"maintAmt":0.0,"info":{}
}


def main(argv):
    args=Arguments(["backtesting",*argv]).get_parsed_arg()
    config=setup_optimize_configuration(args,RunMode.BACKTEST)
    assert config["exchange"]["name"]=="okx"
    assert config["exchange"]["pair_whitelist"]==[PAIR]
    assert config["dry_run"] is True
    exchange=ExchangeResolver.load_exchange(
        config,validate=False,load_leverage_tiers=False
    )
    exchange._markets={PAIR:STATIC_MARKET.copy()}
    exchange._api.set_markets({PAIR:STATIC_MARKET.copy()})
    exchange._leverage_tiers={PAIR:[STATIC_TIER.copy()]}
    # Do not accidentally allow a new call to the public remote market API.
    def no_network(*args,**kwargs):
        raise RuntimeError("OFFLINE_NATIVE_EXCHANGE_PROBE_FORBIDDEN")
    exchange.reload_markets=no_network
    exchange._api.load_markets=lambda *args,**kwargs:exchange._api.markets
    config["backtest_offline_metadata_proxy"]=True
    print("NATIVE_BACKTEST_OFFLINE_MARKET_METADATA_SIMULATED_PRICE_AND_STRATEGY_UNMODIFIED",
          flush=True)
    print("NATIVE_MARKET_FIXTURE",json.dumps(
        {"pair":PAIR,"market":STATIC_MARKET,"tier":STATIC_TIER},
        sort_keys=True),flush=True)
    runner=Backtesting(config,exchange=exchange)
    runner.start()
    print("NATIVE_FREQTRADE_OFFLINE_BACKTEST_FINISHED",flush=True)


if __name__=="__main__":
    main(sys.argv[1:])
