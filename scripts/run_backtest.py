from __future__ import annotations

import argparse
from pathlib import Path

from ember.config import EmberConfig
from ember.core.data_engine import DataEngine
from ember.research.report_engine import ReportEngine
from ember.simulation.backtester import Backtester


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EMBER backtest on local OHLCV CSV")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("results/backtest"))
    parser.add_argument("--equity", type=float, default=10_000.0)
    args = parser.parse_args()
    candles = DataEngine.load_csv(args.csv)
    result = Backtester(EmberConfig()).run(candles, initial_equity=args.equity)
    ReportEngine().write_backtest(result, args.out_dir)
    print(result.metrics)


if __name__ == "__main__":
    main()
