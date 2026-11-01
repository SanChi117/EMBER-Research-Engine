"""Ex-ante frozen Binance USDT-M 3-target geometry for one original P06 signal.

No PnL, financial assumptions, real/virtual orders or backtest tuning.
"""
import json
import subprocess
import sys
from pathlib import Path


def test_p06_third_target_and_be_transition_are_preknown():
    script = Path(__file__).resolve().parents[1] / "research" / "source_parity_trace_20261101" / "p06_three_tp_plan.py"
    proc = subprocess.run([sys.executable,str(script)],capture_output=True,text=True,timeout=30)
    assert proc.returncode == 0,proc.stdout + proc.stderr
    receipt = [line for line in proc.stdout.splitlines() if line.startswith("EMBER_P06_STRUCTURAL_LADDER=")]
    assert len(receipt)==1
    plan=json.loads(receipt[0].split("=",1)[1])
    assert plan["original_code_unmodified"]
    assert [x["price"] for x in plan["targets"]]==[86365.5,86699.9,87247.3]
    assert all(x["known_at_signal"] for x in plan["targets"])
    assert plan["initial_structural_SL_hypothesis"]==84820.7
    assert plan["management_state_machine"][1]["event"]=="TP1_PARTIAL_FILL_CONFIRMED"
    assert plan["management_state_machine"][1]["new_stop_price"]==86205.2
    print("P06_SOURCE_TARGET_LADDER="+json.dumps(plan["targets"],ensure_ascii=False))
