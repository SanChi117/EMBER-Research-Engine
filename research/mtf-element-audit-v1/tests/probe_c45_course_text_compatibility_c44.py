#!/usr/bin/env python3
"""C45: prove entire 97MB frozen C44 source lacks required course POI evidence.

This is a semantic SOURCE-EVIDENCE audit, not actual 45ZIP rescan, and does
NOT claim all historical market events were invalid. Unknown author proof
stays unknown; zero *provably certified* entries or orders.
"""
import json,sys,hashlib
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c45_recovered_course_text_contract import (
    recovered_text_claims,source_only_c44_compatibility)
SOURCE=ROOT/"evidence/c44/C44_ORIGINAL_BOUNDED_FTA_SOURCE_45ZIP.json"
RECOVERED=ROOT/"d05/C45_RECOVERED_AUTHOR_TEXT_RULES_20261023.json"
PIN=ROOT/"evidence/c45/C45_ALL_C44_CONTEXTS_COURSE_TEXT_GAP_AUDIT.json"
C44_SHA="62a8ef144a045733e2cdc35592056417916c9ab6db41e2dc8ffb9ea0c41f4892"

def run(path=None):
    raw=SOURCE.read_bytes()
    assert len(raw)==97764435
    assert hashlib.sha256(raw).hexdigest()==C44_SHA
    old=json.loads(raw)
    assert old["readiness"]=="NOT_TRADE_READY"
    assert old["original_binance_usdm_source_zip"]==45
    assert old["original_native3m_closed"]==76800
    assert old["native15m_exact_decimal"]==15360
    assert old["correlated_parent_contexts"]==17316
    assert old["route_count"]==36
    claims=recovered_text_claims()
    lesson=json.loads(RECOVERED.read_text(encoding="utf8"))
    assert len(claims)==17 and len(lesson["source_files"])==9
    markets=[]
    total=0
    aggregate=Counter()
    for m in old["markets"]:
        n=0
        statuses=Counter()
        gate_positive=Counter()
        assert len(m["source_routes"])==36
        for rt in m["source_routes"]:
            for c in rt["source_contexts"]:
                assert len(c["decisions"])==4
                assert c["orders"]==c["trades"]==[]
                assert c["readiness"]=="NOT_TRADE_READY"
                v=source_only_c44_compatibility(c)
                statuses[v["status"]]+=1
                assert v["author_ready"] is False and v["orders"]==0
                for decision in c["decisions"]:
                    if decision["selected_candidate"] is not None:
                        gate_positive[decision["policy_id"]]+=1
                    assert decision["trade_allowed"] is False
                    assert decision["author_poi_verified"] is False
                    assert decision["author_fta_verified"] is False
                n+=1
        total+=n
        aggregate.update(statuses)
        markets.append({"symbol":m["symbol"],"correlated_contexts":n,
            "course_text_source_evidence_statuses":dict(sorted(statuses.items())),
            "author_certified_contexts":0,"orders":0,"trades":0,
            "C44_adapted_candidate_counts":dict(sorted(gate_positive.items()))})
        print("C45_SOURCE_TEXT_GAP",m["symbol"],n,"no verified typed POI chain",flush=True)
    assert total==17316
    assert aggregate=={"COURSE_AUTHOR_POI_EVIDENCE_NOT_PRESENT":17316}
    result={
      "schema":"EMBER_C45_RECOVERED_TEXT_ORIGINAL_C44_SOURCE_EVIDENCE_GAP_V1",
      "frozen_C44_complete_JSON_sha256":C44_SHA,
      "frozen_C44_bytes":len(raw),
      "recovered_9_lesson_text_titles":[v["title"] for v in lesson["source_files"]],
      "recovered_17_course_text_claim_ids":sorted(claims),
      "original_C44_source_market_count":len(markets),
      "original_native3m_closed":old["original_native3m_closed"],
      "original_native15m_exact":old["native15m_exact_decimal"],
      "repeated_correlated_context_copies":total,
      "source_only_author_poi_evidence_statuses":dict(aggregate),
      "course_route_claim_to_original_C44_contexts_verified":0,
      "independently_author_labeled_2023_chart_goldens":0,
      "author_verified_trade_setups":0,
      "orders":0,"trades":0,"readiness":"NOT_TRADE_READY",
      "important_interpretation":"This is absence of original author-labeled POI test, context/VC, timeframe target, StrongHL source fields in existing C44 research output. It does NOT mean 17316 market events lacked any true real-world valid setup. A synthetically TEXT-CONSISTENT example is also not an academic chart golden.",
      "markets":markets}
    if path:
        file=Path(path);file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if PIN.exists():
        assert json.loads(PIN.read_text(encoding="utf8"))==result,"C45_FROZEN_SOURCE_AUDIT_DRIFT"
    print(json.dumps({"contexts":total,"author_certified":0,"gaps":dict(aggregate)},sort_keys=True),flush=True)
    return result

if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
