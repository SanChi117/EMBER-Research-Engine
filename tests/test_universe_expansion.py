from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_universe_expansion import (
    blocked_payload,
    expansion_verdict,
    load_universe,
    render_report,
    require_portfolio_pass,
    tier_for,
)


def test_tier_rules_are_strict() -> None:
    assert tier_for(10, 1.0, 1.5001) == "Tier 1"
    assert tier_for(9, 1.0, 2.0) == "Tier 2"
    assert tier_for(5, 1.0, 1.0001) == "Tier 2"
    assert tier_for(5, 0.0, 2.0) == "Tier 3"
    assert tier_for(10, 1.0, 1.5) == "Tier 2"
    assert tier_for(4, 1.0, 2.0) == "Tier 3"


def test_expansion_verdict_uses_tier_one_count() -> None:
    assert expansion_verdict([{"tier": "Tier 1"}] * 10 + [{"tier": "Tier 3"}] * 10) == "PASS"
    assert expansion_verdict([{"tier": "Tier 1"}] * 5 + [{"tier": "Tier 2"}] * 15) == "PARTIAL"
    assert expansion_verdict([{"tier": "Tier 1"}] * 4 + [{"tier": "Tier 3"}] * 16) == "FAIL"


def test_portfolio_gate_blocks_failed_wfo(tmp_path: Path) -> None:
    path = tmp_path / "portfolio.json"
    path.write_text(json.dumps({"result": {"status": "FAIL"}}), encoding="utf-8")
    with pytest.raises(PermissionError, match="blocked"):
        require_portfolio_pass(path)


def test_portfolio_gate_accepts_pass(tmp_path: Path) -> None:
    path = tmp_path / "portfolio.json"
    path.write_text(json.dumps({"result": {"status": "PASS"}}), encoding="utf-8")
    assert require_portfolio_pass(path)["status"] == "PASS"


def test_universe_requires_exactly_twenty_unique_usdt_symbols(tmp_path: Path) -> None:
    path = tmp_path / "universe.json"
    symbols = [f"COIN{index}USDT" for index in range(20)]
    path.write_text(json.dumps({"symbols": symbols}), encoding="utf-8")
    assert load_universe(path) == tuple(symbols)

    path.write_text(json.dumps({"symbols": symbols[:-1]}), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly 20"):
        load_universe(path)


def test_blocked_report_has_tier_table_without_fake_results() -> None:
    payload = blocked_payload(Path("data/universe_20.json"), "15m", 15000, "FAIL")
    report = render_report(payload)
    assert payload["status"] == "BLOCKED"
    assert payload["results"] == []
    assert "| — | — | — | — | — | — | — | BLOCKED |" in report
    assert "no tier result is fabricated" in report
