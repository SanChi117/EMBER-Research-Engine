from __future__ import annotations

import argparse
import json
from pathlib import Path

from ember.config import EmberConfig
from ember.core.data_engine import DataEngine
from ember.research.report_engine import ReportEngine
from ember.simulation.backtester import Backtester


def config_for_profile(profile: str) -> EmberConfig:
    config = EmberConfig()
    if profile == "baseline":
        return config
    if profile == "both-directions":
        return config.model_copy(
            update={"allowed_direction_contexts": ("bull", "bear")}
        )
    if profile == "wide":
        return config.model_copy(
            update={
                "allowed_direction_contexts": ("bull", "bear"),
                "min_confidence": 20.0,
                "min_volume_ratio": 0.5,
                "min_rr": 1.2,
                "atr_stop_multiplier": 1.0,
            }
        )
    raise ValueError(f"unknown profile: {profile}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EMBER backtest on local OHLCV CSV")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("results/backtest"))
    parser.add_argument("--equity", type=float, default=10_000.0)
    parser.add_argument(
        "--profile",
        choices=("baseline", "both-directions", "wide"),
        default="baseline",
    )
    parser.add_argument("--diagnostics", action="store_true")
    args = parser.parse_args()

    candles = DataEngine.load_csv(args.csv)
    config = config_for_profile(args.profile)
    backtester = Backtester(config)
    result = backtester.run(
        candles,
        initial_equity=args.equity,
        diagnostics=args.diagnostics,
    )
    ReportEngine().write_backtest(result, args.out_dir)
    if args.diagnostics:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "reject_diagnostics.json").write_text(
            json.dumps(backtester.last_diagnostics, indent=2),
            encoding="utf-8",
        )

    metrics = result.metrics
    print(f"Profile: {args.profile}")
    print(f"Return: {metrics.total_return:.6f}%")
    print(f"PF: {metrics.profit_factor}")
    print(f"DD: {metrics.max_drawdown:.6f}%")
    print(f"Trades: {metrics.num_trades}")
    print(f"Win rate: {metrics.win_rate:.6f}%")
    print(f"Final equity: {metrics.final_equity:.6f}")


if __name__ == "__main__":
    main()
