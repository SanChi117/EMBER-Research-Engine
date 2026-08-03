from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import polars as pl

from ember.core.binance_history import fetch_history
from ember.research.profiles import config_for_profile
from ember.simulation.backtester import Backtester

EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
TICKER_24H_URL = "https://fapi.binance.com/fapi/v1/ticker/24hr"
LEVERAGED_SUFFIXES = ("UP", "DOWN", "BULL", "BEAR")
DEFAULT_EXCLUDED = (
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "DOTUSDT",
    "MATICUSDT",
    "INJUSDT",
    "TONUSDT",
    "DOGEUSDT",
    "ARBUSDT",
    "NEARUSDT",
    "OPUSDT",
    "PEPEUSDT",
    "FETUSDT",
    "WIFUSDT",
    "SUIUSDT",
)


def _parse_csv_list(value: str) -> tuple[str, ...]:
    return tuple(item.strip().upper() for item in value.split(",") if item.strip())


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


def _base_asset(item: dict[str, Any], symbol: str) -> str:
    explicit = str(item.get("baseAsset", "")).upper()
    if explicit:
        return explicit
    return symbol[:-4] if symbol.endswith("USDT") else symbol


def filter_usdt_perpetual_symbols(
    payload: dict[str, Any],
    excluded: set[str],
) -> list[str]:
    symbols: list[str] = []
    for item in payload.get("symbols", []):
        symbol = str(item.get("symbol", "")).upper()
        base_asset = _base_asset(item, symbol)
        is_leveraged = any(base_asset.endswith(suffix) for suffix in LEVERAGED_SUFFIXES)
        if (
            item.get("status") == "TRADING"
            and item.get("contractType") == "PERPETUAL"
            and item.get("quoteAsset") == "USDT"
            and symbol
            and symbol not in excluded
            and not is_leveraged
        ):
            symbols.append(symbol)
    return sorted(set(symbols))


def _fetch_json(url: str) -> Any:
    request = Request(url, headers={"User-Agent": "EMBER-Research-Engine/0.2.0"})
    with urlopen(request, timeout=30) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def fetch_futures_universe(excluded: set[str]) -> list[str]:
    payload = _fetch_json(EXCHANGE_INFO_URL)
    if not isinstance(payload, dict):
        raise ValueError("unexpected Binance exchangeInfo response")
    return filter_usdt_perpetual_symbols(payload, excluded)


def parse_quote_volumes(payload: Any) -> dict[str, float]:
    if not isinstance(payload, list):
        raise ValueError("unexpected Binance 24h ticker response")
    volumes: dict[str, float] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol", "")).upper()
        if not symbol:
            continue
        try:
            quote_volume = float(item.get("quoteVolume", 0.0))
        except (TypeError, ValueError):
            quote_volume = 0.0
        volumes[symbol] = max(quote_volume, 0.0)
    return volumes


def fetch_quote_volumes() -> dict[str, float]:
    return parse_quote_volumes(_fetch_json(TICKER_24H_URL))


def rank_symbols_by_volume(
    symbols: list[str],
    quote_volumes: dict[str, float],
) -> list[str]:
    return sorted(symbols, key=lambda symbol: (-quote_volumes.get(symbol, 0.0), symbol))


def write_fixed_universe(
    path: Path,
    symbols: list[str],
    quote_volumes: dict[str, float],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "FROZEN_DISCOVERY_UNIVERSE",
        "selection_method": "top Binance USD-M perpetual USDT pairs by 24h quoteVolume after predeclared exclusions",
        "selected_at_utc": datetime.now(timezone.utc).isoformat(),
        "symbols": symbols,
        "quote_volume_24h": {
            symbol: quote_volumes.get(symbol, 0.0) for symbol in symbols
        },
        "research_note": "Discovery/in-sample universe only; not OOS evidence.",
    }
    path.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")


def liquidity_proxy(frame: pl.DataFrame) -> float:
    value = frame.select((pl.col("close") * pl.col("volume")).mean()).item()
    return float(value or 0.0)


def qualifies(
    trades: int,
    profit_factor: float | str,
    min_trades: int,
    min_profit_factor: float,
) -> bool:
    return trades >= min_trades and _numeric_pf(profit_factor) > min_profit_factor


def _write_outputs(rows: list[dict[str, Any]], out_dir: Path, protocol: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    columns = [
        "symbol",
        "status",
        "rows",
        "quote_volume_24h",
        "mean_quote_volume_per_bar",
        "trades",
        "return_pct",
        "profit_factor",
        "max_drawdown_pct",
        "win_rate_pct",
        "selected",
        "error",
    ]
    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})

    payload = {"protocol": protocol, "results": rows}
    (out_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    lines = [
        "# EMBER Universe Scanner",
        "",
        "This is a discovery sample, not an out-of-sample proof. The exact top-volume",
        "universe is frozen before the backtests and requires a separate untouched holdout",
        "or forward paper validation.",
        "",
        "| Symbol | 24h Quote Volume | Liquidity / 15m | Trades | Return | PF | DD | Selected | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        pf = row.get("profit_factor", 0.0)
        pf_text = str(pf) if isinstance(pf, str) else f"{float(pf):.4f}"
        lines.append(
            "| {symbol} | {volume:,.0f} | {liquidity:,.0f} | {trades} | {ret:+.4f}% | {pf} | "
            "{dd:.4f}% | {selected} | {status} |".format(
                symbol=row["symbol"],
                volume=float(row.get("quote_volume_24h", 0.0)),
                liquidity=float(row.get("mean_quote_volume_per_bar", 0.0)),
                trades=int(row.get("trades", 0)),
                ret=float(row.get("return_pct", 0.0)),
                pf=pf_text,
                dd=float(row.get("max_drawdown_pct", 0.0)),
                selected="yes" if row.get("selected") else "no",
                status=row.get("status", "unknown"),
            )
        )
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Research-only Binance USD-M universe discovery scanner"
    )
    parser.add_argument(
        "--symbols",
        type=_parse_csv_list,
        default=(),
        help="optional fixed comma-separated universe; otherwise rank exchangeInfo by 24h volume",
    )
    parser.add_argument("--exclude", type=_parse_csv_list, default=DEFAULT_EXCLUDED)
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--bars", type=int, default=15_000)
    parser.add_argument("--max-symbols", type=int, default=20)
    parser.add_argument("--min-liquidity", type=float, default=1_000_000.0)
    parser.add_argument("--min-trades", type=int, default=10)
    parser.add_argument("--min-profit-factor", type=float, default=1.0)
    parser.add_argument("--equity", type=float, default=10_000.0)
    parser.add_argument("--data-dir", type=Path, default=Path("data/universe_scan"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/universe_scan"))
    parser.add_argument(
        "--universe-output", type=Path, default=Path("data/universe_20.json")
    )
    args = parser.parse_args()

    if args.bars <= 0 or args.max_symbols <= 0:
        raise ValueError("bars and max-symbols must be positive")
    if args.min_liquidity < 0 or args.min_trades < 0 or args.min_profit_factor < 0:
        raise ValueError("scanner thresholds must be non-negative")

    excluded = set(args.exclude)
    if args.symbols:
        quote_volumes = {symbol: 0.0 for symbol in args.symbols}
        universe = [symbol for symbol in args.symbols if symbol not in excluded]
    else:
        candidates = fetch_futures_universe(excluded)
        quote_volumes = fetch_quote_volumes()
        universe = rank_symbols_by_volume(candidates, quote_volumes)
    universe = universe[: args.max_symbols]
    if not universe:
        raise ValueError("universe selection returned no symbols")

    write_fixed_universe(args.universe_output, universe, quote_volumes)
    config = config_for_profile("high-vol-block")
    args.data_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for index, symbol in enumerate(universe, start=1):
        print(f"[{index}/{len(universe)}] {symbol}")
        row: dict[str, Any] = {
            "symbol": symbol,
            "status": "ERROR",
            "rows": 0,
            "quote_volume_24h": quote_volumes.get(symbol, 0.0),
            "mean_quote_volume_per_bar": 0.0,
            "trades": 0,
            "return_pct": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_pct": 0.0,
            "win_rate_pct": 0.0,
            "selected": False,
            "error": "",
        }
        try:
            frame = fetch_history(symbol, args.interval, args.bars)
            row["rows"] = frame.height
            frame.write_csv(args.data_dir / f"{symbol}_{args.interval}_{frame.height}.csv")
            if frame.height != args.bars:
                row["status"] = "INSUFFICIENT_HISTORY"
                row["error"] = f"expected {args.bars}, received {frame.height}"
                rows.append(row)
                continue

            liquidity = liquidity_proxy(frame)
            row["mean_quote_volume_per_bar"] = liquidity
            if liquidity < args.min_liquidity:
                row["status"] = "LOW_LIQUIDITY"
                rows.append(row)
                continue

            result = Backtester(config).run(frame, initial_equity=args.equity)
            metrics = result.metrics
            pf = _metric_value(float(metrics.profit_factor))
            row.update(
                {
                    "status": "TESTED",
                    "trades": int(metrics.num_trades),
                    "return_pct": float(metrics.total_return),
                    "profit_factor": pf,
                    "max_drawdown_pct": float(metrics.max_drawdown),
                    "win_rate_pct": float(metrics.win_rate),
                    "selected": qualifies(
                        int(metrics.num_trades),
                        pf,
                        args.min_trades,
                        args.min_profit_factor,
                    ),
                }
            )
        except Exception as error:  # noqa: BLE001
            row["error"] = f"{type(error).__name__}: {error}"
        rows.append(row)

    protocol = {
        "profile": "high-vol-block",
        "interval": args.interval,
        "bars": args.bars,
        "selection": "top_24h_quote_volume_before_backtest",
        "universe_output": str(args.universe_output),
        "min_liquidity": args.min_liquidity,
        "min_trades": args.min_trades,
        "min_profit_factor": args.min_profit_factor,
        "excluded": sorted(excluded),
        "universe_size": len(universe),
    }
    _write_outputs(rows, args.out_dir, protocol)
    selected = [row["symbol"] for row in rows if row.get("selected")]
    print(f"Frozen universe: {args.universe_output.resolve()}")
    print(f"Selected by in-sample gates {len(selected)}/{len(rows)}: {', '.join(selected) or 'none'}")
    print(f"Summary: {(args.out_dir / 'summary.md').resolve()}")


if __name__ == "__main__":
    main()
