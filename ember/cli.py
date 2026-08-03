"""Console entry points."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import uvicorn

from ember.config import EmberConfig
from ember.research.report_engine import ReportEngine
from ember.research.synthetic import mixed_regime_synthetic_data
from ember.server.paper_server import create_app
from ember.simulation.backtester import Backtester
from ember.simulation.walk_forward import WalkForwardValidator


def run_demo() -> None:
    parser = argparse.ArgumentParser(description="Run the EMBER synthetic research demo")
    parser.add_argument("--demo", action="store_true", help="compatibility flag")
    parser.add_argument("--out-dir", type=Path, default=Path("results/demo"))
    parser.add_argument("--bars", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--wfo", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    config = EmberConfig(allowed_direction_contexts=("bull", "bear"))
    candles = mixed_regime_synthetic_data(bars=args.bars, seed=args.seed)
    backtester = Backtester(config)
    backtest = backtester.run(candles, diagnostics=True)
    reports = ReportEngine()
    reports.write_backtest(backtest, args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "reject_diagnostics.json").write_text(
        json.dumps(backtester.last_diagnostics, indent=2),
        encoding="utf-8",
    )

    print(f"Return: {backtest.metrics.total_return:.4f}%")
    print(f"PF: {backtest.metrics.profit_factor:.4f}")
    print(f"DD: {backtest.metrics.max_drawdown:.4f}%")
    print(f"Trades: {backtest.metrics.num_trades}")
    print(f"Win rate: {backtest.metrics.win_rate:.4f}%")

    if args.wfo:
        wfo = WalkForwardValidator(config).run(candles)
        reports.write_wfo(wfo, args.out_dir)
        print(f"WFO: {wfo.pass_fail}")
    else:
        print("WFO: SKIPPED")
    print(f"Reports: {args.out_dir.resolve()}")


def run_paper_server() -> None:
    parser = argparse.ArgumentParser(description="Run EMBER virtual-only paper server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8095)
    parser.add_argument("--db", type=Path, default=Path("paper_trades.db"))
    args = parser.parse_args()
    uvicorn.run(create_app(args.db), host=args.host, port=args.port)
