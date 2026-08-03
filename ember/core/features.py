"""Polars-native, past-only market and SMC feature construction."""

from __future__ import annotations

import polars as pl

from ember.config import EmberConfig
from ember.core.data_engine import DataEngine


class FeatureBuilder:
    """Build deterministic features without reading bars after the current row."""

    def __init__(self, config: EmberConfig | None = None) -> None:
        self.config = config or EmberConfig()

    def add_features(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        lf = DataEngine.validate(lf).sort(["symbol", "time"])
        symbol = "symbol"

        previous_close = pl.col("close").shift(1).over(symbol)
        true_range = pl.max_horizontal(
            pl.col("high") - pl.col("low"),
            (pl.col("high") - previous_close).abs(),
            (pl.col("low") - previous_close).abs(),
        )
        body = (pl.col("close") - pl.col("open")).abs()

        lf = lf.with_columns(
            true_range.alias("true_range"),
            body.alias("body"),
            pl.col("volume")
            .rolling_mean(window_size=20, min_samples=1)
            .over(symbol)
            .alias("avg_volume_20"),
            body.rolling_mean(window_size=20, min_samples=1)
            .over(symbol)
            .alias("avg_body_20"),
        ).with_columns(
            pl.col("true_range")
            .rolling_mean(window_size=self.config.atr_period, min_samples=1)
            .over(symbol)
            .alias("atr"),
            pl.when(pl.col("avg_volume_20") > 0)
            .then(pl.col("volume") / pl.col("avg_volume_20"))
            .otherwise(0.0)
            .alias("volume_ratio"),
        )

        # A pivot at i is confirmed only on i+2. The event is therefore emitted on the
        # confirmation bar and carries the pivot price in a separate column.
        high = pl.col("high")
        low = pl.col("low")
        swing_high = (
            (high.shift(2).over(symbol) > high.shift(1).over(symbol))
            & (high.shift(2).over(symbol) > high.shift(3).over(symbol))
            & (high.shift(2).over(symbol) >= high.over(symbol))
            & (high.shift(2).over(symbol) >= high.shift(4).over(symbol))
        )
        swing_low = (
            (low.shift(2).over(symbol) < low.shift(1).over(symbol))
            & (low.shift(2).over(symbol) < low.shift(3).over(symbol))
            & (low.shift(2).over(symbol) <= low.over(symbol))
            & (low.shift(2).over(symbol) <= low.shift(4).over(symbol))
        )
        lf = lf.with_columns(
            swing_high.fill_null(False).alias("swing_high"),
            swing_low.fill_null(False).alias("swing_low"),
        ).with_columns(
            pl.when(pl.col("swing_high"))
            .then(pl.col("high").shift(2).over(symbol))
            .otherwise(None)
            .alias("swing_high_price"),
            pl.when(pl.col("swing_low"))
            .then(pl.col("low").shift(2).over(symbol))
            .otherwise(None)
            .alias("swing_low_price"),
        )

        lf = lf.with_columns(
            pl.col("swing_high_price")
            .forward_fill()
            .over(symbol)
            .shift(1)
            .over(symbol)
            .alias("last_swing_high"),
            pl.col("swing_low_price")
            .forward_fill()
            .over(symbol)
            .shift(1)
            .over(symbol)
            .alias("last_swing_low"),
        ).with_columns(
            (
                pl.col("last_swing_high").is_not_null()
                & (pl.col("close") > pl.col("last_swing_high") + pl.col("atr") * 0.3)
            ).alias("bull_break"),
            (
                pl.col("last_swing_low").is_not_null()
                & (pl.col("close") < pl.col("last_swing_low") - pl.col("atr") * 0.3)
            ).alias("bear_break"),
        )

        lf = lf.with_columns(
            pl.when(pl.col("bull_break"))
            .then(pl.lit("bull"))
            .when(pl.col("bear_break"))
            .then(pl.lit("bear"))
            .otherwise(pl.lit(None, dtype=pl.String))
            .alias("break_direction")
        ).with_columns(
            pl.col("break_direction")
            .forward_fill()
            .over(symbol)
            .shift(1)
            .over(symbol)
            .alias("previous_break_direction")
        ).with_columns(
            pl.when(pl.col("bull_break") & (pl.col("previous_break_direction") == "bear"))
            .then(pl.lit("bull_choch"))
            .when(pl.col("bear_break") & (pl.col("previous_break_direction") == "bull"))
            .then(pl.lit("bear_choch"))
            .when(pl.col("bull_break"))
            .then(pl.lit("bull_bos"))
            .when(pl.col("bear_break"))
            .then(pl.lit("bear_bos"))
            .otherwise(pl.lit(None, dtype=pl.String))
            .alias("bos_choch")
        )

        bull_fvg = (
            pl.col("low") - pl.col("high").shift(2).over(symbol) > pl.col("atr") * 0.15
        )
        bear_fvg = (
            pl.col("low").shift(2).over(symbol) - pl.col("high") > pl.col("atr") * 0.15
        )
        lf = lf.with_columns(
            pl.when(bull_fvg)
            .then(pl.lit("bull_fvg"))
            .when(bear_fvg)
            .then(pl.lit("bear_fvg"))
            .otherwise(pl.lit(None, dtype=pl.String))
            .alias("fvg"),
            pl.when(bull_fvg)
            .then(pl.col("high").shift(2).over(symbol))
            .when(bear_fvg)
            .then(pl.col("high"))
            .otherwise(None)
            .alias("fvg_lower"),
            pl.when(bull_fvg)
            .then(pl.col("low"))
            .when(bear_fvg)
            .then(pl.col("low").shift(2).over(symbol))
            .otherwise(None)
            .alias("fvg_upper"),
            pl.col("time").cum_count().over(symbol).cast(pl.Int64).alias("row_number"),
        ).with_columns(
            pl.when(pl.col("fvg").is_not_null())
            .then(pl.col("row_number"))
            .otherwise(None)
            .forward_fill()
            .over(symbol)
            .alias("latest_fvg_row"),
            pl.col("fvg").forward_fill().over(symbol).alias("active_fvg_type"),
            pl.col("fvg_lower").forward_fill().over(symbol).alias("active_fvg_lower"),
            pl.col("fvg_upper").forward_fill().over(symbol).alias("active_fvg_upper"),
        ).with_columns(
            (pl.col("row_number") - pl.col("latest_fvg_row"))
            .fill_null(0)
            .cast(pl.Int64)
            .alias("fvg_age"),
            pl.when(
                (pl.col("row_number") > pl.col("latest_fvg_row"))
                & (
                    ((pl.col("active_fvg_type") == "bull_fvg")
                     & (pl.col("low") <= pl.col("active_fvg_upper")))
                    | ((pl.col("active_fvg_type") == "bear_fvg")
                       & (pl.col("high") >= pl.col("active_fvg_lower")))
                )
            )
            .then(True)
            .otherwise(False)
            .alias("fvg_mitigated"),
        )

        previous_bearish = pl.col("close").shift(1).over(symbol) < pl.col("open").shift(1).over(symbol)
        previous_bullish = pl.col("close").shift(1).over(symbol) > pl.col("open").shift(1).over(symbol)
        previous_large_body = (
            pl.col("body").shift(1).over(symbol)
            > pl.col("avg_body_20").shift(1).over(symbol) * 1.5
        )
        lf = lf.with_columns(
            pl.when(pl.col("bull_break") & previous_bearish & previous_large_body)
            .then(pl.lit("bull_ob"))
            .when(pl.col("bear_break") & previous_bullish & previous_large_body)
            .then(pl.lit("bear_ob"))
            .otherwise(pl.lit(None, dtype=pl.String))
            .alias("order_block"),
            pl.when(pl.col("bull_break") & previous_bearish & previous_large_body)
            .then(pl.col("low").shift(1).over(symbol))
            .when(pl.col("bear_break") & previous_bullish & previous_large_body)
            .then(pl.col("low").shift(1).over(symbol))
            .otherwise(None)
            .alias("ob_low"),
            pl.when(pl.col("bull_break") & previous_bearish & previous_large_body)
            .then(pl.col("high").shift(1).over(symbol))
            .when(pl.col("bear_break") & previous_bullish & previous_large_body)
            .then(pl.col("high").shift(1).over(symbol))
            .otherwise(None)
            .alias("ob_high"),
        )

        lf = lf.with_columns(
            pl.col("atr")
            .rolling_mean(window_size=20, min_samples=1)
            .over(symbol)
            .alias("atr_sma_20"),
            pl.col("low")
            .rolling_min(window_size=50, min_samples=1)
            .over(symbol)
            .alias("rolling_min_low_50"),
            pl.col("high")
            .rolling_max(window_size=50, min_samples=1)
            .over(symbol)
            .alias("rolling_max_high_50"),
        ).with_columns(
            pl.when(pl.col("atr_sma_20") > 0)
            .then(pl.col("atr") / pl.col("atr_sma_20"))
            .otherwise(1.0)
            .alias("atr_regime_ratio"),
            pl.when(pl.col("rolling_max_high_50") > pl.col("rolling_min_low_50"))
            .then(
                (pl.col("close") - pl.col("rolling_min_low_50"))
                / (pl.col("rolling_max_high_50") - pl.col("rolling_min_low_50"))
            )
            .otherwise(0.5)
            .clip(0.0, 1.0)
            .alias("pda_position"),
        ).with_columns(
            pl.when(pl.col("atr_regime_ratio") > 1.5)
            .then(pl.lit("high"))
            .when(pl.col("atr_regime_ratio") < 0.7)
            .then(pl.lit("low"))
            .otherwise(pl.lit("normal"))
            .alias("volatility_regime"),
            pl.when(pl.col("time").dt.hour() < 8)
            .then(pl.lit("asia"))
            .when(pl.col("time").dt.hour() < 16)
            .then(pl.lit("london"))
            .otherwise(pl.lit("ny"))
            .alias("session"),
        )

        return lf.drop(
            [
                "row_number",
                "latest_fvg_row",
                "previous_break_direction",
                "break_direction",
            ]
        )
