"""Blind additional snapshot dates: check V4 selection port against original TS.

The initial 300 parity snapshots used fractions .20/.35/.50/.65/.80/1.0.
This second set uses different predetermined fractions and was not examined
while constructing the port. It is not an independent economic OOS test.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

from ember.research.mtf_v2_bars import H4
from ember.research.mtf_v4_source_selection import source_visible_active_zones
from scripts.audit_mtf_v4_native_parity import (
    DATA_DIR,
    RUNNER,
    compare,
    to_candle,
    verify_source,
)
from scripts.run_mtf_v3_universe import load_batched

HELDOUT_FRACTIONS = (.27, .43, .58, .74, .91)


def run(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    shas = verify_source()
    sources, receipts = load_batched(DATA_DIR)
    jobs = []
    predictions = {}
    for symbol in sorted(sources):
        bars = sources[symbol]["4h"]
        for fraction in HELDOUT_FRACTIONS:
            n = min(len(bars), max(140, int(len(bars) * fraction)))
            prefix = bars[:n]
            asof = prefix[-1].ts + H4
            predictions[(symbol, n)] = source_visible_active_zones(prefix)
            jobs.append({
                "symbol": symbol, "n": n, "asof": asof,
                "candles": [to_candle(b) for b in prefix],
            })
    result = subprocess.run(
        ["node", "--experimental-strip-types", str(RUNNER)],
        input=json.dumps({"snapshots": jobs}, separators=(",", ":")),
        text=True, capture_output=True, check=True, timeout=240,
    )
    native_snapshots = json.loads(result.stdout)["snapshots"]
    if len(native_snapshots) != len(jobs):
        raise ValueError("native heldout snapshot count mismatch")
    counts = Counter()
    mismatch_examples = []
    for item in native_snapshots:
        stats, mismatches = compare(
            item["zones"], predictions[(item["symbol"], item["n"])]
        )
        counts["snapshots"] += 1
        counts["native_active_levels"] += stats["native_active"]
        counts["port_active_levels"] += stats["v3_active"]
        counts["exact_matches"] += stats["exact_active_matches"]
        counts["missing"] += stats["native_only_active"]
        counts["extra"] += stats["replica_only_active"]
        counts["wrong_geometry"] += stats["active_geometry_mismatch"]
        for difference in mismatches[:3]:
            if len(mismatch_examples) < 50:
                mismatch_examples.append({
                    "symbol": item["symbol"], "n": item["n"], **difference,
                })
    report = {
        "status": "V4_4H_ZONE_SELECTION_HOLDOUT_ONLY",
        "sample_kind": "additional 5 time points per symbol; NOT true market OOS",
        "original_snapshots_previously_audited": 300,
        "contract_count": len(sources),
        "fractions": HELDOUT_FRACTIONS,
        "pinned_smoke_blobs": shas,
        "input_batches": receipts,
        "counts": dict(counts),
        "accept_selection_presence_geometry": not (
            counts["missing"] or counts["extra"] or counts["wrong_geometry"]
        ),
        "notes": [
            "Only active zone inclusion/bounds compared, not scores/ranking.",
            "No trades or price outcome labels used; no hypothesis threshold tuning.",
            "Source origin-to-confirmation invalidations intentionally included.",
            "Not a profitability, margin, mark, funding, fill or risk test.",
        ],
    }
    (out_dir / "selection_holdout_summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "selection_holdout_differences.json").write_text(
        json.dumps(mismatch_examples, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "accept_selection_presence_geometry": report["accept_selection_presence_geometry"],
        "counts": report["counts"],
        "contract_count": report["contract_count"],
    }, sort_keys=True))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir", type=Path, default=Path("results/mtf_v4_parity"),
    )
    args = parser.parse_args()
    summary = run(args.out_dir)
    if not summary["accept_selection_presence_geometry"]:
        raise SystemExit("SOURCE_PARITY_MISMATCH: inspect archived heldout evidence")


if __name__ == "__main__":
    main()
