from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl

from ember.config import EmberConfig
from ember.core.binance_history import fetch_history
from ember.core.context_builder import ContextBuilder
from ember.core.data_engine import DataEngine
from ember.core.features import FeatureBuilder
from ember.research.profiles import config_for_profile
from ember.research.report_engine import ReportEngine
from ember.simulation.backtester import Backtester
from ember.simulation.walk_forward import WalkForwardValidator
from ember.utils import timeframe_to_minutes

DEFAULT_SYMBOLS = ("PEPEUSDT", "FETUSDT", "WIFUSDT", "SUIUSDT")
CORE_HIGH_VOL_BLOCK = {
    "symbols": 6,
    "positive_pf_1_5": 6,
    "total_trades": 73,
    "average_return_pct": 8.751167400327335,
    "worst_drawdown_pct": 2.439697743696847,
    "wfo_status": "PASS_WITH_WARNING",
}


def _parse_csv_list(value: str) -> tuple[str, ...]:
    items = tuple(item.strip().upper() for item in value.split(",") if item.strip())
    if not items:
        raise argparse.ArgumentTypeError("at least one symbol is required")
    return items


def _metric_value(value: float) -> float | str:
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    if math.isnan(value):
        return "nan"
    return value


def _numeric_pf(value: float | str) -> float:
    if value == "inf":
        return math.inf
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


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
        frame = DataEngine.load_csv(path).collect()
    else:
        frame = fetch_history(symbol, interval, bars)
        data_dir.mkdir(parents=True, exist_ok=True)
        frame.write_csv(path)
        print(f"FETCH {symbol}: {frame.height} rows -> {path}")

    if frame.height != bars:
        raise RuntimeError(
            f"{symbol}: expected exactly {bars} rows, received {frame.height}; "
            "do not replace or drop the symbol without documenting the data failure"
        )
    return frame


def _data_quality(frame: pl.DataFrame, interval: str) -> dict[str, Any]:
    ordered = frame.sort("time")
    times = ordered.get_column("time").to_list()
    expected_seconds = timeframe_to_minutes(interval) * 60
    gap_count = 0
    largest_gap_seconds = 0.0
    for previous, current in zip(times, times[1:], strict=False):
        if not isinstance(previous, datetime) or not isinstance(current, datetime):
            continue
        delta = (current - previous).total_seconds()
        largest_gap_seconds = max(largest_gap_seconds, delta)
        if delta != expected_seconds:
            gap_count += 1

    quote_volume = ordered.select((pl.col("close") * pl.col("volume")).mean()).item()
    zero_volume = ordered.select((pl.col("volume") <= 0).mean()).item()
    duplicate_count = ordered.height - ordered.get_column("time").n_unique()
    first_time = times[0]
    last_time = times[-1]
    coverage_days = (
        (last_time - first_time).total_seconds() / 86400.0
        if isinstance(first_time, datetime) and isinstance(last_time, datetime)
        else 0.0
    )
    return {
        "rows": ordered.height,
        "coverage_days": coverage_days,
        "gap_count": gap_count,
        "largest_gap_minutes": largest_gap_seconds / 60.0,
        "duplicate_timestamps": duplicate_count,
        "zero_volume_ratio_pct": float(zero_volume or 0.0) * 100.0,
        "mean_quote_volume_per_bar": float(quote_volume or 0.0),
        "mean_quote_volume_per_day": float(quote_volume or 0.0) * 96.0,
    }


def _context_distribution(
    frame: pl.DataFrame,
    config: EmberConfig,
) -> tuple[dict[str, float], dict[str, float]]:
    validated = DataEngine.validate(frame.lazy())
    features = FeatureBuilder(config)
    entry_frame = features.add_features(validated).collect().sort("time")
    htf_frames = {
        timeframe: features.add_features(
            DataEngine.resample(validated, config.entry_tf, timeframe)
        ).collect()
        for timeframe in config.context_tfs
        if timeframe != config.entry_tf
    }
    builder = ContextBuilder(config)
    regime_counts: Counter[str] = Counter()
    bias_counts: Counter[str] = Counter()
    for row_index in range(60, entry_frame.height):
        row = entry_frame.row(row_index, named=True)
        context = builder.build_at(
            symbol=str(row["symbol"]),
            entry_time=row["time"],
            entry_row=row,
            htf_frames=htf_frames,
        )
        regime_counts[context.regime] += 1
        bias_counts[context.bias] += 1

    total = sum(regime_counts.values())
    regime_pct = {
        name: regime_counts[name] / total * 100.0 if total else 0.0
        for name in ("high_vol", "trend", "range", "low_vol")
    }
    bias_pct = {
        name: bias_counts[name] / total * 100.0 if total else 0.0
        for name in ("bull", "bear", "neutral")
    }
    return regime_pct, bias_pct


def _wfo_payload(summary: Any) -> dict[str, Any]:
    zero_trade_folds = sum(fold.num_trades == 0 for fold in summary.folds)
    if summary.pass_fail == "PASS" and zero_trade_folds:
        status = "PASS_WITH_WARNING"
    else:
        status = summary.pass_fail
    return {
        "status": status,
        "formal_status": summary.pass_fail,
        "folds": len(summary.folds),
        "zero_trade_folds": zero_trade_folds,
        "avg_return_pct": _metric_value(float(summary.avg_return)),
        "avg_profit_factor": _metric_value(float(summary.avg_pf)),
        "worst_drawdown_pct": float(summary.worst_dd),
        "stability_score_pct": float(summary.stability_score),
        "fold_results": [
            {
                "fold": fold.fold,
                "return_pct": float(fold.return_pct),
                "profit_factor": _metric_value(float(fold.profit_factor)),
                "max_drawdown_pct": float(fold.max_drawdown),
                "trades": int(fold.num_trades),
                "positive": bool(fold.positive),
                "train_start": fold.train_start.isoformat(),
                "train_end": fold.train_end.isoformat(),
                "test_start": fold.test_start.isoformat(),
                "test_end": fold.test_end.isoformat(),
            }
            for fold in summary.folds
        ],
    }


def verdict(rows: list[dict[str, Any]]) -> tuple[str, int]:
    qualifying = sum(
        float(row["return_pct"]) > 0.0
        and _numeric_pf(row["profit_factor"]) > 1.5
        for row in rows
    )
    if qualifying >= 3:
        return "PASS", qualifying
    if qualifying == 2:
        return "PARTIAL", qualifying
    return "FAIL", qualifying


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "symbol",
        "bars",
        "trades",
        "return_pct",
        "profit_factor",
        "max_drawdown_pct",
        "win_rate_pct",
        "wfo_status",
        "wfo_folds",
        "wfo_zero_trade_folds",
        "high_vol_pct",
        "trend_pct",
        "range_pct",
        "low_vol_pct",
        "mean_quote_volume_per_bar",
        "gap_count",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in columns})


def _table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Symbol | Trades | Return | PF | DD | Win rate | WFO status |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        pf = row["profit_factor"]
        pf_text = str(pf) if isinstance(pf, str) else f"{float(pf):.4f}"
        lines.append(
            "| {symbol} | {trades} | {ret:+.4f}% | {pf} | {dd:.4f}% | "
            "{win:.2f}% | {wfo} |".format(
                symbol=row["symbol"],
                trades=row["trades"],
                ret=row["return_pct"],
                pf=pf_text,
                dd=row["max_drawdown_pct"],
                win=row["win_rate_pct"],
                wfo=row["wfo_status"],
            )
        )
    return "\n".join(lines)


def _regime_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Symbol | High vol | Trend | Range | Low vol | Mean quote vol / 15m | Gaps |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {symbol} | {high:.2f}% | {trend:.2f}% | {range:.2f}% | {low:.2f}% | "
            "{volume:,.0f} USDT | {gaps} |".format(
                symbol=row["symbol"],
                high=row["high_vol_pct"],
                trend=row["trend_pct"],
                range=row["range_pct"],
                low=row["low_vol_pct"],
                volume=row["mean_quote_volume_per_bar"],
                gaps=row["gap_count"],
            )
        )
    return "\n".join(lines)


def _diagnostics_section(rows: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for row in rows:
        blocks.extend(
            [
                f"### {row['symbol']}",
                "",
                "```json",
                json.dumps(row["reject_diagnostics"], indent=2, allow_nan=False),
                "```",
                "",
            ]
        )
    return "\n".join(blocks)


def _wfo_section(rows: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for row in rows:
        blocks.extend(
            [
                f"### {row['symbol']}",
                "",
                "```json",
                json.dumps(row["wfo"], indent=2, allow_nan=False),
                "```",
                "",
            ]
        )
    return "\n".join(blocks)


def _markdown(
    rows: list[dict[str, Any]],
    decision: str,
    qualifying: int,
    config: EmberConfig,
    interval: str,
    bars: int,
) -> str:
    average_return = sum(float(row["return_pct"]) for row in rows) / len(rows)
    average_dd = sum(float(row["max_drawdown_pct"]) for row in rows) / len(rows)
    total_trades = sum(int(row["trades"]) for row in rows)
    if decision == "PASS":
        interpretation = (
            "Порог robustness пройден. Следующий исследовательский этап — расширение "
            "фиксированного universe и portfolio-level paper comparison."
        )
    elif decision == "PARTIAL":
        interpretation = (
            "Результат зависит от symbol/sector/regime. Нельзя расширять universe без "
            "дополнительного анализа фильтров ликвидности и режимов."
        )
    else:
        interpretation = (
            "High-vol-block не подтвердил переносимость на холодный universe. "
            "Core-6 результат следует считать возможным selection bias до исправления причины."
        )

    return "\n".join(
        [
            "# EMBER Out-of-Sample Validation: 4 New Alts",
            "",
            "Дата выполнения фиксируется временем GitHub Actions artifact/commit.",
            "",
            "## Predeclared scope",
            "",
            f"- Symbols: `{', '.join(row['symbol'] for row in rows)}`",
            f"- Interval: `{interval}`",
            f"- Bars per symbol: `{bars}`",
            "- Profile: `high-vol-block`",
            f"- `blocked_volatility_regimes={config.blocked_volatility_regimes}`",
            f"- `min_confidence={config.min_confidence}`",
            f"- `min_rr={config.min_rr}`",
            f"- WFO folds: `{config.wfo_folds}`",
            f"- WFO lookback: `{config.wfo_lookback_days}` days",
            f"- WFO embargo: `{config.wfo_embargo_bars}` bars",
            "- No symbol was removed because of poor performance.",
            "",
            "The shared downloader prefers Binance Vision spot klines and falls back to "
            "Binance USD-M Futures. This is the same project data path used by the core study.",
            "",
            "## Results",
            "",
            _table(rows),
            "",
            f"Total trades: **{total_trades}**  ",
            f"Average return: **{average_return:+.4f}%**  ",
            f"Average drawdown: **{average_dd:.4f}%**",
            "",
            "## Verdict",
            "",
            f"**{decision} — {qualifying}/4 symbols have positive return and PF > 1.5.**",
            "",
            interpretation,
            "",
            "The verdict uses only the predeclared rule: PASS >=3, PARTIAL =2, FAIL <=1.",
            "",
            "## Comparison with core 6",
            "",
            "| Universe | Qualifying symbols | Trades | Average return | Worst DD | WFO |",
            "|---|---:|---:|---:|---:|---|",
            "| Core 6 high-vol-block | 6/6 | 73 | +8.7512% | 2.4397% | PASS_WITH_WARNING |",
            (
                f"| OOS 4 high-vol-block | {qualifying}/4 | {total_trades} | "
                f"{average_return:+.4f}% | "
                f"{max(float(row['max_drawdown_pct']) for row in rows):.4f}% | mixed per symbol |"
            ),
            "",
            "Core and OOS histories are separate symbol universes. This comparison does not "
            "remove weak OOS symbols and does not re-optimize parameters.",
            "",
            "## Regime and data-quality diagnostics",
            "",
            _regime_table(rows),
            "",
            "A gap is any adjacent timestamp delta that is not exactly one 15-minute interval. "
            "Liquidity is a diagnostic proxy, not an exclusion rule in this run.",
            "",
            "## Reject diagnostics",
            "",
            _diagnostics_section(rows),
            "## Per-symbol WFO details",
            "",
            _wfo_section(rows),
            "## Gate",
            "",
            "```text",
            f"OOS verdict: {decision}",
            "Paper gate: BLOCKED until 100 completed paper trades and 30 days",
            "Live gate: BLOCKED",
            "```",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run predeclared out-of-sample validation on four new altcoins"
    )
    parser.add_argument("--symbols", type=_parse_csv_list, default=DEFAULT_SYMBOLS)
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--bars", type=int, default=15_000)
    parser.add_argument("--equity", type=float, default=10_000.0)
    parser.add_argument("--data-dir", type=Path, default=Path("data/oos_4alts"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/oos_4alts"))
    parser.add_argument("--skip-fetch", action="store_true")
    args = parser.parse_args()

    symbols = tuple(args.symbols)
    if len(symbols) != 4:
        raise ValueError("this protocol requires exactly four predeclared symbols")
    if len(set(symbols)) != 4:
        raise ValueError("symbols must be unique")
    if args.bars <= 0:
        raise ValueError("bars must be positive")

    config = config_for_profile("high-vol-block")
    if config.blocked_volatility_regimes != ("high_vol",):
        raise RuntimeError("high-vol-block profile does not block high_vol")
    if config.min_confidence != 43.0 or config.min_rr != 1.8:
        raise RuntimeError("OOS protocol requires min_confidence=43 and min_rr=1.8")
    if (
        config.wfo_folds != 4
        or config.wfo_lookback_days != 30
        or config.wfo_embargo_bars != 3
    ):
        raise RuntimeError("OOS protocol requires 4 folds, 30-day lookback and 3-bar embargo")

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
    report_engine = ReportEngine()
    for symbol in symbols:
        print(f"\n=== OOS {symbol} ===")
        frame = frames[symbol]
        quality = _data_quality(frame, args.interval)
        regimes, biases = _context_distribution(frame, config)

        backtester = Backtester(config)
        result = backtester.run(frame, initial_equity=args.equity)
        report_engine.write_backtest(
            result,
            args.out_dir / "reports" / symbol / "backtest",
        )

        wfo_summary = WalkForwardValidator(config).run(
            frame,
            initial_equity=args.equity,
        )
        report_engine.write_wfo(
            wfo_summary,
            args.out_dir / "reports" / symbol / "wfo",
        )
        wfo = _wfo_payload(wfo_summary)
        metrics = result.metrics
        row = {
            "symbol": symbol,
            "bars": frame.height,
            "trades": int(metrics.num_trades),
            "return_pct": float(metrics.total_return),
            "profit_factor": _metric_value(float(metrics.profit_factor)),
            "max_drawdown_pct": float(metrics.max_drawdown),
            "win_rate_pct": float(metrics.win_rate),
            "final_equity": float(metrics.final_equity),
            "wfo_status": wfo["status"],
            "wfo_folds": wfo["folds"],
            "wfo_zero_trade_folds": wfo["zero_trade_folds"],
            "high_vol_pct": regimes["high_vol"],
            "trend_pct": regimes["trend"],
            "range_pct": regimes["range"],
            "low_vol_pct": regimes["low_vol"],
            "bias_distribution_pct": biases,
            "mean_quote_volume_per_bar": quality["mean_quote_volume_per_bar"],
            "gap_count": quality["gap_count"],
            "data_quality": quality,
            "regime_distribution_pct": regimes,
            "reject_diagnostics": dict(backtester.last_diagnostics),
            "wfo": wfo,
        }
        rows.append(row)
        print(
            "RESULT {symbol}: trades={trades}, return={ret:+.4f}%, PF={pf}, "
            "DD={dd:.4f}%, WFO={wfo}".format(
                symbol=symbol,
                trades=row["trades"],
                ret=row["return_pct"],
                pf=row["profit_factor"],
                dd=row["max_drawdown_pct"],
                wfo=row["wfo_status"],
            )
        )

    decision, qualifying = verdict(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(rows, args.out_dir / "summary.csv")
    payload = {
        "protocol": {
            "symbols": symbols,
            "interval": args.interval,
            "bars_per_symbol": args.bars,
            "profile": "high-vol-block",
            "config": {
                "blocked_volatility_regimes": config.blocked_volatility_regimes,
                "min_confidence": config.min_confidence,
                "min_rr": config.min_rr,
                "wfo_folds": config.wfo_folds,
                "wfo_lookback_days": config.wfo_lookback_days,
                "wfo_embargo_bars": config.wfo_embargo_bars,
            },
        },
        "verdict": decision,
        "qualifying_symbols": qualifying,
        "criteria": {"PASS": ">=3", "PARTIAL": "2", "FAIL": "<=1"},
        "core_high_vol_block": CORE_HIGH_VOL_BLOCK,
        "results": rows,
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    markdown = _markdown(
        rows,
        decision,
        qualifying,
        config,
        args.interval,
        args.bars,
    )
    (args.out_dir / "summary.md").write_text(markdown, encoding="utf-8")

    print("\n=== OUT-OF-SAMPLE TABLE ===")
    print(_table(rows))
    print(f"\nVERDICT: {decision} ({qualifying}/4 qualifying symbols)")
    print(f"Summary: {(args.out_dir / 'summary.md').resolve()}")


if __name__ == "__main__":
    main()
