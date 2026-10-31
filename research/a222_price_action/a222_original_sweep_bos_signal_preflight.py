"""A222 Price Action: original sweep-BOS causal signal audit, REAL Binance USD-M.

No orders, no simulated profit, no changes to original strategy.
"""
import hashlib
import importlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/a221_wide_futures_screen"))
import a221_tsmom_genuine_futures as binance_source  # noqa: E402

SHA = "823f81c93afe82e704f4e40d4c6f3744db2790b4"
FILES = {
    "config.py": "4de45902752b815e28332aca8bcf6f59e3fbb5f6",
    "src/indicators.py": "c6517e5b7ce1e48c4eafb4e6d363b4eca28998c0",
    "src/strategy.py": "a47e25730bd4e161cbb53d023b3fe99ce51568cb",
    "src/backtester.py": "968f364db6bc4d04b01b6e549f68ad90a62d802e",
}


def fetch_original(folder):
    receipts = []
    for filename, expected in FILES.items():
        url = f"https://raw.githubusercontent.com/hroussel18/Revelio_Improved_Strategy/{SHA}/{filename}"
        data = binance_source.fetch(url)
        if binance_source.blob_sha(data) != expected:
            raise ValueError(f"Original git blob changed: {filename}")
        path = folder / filename
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_bytes(data)
        receipts.append({"file": filename, "git_blob": expected,
                         "sha256": hashlib.sha256(data).hexdigest()})
    (folder / "src/__init__.py").write_text("")
    return receipts


def generate(strat, cfg, candles):
    return strat.generate_signals(candles, cfg.DEFAULT_STRATEGY,
                                  use_session_filter=False,
                                  direction="both", htf_bias=None)


def run():
    mandate = json.loads((ROOT / "config/research_mandate.lock.json").read_text())
    assert mandate["scope"] == "BINANCE_USDT_M_FUTURES"
    assert mandate["state"] == "LOCKED_USER_ONLY"
    manifest = json.loads(
        (ROOT / "research/a217_trendrider_original/evidence/source_manifest.json").read_text()
    )
    with tempfile.TemporaryDirectory(prefix="a222-price-action-original-") as td:
        folder = Path(td)
        receipts = fetch_original(folder)
        sys.path.insert(0, td)
        cfg = importlib.import_module("config")
        strat = importlib.import_module("src.strategy")
        original = cfg.DEFAULT_STRATEGY
        assert original == {
            "pivot_lookback": 5,
            "max_bars_sweep_to_bos": 12,
            "require_close_back_inside": True,
            "min_sweep_atr": 0.0,
            "atr_period": 14,
        }, original
        asset = cfg.ASSETS["BTCUSD"]
        assert asset["timeframe"] == "1h"
        assert asset["direction"] == "both"
        assert asset["risk_per_trade"] == 0.02
        assert asset["exit"]["type"] == "trailing"
        assert not asset["use_session_filter"]
        assert not cfg.HTF_BIAS.get("enabled", False)
        candles, funding, binance_receipts = binance_source.load_all(manifest)
        frame = candles["BTCUSDT"]
        full = generate(strat, cfg, frame)
        probes = []
        for cut in ("2024-04-01", "2024-10-01", "2025-04-01",
                    "2025-10-01", "2026-04-01", "2026-09-01"):
            dt = pd.Timestamp(cut, tz="UTC")
            prefix = generate(strat, cfg, frame.loc[:dt])
            f = full.loc[full["entry_time"] <= dt,
                         ["entry_time", "direction", "sl_price"]]
            p = prefix[["entry_time", "direction", "sl_price"]]
            if len(f) != len(p):
                raise AssertionError(f"Future-dependent signal count at {cut}")
            if len(f) and (not np.array_equal(f["entry_time"].to_numpy(), p["entry_time"].to_numpy())
                           or not np.array_equal(f["direction"].to_numpy(), p["direction"].to_numpy())
                           or not np.allclose(f["sl_price"].to_numpy(), p["sl_price"].to_numpy())):
                raise AssertionError(f"Future-dependent original signal at {cut}")
            probes.append({"asof_utc": cut, "signals": len(p), "passed": True})
        stats = {}
        for name, start, end in (
            ("2024", "2024-01-01", "2025-01-01"),
            ("2025", "2025-01-01", "2026-01-01"),
            ("2026_JAN_SEP", "2026-01-01", "2026-10-01"),
        ):
            t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
            ss = full.loc[(full["entry_time"] >= t0) & (full["entry_time"] < t1)]
            stats[name] = {"original_raw_signals": len(ss),
                           "long": int((ss["direction"] == 1).sum()),
                           "short": int((ss["direction"] == -1).sum()),
                           "actual_btc_funding_prints": len(funding["BTCUSDT"].loc[t0:t1])}
        receipt = {
            "cycle": "A222",
            "status": "SOURCE_CAUSALITY_AND_REAL_FUTURES_SIGNALS_ONLY",
            "verified_futures_candidate": False,
            "original_sha": SHA, "original_files": receipts,
            "genuine_binance_usdm_zip_verified": len(binance_receipts),
            "genuine_price_symbol": "BTCUSDT", "genuine_funding_available": True,
            "original_asset_config_key": "BTCUSD",
            "causal_prefix_tests": probes,
            "periods": stats,
            "execution_and_economic_status": "BLOCKED_PENDING_NEXT_OPEN_REAL_FUNDING_FEES_RISK_LEDGER",
            "author_same_candle_close_fills_not_accepted": True,
            "PnL_claim": False, "actual_orders": False
        }
        path = ROOT / "research/a222_price_action/evidence/A222_ORIGINAL_SWEEP_BOS_SOURCE_CAUSALITY.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n")
        print(json.dumps({"verdict": receipt["status"],
                          "zip_verified": len(binance_receipts),
                          "prefix_probes_pass": len(probes),
                          "year_signal_counts": stats}, ensure_ascii=False))


if __name__ == "__main__":
    run()
