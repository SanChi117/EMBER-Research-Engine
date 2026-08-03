from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import polars as pl

from ember.config import EmberConfig
from ember.core.binance_history import fetch_history
from ember.core.data_engine import DataEngine
from ember.research.profiles import config_for_profile
from ember.research.report_engine import ReportEngine
from ember.simulation.backtester import Backtester
from ember.simulation.walk_forward import WalkForwardValidator

DEFAULT_SYMBOLS = (
    "INJUSDT",
    "TONUSDT",
    "DOGEUSDT",
    "ARBUSDT",
    "NEARUSDT",
    "OPUSDT",
)
DEFAULT_PROFILES = (
    "baseline",
    "structure-bias",
    "high-vol-block",
    "opposite-liquidity",
)


def _parse_csv_list(value: str) -> tuple[str, ...]:
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    if not items:
        raise argparse.ArgumentTypeError("at least one value is required")
    return items


def _metric_value(value: float) -> float | str:
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    if math.isnan(value):
        return "nan"
    return value


def _load_or_fetch(
    symbol: str,
    interval: str,
    bars: int,
    data_dir: Path,
    skip_fetch: bool,
) -> pl.DataFrame:
    path = data_dir / f"{symbol}_{interval}_{bars}.csv"
    if skip_fetch:
        if not path.exists():
            raise FileNotFoundError(f"missing cached dataset: {path}")
        return DataEngine.load_csv(path).collect()

    frame = fetch_history(symbol, interval, bars)
    if frame.height != bars:
        raise RuntimeError(f"{symbol}: expected {bars} rows, received {frame.height}")
    data_dir.mkdir(parents=True, exist_ok=True)
    frame.write_csv(path)
    print(f"FETCH {symbol}: {frame.height} rows -> {path}")
    return frame


def _row(
    symbol: str,
    profile: str,
    bars: int,
    config: EmberConfig,
    backtester: Backtester,
    result: Any,
) -> dict[str, Any]:
    metrics = result.metrics
    rejects = backtester.last_diagnostics
    seen = int(rejects["bars_seen"])
    neutral = int(rejects["neutral_context"])
    return {
        "symbol": symbol,
        "profile": profile,
        "bars": bars,
        "bias_mode": config.htf_bias_mode,
        "blocked_volatility_regimes": ",".join(config.blocked_volatility_regimes),
        "tp_mode": config.tp_mode,
        "bars_seen": seen,
        "neutral_context": neutral,
        "neutral_ratio_pct": neutral / seen * 100.0 if seen else 0.0,
        "candidates": int(rejects["candidate_passed"]),
        "executed": int(metrics.num_trades),
        "return_pct": float(metrics.total_return),
        "profit_factor": _metric_value(float(metrics.profit_factor)),
        "max_drawdown_pct": float(metrics.max_drawdown),
        "win_rate_pct": float(metrics.win_rate),
        "final_equity": float(metrics.final_equity),
        "regime_reject": int(rejects["regime_reject"]),
        "rr_low": int(rejects["rr_low"]),
        "cost_gate": int(rejects["cost_gate"]),
        "quality_reject": int(rejects["quality_reject"]),
        "structure_reject": int(rejects["structure_reject"]),
        "halted": int(rejects["halted"]),
    }


def _numeric_pf(value: float | str) -> float:
    if value == "inf":
        return math.inf
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _qualifies_for_wfo(row: dict[str, Any]) -> bool:
    return (
        int(row["executed"]) > 0
        and float(row["return_pct"]) > 0.0
        and _numeric_pf(row["profit_factor"]) > 1.5
    )


def _fixed_portfolio(frames: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Build one immutable WFO universe from every requested symbol."""

    if not frames:
        raise ValueError("at least one symbol frame is required")
    return pl.concat(list(frames.values()), how="vertical").sort(["time", "symbol"])


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _markdown_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Symbol | Profile | Neutral | Candidates | Trades | Return | PF | DD | Win rate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        pf = row["profit_factor"]
        pf_text = str(pf) if isinstance(pf, str) else f"{float(pf):.4f}"
        lines.append(
            "| {symbol} | {profile} | {neutral:.2f}% | {candidates} | {executed} | "
            "{ret:+.4f}% | {pf} | {dd:.4f}% | {wr:.2f}% |".format(
                symbol=row["symbol"],
                profile=row["profile"],
                neutral=float(row["neutral_ratio_pct"]),
                candidates=row["candidates"],
                executed=row["executed"],
                ret=float(row["return_pct"]),
                pf=pf_text,
                dd=float(row["max_drawdown_pct"]),
                wr=float(row["win_rate_pct"]),
            )
        )
    return "\n".join(lines)


def _aggregate(rows: list[dict[str, Any]], profiles: tuple[str, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for profile in profiles:
        selected = [row for row in rows if row["profile"] == profile]
        result[profile] = {
            "symbols": len(selected),
            "positive_return_symbols": sum(float(row["return_pct"]) > 0 for row in selected),
            "pf_above_1_5_symbols": sum(
                _numeric_pf(row["profit_factor"]) > 1.5 for row in selected
            ),
            "wfo_eligible_symbols": sum(_qualifies_for_wfo(row) for row in selected),
            "total_trades": sum(int(row["executed"]) for row in selected),
            "average_return_pct": (
                sum(float(row["return_pct"]) for row in selected) / len(selected)
                if selected
                else 0.0
            ),
            "worst_drawdown_pct": max(
                (float(row["max_drawdown_pct"]) for row in selected),
                default=0.0,
            ),
        }
    return result


def _conditional_wfo(
    frames: dict[str, pl.DataFrame],
    rows: list[dict[str, Any]],
    profiles: tuple[str, ...],
    out_dir: Path,
    equity: float,
) -> dict[str, Any]:
    portfolio = _fixed_portfolio(frames)
    universe_symbols = sorted(frames)
    summaries: dict[str, Any] = {}
    for profile in profiles:
        qualifying_symbols = [
            row["symbol"]
            for row in rows
            if row["profile"] == profile and _qualifies_for_wfo(row)
        ]
        if len(qualifying_symbols) < 3:
            summaries[profile] = {
                "status": "BLOCKED",
                "reason": "fewer than 3 symbols have positive return and PF > 1.5",
                "qualifying_symbols": qualifying_symbols,
                "universe_policy": "fixed_all_requested_symbols",
                "universe_symbols": universe_symbols,
            }
            continue

        config = config_for_profile(profile)
        summary = WalkForwardValidator(config).run(portfolio, initial_equity=equity)
        ReportEngine().write_wfo(summary, out_dir / "wfo" / profile)
        summaries[profile] = {
            "status": summary.pass_fail,
            "qualifying_symbols": qualifying_symbols,
            "universe_policy": "fixed_all_requested_symbols",
            "universe_symbols": universe_symbols,
            "folds": len(summary.folds),
            "zero_trade_folds": sum(fold.num_trades == 0 for fold in summary.folds),
            "avg_return": _metric_value(float(summary.avg_return)),
            "avg_pf": _metric_value(float(summary.avg_pf)),
            "worst_dd": float(summary.worst_dd),
            "stability_score": float(summary.stability_score),
        }
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run 15000-bar multi-symbol EMBER research validation"
    )
    parser.add_argument(
        "--symbols",
        type=_parse_csv_list,
        default=DEFAULT_SYMBOLS,
        help="comma-separated Binance symbols",
    )
    parser.add_argument(
        "--profiles",
        type=_parse_csv_list,
        default=DEFAULT_PROFILES,
        help="comma-separated research profiles",
    )
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--bars", type=int, default=15_000)
    parser.add_argument("--equity", type=float, default=10_000.0)
    parser.add_argument("--data-dir", type=Path, default=Path("data/core_validation"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/core_validation"))
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--skip-wfo", action="store_true")
    args = parser.parse_args()

    symbols = tuple(symbol.upper() for symbol in args.symbols)
    profiles = tuple(args.profiles)
    for profile in profiles:
        config_for_profile(profile)
    if args.bars <= 0:
        raise ValueError("bars must be positive")

    frames = {
        symbol: _load_or_fetch(
            symbol,
            args.interval,
            args.bars,
            args.data_dir,
            args.skip_fetch,
        )
        for symbol in symbols
    }

    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        frame = frames[symbol]
        for profile in profiles:
            print(f"\nRUN {symbol} / {profile}")
            config = config_for_profile(profile)
            backtester = Backtester(config)
            result = backtester.run(frame, initial_equity=args.equity)
            report_dir = args.out_dir / "reports" / symbol / profile
            ReportEngine().write_backtest(result, report_dir)
            row = _row(symbol, profile, frame.height, config, backtester, result)
            rows.append(row)
            print(
                "RESULT {symbol} {profile}: trades={trades}, return={ret:+.4f}%, "
                "PF={pf}, DD={dd:.4f}%, neutral={neutral:.2f}%".format(
                    symbol=symbol,
                    profile=profile,
                    trades=row["executed"],
                    ret=row["return_pct"],
                    pf=row["profit_factor"],
                    dd=row["max_drawdown_pct"],
                    neutral=row["neutral_ratio_pct"],
                )
            )

    aggregate = _aggregate(rows, profiles)
    wfo = (
        {profile: {"status": "SKIPPED"} for profile in profiles}
        if args.skip_wfo
        else _conditional_wfo(frames, rows, profiles, args.out_dir, args.equity)
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(rows, args.out_dir / "summary.csv")
    payload = {
        "symbols": symbols,
        "profiles": profiles,
        "interval": args.interval,
        "bars_requested": args.bars,
        "results": rows,
        "aggregate": aggregate,
        "wfo": wfo,
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    markdown = [
        "# EMBER Core Validation",
        "",
        f"Symbols: {', '.join(symbols)}",
        f"Profiles: {', '.join(profiles)}",
        f"Interval: {args.interval}",
        f"Bars per symbol: {args.bars}",
        "",
        _markdown_table(rows),
        "",
        "## Aggregate",
        "",
        "```json",
        json.dumps(aggregate, indent=2, allow_nan=False),
        "```",
        "",
        "## Conditional WFO",
        "",
        "```json",
        json.dumps(wfo, indent=2, allow_nan=False),
        "```",
    ]
    (args.out_dir / "summary.md").write_text("\n".join(markdown), encoding="utf-8")

    print("\n=== CORE VALIDATION TABLE ===")
    print(_markdown_table(rows))
    print("\n=== AGGREGATE ===")
    print(json.dumps(aggregate, indent=2, allow_nan=False))
    print("\n=== CONDITIONAL WFO ===")
    print(json.dumps(wfo, indent=2, allow_nan=False))
    print(f"\nSummary: {(args.out_dir / 'summary.md').resolve()}")


if __name__ == "__main__":
    main()
