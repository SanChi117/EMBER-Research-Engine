"""H1 input contracts only; no strategy, no investment action, no PnL."""
from dataclasses import dataclass
from decimal import Decimal

from .market_contract import DataUntrusted, dec, timestamp


@dataclass(frozen=True)
class FundingSettlement:
    symbol: str
    settlement_ms: int
    observed_at_ms: int
    rate: Decimal

    def __post_init__(self):
        timestamp(self.settlement_ms)
        timestamp(self.observed_at_ms)
        if self.observed_at_ms < self.settlement_ms:
            raise DataUntrusted("SETTLED_FUNDING_USED_BEFORE_SETTLEMENT")
        rate = dec(self.rate)
        if not -1 < rate < 1:
            raise DataUntrusted("IMPLAUSIBLE_FUNDING_RATE")
        object.__setattr__(self, "rate", rate)


@dataclass(frozen=True)
class TopBook:
    symbol: str
    venue: str
    kind: str
    bid: Decimal
    ask: Decimal
    observed_at_ms: int

    def __post_init__(self):
        if self.kind not in ("SPOT", "PERP_USDM") or not self.symbol or not self.venue:
            raise DataUntrusted("UNKNOWN_TWO_LEG_MARKET")
        timestamp(self.observed_at_ms)
        bid = dec(self.bid, positive=True)
        ask = dec(self.ask, positive=True)
        if bid > ask:
            raise DataUntrusted("CROSSED_TWO_LEG_BOOK")
        object.__setattr__(self, "bid", bid)
        object.__setattr__(self, "ask", ask)


def settled_funding_asof(records, decision_at_ms):
    """Past *settled* funding as observation; never predicted cash flow."""
    timestamp(decision_at_ms)
    return tuple(r for r in records if r.observed_at_ms <= decision_at_ms)


def executable_spot_long_perp_short_basis(spot, perp, *, decision_at_ms,
                                         max_quote_age_ms=15000):
    """Executable leg quote estimate, not realized return. Borrow/margin unmodeled."""
    timestamp(decision_at_ms)
    if not isinstance(spot, TopBook) or not isinstance(perp, TopBook):
        raise DataUntrusted("TWO_BOOKS_REQUIRED")
    if (spot.kind != "SPOT" or perp.kind != "PERP_USDM" or
        spot.symbol != perp.symbol or spot.venue != perp.venue):
        raise DataUntrusted("SPOT_PERP_IDENTITY_MISMATCH")
    if type(max_quote_age_ms) is not int or max_quote_age_ms < 0:
        raise DataUntrusted("INVALID_TWO_LEG_FRESHNESS")
    for book in (spot, perp):
        if book.observed_at_ms > decision_at_ms or (
            decision_at_ms - book.observed_at_ms > max_quote_age_ms
        ):
            raise DataUntrusted("STALE_OR_FUTURE_LEG")
    return perp.bid / spot.ask - 1


def half_open_bars(bars, start_ms, end_exclusive_ms):
    timestamp(start_ms)
    timestamp(end_exclusive_ms)
    if start_ms >= end_exclusive_ms:
        raise DataUntrusted("BAD_RESEARCH_WINDOW")
    return tuple(x for x in bars if start_ms <= x.open_ms < end_exclusive_ms)
