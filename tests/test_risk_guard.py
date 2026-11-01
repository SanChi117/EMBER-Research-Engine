"""Adversarial RISK-CARCASE-01 fixtures; PAPER only."""
from dataclasses import replace
from decimal import Decimal as D

from research.platform.risk_guard import (
    PaperIntent,
    RiskLimits,
    RiskSnapshot,
    assess_paper_risk,
)

NOW = 1762000000000


def config():
    return RiskLimits(
        frozenset({"SOLUSDT", "LINKUSDT"}), D("0.04"), D("0.08"), D("2"),
        D("5"), 1, D("736"), D("0.25"), 15000, 600000,
    )


def account():
    return RiskSnapshot(D("920"), D("950"), D("500"), D("0"), 0, NOW - 1000, True, False)


def request():
    return PaperIntent(
        "SOLUSDT", "BINANCE", "PERP_USDM", "LONG", D("100"), D("98"),
        D("2"), D("2"), D("0.0004"), D("0.0002"), NOW - 10000, NOW - 500,
    )


def verdict(intent=None, snap=None, policy=None):
    return assess_paper_risk(
        request() if intent is None else intent,
        account() if snap is None else snap,
        config() if policy is None else policy,
        now_ms=NOW,
    )


def test_paper_only_does_not_authorize_live():
    v = verdict()
    assert v.paper_preflight_ok and not v.live_allowed
    assert v.reason == "PAPER_PREFLIGHT_ONLY"
    assert v.stop_loss_estimate > D("4")
    assert v.notional == D("200")


def test_short_stop_fee_slippage():
    v = verdict(replace(request(), side="SHORT", stop=D("102")))
    assert v.paper_preflight_ok and v.stop_loss_estimate > D("4")


def test_spot_and_bybit_denied():
    assert verdict(replace(request(), market_kind="SPOT")).reason == "NOT_BINANCE_USDM_FUTURES"
    assert verdict(replace(request(), venue="BYBIT")).reason == "NOT_BINANCE_USDM_FUTURES"


def test_source_must_be_trusted_and_not_halted():
    assert verdict(snap=replace(account(), source_ok=False)).reason == "UNTRUSTED_PORTFOLIO_SOURCE"
    assert verdict(snap=replace(account(), source_ok=None)).reason == "UNTRUSTED_PORTFOLIO_SOURCE"
    assert verdict(snap=replace(account(), halted=True)).reason == "PORTFOLIO_HALTED"


def test_stale_or_future():
    assert verdict(replace(request(), quote_observed_at_ms=NOW + 1)).reason == "FUTURE_INPUT"
    assert verdict(replace(request(), quote_observed_at_ms=NOW - 20000, signal_confirmed_at_ms=NOW - 21000)).reason == "STALE_INPUT"
    assert verdict(snap=replace(account(), observed_at_ms=NOW - 20000)).reason == "STALE_INPUT"
    assert verdict(replace(request(), signal_confirmed_at_ms=NOW + 1)).reason == "FUTURE_INPUT"


def test_equity_kill_and_drawdown():
    assert verdict(snap=replace(account(), equity=D("736"))).reason == "KILL_EQUITY_REACHED"
    s = replace(account(), equity=D("700"))
    assert verdict(snap=s, policy=replace(config(), kill_equity=D("100"))).reason == "MAX_DRAWDOWN_REACHED"


def test_open_position_and_leverage_limits():
    assert verdict(snap=replace(account(), open_positions=1)).reason == "MAX_POSITIONS_REACHED"
    assert verdict(replace(request(), leverage=D("6"))).reason == "MAX_LEVERAGE_EXCEEDED"


def test_trade_risk_includes_costs():
    assert verdict(replace(request(), quantity=D("20"))).reason == "TRADE_RISK_EXCEEDED"


def test_portfolio_reserved_risk_is_counted():
    assert verdict(snap=replace(account(), reserved_stop_risk=D("70"))).reason == "PORTFOLIO_RISK_EXCEEDED"
    assert verdict(replace(request(), quantity=D("36")), policy=replace(config(), max_trade_risk_fraction=D("0.2"))).reason == "PORTFOLIO_RISK_EXCEEDED"


def test_notional_and_collateral_caps():
    c = replace(config(), max_trade_risk_fraction=D("0.2"), max_portfolio_risk_fraction=D("0.3"))
    assert verdict(replace(request(), quantity=D("20")), policy=c).reason == "NOTIONAL_CAP_EXCEEDED"
    assert verdict(snap=replace(account(), free_collateral=D("99"))).reason == "INSUFFICIENT_COLLATERAL"


def test_stop_geometry_allowlist_and_invalid_numeric_input():
    assert verdict(replace(request(), stop=D("101"))).reason == "BAD_STOP_GEOMETRY"
    assert verdict(replace(request(), symbol="OPUSDT")).reason == "UNREGISTERED_SYMBOL_OR_SIDE"
    assert verdict(replace(request(), quantity=0.1)).reason == "INVALID_OR_MISSING_RISK_INPUT"
    assert verdict(replace(request(), entry=D("NaN"))).reason == "INVALID_OR_MISSING_RISK_INPUT"


def test_missing_or_invalid_limits_are_blocked():
    assert verdict(policy=replace(config(), max_positions=0)).reason == "INVALID_RISK_POLICY_OR_SNAPSHOT"
    assert verdict(policy=replace(config(), max_data_lag_ms=-1)).reason == "INVALID_RISK_POLICY_OR_SNAPSHOT"
    assert assess_paper_risk(request(), account(), None, now_ms=NOW).reason == "UNREGISTERED_LIMITS"
