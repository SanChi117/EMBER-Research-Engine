"""A243: genuine Binance USD-M BTC/ETH original Winner15m prerequisites.
Wrap original A228 SHA-authenticated real kline/mark/funding downloader.
For Freqtrade 2025.11 encode each *actual funding scalar* in six-column
OHLCV-shaped exchange funding candle format (date/rate/rate/rate/rate/zero).
No price imputation, no changes to settlements or original trading logic.
"""
from pathlib import Path
import pandas as pd
from freqtrade.data.history.datahandlers.featherdatahandler import FeatherDataHandler
from freqtrade.enums import CandleType
from research.a228_five_original import a228_prepare_pinned_originals_and_real_futures as base

base.COINS=("BTCUSDT","ETHUSDT")
base.PINS={
 "Winner15m":{
  "repo":"win-boom/BTCquant",
  "commit":"82c6955a15f80196d1e0ae8320b2c41432980b40",
  "path":"user_data/strategies/winner_strat.py",
  "git_blob":"585df3f6198837230816c73fe59957996f45d13a"
 }
}

def store_native_market_2025_11(candles,marks,settlements):
    datadir=base.OUT/"binance"
    (datadir/"futures").mkdir(parents=True,exist_ok=True)
    dh=FeatherDataHandler(datadir)
    sizes={}
    for sym in base.COINS:
        pair=sym.replace("USDT","/USDT:USDT")
        frame=base.to_candle_frame(candles[sym],"5m",sym)
        assert frame.index[0]==pd.Timestamp("2023-11-01T00:00:00Z")
        assert frame.index[-1]==pd.Timestamp("2026-05-31T23:55:00Z")
        for tf in base.TFS:
            data=base.aggregate_5m(frame,tf).reset_index()
            dh.ohlcv_store(pair,tf,data,CandleType.FUTURES)
            sizes[f"{sym}_{tf}"]=len(data)
        markdf=base.to_candle_frame(marks[sym],"8h","mark "+sym).reset_index()
        dh.ohlcv_store(pair,"8h",markdf,CandleType.MARK)
        rates=sorted(settlements[sym])
        if len(rates)!=len({stamp for stamp,_ in rates}):
            raise ValueError("A243_DUPLICATED_REAL_FUNDING")
        timestamps=pd.to_datetime([stamp for stamp,_ in rates],unit="ms",utc=True)
        values=[float(rate) for _,rate in rates]
        fundingdf=pd.DataFrame({"date":timestamps,"open":values,"high":values,
                                "low":values,"close":values,"volume":[0.0]*len(values)})
        assert all((fundingdf["open"]==fundingdf[field]).all() for field in ("high","low","close"))
        dh.ohlcv_store(pair,"8h",fundingdf,CandleType.FUNDING_RATE)
        sizes[f"{sym}_mark_8h"]=len(markdf)
        sizes[f"{sym}_actual_funding"]=len(fundingdf)
    print("A243_FREQTRADE_2025_11_REAL_FUNDING_SCALAR_COMPAT_DATA",sizes,flush=True)
    return sizes

base.store_native_market=store_native_market_2025_11

if __name__=="__main__":
    base.main()
