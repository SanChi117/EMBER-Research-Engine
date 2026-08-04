from __future__ import annotations

from pathlib import Path

from scripts.run_frequency_diagnostics import PROFILE_ORDER, run_frequency_diagnostics


def test_frequency_profile_order_is_isolated() -> None:
    assert PROFILE_ORDER == (
        "legacy-baseline",
        "both-directions",
        "high-vol-block",
        "bidirectional-high-vol-block",
    )


def test_frequency_diagnostics_writes_reject_summary(tmp_path: Path) -> None:
    payload = run_frequency_diagnostics(bars=500, seed=7, out_dir=tmp_path)
    assert set(payload["results"]) == set(PROFILE_ORDER)
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "summary.md").exists()

    legacy = payload["results"]["legacy-baseline"]["config"]
    direction_only = payload["results"]["both-directions"]["config"]
    volatility_only = payload["results"]["high-vol-block"]["config"]
    combined = payload["results"]["bidirectional-high-vol-block"]["config"]

    assert legacy["allowed_direction_contexts"] == ["down"]
    assert legacy["blocked_volatility_regimes"] == []
    assert direction_only["allowed_direction_contexts"] == ["bull", "bear"]
    assert direction_only["blocked_volatility_regimes"] == []
    assert volatility_only["allowed_direction_contexts"] == ["down"]
    assert volatility_only["blocked_volatility_regimes"] == ["high_vol"]
    assert combined["allowed_direction_contexts"] == ["bull", "bear"]
    assert combined["blocked_volatility_regimes"] == ["high_vol"]

    for profile in PROFILE_ORDER:
        result = payload["results"][profile]
        assert "rejects" in result
        assert result["metrics"]["trades"] >= 0
