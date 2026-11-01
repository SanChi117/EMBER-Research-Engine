"""Equal-distance control: do not misstate geometric asymmetry as edge."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_symmetric_1atr_4h_control_older_and_newer_6_future_pairs():
    p=Path(__file__).resolve().parents[1]/"research"/(
        "one_behavior_study_20261101/behavior02_symmetric_control_20261101.py")
    x=subprocess.run([sys.executable,str(p)],capture_output=True,
                     text=True,timeout=240)
    assert x.returncode==0,x.stderr[-8000:]+x.stdout[-1000:]
    tag="EMBER_BEHAVIOR02_SYMMETRIC="
    l=next((z for z in x.stdout.splitlines() if z.startswith(tag)),None)
    assert l
    out=json.loads(l.split("=",1)[1])
    assert out["total_impulse_events_checked"]==973
    assert len(out["complete_case_level_audit"])==973
    for q in out["complete_case_level_audit"]:
        assert q["symmetric"]["class"] in (
            "POS_1ATR_FIRST","NEG_1ATR_FIRST","SAME_BAR_UNKNOWN",
            "NEITHER_6","RIGHT_CENSORED")
        assert q["body_size_ATR"]>=0
        if q["symmetric"]["entry_ref"] is not None:
            center=q["symmetric"]["entry_ref"]
            plus=q["symmetric"]["positive_symmetric_marker"]
            minus=q["symmetric"]["negative_symmetric_marker"]
            assert abs(plus-center)>0
            assert abs(abs(plus-center)-abs(minus-center))<1e-7
    compact={k:v for k,v in out.items()
             if k!="complete_case_level_audit"}
    warnings.warn("EMBER_BEHAVIOR02_SYMMETRIC_SUMMARY="+json.dumps(
        compact,ensure_ascii=False,separators=(",",":")),stacklevel=1)
    warnings.warn("EMBER_BEHAVIOR02_SYMMETRIC_EVENTS="+json.dumps(
        out["complete_case_level_audit"],ensure_ascii=False,
        separators=(",",":")),stacklevel=1)
