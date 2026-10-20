#!/usr/bin/env python3
"""C36 immutable academic/adapted slot design receipt, no order adapter."""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c36_adapted_slot_registry import (
    VARIANTS,slot_manifest,create_research_assembly)
PATH=ROOT/"evidence/c36/C36_VERSIONED_ADAPTED_SLOT_REGISTRY.json"

def run(output=None):
    r=slot_manifest()
    r["research_assemblies"]={v:asdict(
        create_research_assembly({"BOS_PIVOT":v})) for v in VARIANTS}
    assert len(r["research_assemblies"])==4
    assert r["academic_core"]["academic_original_evidence"]=="C20-C35_READ_ONLY"
    assert all(x["paper_order_placement_allowed"] is False and
               x["technical_backtest_ready"] is False and
               x["real_order_placement_allowed"] is False and
               not x["orders"] and not x["trades"] for x in r["research_assemblies"].values())
    assert r["readiness"]=="NOT_TRADE_READY"
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(r,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if PATH.exists():
        assert json.loads(PATH.read_text(encoding="utf8"))==r,"C36_SLOT_MANIFEST_PINNED_FULL_JSON_DRIFT"
    print(json.dumps({"academic_core_id":r["core_id"],
        "registered_variants":list(r["research_assemblies"]),
        "orders":r["orders"],"trades":r["trades"],
        "ready":r["readiness"]},sort_keys=True),flush=True)
    return r
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
