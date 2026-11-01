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

    export_rows=[]
    for item in r["individual_75_price_traces"]:
        output={
            "symbol":item["symbol"],"direction":item["direction"],
            "signal_close_ms":item["signal_close_ms"],
            "tp1_first_touch_ms":item["TP1_first_touch_H1_open_ms"],
            "entry":item["entry_observed_next_H1_open"],
            "tp1":item["TP1_level_preknown"],
            "original_sl_proxy":item["initial_SL_wick_ATR_proxy"],
            "atr":item["ATR14_at_signal"],
            "tp2":item["TP2_preknown"],
            "first_tp1_bar_closed_beyond":item["TP1_first_bar_close_beyond"],
            "entry_revisit_same_tp1_h1_ambiguous":item[
                "TP1_first_bar_entry_revisit_ambiguous"],
            "conditional_runner_status":item["runner_BE_counterfactual"],
        }
        for horizon in ("1","3","6","12","24","72"):
            w=item["post_first_TP1_hour_windows"][horizon]
            output["next_"+horizon+"h_max_extension_ATR"]=(
                w["extension_in_ATR"] if w is not None else None)
            output["next_"+horizon+"h_returned_to_entry"]=(
                w["revisited_entry_at_any_point"] if w is not None else None)
        export_rows.append(output)
    warnings.warn("EMBER_TRACE75_CSV_ROWS="+json.dumps(
        export_rows,ensure_ascii=False,separators=(",",":")),stacklevel=1)
