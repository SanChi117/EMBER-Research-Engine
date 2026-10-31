"""Z01, Z03, Z09, Z10: market event validity and execution uncertainty."""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Iterable, Mapping, Sequence

from .types import Candle, Evidence, ascending, finite, positive


def asof_evidence(events: Sequence[Evidence], decision_at: int, max_age: int | None = None) -> Evidence | None:
    """Return latest *available* event (not latest dated event).

    Source-provided list can be unsorted. Ties break by event_time then source.
    A backwards dated event published late is unavailable until publication.
    """
    if max_age is not None and max_age < 0:
        raise ValueError("max_age must be >= 0")
    visible = [e for e in events if e.available_at <= decision_at and e.event_time <= decision_at]
    if max_age is not None:
        visible = [e for e in visible if decision_at - e.available_at <= max_age]
    return max(visible, key=lambda e: (e.available_at, e.event_time, e.source), default=None)


def join_at_decision(streams: Mapping[str, Sequence[Evidence]], decision_at: int, max_age: int | None = None) -> dict[str, Evidence | None]:
    return {key: asof_evidence(value, decision_at, max_age) for key, value in streams.items()}


@dataclass(frozen=True)
class Book:
    bid: float
    ask: float
    bid_quantity: float
    ask_quantity: float
    exchange_time: int
    available_at: int

    def __post_init__(self) -> None:
        positive(self.bid, self.ask, self.bid_quantity, self.ask_quantity)
        if self.bid >= self.ask or self.exchange_time > self.available_at:
            raise ValueError("crossed or impossible book")


def orderbook_imbalance(book: Book) -> float:
    return (book.bid_quantity - book.ask_quantity) / (book.bid_quantity + book.ask_quantity)


def microprice(book: Book) -> float:
    """Bid weighted by ask size and ask by bid size (microprice)."""
    return (book.ask * book.bid_quantity + book.bid * book.ask_quantity) / (book.bid_quantity + book.ask_quantity)


class FillCertainty(str, Enum):
    UNKNOWN = "UNKNOWN"
    CONFIRMED = "CONFIRMED"
    NO_FILL = "NO_FILL"


@dataclass(frozen=True)
class QueueEvidence:
    """Only aggressive traded volume *ahead of* our displayed queue counts.

    Cancellation, hidden liquidity and priority changes cannot be inferred
    from OHLCV; volume alone is never sufficient to assert a maker fill.
    """
    queue_ahead: float | None
    executions_at_or_through_price: float | None
    fully_observed: bool = False


def maker_fill_certainty(e: QueueEvidence, our_quantity: float) -> FillCertainty:
    positive(our_quantity)
    if not e.fully_observed or e.queue_ahead is None or e.executions_at_or_through_price is None:
        return FillCertainty.UNKNOWN
    finite(e.queue_ahead, e.executions_at_or_through_price)
    if e.queue_ahead < 0 or e.executions_at_or_through_price < 0:
        raise ValueError("negative queue or execution")
    # A guaranteed full fill requires definitive evidence that all prior queue
    # volume plus our own order was consumed. With incomplete data: UNKNOWN.
    if e.executions_at_or_through_price >= e.queue_ahead + our_quantity:
        return FillCertainty.CONFIRMED
    return FillCertainty.UNKNOWN


class BarOutcome(str, Enum):
    STOP = "STOP"
    TARGET = "TARGET"
    NEITHER = "NEITHER"
    AMBIGUOUS = "AMBIGUOUS"
    GAP_STOP = "GAP_STOP"
    GAP_TARGET = "GAP_TARGET"


def classify_bracket_bar(bar: Candle, side: str, stop: float, target: float) -> BarOutcome:
    positive(stop, target)
    if side not in ("long", "short"):
        raise ValueError("side must be long or short")
    if (side == "long" and stop >= target) or (side == "short" and stop <= target):
        raise ValueError("bad bracket geometry")
    # Open gaps resolve before the intrabar high/low sequence.
    if side == "long":
        if bar.open <= stop: return BarOutcome.GAP_STOP
        if bar.open >= target: return BarOutcome.GAP_TARGET
        s, t = bar.low <= stop, bar.high >= target
    else:
        if bar.open >= stop: return BarOutcome.GAP_STOP
        if bar.open <= target: return BarOutcome.GAP_TARGET
        s, t = bar.high >= stop, bar.low <= target
    if s and t: return BarOutcome.AMBIGUOUS
    if s: return BarOutcome.STOP
    if t: return BarOutcome.TARGET
    return BarOutcome.NEITHER


class OrderState(str, Enum):
    NEW = "NEW"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class OrderSnapshot:
    order_id: str
    created_at: int
    expires_at: int
    requested: float
    executed: float = 0.0
    state: OrderState = OrderState.NEW

    def __post_init__(self) -> None:
        positive(self.requested)
        finite(self.executed)
        if not self.order_id or self.created_at >= self.expires_at or self.executed < 0 or self.executed > self.requested:
            raise ValueError("invalid order")
        if self.state == OrderState.NEW and self.executed != 0:
            raise ValueError("NEW order with executed quantity")
        if self.state == OrderState.FILLED and self.executed != self.requested:
            raise ValueError("FILLED but partial quantity")
        if self.state == OrderState.PARTIAL and not (0 < self.executed < self.requested):
            raise ValueError("PARTIAL requires proper fraction")


def transition_order(order: OrderSnapshot, kind: str, at: int, quantity: float = 0) -> OrderSnapshot:
    """Pure reducer. A fill on or after expiry is invalid, not a guessed fill."""
    from dataclasses import replace
    if at < order.created_at:
        raise ValueError("event predates order")
    if order.state not in (OrderState.NEW, OrderState.PARTIAL):
        raise ValueError("terminal order")
    if kind == "FILL":
        positive(quantity)
        if at >= order.expires_at or order.executed + quantity > order.requested + 1e-10:
            raise ValueError("late/over fill")
        filled = min(order.requested, order.executed + quantity)
        return replace(order, executed=filled, state=OrderState.FILLED if filled == order.requested else OrderState.PARTIAL)
    if kind not in ("EXPIRE", "CANCEL", "REJECT"):
        raise ValueError("unknown order event")
    if kind == "EXPIRE" and at < order.expires_at:
        raise ValueError("early expiry")
    if kind in ("CANCEL", "REJECT") and at >= order.expires_at:
        raise ValueError("terminal decision after expiry requires EXPIRE transition")
    return replace(order, state={"EXPIRE": OrderState.EXPIRED, "CANCEL": OrderState.CANCELLED, "REJECT": OrderState.REJECTED}[kind])
