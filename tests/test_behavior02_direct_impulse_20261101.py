"""Secondary exploratory impulse research must report *all* 894 original seeds."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_secondary_direct_impulse_no_cherrypick_original_impulse_cohort():
    script=Path(__file__).resolve().parents[1]/"research"/(
        "one_behavior_study_20261101/behavior02_direct_impulse_20261101.py")
    p=subprocess.run([sys.executable,str(script)],capture_output=True,
                     text=True,timeout=240)
    assert p.returncode==0,p.stderr[-9000:]+p.stdout[-2000:]
    marker="EMBER_BEHAVIOR02_RESULT="
    line=next((x for x in p.stdout.splitlines() if x.startswith(marker)),None)
    assert line
    data=json.loads(line.split("=",1)[1])
    assert data["n_original_impulse_candidates"]==894
    assert len(data["all_impulse_events"])==894
    for x in data["all_impulse_events"]:
        assert x["signal_close_ms"]>=x["impulse_open_ms"]
        assert x["outcome"]["first_6bar_path_class"] in (
            "EXTRA_EXTENSION_BEFORE_HALF_BODY_RETRACE",
            "HALF_BODY_RETRACE_BEFORE_EXTRA_EXTENSION",
            "AMBIGUOUS_BOTH_IN_SAME_BAR",
            "NO_EXTENSION_OR_RETRACE_6","RIGHT_CENSORED")
        assert x["pre_signal_features"]["impulse_true_range_atr"]>=1.5
        assert x["pre_signal_features"][
            "close_clearance_over_prior20_level_ATR"]>0
    short={k:v for k,v in data.items() if k!="all_impulse_events"}
    warnings.warn("EMBER_BEHAVIOR02_SUMMARY="+json.dumps(
        short,ensure_ascii=False,separators=(",",":")),stacklevel=1)
    warnings.warn("EMBER_BEHAVIOR02_EVENTS="+json.dumps(
        data["all_impulse_events"],ensure_ascii=False,
        separators=(",",":")),stacklevel=1)
