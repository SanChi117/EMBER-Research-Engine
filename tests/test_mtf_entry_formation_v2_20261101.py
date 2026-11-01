"""D1 closed context + H4 origin -> H1 confirmation; no lower-TF leakage."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_entry_requires_prior_closed_h4_break_and_h1_retest():
    p=(Path(__file__).resolve().parents[1]/"research"/
       "source_parity_trace_20261101"/"mtf_entry_formation_v2_20261101.py")
    run=subprocess.run([sys.executable,str(p)],capture_output=True,
                       text=True,timeout=240)
    assert run.returncode==0,run.stderr[-10000:]+run.stdout[-3000:]
    key="EMBER_MTF_ENTRY_V2="
    text=next((s for s in run.stdout.splitlines() if s.startswith(key)),None)
    assert text is not None
    data=json.loads(text.split("=",1)[1])
    assert data["scope"]=="MTF_V2_D1_CONTEXT_H4_FORMATION_H1_RETEST_NO_15M_DATA"
    assert sum(x["H1_closed_bars"] for x in data["symbol_counts"].values())==4497
    for z in data["all_H4_originated_events"]:
        assert z["do_not_use_5m_for_generation"] if (
            z["outcome"]!="H4_BREAK_IGNORED_EXISTING_PENDING") else True
        if z["outcome"]=="H1_RETEST_HOLD_ENTRY_CANDIDATE":
            br=z["break"]
            assert br["break_close_ms"]<z["confirmation_H1_close_ms"]
            assert br["source_prior_12_closed_h4_end_ms"]<br["break_close_ms"]
            assert z["why_entry"].startswith("4H_RANGE_BREAK_KNOWN")
            assert z["structure_location"]["range_H4_high_before_break"]>=(
                z["structure_location"]["range_H4_low_before_break"])
            d1=z["d1_at_confirmation"]
            if d1["status"]=="D1_AS_OF_SNAPSHOT":
                assert d1["last_closed_d1_end"]<=z["confirmation_H1_close_ms"]
    compact={k:v for k,v in data.items()
             if k!="all_H4_originated_events"}
    warnings.warn("EMBER_MTF_ENTRY_V2_SUMMARY="+json.dumps(
        compact,ensure_ascii=False),stacklevel=1)

    warnings.warn("EMBER_MTF_ENTRY_V2_RECORDS="+json.dumps(
        data["all_H4_originated_events"],ensure_ascii=False,
        separators=(",",":")),stacklevel=1)
