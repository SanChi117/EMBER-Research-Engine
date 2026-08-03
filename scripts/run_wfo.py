from __future__ import annotations

import argparse
from pathlib import Path

from ember.config import EmberConfig
from ember.core.data_engine import DataEngine
from ember.research.report_engine import ReportEngine
from ember.simulation.walk_forward import WalkForwardValidator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run purged EMBER walk-forward validation")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("results/wfo"))
    parser.add_argument("--equity", type=float, default=10_000.0)
    parser.add_argument("--test-days", type=int, default=None)
    args = parser.parse_args()
    candles = DataEngine.load_csv(args.csv)
    summary = WalkForwardValidator(EmberConfig()).run(
        candles,
        initial_equity=args.equity,
        test_days=args.test_days,
    )
    ReportEngine().write_wfo(summary, args.out_dir)
    print(summary)


if __name__ == "__main__":
    main()
