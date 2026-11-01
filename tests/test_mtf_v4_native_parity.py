"""Native-source vs replica V3 point-in-time parity auditor invariants."""
from scripts.audit_mtf_v4_native_parity import (
    compare,
    git_blob_sha,
    same_geometry,
    snapshot_sizes,
    verify_source,
)


def zone(family="order_block", active=True, low=90, high=100, origin=1):
    return {
        "family": family, "kind": "demand", "origin_at": origin,
        "low": low, "high": high, "active": active,
    }


def test_git_source_receipts_are_identical_to_smoke() -> None:
    got = verify_source()
    assert len(got) == 4
    assert got["zones.ts"] == "f5ca1bd6a7757b8574d3cbd833abb9b0b077405d"
    assert git_blob_sha(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_inactive_native_zone_is_not_native_active_but_v3_ghost_is_counted() -> None:
    summary, issues = compare([zone(active=False)], [zone(active=True)])
    assert summary["replica_only_active"] == 1
    assert summary["native_only_active"] == 0
    assert issues[0]["type"] == "V3_ACTIVE_NOT_NATIVE_ACTIVE"
    assert issues[0]["native_inactive_or_missing"]["active"] is False


def test_missing_and_wrong_geometry_separate_from_activity() -> None:
    summary, issues = compare(
        [zone(), zone(family="fvg", origin=2)],
        [zone(high=101)],
    )
    assert summary["native_only_active"] == 1
    assert summary["active_geometry_mismatch"] == 1
    assert {x["type"] for x in issues} == {
        "NATIVE_ACTIVE_ABSENT_IN_V3", "ACTIVE_GEOMETRY_MISMATCH",
    }


def test_no_future_snapshots_and_float_tolerance() -> None:
    assert snapshot_sizes(1000) == [200, 350, 500, 650, 800, 1000]
    assert same_geometry(zone(), zone(high=100 + 1e-8))
    assert not same_geometry(zone(), zone(high=101))
