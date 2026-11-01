"""Research mechanism-only audited original source on frozen Binance USD-M candles.

No native trading engine, no PnL, no economics, no real/PAPER orders.
"""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_mechanism_formation_on_real_closed_usdtm_candles():
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q",
         "numpy>=1.26,<3", "pandas>=2.1,<3", "scipy>=1.11,<2",
         "TA-Lib>=0.6.4,<1"],
        check=True, timeout=190,
    )
    p=Path(__file__).resolve().parents[1]/"research"/"source_parity_trace_20261101"/"mechanism_audit.py"
    proc=subprocess.run([sys.executable,str(p)],capture_output=True,text=True,timeout=450)
    assert proc.returncode == 0,(proc.stdout[-10000:]+"\n"+proc.stderr[-18000:])
    matches=[line for line in proc.stdout.splitlines() if line.startswith("EMBER_MECHANISM_AUDIT=")]
    assert matches,"No JSON audit receipt"
    obj=json.loads(matches[-1].split("=",1)[1])
    assert obj["no_money_economics"] is True
    assert obj["p07"]["total"]==134
    assert obj["p10"]["total"]==54
    report={k:{v:val for v,val in obj[k].items() if v!="first20"} for k in ("p07","p10","p06")}
    warnings.warn("EMBER_FORMATION_SUMMARY="+json.dumps(report,ensure_ascii=False),stacklevel=1)
    for k in ("p07","p10","p06"):
        warnings.warn("EMBER_FORMATION_CARDS_"+k.upper()+"="+json.dumps(obj[k]["first20"],ensure_ascii=False),stacklevel=1)
