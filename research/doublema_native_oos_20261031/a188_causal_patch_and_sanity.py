#!/usr/bin/env python3
"""A188: one-line causal data boundary correction, source-pinned and fail-closed.
Test copy ONLY. Do not modify or deploy author's source or live trading.
"""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import pandas as pd

SOURCE_BLOB="22ca6588bbd056e671783f676f1a4010cbfc1bb6"
OLD='return dataframe.loc[dates <= candle_time]'
NEW='return dataframe.loc[dates < candle_time.floor("h")]'

def load_class(path: Path, module_name: str):
    spec=importlib.util.spec_from_file_location(module_name, path)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.VideoDoubleMaFuturesStrategy

def main(original: Path, patched: Path):
    data=original.read_bytes()
    sha=hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()
    assert sha==SOURCE_BLOB, f"UPSTREAM_BLOB_CHANGED:{sha}"
    code=data.decode("utf-8")
    assert code.count(OLD)==1, "EXPECTED_EXACTLY_ONE_CALLBACK_BOUNDARY"
    assert code.count(NEW)==0, "SOURCE_ALREADY_PATCHED"
    patched.parent.mkdir(parents=True,exist_ok=True)
    patched.write_text(code.replace(OLD,NEW),encoding="utf-8")
    A=load_class(original, "dma_author_a188")
    B=load_class(patched, "dma_causal_a188")
    df=pd.DataFrame({
        "date":pd.to_datetime(["2026-07-10T05:00:00Z","2026-07-10T06:00:00Z"],utc=True),
        "close":[3000.0,3900.0],
        "high":[3010.0,4010.0],
        "low":[2990.0,2700.0],
        "atr_14":[20.0,300.0],
        "cluster_zone_low":[2990.0,2600.0],
    })
    now=pd.Timestamp("2026-07-10T06:00:00Z").to_pydatetime()
    full_original=A._candles_until(df,now)
    live_observed=A._candles_until(df.iloc[:-1],now)
    full_fixed=B._candles_until(df,now)
    assert len(full_original)==2 and len(live_observed)==1 and len(full_fixed)==1
    assert full_fixed.iloc[-1]["date"]==live_observed.iloc[-1]["date"]
    tr=SimpleNamespace(open_date_utc=now)
    a=A._entry_candle(full_original,tr)
    b=B._entry_candle(full_fixed,tr)
    assert a["date"]==df.iloc[1]["date"] and b["date"]==df.iloc[0]["date"]
    assert a["atr_14"]!=b["atr_14"]
    assert len(B._candles_until(df, pd.Timestamp("2026-07-10T06:59:59Z").to_pydatetime()))==1
    assert len(B._candles_until(df, pd.Timestamp("2026-07-10T07:00:00Z").to_pydatetime()))==2
    print("A188_CAUSALITY_BREACH_REPRODUCED_AND_ONE_LINE_BOUNDARY_FIX_SANITY_PASS")
    print("original_btest_open_06_candle=06:00, original_live=05:00, causal_btest=05:00")
    print("author_upstream_blob="+sha)

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: a188_causal_patch_and_sanity.py original.py patched.py")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
