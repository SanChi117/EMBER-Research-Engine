#!/usr/bin/env python3
"""C113 final C109 4H execution hypothesis, immutable historical PAPER only.

All candidates are admitted B1 C109 original signals on the same seven-day
terminal embargo. B1/B2 missed fills are recorded, never dropped as losses.
"""
from bisect import bisect_left
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
import argparse
import hashlib
import json

import c109_simple_p4_core_vs_original_research as core
import c110_blind_unchanged_c109_second_regime as unchanged
import c105_parent4h_structural_geometry as h4

class C113Error(ValueError):
    pass

PRECOMMIT = "cycles/B1_C113_PRECOMMIT_FINAL_EXECUTION_GEOMETRY_RU.md"
WINDOWS = (
    ("WIN_A", datetime(2024, 1, 1, tzinfo=timezone.utc),
     datetime(2024, 3, 5, tzinfo=timezone.utc),
     datetime(2024, 2, 2, tzinfo=timezone.utc)),
    ("WIN_B", datetime(2024, 4, 1, tzinfo=timezone.utc),
     datetime(2024, 6, 4, tzinfo=timezone.utc),
     datetime(2024, 5, 3, tzinfo=timezone.utc)),
)
ARM_LIMIT_ORIG = "B1_LIMIT_ORIGINAL_H4_STOP_48H"
ARM_LIMIT_WIDE = "B2_LIMIT_WIDE_H4_STOP_7D"
ARMS = (ARM_LIMIT_ORIG, ARM_LIMIT_WIDE)
DAY = 24 * h4.H
LIMIT_TTL = DAY
HOLD = {ARM_LIMIT_ORIG: 48 * h4.H, ARM_LIMIT_WIDE: 7 * DAY}
SEVEN_DAY_EMBARGO = 7 * DAY
EXPECTED_ZIPS = 1536
EXPECTED_BARS = 737280
ORIGINAL_C109_SHA = unchanged.CORE_SHA

def frozen():
    unchanged.source_code_verified()
    if len(WINDOWS) != 2 or len(core.SYMBOLS) != 12:
        raise C113Error("CHANGED_FROZEN_UNIVERSE")
    for _, start, end, fold in WINDOWS:
        if end - start != timedelta(days=64) or not start < fold < end:
            raise C113Error("CHANGED_PRECOMMITTED_WINDOWS")
    return True

@contextmanager
def scoped(window):
    frozen()
    _, begin, end, fold = window
    old = {field: getattr(core, field) for field in unchanged.CAL_FIELDS}
    try:
        core.BEGIN, core.END = begin, end
        core.BEGIN_MS, core.END_MS = int(begin.timestamp()*1000), int(end.timestamp()*1000)
        core.DAYS = tuple((begin + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(64))
        core.WARMUP_END = core.BEGIN_MS + SEVEN_DAY_EMBARGO
        core.LAST_ENTRY = core.END_MS - SEVEN_DAY_EMBARGO
        core.FOLD_MS = int(fold.timestamp()*1000)
        assert core.WARMUP_END < core.FOLD_MS < core.LAST_ENTRY
        yield
    finally:
        for field, value in old.items():
            setattr(core, field, value)

def basis(t, arm):
    """Price geometry known entirely at the original C109 signal."""
    side = t["side"]
    if side not in ("LONG", "SHORT"):
        raise C113Error("BAD_SIDE")
    upper, lower = D(t["zone_upper"]), D(t["zone_lower"])
    atr, tp = D(t["atr4h"]), D(t["target"])
    if not 0 < lower < upper or atr <= 0:
        raise C113Error("BAD_ORIGINAL_4H_SOURCE")
    limit = upper if side == "LONG" else lower
    if arm == ARM_LIMIT_ORIG:
        stop = D(t["stop"])
    elif arm == ARM_LIMIT_WIDE:
        stop = lower - D("0.35") * atr if side == "LONG" else upper + D("0.35") * atr
    else:
        raise C113Error("UNKNOWN_ARM")
    if arm == ARM_LIMIT_ORIG:
        expected = lower - h4.PAD*atr if side == "LONG" else upper + h4.PAD*atr
        if stop != expected:
            raise C113Error("ORIGINAL_STOP_CHANGED")
    if not (stop < limit < tp if side == "LONG" else tp < limit < stop):
        return None, "STRUCTURE_WRONG_SIDE"
    risk = abs(limit-stop)
    if not h4.MIN_RISK <= risk/limit <= h4.MAX_RISK:
        return None, "STRUCTURE_RISK_BOUNDS"
    rr = abs(tp-limit)/risk
    if rr < h4.MIN_RR:
        return None, "STRUCTURE_RR_BELOW_1_25"
    return {"limit": limit, "stop": stop, "target": tp, "risk": risk,
            "rr": rr, "atr": atr, "side": side, "lower": lower, "upper": upper}, "OK"

def touched(row, side, limit):
    return row.low <= limit if side == "LONG" else row.high >= limit

def invalidated(side, lower, upper, close):
    return close < lower if side == "LONG" else close > upper

def exit_on_bar(row, side, stop, target, *, first=False):
    """Never give same-bar fill a fictional pre-fill TP."""
    if side == "LONG":
        if row.open <= stop:
            return row.open, "STOP_GAP"
        if row.low <= stop:
            return stop, "STOP_FIRST_NATIVE3M"
        if not first and row.open >= target:
            return target, "TP_AT_OPEN"
        if not first and row.high >= target:
            return target, "4H_FTA_TARGET"
    else:
        if row.open >= stop:
            return row.open, "STOP_GAP"
        if row.high >= stop:
            return stop, "STOP_FIRST_NATIVE3M"
        if not first and row.open <= target:
            return target, "TP_AT_OPEN"
        if not first and row.low <= target:
            return target, "4H_FTA_TARGET"
    return None, None

def simulate_limit(t, rows, starts, closed4_by_ms, arm, last_fill_ms):
    """Result ledger is one record for EACH original C109 opportunity."""
    p, reason = basis(t, arm)
    orig_ms = t["entry_ms"]
    if p is None:
        return {"status": reason, "source_entry_ms": orig_ms, "trade": None}
    pos = bisect_left(starts, orig_ms)
    if pos >= len(rows) or starts[pos] != orig_ms:
        raise C113Error("MISSING_NATIVE3M_ORIGINAL_ENTRY")
    end_ms = min(orig_ms+LIMIT_TTL, last_fill_ms)
    if orig_ms >= end_ms:
        raise C113Error("SIGNAL_INSIDE_SEVEN_DAY_EMBARGO")
    fill_i = None
    for i in range(pos, len(rows)):
        row = rows[i]
        if row.start_ms >= end_ms:
            break
        if i > pos and rows[i-1].known_ms != row.start_ms:
            raise C113Error("GAPPED_NATIVE3M")
        # H4 invalidation is checked only AFTER that candle is fully closed.
        previous_closed = closed4_by_ms.get(row.start_ms)
        if previous_closed is not None and invalidated(
            p["side"], p["lower"], p["upper"], previous_closed):
            return {"status": "CANCELLED_PARENT_INVALIDATION",
                    "source_entry_ms": orig_ms, "trade": None}
        if touched(row, p["side"], p["limit"]):
            fill_i = i
            break
    if fill_i is None:
        return {"status": "UNFILLED_EXPIRED",
                "source_entry_ms": orig_ms, "trade": None}
    if not p["stop"] < p["limit"] < p["target"] if p["side"] == "LONG" else not p["target"] < p["limit"] < p["stop"]:
        raise C113Error("BROKEN_FILL_STRUCTURE")
    fillrow = rows[fill_i]
    expiry = fillrow.start_ms + HOLD[arm]
    if expiry > core.END_MS:
        raise C113Error("UNEMBARGOED_SEVEN_DAY_HOLD")
    exitprice = None
    exit_reason = None
    exitknown = None
    for i in range(fill_i, len(rows)):
        bar = rows[i]
        if i > fill_i and rows[i-1].known_ms != bar.start_ms:
            raise C113Error("GAPPED_NATIVE3M_EXIT")
        exitprice, exit_reason = exit_on_bar(
            bar, p["side"], p["stop"], p["target"], first=(i==fill_i))
        if exitprice is not None:
            exitknown = bar.known_ms
            break
        if bar.known_ms >= expiry:
            exitprice, exit_reason, exitknown = bar.close, "TIMEOUT", bar.known_ms
            break
    if exitprice is None or exitknown is None:
        raise C113Error("RIGHT_CENSORED_LIMIT_TRADE")
    direction = D(1) if p["side"] == "LONG" else D(-1)
    gross = direction * (exitprice-p["limit"])/p["risk"]
    r14 = gross - D(14)/D(10000)*p["limit"]/p["risk"]
    trade = {
        "entry_ms": fillrow.start_ms, "exit_ms": exitknown,
        "source_signal_ms": orig_ms, "symbol": t["symbol"],
        "parent_id": t["parent_id"], "side": p["side"],
        "entry": str(p["limit"]), "stop": str(p["stop"]), "target": str(p["target"]),
        "atr4h": str(p["atr"]), "gross_r": round(float(gross), 6),
        "net_r": round(float(r14), 6), "exit_reason": exit_reason,
        "target_source_tf": "4H", "stop_source_tf": "4H",
        "parent_tf": "4H", "derived_rr": round(float(p["rr"]), 6),
        "stop_pct": round(float(p["risk"]/p["limit"]*100), 6),
        "limit_wait_hours": round((fillrow.start_ms-orig_ms)/h4.H, 6),
        "same_bar_stop": exitknown == fillrow.known_ms,
        "fill_at_frozen_limit_no_improvement": True,
        "fee_slip_roundtrip_bps": 14, "arm": arm,
    }
    return {"status": "FILLED", "source_entry_ms": orig_ms, "trade": trade}

def costs(t, bps):
    e, stop = D(t["entry"]), D(t["stop"])
    return D(t["gross_r"]) - D(bps)/D(10000)*e/abs(e-stop)

def report_score(trades, bps, n_signals, fold_ms):
    by = [float(costs(t, bps)) for t in trades]
    gains = sum(x for x in by if x > 0)
    losses = -sum(x for x in by if x < 0)
    return {
        "signals": n_signals, "fills": len(trades),
        "filled_fraction": len(trades)/n_signals if n_signals else 0,
        "sum_r": round(sum(by), 6),
        "avg_r_per_signal": round(sum(by)/n_signals, 6) if n_signals else None,
        "pf": round(gains/losses, 6) if losses else (None if not by else float("inf")),
        "early_n": sum(t["source_signal_ms"] < fold_ms for t in trades),
        "late_n": sum(t["source_signal_ms"] >= fold_ms for t in trades),
    }

def portfolio_dd(trades, market, bps=25):
    """1% initial paper equity at risk per fill, concurrent 12-symbol 3m MTM.

    No margin/leverage assumptions: returns conservative equity bounds, not live DD.
    Every active position is marked at each original bar close and adverse wick.
    """
    symbols = tuple(core.SYMBOLS)
    n = len(market[symbols[0]])
    if any(len(market[s]) != n for s in symbols):
        raise C113Error("PORTFOLIO_CLOCK_LENGTH")
    trades_by = {s: sorted((t for t in trades if t["symbol"] == s),
                           key=lambda x: x["entry_ms"]) for s in symbols}
    pointers = {s: 0 for s in symbols}
    realized = 0.0
    peak_close = peak_wick = 100.0
    dd_close = dd_wick = 0.0
    max_open = 0
    for j in range(n):
        unclose = unwick = 0.0
        open_count = 0
        stamp = market[symbols[0]][j].start_ms
        for s in symbols:
            bar = market[s][j]
            if bar.start_ms != stamp:
                raise C113Error("PORTFOLIO_MISALIGNED_CLOCKS")
            z = trades_by[s]
            k = pointers[s]
            while k < len(z) and z[k]["exit_ms"] <= stamp:
                realized += float(costs(z[k], bps))
                k += 1
            pointers[s] = k
            if k >= len(z):
                continue
            t = z[k]
            if t["entry_ms"] <= stamp < t["exit_ms"]:
                open_count += 1
                side = 1 if t["side"] == "LONG" else -1
                entry, risk = D(t["entry"]), abs(D(t["entry"])-D(t["stop"]))
                close_r = side * (bar.close-entry)/risk
                adverse = bar.low if side == 1 else bar.high
                worst_r = side * (adverse-entry)/risk
                friction = D(bps)/D(10000)*entry/risk
                unclose += float(close_r-friction)
                unwick += float(worst_r-friction)
        max_open = max(max_open, open_count)
        eq_close, eq_wick = 100+realized+unclose, 100+realized+unwick
        peak_close = max(peak_close, eq_close)
        peak_wick = max(peak_wick, eq_close)
        dd_close = max(dd_close, 100*(peak_close-eq_close)/peak_close)
        dd_wick = max(dd_wick, 100*(peak_wick-eq_wick)/peak_wick)
    return {"dd_close_pct": round(dd_close, 6),
            "dd_adverse_wick_pct_upper_bound": round(dd_wick, 6),
            "max_simultaneous_positions": max_open,
            "initial_equity": 100, "initial_equity_risk_per_fill_pct": 1,
            "capital_model": "STATIC_INITIAL_EQUITY_1PCT_PER_FILL_NO_LEVERAGE_FUNDING"}

def per_symbol(rows, symbol):
    old = core.replay_per_symbol(rows, symbol)
    baseline = old["by_arm"][core.ARM_CORE]["trades"]
    starts = [x.start_ms for x in rows]
    four = h4.aggregate(rows, h4.H4)
    closed4_by_ms = {x.close_ms: x.close for x in four}
    arms = {}
    for arm in ARMS:
        ledger, accepted, status = [], [], Counter()
        busy_until = 0
        for t in baseline:
            if t["entry_ms"] < busy_until:
                item = {"status": "CAPACITY_BLOCKED",
                        "source_entry_ms": t["entry_ms"], "trade": None}
            else:
                item = simulate_limit(t, rows, starts, closed4_by_ms, arm, core.LAST_ENTRY)
                if item["status"] == "FILLED":
                    accepted.append(item["trade"])
                    busy_until = item["trade"]["exit_ms"]
                elif item["status"] in ("UNFILLED_EXPIRED", "CANCELLED_PARENT_INVALIDATION"):
                    busy_until = min(t["entry_ms"]+LIMIT_TTL, core.LAST_ENTRY)
            item["parent_id"] = t["parent_id"]
            item["source_symbol"] = symbol
            ledger.append(item)
            status[item["status"]] += 1
        arms[arm] = {"ledger": ledger, "trades": accepted, "status": dict(status)}
        if len(ledger) != len(baseline):
            raise C113Error("DROPPED_ORIGINAL_OPPORTUNITY")
    return {"baseline": baseline, "arms": arms, "source_bars": len(rows)}

def evaluate(window, market, manifest):
    if len(manifest) != 768 or set(market) != set(core.SYMBOLS):
        raise C113Error("MISSING_BINANCE_ORIGINAL_SOURCE")
    by = {s: per_symbol(market[s], s) for s in core.SYMBOLS}
    baseline = [t for s in core.SYMBOLS for t in by[s]["baseline"]]
    n = len(baseline)
    summary = {"A0_UNMODIFIED_4H": {}, ARM_LIMIT_ORIG: {}, ARM_LIMIT_WIDE: {}}
    fold_ms = core.FOLD_MS
    summary["A0_UNMODIFIED_4H"]["scores"] = {
        str(b): report_score([{**t, "gross_r": float(
            D(t["net_r"]) + D(14)/D(10000)*D(t["entry"])/abs(D(t["entry"])-D(t["stop"])))},
            "source_signal_ms": t["entry_ms"]} for t in baseline], b, n, fold_ms)
        for b in (14, 25, 40)}
    summary["A0_UNMODIFIED_4H"]["portfolio"] = portfolio_dd(
        baseline, market, 25)
    for arm in ARMS:
        trades = [t for s in core.SYMBOLS for t in by[s]["arms"][arm]["trades"]]
        summary[arm]["scores"] = {
            str(b): report_score(trades,b,n,fold_ms) for b in (14,25,40)}
        summary[arm]["status_counts"] = dict(sum(
            (Counter(by[s]["arms"][arm]["status"]) for s in core.SYMBOLS), Counter()))
        summary[arm]["portfolio"] = portfolio_dd(trades, market, 25)
    b2 = summary[ARM_LIMIT_WIDE]
    a0 = summary["A0_UNMODIFIED_4H"]
    reasons=[]
    for b in (25,40):
        x=b2["scores"][str(b)]
        if x["fills"] < 30 and b==25: reasons.append("NO_POWER_N_LT_30")
        if (x["early_n"] < 10 or x["late_n"] < 10) and b==25:
            reasons.append("NO_POWER_TEMPORAL_FOLD")
    x=b2["scores"]["25"]
    if x["sum_r"] <= 0: reasons.append("NONPOSITIVE_25BPS")
    if x["pf"] is None or x["pf"] <= 1.2: reasons.append("PF25_LE_1_2")
    y=b2["scores"]["40"]
    if y["pf"] is None or y["pf"] <= 1.1: reasons.append("PF40_LE_1_1")
    if x["sum_r"] <= a0["scores"]["25"]["sum_r"]:
        reasons.append("NOT_BETTER_THAN_PAIRED_A0")
    # use adverse wick upper-bound to prevent optimistic portfolio approval
    if b2["portfolio"]["dd_adverse_wick_pct_upper_bound"] >= 10:
        reasons.append("PORTFOLIO_WICK_DD_GE_10")
    if not b2["portfolio"]["capital_model"]:
        reasons.append("NO_PORTFOLIO_DD_EVIDENCE")
    return {
        "window": window[0], "source_zip_count": len(manifest),
        "source_manifest": manifest, "original_native3m_bars": sum(len(q) for q in market.values()),
        "original_c109_eligible_signal_count": n, "per_symbol": by, "summary": summary,
        "admission": {"screen_pass": not reasons, "fail_reasons": reasons,
                      "live_approved": False, "funding_missing": True}
    }

def run():
    frozen()
    windows={}
    for window in WINDOWS:
        with scoped(window):
            market, manifest = core.provider_3m()
            windows[window[0]] = evaluate(window, market, manifest)
    return {"schema": "EMBER_C113_TERMINAL_C109_EXECUTION_FALSIFICATION",
            "precommit": PRECOMMIT, "c109_source_sha": ORIGINAL_C109_SHA,
            "source_zip_count": sum(x["source_zip_count"] for x in windows.values()),
            "original_native3m_bars": sum(x["original_native3m_bars"] for x in windows.values()),
            "both_historical_windows_pass": all(x["admission"]["screen_pass"] for x in windows.values()),
            "paper_only": True, "live_approved": False, "true_forward_oos": False,
            "funding_missing": True, "orders": [], "fills": [], "live_trades": [], "windows": windows}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    if result["source_zip_count"] != EXPECTED_ZIPS or result["original_native3m_bars"] != EXPECTED_BARS:
        raise C113Error("INCOMPLETE_ORIGINAL_PROVIDER_EVIDENCE")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    digest={}
    for name, payload in result["windows"].items():
        fn=f"C113_{name}_ORIGINAL_768_SOURCE_LEDGER.json"
        raw=(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
        (args.output_dir/fn).write_bytes(raw)
        digest[name]={"filename":fn,"sha256":hashlib.sha256(raw).hexdigest(),
                      "bytes":len(raw),
                      "admission":payload["admission"],
                      "scores":payload["summary"]}
    summary={k:v for k,v in result.items() if k!="windows"}
    summary["window_receipts"]=digest
    raw=(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    (args.output_dir/"C113_SUMMARY.json").write_bytes(raw)
    print(json.dumps({"source_zips":result["source_zip_count"],
                      "native3m_bars":result["original_native3m_bars"],
                      "windows":digest,"both_pass":result["both_historical_windows_pass"],
                      "summary_sha256":hashlib.sha256(raw).hexdigest()},ensure_ascii=False,sort_keys=True))
if __name__ == "__main__":
    main()
