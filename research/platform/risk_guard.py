"""Strategy-neutral, fail-closed PAPER risk preflight. NEVER grants live execution.

Stop cost is a modeled estimate, not a gap/liquidation loss ceiling.
"""
from dataclasses import dataclass
from decimal import Decimal as D

from .market_contract import DataUntrusted, dec, timestamp


@dataclass(frozen=True)
class RiskLimits:
    allowed_symbols: frozenset[str]
    max_trade_risk_fraction: D
    max_portfolio_risk_fraction: D
    max_notional_to_equity: D
    max_leverage: D
    max_positions: int
    kill_equity: D
    max_peak_drawdown_fraction: D
    max_data_lag_ms: int
    max_signal_lag_ms: int


@dataclass(frozen=True)
class RiskSnapshot:
    equity: D
    peak_equity: D
    free_collateral: D
    reserved_stop_risk: D
    open_positions: int
    observed_at_ms: int
    source_ok: bool
    halted: bool


@dataclass(frozen=True)
class PaperIntent:
    symbol: str
    venue: str
    market_kind: str
    side: str
    entry: D
    stop: D
    quantity: D
    leverage: D
    fee_rate: D
    slip_rate: D
    signal_confirmed_at_ms: int
    quote_observed_at_ms: int


@dataclass(frozen=True)
class RiskVerdict:
    paper_preflight_ok: bool
    reason: str
    stop_loss_estimate: D | None = None
    collateral_estimate: D | None = None
    notional: D | None = None
    live_allowed: bool = False


def _blocked(reason: str) -> RiskVerdict:
    return RiskVerdict(False, reason)


def _number(value: object, *, positive: bool = False, nonnegative: bool = False) -> D:
    if isinstance(value, bool) or not isinstance(value, (str, int, D)):
        raise DataUntrusted("NON_DECIMAL_RISK_INPUT")
    return dec(value, positive=positive, nonnegative=nonnegative)


def assess_paper_risk(
    intent: PaperIntent,
    snapshot: RiskSnapshot,
    limits: RiskLimits,
    *,
    now_ms: int,
) -> RiskVerdict:
    """Pure refusal gate. A PASS does not authorize execution or prove risk coverage."""
    if not isinstance(intent, PaperIntent) or not isinstance(snapshot, RiskSnapshot):
        return _blocked("INVALID_RISK_CONTRACT")
    if not isinstance(limits, RiskLimits):
        return _blocked("UNREGISTERED_LIMITS")
    try:
        timestamp(now_ms)
        timestamp(snapshot.observed_at_ms)
        timestamp(intent.quote_observed_at_ms)
        timestamp(intent.signal_confirmed_at_ms)
        trade_fraction = _number(limits.max_trade_risk_fraction, positive=True)
        portfolio_fraction = _number(limits.max_portfolio_risk_fraction, positive=True)
        notional_multiple = _number(limits.max_notional_to_equity, positive=True)
        max_leverage = _number(limits.max_leverage, positive=True)
        drawdown = _number(limits.max_peak_drawdown_fraction, positive=True)
        kill = _number(limits.kill_equity, positive=True)
        equity = _number(snapshot.equity, positive=True)
        peak = _number(snapshot.peak_equity, positive=True)
        free = _number(snapshot.free_collateral, nonnegative=True)
        reserved = _number(snapshot.reserved_stop_risk, nonnegative=True)
        entry = _number(intent.entry, positive=True)
        stop = _number(intent.stop, positive=True)
        quantity = _number(intent.quantity, positive=True)
        leverage = _number(intent.leverage, positive=True)
        fee = _number(intent.fee_rate, nonnegative=True)
        slip = _number(intent.slip_rate, nonnegative=True)

        if (
            trade_fraction >= 1
            or portfolio_fraction >= 1
            or drawdown >= 1
            or fee >= 1
            or slip >= 1
            or not isinstance(limits.allowed_symbols, frozenset)
            or not limits.allowed_symbols
            or not all(isinstance(s, str) and s.endswith("USDT") for s in limits.allowed_symbols)
            or type(limits.max_positions) is not int
            or limits.max_positions < 1
            or type(snapshot.open_positions) is not int
            or snapshot.open_positions < 0
            or type(limits.max_data_lag_ms) is not int
            or limits.max_data_lag_ms < 0
            or type(limits.max_signal_lag_ms) is not int
            or limits.max_signal_lag_ms < 0
            or peak < equity
            or kill >= peak
        ):
            return _blocked("INVALID_RISK_POLICY_OR_SNAPSHOT")
        if snapshot.source_ok is not True:
            return _blocked("UNTRUSTED_PORTFOLIO_SOURCE")
        if snapshot.halted is not False:
            return _blocked("PORTFOLIO_HALTED")
        if intent.venue != "BINANCE" or intent.market_kind != "PERP_USDM":
            return _blocked("NOT_BINANCE_USDM_FUTURES")
        if intent.symbol not in limits.allowed_symbols or intent.side not in ("LONG", "SHORT"):
            return _blocked("UNREGISTERED_SYMBOL_OR_SIDE")
        if (
            snapshot.observed_at_ms > now_ms
            or intent.quote_observed_at_ms > now_ms
            or intent.signal_confirmed_at_ms > intent.quote_observed_at_ms
        ):
            return _blocked("FUTURE_INPUT")
        if (
            now_ms - snapshot.observed_at_ms > limits.max_data_lag_ms
            or now_ms - intent.quote_observed_at_ms > limits.max_data_lag_ms
            or now_ms - intent.signal_confirmed_at_ms > limits.max_signal_lag_ms
        ):
            return _blocked("STALE_INPUT")
        if equity <= kill:
            return _blocked("KILL_EQUITY_REACHED")
        if equity <= peak * (1 - drawdown):
            return _blocked("MAX_DRAWDOWN_REACHED")
        if snapshot.open_positions >= limits.max_positions:
            return _blocked("MAX_POSITIONS_REACHED")
        if leverage > max_leverage:
            return _blocked("MAX_LEVERAGE_EXCEEDED")
        if intent.side == "LONG":
            if stop >= entry:
                return _blocked("BAD_STOP_GEOMETRY")
            paid = entry * (1 + slip)
            stop_fill = stop * (1 - slip)
            stop_loss = (paid - stop_fill) * quantity
        else:
            if stop <= entry:
                return _blocked("BAD_STOP_GEOMETRY")
            paid = entry * (1 - slip)
            stop_fill = stop * (1 + slip)
            stop_loss = (stop_fill - paid) * quantity
        stop_loss = max(stop_loss, D("0")) + (paid + stop_fill) * quantity * fee
        notional = entry * quantity
        collateral = notional / leverage + (paid + stop_fill) * quantity * fee
        if stop_loss > equity * trade_fraction:
            return _blocked("TRADE_RISK_EXCEEDED")
        if reserved + stop_loss > equity * portfolio_fraction:
            return _blocked("PORTFOLIO_RISK_EXCEEDED")
        if notional > equity * notional_multiple:
            return _blocked("NOTIONAL_CAP_EXCEEDED")
        if collateral > free:
            return _blocked("INSUFFICIENT_COLLATERAL")
        return RiskVerdict(True, "PAPER_PREFLIGHT_ONLY", stop_loss, collateral, notional)
    except (DataUntrusted, ValueError, TypeError, ArithmeticError):
        return _blocked("INVALID_OR_MISSING_RISK_INPUT")
