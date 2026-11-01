"""Frozen Binance 5m TP1-BE example consistency against 1h source data."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_frozen_five_minute_bar_sequence_for_three_source_setups():
    script=(Path(__file__).resolve().parents[1]/"research"/
            "source_parity_trace_20261101"/"three_tp_be_5m_examples.py")
    proc=subprocess.run([sys.executable,str(script)],capture_output=True,text=True,timeout=40)
    assert proc.returncode==0,proc.stdout[-12000:]+proc.stderr[-12000:]
    lines=[x for x in proc.stdout.splitlines() if x.startswith("EMBER_5M_TP1_BE=")]
    assert len(lines)==1
    r=json.loads(lines[0].split("=",1)[1])
    assert r["total_bars"]==2592
    assert r["72h_5m_bar_to_1h_alignment"].startswith("EXACT")
    assert r["source_data_Git_blob_sha"]=="e574a70d0ab2842bf9e22dd56d84ae952ab9bd27"
    assert r["examples"]["P06_BTC_20261002"]=={
        "status":"TP1_THEN_PRICE_LEVEL_BE_TOUCH_ON_LATER_5M",
        "tp1_bar_open_utc":"2026-10-02T09:40Z",
        "be_bar_open_utc":"2026-10-02T10:20Z",
    }
    warnings.warn("EMBER_5M_TP1_BE="+json.dumps(r,ensure_ascii=False),stacklevel=1)
