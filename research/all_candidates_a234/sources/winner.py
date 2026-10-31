"""
Winning Strategy — 15m Dual EMA+MACD+ROC+ADX
Backtest: 27.6% annual, Sharpe 3.23, 65.8% win rate
All 6 sliding windows profitable
"""
from pandas import DataFrame
import talib.abstract as ta
from freqtrade.strategy import IStrategy

class Winner15m(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = '15m'
    can_short = True

    stoploss = -0.025
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.018
    trailing_only_offset_is_reached = True

    minimal_roi = {"0": 0.08, "480": 0.05, "1440": 0.03, "4320": 0}

    max_open_trades = 10
    startup_candle_count = 200
    process_only_new_candles = True
    use_exit_signal = False

    def populate_indicators(self, d, m):
        d['e10'] = ta.EMA(d, timeperiod=10)
        d['e30'] = ta.EMA(d, timeperiod=30)
        macd = ta.MACD(d, fastperiod=12, slowperiod=26, signalperiod=9)
        d['md'] = macd['macd']
        d['ms'] = macd['macdsignal']
        d['mom'] = ta.ROC(d, timeperiod=3)
        d['adx'] = ta.ADX(d, timeperiod=14)
        d['vr'] = d['volume'] / ta.SMA(d['volume'], timeperiod=20)
        return d

    def populate_entry_trend(self, d, m):
        d.loc[
            (d['e10'] > d['e30']) & (d['md'] > d['ms']) &
            (d['mom'] > 0.1) & (d['adx'] > 18) & (d['vr'] > 1.0) & (d['volume'] > 0),
            ['enter_long', 'enter_tag']
        ] = (1, 'L')

        d.loc[
            (d['e10'] < d['e30']) & (d['md'] < d['ms']) &
            (d['mom'] < -0.1) & (d['adx'] > 18) & (d['vr'] > 1.0) & (d['volume'] > 0),
            ['enter_short', 'enter_tag']
        ] = (1, 'S')
        return d

    def populate_exit_trend(self, d, m):
        return d
