"""RESET-06: deterministic PAPER-only risk budget proposal, not order permission.

Manual regime has no cryptographic attestation/ledger adapter yet; WINDOW_OPEN
is refused until verified review evidence arrives. Only ladder step 2 is active
until owner-signed gate event integration. This never calls an exchange.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal as D

LADDER = (D("0.02"), D("0.03"), D("0.04"))
BASE_EQUITY = D("920")
KILL_EQUITY = D("736")
MAX_NOTIONAL = D("2760")
MAX_LEVERAGE = D("3")
RATCHET_FLOOR = D("1104")
BONUS_FRACTION = D("0.08")
MAX_DD = D("0.20")
REGIMES = frozenset({"WINDOW_OPEN", "NEUTRAL", "CHOP"})


@dataclass(frozen=True)
class RampVerdict:
    paper_budget_only: bool
    reason: str
    risk_budget_usdt: D
    notional_cap_usdt: D
    trades_per_utc_day: int
    active_ladder_fraction: D
    live_allowed: bool = False


def _fail(reason: str) -> RampVerdict:
    return RampVerdict(False, reason, D("0"), D("0"), 0, LADDER[0])


def _number(value: object) -> D:
    if isinstance(value, bool) or not isinstance(value, (D, str, int)):
        raise ValueError("INVALID_DECIMAL_RAMP_INPUT")
    number = D(value)
    if not number.is_finite() or number < 0:
        raise ValueError("INVALID_DECIMAL_RAMP_INPUT")
    return number


def propose_paper_budget(
    *,
    equity_current: D,
    peak_equity: D,
    requested_ladder_step: int = 2,
    regime_state: str = "NEUTRAL",
    trades_today: int = 0,
    notional_requested: D = D("0"),
    leverage_requested: D = D("1"),
    owner_regime_review_verified: bool = False,
    ladder_gate_verified: bool = False,
    remaining_series_budget_usdt: D | None = None,
) -> RampVerdict:
    """Pure conservative proposal. Always LIVE_BLOCKED; no activation."""

    try:
        equity = _number(equity_current)
        peak = _number(peak_equity)
        nominal = _number(notional_requested)
        leverage = _number(leverage_requested)
        if (
            type(requested_ladder_step) is not int
            or requested_ladder_step not in (2, 3, 4)
            or type(trades_today) is not int or trades_today < 0
            or type(regime_state) is not str or regime_state not in REGIMES
            or type(owner_regime_review_verified) is not bool
            or type(ladder_gate_verified) is not bool
            or peak < equity or leverage == 0
            or (remaining_series_budget_usdt is not None
                and _number(remaining_series_budget_usdt) <= 0)
        ):
            return _fail("INVALID_RAMP_POLICY_OR_SNAPSHOT")
    except (ValueError, TypeError, ArithmeticError):
        return _fail("INVALID_RAMP_INPUT")

    if equity <= KILL_EQUITY:
        return _fail("KILL_EQUITY_REACHED")
    if equity <= peak * (D("1") - MAX_DD):
        return _fail("MAX_DRAWDOWN_REACHED")
    if regime_state == "CHOP":
        return _fail("CHOP_NO_EXECUTION")
    if regime_state == "WINDOW_OPEN" and not owner_regime_review_verified:
        return _fail("WINDOW_OPEN_NEEDS_VERIFIED_WEEKLY_REVIEW")
    if requested_ladder_step > 2 and not ladder_gate_verified:
        return _fail("LADDER_NOT_UNLOCKED")
    if nominal > MAX_NOTIONAL or nominal > equity * MAX_LEVERAGE:
        return _fail("NOTIONAL_CAP_EXCEEDED")
    if leverage > MAX_LEVERAGE:
        return _fail("LEVERAGE_CAP_EXCEEDED")

    max_daily = 3 if regime_state == "WINDOW_OPEN" else 1
    if trades_today >= max_daily:
        return _fail("REGIME_DAILY_TRADE_LIMIT")

    fraction = LADDER[requested_ladder_step - 2]
    base = BASE_EQUITY * fraction
    bonus = BONUS_FRACTION * max(D("0"), equity - RATCHET_FLOOR)
    risk = base + bonus
    if remaining_series_budget_usdt is not None:
        risk = min(risk, _number(remaining_series_budget_usdt))
    # This budget may exceed position-specific risk: real preflight must
    # enforce stop+slippage+fees plus leverage/collateral/nominal again.
    # No gap-through-stop guarantee is supplied by this module.
    return RampVerdict(True, "PAPER_BUDGET_PROPOSAL_ONLY", risk, MAX_NOTIONAL,
                       max_daily, fraction)
