"""RESET-05 part 3: immutable pre-registration verification (NO trade execution).

Registered JSON records are canonical, source/risk deficits are explicit blocks.
Integrity: existing sha_ledger SHA256 chain + pinned Git blob receipt + Git
history no-edit guard in CI. A later revision MUST use a new strategy_id.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import sha_ledger

STRATEGY_RE = re.compile(r"[A-Z][A-Z0-9_]{3,79}\Z")
SYMBOL_RE = re.compile(r"[A-Z0-9]{2,18}USDT\Z")
SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
MANDATORY = frozenset({
    "schema", "strategy_id", "parent_strategy_id", "registered_on_utc",
    "hypothesis", "source", "market", "universe", "execution", "risk",
    "costs", "gates", "eligibility", "evidence",
})
RISK_FIELDS = frozenset({
    "initial_equity_usdt", "per_trade_risk_fraction",
    "per_trade_risk_usdt", "kill_equity_usdt", "max_notional_usdt",
    "max_leverage", "max_drawdown_fraction",
})
GATE_FIELDS = frozenset({
    "laboratory_min_trades", "laboratory_pf_strictly_greater_than",
    "paper_min_closed_trades", "paper_min_calendar_days",
    "paper_max_drawdown_fraction", "kill_equity_usdt",
})
COST_FIELDS = frozenset({"fee_bps", "slippage_bps", "basis"})


class RegistryError(ValueError):
    pass


def fail(code: str) -> None:
    raise RegistryError(code)


def _no_dupe_pairs(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    for k, v in pairs:
        if k in out:
            fail("DUPLICATE_JSON_KEY")
        out[k] = v
    return out


def _nonfinite(_: str) -> None:
    fail("NONFINITE_JSON")


def canonical_json(obj: dict) -> bytes:
    return sha_ledger.canonical(obj) + b"\n"


def parse_canonical(raw: bytes) -> dict:
    try:
        doc = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_no_dupe_pairs,
            parse_constant=_nonfinite,
        )
        if type(doc) is not dict or canonical_json(doc) != raw:
            fail("NONCANONICAL_REGISTRY_JSON")
        return doc
    except (ValueError, UnicodeError, TypeError) as exc:
        raise RegistryError("INVALID_REGISTRY_JSON") from exc


def _require_exact(doc: dict, names: frozenset[str]) -> None:
    if type(doc) is not dict or set(doc) != names:
        fail("SCHEMA_FIELD_MISMATCH")


def _nonempty(value: object) -> None:
    if type(value) is not str or not value.strip():
        fail("REQUIRED_NONEMPTY_STRING")


def _decimal(value: object, *, nullable=False, positive=False, nonnegative=False) -> Decimal | None:
    if value is None and nullable:
        return None
    if type(value) is not str:
        fail("RISK_VALUE_MUST_BE_DECIMAL_STRING")
    try:
        number = Decimal(value)
    except (ValueError, InvalidOperation):
        fail("INVALID_DECIMAL")
    if not number.is_finite() or (positive and number <= 0) or (nonnegative and number < 0):
        fail("INVALID_DECIMAL_RANGE")
    return number


def validate_entry(doc: dict) -> None:
    _require_exact(doc, MANDATORY)
    if doc["schema"] != "EMBER_STRATEGY_PREREG_V1":
        fail("REGISTRY_SCHEMA_VERSION")
    strategy_id = doc["strategy_id"]
    if type(strategy_id) is not str or not STRATEGY_RE.fullmatch(strategy_id):
        fail("INVALID_STRATEGY_ID")
    parent = doc["parent_strategy_id"]
    if parent is not None and (
        type(parent) is not str or not STRATEGY_RE.fullmatch(parent) or parent == strategy_id
    ):
        fail("INVALID_PARENT_STRATEGY_ID")
    try:
        if type(doc["registered_on_utc"]) is not str:
            fail("REGISTRATION_DAY_REQUIRED")
        if date.fromisoformat(doc["registered_on_utc"]).isoformat() != doc["registered_on_utc"]:
            fail("NONCANONICAL_REGISTRATION_DAY")
    except ValueError as exc:
        raise RegistryError("INVALID_REGISTRATION_DAY") from exc
    hypothesis = doc["hypothesis"]
    _require_exact(hypothesis, frozenset({"family", "thesis", "document"}))
    for value in hypothesis.values():
        _nonempty(value)
    source = doc["source"]
    _require_exact(source, frozenset({"code_path", "code_blob_sha", "status"}))
    if source["code_path"] is not None:
        _nonempty(source["code_path"])
    if source["code_blob_sha"] is not None and (
        type(source["code_blob_sha"]) is not str
        or not SHA1_RE.fullmatch(source["code_blob_sha"])
    ):
        fail("INVALID_PINNED_SOURCE_SHA")
    if (source["code_path"] is None) != (source["code_blob_sha"] is None):
        fail("SOURCE_PIN_MUST_BE_COMPLETE")
    _nonempty(source["status"])
    market = doc["market"]
    _require_exact(market, frozenset({"scope", "paper_only", "two_leg_spot_research_only"}))
    if market["scope"] != "BINANCE_USDT_M_FUTURES" or market["paper_only"] is not True:
        fail("FUTURES_PAPER_SCOPE_REQUIRED")
    if type(market["two_leg_spot_research_only"]) is not bool:
        fail("INVALID_MARKET_MODE")
    universe = doc["universe"]
    _require_exact(universe, frozenset({"tradable_symbols", "context_anchors", "exclusions"}))
    tradable = universe["tradable_symbols"]
    anchors = universe["context_anchors"]
    if (
        type(tradable) is not list or not tradable
        or type(anchors) is not list
        or not all(type(s) is str and SYMBOL_RE.fullmatch(s) for s in tradable + anchors)
        or len(set(tradable)) != len(tradable)
        or len(set(anchors)) != len(anchors)
    ):
        fail("INVALID_FUTURES_UNIVERSE")
    exclusions = universe["exclusions"]
    if type(exclusions) is not list:
        fail("INVALID_EXCLUSIONS")
    seen = set()
    for exclusion in exclusions:
        _require_exact(exclusion, frozenset({"symbol", "blocked_through_utc_date", "reason"}))
        symbol = exclusion["symbol"]
        if type(symbol) is not str or not SYMBOL_RE.fullmatch(symbol) or symbol in seen:
            fail("INVALID_EXCLUDED_SYMBOL")
        seen.add(symbol)
        _nonempty(exclusion["reason"])
        try:
            if date.fromisoformat(exclusion["blocked_through_utc_date"]).isoformat() != exclusion["blocked_through_utc_date"]:
                fail("INVALID_EXCLUSION_DATE")
        except (ValueError, TypeError) as exc:
            raise RegistryError("INVALID_EXCLUSION_DATE") from exc
    if seen.intersection(tradable):
        fail("COOLDOWN_SYMBOL_CANNOT_BE_TRADABLE")
    execution = doc["execution"]
    _require_exact(execution, frozenset({"order_type", "entry_rules", "exit_rules", "max_open_positions"}))
    for key in ("order_type", "entry_rules", "exit_rules"):
        _nonempty(execution[key])
    if execution["max_open_positions"] is not None and (
        type(execution["max_open_positions"]) is not int or execution["max_open_positions"] < 1
    ):
        fail("INVALID_POSITION_COUNT")
    risk = doc["risk"]
    _require_exact(risk, RISK_FIELDS)
    initial = _decimal(risk["initial_equity_usdt"], nullable=True, positive=True)
    fraction = _decimal(risk["per_trade_risk_fraction"], nullable=True, positive=True)
    budget = _decimal(risk["per_trade_risk_usdt"], nullable=True, positive=True)
    kill = _decimal(risk["kill_equity_usdt"], nullable=True, nonnegative=True)
    cap = _decimal(risk["max_notional_usdt"], nullable=True, positive=True)
    leverage = _decimal(risk["max_leverage"], nullable=True, positive=True)
    dd = _decimal(risk["max_drawdown_fraction"], nullable=True, positive=True)
    if fraction is not None and fraction >= 1 or dd is not None and dd >= 1:
        fail("INVALID_RISK_FRACTION")
    if initial is not None and kill is not None and kill >= initial:
        fail("INVALID_KILL_EQUITY")
    if None not in (initial, fraction, budget) and initial * fraction != budget:
        fail("RISK_BUDGET_ARITHMETIC_MISMATCH")
    if cap is not None and initial is None:
        fail("NOTIONAL_CAP_REQUIRES_EQUITY")
    costs = doc["costs"]
    _require_exact(costs, COST_FIELDS)
    fee = _decimal(costs["fee_bps"], nullable=True, nonnegative=True)
    slip = _decimal(costs["slippage_bps"], nullable=True, nonnegative=True)
    _nonempty(costs["basis"])
    if fee is not None and fee >= 10000 or slip is not None and slip >= 10000:
        fail("INVALID_COST_RATE")
    gates = doc["gates"]
    _require_exact(gates, GATE_FIELDS)
    if (
        type(gates["laboratory_min_trades"]) is not int
        or gates["laboratory_min_trades"] < 30
        or type(gates["paper_min_closed_trades"]) is not int
        or gates["paper_min_closed_trades"] < 100
        or type(gates["paper_min_calendar_days"]) is not int
        or gates["paper_min_calendar_days"] < 30
    ):
        fail("GATE_THRESHOLD_WEAKENED")
    if _decimal(gates["laboratory_pf_strictly_greater_than"], positive=True) < Decimal("1.2"):
        fail("GATE_PF_WEAKENED")
    gate_dd = _decimal(gates["paper_max_drawdown_fraction"], nullable=True, positive=True)
    gate_kill = _decimal(gates["kill_equity_usdt"], nullable=True, nonnegative=True)
    if gate_dd is not None and gate_dd >= 1:
        fail("INVALID_GATE_DRAWDOWN")
    if gate_kill != kill or gate_dd != dd:
        fail("RISK_GATE_NOT_MATCHED")
    eligibility = doc["eligibility"]
    _require_exact(eligibility, frozenset({"status", "paper_allowed", "live_allowed", "block_reasons"}))
    if (
        eligibility["status"] not in ("ECONOMIC_NOT_TESTED", "BLOCKED_INCOMPLETE_REGISTRATION")
        or eligibility["paper_allowed"] is not False
        or eligibility["live_allowed"] is not False
        or type(eligibility["block_reasons"]) is not list
        or not eligibility["block_reasons"]
        or not all(type(x) is str and x for x in eligibility["block_reasons"])
    ):
        fail("UNVERIFIED_STRATEGY_CANNOT_BE_ENABLED")
    if any(v is None for v in (cap, leverage, dd, fee, slip)) and not eligibility["block_reasons"]:
        fail("MISSING_BLOCK_REASON")
    evidence = doc["evidence"]
    _require_exact(evidence, frozenset({"authority", "unresolved"}))
    _nonempty(evidence["authority"])
    if type(evidence["unresolved"]) is not list:
        fail("INVALID_UNRESOLVED_EVIDENCE")
    if strategy_id == "VIRTUAL_MECH_920":
        if (
            initial != Decimal("920") or fraction != Decimal("0.04")
            or budget != Decimal("36.8") or kill != Decimal("736")
            or execution["max_open_positions"] != 1
            or execution["order_type"] != "LIMIT_ONLY"
            or set(tradable) != {
                "SOLUSDT", "LINKUSDT", "AVAXUSDT", "NEARUSDT", "SUIUSDT",
                "ARBUSDT", "APTUSDT", "INJUSDT", "TIAUSDT", "DOGEUSDT",
            }
            or "BTCUSDT" not in anchors
            or not any(x["symbol"] == "OPUSDT" and x["blocked_through_utc_date"] == "2026-11-03" for x in exclusions)
        ):
            fail("OWNER_VIRTUAL_CONTRACT_MISMATCH")
    if strategy_id == "H1_CARRY_001" and eligibility["status"] != "ECONOMIC_NOT_TESTED":
        fail("H1_NOT_ECONOMICALLY_TESTED")


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()


def verify_registry(root: Path) -> str:
    root = Path(root)
    folder = root / "strategies"
    receipt_file = root / "registry_witness.jsonl"
    try:
        receipts = [
            json.loads(line, object_pairs_hook=_no_dupe_pairs, parse_constant=_nonfinite)
            for line in receipt_file.read_text(encoding="utf-8").splitlines()
        ]
        head = sha_ledger.verify(receipts)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RegistryError("BROKEN_REGISTRY_WITNESS") from exc
    manifests = sorted(folder.glob("*.json"))
    if len(manifests) != len(receipts) or not manifests:
        fail("REGISTRY_FILE_COUNT_WITNESS_MISMATCH")
    names = set()
    pins = set()
    for row in receipts:
        payload = row.get("payload", {})
        if row.get("event_type") != "STRATEGY_REGISTERED" or not isinstance(payload, dict):
            fail("INVALID_REGISTRY_RECEIPT_TYPE")
        if set(payload) != {"strategy_id", "path", "git_blob_sha", "registered_on_utc"}:
            fail("INVALID_REGISTRY_RECEIPT_FIELDS")
        name = payload["strategy_id"]
        if name in names or payload["path"] in pins or not STRATEGY_RE.fullmatch(name):
            fail("DUPLICATE_STRATEGY_OR_PATH")
        names.add(name)
        pins.add(payload["path"])
        if payload["path"] != f"strategies/{name}.json":
            fail("REGISTRY_PATH_NOT_CANONICAL")
        path = root / payload["path"]
        raw = path.read_bytes()
        if git_blob_sha(raw) != payload["git_blob_sha"]:
            fail("REGISTERED_SOURCE_TAMPERED")
        record = parse_canonical(raw)
        validate_entry(record)
        if record["strategy_id"] != name or record["registered_on_utc"] != payload["registered_on_utc"]:
            fail("RECEIPT_RECORD_MISMATCH")
    if set(manifests) != {root / x for x in pins}:
        fail("UNWITNESSED_REGISTRY_FILE")
    for path in manifests:
        doc = parse_canonical(path.read_bytes())
        parent = doc["parent_strategy_id"]
        if parent is not None and parent not in names:
            fail("UNKNOWN_PARENT_STRATEGY")
    return head


def verify_history(root: Path) -> None:
    # New strategies must be ADDED, never edited/deleted/renamed in later commits.
    # This is an operational CI gate; not a GitHub branch-protection ruleset.
    root = Path(root)
    command = ["git", "log", "--format=", "--name-status", "--diff-filter=DMRT",
               "--", str(root / "strategies")]
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    if result.stdout.strip():
        fail("REGISTERED_FILE_WAS_EDITED_OR_REMOVED_IN_GIT_HISTORY")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="research/registry")
    parser.add_argument("--verify-history", action="store_true")
    args = parser.parse_args()
    root = Path(args.root)
    head = verify_registry(root)
    if args.verify_history:
        verify_history(root)
    print("STRATEGY_REGISTRY_OK", head)


if __name__ == "__main__":
    main()
