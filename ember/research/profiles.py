"""Named research configurations used for controlled diagnostic comparisons."""

from ember.config import EmberConfig

PROFILE_NAMES = (
    "baseline",
    "both-directions",
    "ema-tight",
    "ema50",
    "structure-bias",
    "high-vol-block",
    "opposite-liquidity",
    "wide",
)


def diagnostic_profiles() -> dict[str, EmberConfig]:
    """Return profiles where each experiment changes one declared assumption."""

    baseline = EmberConfig()
    both_directions = baseline.model_copy(
        update={"allowed_direction_contexts": ("bull", "bear")}
    )
    return {
        "baseline": baseline,
        "both-directions": both_directions,
        "ema-tight": both_directions.model_copy(
            update={"htf_ema_threshold_pct": 0.5}
        ),
        "ema50": both_directions.model_copy(
            update={"htf_ema_period": 50}
        ),
        "structure-bias": both_directions.model_copy(
            update={"htf_bias_mode": "structure"}
        ),
        "high-vol-block": baseline.model_copy(
            update={"blocked_volatility_regimes": ("high_vol",)}
        ),
        "opposite-liquidity": baseline.model_copy(
            update={"tp_mode": "opposite_htf_liquidity"}
        ),
        "wide": both_directions.model_copy(
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
