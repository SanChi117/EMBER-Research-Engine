"""Dynamic equity portfolio and mandatory kill-switches."""

from __future__ import annotations

from ember.config import EmberConfig
from ember.models import PortfolioState, Trade
from ember.utils import ensure_utc


class PortfolioSimulator:
    def __init__(
        self,
        initial_equity: float,
        config: EmberConfig | None = None,
    ) -> None:
        if initial_equity <= 0:
            raise ValueError("initial_equity must be positive")
        self.config = config or EmberConfig()
        self.state = PortfolioState(
            cash=initial_equity,
            equity=initial_equity,
            peak_equity=initial_equity,
        )
        self._daily_peaks: dict[object, float] = {}
        self._weekly_peaks: dict[str, float] = {}

    def can_open(self) -> bool:
        return not self.state.halted and len(self.state.open_trades) < self.config.max_positions

    def open_trade(self, trade: Trade) -> bool:
        if not self.can_open():
            return False
        self.state.open_trades.append(trade)
        return True

    def close_trade(self, trade: Trade) -> None:
        self.state.open_trades = [item for item in self.state.open_trades if item.id != trade.id]
        if trade.result_r is None or trade.exit_time is None:
            return

        pnl = trade.result_r * trade.risk_amount
        previous_equity = self.state.equity
        exit_time = ensure_utc(trade.exit_time)
        day_key = exit_time.date()
        iso = exit_time.isocalendar()
        week_key = f"{iso.year}-W{iso.week:02d}"
        self._daily_peaks.setdefault(day_key, previous_equity)
        self._weekly_peaks.setdefault(week_key, previous_equity)

        self.state.cash += pnl
        self.state.equity += pnl
        self.state.peak_equity = max(self.state.peak_equity, self.state.equity)
        self.state.closed_trades.append(trade)
        self.state.daily_pnl[day_key] = self.state.daily_pnl.get(day_key, 0.0) + pnl
        self.state.weekly_pnl[week_key] = self.state.weekly_pnl.get(week_key, 0.0) + pnl
        self._daily_peaks[day_key] = max(self._daily_peaks[day_key], self.state.equity)
        self._weekly_peaks[week_key] = max(self._weekly_peaks[week_key], self.state.equity)

        if trade.result_r > 0:
            self.state.consecutive_losses = 0
        else:
            self.state.consecutive_losses += 1
        self._evaluate_halt(day_key, week_key)

    def _evaluate_halt(self, day_key: object, week_key: str) -> None:
        if self.state.halted:
            return
        daily_peak = self._daily_peaks[day_key]
        weekly_peak = self._weekly_peaks[week_key]
        daily_drawdown = (daily_peak - self.state.equity) / daily_peak * 100.0
        weekly_drawdown = (weekly_peak - self.state.equity) / weekly_peak * 100.0
        if daily_drawdown >= self.config.daily_drawdown_stop_pct:
            self._halt(f"daily drawdown reached {daily_drawdown:.2f}%")
        elif weekly_drawdown >= self.config.weekly_drawdown_stop_pct:
            self._halt(f"weekly drawdown reached {weekly_drawdown:.2f}%")
        elif self.state.consecutive_losses >= self.config.consecutive_loss_stop:
            self._halt(f"{self.state.consecutive_losses} consecutive losses")

    def _halt(self, reason: str) -> None:
        self.state.halted = True
        self.state.halt_reason = reason
