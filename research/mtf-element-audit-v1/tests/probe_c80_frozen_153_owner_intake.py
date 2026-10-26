#!/usr/bin/env python3
"""C80 independent 153-case source-intake probe, not authenticated goldens.

A hypothesis 'negative' at every context below is a test INPUT, not a
real author-negative outcome. The resulting valid intake stays UNVERIFIED.
"""
from pathlib import Path
import sys,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c80_owner_golden_intake import (review,audit_batch,C73_SHA,C72_BLOB,
    COURSE_A,POI_COURSE,PINNED_AUTHOR_CASE_ATTESTATIONS)
r73=(ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()
r72=(ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_bytes()
assert len(r73)==303327 and hashlib.sha256(r73).hexdigest()==C73_SHA
blob=hashlib.sha1(b"blob "+str(len(r72)).encode()+b"\0"+r72).hexdigest()
assert blob==C72_BLOB
s73=json.loads(r73);s72=json.loads(r72)
m72={(m["symbol"],q["original_c46_4h_parent_index"]):dict(q,symbol=m["symbol"])
    for m in s72["markets"] for q in m["original_parent_source_cases"]}
allrows=[];positive_possible=0
for market in s73["markets"]:
    for case in market["original_parent_source_cases"]:
        case=dict(case,symbol=market["symbol"])
        other=m72[case["symbol"],case["original_c46_4h_parent_index"]]
        candidate={
          "symbol":case["symbol"],"context_index":case["original_c46_4h_parent_index"],
          "source_side":case["side"],"claim":"1H_POI_VALID_FIRST_TEST",
          "polarity":"NEGATIVE","c73_sha256":C73_SHA,"c72_blob_sha1":C72_BLOB,
          "poi_created_ms":case["source_1h_poi_created_at_ms"],
          "original3m_touch_id":case["original_first_source3m_touch_id"],
          "original3m_touch_closed_ms":case["original_first_source3m_touch_closed_ms"],
          "source15m_event_closed_ms":case["first_source15m_event_fully_known_ms"],
          "source5m_event_closed_ms":other["first_any_5m_event_known_ms"],
          "course_route_a_id":COURSE_A,"course_poi_id":POI_COURSE,
          "source_document_url":None,"source_document_sha256":None,
          "author_label_anchor":None,"source_scope":"BINANCE_USDM_ORIGINAL_FROZEN",
          "source_reviewer_attestation":None
        }
        allrows.append(review(candidate,case,other))
        if case["first_source15m_event_fully_known_ms"] is not None:
            candidate["claim"]="15M_TRIGGER";candidate["polarity"]="POSITIVE"
            p=review(candidate,case,other)
            assert not p.actual_author_authentication and not p.author_15m_trigger
            positive_possible+=1
s=audit_batch(tuple(allrows))
assert len(m72)==s["intake_claims"]==153 and positive_possible==12
assert s["author_authenticated"]==s["trades"]==0
assert not PINNED_AUTHOR_CASE_ATTESTATIONS
w={"schema":"EMBER_C80_FROZEN_153_OWNER_GOLDEN_INTAKE_EMPTY_REGISTRY_V1",
   "date":"2026-10-26","C73_SHA256":C73_SHA,
   "C72_git_blob_sha1":blob,
   "source_cases_checked":153,
   "synthetic_negative_claims_passed":153,
   "source_15m_geometric_positive_hypotheses_screened":12,
   "claimed_label_sources_externally_authenticated":0,
   "owner_annotated_binance_positive_goldens":0,
   "owner_annotated_binance_negative_goldens":0,
   "all_intake_remains_unverified":True,
   "original_ZIPs_downloaded_this_cycle":False,
   "academic_routes":["Route A only; B IDM and C Raid-BOS separate"],
   "evidence_class":"SOURCE_ONLY_NOT_AUTHOR_CERTIFIED",
   "orders":0,"fills":0,"trades":0,"readiness":"NOT_TRADE_READY"}
print("C80_PINNED_SOURCE_INTAKE_WITNESS:"+json.dumps(w,sort_keys=True,separators=(",",":")),flush=True)
print("C80_SOURCE_153_NO_AUTHOR_GOLDEN_0_ORDERS_SUCCESS",flush=True)
