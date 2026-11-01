"""RESET-05 part 3: negative immutable strategy-registration and risk gates."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.platform import sha_ledger
from research.platform import strategy_registry as r

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research/registry"


def load(strategy_id):
    return r.parse_canonical((REGISTRY / "strategies" / f"{strategy_id}.json").read_bytes())


def isolated(tmp_path):
    dest = tmp_path / "registry"
    shutil.copytree(REGISTRY, dest)
    return dest


def test_two_registered_candidates_validate_with_immutable_receipts():
    assert set(path.stem for path in (REGISTRY / "strategies").glob("*.json")) == {
        "H1_CARRY_001", "VIRTUAL_MECH_920", "CONVEX_RUNNER_001"
    }
    assert r.verify_registry(REGISTRY) == "7b37c738dbd24ab2d8e667591fdf19488017f1217c6c35c350699184d282f471"
    assert len((REGISTRY / "registry_witness.jsonl").read_text().splitlines()) == 4


def test_both_candidates_block_paper_and_live():
    for key in ("H1_CARRY_001", "VIRTUAL_MECH_920", "CONVEX_RUNNER_001"):
        doc = load(key)
        assert doc["market"]["scope"] == "BINANCE_USDT_M_FUTURES"
        assert doc["eligibility"]["paper_allowed"] is False
        assert doc["eligibility"]["live_allowed"] is False
        assert doc["eligibility"]["block_reasons"]


def test_virtual_920_owner_limits_are_exact_not_inferred():
    doc = load("VIRTUAL_MECH_920")
    assert doc["risk"]["initial_equity_usdt"] == "920"
    assert doc["risk"]["per_trade_risk_fraction"] == "0.04"
    assert doc["risk"]["per_trade_risk_usdt"] == "36.8"
    assert doc["risk"]["kill_equity_usdt"] == "736"
    assert doc["risk"]["max_notional_usdt"] == "2760"
    assert doc["risk"]["max_leverage"] == "3"
    assert doc["risk"]["max_drawdown_fraction"] == "0.20"
    assert doc["risk"]["regime_state"] == "NEUTRAL"
    assert doc["risk"]["ladder_fractions"] == ["0.02", "0.03", "0.04"]
    assert doc["version"] == "1.1"
    assert doc["execution"]["max_open_positions"] == 1
    assert doc["execution"]["order_type"] == "LIMIT_ONLY"
    assert len(doc["universe"]["tradable_symbols"]) == 10
    assert "BTCUSDT" in doc["universe"]["context_anchors"]
    assert "BTCUSDT" not in doc["universe"]["tradable_symbols"]
    assert "OPUSDT" not in doc["universe"]["tradable_symbols"]
    assert any(
        x["symbol"] == "OPUSDT" and x["blocked_through_utc_date"] == "2026-11-03"
        for x in doc["universe"]["exclusions"]
    )
    assert "APPROVED_MAX_NOTIONAL_USDT_NOT_FOUND_IN_ACCOUNT_AUDIT" not in doc["eligibility"]["block_reasons"]
    assert "OWNER_ENTRY_EXIT_RULES_NOT_PINNED" in doc["eligibility"]["block_reasons"]
    assert "2908" in " ".join(doc["evidence"]["unresolved"])
    assert "15000" in " ".join(doc["evidence"]["unresolved"])


def test_h1_source_only_no_fake_profit_or_funding_forecast():
    doc = load("H1_CARRY_001")
    assert doc["eligibility"]["status"] == "ECONOMIC_NOT_TESTED"
    assert doc["market"]["two_leg_spot_research_only"] is True
    assert doc["costs"]["fee_bps"] is None
    assert doc["risk"]["max_notional_usdt"] is None
    original = (ROOT / doc["source"]["code_path"]).read_bytes()
    assert r.git_blob_sha(original) == doc["source"]["code_blob_sha"]


def test_gate_thresholds_are_preregistered_and_identical():
    for key in ("H1_CARRY_001", "VIRTUAL_MECH_920"):
        gates = load(key)["gates"]
        assert gates["laboratory_min_trades"] == 30
        assert gates["laboratory_pf_strictly_greater_than"] == "1.2"
        assert gates["paper_min_closed_trades"] == 100
        assert gates["paper_min_calendar_days"] == 30
        if key == "VIRTUAL_MECH_920":
            assert gates["paper_max_drawdown_fraction"] == "0.20"
        else:
            assert gates["paper_max_drawdown_fraction"] is None


def test_mutating_existing_manifest_breaks_sha_witness(tmp_path):
    root = isolated(tmp_path)
    path = root / "strategies" / "VIRTUAL_MECH_920.json"
    doc = r.parse_canonical(path.read_bytes())
    doc["risk"]["per_trade_risk_fraction"] = "0.05"
    path.write_bytes(r.canonical_json(doc))
    with pytest.raises(r.RegistryError, match="REGISTERED_SOURCE_TAMPERED"):
        r.verify_registry(root)


def test_replacing_witness_payload_without_rehash_is_detected(tmp_path):
    root = isolated(tmp_path)
    path = root / "registry_witness.jsonl"
    raw = path.read_bytes()
    assert b"5f4761fefe862824db69c47ac8eb85a0d9bd24c2" in raw
    path.write_bytes(raw.replace(
        b"5f4761fefe862824db69c47ac8eb85a0d9bd24c2",
        b"6f4761fefe862824db69c47ac8eb85a0d9bd24c2",
        1,
    ))
    with pytest.raises(r.RegistryError, match="BROKEN_REGISTRY_WITNESS"):
        r.verify_registry(root)


def test_added_unwitnessed_manifest_is_rejected(tmp_path):
    root = isolated(tmp_path)
    p = root / "strategies" / "THIRD_001.json"
    p.write_bytes((root / "strategies" / "H1_CARRY_001.json").read_bytes())
    with pytest.raises(r.RegistryError, match="REGISTRY_FILE_COUNT_WITNESS_MISMATCH"):
        r.verify_registry(root)


def test_removed_manifest_or_receipt_is_rejected(tmp_path):
    root = isolated(tmp_path)
    (root / "strategies" / "H1_CARRY_001.json").unlink()
    with pytest.raises(r.RegistryError, match="REGISTRY_FILE_COUNT_WITNESS_MISMATCH"):
        r.verify_registry(root)


def test_weakening_gate_fails_schema():
    doc = load("VIRTUAL_MECH_920")
    doc["gates"]["paper_min_closed_trades"] = 99
    with pytest.raises(r.RegistryError, match="GATE_THRESHOLD_WEAKENED"):
        r.validate_entry(doc)
    doc = load("VIRTUAL_MECH_920")
    doc["gates"]["laboratory_pf_strictly_greater_than"] = "1.1"
    with pytest.raises(r.RegistryError, match="GATE_PF_WEAKENED"):
        r.validate_entry(doc)


def test_wrong_risk_arithmetic_and_owner_kill_rejected():
    doc = load("VIRTUAL_MECH_920")
    doc["risk"]["per_trade_risk_usdt"] = "40"
    with pytest.raises(r.RegistryError, match="RISK_BUDGET_ARITHMETIC_MISMATCH"):
        r.validate_entry(doc)
    doc = load("VIRTUAL_MECH_920")
    doc["risk"]["kill_equity_usdt"] = "700"
    doc["gates"]["kill_equity_usdt"] = "700"
    with pytest.raises(r.RegistryError, match="OWNER_VIRTUAL_CONTRACT_MISMATCH"):
        r.validate_entry(doc)


def test_spot_or_unapproved_pair_fails_schema():
    doc = load("VIRTUAL_MECH_920")
    doc["market"]["scope"] = "SPOT"
    with pytest.raises(r.RegistryError, match="FUTURES_PAPER_SCOPE_REQUIRED"):
        r.validate_entry(doc)
    doc = load("VIRTUAL_MECH_920")
    doc["universe"]["tradable_symbols"].append("OPUSDT")
    with pytest.raises(r.RegistryError, match="COOLDOWN_SYMBOL_CANNOT_BE_TRADABLE"):
        r.validate_entry(doc)


def test_cannot_silently_flip_paper_or_live_allowed():
    doc = load("VIRTUAL_MECH_920")
    doc["eligibility"]["paper_allowed"] = True
    with pytest.raises(r.RegistryError, match="UNVERIFIED_STRATEGY_CANNOT_BE_ENABLED"):
        r.validate_entry(doc)
    doc = load("H1_CARRY_001")
    doc["eligibility"]["live_allowed"] = True
    with pytest.raises(r.RegistryError, match="UNVERIFIED_STRATEGY_CANNOT_BE_ENABLED"):
        r.validate_entry(doc)


def test_no_float_cost_leverage_notional_accepted():
    for field in ("max_notional_usdt", "max_leverage"):
        doc = load("VIRTUAL_MECH_920")
        doc["risk"][field] = 3000.0
        with pytest.raises(r.RegistryError, match="RISK_VALUE_MUST_BE_DECIMAL_STRING"):
            r.validate_entry(doc)
    doc = load("VIRTUAL_MECH_920")
    doc["costs"]["fee_bps"] = float("nan")
    with pytest.raises(r.RegistryError, match="RISK_VALUE_MUST_BE_DECIMAL_STRING"):
        r.validate_entry(doc)


def test_history_guard_allows_only_witnessed_reset06_amendment(monkeypatch):
    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(stdout="M\tresearch/registry/strategies/VIRTUAL_MECH_920.json\n")
    monkeypatch.setattr(r.subprocess, "run", fake_run)
    r.verify_history(REGISTRY)


def test_unique_parent_and_version_contract():
    doc = load("VIRTUAL_MECH_920")
    doc["parent_strategy_id"] = doc["strategy_id"]
    with pytest.raises(r.RegistryError, match="INVALID_PARENT_STRATEGY_ID"):
        r.validate_entry(doc)
    doc = load("H1_CARRY_001")
    assert doc["parent_strategy_id"] is None


def test_existing_sha_ledger_unchanged_and_valid():
    lines = (REGISTRY / "registry_witness.jsonl").read_text().splitlines()
    events = [json.loads(line) for line in lines]
    assert sha_ledger.verify(events) == events[-1]["record_sha256"]


def test_noncanonical_json_does_not_hide_revisions():
    doc = load("H1_CARRY_001")
    raw = json.dumps(doc).encode() + b"\n"
    with pytest.raises(r.RegistryError, match="INVALID_REGISTRY_JSON"):
        r.parse_canonical(raw)


def test_no_planner_or_order_clients_in_validator():
    assert not hasattr(r, "place_order")
    assert not hasattr(r, "order_api")
    assert not hasattr(r, "binance_client")


def test_history_guard_rejects_other_registered_file_edits(monkeypatch):
    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(stdout="M\tresearch/registry/strategies/H1_CARRY_001.json\n")
    monkeypatch.setattr(r.subprocess, "run", fake_run)
    with pytest.raises(r.RegistryError, match="UNAUTHORIZED_REGISTERED_FILE_EDIT"):
        r.verify_history(REGISTRY)


def test_reset06_amendment_receipt_cannot_be_silently_removed(tmp_path):
    root = isolated(tmp_path)
    witness = root / "registry_witness.jsonl"
    witness.write_text("\n".join(witness.read_text().splitlines()[:2]) + "\n")
    with pytest.raises(r.RegistryError, match="REGISTRY_FILE_COUNT_WITNESS_MISMATCH"):
        r.verify_registry(root)


def test_convex_runner_is_only_blocked_skeleton():
    doc = load("CONVEX_RUNNER_001")
    assert doc["eligibility"]["status"] == "BLOCKED_UNTIL_BACKTEST"
    assert not doc["eligibility"]["paper_allowed"]
    assert not doc["eligibility"]["live_allowed"]
    assert doc["risk"]["max_leverage"] == "15"
