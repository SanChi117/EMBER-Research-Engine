"""Run portfolio-level WFO for the frozen four-symbol OOS universe.

This entry point implements the Portfolio WFO protocol from the project
specification.  All symbols are concatenated into one multi-symbol Polars
DataFrame and passed to one WalkForwardValidator, so every fold uses one
shared PortfolioSimulator and one equity curve.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Sequence

import polars as pl

from ember.core.data_engine import DataEngine
from ember.research.profiles import config_for_profile
from ember.simulation.walk_forward import WalkForwardValidator

DEFAULT_SYMBOLS = ("PEPEUSDT", "FETUSDT", "WIFUSDT", "SUIUSDT")
DEFAULT_PROFILE = "high-vol-block"
MIN_TOTAL_TRADES = 20
MIN_STABILITY = 70.0
MIN_AVG_PF = 1.5
MAX_WORST_DD = 10.0
MIN_AVG_RETURN = 0.0


def _parse_symbols(value: str) -> tuple[str, ...]:
    symbols = tuple(item.strip().upper() for item in value.split(",") if item.strip())
    if not symbols:
        raise argparse.ArgumentTypeError("at least one symbol is required")
    if len(set(symbols)) != len(symbols):
        raise argparse.ArgumentTypeError("symbols must be unique")
    return symbols


def _metric_value(value: float) -> float | str:
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    if math.isnan(value):
        return "nan"
    return value


def _display_metric(value: float | str, digits: int = 4) -> str:
    if isinstance(value, str):
        return value
    return f"{value:.{digits}f}"


def load_portfolio_data(
    data_dir: Path,
    symbols: tuple[str, ...],
    interval: str,
    bars: int,
) -> pl.DataFrame:
    """Load the exact fixed universe and return one sorted multi-symbol frame."""

    frames: list[pl.DataFrame] = []
    missing: list[Path] = []
    for symbol in symbols:
        path = data_dir / f"{symbol}_{interval}_{bars}.csv"
        if not path.exists():
            missing.append(path)
            continue
        frame = DataEngine.load_csv(path).collect()
        if frame.height != bars:
            raise RuntimeError(
                f"{symbol}: expected exactly {bars} rows, received {frame.height}"
            )
        observed_symbols = set(frame.get_column("symbol").unique().to_list())
        if observed_symbols != {symbol}:
            raise RuntimeError(
                f"{symbol}: CSV symbol column contains {sorted(observed_symbols)}"
            )
        frames.append(frame)

    if missing:
        joined = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"missing portfolio CSV files: {joined}")
    if len(frames) != len(symbols):
        raise RuntimeError("not all requested symbols were loaded")

    portfolio = pl.concat(frames, how="vertical").sort(["time", "symbol"])
    if portfolio.height != bars * len(symbols):
        raise RuntimeError(
            "portfolio row count mismatch: "
            f"expected {bars * len(symbols)}, received {portfolio.height}"
        )
    return portfolio


def protocol_passes(summary: Any, total_trades: int) -> bool:
    """Apply the complete Portfolio WFO PASS gate from the specification."""

    return bool(
        float(summary.stability_score) >= MIN_STABILITY
        and float(summary.avg_pf) >= MIN_AVG_PF
        and float(summary.worst_dd) < MAX_WORST_DD
        and float(summary.avg_return) > MIN_AVG_RETURN
        and total_trades >= MIN_TOTAL_TRADES
    )


def serialize_summary(summary: Any, symbols: tuple[str, ...]) -> dict[str, Any]:
    total_trades = sum(int(fold.num_trades) for fold in summary.folds)
    status = "PASS" if protocol_passes(summary, total_trades) else "FAIL"
    return {
        "status": status,
        "engine_status": str(summary.pass_fail),
        "portfolio_mode": True,
        "universe_policy": "fixed_all_requested_symbols",
        "symbols": list(symbols),
        "folds": len(summary.folds),
        "zero_trade_folds": sum(int(fold.num_trades) == 0 for fold in summary.folds),
        "total_trades": total_trades,
        "avg_return": _metric_value(float(summary.avg_return)),
        "avg_pf": _metric_value(float(summary.avg_pf)),
        "worst_dd": float(summary.worst_dd),
        "stability_score": float(summary.stability_score),
        "pass_gate": {
            "stability_score_gte": MIN_STABILITY,
            "avg_pf_gte": MIN_AVG_PF,
            "worst_dd_lt": MAX_WORST_DD,
            "avg_return_gt": MIN_AVG_RETURN,
            "total_trades_gte": MIN_TOTAL_TRADES,
        },
        "fold_details": [
            {
                "fold": int(fold.fold),
                "train_start": fold.train_start.isoformat(),
                "train_end": fold.train_end.isoformat(),
                "test_start": fold.test_start.isoformat(),
                "test_end": fold.test_end.isoformat(),
                "return_pct": float(fold.return_pct),
                "profit_factor": _metric_value(float(fold.profit_factor)),
                "max_drawdown": float(fold.max_drawdown),
                "num_trades": int(fold.num_trades),
                "positive": bool(fold.positive),
            }
            for fold in summary.folds
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    result = payload["result"]
    symbols = ", ".join(payload["symbols"])
    lines = [
        "# Portfolio WFO — OOS 4 Alts",
        "",
        "## Setup",
        "",
        f"- Symbols: {symbols}",
        f"- Interval: {payload['interval']}",
        f"- Bars per symbol: {payload['bars_per_symbol']}",
        f"- Profile: {payload['profile']}",
        "- WFO: 4 folds, 30-day lookback, 3-bar embargo",
        "- Portfolio mode: one shared PortfolioSimulator and equity curve per fold",
        "- Universe policy: fixed before validation; no symbol removal",
        "",
        "## Results",
        "",
        "| Fold | Train Start | Train End | Test Start | Test End | Return | PF | DD | Trades |",
        "|---:|---|---|---|---|---:|---:|---:|---:|",
    ]
    for fold in result["fold_details"]:
        lines.append(
            "| {fold} | {train_start} | {train_end} | {test_start} | {test_end} | "
            "{ret:+.4f}% | {pf} | {dd:.4f}% | {trades} |".format(
                fold=fold["fold"],
                train_start=fold["train_start"],
                train_end=fold["train_end"],
                test_start=fold["test_start"],
                test_end=fold["test_end"],
                ret=fold["return_pct"],
                pf=_display_metric(fold["profit_factor"]),
                dd=fold["max_drawdown"],
                trades=fold["num_trades"],
            )
        )

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Avg Return: {_display_metric(result['avg_return'])}%",
            f"- Avg PF: {_display_metric(result['avg_pf'])}",
            f"- Worst DD: {result['worst_dd']:.4f}%",
            f"- Stability: {result['stability_score']:.2f}%",
            f"- Total Trades: {result['total_trades']}",
            f"- Zero-trade folds: {result['zero_trade_folds']}",
            f"- Status: **{result['status']}**",
            "",
            "## Interpretation",
            "",
        ]
    )
    if result["status"] == "PASS":
        lines.extend(
            [
                "The fixed OOS portfolio satisfies every predeclared gate, including the minimum of 20 completed test trades.",
                "This is portfolio-level research evidence only and does not unlock live trading.",
                "",
                "## Next Step",
                "",
                "Proceed to the separately predeclared universe-expansion protocol and paper research.",
            ]
        )
    else:
        failed: list[str] = []
        if result["stability_score"] < MIN_STABILITY:
            failed.append(f"stability {result['stability_score']:.2f}% < {MIN_STABILITY:.0f}%")
        avg_pf = result["avg_pf"]
        if isinstance(avg_pf, float) and avg_pf < MIN_AVG_PF:
            failed.append(f"average PF {avg_pf:.4f} < {MIN_AVG_PF:.1f}")
        if result["worst_dd"] >= MAX_WORST_DD:
            failed.append(f"worst DD {result['worst_dd']:.4f}% >= {MAX_WORST_DD:.0f}%")
        avg_return = result["avg_return"]
        if isinstance(avg_return, float) and avg_return <= MIN_AVG_RETURN:
            failed.append(f"average return {avg_return:.4f}% <= 0%")
        if result["total_trades"] < MIN_TOTAL_TRADES:
            failed.append(
                f"total trades {result['total_trades']} < {MIN_TOTAL_TRADES}"
            )
        lines.extend(
            [
                "The portfolio does not satisfy the complete predeclared PASS gate: "
                + "; ".join(failed)
                + ".",
                "The result is statistically insufficient; no symbol may be removed retroactively to improve it.",
                "",
                "## Next Step",
                "",
                "Universe expansion is blocked by the specification because Portfolio WFO did not pass. Preserve the result, keep paper/live blocked, and validate any new hypothesis on a fresh predeclared period or universe.",
            ]
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run fixed-universe portfolio WFO for the four OOS alts"
    )
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--out-dir", type=Path, default=Path("results/portfolio_wfo_oos")
    )
    parser.add_argument(
        "--report-path", type=Path, default=Path("docs/PORTFOLIO_WFO_OOS.md")
    )
    parser.add_argument(
        "--symbols",
        type=_parse_symbols,
        default=DEFAULT_SYMBOLS,
        help="comma-separated fixed universe",
    )
    parser.add_argument("--profile", choices=(DEFAULT_PROFILE,), default=DEFAULT_PROFILE)
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--bars", type=int, default=15_000)
    parser.add_argument("--initial-equity", type=float, default=10_000.0)
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    symbols = tuple(args.symbols)
    portfolio = load_portfolio_data(args.data_dir, symbols, args.interval, args.bars)
    config = config_for_profile(args.profile).model_copy(
        update={
            "wfo_folds": 4,
            "wfo_lookback_days": 30,
            "wfo_embargo_bars": 3,
        }
    )
    summary = WalkForwardValidator(config).run(
        portfolio,
        initial_equity=args.initial_equity,
    )
    result = serialize_summary(summary, symbols)
    payload = {
        "symbols": list(symbols),
        "profile": args.profile,
        "interval": args.interval,
        "bars_per_symbol": args.bars,
        "initial_equity": args.initial_equity,
        "result": result,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary_json = args.out_dir / "summary.json"
    summary_md = args.out_dir / "summary.md"
    markdown = render_markdown(payload)
    summary_json.write_text(
        json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8"
    )
    summary_md.write_text(markdown, encoding="utf-8")

    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(markdown, encoding="utf-8")
    args.report_path.with_suffix(".json").write_text(
        json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8"
    )

    print("Portfolio WFO — OOS 4 Alts")
    print("==========================")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Period: {args.bars} bars per symbol")
    print(f"Profile: {args.profile}")
    for fold in result["fold_details"]:
        print(
            "Fold {fold}: Return {ret:+.4f}%, PF {pf}, DD {dd:.4f}%, Trades {trades}".format(
                fold=fold["fold"],
                ret=fold["return_pct"],
                pf=_display_metric(fold["profit_factor"]),
                dd=fold["max_drawdown"],
                trades=fold["num_trades"],
            )
        )
    print("Summary:")
    print(f"  Avg Return: {_display_metric(result['avg_return'])}%")
    print(f"  Avg PF: {_display_metric(result['avg_pf'])}")
    print(f"  Worst DD: {result['worst_dd']:.4f}%")
    print(f"  Stability: {result['stability_score']:.2f}%")
    print(f"  Total Trades: {result['total_trades']}")
    print(f"  Status: {result['status']}")
    print(f"Report: {args.report_path.resolve()}")
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run(args)
    except (FileNotFoundError, RuntimeError, ValueError, TypeError) as exc:
        print(f"portfolio WFO error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
