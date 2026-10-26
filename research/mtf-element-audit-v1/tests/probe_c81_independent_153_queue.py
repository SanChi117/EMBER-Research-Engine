#!/usr/bin/env python3
"""C81 full actual 153-case independent queue verification.

Exact equality between newly derived source-only frozen-price queue and
separately committed 153 review packets. Queue identity is cryptographic
manifest evidence, NOT owner-signed signals or author-negative goldens.
"""
from pathlib import Path
from dataclasses import asdict
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c81_source_authenticated_review_queue import build,validate_queue,C73_SHA,C72_GIT_BLOB
src73=(ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()
src72=(ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_bytes()
queue=build(src73,src72)
checked=validate_queue(queue)
target=(ROOT/"evidence/c81/C81_FROZEN153_INDEPENDENT_REVIEW_QUEUE_SOURCE_ONLY.json").read_bytes()
declared=json.loads(target)
expected=[asdict(x) for x in queue]
assert expected==declared, "C81_FROZEN_QUEUE_FIELD_BYTES_OR_AUTHOR_SPOOF_DRIFT"
assert json.dumps(expected,sort_keys=True,indent=2,ensure_ascii=False).encode()+b"\n"==target
assert checked["priority_counts"]=={0:12,1:23,2:71,3:47}
assert len(declared)==153 and sum(x["priority"]==0 for x in declared)==12
assert all(not x["author_verified"] and not x["entry_allowed"] and
           not x["author_source_authenticated"] and not x["orders"] and
           not x["fills"] and not x["trades"] for x in declared)
assert checked["proven_positive_goldens"]==checked["proven_negative_goldens"]==0
shortlist=[{"source_key":x.source_key,"side":x.side,
            "poi_kind":x.poi_kind,"created_ms":x.poi_created_ms,
            "first3m_close_ms":x.first_original_3m_close_ms,
            "first15m_known_ms":x.source15m_known_ms,
            "first5m_known_ms":x.first5m_known_ms,
            "first5m_kind":x.first5m_kind,
            "source_visits":x.visits_before_source15m} for x in queue[:12]]
report={
 "schema":"EMBER_C81_FULL_FROZEN_SOURCE_REVIEW_QUEUE_INDEPENDENT_RECEIPT_V1",
 "source_C73_sha256":C73_SHA,"source_C72_git_blob_sha1":C72_GIT_BLOB,
 "queue_sha256":hashlib.sha256(target).hexdigest(),
 "queue_bytes":len(target),"source_contexts":153,
 "priority_counts":{str(k):v for k,v in checked["priority_counts"].items()},
 "status":"AWAITING_AUTHENTIC_OWNER_MEDIA_NOT_TRADE_READY",
 "first_review_batch":shortlist,
 "original_market_ZIPs_refetched_in_C81":False,
 "author_positive_crypto_goldens":0,"author_negative_crypto_goldens":0,
 "independently_owner_signed_cases":0,
 "orders":0,"fills":0,"trades":0}
print("C81_INDEPENDENT_153_QUEUE_RECEIPT:"+json.dumps(report,sort_keys=True,separators=(",",":")),flush=True)
print("C81_FROZEN_QUEUE_FULL_BYTES_AND_SOURCE_SHA_PASS",flush=True)
