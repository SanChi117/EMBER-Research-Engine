"""One-call read-only Binance USD-M source → research-spares features.

This is a real integration entrypoint. It neither opens/edits positions nor
changes any existing EMBER, SMOKE or PAPER scheduler. It cannot give a price
fill or liquidation proof without genuine exchange evidence.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any
from .binance_feed import BinanceUSDMPublic
from .workflow import usd_m_snapshot,calculate_indicators
from .types import Candle


def run_binance_usdm(*,symbol:str,interval:str,start_ms:int,end_ms:int,decision_at:int,
                     funding_lag_ms:int,oi_lag_ms:int,oi_period:str='1h',
                     client:BinanceUSDMPublic|None=None,lookback:int=20) -> dict[str,Any]:
    """Read-only automated feature computation with per-source explicit blockers.

    Args use UTC epoch milliseconds for range and seconds for decision_at;
    no timezone guessing, historical spot substitutions or magic fill rates.
    """
    client=client or BinanceUSDMPublic()
    source=usd_m_snapshot(client,symbol=symbol,interval=interval,start_ms=start_ms,end_ms=end_ms,
                         decision_at=decision_at,funding_lag_ms=funding_lag_ms,oi_lag_ms=oi_lag_ms,
                         oi_period=oi_period)
    candles=source['data'].get('candles',[])
    if not candles:
        return {'symbol':symbol,'status':'BLOCKED_SOURCE','missing':source['missing'],
                'counts':source['counts'],'features':{}}
    indicators=calculate_indicators(candles,decision_at=decision_at,
                                  funding=source['data'].get('funding',()),
                                  oi=source['data'].get('oi',()),
                                  taker_buy_volumes=source['data'].get('taker_buy_volumes',()),
                                  lookback=lookback)
    return {'symbol':symbol,'status':'SOURCE_COMPLETE' if source['complete'] else 'PARTIAL_SOURCE',
            'missing':source['missing'],'counts':source['counts'],
            'features':{name:asdict(result) for name,result in indicators.items()},
            'no_trade_execution':True}
