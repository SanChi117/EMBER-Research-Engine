"""One-off evidence-first source-signal parity trace, isolated research branch.

This test does not execute orders, a strategy PnL backtest, or optimization.
Data is frozen real Binance USD-M closed OHLCV stored in the repository.
"""
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
    summary = lines[-1] if lines else (proc.stdout[-1500:] + proc.stderr[-1500:])
    warnings.warn("Source signal trace (see repo JSON/report): " + summary[:3500], stacklevel=1)
    assert proc.returncode == 0, proc.stdout[-15000:] + proc.stderr[-15000:]
