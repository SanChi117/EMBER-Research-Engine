"""Named research configurations used for controlled diagnostic comparisons."""

from ember.config import EmberConfig

PROFILE_NAMES = (
    "baseline",
    "legacy-baseline",
    "both-directions",
    "high-vol-block",
    "bidirectional-high-vol-block",
    "ema-tight",
    "ema50",
    "structure-bias",
    "opposite-liquidity",
    "wide",
)


def diagnostic_profiles() -> dict[str, EmberConfig]:
    """Return profiles with explicit historical controls and isolated hypotheses.

    ``baseline`` and ``bidirectional-high-vol-block`` use the current default
    configuration. ``legacy-baseline``, ``both-directions`` and
    ``high-vol-block`` preserve the exact assumptions used by earlier reports so
    those results remain reproducible after the default configuration changes.
    """

    baseline = EmberConfig()
    legacy_baseline = baseline.model_copy(
        update={
            "allowed_direction_contexts": ("down",),
            "blocked_volatility_regimes": (),
        }
    )
    both_directions = legacy_baseline.model_copy(
        update={"allowed_direction_contexts": ("bull", "bear")}
    )
    historical_high_vol_block = legacy_baseline.model_copy(
        update={"blocked_volatility_regimes": ("high_vol",)}
    )
    return {
        "baseline": baseline,
        "legacy-baseline": legacy_baseline,
        "both-directions": both_directions,
        "high-vol-block": historical_high_vol_block,
        "bidirectional-high-vol-block": baseline,
        "ema-tight": baseline.model_copy(update={"htf_ema_threshold_pct": 0.5}),
        "ema50": baseline.model_copy(update={"htf_ema_period": 50}),
        "structure-bias": baseline.model_copy(update={"htf_bias_mode": "structure"}),
        "opposite-liquidity": baseline.model_copy(
            update={"tp_mode": "opposite_htf_liquidity"}
        ),
        "wide": baseline.model_copy(
            update={
                "min_confidence": 20.0,
                "min_volume_ratio": 0.5,
                "min_rr": 1.2,
                "atr_stop_multiplier": 1.0,
            }
        ),
    }


def config_for_profile(profile: str) -> EmberConfig:
    try:
        return diagnostic_profiles()[profile]
    except KeyError as error:
        raise ValueError(f"unknown profile: {profile}") from error
