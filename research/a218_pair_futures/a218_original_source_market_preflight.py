"""A218: run PINNED ORIGINAL pair signal engine on SHA-receipted genuine Binance UM daily data.

Strictly a preflight and diagnostic. Not a futures-accurate PnL engine.
No leverage, simulated fills, orders, portfolio return or strategy changes.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REMOTE_COMMIT = "1823a2137d5b02a5649b32328d024057c968ada0"
BLOBS = {
    "pair_trading.py": "65e7c6dd3b8d62067704ad2148082392bbc17814",
    "config.json": "efbb698bc1072356051fcbc669943fddf1b3a6b7",
    "backtest.py": "48bcb2417fb3798349df9be97244ddb829e19121",
}
START_MONTH = (2023, 9)
END_MONTH_EXCLUSIVE = (2026, 1)
FIRST_EVAL = "2024-01-01"
LAST_EVAL = "2025-12-31"


def git_blob_sha(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(b"blob " + str(len(data)).encode() + b"\0" + data)
    return h.hexdigest()


def download_bytes(url: str) -> bytes:
    if not url.startswith(("https://raw.githubusercontent.com/", "https://data.binance.vision/")):
        raise ValueError("Unapproved upstream")
    request = urllib.request.Request(url, headers={"User-Agent": "EMBER-A218-research-only"})
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read()


def pinned_sources(folder: Path) -> dict:
    evidence = {}
    for name, wanted in BLOBS.items():
        url = f"https://raw.githubusercontent.com/djienne/pair_trading_NEDL/{REMOTE_COMMIT}/{name}"
        data = download_bytes(url)
        actual = git_blob_sha(data)
        if actual != wanted:
            raise ValueError(f"Upstream blob SHA mismatch {name}: {actual}")
        (folder / name).write_bytes(data)
        evidence[name] = {"url": url, "git_blob_sha": actual, "sha256": hashlib.sha256(data).hexdigest()}
    return evidence


def months():
    y, m = START_MONTH
    while (y, m) < END_MONTH_EXCLUSIVE:
        yield y, m
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1


def millis(value: str) -> int:
    number = int(value)
    if number >= 10**15:
        number //= 1000
    if not 1500000000000 <= number < 1800000000000:
        raise ValueError("Invalid UTC market timestamp")
    return number


def genuine_daily_closes(symbol: str, manifest: dict) -> tuple[pd.Series, list[dict]]:
    output = []
    evidence = []
    for year, month in months():
        url = (f"https://data.binance.vision/data/futures/um/monthly/klines/"
               f"{symbol}/1d/{symbol}-1d-{year}-{month:02d}.zip")
        key = f"{symbol}/1d/{year}/{month}"
        expected = manifest["source_receipts"][key]
        if expected["url"] != url:
            raise ValueError("A217 real-data receipt URL mismatch")
        payload = download_bytes(url)
        zip_sha = hashlib.sha256(payload).hexdigest()
        if zip_sha != expected["zip_sha256"]:
            raise ValueError(f"Binance ZIP SHA mismatch {key}")
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            files = [x for x in archive.namelist() if x.endswith(".csv")]
            if len(files) != 1:
                raise ValueError(f"Expected exactly one CSV in {key}")
            raw = archive.read(files[0])
        csv_sha = hashlib.sha256(raw).hexdigest()
        if csv_sha != expected["csv_sha256"]:
            raise ValueError(f"Binance CSV SHA mismatch {key}")
        lines = list(csv.reader(io.StringIO(raw.decode("utf-8"))))
        if len(lines) != expected["raw_csv_lines"]:
            raise ValueError("Binance CSV line count mismatch")
        n = 0
        for row in lines:
            if not row or not row[0].isdigit():
                continue
            ts = millis(row[0])
            px = float(row[4])
            if not np.isfinite(px) or px <= 0:
                raise ValueError(f"Invalid futures price {key}")
            output.append((ts, px))
            n += 1
        if not n:
            raise ValueError(f"Empty futures monthly {key}")
        evidence.append({"key": key, "zip_sha256": zip_sha, "csv_sha256": csv_sha, "rows": n})
    output.sort()
    if len(set(t for t, _ in output)) != len(output):
        raise ValueError("Duplicate daily UTC timestamps")
    if any(t2 - t1 != 86_400_000 for (t1, _), (t2, _) in zip(output, output[1:])):
        raise ValueError("Incomplete futures daily grid")
    idx = pd.to_datetime([t for t, _ in output], unit="ms", utc=True)
    s = pd.Series([p for _, p in output], index=idx, dtype="float64")
    if s.index[0] != pd.Timestamp("2023-09-01", tz="UTC"):
        raise ValueError("Warmup start mismatch")
    if s.index[-1] != pd.Timestamp("2025-12-31", tz="UTC"):
        raise ValueError("End-of-test source mismatch")
    return s, evidence


def source_accounting_gates(source_text: str) -> dict:
    # The frozen source has price weights and delta-weight fees but no
    # futures ledger. These evidence predicates fail CLOSED if source differs.
    required = [
        "net_return = gross_return - self.config.transaction_fee * (",
        "abs(position0 - old_position0) + abs(position1 - old_position1)",
        "price0_next = df['price0'].iloc[t + 1]",
        "price1_next = df['price1'].iloc[t + 1]",
        "state.current_return = (1 + state.current_return) * (1 + gross_return) - 1",
        "for t in range(self.config.window, len(df) - 1)",
    ]
    for exact in required:
        if exact not in source_text:
            raise ValueError(f"Original source changed or expected accounting code missing: {exact[:80]}")
    # Not claims of source absence by arbitrary substring: these predicates
    # describe missing accounting in the original RETURNS LOOP only.
    body = source_text.split("    def run(\n", 1)[1].split("        return ", 1)[0]
    for suspicious in ("funding_rate", "mark_price", "maintenance_margin", "liquidation_price"):
        if suspicious in body:
            raise ValueError(f"Original accounting changed, manually reassess: {suspicious}")
    return {
        "commission_on_weight_delta_only": True,
        "daily_target_rebalance_fee_not_reconciled": True,
        "perpetual_funding_ledger": False,
        "mark_and_margin_liquidation_ledger": False,
        "terminal_two_leg_close_ledger": False,
        "post_close_executable_price_reconciliation": False,
    }


def run():
    mandate = json.loads((ROOT / "config/research_mandate.lock.json").read_text("utf-8"))
    assert mandate["state"] == "LOCKED_USER_ONLY"
    assert mandate["scope"] == "BINANCE_USDT_M_FUTURES"
    base = ROOT / "research/a217_trendrider_original/evidence/source_manifest.json"
    manifest = json.loads(base.read_text("utf-8"))
    with tempfile.TemporaryDirectory(prefix="ember-a218-original-") as tmp:
        folder = Path(tmp)
        sources = pinned_sources(folder)
        source_text = (folder / "pair_trading.py").read_text("utf-8")
        gates = source_accounting_gates(source_text)
        config = json.loads((folder / "config.json").read_text("utf-8"))
        frozen = config["strategy"]
        assert (frozen["window"], frozen["entry_threshold"], frozen["stop_loss_threshold"]) == (100, 0.02, -0.05)
        assert frozen["transaction_fee"] == 0.0001
        btc, btc_receipts = genuine_daily_closes("BTCUSDT", manifest)
        eth, eth_receipts = genuine_daily_closes("ETHUSDT", manifest)
        assert btc.index.equals(eth.index)
        spec = importlib.util.spec_from_file_location("original_a218", folder / "pair_trading.py")
        module = importlib.util.module_from_spec(spec)
        import sys
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        strat = module.PairTradingStrategy(module.StrategyConfig.from_dict(config))
        results = strat.run(btc, eth)
        actual = results.loc[(results.index >= FIRST_EVAL) & (results.index <= LAST_EVAL)]
        if len(actual) < 700 or not set(actual.signal.unique()).issubset({-1, 0, 1}):
            raise ValueError("Insufficient/invalid original signal results")
        expected_ledger_missing = all(
            (not gates[k] for k in (
                "perpetual_funding_ledger",
                "mark_and_margin_liquidation_ledger",
                "terminal_two_leg_close_ledger",
                "post_close_executable_price_reconciliation",
            ))
        )
        assert expected_ledger_missing
        receipt = {
            "status": "BLOCKED_SOURCE_EXECUTION_ACCOUNTING",
            "verified_futures_candidate": False,
            "profitability_claim": False,
            "source_commit": REMOTE_COMMIT,
            "pinned_sources": sources,
            "genuine_exchange": "Binance USDT-M Futures archived 1d klines",
            "source_market_type": "FUTURES_UM_NOT_SPOT",
            "original_config": frozen,
            "market_data_receipts": btc_receipts + eth_receipts,
            "matched_daily_utc_bars": len(btc),
            "audit_signal_rows_2024_2025": len(actual),
            "original_nonzero_signal_days_2024_2025": int((actual.signal != 0).sum()),
            "original_transitions_2024_2025": int(actual.signal.ne(actual.signal.shift(fill_value=0)).sum()),
            "original_return_metrics_omitted_intentionally": True,
            "accounting_gates": gates,
            "missing_essential_ledgers": [
                "two-leg funding settlement", "mark-to-market margin and liquidation",
                "daily rebalance actual turnover fees", "terminal forced closure",
                "post-signal executable fills", "stress execution costs",
            ],
            "no_orders": True,
            "note": "Original signal observations on genuine data only; no valid futures net PnL.",
        }
        target = HERE / "evidence" / "a218_original_preflight.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", "utf-8")
        print(json.dumps({
            "status": receipt["status"],
            "receipts": len(receipt["market_data_receipts"]),
            "utc_daily_bars": receipt["matched_daily_utc_bars"],
            "signal_rows": receipt["audit_signal_rows_2024_2025"],
            "nonzero_days": receipt["original_nonzero_signal_days_2024_2025"],
            "transitions": receipt["original_transitions_2024_2025"],
            "output": str(target),
        }))
        if any(x for x in (
            receipt["verified_futures_candidate"],
            receipt["profitability_claim"],
            receipt["status"] != "BLOCKED_SOURCE_EXECUTION_ACCOUNTING",
        )):
            raise AssertionError("Cannot promote unverified futures PnL")


if __name__ == "__main__":
    run()
