"""V3 research-only diagnostic: causal non-overlap and market-wide signal clustering.

This does NOT model a financed futures portfolio, mark-price liquidation, fills,
funding, borrowing, or shared margin. It tests whether duplicated or overlapping
hypotheses inflate apparent event independence. No strategy rules are changed.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

MILLIS_PER_DAY = 86_400_000
FAMILY_PRIORITY = {"order_block": 0, "swing": 1, "fvg": 2}


def as_simulated(rows: list[dict], variant: str) -> list[dict]:
    return [
        row for row in rows
        if row.get("research_variant") == variant and row.get("status") == "SIMULATED"
    ]


def choose_symbol_nonoverlap(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """One open research hypothesis per contract, with an ex-ante tie-break.

    Ordering uses known entry clock, zone family, original contact clock,
    and event_id. It does not use realized PnL or future exit reason.
    """
    ordered = sorted(
        rows,
        key=lambda row: (
            row["entry_at"],
            FAMILY_PRIORITY.get(row["zone_family"], 99),
            row["contact_at"],
            row["event_id"],
        ),
    )
    busy_until: dict[str, int] = {}
    accepted: list[dict] = []
    rejected: list[dict] = []
    for row in ordered:
        symbol = row["symbol"]
        if row["entry_at"] < busy_until.get(symbol, -1):
            rejected.append(row)
            continue
        accepted.append(row)
        busy_until[symbol] = row["exit_at"]
    return accepted, rejected


def describe(rows: list[dict]) -> dict:
    """Nominal trade-level statistics, not return on a shared wallet."""
    if not rows:
        return {
            "events": 0,
            "mean_after_stress_pct_nominal": None,
            "win_fraction": None,
            "stop_fraction": None,
            "distinct_symbols": 0,
            "distinct_utc_days": 0,
            "day_equal_weight_mean_pct_nominal": None,
            "days_with_3plus_symbols": 0,
            "max_distinct_symbols_one_day": 0,
            "hours_with_3plus_symbols": 0,
        }
    daily: dict[int, list[dict]] = defaultdict(list)
    hourly: dict[int, set[str]] = defaultdict(set)
    for row in rows:
        daily[row["entry_at"] // MILLIS_PER_DAY].append(row)
        hourly[row["entry_at"] // 3_600_000].add(row["symbol"])
    returns = [row["stress_proxy_nominal_pct"] for row in rows]
    day_means = [
        sum(x["stress_proxy_nominal_pct"] for x in events) / len(events)
        for events in daily.values()
    ]
    stops = {"STOP", "GAP_STOP", "BOTH_STOP_FIRST"}
    return {
        "events": len(rows),
        "mean_after_stress_pct_nominal": round(sum(returns) / len(returns), 6),
        "win_fraction": round(sum(x > 0 for x in returns) / len(returns), 6),
        "stop_fraction": round(
            sum(row["exit_reason"] in stops for row in rows) / len(rows), 6
        ),
        "distinct_symbols": len({row["symbol"] for row in rows}),
        "distinct_utc_days": len(daily),
        "day_equal_weight_mean_pct_nominal": round(
            sum(day_means) / len(day_means), 6
        ),
        "days_with_3plus_symbols": sum(
            len({row["symbol"] for row in events}) >= 3
            for events in daily.values()
        ),
        "max_distinct_symbols_one_day": max(
            len({row["symbol"] for row in events}) for events in daily.values()
        ),
        "hours_with_3plus_symbols": sum(
            len(symbols) >= 3 for symbols in hourly.values()
        ),
    }


def audit(rows: list[dict]) -> dict:
    output = {
        "status": "DIAGNOSTIC_ONLY_NOT_PORTFOLIO_NOT_VERIFIED",
        "tie_break": "earliest_entry_then_OB_swing_FVG_then_contact_then_event_id",
        "variants": {},
        "limitations": [
            "Sequential de-overlap is one-at-a-time per symbol, not an executed portfolio",
            "The source stress haircut of 0.35pct is hypothetical, not observed costs",
            "Day clustering is descriptive; shared BTC exposure remains correlated",
            "No mark/funding/liquidation/margin/spread/15m source-native execution",
            "No OOS, no causal feature discovery, no parameters fitted",
        ],
    }
    for variant in ("PRICE_ONLY", "TAKER_CONFIRMED"):
        original = as_simulated(rows, variant)
        selected, overlapping = choose_symbol_nonoverlap(original)
        output["variants"][variant] = {
            "all_entry_hypotheses": describe(original),
            "one_at_a_time_per_symbol": describe(selected),
            "overlapping_hypotheses_removed": len(overlapping),
            "overlap_fraction": round(
                len(overlapping) / len(original), 6
            ) if original else None,
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    path = args.out_dir / "structural_transfer_paths.jsonl"
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    result = audit(rows)
    (args.out_dir / "independence_audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
