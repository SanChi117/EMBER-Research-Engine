"""120 candidate setups; ex-ante first target geometry and 8 second-bar audit."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_no_cherry_picking_and_ambiguous_first_second_correctness():
    file=(Path(__file__).resolve().parents[1]/"research"/
          "source_parity_trace_20261101"/"formation_quality_audit_20261101.py")
    out=subprocess.run([sys.executable,str(file)],capture_output=True,
                       text=True,timeout=240)
    assert out.returncode==0,out.stdout[-8000:]+out.stderr[-8000:]
    marker="EMBER_SETUP_QUALITY="
    line=next((x for x in out.stdout.splitlines() if x.startswith(marker)),None)
    assert line is not None
    result=json.loads(line.split("=",1)[1])
    assert result["base_candidate_events"]==120
    assert result["events_with_H1_TP1"]==113
    assert result["all_75_winner_paths_not_rewritten"]==75
    assert len(result["individual_120_formation_cards"])==120
    assert len(result["one_second_price_path_8_ambiguous"])==8
    assert sum(x["second_open_equals_entry"] for x in result[
        "one_second_price_path_8_ambiguous"])==3
    assert all(x["distance_entry_TP1_pct"]<.1 for x in result[
        "one_second_price_path_8_ambiguous"])
    assert all(x["first_pivot_confirmed_at"]<=x["signal_i"]
               for x in result["individual_120_formation_cards"]
               if x["first_pivot_confirmed_at"] is not None)
    assert all(x["candidate_structural_pivot_confirmed_at"]<=x["signal_i"]
               for x in result["individual_120_formation_cards"]
               if x["candidate_structural_pivot_confirmed_at"] is not None)
    compact={k:v for k,v in result.items()
             if k not in ("individual_120_formation_cards",
                          "one_second_price_path_8_ambiguous")}
    warnings.warn("EMBER_SETUP_QUALITY_SUMMARY="+json.dumps(
        compact,ensure_ascii=False),stacklevel=1)
    warnings.warn("EMBER_SETUP_QUALITY_EIGHT="+json.dumps(result[
        "one_second_price_path_8_ambiguous"],ensure_ascii=False),stacklevel=1)
