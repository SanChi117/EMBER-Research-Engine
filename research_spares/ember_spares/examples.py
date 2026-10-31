"""Thirty-seven runnable examples proving every registered Zxx component can be called.

All numbers are synthetic placeholders, never actual Binance observations.
Use ``python -m ember_spares.examples`` to execute every example offline.
"""
from __future__ import annotations

import base64
import hashlib
import json
import tempfile
from pathlib import Path

from .plugin import invoke
from .registry import REGISTRY
from .accounting import RiskState, save_risk_state


def _candle(i: int=0, o: float=100, h: float=105, l: float=95, c: float=101, v: float=100) -> dict:
    return dict(open_time=i*60, close_time=(i+1)*60, open=o, high=h, low=l, close=c, volume=v, available_at=(i+1)*60)


def example_inputs(risk_file: str) -> dict[str,dict]:
    candles=[_candle(i,o=100+i/10,h=105+i/10,l=95+i/10,c=101+i/10) for i in range(32)]
    trace={'decision_at':200,'symbol':'BTCUSDT','side':'long','entry':100.,'stop':95.,'target':110.,'source':'reference'}
    trade={'trade_id':'trade-1','symbol':'BTCUSDT','strategy':'example','net_pnl_usdt':10.,'exit_at':300,'setup':'breakout'}
    artifact=b'{"version":1,"weights":{"a":0.25},"intercept":0.0}'
    sha=hashlib.sha256(artifact).hexdigest()
    return {
       'Z01':{'streams':{'funding':[{'event_time':100,'available_at':110,'value':0.0001,'source':'test'}]},'decision_at':120},
       'Z02':{'p':{'side':'long','quantity':1.,'entry_price':100.,'mark_price':102.,'collateral_usdt':20.},'tiers':[{'notional_floor':0.,'notional_ceiling':100000.,'maintenance_rate':.01}]},
       'Z03':{'book':{'bid':100.,'ask':101.,'bid_quantity':20.,'ask_quantity':10.,'exchange_time':10,'available_at':11}},
       'Z04':{'original':[trace],'challenger':[trace]},
       'Z05':{'legs':[{'asset':'BTC','side':'long','quantity':1.,'entry_price':100.,'mark_price':102.},{'asset':'ETH','side':'short','quantity':1.,'entry_price':50.,'mark_price':49.}]},
       'Z06':{'symbol':'BTC','side':'long','events':[{'event_id':'e1','sequence':1,'action':'OPEN','quantity':1.,'price':100.},{'event_id':'e2','sequence':2,'action':'FUNDING','funding':.3}]},
       'Z07':{'exposures':[],'new':{'strategy':'demo','symbol':'BTC','direction':'long','stop_risk_usdt':10.,'notional_usdt':100.},'max_total_stop_risk':100.,'max_symbol_notional':10000.},
       'Z08':{'path':risk_file},
       'Z09':{'bar':_candle(),'side':'long','stop':96.,'target':104.},
       'Z10':{'order':{'order_id':'o1','created_at':10,'expires_at':100,'requested':1.},'kind':'FILL','at':20,'quantity':.5},
       'Z11':{'zone':{'zone_id':'z1','side':'demand','low':95.,'high':98.,'born_at':0},'candle':_candle(1)},
       'Z13':{'candles':candles,'rules':[{'field':'close','operator':'>','value':100.}],'decision_at':32*60},
       'Z14':{'state':{'phase':'IDLE'},'candle':_candle(),'is_compressed':True,'compressed_range':[98.,102.]},
       'Z15':{'candles':candles},
       'Z16':{'candles':candles,'lookback':10},
       'Z17':{'previous':_candle(0,c=101),'current':_candle(1,c=99),'level':100.,'side':'long'},
       'Z18':{'prior':{'state':'range','pending':'range','count':0},'trend_strength':.9},
       'Z19':{'values':[float(i+100) for i in range(40)],'window':10},
       'Z20':{'history':[.004,.003,.004,.002,.003,.002,.003,.002,.003,.002]},
       'Z21':{'prev_price':100.,'price':101.,'prev_oi':1000.,'oi':1010.},
       'Z22':{'buy_volume':[4.,7.,3.],'total_volume':[10.,12.,8.]},
       'Z23':{'leader_returns':[0.,1.,0.,-1.,0.,1.,0.],'follower_returns':[0.,0.,1.,0.,-1.,0.,1.],'max_lag':2},
       'Z24':{'price_histories':{'BTC':[100.,101.,102.],'SOL':[50.,49.,55.]},'lookback':2},
       'Z25':{'prices_y':[2.,4.1,6.,8.2,9.9,12.3,14.1],'prices_x':[1.,2.,3.,4.,5.,6.,7.],'latest_y':16.,'latest_x':8.},
       'Z26':{'prices':[100.,101.,102.,103.],'latest':60.},
       'Z27':{'contract':{'model_name':'toy','artifact_sha256':sha,'trained_until':10,'feature_names':['a'],'min_probability':0.6},'artifact':'base64:'+base64.b64encode(artifact).decode(),'available_features':{'a':.3},'at':20},
       'Z28':{'impulse_low':95.,'impulse_high':110.,'side':'long','atr':1.},
       'Z29':{'baseline':[trade],'variant':[{**trade,'net_pnl_usdt':12.}]},
       'Z30':{'raw_pvalue':.03,'trial_count':6},
       'Z31':{'trades':[trade]},
       'Z32':{'features':[{'name':'EMA','observed_at':10,'available_at':11,'source':'test','warmup_required':10,'warmup_available':30}],'decision_at':100},
       'Z33':{'original':[trace],'challenger':[trace]},
       'Z34':{'quote_volume_usdt':100000.,'price':100.,'fraction':.01},
       'Z35':{'trades':[trade]},
       'Z36':{'holdings':[{'strategy':'demo','symbol':'BTC','start':10,'end':20}],'start':0,'end':30},
       'Z37':{'equity':1000.,'floors_and_fractions':[[0.,.01],[1000.,.005]],'hard_cap':100.},
       'Z38':{'original':[trace],'challenger':[trace]},
    }


def run_all() -> dict[str,object]:
    with tempfile.TemporaryDirectory(prefix='ember_spares_examples_') as d:
        path=str(Path(d)/'risk_state.json')
        save_risk_state(path,RiskState('2026-11-01','2026-W44',0.,0.,0,False))
        fixtures=example_inputs(path)
        if {c.id for c in REGISTRY} != set(fixtures):
            raise ValueError('missing coverage of registered component')
        return {cid:invoke(cid,payload) for cid,payload in fixtures.items()}


if __name__=='__main__':
    result=run_all()
    print(json.dumps({'checked':len(result),'components':list(result),'status':'COMPUTATION_ONLY'},ensure_ascii=False))
