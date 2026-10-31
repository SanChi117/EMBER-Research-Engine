#!/usr/bin/env python3
"""A201 causal-prefix audit, running unchanged author strategy classes.
Compare signals available on each historic candle to the same candle
after appending 100s of *future* candles. No simulated PnL.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd

PINS = {
    "momentum_wick": "1377a5bbf454252ca835cca3056787ac8ed73c04",
    "momentum_rsi": "3f839276f661f242a30e4dd1aa0b739459e7d65b",
}
def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def sample(n: int = 800) -> pd.DataFrame:
    t = np.arange(n, dtype=float)
    # Alternating trends produce hundreds of test signals for the original wick family.
    delta = 0.35 * np.sin(t / 7.) + 0.08 * np.cos(t / 2.3)
    close = 100 + np.cumsum(delta)
    open_ = close - delta
    return pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=n, freq="5min", tz="UTC"),
        "open": open_,
        "high": np.maximum(open_, close) + .012,
        "low": np.minimum(open_, close) - .012,
        "close": close,
        "volume": np.full(n, 1000.),
    })

def get_class(repo: Path, strategy: str):
    path = repo / "strategies" / "momentum" / (strategy + ".py")
    data = path.read_bytes()
    assert blob_sha(data) == PINS[strategy], (strategy, "SOURCE_BYTES_DIFFER")
    spec = importlib.util.spec_from_file_location("a201_author_" + strategy, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, strategy), blob_sha(data)

def make_signals(cls, candles: pd.DataFrame):
    # Original populate_* functions use no instance config or mutable data-provider.
    strategy = cls.__new__(cls)
    df = strategy.populate_indicators(candles.copy(), {"pair": "SOL/USDT:USDT"})
    df = strategy.populate_entry_trend(df, {"pair": "SOL/USDT:USDT"})
    def col(k):
        if k not in df:
            return np.zeros(len(df), dtype=np.int64)
        values = df[k].fillna(0).to_numpy()
        assert np.isfinite(values.astype(float)).all(), (k, "NONFINITE_SIGNAL")
        return values.astype(np.int64)
    result = np.column_stack((col("enter_long"), col("enter_short")))
    assert np.isin(result, [0, 1]).all()
    assert not np.any((result[:, 0] == 1) & (result[:, 1] == 1))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-repo",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    root=Path(a.original_repo)
    candles=sample()
    results={}
    for name in PINS:
        cls,sha=get_class(root,name)
        all_signals=make_signals(cls,candles)
        for length in (210,257,347,533,680):
            # No post-signal data may change any earlier historical entry.
            past=make_signals(cls,candles.iloc[:length].copy())
            assert np.array_equal(past,all_signals[:length]), (
                name,"FUTURE_DATA_ALTERS_PAST",length,
                np.flatnonzero(np.any(past!=all_signals[:length],axis=1))[:10].tolist())
        longs=int(all_signals[:,0].sum()); shorts=int(all_signals[:,1].sum())
        assert longs+shorts>0,(name,"NO_TEST_SIGNAL")
        if name=="momentum_wick":
            assert longs>0 and shorts>0
        if name=="momentum_rsi":
            assert longs==0,(name,"LONG_ZERO_SOURCE_CONTRACT_VIOLATED")
            assert shorts>0
        results[name]={"git_blob":sha,"prefix_lengths":[210,257,347,533,680],
                       "synthetic_long_entries":longs,"synthetic_short_entries":shorts,
                       "historic_signals_unchanged_after_appending_future":True,
                       "NOT_EVIDENCE_OF_PROFIT":True}
        print("A201_CAUSAL_PREFIX_PASS",name,"long",longs,"short",shorts,flush=True)
    out=Path(a.output)
    out.mkdir(parents=True,exist_ok=True)
    (out/"A201_ORIGINAL_SIGNAL_CAUSAL_PREFIX_MACHINE.json").write_text(
        json.dumps({"schema":"A201_ORIGINAL_SOURCES_PREFIX_CONSISTENCY_ONLY",
                    "strategy_results":results,
                    "limitations":"Synthetic series verifies prefix-consistency of code only; not lookahead-analysis on exchange history, not profitability"},indent=2)+"\n")
    print("A201_BOTH_UNCHANGED_ORIGINAL_SOURCE_CAUSAL_PREFIX_AUDITS_PASS",flush=True)
if __name__=="__main__":
    main()
