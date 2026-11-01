"""RESET-05 part 4 / RESET-06: strict deterministic PAPER scaling gate report.

The ONLY trade source is the SHA-verified PAPER ledger. No cached metrics,
exchange calls or LIVE authorization. Missing/incomplete evidence blocks gates.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal as D
from decimal import InvalidOperation
from pathlib import Path

from .paper_ledger import JsonlPaperLedgerStore
from .strategy_registry import parse_canonical, validate_entry

DAY_MS = 86_400_000


class GateError(ValueError):
    pass


def _decimal_str(value: object) -> D:
    if type(value) is not str:
        raise GateError("GATE_METRIC_REQUIRES_DECIMAL_STRING")
    try:
        result = D(value)
    except InvalidOperation as exc:
        raise GateError("INVALID_GATE_NUMBER") from exc
    if not result.is_finite():
        raise GateError("NONFINITE_GATE_NUMBER")
    return result


def _status(value: object, threshold: object, operator: str) -> dict:
    return {"status": value, "threshold": threshold, "operator": operator}


def evaluate_gates(manifest: dict, trade_rows: tuple[dict, ...]) -> dict:
    """Only TRADE_CLOSED rows count; assume caller verified SHA chain first."""
    validate_entry(manifest)
    strategy_id = manifest["strategy_id"]
    risk = manifest["risk"]
    gates = manifest["gates"]
    equity0 = _decimal_str(risk["initial_equity_usdt"]) if risk["initial_equity_usdt"] is not None else None
    dd_limit = _decimal_str(gates["paper_max_drawdown_fraction"]) if gates["paper_max_drawdown_fraction"] is not None else None
    min_trades = gates["paper_min_closed_trades"]
    min_days = gates["paper_min_calendar_days"]
    pf_limit = _decimal_str(gates["laboratory_pf_strictly_greater_than"])

    closed = []
    seen = set()
    last_seen_ms = 0
    for row in trade_rows:
        if row.get("event_type") != "TRADE_CLOSED":
            continue
        payload = row.get("payload")
        if type(payload) is not dict:
            raise GateError("INVALID_CLOSED_TRADE_RECORD")
        if payload.get("strategy_id") != strategy_id:
            # One shared portfolio may not use strategy-filtered equity/DD
            # without a separately proven allocation model.
            raise GateError("MIXED_STRATEGY_LEDGER_REQUIRES_ALLOCATED_EQUITY")
        trade_id = payload.get("trade_id")
        ts = payload.get("observed_at_ms")
        if type(trade_id) is not str or not trade_id or trade_id in seen:
            raise GateError("DUPLICATE_OR_MISSING_CLOSED_TRADE_ID")
        if type(ts) is not int or ts <= 0 or ts < last_seen_ms:
            raise GateError("NONMONOTONIC_CLOSED_TRADE_TIME")
        seen.add(trade_id)
        last_seen_ms = ts
        pnl = _decimal_str(payload.get("net_pnl_usdt"))
        equity_after = _decimal_str(payload.get("equity_after_usdt"))
        if equity_after <= 0:
            raise GateError("INVALID_CLOSED_TRADE_EQUITY")
        closed.append((ts, pnl, equity_after))

    n = len(closed)
    # Conservative: count distinct UTC dates with closed trades, not merely
    # elapsed days since a start or periods with no observations.
    days = len({datetime.fromtimestamp(t / 1000, tz=timezone.utc).date() for t, _, _ in closed})
    gross_profit = sum((p for _, p, _ in closed if p > 0), D("0"))
    gross_loss = -sum((p for _, p, _ in closed if p < 0), D("0"))
    pf = gross_profit / gross_loss if gross_loss > 0 else None

    peak = equity0
    max_dd = D("0") if equity0 is not None else None
    for _, _, equity in closed:
        if peak is None:
            peak = equity
            max_dd = D("0")
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak)

    count_status = "PASS" if n >= min_trades else "IN_PROGRESS"
    days_status = "PASS" if days >= min_days else "IN_PROGRESS"
    pf_status = (
        "IN_PROGRESS" if pf is None
        else "PASS" if pf > pf_limit else "FAIL"
    )
    dd_status = (
        "IN_PROGRESS" if not closed or dd_limit is None or max_dd is None
        else "PASS" if max_dd <= dd_limit else "FAIL"
    )
    statuses = {
        "trades_closed": count_status,
        "days_active": days_status,
        "profit_factor": pf_status,
        "max_drawdown": dd_status,
    }
    eligibility = manifest["eligibility"]
    # Fail closed even when four numerical gates pass until strategy owner
    # explicitly approves PAPER and removes unresolved blocks in a new audit.
    unlocked = (
        all(x == "PASS" for x in statuses.values())
        and eligibility["paper_allowed"] is True
        and not eligibility["block_reasons"]
    )
    return {
        "strategy_id": strategy_id,
        "source": "SHA_VERIFIED_TRADES_JSONL",
        "values": {
            "trades_closed": n,
            "days_active": days,
            "gross_profit_usdt": format(gross_profit, "f"),
            "gross_loss_usdt": format(gross_loss, "f"),
            "profit_factor": None if pf is None else format(pf, "f"),
            "max_drawdown_fraction": None if max_dd is None else format(max_dd, "f"),
        },
        "thresholds": {
            "trades_closed_min": min_trades,
            "days_active_min": min_days,
            "profit_factor_strictly_greater_than": format(pf_limit, "f"),
            "max_drawdown_fraction_max": None if dd_limit is None else format(dd_limit, "f"),
        },
        "gates": statuses,
        "LADDER_STEP_UNLOCK": unlocked,
        "paper_allowed": False,  # Report is not an authorization to execute.
        "live_allowed": False,
        "eligibility_block_reasons": eligibility["block_reasons"],
    }


def report_from_store(
    *,
    journal_root: Path,
    registry_root: Path,
    strategy_id: str = "VIRTUAL_MECH_920",
    expected_trades_head: str | None = None,
) -> dict:
    manifest = parse_canonical(
        (Path(registry_root) / "strategies" / f"{strategy_id}.json").read_bytes()
    )
    store = JsonlPaperLedgerStore(journal_root)
    # Prevent bypassing ledger verification and detect externally anchored
    # valid tail truncations when expected_head is provided by the caller.
    store.verify("trades", expected_head=expected_trades_head)
    return evaluate_gates(manifest, store.read("trades"))


def render_report(report: dict) -> str:
    lines = [
        f"STRATEGY: {report['strategy_id']}",
        f"TRADES_CLOSED: {report['values']['trades_closed']} / {report['thresholds']['trades_closed_min']} : {report['gates']['trades_closed']}",
        f"DAYS_ACTIVE: {report['values']['days_active']} / {report['thresholds']['days_active_min']} : {report['gates']['days_active']}",
        f"PROFIT_FACTOR: {report['values']['profit_factor']} > {report['thresholds']['profit_factor_strictly_greater_than']} : {report['gates']['profit_factor']}",
        f"MAX_DRAWDOWN: {report['values']['max_drawdown_fraction']} <= {report['thresholds']['max_drawdown_fraction_max']} : {report['gates']['max_drawdown']}",
        f"LADDER_STEP_UNLOCK: {str(report['LADDER_STEP_UNLOCK']).lower()}",
        "LIVE_ALLOWED: false",
        "JSON:",
        json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--journal-root", default="data/paper")
    parser.add_argument("--registry-root", default="research/registry")
    parser.add_argument("--strategy-id", default="VIRTUAL_MECH_920")
    parser.add_argument("--expected-trades-head", default=None)
    args = parser.parse_args()
    try:
        result = report_from_store(
            journal_root=Path(args.journal_root),
            registry_root=Path(args.registry_root),
            strategy_id=args.strategy_id,
            expected_trades_head=args.expected_trades_head,
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("GATE_REPORT_FAIL_CLOSED: " + str(exc), file=sys.stderr)
        sys.exit(2)
    print(render_report(result), end="")


if __name__ == "__main__":
    main()
