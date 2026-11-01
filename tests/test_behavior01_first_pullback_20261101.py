"""Preregistered behavior discovery on real frozen Binance USD-M prices."""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_preregistered_impulse_first_pullback_all_assets_all_timeframes():
    script=Path(__file__).resolve().parents[1]/"research"/(
        "one_behavior_study_20261101/behavior01_first_pullback_20261101.py")
    p=subprocess.run([sys.executable,str(script)],capture_output=True,
                     text=True,timeout=240)
    assert p.returncode==0,p.stderr[-10000:]+p.stdout[-1500:]
    tag="EMBER_BEHAVIOR01_RESULT="
    line=next((x for x in p.stdout.splitlines() if x.startswith(tag)),None)
    assert line
    result=json.loads(line.split("=",1)[1])
    assert len(result["universes"]["CORE"])==3
    assert len(result["universes"]["ALT_COMPARATOR"])==3
    assert set(result["H4_H1_cross_venue_exact_OHLCV_parity"])=={
        "BTCUSDT","ETHUSDT","SOLUSDT","STRKUSDT","ZKUSDT","LDOUSDT"}
    assert result["total_impulses"]>=result["total_qualifying_first_pullbacks"]
    assert len(result["all_qualifying_events"])==(
        result["total_qualifying_first_pullbacks"])
    for e in result["all_qualifying_events"]:
        assert e["impulse_close_ms"]<e["signal_close_ms"]
        assert .35<=e["pre_entry_features"]["pullback_depth_ATR"]<=1.50
        assert e["pre_entry_features"]["time_to_first_pullback_bars"] in range(1,7)
        assert e["price_path"]["status"] in (
            "CONTINUATION_BEFORE_INVALIDATION",
            "INVALIDATION_BEFORE_CONTINUATION","AMBIGUOUS_SAME_BAR",
            "TIME_CENSORED_12","RIGHT_CENSORED_FUTURE",
            "CENSORED_NO_NEXT_OPEN")
    compact={k:v for k,v in result.items() if k!="all_qualifying_events"}
    warnings.warn("EMBER_BEHAVIOR01_SUMMARY="+json.dumps(
        compact,ensure_ascii=False,separators=(",",":")),stacklevel=1)
    warnings.warn("EMBER_BEHAVIOR01_EVENTS="+json.dumps(
        result["all_qualifying_events"],ensure_ascii=False,
        separators=(",",":")),stacklevel=1)
