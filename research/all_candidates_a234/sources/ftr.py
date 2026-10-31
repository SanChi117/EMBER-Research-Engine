import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy

try:
    from freqtrade.strategy import BoolParameter
except ImportError:  # Backward compatibility for older Freqtrade versions
    from freqtrade.strategy import CategoricalParameter

    class BoolParameter(CategoricalParameter):
        def __init__(self, default: bool = False, **kwargs):
            super().__init__([True, False], default=default, **kwargs)

logger = logging.getLogger(__name__)


class FailureToReturnStrategy(IStrategy):
    """
    Failure to Return (FTR) strategy - breakout, failed pullback, continuation

    Designed for trend continuation when price breaks a prior swing level,
    pulls back but fails to return below the breakout level, and then re-engulfs.
    Especially suitable for Forex pairs with clean structure.
    """

    INTERFACE_VERSION = 3

    # Optimizable parameters
    sr_lookback = IntParameter(20, 80, default=40, space="buy", optimize=True)
    pullback_lookback = IntParameter(3, 12, default=6, space="buy", optimize=True)
    impulse_atr = DecimalParameter(0.8, 2.0, default=1.2, space="buy", optimize=True)
    impulse_body_atr = DecimalParameter(0.6, 1.5, default=0.9, space="buy", optimize=True)
    pullback_atr = DecimalParameter(0.1, 0.8, default=0.3, space="buy", optimize=True)
    fail_atr = DecimalParameter(0.1, 0.8, default=0.2, space="buy", optimize=True)
    reengulf_atr = DecimalParameter(0.1, 0.8, default=0.25, space="buy", optimize=True)
    volume_factor = DecimalParameter(0.8, 2.0, default=1.0, space="buy", optimize=True)
    min_atr_ratio = DecimalParameter(0.0003, 0.005, default=0.001, space="buy", optimize=True)

    use_session_filter = BoolParameter(default=True, space="buy", optimize=True)
    london_start_hour = IntParameter(6, 9, default=7, space="buy", optimize=True)
    london_end_hour = IntParameter(15, 18, default=16, space="buy", optimize=True)
    ny_start_hour = IntParameter(11, 14, default=12, space="buy", optimize=True)
    ny_end_hour = IntParameter(20, 23, default=21, space="buy", optimize=True)
    use_daily_profit_guard = BoolParameter(default=True, space="buy", optimize=True)
    daily_profit_target = DecimalParameter(0.005, 0.05, default=0.02, space="buy", optimize=True)

    # Fixed parameters
    timeframe = "1h"
    stoploss = -0.08
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 200
    can_short = False

    minimal_roi = {
        "0": 0.04,
        "240": 0.03,
        "720": 0.01
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        lookback = int(self.sr_lookback.value)
        pullback_window = int(self.pullback_lookback.value)

        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["volume_sma"] = dataframe["volume"].rolling(window=20).mean()

        dataframe["swing_high"] = dataframe["high"].rolling(lookback).max().shift(1)
        dataframe["swing_low"] = dataframe["low"].rolling(lookback).min().shift(1)
        body = (dataframe["close"] - dataframe["open"]).abs()

        dataframe["impulse"] = (
            (dataframe["close"] > dataframe["swing_high"] + dataframe["atr"] * self.impulse_atr.value) &
            (body > dataframe["atr"] * self.impulse_body_atr.value)
        )
        dataframe["impulse_short"] = (
            (dataframe["close"] < dataframe["swing_low"] - dataframe["atr"] * self.impulse_atr.value) &
            (body > dataframe["atr"] * self.impulse_body_atr.value)
        )

        dataframe["impulse_level"] = dataframe["swing_high"].where(dataframe["impulse"]).ffill(
            limit=pullback_window
        )
        dataframe["impulse_level_short"] = dataframe["swing_low"].where(dataframe["impulse_short"]).ffill(
            limit=pullback_window
        )
        dataframe["recent_impulse"] = dataframe["impulse_level"].notna()
        dataframe["recent_impulse_short"] = dataframe["impulse_level_short"].notna()

        dataframe["pullback_zone"] = (
            dataframe["recent_impulse"] &
            (dataframe["low"] <= dataframe["impulse_level"] + dataframe["atr"] * self.pullback_atr.value) &
            (dataframe["low"] >= dataframe["impulse_level"] - dataframe["atr"] * self.fail_atr.value)
        )
        dataframe["pullback_zone_short"] = (
            dataframe["recent_impulse_short"] &
            (dataframe["high"] >= dataframe["impulse_level_short"] - dataframe["atr"] * self.pullback_atr.value) &
            (dataframe["high"] <= dataframe["impulse_level_short"] + dataframe["atr"] * self.fail_atr.value)
        )

        dataframe["pullback_recent"] = (
            dataframe["pullback_zone"]
            .shift(1)
            .rolling(window=pullback_window)
            .max()
            .fillna(0)
            .astype(bool)
        )
        dataframe["pullback_recent_short"] = (
            dataframe["pullback_zone_short"]
            .shift(1)
            .rolling(window=pullback_window)
            .max()
            .fillna(0)
            .astype(bool)
        )

        dataframe["reengulf"] = (
            dataframe["recent_impulse"] &
            (dataframe["close"] > dataframe["impulse_level"] + dataframe["atr"] * self.reengulf_atr.value)
        )
        dataframe["reengulf_short"] = (
            dataframe["recent_impulse_short"] &
            (dataframe["close"] < dataframe["impulse_level_short"] - dataframe["atr"] * self.reengulf_atr.value)
        )

        dataframe["atr_ratio"] = dataframe["atr"] / dataframe["close"]
        dataframe["liquid_session"] = self._is_liquid_session(dataframe)

        return dataframe

    def _is_liquid_session(self, dataframe: DataFrame) -> pd.Series:
        dates = pd.to_datetime(dataframe["date"], utc=True, errors="coerce")
        hours = dates.dt.hour

        london = (hours >= int(self.london_start_hour.value)) & (hours < int(self.london_end_hour.value))
        new_york = (hours >= int(self.ny_start_hour.value)) & (hours < int(self.ny_end_hour.value))

        return (london | new_york).fillna(False)

    def _daily_profit_ratio(self, now: Optional[datetime] = None) -> float:
        if now is None:
            now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        trades = Trade.get_trades_proxy(is_open=False, close_date=start)
        profit = 0.0
        for trade in trades:
            if trade.close_date_utc and trade.close_date_utc >= start:
                profit += float(trade.close_profit or 0.0)

        return profit

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        trend_ok = (dataframe["close"] > dataframe["ema_slow"]) & (dataframe["ema_fast"] > dataframe["ema_slow"])
        trend_ok_short = (dataframe["close"] < dataframe["ema_slow"]) & (dataframe["ema_fast"] < dataframe["ema_slow"])
        volume_ok = (dataframe["volume"] > dataframe["volume_sma"] * self.volume_factor.value) & (
            dataframe["volume"] > 0
        )
        volatility_ok = dataframe["atr_ratio"] >= self.min_atr_ratio.value
        session_ok = (~self.use_session_filter.value) | dataframe["liquid_session"]

        dataframe.loc[
            (
                trend_ok &
                volume_ok &
                volatility_ok &
                session_ok &
                dataframe["pullback_recent"] &
                dataframe["reengulf"]
            ),
            "enter_long"
        ] = 1

        dataframe.loc[
            (
                trend_ok_short &
                volume_ok &
                volatility_ok &
                session_ok &
                dataframe["pullback_recent_short"] &
                dataframe["reengulf_short"]
            ),
            "enter_short"
        ] = 1

        return dataframe

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time: datetime,
        entry_tag: Optional[str],
        side: str,
        **kwargs
    ) -> bool:
        if not self.use_daily_profit_guard.value:
            return True

        daily_profit = self._daily_profit_ratio(current_time)
        if daily_profit >= float(self.daily_profit_target.value):
            return False

        return True

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                ((dataframe["close"] < dataframe["ema_fast"]) &
                 (dataframe["close"].shift(1) >= dataframe["ema_fast"].shift(1))) |
                (dataframe["close"] < dataframe["ema_slow"])
            ),
            "exit_long"
        ] = 1

        dataframe.loc[
            (
                ((dataframe["close"] > dataframe["ema_fast"]) &
                 (dataframe["close"].shift(1) <= dataframe["ema_fast"].shift(1))) |
                (dataframe["close"] > dataframe["ema_slow"])
            ),
            "exit_short"
        ] = 1

        return dataframe
