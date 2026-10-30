"""A191 actual Freqtrade 2026.4 Backtesting with offline Binance market metadata.
Real Binance Vision historical OHLCV and previously captured real settled funding/mark.
Static exchange metadata is NOT real exchange order-book or futures maintenance-tier proof.
No trading credentials or network order operations.
"""
from __future__ import annotations
import json,sys
from freqtrade.commands.arguments import Arguments
from freqtrade.commands.optimize_commands import setup_optimize_configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting
from freqtrade.resolvers.exchange_resolver import ExchangeResolver

PAIR="ETH/USDT:USDT"
MARKET={
    "id":"ETHUSDT","symbol":PAIR,"base":"ETH","quote":"USDT",
    "settle":"USDT","type":"swap","spot":False,"margin":False,
    "swap":True,"future":False,"option":False,"contract":True,
    "linear":True,"inverse":False,"active":True,"contractSize":1.0,
    "expiry":None,"expiryDatetime":None,"strike":None,"optionType":None,
    "precision":{"amount":0.001,"price":0.01,"cost":0.01},
    "limits":{"leverage":{"min":1.0,"max":50.0},
              "amount":{"min":0.001,"max":1e8},
              "price":{"min":0.01,"max":1e8},
              "cost":{"min":5.0,"max":1e12}},
    "maker":0.0002,"taker":0.0005,"percentage":True,
    "tierBased":False,"info":{"symbol":"ETHUSDT","contractType":"PERPETUAL","status":"TRADING"}
}
TIER={"tier":1,"symbol":PAIR,"minNotional":0.0,"maxNotional":1e10,
    "maintenanceMarginRate":0.005,"maxLeverage":50.0,"maintAmt":0.0,"info":{}}

def main(argv):
    args=Arguments(["backtesting",*argv]).get_parsed_arg()
    config=setup_optimize_configuration(args,RunMode.BACKTEST)
    assert config["exchange"]["name"]=="binance",config["exchange"]["name"]
    assert config["exchange"]["pair_whitelist"]==[PAIR]
    assert config["trading_mode"]=="futures"
    assert config["margin_mode"]=="isolated"
    assert config["dry_run"] is True
    exchange=ExchangeResolver.load_exchange(config,validate=False,load_leverage_tiers=False)
    exchange._markets={PAIR:MARKET.copy()}
    exchange._api.set_markets({PAIR:MARKET.copy()})
    exchange._leverage_tiers={PAIR:[TIER.copy()]}
    def disabled(*a,**kw):raise RuntimeError("A191_EXCHANGE_NETWORK_PROBE_FORBIDDEN")
    exchange.reload_markets=disabled
    exchange._api.load_markets=lambda *args,**kwargs:exchange._api.markets
    config["a191_static_binance_exchange_metadata_not_live_fills"]=True
    print("A191_REAL_FREQTRADE_2026_4_BINANCE_SOURCE_STATIC_METADATA",flush=True)
    runner=Backtesting(config,exchange=exchange)
    runner.start()
    print("A191_NATIVE_FREQTRADE_BACKTEST_DONE",flush=True)

if __name__=="__main__":
    main(sys.argv[1:])
