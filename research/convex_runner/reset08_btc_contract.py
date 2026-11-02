"""RESET-08: independently hash and validate only the owner-approved BTC data."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path

from .data_contract import END, INTERVALS, DataIntegrityFailure


def check_btc(root: Path, expected: dict[str, str] | None = None):
    result = {}
    for tf, step in INTERVALS.items():
        path = root / f"BTCUSDT_{tf}.json"
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if expected is not None and expected[tf] != sha:
            raise DataIntegrityFailure("BTC_SHA256_MISMATCH")
        rows = json.loads(raw)
        if not rows or type(rows) is not list:
            raise DataIntegrityFailure("BTC_EMPTY")
        last = None
        for item in rows:
            if type(item) is not list or len(item) != 12:
                raise DataIntegrityFailure("BTC_SCHEMA")
            t = item[0]
            if type(t) is not int or t % step or item[6] != t + step - 1:
                raise DataIntegrityFailure("BTC_TIME")
            if last is not None and t != last + step:
                raise DataIntegrityFailure("BTC_GAP")
            o, h, low, c = (Decimal(item[k]) for k in range(1, 5))
            if (any(not n.is_finite() or n <= 0 for n in (o, h, low, c))
                or low > min(o, c) or h < max(o, c)):
                raise DataIntegrityFailure("BTC_OHLC")
            last = t
        if last != END - step:
            raise DataIntegrityFailure("BTC_END_MISSING")
        result[tf] = {"sha256": sha, "bars": len(rows),
                      "first_ms": rows[0][0], "last_ms": last}
    return result


def main():
    data = check_btc(Path("research/convex_runner/raw"))
    print("RESET08_BTC_SHA256_JSON=" +
          json.dumps(data, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
