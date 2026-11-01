"""Optional BE must remain separate, ambiguous bars not awarded as wins."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_optional_be_counterfactual_only_after_unambiguous_tp1():
    p=(Path(__file__).resolve().parents[1]/"research"/
       "source_parity_trace_20261101"/"optional_be_counterfactual_20261101.py")
    r=subprocess.run([sys.executable,str(p)],capture_output=True,text=True,timeout=240)
    assert r.returncode==0,r.stdout[-9000:]+r.stderr[-9000:]
    lines=[l for l in r.stdout.splitlines() if l.startswith("EMBER_OPTIONAL_BE_RESULT=")]
    assert len(lines)==1
    x=json.loads(lines[0].split("=",1)[1])
    assert x["all_early_entries"]==120
    assert x["clear_TP1_first"]==75
    assert x["TP1_first_with_preknown_further_H1_TP2"]+x["TP1_first_without_preknown_H1_TP2"]==75
    assert sum(x["BE_scenario_touch_outcomes"].values())==x["TP1_first_with_preknown_further_H1_TP2"]
    assert sum(x["no_BE_scenario_touch_outcomes"].values())==x["TP1_first_with_preknown_further_H1_TP2"]
    assert x["status"].startswith("OPTIONAL_")
    summary={k:v for k,v in x.items() if k!="records"}
    warnings.warn("EMBER_OPTIONAL_BE_SUMMARY="+json.dumps(summary,ensure_ascii=False),
                  stacklevel=1)
