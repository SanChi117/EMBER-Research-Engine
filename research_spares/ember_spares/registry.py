"""Explicit opt-in component registry. No dynamic imports, no side effects.

Each ID maps to exactly one study-only primitive or small family. Z12 is an
already-present mechanism in SMOKE and deliberately not reimplemented.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Component:
    id: str
    module: str
    entrypoint: str
    readiness: str
    notes: str


# CORE_TESTABLE means deterministic pure calculation can be unit-tested.
# REQUIRES_MARKET_DATA means meaningful use requires a verified point-in-time
# source and its integration. It does not mean the exchange adapter exists.
# OFFLINE_ONLY excludes operational/order execution readiness in ALL cases.
REGISTRY: tuple[Component,...] = (
    Component("Z01","market","join_at_decision","REQUIRES_MARKET_DATA","Causal as-of join; needs Binance feed timestamps"),
    Component("Z02","accounting","margin_state","REQUIRES_MARKET_DATA","Tier-aware snapshot; not exchange liquidation price"),
    Component("Z03","market","microprice","REQUIRES_MARKET_DATA","L2 snapshot feature; queue evidence external"),
    Component("Z04","research","diff_traces","CORE_TESTABLE","Requires two externally produced traces"),
    Component("Z05","accounting","multileg_pnl","CORE_TESTABLE","Leg cashflow; not atomic execution"),
    Component("Z06","accounting","replay_cash_events","CORE_TESTABLE","Deterministic fill/funding ledger"),
    Component("Z07","accounting","portfolio_risk_gate","CORE_TESTABLE","Conservative correlated exposures not netted"),
    Component("Z08","accounting","load_risk_state","CORE_TESTABLE","Local file latch, no broker reconciliation"),
    Component("Z09","market","classify_bracket_bar","CORE_TESTABLE","AMBIGUOUS on both hits"),
    Component("Z10","market","transition_order","CORE_TESTABLE","Order lifecycle no broker gateway"),
    Component("Z11","structure","advance_zone","CORE_TESTABLE","Flip candidate != confirmed structure flip"),
    Component("Z13","structure","evaluate_rules","CORE_TESTABLE","Safe declarative basic PA conditions"),
    Component("Z14","structure","advance_compression","CORE_TESTABLE","Requires historical compression classification"),
    Component("Z15","structure","double_top","CORE_TESTABLE","One confirmed pattern, not full 8-detector family"),
    Component("Z16","structure","fvg_channel","CORE_TESTABLE","Standalone simple FVG midpoint channel"),
    Component("Z17","structure","failed_breakout","CORE_TESTABLE","Close-to-close failure"),
    Component("Z18","structure","advance_regime","CORE_TESTABLE","Absolute trend-strength hysteresis"),
    Component("Z19","structure","hull_ma","CORE_TESTABLE","HMA and SuperTrend available; OTT not reproduced"),
    Component("Z20","signals","fit_ou","REQUIRES_MARKET_DATA","Historical funding settlement inputs"),
    Component("Z21","signals","oi_quadrant","REQUIRES_MARKET_DATA","Requires timestamp-aligned OI; motive not proven"),
    Component("Z22","signals","taker_pressure","REQUIRES_MARKET_DATA","Requires complete taker volume candles"),
    Component("Z23","signals","lag_correlations","REQUIRES_MARKET_DATA","Offline event study, not predictive entry"),
    Component("Z24","signals","momentum_ranks","REQUIRES_MARKET_DATA","Universe snapshot must be frozen"),
    Component("Z25","signals","pair_spread","REQUIRES_MARKET_DATA","OLS not cointegration validation"),
    Component("Z26","signals","mean_dislocation","CORE_TESTABLE","Separate RSI filter/time hold not included"),
    Component("Z27","signals","verify_model_contract","CORE_TESTABLE","Artifact check only, no ML prediction"),
    Component("Z28","structure","fibonacci_retracement","CORE_TESTABLE","Two-entry geometry, no allocation/order"),
    Component("Z29","research","paired_ablation","CORE_TESTABLE","Matched trade comparison"),
    Component("Z30","research","bonferroni_pvalue","CORE_TESTABLE","IC/correction; not full deflated Sharpe"),
    Component("Z31","research","pnl_attribution","CORE_TESTABLE","Concentration, leave-one-out PnL"),
    Component("Z32","research","leakage_violations","CORE_TESTABLE","Metadata gate; external code scan separate"),
    Component("Z33","research","diff_traces","CORE_TESTABLE","Differential signal comparison"),
    Component("Z34","research","capacity_limit_quantity","REQUIRES_MARKET_DATA","Capacity upper bound only"),
    Component("Z35","research","session_pnl","CORE_TESTABLE","Ex-post bucket, no tuned session filter"),
    Component("Z36","research","exposure_report","CORE_TESTABLE","Union of holding intervals"),
    Component("Z37","accounting","staircase_risk","CORE_TESTABLE","Risk calculator only; no liquidation authorisation"),
    Component("Z38","research","diff_traces","CORE_TESTABLE","Diff diagnostics; no Freqtrade/Pine runtime adapter"),
)


def get_component(component_id: str) -> Component:
    match=next((x for x in REGISTRY if x.id==component_id),None)
    if match is None:
        raise KeyError(component_id)
    return match


assert len(REGISTRY)==37 and len({x.id for x in REGISTRY})==37
assert "Z12" not in {x.id for x in REGISTRY}
