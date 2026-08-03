"""HYBRID v2 setup detection using past data and an entry-time MTF context."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import polars as pl

from ember.config import EmberConfig
from ember.models import MTFContext, SetupCandidate
from ember.utils import bounded, ensure_utc, safe_mean


class SetupDetector:
    def __init__(self, config: EmberConfig | None = None) -> None:
        self.config = config or EmberConfig()

    def detect(
        self,
        past_df: pl.DataFrame,
        context: MTFContext,
    ) -> SetupCandidate | None:
        """Return the best allowed setup from data ending at the candidate bar."""

        if past_df.is_empty():
            return None
        if context.regime in self.config.blocked_volatility_regimes:
            return None
        if not self._direction_allowed(context.bias):
            return None

        candidates = [
            candidate
            for candidate in (
                self._detect_pullback(past_df, context),
                self._detect_ignition(past_df, context),
            )
            if candidate is not None and self._candidate_allowed(candidate, context)
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda candidate: candidate.confidence)

    def _detect_pullback(
        self,
        past_df: pl.DataFrame,
        context: MTFContext,
    ) -> SetupCandidate | None:
        if past_df.height < 6 or context.bias == "neutral" or context.atr <= 0:
            return None
        row = past_df.tail(1).row(0, named=True)
        side = "long" if context.bias == "bull" else "short"
        recent = past_df.tail(6).head(5).to_dicts()
        impulse_found = any(self._aligned_impulse(item, side) for item in recent)
        if not impulse_found:
            return None

        candle_range = float(row["high"]) - float(row["low"])
        if candle_range <= 0:
            return None
        if side == "long":
            location_ok = context.pda_position < 0.4
            rejection = (float(row["close"]) - float(row["low"])) / candle_range > 0.3
            depth = (0.4 - context.pda_position) / 0.4
        else:
            location_ok = context.pda_position > 0.6
            rejection = (float(row["high"]) - float(row["close"])) / candle_range > 0.3
            depth = (context.pda_position - 0.6) / 0.4
        if not location_ok or not rejection or context.volume_ratio < 0.7:
            return None

        confidence = bounded(55.0 + bounded(depth, 0.0, 1.0) * 50.0, 0.0, 100.0)
        return SetupCandidate(
            symbol=str(row["symbol"]),
            time=self._time(row),
            setup_type="pullback",
            side=side,
            confidence=confidence,
            trigger_price=float(row["close"]),
            notes=(
                f"bias={context.bias}; pda={context.pda_position:.3f}; "
                f"rejection=1; volume_ratio={context.volume_ratio:.2f}"
            ),
        )

    def _detect_ignition(
        self,
        past_df: pl.DataFrame,
        context: MTFContext,
    ) -> SetupCandidate | None:
        if past_df.height < 11 or context.bias == "neutral" or context.atr <= 0:
            return None
        rows = past_df.tail(11).to_dicts()
        row = rows[-1]
        prior = rows[:5]
        recent = rows[5:10]
        prior_atr = safe_mean(float(item.get("atr") or 0.0) for item in prior)
        recent_atr = safe_mean(float(item.get("atr") or 0.0) for item in recent)
        if prior_atr <= 0 or not (recent_atr < prior_atr * 0.8):
            return None

        body = abs(float(row["close"]) - float(row["open"]))
        volume_ratio = float(row.get("volume_ratio") or 0.0)
        displacement = body > float(row.get("atr") or context.atr) * 1.5
        side = "long" if float(row["close"]) > float(row["open"]) else "short"
        aligned = (side == "long" and context.bias == "bull") or (
            side == "short" and context.bias == "bear"
        )
        if not displacement or volume_ratio <= 1.3 or not aligned:
            return None

        confidence = bounded(60.0 + (volume_ratio - 1.0) * 20.0, 0.0, 100.0)
        return SetupCandidate(
            symbol=str(row["symbol"]),
            time=self._time(row),
            setup_type="ignition",
            side=side,
            confidence=confidence,
            trigger_price=float(row["close"]),
            notes=(
                f"compression={recent_atr / prior_atr:.3f}; "
                f"body_atr={body / max(context.atr, 1e-12):.2f}; "
                f"volume_ratio={volume_ratio:.2f}"
            ),
        )

    @staticmethod
    def _aligned_impulse(row: dict[str, Any], side: str) -> bool:
        atr = float(row.get("atr") or 0.0)
        if atr <= 0:
            return False
        body = abs(float(row["close"]) - float(row["open"]))
        if side == "long":
            direction_ok = float(row["close"]) > float(row["open"])
        else:
            direction_ok = float(row["close"]) < float(row["open"])
        return direction_ok and body > atr * 1.2

    def _candidate_allowed(
        self,
        candidate: SetupCandidate,
        context: MTFContext,
    ) -> bool:
        return (
            candidate.setup_type in self.config.allowed_setups
            and candidate.setup_type not in self.config.blocked_setups
            and candidate.confidence >= self.config.min_confidence
            and context.volume_ratio >= self.config.min_volume_ratio
        )

    def _direction_allowed(self, bias: str) -> bool:
        normalized = {
            "up": "bull",
            "down": "bear",
            "long": "bull",
            "short": "bear",
        }
        allowed = {normalized.get(value.lower(), value.lower()) for value in self.config.allowed_direction_contexts}
        return bias in allowed

    @staticmethod
    def _time(row: dict[str, Any]) -> datetime:
        value = row["time"]
        if not isinstance(value, datetime):
            raise TypeError("time must be a datetime")
        return ensure_utc(value)
