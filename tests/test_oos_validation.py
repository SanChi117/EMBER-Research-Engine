from __future__ import annotations

from ember.research.profiles import config_for_profile
from scripts.run_oos_validation import verdict


def _row(return_pct: float, profit_factor: float) -> dict[str, float]:
    return {"return_pct": return_pct, "profit_factor": profit_factor}


def test_oos_verdict_thresholds_are_predeclared() -> None:
    passed = [_row(1.0, 2.0), _row(2.0, 1.6), _row(0.5, 1.7), _row(-1.0, 0.8)]
    partial = [_row(1.0, 2.0), _row(2.0, 1.6), _row(0.5, 1.2), _row(-1.0, 3.0)]
    failed = [_row(1.0, 2.0), _row(2.0, 1.2), _row(-0.5, 2.0), _row(-1.0, 0.8)]

    assert verdict(passed) == ("PASS", 3)
    assert verdict(partial) == ("PARTIAL", 2)
    assert verdict(failed) == ("FAIL", 1)


def test_oos_profile_matches_frozen_protocol() -> None:
    config = config_for_profile("high-vol-block")

    assert config.blocked_volatility_regimes == ("high_vol",)
    assert config.min_confidence == 43.0
    assert config.min_rr == 1.8
    assert config.wfo_folds == 4
    assert config.wfo_lookback_days == 30
    assert config.wfo_embargo_bars == 3
