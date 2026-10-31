"""Z02/Z05/Z06/Z07/Z08/Z37. Offline accounting; no broker adapter.

Quantities, prices and USDT balances are floating-point research estimates.
Do not use this standalone engine to calculate an exchange liquidation price;
Binance has dynamic margin tiers, fees, closeout and account-level rules.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from pathlib import Path
import json
import os
import tempfile
from typing import Iterable, Mapping, Sequence

from .types import finite, positive


@dataclass(frozen=True)
class MarginTier:
    notional_floor: float
    notional_ceiling: float
    maintenance_rate: float
    cumulative_deduction: float = 0.0

    def __post_init__(self) -> None:
        finite(self.notional_floor, self.notional_ceiling, self.maintenance_rate, self.cumulative_deduction)
        if not (0 <= self.notional_floor < self.notional_ceiling) or not (0 <= self.maintenance_rate < 1) or self.cumulative_deduction < 0:
            raise ValueError("bad maintenance tier")


def maintenance_required(notional: float, tiers: Sequence[MarginTier]) -> float:
    positive(notional)
    ordered = sorted(tiers, key=lambda t: t.notional_floor)
    if not ordered or ordered[0].notional_floor != 0:
        raise ValueError("complete tiers are required")
    for i in range(1, len(ordered)):
        if ordered[i - 1].notional_ceiling != ordered[i].notional_floor:
            raise ValueError("tier gap/overlap")
    matching = next((t for t in ordered if t.notional_floor <= notional < t.notional_ceiling), None)
    if matching is None:
        raise ValueError("notional outside supplied tiers")
    result = notional * matching.maintenance_rate - matching.cumulative_deduction
    if result < 0:
        raise ValueError("negative maintenance margin from inconsistent tiers")
    return result


@dataclass(frozen=True)
class IsolatedMargin:
    side: str
    quantity: float
    entry_price: float
    mark_price: float
    collateral_usdt: float
    accrued_funding_usdt: float = 0.0   # signed expense: positive is paid
    close_fee_reserve_usdt: float = 0.0

    def __post_init__(self) -> None:
        if self.side not in ("long", "short"):
            raise ValueError("side")
        positive(self.quantity, self.entry_price, self.mark_price)
        finite(self.collateral_usdt, self.accrued_funding_usdt, self.close_fee_reserve_usdt)
        if self.collateral_usdt < 0 or self.close_fee_reserve_usdt < 0:
            raise ValueError("negative balance")


def unrealised_pnl(p: IsolatedMargin) -> float:
    sign = 1 if p.side == "long" else -1
    return sign * p.quantity * (p.mark_price - p.entry_price)


def margin_state(p: IsolatedMargin, tiers: Sequence[MarginTier]) -> dict[str, float | bool]:
    """Tier-aware margin health at a supplied mark, NOT exchange liquidation order.

    Excludes ADL, cross-margin transfers, automatic asset conversion and all
    unprovided fees/tier updates. Caller must supply accurate mark and tiers.
    """
    maintenance = maintenance_required(p.quantity * p.mark_price, tiers)
    equity = p.collateral_usdt + unrealised_pnl(p) - p.accrued_funding_usdt - p.close_fee_reserve_usdt
    return {"equity": equity, "maintenance": maintenance, "below_maintenance": equity <= maintenance, "notional": p.quantity * p.mark_price}


@dataclass(frozen=True)
class Leg:
    asset: str
    side: str
    quantity: float
    entry_price: float
    mark_price: float
    fee_usdt: float = 0.0
    funding_usdt: float = 0.0  # signed expense

    def __post_init__(self) -> None:
        if self.side not in ("long", "short") or not self.asset:
            raise ValueError("invalid leg")
        positive(self.quantity, self.entry_price, self.mark_price)
        finite(self.fee_usdt, self.funding_usdt)
        if self.fee_usdt < 0:
            raise ValueError("negative fee")


def multileg_pnl(legs: Sequence[Leg]) -> dict[str, float]:
    """Compute signed leg PnL, including both legs' fees/funding; no atomic fill assumptions."""
    if not legs:
        raise ValueError("no legs")
    gross = sum((1 if x.side == "long" else -1) * x.quantity * (x.mark_price - x.entry_price) for x in legs)
    fees = sum(x.fee_usdt for x in legs)
    funding = sum(x.funding_usdt for x in legs)
    # net exposure in USDT differs from beta-neutrality/cointegration neutrality.
    signed_notional = sum((1 if x.side == "long" else -1) * x.quantity * x.mark_price for x in legs)
    return {"gross_usdt": gross, "fees_usdt": fees, "funding_usdt": funding,
            "net_usdt": gross - fees - funding, "signed_notional_usdt": signed_notional}


@dataclass(frozen=True)
class Position:
    """One-way net position, no shorting with a signed quantity."""
    symbol: str
    side: str
    quantity: float
    avg_entry: float
    realised_pnl: float = 0.0
    paid_fees: float = 0.0
    paid_funding: float = 0.0

    def __post_init__(self) -> None:
        if not self.symbol or self.side not in ("long", "short"):
            raise ValueError("invalid position")
        finite(self.quantity, self.avg_entry, self.realised_pnl, self.paid_fees, self.paid_funding)
        if self.quantity < 0 or self.avg_entry < 0 or self.paid_fees < 0:
            raise ValueError("invalid position quantities")
        if self.quantity > 0 and self.avg_entry == 0:
            raise ValueError("average entry missing")


@dataclass(frozen=True)
class CashEvent:
    event_id: str
    sequence: int
    action: str  # OPEN | ADD | REDUCE | FUNDING
    quantity: float = 0.0
    price: float = 0.0
    fee: float = 0.0
    funding: float = 0.0  # positive cost, negative credit

    def __post_init__(self) -> None:
        if not self.event_id or self.sequence < 0 or self.action not in ("OPEN", "ADD", "REDUCE", "FUNDING"):
            raise ValueError("bad event")
        finite(self.quantity, self.price, self.fee, self.funding)
        if self.quantity < 0 or self.price < 0 or self.fee < 0:
            raise ValueError("negative quantity, price, fee")
        if self.action in ("OPEN", "ADD", "REDUCE") and (self.quantity == 0 or self.price == 0):
            raise ValueError("missing fill")
        if self.action == "FUNDING" and self.quantity != 0:
            raise ValueError("funding is not a fill")


def replay_cash_events(symbol: str, side: str, events: Iterable[CashEvent]) -> Position:
    """Deterministic replay. Enforces unique IDs, increasing sequence, no oversell."""
    p = Position(symbol, side, 0.0, 0.0)
    last_sequence = -1
    seen: set[str] = set()
    for event in events:
        if event.event_id in seen or event.sequence <= last_sequence:
            raise ValueError("duplicate/out-of-order event")
        seen.add(event.event_id)
        last_sequence = event.sequence
        if event.action in ("OPEN", "ADD"):
            if p.quantity == 0:
                avg = event.price
            else:
                avg = (p.avg_entry * p.quantity + event.price * event.quantity) / (p.quantity + event.quantity)
            p = replace(p, quantity=p.quantity + event.quantity, avg_entry=avg,
                        paid_fees=p.paid_fees + event.fee)
        elif event.action == "REDUCE":
            if event.quantity > p.quantity + 1e-10:
                raise ValueError("reduce-only oversell")
            sign = 1 if side == "long" else -1
            pnl = sign * event.quantity * (event.price - p.avg_entry)
            remaining = max(0.0, p.quantity - event.quantity)
            p = replace(p, quantity=remaining, avg_entry=p.avg_entry if remaining else 0.0,
                        realised_pnl=p.realised_pnl + pnl, paid_fees=p.paid_fees + event.fee)
        elif event.action == "FUNDING":
            p = replace(p, paid_funding=p.paid_funding + event.funding)
    return p


@dataclass(frozen=True)
class Exposure:
    strategy: str
    symbol: str
    direction: str
    stop_risk_usdt: float
    notional_usdt: float

    def __post_init__(self) -> None:
        if not self.strategy or not self.symbol or self.direction not in ("long", "short"):
            raise ValueError("invalid exposure")
        finite(self.stop_risk_usdt, self.notional_usdt)
        if self.stop_risk_usdt < 0 or self.notional_usdt < 0:
            raise ValueError("negative exposure")


def portfolio_risk_gate(exposures: Sequence[Exposure], new: Exposure, max_total_stop_risk: float,
                        max_symbol_notional: float) -> tuple[bool, str]:
    """Conservative total stop-risk gate; correlation does not offset risk."""
    positive(max_total_stop_risk, max_symbol_notional)
    if sum(e.stop_risk_usdt for e in exposures) + new.stop_risk_usdt > max_total_stop_risk:
        return False, "STOP_RISK_BUDGET"
    if sum(e.notional_usdt for e in exposures if e.symbol == new.symbol) + new.notional_usdt > max_symbol_notional:
        return False, "SYMBOL_NOTIONAL_BUDGET"
    return True, "OK"


@dataclass(frozen=True)
class RiskState:
    day: str
    week: str
    daily_loss_usdt: float
    weekly_loss_usdt: float
    consecutive_losses: int
    halted: bool

    def __post_init__(self) -> None:
        if not self.day or not self.week or self.consecutive_losses < 0:
            raise ValueError("invalid risk state")
        finite(self.daily_loss_usdt, self.weekly_loss_usdt)
        if self.daily_loss_usdt < 0 or self.weekly_loss_usdt < 0:
            raise ValueError("loss counter negative")


def update_risk(state: RiskState, pnl_usdt: float, *, day: str, week: str,
                daily_limit: float, weekly_limit: float, max_losses: int) -> RiskState:
    """Once halted, remains halted until an *explicit* external reset.

    This is intentional: a new UTC day or process restart never silently
    clears the protective latch. Use a documented operator reset separately.
    """
    finite(pnl_usdt)
    positive(daily_limit, weekly_limit)
    if max_losses < 1:
        raise ValueError("max_losses")
    daily = 0.0 if day != state.day else state.daily_loss_usdt
    weekly = 0.0 if week != state.week else state.weekly_loss_usdt
    daily = max(0.0, daily - pnl_usdt)
    weekly = max(0.0, weekly - pnl_usdt)
    nloss = state.consecutive_losses + 1 if pnl_usdt < 0 else (0 if pnl_usdt > 0 else state.consecutive_losses)
    return RiskState(day, week, daily, weekly, nloss,
                     state.halted or daily >= daily_limit or weekly >= weekly_limit or nloss >= max_losses)


def save_risk_state(path: str | Path, state: RiskState) -> None:
    """Atomic replacement, local research-only. No host service/restart hooks."""
    from dataclasses import asdict
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".risk-", suffix=".tmp", dir=str(destination.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(asdict(state), f, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, destination)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def load_risk_state(path: str | Path) -> RiskState:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(payload) != {"day", "week", "daily_loss_usdt", "weekly_loss_usdt", "consecutive_losses", "halted"}:
        raise ValueError("unexpected risk state fields")
    if type(payload["halted"]) is not bool:
        raise ValueError("invalid halted flag")
    return RiskState(**payload)


def staircase_risk(equity: float, floors_and_fractions: Sequence[tuple[float, float]], hard_cap: float) -> float:
    """Study-only capital-tier risk amount; never infer leverage/stop from it."""
    positive(equity, hard_cap)
    if not floors_and_fractions:
        raise ValueError("empty risk schedule")
    ordered = sorted(floors_and_fractions)
    if ordered[0][0] != 0:
        raise ValueError("risk schedule must begin at 0")
    for floor, fraction in ordered:
        finite(floor, fraction)
        if floor < 0 or not (0 <= fraction <= 1):
            raise ValueError("invalid risk tier")
    rate = next(rate for floor, rate in reversed(ordered) if equity >= floor)
    return min(hard_cap, equity * rate)
