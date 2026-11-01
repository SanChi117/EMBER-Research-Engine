"""Exact event/price/time parity of two original engines vs independent replay.

No real exchange orders; not a profitability or OOS test.
"""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_original_execution_ledger_with_real_funding():
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "numpy>=1.26,<3", "pandas>=2.1,<3", "scipy>=1.11,<2", "requests>=2,<3"], check=True, timeout=180)
    script=Path(__file__).resolve().parents[1]/"research"/"source_parity_trace_20261101"/"replay_execution.py"
    process=subprocess.run([sys.executable,str(script)],capture_output=True,text=True,timeout=350)
    assert process.returncode==0, (process.stdout[-3000:]+"\n"+process.stderr[-14000:])
    matches=[x for x in process.stdout.splitlines() if x.startswith("EMBER_EXECUTION_REPLAY=")]
    assert matches,"No explicit execution report from runner"
    report=json.loads(matches[-1].split("=",1)[1])
    small={"funding_sha256":report["funding_sha256"],
           "p07":{k:{"trades":v["trades"],
                     "source_event_parity":v["native_trade_event_parity"],
                     "extra_source_exit_fees":v["native_duplicate_exit_fees_usd"],
                     "signed_funding":v["corrected_actual_signed_funding"]["funding_usd"],
                     "corrected_net_usd":v["corrected_actual_signed_funding"]["net_usd"]}
                   for k,v in report["p07"].items()},
           "p10":{k:v for k,v in report["p10"].items() if k not in
                  {"first20_original_trades","same_vs_next_first5_diffs"}}}
    warnings.warn("EMBER_EXECUTION_REPLAY_SUMMARY="+json.dumps(small,ensure_ascii=False),stacklevel=1)
    warnings.warn("P10_ENTRY_STRESS_DIFFS="+json.dumps(report["p10"]["same_vs_next_first5_diffs"][:5],ensure_ascii=False),stacklevel=1)
    assert report["p10"]["all_trade_events_equal_independent"]
    assert all(v["native_trade_event_parity"] for v in report["p07"].values())
