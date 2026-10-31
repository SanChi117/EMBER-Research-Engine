#!/usr/bin/env python3
"""A199 exact original public Freqtrade futures strategy class in native
Freqtrade 2026.4 Backtesting engine, offline STATIC exchange market metadata.
Four real Binance Vision futures pairs, own 1000 wallet and fixed $100 stake.
Never passes API credentials nor sends orders; market metadata is synthetic
and must not be mistaken for proof of real fills.
"""
from __future__ import annotations
import json,sys
from freqtrade.commands.arguments import Arguments
from freqtrade.commands.optimize_commands import setup_optimize_configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting
from freqtrade.resolvers.exchange_resolver import ExchangeResolver

PREC={"BTC":(0.001,0.1),"ETH":(0.001,0.01),"SOL":(0.01,0.001),"LINK":(0.1,0.001)}
def main(argv):
    args=Arguments(["backtesting",*argv]).get_parsed_arg()
    config=setup_optimize_configuration(args,RunMode.BACKTEST)
    assert config["exchange"]["name"]=="binance"
    assert len(config["exchange"]["pair_whitelist"])==1
    assert config["trading_mode"]=="futures" and config["margin_mode"]=="isolated"
    assert config["dry_run"] is True and config["dry_run_wallet"]==1000
    assert float(config["stake_amount"])==100 and config["max_open_trades"]==1
    assert not config["exchange"].get("key") and not config["exchange"].get("secret")
    pair=config["exchange"]["pair_whitelist"][0];sym=pair.split("/")[0]
    assert sym in PREC
    amount,price=PREC[sym]
    market={"id":sym+"USDT","symbol":pair,"base":sym,"quote":"USDT","settle":"USDT",
      "type":"swap","spot":False,"margin":False,"swap":True,"future":False,
      "option":False,"contract":True,"linear":True,"inverse":False,"active":True,
      "contractSize":1.0,"expiry":None,"expiryDatetime":None,"strike":None,
      "optionType":None,"precision":{"amount":amount,"price":price,"cost":0.01},
      "limits":{"leverage":{"min":1.0,"max":50.0},
       "amount":{"min":amount,"max":1e9},"price":{"min":price,"max":1e9},
       "cost":{"min":5.0,"max":1e14}},"maker":0.0002,"taker":0.0005,
      "percentage":True,"tierBased":False,
      "info":{"symbol":sym+"USDT","contractType":"PERPETUAL","status":"TRADING"}}
    tier={"tier":1,"symbol":pair,"minNotional":0.0,"maxNotional":1e12,
      "maintenanceMarginRate":0.005,"maxLeverage":50.0,"maintAmt":0.0,"info":{}}
    exchange=ExchangeResolver.load_exchange(config,validate=False,load_leverage_tiers=False)
    exchange._markets={pair:market}
    exchange._api.set_markets({pair:market})
    exchange._leverage_tiers={pair:[tier]}
    def forbidden(*args,**kwargs):
        raise RuntimeError("A199_OFFLINE_API_CALL_FORBIDDEN")
    exchange.reload_markets=forbidden
    exchange._api.load_markets=lambda *args,**kwargs:exchange._api.markets
    config["a199_offline_static_binance_market_metadata_not_real_execution"]=True
    print("A199_NATIVE_FREQTRADE_FUTURES_STATIC_METADATA",
      json.dumps({"symbol":pair,"wallet":1000,"stake":100,
       "amount_step":amount,"price_step":price}),flush=True)
    engine=Backtesting(config,exchange=exchange)
    engine.start()
    print("A199_TRUE_FREQTRADE_2026_4_ORIGINAL_SOURCE_COMPLETED",pair,flush=True)
if __name__=="__main__":main(sys.argv[1:])
