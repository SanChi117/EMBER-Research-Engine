from __future__ import annotations

from ember.config import EmberConfig
from ember.research.synthetic import trending_synthetic_data
from ember.simulation.walk_forward import WalkForwardValidator


def test_walk_forward_bounds_use_unique_projection_names() -> None:
    candles = trending_synthetic_data(bars=120)
    summary = WalkForwardValidator(
        EmberConfig(
            allowed_direction_contexts=("bear",),
            wfo_lookback_days=1,
            wfo_folds=1,
        )
    ).run(candles, test_days=1)
    assert summary.pass_fail in {"PASS", "FAIL"}
