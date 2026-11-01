"""One-off evidence-first source-signal parity trace, isolated research branch.

This test does not execute orders, a strategy PnL backtest, or optimization.
Data is frozen real Binance USD-M closed OHLCV stored in the repository.
"""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_real_usdtm_native_signal_source_trace():
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q",
         "numpy>=1.26,<3", "pandas>=2.1,<3", "scipy>=1.11,<2", "requests>=2,<3"],
        check=True,
        timeout=180,
    )
    runner = (
        Path(__file__).resolve().parents[1]
        / "research" / "source_parity_trace_20261101" / "run_trace.py"
    )
    proc = subprocess.run(
        [sys.executable, str(runner)], capture_output=True, text=True, timeout=540,
    )
    lines = [line for line in proc.stdout.splitlines() if line.startswith("EMBER_PARITY_REPORT=")]
    if lines:
        report = json.loads(lines[-1].split("=", 1)[1])
        compact = {
            k: {
                "error": v.get("error"),
                "status": v.get("status", "PYTHON_CLASS_EXECUTED"),
                "n": v.get("n", v.get("n_rebalance_states", v.get("long_signals"))),
                "daily_counts": v.get("long_daily_decisions_by_symbol"),
                "sample": v.get("first20", v.get("native_signal_trace", []))[:2],
                "first20_match": v.get("first20_match_independent"),
            }
            for k, v in report["results"].items()
        }
        summary = json.dumps(compact, ensure_ascii=False)
    else:
        summary = proc.stdout[-1500:] + proc.stderr[-1500:]
    warnings.warn("Source signal trace SUMMARY: " + summary[:8000], stacklevel=1)
    assert proc.returncode == 0, proc.stdout[-15000:] + proc.stderr[-15000:]
    assert lines, "Runner did not emit a JSON report"
    assert all("error" not in v for v in report["results"].values()), summary
