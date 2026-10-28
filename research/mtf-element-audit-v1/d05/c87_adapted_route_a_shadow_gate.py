"""C87 sealed Route A adaptation; owner text vs technical proxies, source-only.

This is a *working deterministic research classifier*, not a signal router.
One never promotes first raw 3m wick to author-valid POI test, ambiguous
15m geometry to Trigger or VC, aligned 5m geometry to owner VC, or a 4H
parent source index to an authenticated first 4H test.
"""
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from c83_owner_course_text_crosswalk import source_matched_queue
from c81_source_authenticated_review_queue import validate_queue
from c86_original153_first_test_receipts import inspect_all,summarize as c86_summarize
from c85_owner_narrative_golden_firewall import ENTRY,RB,POI,IDM

class C87Rejected(ValueError): pass

# Frozen before selecting from the original 153-case queue. This is a
# temporal COVERAGE partition, not a training/test split for PnL.
HOLDOUT_START_MS=1789862400000 # 2026-09-20 00:00 UTC
END_SOURCE_MS=1790985600000    # 2026-10-03 00:00 UTC

POLICY={
 "version":"C87_ROUTE_A_ADAPTED_SHADOW_RESEARCH_V1",
 "route":"A",
 "evidence_class":"ADAPTED_HYPOTHESIS",
 "source_of_truth":"ORIGINAL_BINANCE_USDM_C73_C72_C81_C86_FROZEN",
 "owner_text_drive_id":ENTRY,
 "rb_owner_text_drive_id":RB,
 "poi_owner_text_drive_id":POI,
 "route_b_exclusion_drive_id":IDM,
 "assumption_01":"1H first raw 3m source wick represents PHYSICAL contact only, not author first valid POI test.",
 "assumption_02":"A solitary physical episode may be prioritized for source review; never sufficient for owner-valid test.",
 "assumption_03":"Source 15m IMB/SNR price geometry is not enough to choose Trigger vs direct VC.",
 "assumption_04":"Subsequent original 5m aligned price pattern is not sufficient to confirm owner 5m VC.",
 "assumption_05":"4H C46 source parent index is not proof of author-valid parent test/raid.",
 "assumption_06":"Source RB proxy requires independently authenticated wick raid or IMB interaction and 2-candle validity to become author RB.",
 "assumption_07":"4H IMB nesting veto and only IMB/SNR entry VC remain author text requirements but parent type and valid VC unproven.",
 "assumption_08":"Any source candidate is research-review-only; no Entry, SL, TP, order, fill, trade, statistical edge or numeric profit.",
 "countertests":(
   "NEG_MISSING_4H_FIRST_TEST","NEG_PARENT_C46_AS_AUTHOR_TEST",
   "NEG_RAW3M_REVISIT_AS_VALID_FIRST","NEG_P3_ORPHAN_RAW3M_AS_SELECTED_PARENT",
   "NEG_15M_PATTERN_AS_AUTHOR_TRIGGER","NEG_DIRECT_15M_VC_TO_5M",
   "NEG_5M_ALIGNED_AS_OWNER_VC","NEG_OPPOSITE_5M_DRESSED_AS_ALIGNED",
   "NEG_ROUTE_B_IDM_OR_C_RAID_BOS","NEG_FUTURE_15M_5M_LEAKAGE",
   "NEG_SYNTHETIC_AUTHOR_POSITIVE_NEGATIVE","NEG_LIVE_ORDERS"),
 "readiness":"NOT_TRADE_READY",
}

ALIGNED={"FIRST_5M_IMB_ALIGNED_NOT_AUTHOR_VC",
         "FIRST_5M_SNR_ALIGNED_NOT_AUTHOR_VC"}
OPPOSITE={"FIRST_5M_SOURCE_OPPOSITE_SIDE"}
AMBIGUOUS={"FIRST_5M_SOURCE_MULTIPLE_KINDS_AMBIGUOUS"}

@dataclass(frozen=True)
class AuthorClaim:
    case_key:str
    claimed_parent_4h_valid:bool=False
    claimed_first_1h_valid:bool=False
    claimed_15m_trigger:bool=False
    claimed_direct_15m_vc:bool=False
    claimed_5m_vc:bool=False
    claimed_owner_positive:bool=False
    claimed_owner_negative:bool=False
    claimed_route:str="A"
    proposed_entry:str=""
    proposed_sl:str=""
    proposed_tp:str=""

def reject_unverified_claim(claim):
    """Reject all self-certified owner and entry claims; no trust loophole."""
    if type(claim) is not AuthorClaim or not isinstance(claim.case_key,str) or not claim.case_key:
        raise C87Rejected("EXACT_CLAIM_REQUIRED")
    if claim.claimed_route!="A":
        raise C87Rejected("B_OR_C_CROSS_ROUTE")
    if any((claim.claimed_parent_4h_valid,claim.claimed_first_1h_valid,
            claim.claimed_15m_trigger,claim.claimed_direct_15m_vc,
            claim.claimed_5m_vc,claim.claimed_owner_positive,
            claim.claimed_owner_negative)):
        raise C87Rejected("SELF_ATTESTED_OWNER_SEMANTIC_FORBIDDEN")
    if claim.proposed_entry or claim.proposed_sl or claim.proposed_tp:
        raise C87Rejected("TRADING_LEVEL_OR_ORDER_FORBIDDEN")
    return {"case_key":claim.case_key,
            "status":"UNVERIFIED_RESEARCH_SUBMISSION_QUARANTINE",
            "author_verified":False,"entry_allowed":False,
            "orders":[],"fills":[],"trades":[],"readiness":"NOT_TRADE_READY"}

def _classify(r,x):
    if r["case_key"]!=x.source_key or r["priority"]!=x.priority or r["symbol"]!=x.symbol:
        raise C87Rejected("CASE_IDENTITY_OR_PRIORITY_DRIFT")
    if r["4h_author_valid_first_test"]!="UNKNOWN_NOT_PROVEN" or r["1h_author_valid_first_test"]!="UNKNOWN_NOT_PROVEN":
        raise C87Rejected("SPOOFED_VALID_FIRST_POI_TEST")
    if r["author_positive_golden"] or r["author_negative_golden"] or r["orders"] or r["fills"] or r["trades"]:
        raise C87Rejected("SPOOFED_GOLDEN_OR_EXECUTION")
    if x.priority==0:
        if x.source15m_known_ms is None or x.first5m_known_ms is None:
            raise C87Rejected("P0_15M_OR_5M_MISSING")
        if not (x.poi_created_ms<x.first_original_3m_close_ms<
                x.source15m_known_ms<x.first5m_known_ms):
            raise C87Rejected("P0_FUTURE_LEAK")
        if x.first5m_kind in ALIGNED:
            direction="ALIGNED_SOURCE_GEOMETRY_ONLY"
        elif x.first5m_kind in OPPOSITE:
            direction="OPPOSITE_SOURCE_GEOMETRY"
        elif x.first5m_kind in AMBIGUOUS:
            direction="MULTIKIND_AMBIGUOUS_SOURCE_GEOMETRY"
        else:
            raise C87Rejected("UNKNOWN_OR_FORGED_5M_SOURCE_KIND")
        visits=x.visits_before_source15m
        if type(visits) is not int or visits<1:
            raise C87Rejected("INVALID_VISIT_EPISODES")
        if visits>1:
            decision="WITHHOLD_REVISIT_FIRST_VALID_UNPROVEN"
        elif direction=="ALIGNED_SOURCE_GEOMETRY_ONLY":
            decision="PRIORITIZED_FOR_HUMAN_MEDIA_REVIEW_ONLY"
        else:
            decision="WITHHOLD_AMBIGUOUS_OR_OPPOSITE_GEOMETRY"
        source_clock=x.first5m_known_ms
    elif x.priority==1:
        direction="NO_SOURCE_15M_5M"
        decision="WITHHOLD_NO_CLOSED_15M_VC_OR_TRIGGER"
        source_clock=x.first_original_3m_close_ms
    elif x.priority==2:
        direction="UNSELECTED_1H_PARENT"
        decision="WITHHOLD_OPPOSITE_OR_AMBIGUOUS_1H_PARENT"
        source_clock=x.poi_created_ms
    elif x.priority==3:
        direction="NO_SELECTED_NEW_1H_POI"
        decision="WITHHOLD_NO_SELECTED_NEW_1H_POI"
        source_clock=x.first_original_3m_close_ms
        if source_clock is None:
            source_clock=None
    else:
        raise C87Rejected("UNSUPPORTED_PRIORITY")
    if source_clock is not None and type(source_clock) is not int:
        raise C87Rejected("SOURCE_EVENT_TIME_NOT_INT")
    split=("UNRESOLVED_SOURCE_TIME" if source_clock is None else
           "COVERAGE_EARLY" if source_clock<HOLDOUT_START_MS else
           "COVERAGE_LATE" if source_clock<END_SOURCE_MS else
           "AFTER_FROZEN_ARCHIVE")
    return {"case_key":x.source_key,"priority":x.priority,
            "native_source_decision":decision,
            "technical_5m_geometry":direction,
            "source_asof_ms":source_clock,"coverage_partition":split,
            "first_physical_1h_contact":r["raw_native_3m"] is not None,
            "first_valid_1h_poi_test":"UNKNOWN_NOT_PROVEN",
            "first_valid_4h_poi_test":"UNKNOWN_NOT_PROVEN",
            "15m_trigger_vs_direct_vc":"UNRESOLVED_NOT_OWNER_VERIFIED",
            "5m_volume_confirmation":"UNRESOLVED_NOT_OWNER_VERIFIED",
            "evidence_class":"ADAPTED_HYPOTHESIS",
            "source_evidence_class":"SOURCE_TECHNICAL",
            "course_rule_source":ENTRY,
            "certified_author_positive":False,"certified_author_negative":False,
            "provisional_entry":None,"provisional_sl":None,
            "provisional_tp":None,
            "orders":[],"fills":[],"trades":[],
            "readiness":"NOT_TRADE_READY"}

def classify_all(c73,c72,c81,receipts_bytes):
    if type(receipts_bytes) is not bytes:
        raise C87Rejected("EXACT_C86_FROZEN_BYTES_REQUIRED")
    # NO archive edit, NO unreviewed input injection, exact C86 fingerprint
    from c86_original153_first_test_receipts import audit_stored_bytes
    audit_stored_bytes(c73,c72,c81,receipts_bytes)
    raw=json.loads(receipts_bytes)
    receipts=raw["receipts"]
    q=source_matched_queue(c73,c72,c81)
    validate_queue(q)
    if len(q)!=len(receipts) or len(q)!=153:
        raise C87Rejected("SOURCE_AND_RECEIPT_COUNT_DRIFT")
    out=[_classify(r,x) for r,x in zip(receipts,q)]
    if len(set(x["case_key"] for x in out))!=153:
        raise C87Rejected("DUPLICATE_ORIGINAL_CASE")
    return out

def summarize(records):
    if type(records) is not list or len(records)!=153 or len({r["case_key"] for r in records})!=153:
        raise C87Rejected("EXPECTED_ORIGINAL153")
    for r in records:
        if (r["evidence_class"]!="ADAPTED_HYPOTHESIS" or
            r["source_evidence_class"]!="SOURCE_TECHNICAL" or
            r["first_valid_4h_poi_test"]!="UNKNOWN_NOT_PROVEN" or
            r["first_valid_1h_poi_test"]!="UNKNOWN_NOT_PROVEN" or
            r["15m_trigger_vs_direct_vc"]!="UNRESOLVED_NOT_OWNER_VERIFIED" or
            r["5m_volume_confirmation"]!="UNRESOLVED_NOT_OWNER_VERIFIED" or
            r["certified_author_positive"] or r["certified_author_negative"] or
            r["provisional_entry"] is not None or r["provisional_sl"] is not None or
            r["provisional_tp"] is not None or
            r["orders"] or r["fills"] or r["trades"] or
            r["readiness"]!="NOT_TRADE_READY"):
            raise C87Rejected("UNVERIFIED_SOURCE_PROMOTED_TO_TRADE_OR_AUTHOR")
    return {"schema":"EMBER_C87_COMPLETED_ROUTE_A_ADAPTED_SHADOW_GATE",
            "source_contexts":153,
            "priority":dict(sorted(Counter(str(r["priority"]) for r in records).items())),
            "decisions":dict(sorted(Counter(r["native_source_decision"] for r in records).items())),
            "source_coverage":dict(sorted(Counter(r["coverage_partition"] for r in records).items())),
            "positive_owner_goldens":0,"negative_owner_goldens":0,
            "paper_profit_metrics_valid":False,"entries":0,"orders":0,"fills":0,
            "trades":0,"readiness":"NOT_TRADE_READY"}

def witness(c73,c72,c81,c86):
    rec=classify_all(c73,c72,c81,c86)
    return {"policy":{**POLICY,"countertests":list(POLICY["countertests"])},
            "summary":summarize(rec),"cases":rec}

def serialize_witness(c73,c72,c81,c86):
    return (json.dumps(witness(c73,c72,c81,c86),ensure_ascii=False,
                       indent=2,sort_keys=True)+"\n").encode("utf8")

def audit_witness(c73,c72,c81,c86,data):
    if type(data) is not bytes or serialize_witness(c73,c72,c81,c86)!=data:
        raise C87Rejected("ADAPTED_SHADOW_WITNESS_DRIFT")
    return {"bytes":len(data),"sha256":sha256(data).hexdigest(),
            "source_contexts":153,"status":"TESTED_RESEARCH_ONLY"}
