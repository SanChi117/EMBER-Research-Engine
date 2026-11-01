"""RESET-06 owner acceptance: 2% ladder, ratchet, manual regime, SHA journal gates."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

import pytest

from research.platform import gate_report as g
from research.platform import ramp_policy as r
from research.platform import strategy_registry as registry
from research.platform.paper_ledger import JsonlPaperLedgerStore

ROOT = Path(__file__).resolve().parents[1] / "research/registry"


def manifest():
    return registry.parse_canonical((ROOT / "strategies/VIRTUAL_MECH_920.json").read_bytes())


def fake_rows(count, *, days=30, pnl_cycle=("2", "-1")):
    out = []
    equity = D("920")
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(count):
        day = (i % days) if days else 0
        # Explicitly repeat active dates without inventing current active days.
        moment = start + timedelta(days=day, seconds=i)
        pnl = D(pnl_cycle[i % len(pnl_cycle)])
        equity += pnl
        out.append({
            "event_id": f"closed:{i}",
            "event_type": "TRADE_CLOSED",
            "payload": {
                "strategy_id": "VIRTUAL_MECH_920",
                "trade_id": f"trade:{i}",
                "observed_at_ms": int(moment.timestamp() * 1000),
                "net_pnl_usdt": str(pnl),
                "equity_after_usdt": str(equity),
            },
        })
    out.sort(key=lambda x: x["payload"]["observed_at_ms"])
    # Recompute a sequential, auditable synthetic equity path after sorting.
    equity = D("920")
    for row in out:
        equity += D(row["payload"]["net_pnl_usdt"])
        row["payload"]["equity_after_usdt"] = format(equity, "f")
    return tuple(out)


def test_registry_v11_three_exact_limits_and_remaining_blocks():
    doc = manifest()
    registry.validate_entry(doc)
    assert doc["version"] == "1.1"
    assert doc["risk"]["max_leverage"] == "3"
    assert doc["risk"]["max_notional_usdt"] == "2760"
    assert doc["gates"]["paper_max_drawdown_fraction"] == "0.20"
    assert doc["risk"]["regime_state"] == "NEUTRAL"
    assert doc["risk"]["ladder_fractions"] == ["0.02", "0.03", "0.04"]
    assert doc["eligibility"]["block_reasons"] == [
        "OWNER_ENTRY_EXIT_RULES_NOT_PINNED",
        "RISK_DENIALS_NOT_YET_PERSISTED_TO_EXECUTABILITY",
    ]


def test_legacy_receipts_are_kept_and_revision_witnessed():
    lines = (ROOT / "registry_witness.jsonl").read_text().splitlines()
    assert len(lines) == 4
    assert registry.verify_registry(ROOT) == (
        "7b37c738dbd24ab2d8e667591fdf19488017f1217c6c35c350699184d282f471"
    )


def test_base_fraction_starts_at_two_percent():
    assert r.propose_paper_budget(
        equity_current=D("920"), peak_equity=D("920")
    ).risk_budget_usdt == D("18.4")
    assert r.propose_paper_budget(
        equity_current=D("920"), peak_equity=D("920")
    ).active_ladder_fraction == D("0.02")


def test_ratchet_boundaries_at_1104_and_1200():
    for equity, expected in [
        (D("1103.99"), D("18.4")),
        (D("1104"), D("18.4")),
        (D("1104.01"), D("18.4008")),
        (D("1200"), D("26.08")),
    ]:
        verdict = r.propose_paper_budget(
            equity_current=equity, peak_equity=equity
        )
        assert verdict.paper_budget_only is True
        assert verdict.risk_budget_usdt == expected
        assert verdict.live_allowed is False


def test_ratchet_never_overrides_absolute_notional_cap():
    verdict = r.propose_paper_budget(
        equity_current=D("2000"), peak_equity=D("2000"),
        notional_requested=D("2760.01"),
    )
    assert not verdict.paper_budget_only
    assert verdict.reason == "NOTIONAL_CAP_EXCEEDED"
    assert verdict.live_allowed is False
    assert r.propose_paper_budget(
        equity_current=D("2000"), peak_equity=D("2000"),
        notional_requested=D("2760"),
    ).notional_cap_usdt == D("2760")


def test_leverage_and_available_equity_cap_position():
    assert r.propose_paper_budget(
        equity_current=D("920"), peak_equity=D("920"),
        leverage_requested=D("3.01"),
    ).reason == "LEVERAGE_CAP_EXCEEDED"
    assert r.propose_paper_budget(
        equity_current=D("850"), peak_equity=D("920"),
        notional_requested=D("2700"),
    ).reason == "NOTIONAL_CAP_EXCEEDED"


def test_kill_and_drawdown_ignore_ratchet():
    assert r.propose_paper_budget(
        equity_current=D("736"), peak_equity=D("920")
    ).reason == "KILL_EQUITY_REACHED"
    assert r.propose_paper_budget(
        equity_current=D("1000"), peak_equity=D("1400")
    ).reason == "MAX_DRAWDOWN_REACHED"


def test_regime_chop_neutral_daily_and_window_fail_closed():
    assert r.propose_paper_budget(
        equity_current=D("920"), peak_equity=D("920"), regime_state="CHOP"
    ).reason == "CHOP_NO_EXECUTION"
    assert r.propose_paper_budget(
        equity_current=D("920"), peak_equity=D("920"), trades_today=1
    ).reason == "REGIME_DAILY_TRADE_LIMIT"
    assert r.propose_paper_budget(
        equity_current=D("920"), peak_equity=D("920"), regime_state="WINDOW_OPEN"
    ).reason == "WINDOW_OPEN_NEEDS_VERIFIED_WEEKLY_REVIEW"
    approved = r.propose_paper_budget(
        equity_current=D("920"), peak_equity=D("920"), regime_state="WINDOW_OPEN",
        owner_regime_review_verified=True, trades_today=2,
    )
    assert approved.trades_per_utc_day == 3
    assert approved.paper_budget_only
    assert not approved.live_allowed


def test_no_ladder_three_or_four_without_gate():
    for stage in (3, 4):
        denied = r.propose_paper_budget(
            equity_current=D("1000"), peak_equity=D("1000"),
            requested_ladder_step=stage,
        )
        assert denied.reason == "LADDER_NOT_UNLOCKED"
        assert not denied.live_allowed
    allowed_budget_only = r.propose_paper_budget(
        equity_current=D("1000"), peak_equity=D("1000"),
        requested_ladder_step=3, ladder_gate_verified=True,
    )
    assert allowed_budget_only.active_ladder_fraction == D("0.03")
    assert allowed_budget_only.live_allowed is False


def test_series_budget_cap_and_float_fail_closed():
    result = r.propose_paper_budget(
        equity_current=D("1200"), peak_equity=D("1200"),
        remaining_series_budget_usdt=D("7"),
    )
    assert result.risk_budget_usdt == D("7")
    assert r.propose_paper_budget(
        equity_current=1200.0, peak_equity=D("1200")
    ).reason == "INVALID_RAMP_INPUT"


def test_zero_ledger_is_in_progress_no_unlock(tmp_path):
    report = g.report_from_store(journal_root=tmp_path, registry_root=ROOT)
    assert report["values"]["trades_closed"] == 0
    assert report["gates"]["trades_closed"] == "IN_PROGRESS"
    assert report["gates"]["days_active"] == "IN_PROGRESS"
    assert report["gates"]["profit_factor"] == "IN_PROGRESS"
    assert report["gates"]["max_drawdown"] == "IN_PROGRESS"
    assert report["LADDER_STEP_UNLOCK"] is False
    assert report["live_allowed"] is False
    assert g.render_report(report) == g.render_report(report)


def test_ninety_nine_trades_never_pass_count():
    report = g.evaluate_gates(manifest(), fake_rows(99))
    assert report["gates"]["trades_closed"] == "IN_PROGRESS"
    assert report["LADDER_STEP_UNLOCK"] is False


def test_day_29_is_in_progress_and_30_pass():
    day29 = g.evaluate_gates(manifest(), fake_rows(100, days=29))
    assert day29["gates"]["days_active"] == "IN_PROGRESS"
    day30 = g.evaluate_gates(manifest(), fake_rows(100, days=30))
    assert day30["gates"]["days_active"] == "PASS"
    assert day30["gates"]["trades_closed"] == "PASS"
    assert day30["LADDER_STEP_UNLOCK"] is False  # owner block not released


def test_profit_factor_below_or_equal_1_2_is_fail():
    for gain in ("1.1999", "1.2"):
        rows = fake_rows(2, days=2, pnl_cycle=(gain, "-1"))
        report = g.evaluate_gates(manifest(), rows)
        assert report["gates"]["profit_factor"] == "FAIL"
        assert report["LADDER_STEP_UNLOCK"] is False


def test_gate_report_is_deterministic_for_same_rows():
    rows = fake_rows(100)
    first = g.render_report(g.evaluate_gates(manifest(), rows))
    second = g.render_report(g.evaluate_gates(manifest(), rows))
    assert first == second
    assert '"LADDER_STEP_UNLOCK":false' in first


def test_trade_row_without_price_evidence_fails_closed():
    rows = list(fake_rows(2))
    bad = copy.deepcopy(rows[1])
    del bad["payload"]["net_pnl_usdt"]
    rows[1] = bad
    with pytest.raises(g.GateError):
        g.evaluate_gates(manifest(), tuple(rows))


def test_mixed_strategy_cannot_falsely_pass_strategy_specific_dd():
    rows = list(fake_rows(2))
    mixed = copy.deepcopy(rows[1])
    mixed["payload"]["strategy_id"] = "H1_CARRY_001"
    rows[1] = mixed
    with pytest.raises(g.GateError, match="MIXED_STRATEGY"):
        g.evaluate_gates(manifest(), tuple(rows))


def test_real_ledger_source_and_external_pin(tmp_path):
    db = JsonlPaperLedgerStore(tmp_path)
    ts = 1762000000000
    closed = db.append("trades", event_id="closed:1", event_type="TRADE_CLOSED",
        payload={"observed_at_ms": ts, "strategy_id": "VIRTUAL_MECH_920",
                 "trade_id": "1", "net_pnl_usdt": "1", "equity_after_usdt": "921"})
    result = g.report_from_store(
        journal_root=tmp_path, registry_root=ROOT,
        expected_trades_head=closed["record_sha256"],
    )
    assert result["values"]["trades_closed"] == 1
    with pytest.raises(ValueError, match="EXTERNAL_HEAD_WITNESS_MISMATCH"):
        g.report_from_store(
            journal_root=tmp_path, registry_root=ROOT,
            expected_trades_head="0" * 64,
        )
