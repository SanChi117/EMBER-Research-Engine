"""Pure conservative PAPER quote-and-candle simulator. No exchange client."""
from dataclasses import dataclass
from decimal import Decimal as D
from .market_contract import DataUntrusted, ClosedBar, dec, timestamp

@dataclass(frozen=True)
class Quote:
    symbol: str
    venue: str
    observed_at_ms: int
    bid: D
    ask: D

@dataclass(frozen=True)
class Plan:
    id: str
    symbol: str
    side: str
    confirmed_at_ms: int
    stop: D
    target: D

@dataclass(frozen=True)
class Policy:
    max_notional: D = D("50")
    risk_budget: D = D("0.5")
    fee_rate: D = D("0.0004")
    slip_rate: D = D("0.0002")
    max_quote_lag_ms: int = 15000
    max_signal_lag_ms: int = 600000

@dataclass(frozen=True)
class Position:
    plan: Plan
    quote: Quote
    price: D
    quantity: D
    fee_paid: D
    risk: D
    next_full_minute_ms: int

@dataclass(frozen=True)
class Result:
    status: str
    cause: str
    net_r: D | None
    net_usdt: D | None
    exit_price: D | None
    covered: int

def open_paper(plan, quote, now_ms, policy=Policy()):
    timestamp(now_ms)
    timestamp(plan.confirmed_at_ms)
    timestamp(quote.observed_at_ms)
    if (not plan.id or plan.side not in ("LONG","SHORT") or
        quote.symbol != plan.symbol or not quote.venue):
        raise DataUntrusted("INVALID_SIGNAL_OR_QUOTE")
    if (plan.confirmed_at_ms > quote.observed_at_ms or
        quote.observed_at_ms > now_ms or
        now_ms-quote.observed_at_ms > policy.max_quote_lag_ms or
        now_ms-plan.confirmed_at_ms > policy.max_signal_lag_ms):
        raise DataUntrusted("FUTURE_OR_STALE_INPUT")
    bid, ask = dec(quote.bid, positive=True), dec(quote.ask, positive=True)
    if bid > ask:
        raise DataUntrusted("CROSSED_BID_ASK")
    stop, target = dec(plan.stop, positive=True), dec(plan.target, positive=True)
    fee, slip = dec(policy.fee_rate, nonnegative=True), dec(policy.slip_rate, nonnegative=True)
    if fee >= 1 or slip >= 1:
        raise DataUntrusted("INVALID_COSTS")
    entry = ask*(1+slip) if plan.side=="LONG" else bid*(1-slip)
    if not (stop < entry < target if plan.side=="LONG" else target < entry < stop):
        raise DataUntrusted("BAD_STRUCTURAL_GEOMETRY")
    quantity = min(dec(policy.max_notional,positive=True)/entry,
                   dec(policy.risk_budget,positive=True)/abs(entry-stop))
    risk = quantity*abs(entry-stop)
    first = (quote.observed_at_ms//60000+1)*60000
    return Position(plan,quote,entry,quantity,entry*quantity*fee,risk,first)

def evaluate_paper(position,bars,now_ms,policy=Policy()):
    """Stop-first, worse gap, double fee, and fail closed on missing minutes."""
    timestamp(now_ms)
    if not isinstance(position,Position):
        raise DataUntrusted("PAPER_POSITION_REQUIRED")
    if position.quote.observed_at_ms>now_ms:
        raise DataUntrusted("EXIT_BEFORE_ENTRY")
    fee,slip=dec(policy.fee_rate,nonnegative=True),dec(policy.slip_rate,nonnegative=True)
    expect=position.next_full_minute_ms
    count=0
    for bar in bars:
        if not isinstance(bar,ClosedBar) or bar.interval_ms!=60000:
            raise DataUntrusted("CLOSED_MINUTE_REQUIRED")
        if (bar.symbol!=position.plan.symbol or bar.venue!=position.quote.venue
            or bar.market_kind!="PERP_USDM"):
            raise DataUntrusted("MIXED_EXCHANGE_OR_SYMBOL")
        if bar.open_ms<expect:
            raise DataUntrusted("PARTIAL_ENTRY_MINUTE_OR_OVERLAP")
        if bar.open_ms!=expect:
            raise DataUntrusted("MISSING_EXIT_COVERAGE")
        if bar.available_at_ms>now_ms:
            return Result("HALTED","FUTURE_MINUTE_NOT_YET_AVAILABLE",None,None,None,count)
        long=position.plan.side=="LONG"
        hit_stop=bar.low<=position.plan.stop if long else bar.high>=position.plan.stop
        hit_target=bar.high>=position.plan.target if long else bar.low<=position.plan.target
        count+=1
        if hit_stop or hit_target:
            if long:
                raw=min(bar.open,position.plan.stop) if hit_stop else position.plan.target
                exit_price=raw*(1-slip)
                gross=(exit_price-position.price)*position.quantity
            else:
                raw=max(bar.open,position.plan.stop) if hit_stop else position.plan.target
                exit_price=raw*(1+slip)
                gross=(position.price-exit_price)*position.quantity
            net=gross-position.fee_paid-exit_price*position.quantity*fee
            return Result("CLOSED","STOP" if hit_stop else "TARGET",
                          net/position.risk,net,exit_price,count)
        expect=bar.close_ms
    return Result("HALTED","NO_FULL_POST_ENTRY_COVERAGE",None,None,None,count)
