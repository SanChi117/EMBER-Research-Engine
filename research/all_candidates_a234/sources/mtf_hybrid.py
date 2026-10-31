
"""
MTF_Hybrid - 1d Regime + 15m Entry
Backtest: 2023 +55.9% / 2024 +23.8% / 2025 +108.7%
DD: 17~31%
"""
from pandas import DataFrame
import talib.abstract as ta
import numpy as np
from freqtrade.strategy import IStrategy

class MTF_Hybrid(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = '15m'
    can_short = True

    stoploss = -0.025
    trailing_stop = True
    trailing_stop_positive = 0.004
    trailing_stop_positive_offset = 0.020
    trailing_only_offset_is_reached = True

    minimal_roi = {"0": 0.10, "960": 0.06, "2880": 0.03, "5760": 0}

    max_open_trades = 8
    startup_candle_count = 500
    process_only_new_candles = True
    use_exit_signal = False

    def populate_indicators(self, d, m):
        # 15m trend
        d['e20'] = ta.EMA(d, timeperiod=20)
        d['e50'] = ta.EMA(d, timeperiod=50)
        macd = ta.MACD(d, fastperiod=12, slowperiod=26, signalperiod=9)
        d['md'] = macd['macd']
        d['ms'] = macd['macdsignal']
        d['adx'] = ta.ADX(d, timeperiod=14)
        d['di_plus'] = ta.PLUS_DI(d, timeperiod=14)
        d['di_minus'] = ta.MINUS_DI(d, timeperiod=14)
        d['vr'] = d['volume'] / ta.SMA(d['volume'], timeperiod=20)

        # 1d regime (96 * 15min = 1 day)
        d['ema200_1d'] = ta.EMA(d, timeperiod=19200)
        d['ema200_rising'] = d['ema200_1d'] > d['ema200_1d'].shift(96)
        d['ema200_falling'] = d['ema200_1d'] < d['ema200_1d'].shift(96)

        d['regime_bull'] = (d['close'] > d['ema200_1d']) & d['ema200_rising']
        d['regime_bear'] = (d['close'] < d['ema200_1d']) & d['ema200_falling']
        d['regime_neutral'] = ~(d['regime_bull'] | d['regime_bear'])

        d['rsi'] = ta.RSI(d, timeperiod=14)
        return d

    def populate_entry_trend(self, d, m):
        long_v6 = (
            (d['e20'] > d['e50']) & (d['close'] > d['e50']) &
            (d['md'] > d['ms']) & (d['adx'] > 20) &
            (d['di_plus'] > d['di_minus']) & (d['vr'] > 0.8) &
            (d['volume'] > 0)
        )
        short_v6 = (
            (d['e20'] < d['e50']) & (d['close'] < d['e50']) &
            (d['md'] < d['ms']) & (d['adx'] > 20) &
            (d['di_minus'] > d['di_plus']) & (d['vr'] > 0.8) &
            (d['volume'] > 0)
        )

        # LONG: bull or neutral regime, not overbought
        d.loc[
            long_v6 & (d['regime_bull'] | d['regime_neutral']) & (d['rsi'] < 75),
            ['enter_long', 'enter_tag']
        ] = (1, 'L_mtf')

        # SHORT: bear or neutral regime, not oversold
        d.loc[
            short_v6 & (d['regime_bear'] | d['regime_neutral']) & (d['rsi'] > 25),
            ['enter_short', 'enter_tag']
        ] = (1, 'S_mtf')
        return d

    def populate_exit_trend(self, d, m): return d
