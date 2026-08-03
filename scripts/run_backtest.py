from __future__ import annotations

import argparse
import json
from pathlib import Path

from ember.core.data_engine import DataEngine
from ember.research.profiles import PROFILE_NAMES, config_for_profile
from ember.research.report_engine import ReportEngine
from ember.simulation.backtester import Backtester


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EMBER backtest on local OHLCV CSV")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("results/backtest"))
    parser.add_argument("--equity", type=float, default=10_000.0)
    parser.add_argument(
        "--profile",
        choices=PROFILE_NAMES,
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
    print(f"HTF bias mode: {config.htf_bias_mode}")
    print(f"HTF EMA period: {config.htf_ema_period}")
    print(f"HTF EMA threshold: {config.htf_ema_threshold_pct:.3f}%")
    print(f"Return: {metrics.total_return:.6f}%")
    print(f"PF: {metrics.profit_factor}")
    print(f"DD: {metrics.max_drawdown:.6f}%")
    print(f"Trades: {metrics.num_trades}")
    print(f"Win rate: {metrics.win_rate:.6f}%")
    print(f"Final equity: {metrics.final_equity:.6f}")


if __name__ == "__main__":
    main()
