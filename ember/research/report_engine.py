"""Markdown, CSV and Parquet research reports."""

from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path
from typing import Any

import polars as pl

from ember.models import BacktestResult, WFOSummary


class ReportEngine:
    def write_backtest(self, result: BacktestResult, out_dir: Path) -> dict[str, Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        metrics = result.metrics
        report = out_dir / "backtest_report.md"
        report.write_text(
            "\n".join(
                [
                    "# EMBER Backtest Report",
                    "",
                    f"- Total Return: {metrics.total_return:.4f}%",
                    f"- Profit Factor: {metrics.profit_factor:.4f}",
                    f"- Max Drawdown: {metrics.max_drawdown:.4f}%",
                    f"- Win Rate: {metrics.win_rate:.4f}%",
                    f"- Average Trade: {metrics.avg_trade:.4f} R",
                    f"- Number of Trades: {metrics.num_trades}",
                    f"- Final Equity: {metrics.final_equity:.4f}",
                    "",
                    "Research-only. This report is not a live-trading authorization.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        rows = [self._serialize(asdict(trade)) for trade in result.trades]
        csv_path = out_dir / "backtest_trades.csv"
        parquet_path = out_dir / "backtest_trades.parquet"
        self._write_csv(rows, csv_path)
        if rows:
            pl.DataFrame(rows).write_parquet(parquet_path)
        else:
            pl.DataFrame({"id": pl.Series([], dtype=pl.Int64)}).write_parquet(parquet_path)
        return {"report": report, "csv": csv_path, "parquet": parquet_path}

    def write_wfo(self, summary: WFOSummary, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "wfo_report.md"
        lines = [
            "# EMBER Walk-Forward Report",
            "",
            f"- Avg Return: {summary.avg_return:.4f}%",
            f"- Avg PF: {summary.avg_pf:.4f}",
            f"- Worst DD: {summary.worst_dd:.4f}%",
            f"- Stability Score: {summary.stability_score:.2f}%",
            f"- Pass/Fail: **{summary.pass_fail}**",
            "",
            "| Fold | Train | Test | Return % | PF | DD % | Trades | Positive |",
            "|---:|---|---|---:|---:|---:|---:|:---:|",
        ]
        for fold in summary.folds:
            lines.append(
                "| {fold} | {train_start} -> {train_end} | {test_start} -> {test_end} | "
                "{ret:.4f} | {pf:.4f} | {dd:.4f} | {trades} | {positive} |".format(
                    fold=fold.fold,
                    train_start=fold.train_start.isoformat(),
                    train_end=fold.train_end.isoformat(),
                    test_start=fold.test_start.isoformat(),
                    test_end=fold.test_end.isoformat(),
                    ret=fold.return_pct,
                    pf=fold.profit_factor,
                    dd=fold.max_drawdown,
                    trades=fold.num_trades,
                    positive="yes" if fold.positive else "no",
                )
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def write_grid(self, rows: list[dict[str, Any]], out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "grid_report.md"
        lines = ["# EMBER Parameter Grid Report", ""]
        if not rows:
            lines.append("No valid parameter combinations were executed.")
        else:
            columns = list(rows[0])
            lines.append("| " + " | ".join(columns) + " |")
            lines.append("|" + "|".join("---" for _ in columns) + "|")
            for row in rows:
                lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    @staticmethod
    def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _serialize(row: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value.isoformat() if hasattr(value, "isoformat") else value
            for key, value in row.items()
        }
