from __future__ import annotations

import argparse
import json
from pathlib import Path

from ember.config import EmberConfig
from ember.core.data_engine import DataEngine
from ember.research.report_engine import ReportEngine
from ember.simulation.backtester import Backtester


def profiles() -> dict[str, EmberConfig]:
    baseline = EmberConfig()
    return {
        "baseline": baseline,
        "both-directions": baseline.model_copy(
            update={"allowed_direction_contexts": ("bull", "bear")}
        ),
        "wide": baseline.model_copy(
            update={
                "allowed_direction_contexts": ("bull", "bear"),
                "min_confidence": 20.0,
                "min_volume_ratio": 0.5,
                "min_rr": 1.2,
                "atr_stop_multiplier": 1.0,
            }
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare baseline, both-direction and wide diagnostic profiles"
    )
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("results/diagnostics"))
    parser.add_argument("--equity", type=float, default=10_000.0)
    args = parser.parse_args()

    candles = DataEngine.load_csv(args.csv)
    summary: dict[str, object] = {}
    for name, config in profiles().items():
        print(f"\n=== PROFILE: {name} ===")
        backtester = Backtester(config)
        result = backtester.run(
            candles,
            initial_equity=args.equity,
            diagnostics=True,
        )
        profile_dir = args.out_dir / name
        ReportEngine().write_backtest(result, profile_dir)
        metrics = result.metrics
        summary[name] = {
            "config": {
                "allowed_direction_contexts": list(config.allowed_direction_contexts),
                "min_confidence": config.min_confidence,
                "min_volume_ratio": config.min_volume_ratio,
                "min_rr": config.min_rr,
                "atr_stop_multiplier": config.atr_stop_multiplier,
            },
            "metrics": {
                "total_return": metrics.total_return,
                "profit_factor": metrics.profit_factor,
                "max_drawdown": metrics.max_drawdown,
                "win_rate": metrics.win_rate,
                "num_trades": metrics.num_trades,
                "final_equity": metrics.final_equity,
            },
            "rejects": backtester.last_diagnostics,
        }
        print(f"Return: {metrics.total_return:.6f}%")
        print(f"PF: {metrics.profit_factor}")
        print(f"DD: {metrics.max_drawdown:.6f}%")
        print(f"Trades: {metrics.num_trades}")
        print(f"Win rate: {metrics.win_rate:.6f}%")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    path = args.out_dir / "summary.json"
    path.write_text(json.dumps(summary, indent=2, allow_nan=True), encoding="utf-8")
    print(f"\nSummary: {path.resolve()}")


if __name__ == "__main__":
    main()
