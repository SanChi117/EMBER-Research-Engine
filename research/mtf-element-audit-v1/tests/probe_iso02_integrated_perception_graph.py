#!/usr/bin/env python3
"""Full frozen-evidence replay for ISO01 + ISO02; no network and no trading."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "d05"))
sys.path.insert(0, str(ROOT / "tests"))
from iso02_integrated_perception_graph import build_integrated_graph, canonical
from probe_iso01_frozen_c56_parent_state_registry import run as run_iso01

A = ROOT / "evidence/c57/C57_ORIGINAL_45ZIP_4H_FIRST_CONTACT_LATER_1H_THEN_FIRST_ANY_NATIVE15M_IMB.json"
B = ROOT / "evidence/c58/C58_ORIGINAL_45ZIP_PREKNOWN_UNSWEPT_1H_FRACTAL_INSIDE_4H_FIRST_CONTACT.json"


def run(out=None):
    # Rebuild Route C from frozen C56 instead of trusting an intermediate file.
    c_doc = run_iso01()
    c_bytes = (json.dumps(c_doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    graph = build_integrated_graph(route_a=A.read_bytes(), route_b=B.read_bytes(), route_c=c_bytes)
    encoded = (canonical(graph) + "\n").encode()
    # Independent in-process repeat must be byte-identical.
    repeat = build_integrated_graph(route_a=A.read_bytes(), route_b=B.read_bytes(), route_c=c_bytes)
    assert encoded == (canonical(repeat) + "\n").encode()
    summary = {
        "schema": "EMBER_ISO02_FULL_FROZEN_REPLAY_WITNESS_V1",
        "source_commit": graph["source_commit"],
        "objects": len(graph["objects"]),
        "objects_by_route": dict(sorted(Counter(o["route"] for o in graph["objects"]).items())),
        "objects_by_kind": dict(sorted(Counter(o["kind"] for o in graph["objects"]).items())),
        "relationships": len(graph["relationships"]),
        "relationships_by_type": dict(sorted(Counter(e["relation"] for e in graph["relationships"]).items())),
        "cross_route_relationships": graph["cross_route_relationships"],
        "scenarios": len(graph["scenarios"]),
        "scenario_states": dict(sorted(Counter(s["observed_scenario_state"] for s in graph["scenarios"]).items())),
        "graph_bytes": len(encoded), "graph_sha256": hashlib.sha256(encoded).hexdigest(),
        "repeat_byte_identical": True, "semantic_gates": graph["semantic_gates"],
        "decision_state": graph["decision_state"], "readiness": graph["readiness"],
        "orders": 0, "fills": 0, "trades": 0, "PnL": None,
        "original_market_redownloaded": False,
        "limitation": "Replay of pinned frozen evidence, not a new independent market-data attestation, author semantic certification, backtest or performance claim.",
    }
    if out:
        target = Path(out); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(encoded)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return graph, summary


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
