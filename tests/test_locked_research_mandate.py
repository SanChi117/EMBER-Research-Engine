"""Stop accidental scope drift away from the user-locked Binance USDT-M Futures mandate.

This is a guard against accidental edits, NOT a substitute for protected branches
or an administrator-configured GitHub ruleset.
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_futures_mandate_is_locked():
    contract = json.loads((ROOT / "config/research_mandate.lock.json").read_text("utf-8"))
    assert contract["schema"] == "EMBER_RESEARCH_MANDATE_LOCK_V1"
    assert contract["state"] == "LOCKED_USER_ONLY"
    assert contract["scope"] == "BINANCE_USDT_M_FUTURES"
    assert contract["spot_only_candidate_allowed"] is False
    assert contract["original_open_source_candidate_first"] is True
    assert contract["real_futures_ohlcv_mark_funding_required"] is True
    assert contract["after_cost_positive_edge_required"] is True
    assert contract["portfolio_drawdown_and_robustness_required"] is True
    assert contract["prospective_validation_required_for_verified"] is True
    assert contract["minimum_verified_count_before_review"] >= 1
    assert contract["preferred_independent_family_candidate_count"] >= 2
    assert contract["automatic_unlock_on_candidate"] is False
    assert contract["explicit_new_user_command_for_scope_change"] is True
    assert contract["automated_real_exchange_orders_allowed"] is False
    assert contract["modify_existing_paper_automations_allowed"] is False
    assert {"A214", "A215", "A216"} <= set(contract["deprecated_cycles"])


def test_canonical_document_mentions_hard_requirements():
    content = (ROOT / "RESEARCH_MANDATE_LOCKED.md").read_text("utf-8")
    for required in (
        "НЕИЗМЕННАЯ ЦЕЛЬ",
        "Binance USDT-M Futures",
        "неизменённого оригинала",
        "положительное математическое ожидание",
        "2–3",
        "только по прямой новой команде пользователя",
    ):
        assert required in content, required
