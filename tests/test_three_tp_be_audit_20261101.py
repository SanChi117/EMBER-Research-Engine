"""Audit source-preserving 3TP + BE price-action paths on real USDT-M candles.

Cash/PnL/position sizing are not defined or tested.
"""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_original_p07_p10_p06_structural_three_targets_and_be():
    # P06 real TA-Lib is available as a wheel in CI py3.11+; original
    # Freqtrade full engine remains blocked. In py3.10 the known P06 timestamp
    # is explicitly pinned but NOT falsely called a reexecuted source class.
    needs = ["numpy>=1.26,<3", "pandas>=2.1,<3", "scipy>=1.11,<2"]
    if sys.version_info >= (3,11):
        needs.append("TA-Lib>=0.6.4,<1")
    subprocess.run([sys.executable,"-m","pip","install","-q",*needs],
                   check=True,timeout=190)
    script=(Path(__file__).resolve().parents[1]/"research"/
            "source_parity_trace_20261101"/"three_tp_be_audit.py")
    proc=subprocess.run([sys.executable,str(script)],capture_output=True,text=True,timeout=450)
    assert proc.returncode==0,proc.stdout[-15000:]+proc.stderr[-15000:]
    result=[line for line in proc.stdout.splitlines()
            if line.startswith("EMBER_3TP_MECHANISM_REPORT=")]
    assert len(result)==1
    data=json.loads(result[0].split("=",1)[1])
    assert data["source_receipt_SHA256"]=="b885da6dc7e80ea81c7bfb97ec1fb3da615e31824af48625f81cdd376d9a7ee7"
    assert data["signals"]==189
    assert data["sums"]["P07"]["signals"]==134
    assert data["sums"]["P10"]["signals"]==54
    assert data["sums"]["P06"]["signals"]==1
    assert data["sums"]["P06"]["first_three_cards"][0]["target_ladder"][0]["price"]==86365.5
    assert [x["price"] for x in data["sums"]["P06"]["first_three_cards"][0]["target_ladder"]]==[
        86365.5,86699.9,87247.3
    ]
    compact={k:{z:v for z,v in row.items() if z!="first_three_cards"}
             for k,row in data["sums"].items()}
    warnings.warn("EMBER_3TP_SUMMARY="+json.dumps(compact,ensure_ascii=False),stacklevel=1)
    for key in ("P07","P10","P06"):
        warnings.warn("EMBER_3TP_EXAMPLE_"+key+"="+json.dumps(
            data["sums"][key]["first_three_cards"],ensure_ascii=False),stacklevel=1)
