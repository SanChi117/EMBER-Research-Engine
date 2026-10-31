"""One-call offline integration into EMBER research snapshots.

No new trade execution. Returns exact calculations or explicit BLOCKED evidence.
Unknown data never becomes zero, and future data are never forwarded.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping, Sequence

from .advanced import (UnavailableEvidence,closed,historical_signal_frame,funding_pressure,
                       taker_series,compression_breakout,dislocation_plan,
                       bootstrap_mean_ci,review_source_for_lookahead)
from .binance_feed import BinanceUSDMPublic, SourceUnavailable
from .signals import oi_quadrant,lag_correlations
from .structure import fvg_channel,supertrend,hull_ma
from .extra import detect_patterns,ott_line
from .market import Book,orderbook_imbalance,microprice
from .types import Candle,Evidence


@dataclass(frozen=True)
class Calculation:
    state: str  # CALCULATED | BLOCKED_DATA | UNAVAILABLE | ERROR
    value: Any = None
    reason: str = ''


def _run(action, *args, **kwargs) -> Calculation:
    try:
        return Calculation('CALCULATED', action(*args,**kwargs))
    except (UnavailableEvidence,SourceUnavailable) as exc:
        return Calculation('BLOCKED_DATA',reason=str(exc))
    except (ValueError,TypeError,IndexError,ZeroDivisionError) as exc:
        return Calculation('UNAVAILABLE',reason=str(exc))


def calculate_indicators(candles: Sequence[Candle], *, decision_at:int,
                         funding:Sequence[Evidence]=(),oi:Sequence[Evidence]=(),
                         taker_buy_volumes:Sequence[float]|None=None,
                         book:Book|None=None,
                         lookback:int=20) -> dict[str,Calculation]:
    """Directly usable feature bundle from actual closed USD-M inputs.

    Full signal provenance requires source receipts from the upstream data
    adapter; this computation makes no profit/trade assertions.
    """
    bars=closed(candles,decision_at,1)
    prices=[c.close for c in bars]
    outputs={
        'Z01':_run(historical_signal_frame,bars,funding,oi,decision_at=decision_at,max_age_seconds=86400),
        'Z14':_run(compression_breakout,bars,decision_at=decision_at,lookback=lookback),
        'Z15':_run(detect_patterns,bars,decision_at=decision_at),
        'Z16':_run(fvg_channel,bars,lookback=lookback),
        'Z19':_run(supertrend,bars),
        'Z19.ott':_run(ott_line,prices,period=9),
        'Z20':_run(funding_pressure,funding,decision_at=decision_at),
    }
    if taker_buy_volumes is not None:
        outputs['Z22']=_run(taker_series,candles,taker_buy_volumes,decision_at=decision_at,window=min(lookback,len(bars)))
    else:
        outputs['Z22']=Calculation('BLOCKED_DATA',reason='historical takerBuyBaseAssetVolume required')
    if book is not None:
        if book.available_at>decision_at:
            outputs['Z03']=Calculation('BLOCKED_DATA',reason='future BBO snapshot')
        else:
            outputs['Z03']=_run(lambda:{'imbalance':orderbook_imbalance(book),'microprice':microprice(book),'available_at':book.available_at})
    else:
        outputs['Z03']=Calculation('BLOCKED_DATA',reason='point-in-time book snapshot required')
    if len(bars)>lookback:
        # RSI must be actually computed from closed bars; never substitute 50.
        change=[prices[i]-prices[i-1] for i in range(1,len(prices))]
        if len(change)>=14:
            gains=sum(max(0,x) for x in change[-14:])/14
            losses=sum(max(0,-x) for x in change[-14:])/14
            rsi=100 if losses==0 and gains>0 else 50 if losses==gains==0 else 100-100/(1+gains/losses) if losses>0 else 100
            outputs['Z26']=_run(dislocation_plan,prices[-lookback-1:-1],prices[-1],rsi=rsi)
        else:
            outputs['Z26']=Calculation('BLOCKED_DATA',reason='RSI14 requires 15 closed prices')
    else:
        outputs['Z26']=Calculation('BLOCKED_DATA',reason='insufficient prior SMA/RSI bars')
    if len(oi)>=2 and len(bars)>=2:
        from .advanced import oi_signal
        evidence=[Evidence(b.close_time,b.available_at,b.close,'closed-bar') for b in bars]
        outputs['Z21']=_run(oi_signal,evidence,oi,None,decision_at=decision_at,max_age=86400)
    else:
        outputs['Z21']=Calculation('BLOCKED_DATA',reason='two available OI points required')
    return outputs


def usd_m_snapshot(client: BinanceUSDMPublic, *, symbol:str, interval:str,
                   start_ms:int,end_ms:int,decision_at:int,
                   funding_lag_ms:int,oi_lag_ms:int,
                   oi_period:str='1h',mark_lag_ms:int=1000)->dict[str,Any]:
    """Fetch actual Binance Futures candles, mark, funding and OI, no spot fallback.

    A failure of any required history makes the entire snapshot incomplete.
    OI history is exchange-retention limited; the caller may instead supply
    archived raw records. Live bid/ask must never be backdated.
    """
    errors={}; data={}
    for label,fn in {
        'candles':lambda:client.klines_with_taker(symbol,interval,start_ms,end_ms),
        'mark_candles':lambda:client.klines(symbol,interval,start_ms,end_ms,mark=True,publish_lag_ms=mark_lag_ms),
        'funding':lambda:client.funding(symbol,start_ms,end_ms,publication_lag_ms=funding_lag_ms),
        'oi':lambda:client.oi(symbol,oi_period,start_ms,end_ms,publication_lag_ms=oi_lag_ms),
    }.items():
        try:
            if label=='candles':
                records=[(bar,buy) for bar,buy in fn() if bar.available_at<=decision_at]
                data['candles']=[bar for bar,_ in records]
                data['taker_buy_volumes']=[buy for _,buy in records]
            else:
                data[label]=[x for x in fn() if x.available_at<=decision_at]
            if not data[label]:
                errors[label]='empty or no data available by decision time'
        except (ValueError,SourceUnavailable) as exc:
            errors[label]=str(exc)
    return {'symbol':symbol,'as_of':decision_at,'complete':not errors,'missing':errors,
            'counts':{label:len(rows) for label,rows in data.items()},'data':data}
