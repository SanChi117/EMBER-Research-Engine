#!/usr/bin/env python3
"""C81 immutable witness vs source bytes; owner-positive labels remain zero."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c81_source_authenticated_review_queue import build,validate_queue,submit_for_review
a=(ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()
b=(ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_bytes()
f=(ROOT/"evidence/c81/C81_FROZEN153_INDEPENDENT_REVIEW_QUEUE_SOURCE_ONLY.json").read_bytes()
w=json.loads((ROOT/"evidence/c81/C81_INDEPENDENT_SOURCE_QUEUE_WITNESS.json").read_text())
q=build(a,b);report=validate_queue(q)
assert hashlib.sha256(f).hexdigest()==w["queue_sha256"]
assert len(f)==w["queue_bytes"]==148772
assert hashlib.sha256(a).hexdigest()==w["source_C73_sha256"]
assert hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()==w["source_C72_git_blob_sha1"]
assert len(q)==w["original_source_cases"]==153
assert {str(k):v for k,v in report["priority_counts"].items()}==w["priority_counts"]
assert [x.source_key for x in q[:12]]==w["first_review_batch"]
assert w["owner_authenticated_positive_goldens"]==w["owner_authenticated_negative_goldens"]==0
assert sum(x.source_group=="NO_SELECTED_NEW_1H_POI" and x.first_original_3m_close_ms is not None for x in q)==23
assert w["original_60_zip_archive_refetched_during_C81"] is False
fake=submit_for_review(q[0],document_sha256="b"*64,
                       source_anchor="owner slide 8 (unverified)",
                       reviewer_declared="claimed expert reviewer")
assert fake["review_status"]=="QUARANTINED_EXTERNAL_OWNER_MEDIA_UNAUTHENTICATED"
assert fake["author_verified"] is False and fake["entry_allowed"] is False
assert w["orders"]==w["fills"]==w["trades"]==0
print("C81_SOURCE_QUEUE_WITNESS_153_12_23_71_47_AND_SHA256_PASS",flush=True)
