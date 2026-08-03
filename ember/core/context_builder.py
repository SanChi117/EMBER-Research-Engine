"""Multi-timeframe context construction using data available at entry time only."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

import polars as pl

from ember.config import EmberConfig
from ember.core.features import FeatureBuilder
from ember.models import MTFContext
from ember.utils import bounded, ensure_utc


class ContextBuilder:
    def __init__(self, config: EmberConfig | None = None) -> None:
        self.config = config or EmberConfig()
        self.feature_builder = FeatureBuilder(self.config)

    def build_at(
        self,
        symbol: str,
        entry_time: datetime,
        entry_row: Mapping[str, Any],
        htf_frames: Mapping[str, pl.DataFrame | pl.LazyFrame],
    ) -> MTFContext:
        """Build context from HTF bars whose timestamp is <= ``entry_time``."""

        entry_time = ensure_utc(entry_time)
        selected = self._select_htf(symbol, entry_time, htf_frames)
        rows = selected.to_dicts()
        if not rows:
            return self._neutral_context(symbol, entry_time, entry_row)

        closes = [float(row["close"]) for row in rows]
        ema20 = self._ema(closes, span=20)
        last_close = closes[-1]
        if last_close > ema20 * 1.02:
            bias = "bull"
        elif last_close < ema20 * 0.98:
            bias = "bear"
        else:
            bias = "neutral"

        structure = self._structure(rows)
        volatility = str(rows[-1].get("volatility_regime") or "normal")
        if volatility == "high":
            regime = "high_vol"
        elif structure == "consolidation":
            regime = "range"
        elif volatility == "low":
            regime = "low_vol"
        else:
            regime = "trend"

        liquidity_swept = self._liquidity_swept(rows)
        poi_active = self._poi_active(rows)
        opposite_liquidity = self._opposite_liquidity(rows, bias)

        return MTFContext(
            symbol=symbol,
            time=entry_time,
            bias=bias,
            regime=regime,
            pda_position=bounded(float(entry_row.get("pda_position", 0.5)), 0.0, 1.0),
            session=self._session(entry_row, entry_time),
            htf_liquidity_swept=liquidity_swept,
            htf_poi_active=poi_active,
            htf_structure=structure,
            volume_ratio=max(0.0, float(entry_row.get("volume_ratio", 0.0))),
            atr=max(0.0, float(entry_row.get("atr", 0.0))),
            opposite_htf_liquidity=opposite_liquidity,
        )

    def _select_htf(
        self,
        symbol: str,
        entry_time: datetime,
        htf_frames: Mapping[str, pl.DataFrame | pl.LazyFrame],
    ) -> pl.DataFrame:
        # 4H is the preferred context, then 1D as specified.
        preference = ("4h", "1d")
        fallback = tuple(tf for tf in self.config.context_tfs if tf not in preference)
        for timeframe in (*preference, *fallback):
            source = htf_frames.get(timeframe)
            if source is None:
                continue
            lazy = source.lazy() if isinstance(source, pl.DataFrame) else source
            names = lazy.collect_schema().names()
            if "atr" not in names:
                lazy = self.feature_builder.add_features(lazy)
            frame = (
                lazy.filter(
                    (pl.col("symbol") == symbol.upper())
                    & (pl.col("time") <= pl.lit(entry_time))
                )
                .sort("time")
                .collect()
            )
            if frame.height:
                return frame
        return pl.DataFrame()

    @staticmethod
    def _ema(values: list[float], span: int) -> float:
        if not values:
            return 0.0
        alpha = 2.0 / (span + 1.0)
        ema = values[0]
        for value in values[1:]:
            ema = alpha * value + (1.0 - alpha) * ema
        return ema

    @staticmethod
    def _structure(rows: list[dict[str, Any]]) -> str:
        highs = [
            float(row["swing_high_price"])
            for row in rows
            if row.get("swing_high") and row.get("swing_high_price") is not None
        ]
        lows = [
            float(row["swing_low_price"])
            for row in rows
            if row.get("swing_low") and row.get("swing_low_price") is not None
        ]
        if len(highs) < 2 or len(lows) < 2:
            return "consolidation"
        if highs[-1] > highs[-2] and lows[-1] > lows[-2]:
            return "uptrend"
        if highs[-1] < highs[-2] and lows[-1] < lows[-2]:
            return "downtrend"
        return "consolidation"

    @staticmethod
    def _liquidity_swept(rows: list[dict[str, Any]]) -> bool:
        recent = rows[-10:]
        history = rows[:-10] if len(rows) > 10 else rows[:-1]
        swing_highs = [
            float(row["swing_high_price"])
            for row in history
            if row.get("swing_high_price") is not None
        ]
        swing_lows = [
            float(row["swing_low_price"])
            for row in history
            if row.get("swing_low_price") is not None
        ]
        last_high = swing_highs[-1] if swing_highs else None
        last_low = swing_lows[-1] if swing_lows else None
        for row in recent:
            if last_low is not None and float(row["low"]) < last_low < float(row["close"]):
                return True
            if last_high is not None and float(row["high"]) > last_high > float(row["close"]):
                return True
        return False

    @staticmethod
    def _poi_active(rows: list[dict[str, Any]]) -> bool:
        for row in rows[-50:]:
            fvg_active = row.get("active_fvg_type") is not None and not bool(
                row.get("fvg_mitigated", False)
            )
            order_block_active = row.get("order_block") is not None
            if fvg_active or order_block_active:
                return True
        return False

    @staticmethod
    def _opposite_liquidity(rows: list[dict[str, Any]], bias: str) -> float | None:
        if bias == "bull":
            levels = [
                float(row["swing_high_price"])
                for row in rows
                if row.get("swing_high_price") is not None
            ]
        elif bias == "bear":
            levels = [
                float(row["swing_low_price"])
                for row in rows
                if row.get("swing_low_price") is not None
            ]
        else:
            return None
        return levels[-1] if levels else None

    @staticmethod
    def _session(
        entry_row: Mapping[str, Any],
        entry_time: datetime,
    ) -> str:
        explicit = entry_row.get("session")
        if explicit in {"asia", "london", "ny"}:
            return str(explicit)
        hour = ensure_utc(entry_time).hour
        if hour < 8:
            return "asia"
        if hour < 16:
            return "london"
        return "ny"

    @staticmethod
    def _neutral_context(
        symbol: str,
        entry_time: datetime,
        entry_row: Mapping[str, Any],
    ) -> MTFContext:
        return MTFContext(
            symbol=symbol,
            time=entry_time,
            bias="neutral",
            regime="range",
            pda_position=bounded(float(entry_row.get("pda_position", 0.5)), 0.0, 1.0),
            session=ContextBuilder._session(entry_row, entry_time),
            htf_liquidity_swept=False,
            htf_poi_active=False,
            htf_structure="consolidation",
            volume_ratio=max(0.0, float(entry_row.get("volume_ratio", 0.0))),
            atr=max(0.0, float(entry_row.get("atr", 0.0))),
            opposite_htf_liquidity=None,
        )
