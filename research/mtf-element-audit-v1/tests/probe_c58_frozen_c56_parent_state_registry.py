#!/usr/bin/env python3
"""C58 replay over the complete frozen C56 evidence; no new market download.

This validates semantic identity/state on all 542 original-source parent
records. It is NOT an independent original-60ZIP revalidation and not a trade
backtest. C56 source bytes remain unchanged and are SHA pinned in the output.
"""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "d05"))

from c56_crypto_native5m_1h_raid_bos_cross_tf import C56CrossTimeframeParent
from c58_route_c_parent_object_state import (
    BOTH, ONLY_3M, ONLY_5M, UNKNOWN_3M, UNKNOWN_5M,
    NativeSourceCoverage, build_parent_state_registry,
    identify_route_c_parent_state,
)

SOURCE = ROOT / "evidence/c56/C56_ORIGINAL_60ZIP_SAME_1H_PARENT_3M_NATIVE5M_COMPLETE_SOURCE.json"
PINNED = ROOT / "evidence/c58/C58_FROZEN_C56_COMPLETE_PARENT_OBJECT_STATE_REGISTRY.json"
AS_OF = 1_790_985_600_000  # 2026-10-03 00:00 UTC, exact C56 closed-source END.


def restore(event):
    return C56CrossTimeframeParent(
        symbol=event["symbol"], raid_type=event["raid_type"],
        first_1h_pivot_center_ms=event["first_1h_pivot_center_ms"],
        first_1h_breach_ms=event["first_1h_breach_ms"],
        raid_closed_known_ms=event["raid_closed_known_ms"],
        original_3m_bos_raw_id=event["original_3m_bos_raw_id"],
        original_3m_bos_known_ms=event["original_3m_bos_known_ms"],
        original_5m_bos_raw_id=event["original_5m_bos_raw_id"],
        original_5m_bos_known_ms=event["original_5m_bos_known_ms"],
        source_status=event["source_status"],
        author_bos_approved=event["author_bos_approved"],
        author_fill_approved=event["author_fill_approved"],
        blockers=tuple(event["blockers"]), orders=tuple(event["orders"]),
        trades=tuple(event["trades"]), readiness=event["readiness"],
    )


def run(out=None):
    raw = SOURCE.read_bytes()
    source = json.loads(raw)
    assert source["schema"] == "EMBER_C56_FRESH_ORIGINAL_60ZIP_NATIVE3M_NATIVE5M_SAME_HOURLY_FIRST_RAID_PARENT_V1"
    assert source["source_unique_1h_parents"] == 542
    assert source["source_shared_1h_parents"] == 509
    assert source["period_utc"] == ["2026-09-01", "2026-10-02"]
    assert source["orders"] == source["trades"] == source["fills"] == 0
    states = []
    for market in source["markets"]:
        c3 = NativeSourceCoverage("3m", True, AS_OF, market["original_3m_bars"])
        c5 = NativeSourceCoverage("5m", True, AS_OF, market["original_5m_bars"])
        for event in market["parent_matched_events"]:
            states.append(identify_route_c_parent_state(
                restore(event), as_of_ms=AS_OF, coverage_3m=c3, coverage_5m=c5,
            ))
    assert len(states) == 542
    registry = build_parent_state_registry(states)
    assert len(registry) == len({x.parent_id for x in registry}) == 542
    assert registry == build_parent_state_registry(reversed(states))
    try:
        build_parent_state_registry((states[0], states[0]))
    except ValueError as exc:
        assert str(exc) == "C58_DUPLICATE_1H_PARENT_IDENTITY"
    else:
        raise AssertionError("C58_DUPLICATE_PARENT_WAS_COUNTED_TWICE")
    counts = Counter(x.observation_state for x in registry)
    assert counts == {BOTH: 509, ONLY_3M: 30, ONLY_5M: 3}
    # Reclassify only the single-TF records with explicitly incomplete other-TF
    # coverage. Absence must collapse to UNKNOWN; observed dual events remain.
    incomplete = []
    for state in registry:
        incomplete.append(identify_route_c_parent_state(
            state.parent, as_of_ms=AS_OF,
            coverage_3m=NativeSourceCoverage("3m", state.coverage_3m.complete,
                AS_OF, state.coverage_3m.original_native_rows),
            coverage_5m=NativeSourceCoverage("5m", False,
                AS_OF, state.coverage_5m.original_native_rows),
        ))
    incomplete3 = [identify_route_c_parent_state(
        state.parent, as_of_ms=AS_OF,
        coverage_3m=NativeSourceCoverage("3m", False, AS_OF,
            state.coverage_3m.original_native_rows),
        coverage_5m=state.coverage_5m,
    ) for state in registry]
    unknown5 = Counter(x.observation_state for x in incomplete)
    unknown3 = Counter(x.observation_state for x in incomplete3)
    assert unknown5 == {BOTH: 509, ONLY_5M: 3, UNKNOWN_5M: 30}
    assert unknown3 == {BOTH: 509, ONLY_3M: 30, UNKNOWN_3M: 3}
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    assert blob == "98f087a731d30c2191dc443038c371751456f316"
    document = {
        "schema": "EMBER_C58_FROZEN_C56_PARENT_OBJECT_STATE_REGISTRY_V1",
        "scope": "ADAPTED_CRYPTO_ROUTE_C_SOURCE_ONLY",
        "source_c56_git_blob": blob,
        "source_c56_sha256": hashlib.sha256(raw).hexdigest(),
        "source_c56_bytes": len(raw),
        "source_as_of_ms": AS_OF,
        "source_original_60zip_redownloaded_by_c58": False,
        "source_unique_parent_objects": len(registry),
        "observation_state_counts": dict(sorted(counts.items())),
        "incomplete_5m_control_counts": dict(sorted(unknown5.items())),
        "incomplete_3m_control_counts": dict(sorted(unknown3.items())),
        "duplicate_parent_identity_rejected": True,
        "registry_order_source_permutation_invariant": True,
        "author_object_identities_approved": 0,
        "author_bos_approved": 0,
        "orders": 0, "fills": 0, "trades": 0, "PnL": None,
        "readiness": "NOT_TRADE_READY",
        "parent_states": [asdict(x) for x in registry],
    }
    encoded = (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    if PINNED.exists():
        assert PINNED.read_bytes() == encoded, "C58_FROZEN_PARENT_STATE_BYTES_DRIFT"
    if out:
        target = Path(out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(encoded)
    print("C58_PARENT_OBJECT_STATES", json.dumps(document["observation_state_counts"], sort_keys=True))
    print("C58_UNKNOWN_CONTROLS", json.dumps({
        "3m": document["incomplete_3m_control_counts"],
        "5m": document["incomplete_5m_control_counts"],
    }, sort_keys=True))
    return document


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
