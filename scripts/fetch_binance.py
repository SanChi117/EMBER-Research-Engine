from __future__ import annotations

import argparse
from pathlib import Path

from ember.core.binance_history import fetch_history


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch paginated public Binance klines")
    parser.add_argument("--symbols", required=True, help="comma-separated symbols")
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--out-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for raw_symbol in args.symbols.split(","):
        symbol = raw_symbol.strip().upper()
        if not symbol:
            continue
        frame = fetch_history(symbol, args.interval, args.limit)
        path = args.out_dir / f"{symbol}_{args.interval}_{args.limit}.csv"
        frame.write_csv(path)
        print(f"{symbol}: {frame.height} rows -> {path}")


if __name__ == "__main__":
    main()
