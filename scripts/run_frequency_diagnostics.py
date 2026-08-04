"""Measure trade frequency and rejection reasons on one fixed synthetic sample."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from ember.research.profiles import config_for_profile
from ember.research.synthetic import mixed_regime_synthetic_data
from ember.simulation.backtester import Backtester

PROFILE_ORDER = (
    "legacy-baseline",
    "both-directions",
    "high-vol-block",
    "bidirectional-high-vol-block",
)


def _safe_metric(value: float) -> float | str:
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    if math.isnan(value):
        return "nan"
    return float(value)


def _format_metric(value: float | str, digits: int = 4) -> str:
    if isinstance(value, str):
        return value
    return f"{value:.{digits}f}"


def run_frequency_diagnostics(
    *,
    bars: int,
    seed: int,
    out_dir: Path,
) -> dict[str, Any]:
    if bars <= 60:
        raise ValueError("bars must be greater than 60")

    candles = mixed_regime_synthetic_data(bars=bars, seed=seed)
    sample_days = bars / 96.0
    results: dict[str, Any] = {}

    for profile in PROFILE_ORDER:
        config = config_for_profile(profile)
        backtester = Backtester(config)
        backtest = backtester.run(candles, diagnostics=True)
        metrics = backtest.metrics
        trades_per_day = metrics.num_trades / sample_days
        results[profile] = {
            "config": {
                "allowed_direction_contexts": list(config.allowed_direction_contexts),
                "blocked_volatility_regimes": list(config.blocked_volatility_regimes),
                "min_confidence": config.min_confidence,
                "min_volume_ratio": config.min_volume_ratio,
                "min_rr": config.min_rr,
                "max_positions": config.max_positions,
            },
            "metrics": {
                "trades": int(metrics.num_trades),
                "trades_per_day": trades_per_day,
                "estimated_trades_per_25_day_fold": trades_per_day * 25.0,
                "return_pct": float(metrics.total_return),
                "profit_factor": _safe_metric(float(metrics.profit_factor)),
                "max_drawdown_pct": float(metrics.max_drawdown),
                "win_rate_pct": float(metrics.win_rate),
            },
            "rejects": dict(backtester.last_diagnostics),
        }

    payload = {
        "protocol": {
            "dataset": "mixed_regime_synthetic_data",
            "bars": bars,
            "seed": seed,
            "sample_days_15m": sample_days,
            "profiles": list(PROFILE_ORDER),
            "attribution_policy": (
                "legacy -> direction-only -> volatility-only -> combined; "
                "one fixed sample, no parameter tuning"
            ),
        },
        "results": results,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    lines = [
        "# Synthetic Frequency Diagnostics",
        "",
        f"- Dataset: fixed mixed-regime synthetic sample, seed `{seed}`",
        f"- Bars: `{bars}` 15m bars (`{sample_days:.2f}` days)",
        "- No filter values are tuned in this diagnostic",
        "",
        "## Frequency and performance",
        "",
        "| Profile | Directions | High-vol blocked | Trades | Trades/day | Est. trades/25d fold | Return | PF | DD |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for profile in PROFILE_ORDER:
        row = results[profile]
        config = row["config"]
        metrics = row["metrics"]
        lines.append(
            "| {profile} | {directions} | {blocked} | {trades} | {density:.4f} | "
            "{fold_density:.2f} | {ret:+.4f}% | {pf} | {dd:.4f}% |".format(
                profile=profile,
                directions=", ".join(config["allowed_direction_contexts"]),
                blocked="yes" if config["blocked_volatility_regimes"] else "no",
                trades=metrics["trades"],
                density=metrics["trades_per_day"],
                fold_density=metrics["estimated_trades_per_25_day_fold"],
                ret=metrics["return_pct"],
                pf=_format_metric(metrics["profit_factor"]),
                dd=metrics["max_drawdown_pct"],
            )
        )

    reject_keys = sorted(
        {
            key
            for profile in PROFILE_ORDER
            for key in results[profile]["rejects"]
        }
    )
    lines.extend(
        [
            "",
            "## Reject reasons",
            "",
            "| Reject reason | " + " | ".join(PROFILE_ORDER) + " |",
            "|---|" + "---:|" * len(PROFILE_ORDER),
        ]
    )
    for key in reject_keys:
        values = [str(results[profile]["rejects"].get(key, 0)) for profile in PROFILE_ORDER]
        lines.append(f"| {key} | " + " | ".join(values) + " |")

    lines.extend(
        [
            "",
            "## Interpretation rule",
            "",
            "This is a frequency diagnostic, not OOS evidence. The two isolated controls",
            "attribute direction and volatility effects before the combined configuration is",
            "tested on real extended history. Synthetic profitability must not be used for",
            "paper or live promotion.",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare isolated direction/volatility frequency hypotheses"
    )
    parser.add_argument("--bars", type=int, default=15_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--out-dir", type=Path, default=Path("results/frequency_diagnostics")
    )
    args = parser.parse_args()

    payload = run_frequency_diagnostics(
        bars=args.bars,
        seed=args.seed,
        out_dir=args.out_dir,
    )
    for profile in PROFILE_ORDER:
        metrics = payload["results"][profile]["metrics"]
        print(
            f"{profile}: trades={metrics['trades']}, "
            f"trades/day={metrics['trades_per_day']:.4f}, "
            f"estimated/25d={metrics['estimated_trades_per_25_day_fold']:.2f}"
        )
    print(f"Report: {(args.out_dir / 'summary.md').resolve()}")


if __name__ == "__main__":
    main()
