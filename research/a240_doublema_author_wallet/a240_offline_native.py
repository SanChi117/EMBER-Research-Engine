"""A240 exact original author one-wallet Freqtrade engine, offline Binance USD-M.
The Binance market metadata/tiers below are A195's TEST FIXTURE extended to
both assets, not verified exchange maintenance-margin or executable limit fills.
"""
from __future__ import annotations
import json
import sys
from freqtrade.commands.arguments import Arguments
from freqtrade.commands.optimize_commands import setup_optimize_configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting
from freqtrade.resolvers.exchange_resolver import ExchangeResolver

PAIRS=("BTC/USDT:USDT","ETH/USDT:USDT")
PREC={"BTC":(0.001,0.1),"ETH":(0.001,0.01)}

def model_market(pair):
    sym=pair.split("/")[0]
    assert sym in PREC
    amount,price=PREC[sym]
    return {
        "id":sym+"USDT","symbol":pair,"base":sym,"quote":"USDT",
        "settle":"USDT","type":"swap","spot":False,"margin":False,
        "swap":True,"future":False,"option":False,"contract":True,
        "linear":True,"inverse":False,"active":True,"contractSize":1.0,
        "expiry":None,"expiryDatetime":None,"strike":None,"optionType":None,
        "precision":{"amount":amount,"price":price,"cost":0.01},
        "limits":{"leverage":{"min":1.0,"max":50.0},
                  "amount":{"min":amount,"max":1e9},
                  "price":{"min":price,"max":1e9},
                  "cost":{"min":5.0,"max":1e14}},
        "maker":0.0002,"taker":0.0005,"percentage":True,"tierBased":False,
        "info":{"symbol":sym+"USDT","contractType":"PERPETUAL","status":"TRADING"}
    }

def model_tier(pair):
    return {"tier":1,"symbol":pair,"minNotional":0.0,"maxNotional":1e12,
            "maintenanceMarginRate":0.005,"maxLeverage":50.0,"maintAmt":0.0,"info":{}}

def main(argv):
    parsed=Arguments(["backtesting",*argv]).get_parsed_arg()
    config=setup_optimize_configuration(parsed,RunMode.BACKTEST)
    assert config["exchange"]["name"]=="binance"
    assert tuple(config["exchange"]["pair_whitelist"])==PAIRS,config["exchange"]["pair_whitelist"]
    assert config["trading_mode"]=="futures" and config["margin_mode"]=="isolated"
    assert config["timeframe"]=="1h",config["timeframe"]
    assert config["max_open_trades"]==1 and config["stake_amount"]=="unlimited"
    assert float(config["dry_run_wallet"])==10000
    assert abs(float(config["tradable_balance_ratio"])-1.0)<1e-10
    assert config["dry_run"] is True
    assert config["order_types"]["stoploss_on_exchange"] is False
    assert config["entry_pricing"]["price_side"]=="other"
    assert config["exit_pricing"]["price_side"]=="other"
    assert config["exchange"]["key"]=="" and config["exchange"]["secret"]==""
    assert config["strategy"]=="VideoDoubleMaFuturesStrategy"
    m={pair:model_market(pair) for pair in PAIRS}
    exchange=ExchangeResolver.load_exchange(config,validate=False,load_leverage_tiers=False)
    exchange._markets=m
    exchange._api.set_markets(m)
    exchange._leverage_tiers={pair:[model_tier(pair)] for pair in PAIRS}
    def forbid(*args,**kwargs):
        raise RuntimeError("A240_UNEXPECTED_EXCHANGE_NETWORK_API_FORBIDDEN")
    exchange.reload_markets=forbid
    exchange._api.load_markets=lambda *a,**kw:exchange._api.markets
    config["a240_offline_contract_tier_fixture_unverified_liquidation"]=True
    print("A240_SINGLE_AUTHOR_ACCOUNT_AND_ORIGINAL_BTC_ETH_ORDER_CONFIRMED",
          json.dumps({"pairs":PAIRS,"wallet":10000,"max_open_trades":1,
                      "stake":"unlimited","offline_metadata_not_exchange_certified":True}),flush=True)
    Backtesting(config,exchange=exchange).start()
    print("A240_NATIVE_FULL_ORIGINAL_BTC_ETH_SHARED_WALLET_COMPLETED",flush=True)

if __name__=="__main__":
    main(sys.argv[1:])
