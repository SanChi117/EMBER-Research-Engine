#!/usr/bin/env python3
"""C100 forensic-only diagnostics of frozen C98 PAPER trades.

NO strategy modification, source downloads, orders, post-hoc profit filters or
claim that OHLCV alone proves a causal failure mode. Works on pinned C98 JSON.
"""
import argparse
import json
import math
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evidence/c98/C98_NEW_OCT_SOURCE_ABC_CLOSED_HOLDOUT.json"
COSTS = (14, 25, 40)
START_MS = 1790985600000
END_MS = 1793059200000
EXPECTED = {"A": 7, "B": 3, "C": 38}

class DiagnosticError(ValueError):
    pass

def dec(x):
    if type(x) is bool:
        raise DiagnosticError("BOOLEAN_NOT_DECIMAL")
    try:
        d = Decimal(str(x))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise DiagnosticError("INVALID_DECIMAL") from exc
    if not d.is_finite():
        raise DiagnosticError("NONFINITE_DECIMAL")
    return d

def inspect_trade(t, route):
    required = ("symbol", "route", "entry_ms", "exit_ms", "entry", "stop",
                "target", "fta", "fta_confirmed_ms", "derived_rr", "net_r",
                "exit_reason", "fee_slip_roundtrip_bps")
    if not isinstance(t, dict) or any(k not in t for k in required):
        raise DiagnosticError("INCOMPLETE_FROZEN_TRADE")
    if route not in EXPECTED:
        raise DiagnosticError("UNKNOWN_ROUTE")
    if type(t["entry_ms"]) is not int or type(t["exit_ms"]) is not int:
        raise DiagnosticError("INVALID_TIME_TYPE")
    if not START_MS <= t["entry_ms"] < t["exit_ms"] <= END_MS:
        raise DiagnosticError("OUT_OF_WINDOW_OR_NONCAUSAL_EXIT")
    if t["fta_confirmed_ms"] > t["entry_ms"]:
        raise DiagnosticError("FUTURE_FTA_AT_ENTRY")
    for field in ("stronghl_confirmed_ms", "poi_first_test_ms", "idm_confirmed_ms",
                  "trigger_close_ms", "vc_close_ms", "signal_ms"):
        if field in t and t[field] > t["entry_ms"]:
            raise DiagnosticError("FUTURE_SIGNAL_CONTEXT")
    if route == "C":
        if t.get("source_tf") != "NATIVE_3M":
            raise DiagnosticError("NATIVE_3M_REQUIRED")
        if not t.get("raid_closed_ms", 0) <= t.get("bos_close_ms", -1) <= t["entry_ms"]:
            raise DiagnosticError("RAID_BOS_SEQUENCE_INVALID")
    if route == "B" and (t.get("source_tf") != "NATIVE_5M"
                          or t.get("limit_filled") is not True):
        raise DiagnosticError("B_UNFILLED_OR_WRONG_TIMEFRAME")
    if t["fee_slip_roundtrip_bps"] != 14:
        raise DiagnosticError("FROZEN_14BPS_BASIS_REQUIRED")
    e, s, target, fta = (dec(t[k]) for k in ("entry", "stop", "target", "fta"))
    if min(e, s, target, fta) <= 0 or e == s or e == target:
        raise DiagnosticError("INVALID_RISK_OR_TARGET")
    if s < e < target and target <= fta:
        side = "LONG"
    elif target < e < s and target >= fta:
        side = "SHORT"
    else:
        raise DiagnosticError("STRUCTURAL_TARGET_OR_SL_SIDE_INVALID")
    if "side" in t and t["side"] != side:
        raise DiagnosticError("EXPLICIT_SIDE_MISMATCH")
    if "fixed_rr" in t:
        raise DiagnosticError("FORBIDDEN_LEGACY_FIXED_RR")
    rr = abs(target - e) / abs(e - s)
    if abs(rr - dec(t["derived_rr"])) > Decimal("0.00002"):
        raise DiagnosticError("INCORRECT_DERIVED_RR")
    net = dec(t["net_r"])
    if str(t["exit_reason"]).startswith("STOP_FIRST") and net >= 0:
        raise DiagnosticError("STOP_AS_PROFIT")
    return {
        "side": side,
        "side_source": "EXPLICIT" if "side" in t else "INFERRED_STOP_TARGET_GEOMETRY",
        "stop_pct": abs(e - s) * 100 / e,
        "risk": abs(e - s),
        "net14": net,
        "exit_reason": t["exit_reason"],
        "duration_minutes": (t["exit_ms"] - t["entry_ms"]) // 60000,
    }

def net_at_bps(t, info, price_bps):
    # Frozen C97 formula, replicated here only for independent diagnostics.
    deduction = Decimal(price_bps - 14) * dec(t["entry"]) / (
        Decimal("10000") * info["risk"])
    return Decimal(str(round(float(info["net14"] - deduction), 6)))

def summarize(doc):
    if doc.get("schema") != "EMBER_C98_PRECOMMITTED_UNTOUCHED_ORIGINAL_BINANCE_OCT03_TO_OCT26":
        raise DiagnosticError("WRONG_SOURCE_SCHEMA")
    if doc.get("no_fixed_rr") is not True or doc.get("only_original_source") is not True:
        raise DiagnosticError("MISSING_FROZEN_SOURCE_GUARDS")
    if doc.get("orders") or doc.get("fills") or doc.get("live_trades"):
        raise DiagnosticError("REAL_EXECUTION_IN_HISTORICAL_SOURCE")
    if doc.get("period_start_ms") != START_MS or doc.get("period_end_exclusive_ms") != END_MS:
        raise DiagnosticError("UNREGISTERED_HISTORICAL_WINDOW")
    models = doc.get("research_models")
    if not isinstance(models, dict) or set(models) != set(EXPECTED):
        raise DiagnosticError("MISSING_OR_EXTRA_ROUTE")
    out = {}
    for route in ("A", "B", "C"):
        original = models[route]
        trades = original["trades"]
        if not isinstance(trades, list) or len(trades) != EXPECTED[route]:
            raise DiagnosticError("FROZEN_SAMPLE_COUNT_CHANGED")
        infos = [inspect_trade(t, route) for t in trades]
        for bps in COSTS:
            reported = original["cost_sensitivity"][str(bps)]
            recalculated = round(float(sum((net_at_bps(t, info, bps)
                               for t, info in zip(trades, infos)), Decimal(0))), 6)
            if abs(recalculated - float(reported["sum_r"])) > 0.00001:
                raise DiagnosticError("COST_REPLAY_DOES_NOT_MATCH_FROZEN_SCORE")
            if reported["n"] != len(trades):
                raise DiagnosticError("REPORTED_SAMPLE_COUNT_MISMATCH")
        out[route] = {
            "n": len(trades),
            "positive_net14_n": sum(x["net14"] > 0 for x in infos),
            "by_reason": dict(sorted(Counter(x["exit_reason"] for x in infos).items())),
            "by_side": dict(sorted(Counter(x["side"] for x in infos).items())),
            "side_inferred_n": sum(x["side_source"] != "EXPLICIT" for x in infos),
            "median_stop_pct": round(float(median(x["stop_pct"] for x in infos)), 6),
            "median_holding_minutes": float(median(x["duration_minutes"] for x in infos)),
            "net_r": {str(b): original["cost_sensitivity"][str(b)]["sum_r"] for b in COSTS},
            "hypothesis_classification": "POST_HOC_DESCRIPTIVE_ONLY_NOT_CAUSALLY_VERIFIED",
        }
    return {"status": "FORENSIC_RESEARCH_ONLY", "source": SOURCE.name,
            "sample": "HISTORICAL_C98_OCT03_26_ALREADY_SEEN",
            "real_orders": 0, "trade_rules_changed": False, "routes": out}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=SOURCE)
    a = p.parse_args()
    result = summarize(json.loads(a.source.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
