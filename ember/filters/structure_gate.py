"""Completed-trade-only structure learning."""

from __future__ import annotations

from datetime import datetime, timedelta

from ember.models import StructureScore, Trade
from ember.utils import bounded, ensure_utc, safe_mean


class StructureGate:
    def completed_trades_before(
        self,
        all_trades: list[Trade],
        entry_time: datetime,
        lookback_days: int = 30,
    ) -> list[Trade]:
        cutoff = ensure_utc(entry_time) - timedelta(days=lookback_days)
        return [
            trade
            for trade in all_trades
            if trade.exit_time is not None
            and ensure_utc(trade.exit_time) < ensure_utc(entry_time)
            and ensure_utc(trade.entry_time) >= cutoff
            and trade.status == "closed"
        ]

    def score(
        self,
        trade_id: int,
        symbol: str,
        setup_type: str,
        side: str,
        regime: str,
        entry_time: datetime,
        all_trades: list[Trade],
        lookback_days: int = 30,
    ) -> StructureScore:
        history = self.completed_trades_before(all_trades, entry_time, lookback_days)
        similar = [
            trade
            for trade in history
            if self.similarity_key(trade.setup_type, trade.side, trade.symbol)
            == self.similarity_key(setup_type, side, symbol)
        ]
        same_regime = [trade for trade in history if trade.regime == regime]

        if similar:
            latest_exit = max(trade.exit_time for trade in similar if trade.exit_time is not None)
            assert latest_exit is not None
            days_old = max(0.0, (ensure_utc(entry_time) - ensure_utc(latest_exit)).total_seconds() / 86400.0)
            recency_score = bounded(100.0 - days_old * 5.0, 0.0, 100.0)
            consistency_score = self._win_rate(similar) * 100.0
        else:
            recency_score = 50.0
            consistency_score = 50.0

        regime_score = self._win_rate(same_regime) * 100.0 if same_regime else 50.0
        composite = recency_score * 0.3 + consistency_score * 0.4 + regime_score * 0.3
        return StructureScore(
            trade_id=trade_id,
            recency_score=recency_score,
            consistency_score=consistency_score,
            regime_score=regime_score,
            composite=composite,
            grade=self._grade(composite),
        )

    @staticmethod
    def similarity_key(setup_type: str, side: str, symbol: str) -> str:
        return f"{setup_type}|{side}|{symbol}"

    @staticmethod
    def _win_rate(trades: list[Trade]) -> float:
        outcomes = [1.0 if (trade.result_r or 0.0) > 0 else 0.0 for trade in trades]
        return safe_mean(outcomes, default=0.5)

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 75:
            return "A"
        if score >= 60:
            return "B"
        if score >= 45:
            return "C"
        return "D"
