"""Reproducible initial six-source-inspired exploratory acceptance experiment.

This test must not be treated as a profitable-strategy proof.
"""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_new_synthetic_early_entry_is_not_old_signal_overlap():
    p=(Path(__file__).resolve().parents[1]/"research"/
       "source_parity_trace_20261101"/"six_source_early_acceptance_20261101.py")
    r=subprocess.run([sys.executable,str(p)],capture_output=True,text=True,timeout=240)
    assert r.returncode==0,r.stdout[-9000:]+r.stderr[-9000:]
    lines=[x for x in r.stdout.splitlines()
           if x.startswith("EMBER_EARLY_FUSION_AUDIT=")]
    assert len(lines)==1
    data=json.loads(lines[0].split("=",1)[1])
    assert data["original_P07_signal_count"]==134
    assert data["original_P10_H1_signal_count"]==54
    assert data["novel_EARLY_ACCEPT_signal_count"]==120
    assert data["new_entry_earlier_than_P07"]==32
    assert data["source_P07_same_breakout_with_later_rebreak"]==76
    assert data["72h_price_touch_outcomes"]=={
        "INITIAL_SL_FIRST":29,"AMBIGUOUS_SAME_H1":9,
        "NO_EX_ANTE_H1_TP1":7,"TP1_FIRST":75}
    assert all(x["tp1_pivot_confirmed_i"]<=x["signal_i"]
               for x in data["all_experimental_entries"]
               if x["tp1_pivot_confirmed_i"] is not None)
    summary={k:v for k,v in data.items() if k!="all_experimental_entries"}
    warnings.warn("EMBER_EARLY_FUSION_SUMMARY="+json.dumps(summary,ensure_ascii=False),
                  stacklevel=1)
