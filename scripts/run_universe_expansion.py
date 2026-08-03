"""Run the conditional 20-symbol universe-expansion research batch.

The specification allows this batch only after the canonical OOS portfolio WFO
has status PASS.  The runner therefore enforces that prerequisite before it
loads or downloads any market data.  A fixed 20-symbol JSON file is required;
no symbol may be removed after performance is observed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Sequence

import polars as pl

from ember.core.binance_history import fetch_history
from ember.core.data_engine import DataEngine
from ember.research.profiles import config_for_profile
from ember.simulation.backtester import Backtester

EXPECTED_UNIVERSE_SIZE = 20
PROFILE = "high-vol-block"


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


def tier_for(trades: int, return_pct: float, profit_factor: float | str) -> str:
    """Apply the predeclared Tier 1/2/3 rules from the specification."""

    pf = _numeric_pf(profit_factor)
    if pf > 1.5 and return_pct > 0.0 and trades >= 10:
        return "Tier 1"
    if pf > 1.0 and return_pct > 0.0 and trades >= 5:
        return "Tier 2"
    return "Tier 3"


def expansion_verdict(rows: list[dict[str, Any]]) -> str:
    tier_one = sum(row.get("tier") == "Tier 1" for row in rows)
    if tier_one >= 10:
        return "PASS"
    if tier_one >= 5:
        return "PARTIAL"
    return "FAIL"


def load_portfolio_gate(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"portfolio WFO report not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("portfolio WFO report must be a JSON object")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise ValueError("portfolio WFO report has no result object")
    return result


def require_portfolio_pass(path: Path) -> dict[str, Any]:
    result = load_portfolio_gate(path)
    status = str(result.get("status", "UNKNOWN")).upper()
    if status != "PASS":
        raise PermissionError(
            "Universe Expansion 20 is blocked: canonical Portfolio WFO status "
            f"is {status}, expected PASS"
        )
    return result


def load_universe(path: Path, expected_size: int = EXPECTED_UNIVERSE_SIZE) -> tuple[str, ...]:
    if not path.exists():
        raise FileNotFoundError(f"universe file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_symbols: Any
    if isinstance(payload, list):
        raw_symbols = payload
    elif isinstance(payload, dict):
        raw_symbols = payload.get("symbols")
    else:
        raw_symbols = None
    if not isinstance(raw_symbols, list):
        raise ValueError("universe file must be a list or an object with a symbols list")

    symbols = tuple(str(item).strip().upper() for item in raw_symbols if str(item).strip())
    if len(symbols) != expected_size:
        raise ValueError(
            f"fixed universe must contain exactly {expected_size} symbols, received {len(symbols)}"
        )
    if len(set(symbols)) != len(symbols):
        raise ValueError("fixed universe contains duplicate symbols")
    if any(not symbol.endswith("USDT") for symbol in symbols):
        raise ValueError("every universe symbol must be a USDT pair")
    return symbols


def _load_or_download(
    symbol: str,
    interval: str,
    bars: int,
    data_dir: Path,
    allow_download: bool,
) -> pl.DataFrame:
    path = data_dir / f"{symbol}_{interval}_{bars}.csv"
    if path.exists():
        frame = DataEngine.load_csv(path).collect()
    else:
        if not allow_download:
            raise FileNotFoundError(f"missing dataset and downloads disabled: {path}")
        frame = fetch_history(symbol, interval, bars)
        data_dir.mkdir(parents=True, exist_ok=True)
        frame.write_csv(path)

    if frame.height != bars:
        raise RuntimeError(f"{symbol}: expected exactly {bars} rows, received {frame.height}")
    observed = set(frame.get_column("symbol").unique().to_list())
    if observed != {symbol}:
        raise RuntimeError(f"{symbol}: CSV symbol column contains {sorted(observed)}")
    return frame


def render_report(payload: dict[str, Any]) -> str:
    rows = payload.get("results", [])
    lines = [
        "# Universe Expansion 20",
        "",
        "## Protocol",
        "",
        f"- Source universe: `{payload['universe_file']}`",
        f"- Symbols: {len(payload['symbols'])}",
        f"- Interval: `{payload['interval']}`",
        f"- Bars per symbol: `{payload['bars_per_symbol']}`",
        f"- Profile: `{payload['profile']}`",
        "- Prerequisite: canonical Portfolio WFO OOS status `PASS`",
        "- Universe policy: exact frozen 20-symbol list; no post-result removal",
        "",
        "## Tier rules",
        "",
        "- Tier 1: PF > 1.5, return > 0, trades >= 10",
        "- Tier 2: PF > 1.0, return > 0, trades >= 5",
        "- Tier 3: PF <= 1.0, return <= 0, or insufficient trades",
        "",
        "## Results",
        "",
        "| Symbol | Trades | Return | PF | DD | Win Rate | Tier | Status |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    if rows:
        for row in rows:
            pf = row["profit_factor"]
            pf_text = str(pf) if isinstance(pf, str) else f"{float(pf):.4f}"
            lines.append(
                "| {symbol} | {trades} | {ret:+.4f}% | {pf} | {dd:.4f}% | "
                "{wr:.2f}% | {tier} | {status} |".format(
                    symbol=row["symbol"],
                    trades=row["trades"],
                    ret=row["return_pct"],
                    pf=pf_text,
                    dd=row["max_drawdown_pct"],
                    wr=row["win_rate_pct"],
                    tier=row["tier"],
                    status=row["status"],
                )
            )
    else:
        lines.append("| — | — | — | — | — | — | — | BLOCKED |")

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Tier 1: {payload.get('tier_counts', {}).get('Tier 1', 0)}/20",
            f"- Tier 2: {payload.get('tier_counts', {}).get('Tier 2', 0)}/20",
            f"- Tier 3: {payload.get('tier_counts', {}).get('Tier 3', 0)}/20",
            f"- Status: **{payload['status']}**",
            "",
            "## Interpretation",
            "",
        ]
    )
    if payload["status"] == "BLOCKED":
        lines.append(
            "The batch was not executed because the required Portfolio WFO OOS prerequisite did not pass. The runner and report contract exist, but no tier result is fabricated."
        )
    elif payload["status"] == "PASS":
        lines.append(
            "At least 10 of 20 symbols reached Tier 1. This permits research universe expansion and paper-mode evaluation, but does not unlock live trading."
        )
    elif payload["status"] == "PARTIAL":
        lines.append(
            "Only 5-9 symbols reached Tier 1. The result supports selective research only and requires a separately frozen validation design."
        )
    else:
        lines.append(
            "Four or fewer symbols reached Tier 1. The expansion hypothesis is rejected for this fixed universe and period."
        )
    return "\n".join(lines) + "\n"


def blocked_payload(
    universe_file: Path,
    interval: str,
    bars: int,
    portfolio_status: str,
) -> dict[str, Any]:
    return {
        "status": "BLOCKED",
        "reason": f"Portfolio WFO OOS status is {portfolio_status}; PASS required",
        "portfolio_wfo_status": portfolio_status,
        "universe_file": str(universe_file),
        "symbols": [],
        "interval": interval,
        "bars_per_symbol": bars,
        "profile": PROFILE,
        "results": [],
        "tier_counts": {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0},
        "paper_gate": "BLOCKED",
        "live_gate": "BLOCKED",
    }


def _write_outputs(payload: dict[str, Any], out_dir: Path, report_path: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = render_report(payload)
    (out_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8"
    )
    (out_dir / "summary.md").write_text(report, encoding="utf-8")
    report_path.write_text(report, encoding="utf-8")
    report_path.with_suffix(".json").write_text(
        json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8"
    )

    rows = payload.get("results", [])
    columns = [
        "symbol",
        "trades",
        "return_pct",
        "profit_factor",
        "max_drawdown_pct",
        "win_rate_pct",
        "tier",
        "status",
        "error",
    ]
    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Conditionally run the frozen 20-symbol universe expansion batch"
    )
    parser.add_argument(
        "--portfolio-report",
        type=Path,
        default=Path("docs/PORTFOLIO_WFO_OOS.json"),
    )
    parser.add_argument(
        "--universe-file", type=Path, default=Path("data/universe_20.json")
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data/universe_expansion_20")
    )
    parser.add_argument(
        "--out-dir", type=Path, default=Path("results/universe_expansion_20")
    )
    parser.add_argument(
        "--report-path", type=Path, default=Path("docs/UNIVERSE_EXPANSION_20.md")
    )
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--bars", type=int, default=15_000)
    parser.add_argument("--initial-equity", type=float, default=10_000.0)
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="require every CSV to already exist locally",
    )
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    gate = require_portfolio_pass(args.portfolio_report)
    symbols = load_universe(args.universe_file)
    config = config_for_profile(PROFILE)
    rows: list[dict[str, Any]] = []

    for index, symbol in enumerate(symbols, start=1):
        print(f"[{index}/{len(symbols)}] {symbol}")
        row: dict[str, Any] = {
            "symbol": symbol,
            "trades": 0,
            "return_pct": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_pct": 0.0,
            "win_rate_pct": 0.0,
            "tier": "Tier 3",
            "status": "ERROR",
            "error": "",
        }
        try:
            frame = _load_or_download(
                symbol,
                args.interval,
                args.bars,
                args.data_dir,
                allow_download=not args.no_download,
            )
            result = Backtester(config).run(frame, initial_equity=args.initial_equity)
            metrics = result.metrics
            pf = _metric_value(float(metrics.profit_factor))
            row.update(
                {
                    "trades": int(metrics.num_trades),
                    "return_pct": float(metrics.total_return),
                    "profit_factor": pf,
                    "max_drawdown_pct": float(metrics.max_drawdown),
                    "win_rate_pct": float(metrics.win_rate),
                    "tier": tier_for(
                        int(metrics.num_trades), float(metrics.total_return), pf
                    ),
                    "status": "TESTED",
                }
            )
        except Exception as error:  # noqa: BLE001
            row["error"] = f"{type(error).__name__}: {error}"
        rows.append(row)

    tier_counts = {
        tier: sum(row["tier"] == tier for row in rows)
        for tier in ("Tier 1", "Tier 2", "Tier 3")
    }
    payload = {
        "status": expansion_verdict(rows),
        "portfolio_wfo_status": gate["status"],
        "universe_file": str(args.universe_file),
        "symbols": list(symbols),
        "interval": args.interval,
        "bars_per_symbol": args.bars,
        "initial_equity": args.initial_equity,
        "profile": PROFILE,
        "results": rows,
        "tier_counts": tier_counts,
        "paper_gate": "RESEARCH_ONLY",
        "live_gate": "BLOCKED",
    }
    _write_outputs(payload, args.out_dir, args.report_path)
    print(
        "Universe Expansion 20: "
        f"{payload['status']} — Tier 1 {tier_counts['Tier 1']}/20"
    )
    print(f"Report: {args.report_path.resolve()}")
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.bars <= 0 or args.initial_equity <= 0:
        print("universe expansion error: bars and initial-equity must be positive", file=sys.stderr)
        return 2
    try:
        run(args)
    except PermissionError as exc:
        try:
            result = load_portfolio_gate(args.portfolio_report)
            status = str(result.get("status", "UNKNOWN")).upper()
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            status = "UNKNOWN"
        payload = blocked_payload(args.universe_file, args.interval, args.bars, status)
        _write_outputs(payload, args.out_dir, args.report_path)
        print(f"universe expansion blocked: {exc}", file=sys.stderr)
        return 3
    except (
        FileNotFoundError,
        RuntimeError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        print(f"universe expansion error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
