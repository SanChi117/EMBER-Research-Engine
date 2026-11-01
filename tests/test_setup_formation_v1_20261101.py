"""Causal H1/H4 TP1 live-level formation; new targets require new outcomes."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_120_six_source_labelled_setup_formation_uses_live_targets_only():
    f=(Path(__file__).resolve().parents[1]/"research"/
       "source_parity_trace_20261101"/"setup_formation_v1_20261101.py")
    done=subprocess.run([sys.executable,str(f)],capture_output=True,
                        text=True,timeout=240)
    assert done.returncode==0,done.stderr[-16000:]+done.stdout[-16000:]
    token="EMBER_SETUP_V1="
    txt=next((x for x in done.stdout.splitlines() if x.startswith(token)),None)
    assert txt
    j=json.loads(txt.split("=",1)[1])
    assert j["base_original_experimental_events"]==120
    assert len(j["all_120_formation_plans"])==120
    for row in j["all_120_formation_plans"]:
        assert row["breakout_level_prior20"]>0
        assert row["stop_retest_extremum_ATR_PROXY"]>0
        assert row["retest_close_beyond_level_ATR"]>0
        if row["first_active_target"]:
            pivot=row["first_active_target"]
            assert not pivot["previously_touched"]
            assert pivot["confirmed_at_ms"]<=row["signal_close_utc_ms"]
            assert pivot["timeframe"] in ("1h","4h")
        else:
            assert "NO_LIVE_CONFIRMED_H1_H4_DESTINATION" in row["reasons"]
    short={k:v for k,v in j.items() if k!="all_120_formation_plans"}
    warnings.warn("EMBER_SETUP_V1_SUMMARY="+json.dumps(
        short,ensure_ascii=False),stacklevel=1)
