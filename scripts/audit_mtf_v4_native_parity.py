"""As-of, source-native SMOKE 4H POI vs V3 research parity audit.

Data are the frozen Binance USDT-M Futures V3 50-contract CSV batches.
Native TS modules remain completely unchanged, pinned by original blob SHA.
No strategy changes, no trading, no OOS profitability claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from ember.research.mtf_v2_bars import H4, FlowBar
from ember.research.mtf_v3_zones import build_source_zones
from scripts.run_mtf_v3_universe import DATA_DIR, load_batched

SOURCE_DIR = Path("research/mtf_v4_native_smoke/source")
RUNNER = Path("research/mtf_v4_native_smoke/native_zones.mjs")
SOURCE_BLOBS = {
    "types.ts": "e9082a351d7fb829184f3687570ca2a1e764878b",
    "math.ts": "125f8551a0fa27b093dd9e6ab94a146cd1607319",
    "structure.ts": "7f8a18913d0674ab873964c43c18f32236fcf31a",
    "zones.ts": "f5ca1bd6a7757b8574d3cbd833abb9b0b077405d",
}
FAMILIES = ("order_block", "swing", "fvg")


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()


def verify_source() -> dict[str, str]:
    digests = {}
    for name, expected in SOURCE_BLOBS.items():
        raw = (SOURCE_DIR / name).read_bytes()
        actual = git_blob_sha(raw)
        if actual != expected:
            raise ValueError(f"source must remain byte-identical: {name}, {actual}")
        digests[name] = actual
    return digests


def snapshot_sizes(n: int) -> list[int]:
    """Predefined equally spaced horizons, not selected by profitability."""
    return sorted({max(140, min(n, int(n * f))) for f in (.20, .35, .50, .65, .80, 1.0)})


def key(zone: dict) -> tuple[str, str, int]:
    return zone["family"], zone["kind"], int(zone["origin_at"])


def same_geometry(a: dict, b: dict) -> bool:
    for prop in ("low", "high"):
        left, right = float(a[prop]), float(b[prop])
        if abs(left - right) > max(1e-9, max(abs(left), abs(right)) * 1e-9):
            return False
    return True


def compare(reference: list[dict], replica: list[dict]) -> tuple[dict, list[dict]]:
    """Compare ACTIVE native zones with ACTIVE replica zones, no future labels."""
    ref_all = {key(z): z for z in reference}
    rep_all = {key(z): z for z in replica}
    ref = {k: z for k, z in ref_all.items() if z["active"]}
    rep = {k: z for k, z in rep_all.items() if z["active"]}
    misses = sorted(ref.keys() - rep.keys())
    extras = sorted(rep.keys() - ref.keys())
    common = sorted(ref.keys() & rep.keys())
    geometry = [k for k in common if not same_geometry(ref[k], rep[k])]
    discrepancies = []
    for k in misses:
        discrepancies.append({
            "type": "NATIVE_ACTIVE_ABSENT_IN_V3",
            "key": list(k),
            "native": ref[k],
            "v3_inactive_or_missing": rep_all.get(k),
        })
    for k in extras:
        discrepancies.append({
            "type": "V3_ACTIVE_NOT_NATIVE_ACTIVE",
            "key": list(k),
            "native_inactive_or_missing": ref_all.get(k),
            "v3": rep[k],
        })
    for k in geometry:
        discrepancies.append({
            "type": "ACTIVE_GEOMETRY_MISMATCH",
            "key": list(k),
            "native": ref[k],
            "v3": rep[k],
        })
    families = {}
    for family in FAMILIES:
        families[family] = {
            "native_active": sum(z["family"] == family for z in ref.values()),
            "v3_active": sum(z["family"] == family for z in rep.values()),
            "missing": sum(k[0] == family for k in misses),
            "extra": sum(k[0] == family for k in extras),
            "geometry": sum(k[0] == family for k in geometry),
        }
    return {
        "native_all": len(reference),
        "v3_all": len(replica),
        "native_active": len(ref),
        "v3_active": len(rep),
        "native_only_active": len(misses),
        "replica_only_active": len(extras),
        "active_geometry_mismatch": len(geometry),
        "exact_active_matches": len(common) - len(geometry),
        "by_family": families,
    }, discrepancies


def to_candle(b: FlowBar) -> dict:
    return {
        "time": b.ts, "open": b.open, "high": b.high,
        "low": b.low, "close": b.close, "volume": b.volume,
    }


def build_snapshots(pool: dict) -> tuple[list[dict], dict[tuple[str, int], list[dict]]]:
    native_jobs = []
    candidates = {}
    for symbol in sorted(pool):
        series = pool[symbol]["4h"]
        for n in snapshot_sizes(len(series)):
            prefix = series[:n]
            asof = prefix[-1].ts + H4
            zones, _ = build_source_zones(prefix)
            candidates[(symbol, n)] = [{
                "family": z.family, "kind": z.kind, "origin_at": z.origin_at,
                "low": z.low, "high": z.high, "active": z.known_active(asof),
                "id": z.zone_id, "available_at": z.available_at,
                "broken_at": z.broken_at, "expires_at": z.expires_at,
            } for z in zones]
            native_jobs.append({
                "symbol": symbol, "n": n, "asof": asof,
                "candles": [to_candle(b) for b in prefix],
            })
    return native_jobs, candidates


def run(out_dir: Path, data_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    original_shas = verify_source()
    pool, source_receipts = load_batched(data_dir)
    jobs, candidates = build_snapshots(pool)
    stdin = json.dumps({"snapshots": jobs}, separators=(",", ":"))
    completed = subprocess.run(
        ["node", "--experimental-strip-types", str(RUNNER)],
        input=stdin, text=True, capture_output=True, check=True, timeout=240,
    )
    native = json.loads(completed.stdout)["snapshots"]
    if len(native) != len(jobs):
        raise ValueError("native/replica snapshot count mismatch")

    per_snapshot = []
    sample = []
    discrepancy_counts: Counter[str] = Counter()
    family_totals: dict[str, Counter[str]] = {
        family: Counter() for family in FAMILIES
    }
    overall = Counter()
    for item in native:
        symbol, n, asof = item["symbol"], item["n"], item["asof"]
        replica = candidates[(symbol, n)]
        stats, diffs = compare(item["zones"], replica)
        row = {"symbol": symbol, "n": n, "asof": asof, **stats}
        per_snapshot.append(row)
        for field in (
            "native_active", "v3_active", "native_only_active",
            "replica_only_active", "active_geometry_mismatch", "exact_active_matches",
        ):
            overall[field] += stats[field]
        for family in FAMILIES:
            family_totals[family].update(stats["by_family"][family])
        discrepancy_counts.update(d["type"] for d in diffs)
        eligible_keys = set(item["eligible_keys"])
        for d in diffs:
            if d["type"] == "V3_ACTIVE_NOT_NATIVE_ACTIVE":
                if d["native_inactive_or_missing"] is not None:
                    state = "NATIVE_INACTIVE"
                elif "|".join(map(str, d["key"])) in eligible_keys:
                    state = "NATIVE_SOURCE_DEDUP_EXCLUSION"
                else:
                    state = "OUTSIDE_NATIVE_GENERATION_WINDOW"
                discrepancy_counts[f"V3_EXTRA_CAUSE_{state}"] += 1
                discrepancy_counts[f"V3_EXTRA_{d['key'][0]}_{state}"] += 1
        for d in diffs[:4]:
            if len(sample) < 120:
                sample.append({"symbol": symbol, "n": n, "asof": asof, **d})
    summary = {
        "status": "SOURCE_NATIVE_PARITY_DIAGNOSTIC_ONLY",
        "decision": "EXACT_ACTIVE_PARITY" if not discrepancy_counts else "PARITY_NOT_PROVEN",
        "scope": "frozen 50-contract Binance USDT-M 4H candle snapshots",
        "native_algorithm": "original SMOKE buildZones(prefix, '4h') from pinned TS blobs",
        "replica_algorithm": "EMBER V3 build_source_zones(prefix) known_active(asof)",
        "snapshot_policy": "six preselected fractions of each symbol history; only closed candles",
        "source_blobs": original_shas,
        "source_batch_sha256": source_receipts,
        "contracts": len(pool),
        "snapshots": len(per_snapshot),
        "overall": dict(overall),
        "family_totals": {k: dict(v) for k, v in family_totals.items()},
        "discrepancy_types": dict(discrepancy_counts),
        "limitations": [
            "Zone parity is not native trading strategy or exchange execution parity.",
            "Repeated as-of snapshots for same symbol are not independent observations.",
            "No mark/funding/margin/portfolio/OOS economics; zero verified candidates.",
            "Source scoring uses past-from-pivot bars up to asof; no future past asof.",
            "Do not optimize entry filters on these snapshots.",
        ],
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    with (out_dir / "snapshots.jsonl").open("w", encoding="utf-8") as handle:
        for row in per_snapshot:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (out_dir / "mismatch_samples.jsonl").open("w", encoding="utf-8") as handle:
        for row in sample:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({
        "status": summary["decision"],
        "contracts": summary["contracts"],
        "snapshots": summary["snapshots"],
        "overall": summary["overall"],
        "by_family": summary["family_totals"],
        "types": summary["discrepancy_types"],
    }, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("results/mtf_v4_parity"))
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    run(args.out_dir, args.data_dir)


if __name__ == "__main__":
    main()
