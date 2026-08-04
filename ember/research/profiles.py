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
    """Return historical controls and isolated research hypotheses.

    The default ``baseline`` remains the configuration used by the original
    validation reports. The proposed bidirectional/high-vol-block combination is
    retained as an explicit profile because its controlled synthetic and
    30000-bar portfolio validations failed; it must not silently replace the
    baseline.
    """

    baseline = EmberConfig()
    both_directions = baseline.model_copy(
        update={"allowed_direction_contexts": ("bull", "bear")}
    )
    high_vol_block = baseline.model_copy(
        update={"blocked_volatility_regimes": ("high_vol",)}
    )
    bidirectional_high_vol_block = baseline.model_copy(
        update={
            "allowed_direction_contexts": ("bull", "bear"),
            "blocked_volatility_regimes": ("high_vol",),
        }
    )
    return {
        "baseline": baseline,
        "legacy-baseline": baseline,
        "both-directions": both_directions,
        "high-vol-block": high_vol_block,
        "bidirectional-high-vol-block": bidirectional_high_vol_block,
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
