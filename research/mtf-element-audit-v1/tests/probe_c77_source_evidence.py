"""C77 independently verify frozen market source, rejected branches, CI receipts."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
C73="c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b"
def review():
    a=ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json"
    assert len(a.read_bytes())==303327
    assert hashlib.sha256(a.read_bytes()).hexdigest()==C73
    real=json.loads((ROOT/"evidence/c77/C77_FRESH_ORIGINAL45ZIP_BRANCH_AWARE_POI_REPLAY.json").read_text())
    forensic=json.loads((ROOT/"evidence/c77/C77_NAIVE_FORENSIC_COUNTEREXAMPLES.json").read_text())
    ci=json.loads((ROOT/"evidence/c77/C77_HISTORICAL_CI_C59_C73_PROOF.json").read_text())
    assert real["readiness"]=="NOT_TRADE_READY" and real["source_contexts"]==153
    assert real["source_C73_sha256"]==C73
    assert real["original_zip_counts"]=={"3m":15,"15m":15,"1d":15,"total":45}
    assert real["original3m_closed"]==76800
    assert real["native15m_equalities"]==15360
    assert sum(x["review"]["contexts"] for x in real["markets"])==82
    assert sum(x["review"]["unselected_source_contexts"] for x in real["markets"])==71
    parents={}
    for m in real["markets"]:
        for k,v in m["review"]["types"].items():parents[k]=parents.get(k,0)+v
        assert m["trades"]==m["author_approved"]==0
    assert parents=={"NO_PARENT":47,"RB":28,"SNR":7}
    assert forensic["source_contexts"]==153
    assert forensic["source_semantic_conflict_contexts"]==71
    assert forensic["fully_strict_verified_contexts"]==82
    assert len(forensic["issues"])==71
    assert len(ci["run_results"])==15
    assert all(x["conclusion"]=="success" for x in ci["run_results"])
    assert len({x["run_id"] for x in ci["run_results"]})==15
    assert (real["orders"],real["fills"],real["trades"],
            forensic["orders"],forensic["fills"],forensic["trades"])==(0,0,0,0,0,0)
    print("C77_ALL_FROZEN_SOURCE_PROOFS_PASS selected35 rejected71 no_new47 source_only no_trades")
if __name__=="__main__":review()
