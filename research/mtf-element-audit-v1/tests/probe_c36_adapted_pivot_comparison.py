#!/usr/bin/env python3
"""C36 offline adaptation selection DISAGREEMENT, not trading backtest."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c36_adapted_pivot_hypotheses import summarize_frozen_c33,FROZEN_C33_SHA,VARIANTS
RAW=ROOT/"evidence/c33/C33_ORIGINAL_COMPETING_BOS_PIVOTS_SOURCE.json"
PIN=ROOT/"evidence/c36/C36_PIVOT_HYPOTHESES_SOURCE_COMPARISON.json"

def main(output=None):
    source_sha=subprocess.check_output(["git","rev-parse","HEAD:research/mtf-element-audit-v1/evidence/c33/C33_ORIGINAL_COMPETING_BOS_PIVOTS_SOURCE.json"],
              text=True,cwd=ROOT.parent).strip()
    # Git HEAD:<path> resolves relative to repository root rather than
    # ROOT's parent research dir. Detect git rev-parse path drift.
    assert source_sha==FROZEN_C33_SHA,(source_sha,FROZEN_C33_SHA)
    prior=json.loads(RAW.read_text(encoding="utf8"))
    x=summarize_frozen_c33(prior)
    assert x["source_c33_git_blob"]==FROZEN_C33_SHA
    assert x["original_parent_events"]==539 and x["original_swing_candidate_links"]==5285
    assert all(x["variant_agreement_only"][v]["n"]==539 for v in VARIANTS)
    assert x["variant_agreement_only"]["LATEST_CONFIRMED_V1"]["agrees_with_c21"]==539
    assert all(x["period_partitions"][s]["events"]>0 for s in ("DEVELOPMENT","VALIDATION","HOLDOUT"))
    assert x["author_selected_BOS_goldens"]==x["orders_created"]==x["trades_created"]==0
    assert x["readiness"]=="NOT_TRADE_READY"
    if output:
        path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if PIN.exists():
        assert json.loads(PIN.read_text(encoding="utf8"))==x,"C36_FROZEN_COMPLETE_539_CASE_JSON_DRIFT"
    print(json.dumps({"counts":x["variant_agreement_only"],
        "time_splits":{s:v["events"] for s,v in x["period_partitions"].items()},
        "markets":{s:m["events"] for s,m in x["by_market"].items()},
        "author_goldens":0,"trades":0,"status":"NOT_TRADE_READY"},sort_keys=True),flush=True)
    return x

if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
