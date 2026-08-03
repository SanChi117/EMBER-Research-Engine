from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import polars as pl

from ember.core.data_engine import DataEngine
from ember.research.profiles import config_for_profile
from ember.research.report_engine import ReportEngine
from ember.simulation.walk_forward import WalkForwardValidator

DEFAULT_SYMBOLS = (
    "INJUSDT",
    "TONUSDT",
    "DOGEUSDT",
    "ARBUSDT",
    "NEARUSDT",
    "OPUSDT",
)
DEFAULT_PROFILES = ("baseline", "high-vol-block", "opposite-liquidity")


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


def _load_fixed_universe(
    data_dir: Path,
    symbols: tuple[str, ...],
    interval: str,
    bars: int,
) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for symbol in symbols:
        path = data_dir / f"{symbol}_{interval}_{bars}.csv"
        if not path.exists():
            raise FileNotFoundError(f"missing fixed-universe dataset: {path}")
        frame = DataEngine.load_csv(path).collect()
        if frame.height != bars:
            raise RuntimeError(f"{symbol}: expected {bars} rows, received {frame.height}")
        frames.append(frame)
    return pl.concat(frames, how="vertical").sort(["time", "symbol"])


def _serialize_summary(summary: Any, symbols: tuple[str, ...]) -> dict[str, Any]:
    return {
        "status": summary.pass_fail,
        "universe_policy": "fixed_all_requested_symbols",
        "universe_symbols": list(symbols),
        "folds": len(summary.folds),
        "zero_trade_folds": sum(fold.num_trades == 0 for fold in summary.folds),
        "avg_return": _metric_value(float(summary.avg_return)),
        "avg_pf": _metric_value(float(summary.avg_pf)),
        "worst_dd": float(summary.worst_dd),
        "stability_score": float(summary.stability_score),
        "fold_details": [
            {
                "fold": fold.fold,
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run purged WFO on one fixed, predeclared symbol universe"
    )
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("results/fixed_wfo"))
    parser.add_argument("--symbols", type=_parse_csv_list, default=DEFAULT_SYMBOLS)
    parser.add_argument("--profiles", type=_parse_csv_list, default=DEFAULT_PROFILES)
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--bars", type=int, default=15_000)
    parser.add_argument("--equity", type=float, default=10_000.0)
    args = parser.parse_args()

    symbols = tuple(symbol.upper() for symbol in args.symbols)
    profiles = tuple(args.profiles)
    portfolio = _load_fixed_universe(args.data_dir, symbols, args.interval, args.bars)
    payload: dict[str, Any] = {
        "symbols": list(symbols),
        "profiles": list(profiles),
        "interval": args.interval,
        "bars_per_symbol": args.bars,
        "results": {},
    }

    for profile in profiles:
        config = config_for_profile(profile)
        summary = WalkForwardValidator(config).run(
            portfolio,
            initial_equity=args.equity,
        )
        ReportEngine().write_wfo(summary, args.out_dir / profile)
        serialized = _serialize_summary(summary, symbols)
        payload["results"][profile] = serialized
        print(
            "WFO {profile}: status={status}, folds={folds}, zero_trade_folds={zero}, "
            "avg_return={ret}, avg_pf={pf}, worst_dd={dd:.4f}%, stability={stability:.2f}%".format(
                profile=profile,
                status=serialized["status"],
                folds=serialized["folds"],
                zero=serialized["zero_trade_folds"],
                ret=serialized["avg_return"],
                pf=serialized["avg_pf"],
                dd=serialized["worst_dd"],
                stability=serialized["stability_score"],
            )
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    lines = [
        "# EMBER Fixed-Universe WFO",
        "",
        f"Universe: {', '.join(symbols)}",
        f"Bars per symbol: {args.bars}",
        "",
        "| Profile | Status | Folds | Zero-trade folds | Avg return | Avg PF | Worst DD | Stability |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for profile in profiles:
        result = payload["results"][profile]
        lines.append(
            "| {profile} | {status} | {folds} | {zero} | {ret} | {pf} | {dd:.4f}% | {stability:.2f}% |".format(
                profile=profile,
                status=result["status"],
                folds=result["folds"],
                zero=result["zero_trade_folds"],
                ret=result["avg_return"],
                pf=result["avg_pf"],
                dd=result["worst_dd"],
                stability=result["stability_score"],
            )
        )
    (args.out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Summary: {(args.out_dir / 'summary.md').resolve()}")


if __name__ == "__main__":
    main()
