"""Cross-venue identity and deterministic 5m->1m->1s TP1 audit."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_price_path_75_resolution_pinned_real_binance_all_bars_parity():
    p=(Path(__file__).resolve().parents[1]/"research"/
       "source_parity_trace_20261101"/"trace75_multires_resolution_20261101.py")
    done=subprocess.run([sys.executable,str(p)],capture_output=True,
                        text=True,timeout=240)
    assert done.returncode==0,done.stdout[-12000:]+done.stderr[-12000:]
    row=next((x for x in done.stdout.splitlines()
              if x.startswith("EMBER_TRACE75_FINE_RESULT=")),None)
    assert row is not None
    a=json.loads(row.split("=",1)[1])
    assert a["n_selected_from_experimental_model"]==75
    assert a["matched_bars_to_pinned_higher_resolution"]=={
        "H1_matched":1875,"5m_matched":44,"1m_matched":22,
        "extra_5m_matched":1}
    assert len(a["case_results"])==75
    assert a["counts"]["TP1_BE_SAME_SECOND_UNRESOLVED"]==8
    assert a["counts"].get("TP2_BE_SAME_BAR_UNRESOLVED",0)==0
    assert a["tp2_vs_be_counts"]["NO_PREKNOWN_TP2"]==5
    for q in a["case_results"]:
        assert q["tp1_first_touch_ms"] is not None
        assert q["tp1_first_touch_resolution"] in ("5m","1m","1s")
        assert q["certified_max_extension_beyond_TP1_before_BE_ATR"]>=0
        assert q["first_post_tp1_BE_ms"] is None or (
            q["first_post_tp1_BE_ms"]>q["tp1_first_touch_ms"])
        assert q["tp2_vs_BE_class"]!="TP2_BEFORE_BE" or (
            q["first_tp2_before_be_ms"] is not None)
    summary={k:v for k,v in a.items() if k!="case_results"}
    warnings.warn("EMBER_TRACE75_FINE_SUMMARY="+json.dumps(
        summary,ensure_ascii=False),stacklevel=1)

    detail=[{
        "id":q["id"],"symbol":q["symbol"],"direction":q["direction"],
        "tp1_at":q["tp1_first_touch_ms"],"entry":q["entry"],
        "tp1":q["tp1"],"tp2":q["tp2"],"atr":q["atr"],
        "be_at":q["first_post_tp1_BE_ms"],
        "be_resolution":q["be_time_resolution"],
        "tp2_before_be_at":q["first_tp2_before_be_ms"],
        "status":q["event_class"],"tp2_class":q["tp2_vs_BE_class"],
        "max_before_be_ATR":q[
            "certified_max_extension_beyond_TP1_before_BE_ATR"],
        "atr_thresholds":q["certified_atr_thresholds_before_BE"],
    } for q in a["case_results"]]
    warnings.warn("EMBER_TRACE75_FINE_CASES="+json.dumps(
        detail,ensure_ascii=False,separators=(",",":")),stacklevel=1)
