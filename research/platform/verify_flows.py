"""TZ-2: SHA integrity and prospective 7-day coverage; no synthetic slots."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .flow_collector import HOUR_MS, symbols_from_config
from .flow_ledger import FlowStore

DAY_MS = 24 * HOUR_MS
MINUTE_MS = 60_000
WEEK_MS = 7 * DAY_MS


class FlowVerificationError(ValueError):
    pass


def coverage_report(
    store: FlowStore, symbols: tuple[str, ...], *,
    start_ms: int, end_ms: int,
) -> dict:
    if (
        type(start_ms) is not int or type(end_ms) is not int
        or start_ms <= 0 or end_ms - start_ms != WEEK_MS
        or start_ms % HOUR_MS != 0
    ):
        raise FlowVerificationError("INVALID_SEVEN_DAY_UTC_WINDOW")
    if len(symbols) != 12 or len(set(symbols)) != 12:
        raise FlowVerificationError("FULL_TWELVE_SYMBOL_UNIVERSE_REQUIRED")
    entries = {name: store.events(name) for name in ("oi", "funding", "liquidations")}
    all_events = [row for events in entries.values() for row in events]
    if any(row["event_type"] == "SCHEMA_DRIFT" for row in all_events):
        raise FlowVerificationError("HALTED_SCHEMA_DRIFT_PRESENT")
    slots = tuple(range(start_ms, end_ms, HOUR_MS))
    missing = {}
    per_symbol_oi = {}
    valid_oi = 0
    marked = 0
    for symbol in symbols:
        observed = {
            item["payload"]["slot_ms"]
            for item in entries["oi"]
            if item["event_type"] == "OI_SNAPSHOT"
            and item["payload"]["symbol"] == symbol
            and start_ms <= item["payload"]["observed_at_ms"] < end_ms
            and item["payload"]["slot_ms"] == (
                item["payload"]["observed_at_ms"] // HOUR_MS * HOUR_MS
            )
        }
        gaps = {
            item["payload"].get("slot_ms")
            for item in entries["oi"]
            if item["event_type"] == "GAP"
            and item["payload"]["symbol"] == symbol
            and item["payload"].get("slot_ms") in slots
        }
        missed = sorted(set(slots) - observed)
        missing[symbol] = missed
        valid_for_symbol = len(set(slots) & observed)
        gaps_for_symbol = len(set(missed) & gaps)
        per_symbol_oi[symbol] = {
            "observed_slots": valid_for_symbol,
            "missing_slots": len(missed),
            "gap_marked_slots": gaps_for_symbol,
            "unmarked_missing_slots": len(missed) - gaps_for_symbol,
            "coverage_rate": f"{valid_for_symbol / len(slots):.6f}",
            "status": "PASS" if valid_for_symbol / len(slots) >= .95
            and gaps_for_symbol == len(missed) else "IN_PROGRESS",
        }
        valid_oi += valid_for_symbol
        marked += gaps_for_symbol
    expected = len(slots) * len(symbols)
    oi_rate = valid_oi / expected
    oi_unmarked = (expected - valid_oi) - marked
    oi_all_symbols_ok = all(
        report["status"] == "PASS" for report in per_symbol_oi.values()
    )

    funding = entries["funding"]
    funding_status = {}
    schedules = 0
    scheduled_settlements = 0
    captured_settlements = 0
    for symbol in symbols:
        rows = [
            r["payload"] for r in funding
            if r["event_type"] == "FUNDING_SCHEDULE"
            and r["payload"]["symbol"] == symbol
            and start_ms <= r["payload"]["observed_at_ms"] < end_ms
        ]
        observed_hourly = {r["slot_ms"] for r in rows if r["slot_ms"] in slots}
        schedule_coverage = len(observed_hourly) / len(slots)
        expected_settlements = {
            r["next_funding_time_ms"] for r in rows
            if start_ms <= r["next_funding_time_ms"] < end_ms
        }
        realized = {
            r["payload"]["funding_time_ms"] for r in funding
            if r["event_type"] == "FUNDING_SETTLED"
            and r["payload"]["symbol"] == symbol
            and start_ms <= r["payload"]["funding_time_ms"] < end_ms
            and r["payload"]["observed_at_ms"] < end_ms + DAY_MS
        }
        known_settlements = len(expected_settlements & realized)
        funding_status[symbol] = {
            "schedule_slots": len(observed_hourly),
            "schedule_coverage": f"{schedule_coverage:.6f}",
            "expected_settlements_from_source": len(expected_settlements),
            "captured_settlements": known_settlements,
            "missing_settlements": sorted(expected_settlements - realized),
        }
        schedules += len(observed_hourly)
        scheduled_settlements += len(expected_settlements)
        captured_settlements += known_settlements
    # Do not mistake the absence of a schedule for 100% settlements.
    # Expected 7-day 8-hour reference minimum: 21 per symbol. A faster
    # per-symbol funding cadence is covered by every source-declared time.
    schedule_ok = schedules == len(slots) * len(symbols)
    funding_ok = (
        schedule_ok and all(
            x["expected_settlements_from_source"] >= 20
            and not x["missing_settlements"]
            for x in funding_status.values()
        )
    )

    liq = entries["liquidations"]
    pongs = {
        row["payload"].get("minute_slot_ms")
        for row in liq
        if row["event_type"] == "LIQ_HEARTBEAT"
        and row["payload"].get("evidence") == "WEBSOCKET_PONG_CONFIRMED"
        and start_ms <= row["payload"]["observed_at_ms"] < end_ms
        and row["payload"].get("minute_slot_ms")
        == row["payload"]["observed_at_ms"] // MINUTE_MS * MINUTE_MS
    }
    expected_minutes = WEEK_MS // MINUTE_MS
    liq_rate = len(pongs) / expected_minutes
    partial = any(
        row["event_type"] == "LIQ_SNAPSHOT_PARTIAL"
        and start_ms <= row["payload"]["observed_at_ms"] < end_ms
        for row in liq
    )
    liq_status = (
        "LIQ_SNAPSHOT_PARTIAL" if partial
        else "PASS" if liq_rate >= .95
        else "IN_PROGRESS"
    )
    return {
        "window_start_ms": start_ms,
        "window_end_ms": end_ms,
        "symbols": list(symbols),
        "oi": {
            "total_expected_hour_symbol_slots": expected,
            "observed_slots": valid_oi,
            "coverage_rate": f"{oi_rate:.6f}",
            "missing_slots": expected - valid_oi,
            "gap_marked_slots": marked,
            "unmarked_missing_slots": oi_unmarked,
            "per_symbol": per_symbol_oi,
            "status": "PASS" if oi_all_symbols_ok
            else "IN_PROGRESS",
        },
        "funding": {
            "total_hourly_schedule_slots": schedules,
            "expected_settlements_from_source": scheduled_settlements,
            "observed_settlements_from_source": captured_settlements,
            "per_symbol": funding_status,
            "status": "PASS" if funding_ok else "IN_PROGRESS",
        },
        "liquidations": {
            "provider_semantics": "ONE_SNAPSHOT_PER_SYMBOL_PER_1000MS",
            "confirmed_pong_minutes": len(pongs),
            "expected_minutes": expected_minutes,
            "uptime_rate": f"{liq_rate:.6f}",
            "status": liq_status,
        },
        "seven_day_acceptance": (
            "PASS" if oi_all_symbols_ok
            and funding_ok and liq_status == "PASS"
            else "PARTIAL_LIQUIDATIONS" if (
                oi_all_symbols_ok
                and funding_ok and liq_status == "LIQ_SNAPSHOT_PARTIAL"
            ) else "IN_PROGRESS"
        ),
    }


def verify_flows(root: Path, *, expected_heads: dict[str, str] | None = None) -> dict:
    store = FlowStore(root)
    heads = store.verify(expected_heads=expected_heads)
    for stream in ("oi", "funding", "liquidations"):
        ids = [row["event_id"] for row in store.events(stream)]
        if len(ids) != len(set(ids)):
            raise FlowVerificationError("DUPLICATE_FLOW_IDS")
        if any(row["event_type"] == "SCHEMA_DRIFT" for row in store.events(stream)):
            raise FlowVerificationError("SCHEMA_DRIFT_FAIL_CLOSED")
    count = sum(len(store.events(s)) for s in ("oi", "funding", "liquidations"))
    size = sum(p.stat().st_size for p in Path(root).glob("*.jsonl"))
    return {"events": count, "files": len(heads), "bytes": size,
            "heads": heads, "integrity": "FLOWS_OK"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="data/flows")
    parser.add_argument("--expected-heads", help="Independent immutable JSON map")
    parser.add_argument("--start-ms", type=int, help="7-day UTC aligned start")
    parser.add_argument("--end-ms", type=int, help="7-day UTC end")
    parser.add_argument("--report-json", help="Optional deterministic JSON output")
    args = parser.parse_args()
    try:
        expected_heads = None
        if args.expected_heads:
            expected_heads = json.loads(Path(args.expected_heads).read_text())
        integrity = verify_flows(Path(args.root), expected_heads=expected_heads)
        report = {"integrity": integrity, "coverage": "NOT_ASSESSED"}
        if args.start_ms is not None or args.end_ms is not None:
            if args.start_ms is None or args.end_ms is None:
                raise FlowVerificationError("BOTH_COVERAGE_BOUNDS_REQUIRED")
            report["coverage"] = coverage_report(
                FlowStore(args.root), symbols_from_config(),
                start_ms=args.start_ms, end_ms=args.end_ms,
            )
        if args.report_json:
            Path(args.report_json).write_text(
                json.dumps(report, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")) + "\n", encoding="utf-8",
            )
        if isinstance(report["coverage"], dict):
            acceptance = report["coverage"]["seven_day_acceptance"]
            if acceptance == "IN_PROGRESS":
                raise FlowVerificationError("SEVEN_DAY_COVERAGE_IN_PROGRESS")
            if acceptance == "PARTIAL_LIQUIDATIONS":
                print("FLOWS_OK: LIQ_SNAPSHOT_PARTIAL (NOT FULL LIQ COVERAGE)")
            else:
                print("FLOWS_OK")
        else:
            print("FLOWS_OK")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("FLOWS_FAIL: " + str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
