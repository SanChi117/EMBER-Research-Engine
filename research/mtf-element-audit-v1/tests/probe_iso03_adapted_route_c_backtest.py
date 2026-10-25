#!/usr/bin/env python3
"""ISO03 original-3m adapted paper replay; never sends orders."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "d05"))
sys.path.insert(0, str(ROOT / "tests"))
from iso03_adapted_route_c_backtest import (
    BacktestConfig, canonical_bytes, load_binance_daily_zips, run_backtest, signals_from_iso01,
)
from probe_iso01_frozen_c56_parent_state_registry import run as run_iso01


def summarize(result):
    return {"metrics": result["metrics"], "exit_reasons": dict(sorted(Counter(
        t["exit_reason"] for t in result["trades_detail"]).items()))}


def run(data_dir, out=None):
    data_dir = Path(data_dir)
    bars, manifest = load_binance_daily_zips(data_dir)
    iso01 = run_iso01()
    signals = signals_from_iso01(iso01)
    configurations = {
        "base_adapted": BacktestConfig(),
        "zero_cost_control": BacktestConfig(fee_rate=0, slippage_rate=0),
        "fees_without_slippage_control": BacktestConfig(slippage_rate=0),
    }
    results = {name: run_backtest(bars, signals, config) for name, config in configurations.items()}
    base = results["base_adapted"]
    encoded = canonical_bytes(base)
    repeat = canonical_bytes(run_backtest(bars, signals, BacktestConfig()))
    assert encoded == repeat
    accounting_delta = base["metrics"]["net_pnl"] - math.fsum(t["net_pnl"] for t in base["trades_detail"])
    assert abs(accounting_delta) < 1e-6
    assert all(t["entry_ms"] >= t["signal_known_ms"] for t in base["trades_detail"])
    assert base["equity_curve"][-1]["open_positions"] == 0
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    witness = {
        "schema": "EMBER_ISO03_ADAPTED_ROUTE_C_BACKTEST_WITNESS_V1",
        "mode": "ADAPTED_RESEARCH_NOT_AUTHOR_STRATEGY",
        "source_archives": len(manifest), "source_symbols": len(bars),
        "source_native3m_bars": sum(map(len, bars.values())),
        "source_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "signals": len(signals), "results": {name: summarize(r) for name, r in results.items()},
        "base_result_bytes": len(encoded), "base_result_sha256": hashlib.sha256(encoded).hexdigest(),
        "repeat_byte_identical": True, "accounting_delta": accounting_delta,
        "future_entries": 0, "open_positions_at_end": 0,
        "funding_included": False, "liquidation_model": False,
        "out_of_sample": False, "parameter_optimization": False,
        "author_strategy_certified": False, "readiness": "NOT_TRADE_READY", "orders_live": 0,
        "limitation": "One 32-day adapted mechanical experiment, not author validation, OOS evidence or expected-profit claim. Controls change equity-dependent sizing and are not paired-trade counterfactuals.",
    }
    if out:
        target = Path(out); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(encoded)
    print(json.dumps(witness, ensure_ascii=False, sort_keys=True, indent=2))
    return results, witness


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: probe_iso03...py DATA_DIR [FULL_RESULT_JSON]")
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
