"""Backward historical H4 confirmation on previously unseen real futures candles."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_unseen_2024_2025_h4_impulse_body_two_atr_confirmation():
    p=(Path(__file__).resolve().parents[1]/"research"/
       "one_behavior_study_20261101"/
       "behavior02_backward_confirm_20261101.py")
    proc=subprocess.run([sys.executable,str(p)],capture_output=True,
                        text=True,timeout=240)
    assert proc.returncode==0,proc.stderr[-12000:]+proc.stdout[-2000:]
    tag="EMBER_BEHAVIOR02_BACKWARD="
    line=next((x for x in proc.stdout.splitlines()
               if x.startswith(tag)),None)
    assert line
    out=json.loads(line.split("=",1)[1])
    assert set(out["daily_parity_old_H4_grouped_into_actual_D1_bars"])=={
        "BTCUSDT","ETHUSDT","SOLUSDT","STRKUSDT","ZKUSDT","LDOUSDT"}
    assert len(out["all_unseen_older_impulses"])==6
    assert all(x>300 for x in out[
        "daily_parity_old_H4_grouped_into_actual_D1_bars"].values())
    assert all(z["body_atr"]>0 for events in out[
        "all_unseen_older_impulses"].values() for z in events)
    assert all(g["OLD_UNSEEN_2024_2025"]["all"]["n"]>0
               for g in out["group_comparisons"].values())
    summary={k:v for k,v in out.items()
             if k!="all_unseen_older_impulses"}
    warnings.warn("EMBER_BEHAVIOR02_BACKWARD_SUMMARY="+json.dumps(
        summary,ensure_ascii=False,separators=(",",":")),stacklevel=1)
    warnings.warn("EMBER_BEHAVIOR02_BACKWARD_EVENTS="+json.dumps(
        out["all_unseen_older_impulses"],ensure_ascii=False,
        separators=(",",":")),stacklevel=1)
