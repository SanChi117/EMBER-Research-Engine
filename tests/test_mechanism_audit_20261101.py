"""Research mechanism-only audited original source on frozen Binance USD-M candles.

No native trading engine, no PnL, no economics, no real/PAPER orders.
"""
import json
import subprocess
import sys
import warnings
from pathlib import Path


def test_mechanism_formation_on_real_closed_usdtm_candles():
    # Python 3.10 on GitHub's current runner tries compiling TA-Lib C source
    # and can hit a >190s timeout. Preserve real-native TA-Lib audit on 3.11/3.12,
    # and do NOT mask P07/P10 original-source parity under a dependency failure.
    native_talib=sys.version_info >= (3,11)
    requirements=["numpy>=1.26,<3","pandas>=2.1,<3","scipy>=1.11,<2"]
    if native_talib:
        requirements.append("TA-Lib>=0.6.4,<1")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", *requirements],
        check=True, timeout=190,
    )
    p=Path(__file__).resolve().parents[1]/"research"/"source_parity_trace_20261101"/"mechanism_audit.py"
    run_args=[sys.executable,str(p)]
    if not native_talib:
        run_args.append("--skip-p06")
    proc=subprocess.run(run_args,capture_output=True,text=True,timeout=450)
    assert proc.returncode == 0,(proc.stdout[-10000:]+"\n"+proc.stderr[-18000:])
    matches=[line for line in proc.stdout.splitlines() if line.startswith("EMBER_MECHANISM_AUDIT=")]
    assert matches,"No JSON audit receipt"
    obj=json.loads(matches[-1].split("=",1)[1])
    assert obj["no_money_economics"] is True
    assert obj["p07"]["total"]==134
    assert obj["p10"]["total"]==54
    if native_talib:
        assert obj["p06"]["status"].startswith("ORIGINAL_CLASS_REAL_TALIB")
    else:
        assert obj["p06"]["status"].startswith("DEPENDENCY_UNAVAILABLE")
    report={k:{v:val for v,val in obj[k].items() if v!="first20"} for k in ("p07","p10","p06")}
    warnings.warn("EMBER_FORMATION_SUMMARY="+json.dumps(report,ensure_ascii=False),stacklevel=1)
    for k in ("p07","p10","p06"):
        warnings.warn("EMBER_FORMATION_CARDS_"+k.upper()+"="+json.dumps(obj[k]["first20"],ensure_ascii=False),stacklevel=1)
