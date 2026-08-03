from __future__ import annotations

import argparse
import json
from pathlib import Path

from ember.core.data_engine import DataEngine
from ember.research.profiles import diagnostic_profiles
from ember.research.report_engine import ReportEngine
from ember.simulation.backtester import Backtester


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare baseline, EMA and structure HTF bias profiles"
    )
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("results/diagnostics"))
    parser.add_argument("--equity", type=float, default=10_000.0)
    args = parser.parse_args()

    candles = DataEngine.load_csv(args.csv)
    summary: dict[str, object] = {}
    for name, config in diagnostic_profiles().items():
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
                "htf_bias_mode": config.htf_bias_mode,
                "htf_ema_period": config.htf_ema_period,
                "htf_ema_threshold_pct": config.htf_ema_threshold_pct,
                "blocked_volatility_regimes": list(config.blocked_volatility_regimes),
                "tp_mode": config.tp_mode,
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
        print(f"Bias mode: {config.htf_bias_mode}")
        print(f"EMA: {config.htf_ema_period}, threshold={config.htf_ema_threshold_pct:.3f}%")
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
