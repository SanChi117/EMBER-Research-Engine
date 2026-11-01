"""Frozen genuine Binance USDT-M one-minute P07 chronology."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_source_p07_tp1_price_touch_then_be_on_one_minute_bars():
    p=Path(__file__).resolve().parents[1]/"research"/"source_parity_trace_20261101"/"p07_1m_be_resolution.py"
    r=subprocess.run([sys.executable,str(p)],capture_output=True,text=True,timeout=30)
    assert r.returncode==0,r.stdout+r.stderr
    line=[x for x in r.stdout.splitlines() if x.startswith("EMBER_P07_1M_RESOLUTION=")]
    assert len(line)==1
    obj=json.loads(line[0].split("=",1)[1])
    assert obj["status"]=="TP1_THEN_BE_PRICE_TOUCHED_UNAMBIGUOUS_ON_1M"
    assert obj["orders_filled_not_asserted"] is True
    assert [x["minute_open_ms"] for x in obj["events"]]==[1788267660000,1788268080000]
    warnings.warn("EMBER_P07_1M_RESOLUTION="+json.dumps(obj,ensure_ascii=False),stacklevel=1)
