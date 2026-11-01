"""Independent reproducible TP1 follow-through tracker; count price, not profits."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_all_75_tp1_first_price_paths_after_first_touch_bar():
    p=(Path(__file__).resolve().parents[1]/"research"/
       "source_parity_trace_20261101"/"trace75_tp1_followthrough_20261101.py")
    x=subprocess.run([sys.executable,str(p)],capture_output=True,text=True,timeout=240)
    assert x.returncode==0,x.stdout[-10000:]+x.stderr[-10000:]
    a=[z for z in x.stdout.splitlines() if z.startswith("EMBER_TRACE75=")]
    assert len(a)==1
    r=json.loads(a[0].split("=",1)[1])
    assert r["original_120_scenarios"]==120
    assert r["selected_75_TP1_FIRST"]==75
    assert len(r["individual_75_price_traces"])==75
    assert r["aggregate"]["cases"]==75
    assert sum(x["cases"] for x in r["by_symbol"].values())==75
    assert r["by_P10_volatility_label"]["yes"]["cases"]==17
    assert r["by_P10_volatility_label"]["no"]["cases"]==58
    for card in r["individual_75_price_traces"]:
        assert card["TP1_level_preknown"]>0
        assert card["ATR14_at_signal"]>0
        assert card["followup_available_H1_bars"]>=0
        assert card["TP1_first_touch_index"]>card["signal_i"]
    for summary in [r["aggregate"],*r["by_symbol"].values()]:
        for w in summary["windows"].values():
            assert w["extended_ge_two_ATR"]<=w["extended_ge_one_ATR"]
            assert w["extended_ge_one_ATR"]<=w["extended_ge_half_ATR"]
            assert w["extended_ge_half_ATR"]<=w["extended_ge_quarter_ATR"]
            assert w["extended_ge_quarter_ATR"]<=w["extended_beyond_TP1_on_later_H1"]
            assert w["extended_beyond_TP1_on_later_H1"]<=w["complete"]
    compact={k:v for k,v in r.items() if k!="individual_75_price_traces"}
    warnings.warn("EMBER_TRACE75_SUMMARY="+json.dumps(compact,ensure_ascii=False),
                  stacklevel=1)
