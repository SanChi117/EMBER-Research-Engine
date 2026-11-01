"""RESET-07: verify raw Binance USD-M kline arrays and print reproducible SHA256."""
from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path

SYMBOLS = ("SOLUSDT", "LINKUSDT", "AVAXUSDT", "NEARUSDT", "SUIUSDT",
           "ARBUSDT", "APTUSDT", "INJUSDT", "TIAUSDT", "DOGEUSDT")
INTERVALS = {"4h": 14_400_000, "1d": 86_400_000}
START = 1704067200000
END = 1793491200000


class DataIntegrityFailure(ValueError):
    pass


def load_raw(root: Path, symbol: str, tf: str, *, expected_sha: str | None = None):
    if symbol not in SYMBOLS or tf not in INTERVALS:
        raise DataIntegrityFailure("UNREGISTERED_SYMBOL_OR_TIMEFRAME")
    raw = (root / f"{symbol}_{tf}.json").read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if expected_sha is not None and sha != expected_sha:
        raise DataIntegrityFailure("RAW_SHA256_MISMATCH")
    try:
        rows = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise DataIntegrityFailure("INVALID_SOURCE_JSON") from exc
    if type(rows) is not list or not rows:
        raise DataIntegrityFailure("MISSING_PRICE_BARS")
    previous = None
    gaps = []
    for row in rows:
        if type(row) is not list or len(row) != 12:
            raise DataIntegrityFailure("INVALID_BINANCE_KLINE_SCHEMA")
        t = row[0]
        step = INTERVALS[tf]
        if type(t) is not int or t % step != 0 or row[6] != t + step - 1:
            raise DataIntegrityFailure("INVALID_KLINE_CLOCK_OR_DURATION")
        try:
            o, h, low, close = (Decimal(row[i]) for i in range(1, 5))
        except (ValueError, TypeError) as exc:
            raise DataIntegrityFailure("INVALID_KLINE_DECIMAL") from exc
        if (not all(x.is_finite() and x > 0 for x in (o, h, low, close))
            or low > min(o, close) or h < max(o, close)):
            raise DataIntegrityFailure("INVALID_KLINE_OHLC_GEOMETRY")
        if previous is not None:
            if t <= previous:
                raise DataIntegrityFailure("DUPLICATED_OR_REVERSED_BAR")
            if t - previous != step:
                gaps.append({"first_missing_ms": previous + step,
                             "next_observed_ms": t,
                             "missing_intervals": (t - previous) // step - 1})
        previous = t
    if rows[-1][0] >= END or rows[0][0] >= END:
        raise DataIntegrityFailure("OUT_OF_SCOPE_PROVIDER_DATA")
    # Valid inception gaps are not interpolated; observation begins at first bar.
    return rows, {"symbol": symbol, "timeframe": tf, "sha256": sha,
                  "bars": len(rows), "first_open_ms": rows[0][0],
                  "last_open_ms": rows[-1][0], "gaps": gaps}


def audit_all(root: Path, pinned: dict | None = None):
    result = {}
    for symbol in SYMBOLS:
        result[symbol] = {}
        for tf in INTERVALS:
            expect = pinned[symbol][tf] if pinned is not None else None
            _, info = load_raw(root, symbol, tf, expected_sha=expect)
            result[symbol][tf] = info
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--raw-root", default="research/convex_runner/raw")
    p.add_argument("--manifest")
    args = p.parse_args()
    pins = json.loads(Path(args.manifest).read_text()) if args.manifest else None
    audit = audit_all(Path(args.raw_root), pins)
    print("RESET07_SOURCE_SHA256_JSON=" +
          json.dumps(audit, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
