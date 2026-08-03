"""ATR risk planning, position sizing and mandatory cost gate."""

from __future__ import annotations

from ember.config import EmberConfig
from ember.models import MTFContext, RiskPlan, SetupCandidate


class RiskEngine:
    def __init__(self, config: EmberConfig | None = None) -> None:
        self.config = config or EmberConfig()

    def plan(
        self,
        candidate: SetupCandidate,
        context: MTFContext,
        equity: float,
    ) -> RiskPlan | None:
        plan, _ = self.plan_with_reason(candidate, context, equity)
        return plan

    def plan_with_reason(
        self,
        candidate: SetupCandidate,
        context: MTFContext,
        equity: float,
    ) -> tuple[RiskPlan | None, str | None]:
        """Build a risk plan and expose the exact rejection gate for diagnostics."""

        if equity <= 0 or context.atr <= 0:
            return None, "risk_none"
        entry = float(candidate.trigger_price)
        if entry <= 0:
            return None, "risk_none"

        raw_distance = context.atr * self.config.atr_stop_multiplier
        min_distance = entry * self.config.min_stop_distance_pct / 100.0
        max_distance = entry * self.config.max_stop_distance_pct / 100.0
        risk_distance = max(min_distance, min(max_distance, raw_distance))
        if risk_distance <= 0:
            return None, "risk_none"

        if candidate.side == "long":
            stop = entry - risk_distance
            fixed_target = entry + risk_distance * self.config.min_rr
            target = self._context_target(
                candidate.side,
                fixed_target,
                entry,
                risk_distance,
                context,
            )
        else:
            stop = entry + risk_distance
            fixed_target = entry - risk_distance * self.config.min_rr
            target = self._context_target(
                candidate.side,
                fixed_target,
                entry,
                risk_distance,
                context,
            )

        target_rr = abs(target - entry) / risk_distance
        if target_rr + 1e-12 < self.config.min_rr:
            return None, "rr_low"

        risk_fraction = self.config.risk_per_trade_pct / 100.0
        fee_cost = self.config.fee_rate * 2.0
        slippage_cost = self.config.slippage_rate * 2.0
        net_edge = (target_rr - 1.0) * risk_fraction - (fee_cost + slippage_cost)
        if net_edge <= 0:
            return None, "cost_gate"

        risk_amount = equity * risk_fraction
        position_size = risk_amount / risk_distance
        notional = position_size * entry
        leverage = min(20.0, self.config.leverage)
        margin = notional / leverage
        within_stop_bounds = min_distance <= risk_distance <= max_distance
        if target_rr >= 2.0 and within_stop_bounds:
            grade = "A"
        elif target_rr >= 1.8:
            grade = "B"
        else:
            grade = "C"

        return (
            RiskPlan(
                symbol=candidate.symbol,
                side=candidate.side,
                entry=entry,
                stop=stop,
                target=target,
                target_rr=target_rr,
                risk_amount=risk_amount,
                position_size=position_size,
                notional=notional,
                margin=margin,
                leverage=leverage,
                setup_type=candidate.setup_type,
                entry_time=candidate.time,
                fee_cost=fee_cost,
                slippage_cost=slippage_cost,
                net_edge=net_edge,
                grade=grade,
            ),
            None,
        )

    def _context_target(
        self,
        side: str,
        fixed_target: float,
        entry: float,
        risk_distance: float,
        context: MTFContext,
    ) -> float:
        if self.config.tp_mode != "opposite_htf_liquidity":
            return fixed_target
        liquidity = context.opposite_htf_liquidity
        if liquidity is None:
            return fixed_target
        if side == "long" and liquidity > entry:
            rr = (liquidity - entry) / risk_distance
            return liquidity if rr >= self.config.min_rr else fixed_target
        if side == "short" and liquidity < entry:
            rr = (entry - liquidity) / risk_distance
            return liquidity if rr >= self.config.min_rr else fixed_target
        return fixed_target
