"""A223 independent source-only causality falsification of a published BTC perp PA hybrid.

No market orders, trading connections, PnL, edits to original, synthetic prices
only to expose chronology invariant. Does not imply that the live deployment
code shares the research backtest's bug.
"""
from __future__ import annotations

import ast
import hashlib
import json
from bisect import bisect_left, bisect_right
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
REPO = "denniskid2520/btcusdt-research-archive"
COMMIT = "66410a708fe5c4ff0d2762fbe764cc25b51ae7e3"
ORIGINAL = "src/research/strategy_c_v2_execution_layer.py"
SHA = "c90f162d8cddca544d7e8b604eee7682398f24a4"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()


def extract_original_function(data: str, name: str, globals_dict: dict):
    tree = ast.parse(data)
    matches = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(matches) != 1:
        raise AssertionError(f"Pinned original method not found exactly once: {name}")
    # Re-run original function AST unchanged; postpone evaluating type hints.
    only = ast.Module(
        body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), matches[0]],
        type_ignores=[],
    )
    ast.fix_missing_locations(only)
    exec(compile(only, f"<ORIGINAL {name}>", "exec"), globals_dict)
    return globals_dict[name]


def check():
    url = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{ORIGINAL}"
    with urlopen(url, timeout=35) as response:
        original = response.read()
    sha = git_blob_sha(original)
    if sha != SHA:
        raise AssertionError(f"Original author source changed: {sha}")
    source = original.decode("utf-8")
    # Source invariant relevant to original reports:
    required = [
        "bars_4h[zone_start_idx].timestamp",
        "lo = bisect_left(ts_list, zone_start_ts)",
        "entries.append((i, \"base\"))",
        "signals_exec[idx] = 1",
    ]
    if not all(s in source for s in required):
        raise AssertionError("Original source code drift; re-audit manually")

    # Mock RSI output only. This test isolates TIMESTAMP availability; it does
    # not pretend to simulate a real historical market or a profitable strategy.
    def rsi_series(closes, window):
        assert window == 20 and len(closes) == 32
        return [None] * 25 + [75.0] * 7

    env = {
        "rsi_series": rsi_series,
        "timedelta": timedelta,
        "bisect_left": bisect_left,
        "bisect_right": bisect_right,
    }
    find_zones = extract_original_function(source, "_identify_regime_zones", env)
    gen_entries = extract_original_function(source, "_generate_signals_in_zone", env)

    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bars_4h = [SimpleNamespace(timestamp=start + timedelta(hours=4 * i)) for i in range(32)]
    feats = [SimpleNamespace(close=float(100+i)) for i in range(32)]
    zones = find_zones(bars_4h, feats)
    if not zones:
        raise AssertionError("No zones emitted by original function")
    first = zones[0]
    zone_start, zone_end, idx, _ = first
    assert idx == 25
    assert zone_start == bars_4h[25].timestamp

    # The 4h RSI uses close of the 4h bar; that close cannot be known until +4h.
    four_hour_regime_known = zone_start + timedelta(hours=4)
    hourly = [
        SimpleNamespace(timestamp=zone_start + timedelta(hours=i),
                        close=100.0, high=100.1, low=99.9)
        for i in range(15)
    ]
    config = SimpleNamespace(
        hold_exec_bars=24,
        max_entries_per_zone=6,
        cooldown_bars=0,
        entry_type="hybrid",
        pullback_pct=0.0075,
        breakout_pct=0.0025,
    )
    original_entries = gen_entries(hourly, zone_start, zone_end, config)
    assert original_entries and original_entries[0] == (0, "base")

    # Original paper engine reads 1h signal at close of bar 0 and fills
    # at open bar 1: 1 hour after 4h bar OPENS, 3 hours before it CLOSES.
    fill_at = hourly[1].timestamp
    delta = (four_hour_regime_known - fill_at).total_seconds() / 3600
    if delta <= 0:
        raise AssertionError("A223 test is not detecting anticipation")
    evidence = {
        "source_repo": REPO,
        "original_commit": COMMIT,
        "source_path": ORIGINAL,
        "pinned_original_blob_sha": SHA,
        "original_byte_sha256": hashlib.sha256(original).hexdigest(),
        "status": "SOURCE_CAUSALITY_BLOCKED_PREMATURE_4H_REGIME_START",
        "test_kind": "adversarial_synthetic_chronology_not_market_PnL",
        "original_function_bodies_used": ["_identify_regime_zones", "_generate_signals_in_zone"],
        "source_logic": {
            "signal_based_on_4h_close": True,
            "zone_start_uses_4h_bar_open_time": True,
            "original_1h_entry_eligible_from_zone_start": True,
            "backtester_next_bar_open_fill": True,
        },
        "synthetic_example": {
            "4h_open": zone_start.isoformat(),
            "earliest_original_fill": fill_at.isoformat(),
            "4h_close_data_known_at": four_hour_regime_known.isoformat(),
            "earliness_hours": delta,
        },
        "caveat": "This demonstrates the source research execution-layer backtest gate; it does NOT establish the live paper runner uses the same bug or quantify actual affected trades.",
        "future_precommit": "Do not cite 6-year author OOS as untouched/causal until corrected baseline is independently rerun without tuning and reconciled to production source.",
        "edge_verified": False,
        "orders_created": False,
    }
    out = HERE / "evidence" / "A223_D1_4H_REGIME_TIMESTAMP_SOURCE_GUARD.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": evidence["status"], "hours_premature": delta, "source_sha": sha}))


if __name__ == "__main__":
    check()
