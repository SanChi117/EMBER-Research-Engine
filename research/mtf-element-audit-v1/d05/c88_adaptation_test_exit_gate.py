"""C88 final engineering acceptance vs owner-semantic and deployment gates.

Finishes adaptation AND broad regression testing. This report intentionally
never upgrades unlabelled Binance geometry to the author's academic signal
or claims out-of-sample trading edge.
"""
from collections import Counter
from hashlib import sha256
import json
from c85_owner_narrative_golden_firewall import serialize_witness as owner_text_witness
from c86_original153_first_test_receipts import audit_stored_bytes
from c87_adapted_route_a_shadow_gate import (audit_witness,classify_all,
                                             summarize as shadow_summarize)
class C88Rejected(ValueError):pass

RELEASE_CONTRACT={
 "research_route":"A",
 "operational_mode":"PAPER_SHADOW_NO_EXECUTION",
 "source_of_academic_text":"USER_OWNED_GOOGLE_DRIVE_ORIGINAL",
 "source_of_market_geometry":"HASH_PINNED_ARCHIVED_BINANCE_USDM",
 "owner_text_is_author_verified_market_case":False,
 "adapted_hypotheses_are_research_only":True,
 "allowed_to_construct_research_review_queue":True,
 "allowed_to_emit_trade_signal":False,
 "allowed_to_choose_entry_sl_tp":False,
 "allowed_to_route_orders":False,
 "allowed_to_autotrade":False,
 "profit_metrics_supported":False,
 "requires_owner_positive_and_negative_media":True,
 "requires_separate_out_of_sample_test_after_owner_validation":True,
 "release_class":"ENGINEERING_ADAPTATION_TEST_COMPLETE_SEMANTIC_GATED",
}
GATES={
 "ACADEMIC_TEXT_LINEAGE":"PASS",
 "PINNED_ARCHIVED_CRYPTO_LINEAGE":"PASS",
 "SOURCE_FIRST_TEST_AND_REVISIT":"PASS_SOURCE_ONLY",
 "ADAPTED_ROUTE_A_FSM_AND_RESEARCH_CLASSIFICATION":"PASS_RESEARCH_ONLY",
 "LTF_15M_TRIGGER_OR_DIRECT_VC_AUTHOR_PROOF":"BLOCKED_UNVERIFIED",
 "FIRST_VALID_4H_1H_OWNER_POI_TESTS":"BLOCKED_UNVERIFIED",
 "REAL_5M_OWNER_VC":"BLOCKED_UNVERIFIED",
 "SIGNED_POSITIVE_AND_NEGATIVE_CRYPTO_GOLDENS":"BLOCKED_MISSING",
 "TRADING_PNL_BACKTEST_VALIDITY":"BLOCKED_NO_AUTHOR_LABELS",
 "LIVE_EXECUTION":"DISABLED_BY_DESIGN",
}
FULL_SOURCE=153
def acceptance(c73,c72,c81,c86,c87,course_text_c85):
    if any(type(x) is not bytes for x in (c73,c72,c81,c86,c87,course_text_c85)):
        raise C88Rejected("IMMUTABLE_SOURCE_BYTES_REQUIRED")
    c85_replay=owner_text_witness(c73,c72,c81)
    if c85_replay!=course_text_c85:
        raise C88Rejected("ACADEMY_TEXT_WITNESS_DRIFT")
    a=audit_stored_bytes(c73,c72,c81,c86)
    b=audit_witness(c73,c72,c81,c86,c87)
    if a["cases"]!=FULL_SOURCE or b["source_contexts"]!=FULL_SOURCE:
        raise C88Rejected("FULL_ARCHIVE_MISSING")
    rec=classify_all(c73,c72,c81,c86)
    info=shadow_summarize(rec)
    obj=json.loads(c87)
    if obj.get("summary")!=info:
        raise C88Rejected("FROZEN_SUMMARY_DRIFT")
    if info["readiness"]!="NOT_TRADE_READY" or any(info[k] for k in ("entries","orders","fills","trades","positive_owner_goldens","negative_owner_goldens")):
        raise C88Rejected("FORGED_AUTHOR_OR_TRADE_READY")
    if info["decisions"].get("PRIORITIZED_FOR_HUMAN_MEDIA_REVIEW_ONLY",0)!=3:
        raise C88Rejected("UNEXPLAINED_CASE_REVIEW_COVERAGE_DRIFT")
    if info["decisions"].get("WITHHOLD_REVISIT_FIRST_VALID_UNPROVEN",0)!=3:
        raise C88Rejected("UNEXPLAINED_REVISIT_DRIFT")
    if info["source_coverage"]!={"COVERAGE_EARLY":69,"COVERAGE_LATE":60,"UNRESOLVED_SOURCE_TIME":24}:
        raise C88Rejected("TIMING_PARTITION_DRIFT")
    return {"schema":"C88_ROUTE_A_ADAPTATION_TEST_EXIT_V1",
            "exit_status":"ENGINEERING_COMPLETE_ACADEMIC_SEMANTIC_UNVERIFIED",
            "contract":RELEASE_CONTRACT,"gates":GATES,
            "source_archive":{"source_contexts":FULL_SOURCE,
                "c73_sha256":sha256(c73).hexdigest(),
                "c72_git_blob_sha1":__import__("hashlib").sha1(b"blob "+str(len(c72)).encode()+b"\x00"+c72).hexdigest(),
                "c81_sha256":sha256(c81).hexdigest(),
                "c85_owner_course_text_witness_sha256":sha256(course_text_c85).hexdigest(),
                "c86_first_test_receipt_sha256":sha256(c86).hexdigest(),
                "c87_adapted_shadow_sha256":sha256(c87).hexdigest()},
            "original_source_summary":info,
            "remaining_dependencies":[
                "Independent author crypto charts with a positive AND negative timestamp-labelled case; otherwise no author-verified goldens",
                "Original 4H parent POI valid first-test and 1H POI valid first-test source identification",
                "Owner-distinguished 15m Trigger versus direct VC, and 5m post-Trigger VC with no future bars",
                "Structural strong-high/low, invalidation, FTA and SL/TP source proof, never inferred from adapted patterns",
                "Independent no-leakage OOS PAPER backtest with valid labelled semantics before integration"
            ],
            "verification_note":"C87 split is timestamp COVERAGE only; not an OOS trading performance test.",
            "orders":[],"fills":[],"trades":[],"pnl":None,
            "readiness":"NOT_TRADE_READY"}

def serialize_acceptance(c73,c72,c81,c86,c87,c85):
    return (json.dumps(acceptance(c73,c72,c81,c86,c87,c85),
                       ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")

def check_frozen_acceptance(c73,c72,c81,c86,c87,c85,frozen):
    if type(frozen) is not bytes or frozen!=serialize_acceptance(c73,c72,c81,c86,c87,c85):
        raise C88Rejected("ACCEPTANCE_PROOF_TAMPERED")
    return {"bytes":len(frozen),"sha256":sha256(frozen).hexdigest(),
            "result":"ENGINEERING_COMPLETE_RESEARCH_ONLY"}
