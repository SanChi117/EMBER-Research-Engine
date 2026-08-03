"""Console entry points."""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from ember.config import EmberConfig
from ember.research.report_engine import ReportEngine
from ember.research.synthetic import trending_synthetic_data
from ember.server.paper_server import create_app
from ember.simulation.backtester import Backtester
from ember.simulation.walk_forward import WalkForwardValidator


def run_demo() -> None:
    parser = argparse.ArgumentParser(description="Run the EMBER synthetic research demo")
    parser.add_argument("--out-dir", type=Path, default=Path("results/demo"))
    parser.add_argument("--bars", type=int, default=1000)
    args = parser.parse_args()

    config = EmberConfig(allowed_direction_contexts=("bear",))
    candles = trending_synthetic_data(bars=args.bars)
    backtest = Backtester(config).run(candles)
    wfo = WalkForwardValidator(config).run(candles)
    reports = ReportEngine()
    reports.write_backtest(backtest, args.out_dir)
    reports.write_wfo(wfo, args.out_dir)
    print(f"Backtest trades: {backtest.metrics.num_trades}")
    print(f"Backtest PF: {backtest.metrics.profit_factor:.4f}")
    print(f"WFO: {wfo.pass_fail}")
    print(f"Reports: {args.out_dir.resolve()}")


def run_paper_server() -> None:
    parser = argparse.ArgumentParser(description="Run EMBER virtual-only paper server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8095)
    parser.add_argument("--db", type=Path, default=Path("paper_trades.db"))
    args = parser.parse_args()
    uvicorn.run(create_app(args.db), host=args.host, port=args.port)
