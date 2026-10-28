"""C86 original153 first-test provenance receipts (PAPER ONLY).

This module cannot infer the author-valid 4H/1H POI test from C46 index,
first raw 3m wick, time ordering, technical RB/IMB/SNR, nor an example
caption. It only creates falsifiable, source-pinned review receipts.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation
from dataclasses import asdict, replace
from hashlib import sha256
import json,re
from c83_owner_course_text_crosswalk import source_matched_queue
from c81_source_authenticated_review_queue import QueueItem,validate_queue
from c85_owner_narrative_golden_firewall import ENTRY,RB,POI

class C86Rejected(ValueError):pass

SOURCE_ID=re.compile(r"^[0-9a-f]{64}:[0-9]+$")
COURSE_ANCHORS=(
    {"gate":"4H_FIRST_VALID_TEST","drive_id":ENTRY,
     "requires":"Owner-qualified original 4H POI first test AND causal 1H branch; C46 source index alone insufficient"},
    {"gate":"1H_POI_CREATED_FROM_4H","drive_id":ENTRY,
     "requires":"Owner-valid 4H test/reaction or 4H liquidity raid contextualizes genuinely new 1H POI"},
    {"gate":"1H_FIRST_VALID_TEST","drive_id":ENTRY,
     "requires":"Author-qualified first real 1H POI test, NOT physical raw 3m first contact"},
    {"gate":"RB_RAID_IMB_WICK_FIRST_TEST","drive_id":RB,
     "requires":"Two opposed closed candles; liquidity wick raid or IMB interaction, body close nuance, no repeat as first"},
    {"gate":"POI_STRENGTH","drive_id":POI,
     "requires":"Liquidity SSL/BSL or FVG interaction is a strength criterion, not self-evident author confirmation"},
)
PROOF_GAPS=("AUTHOR_POSITIVE_TIMESTAMPED_SOURCE_MATCH",
            "AUTHOR_NEGATIVE_TIMESTAMPED_COUNTEREXAMPLE",
            "4H_POI_OR_4H_LIQUIDITY_RAID_OWNER_VALID",
            "4H_FIRST_TEST_TIME_AND_REACTION",
            "1H_NEW_POI_CREATION_AUTHOR_VALID",
            "1H_FIRST_TEST_SEMANTIC_PROOF",
            "RB_WICK_LIQUIDITY_OR_IMB_CONTEXT_IF_RB",
            "VALID_15M_TRIGGER_OR_DIRECT_VC",
            "CAUSAL_5M_VC_AFTER_REAL_TRIGGER")

def _checked_time(value,what):
    if type(value) is not int or value<0:
        raise C86Rejected("INVALID_TIME_"+what)
    return value

def _validate_source_3m(item):
    if item.first_original_3m_close_ms is None:
        if item.first_original_3m_id is not None:
            raise C86Rejected("3M_ID_WITHOUT_CLOSE")
        return None
    close=_checked_time(item.first_original_3m_close_ms,"3M")
    identifier=item.first_original_3m_id
    if type(identifier) is not str or not SOURCE_ID.fullmatch(identifier):
        raise C86Rejected("FORGED_OR_BAD_NATIVE_3M_ID")
    opening=int(identifier.rsplit(":",1)[1])
    if opening%180000!=0 or close-opening!=180000:
        raise C86Rejected("3M_OPEN_CLOSE_OR_ALIGNMENT")
    return {"native_source_id":identifier,"native_open_ms":opening,
            "native_closed_ms":close,
            "observation":"RAW_PHYSICAL_3M_WICK_ONLY_NOT_OWNER_VALID"}

def _checked_price_bounds(item):
    if item.poi_kind=="NO_NEW_1H_POI":
        return None
    if item.poi_kind not in ("1H_NEW_VC_RB_SOURCE","1H_NEW_VC_SNR_SOURCE",
                             "1H_NEW_VC_IMB_SOURCE"):
        raise C86Rejected("UNSUPPORTED_1H_SOURCE_KIND")
    try:
        a=Decimal(item.poi_low);b=Decimal(item.poi_high)
    except (ValueError,TypeError,InvalidOperation):
        raise C86Rejected("BAD_SOURCE_POI_DECIMAL")
    if not a.is_finite() or not b.is_finite() or not 0<a<b:
        raise C86Rejected("BAD_OR_INVERTED_1H_POI")
    return {"low":item.poi_low,"high":item.poi_high,
            "kind":item.poi_kind,"status":"TECHNICAL_SOURCE_ONLY"}

def receipt(item):
    if type(item) is not QueueItem:
        raise C86Rejected("EXACT_FROZEN_QUEUE_ITEM")
    if item.source_key!=item.symbol+"/"+str(item.index) or item.side not in ("LONG","SHORT") or type(item.index) is not int or item.index<0:
        raise C86Rejected("BAD_SOURCE_CASE_ID")
    if item.priority not in (0,1,2,3):
        raise C86Rejected("BAD_PRIORITY")
    if item.author_verified or item.author_source_authenticated or item.claimed_author_label is not None or item.owner_document_anchor is not None or item.reviewer_attestations or item.entry_allowed or item.orders or item.fills or item.trades or item.readiness!="NOT_TRADE_READY":
        raise C86Rejected("FORGED_OWNER_OR_EXECUTION")
    native=_validate_source_3m(item)
    poi=_checked_price_bounds(item)
    created=item.poi_created_ms
    if poi is not None:
        t=_checked_time(created,"1H_CREATED")
        if t%3600000!=0:
            raise C86Rejected("1H_SOURCE_CREATE_NOT_CLOSED_HOUR")
        if native is not None and native["native_closed_ms"]<=t:
            raise C86Rejected("3M_BEFORE_1H_POI_KNOWN")
    else:
        if item.poi_created_ms is not None or item.poi_low is not None or item.poi_high is not None:
            raise C86Rejected("UNSELECTED_POI_WITH_GHOST_LEVELS")
    after=item.source15m_known_ms; later=item.first5m_known_ms
    if item.priority==0:
        if poi is None or native is None or any(type(x) is not int for x in (created,after,later)) or not created<native["native_closed_ms"]<after<later:
            raise C86Rejected("P0_CAUSAL_CLOCK")
        if after%900000!=0 or later%300000!=0:
            raise C86Rejected("P0_NATIVE_CLOSE_NOT_ALIGNED")
        if type(item.visits_before_source15m) is not int or item.visits_before_source15m<1:
            raise C86Rejected("P0_VISITS_MISSING")
        visit_status="SINGLE_PHYSICAL_EPISODE" if item.visits_before_source15m==1 else "MULTIPLE_PHYSICAL_EPISODES"
    elif item.priority==1:
        if poi is None or native is None or after is not None or later is not None:
            raise C86Rejected("P1_NEEDS_TECHNICAL_POI_TOUCH_ONLY")
        visit_status="FIRST_RAW3M_CONTACT_ONLY"
    elif item.priority==2:
        if native is not None or after is not None or later is not None:
            raise C86Rejected("P2_PARENT_UNSELECTED_HAS_FUTURE")
        visit_status="UNSELECTED_PARENT_NO_ELIGIBLE_TOUCH"
    else:
        if poi is not None or after is not None or later is not None:
            raise C86Rejected("P3_MUST_HAVE_NO_NEW_1H_POI")
        visit_status="NO_SELECTED_POI_RAW3M_EXISTS" if native is not None else "NO_SELECTED_POI_NO_RAW3M"
    if item.priority in (0,1,2) and poi is None:
        raise C86Rejected("SELECTED_OR_UNSELECTED_TECHNICAL_POI_ABSENT")
    if item.priority!=0 and item.visits_before_source15m is not None:
        raise C86Rejected("EPISODES_ONLY_WITH_15M_SOURCE")
    return {
      "case_key":item.source_key,"symbol":item.symbol,"side":item.side,
      "priority":item.priority,"parent_c46_4h_index":item.index,
      "4h_parent_source_status":"C46_TECHNICAL_INDEX_ONLY_NO_AUTHOR_FIRST_TEST",
      "4h_source_first_valid_test_closed_ms":None,
      "4h_author_valid_first_test":"UNKNOWN_NOT_PROVEN",
      "1h_poi_source":poi,"1h_poi_created_ms":created,
      "raw_native_3m":native,
      "physical_episode_count_before_source15m":item.visits_before_source15m,
      "physical_visit_class":visit_status,
      "15m_source_known_ms":after,"5m_source_known_ms":later,
      "1h_author_valid_first_test":"UNKNOWN_NOT_PROVEN",
      "15m_author_trigger_or_vc":"UNKNOWN_NOT_PROVEN",
      "5m_author_vc":"UNKNOWN_NOT_PROVEN",
      "course_rule_anchor_ids":[e["gate"] for e in COURSE_ANCHORS],
      "missing_owner_proofs":list(PROOF_GAPS),
      "author_positive_golden":False,"author_negative_golden":False,
      "orders":[],"fills":[],"trades":[],
      "readiness":"NOT_TRADE_READY"}

def inspect_all(c73_bytes,c72_bytes,c81_bytes):
    queue=source_matched_queue(c73_bytes,c72_bytes,c81_bytes)
    validate_queue(queue)
    rows=[receipt(x) for x in queue]
    if len(rows)!=153 or len({r["case_key"] for r in rows})!=153:
        raise C86Rejected("ORIGINAL153_CASE_COUNT")
    counts=Counter(r["priority"] for r in rows)
    if counts!={0:12,1:23,2:71,3:47}:
        raise C86Rejected("SOURCE_PRIORITY_MISMATCH")
    return rows

def summarize(rows):
    if type(rows) is not list or len(rows)!=153 or len({r["case_key"] for r in rows})!=153:
        raise C86Rejected("NOT_153_RECEIPTS")
    counts=Counter(r["priority"] for r in rows)
    if counts!={0:12,1:23,2:71,3:47}:
        raise C86Rejected("SUMMARY_PRIORITIES_DRIFT")
    if any(r["4h_author_valid_first_test"]!="UNKNOWN_NOT_PROVEN" or
           r["1h_author_valid_first_test"]!="UNKNOWN_NOT_PROVEN" or
           r["author_positive_golden"] or r["author_negative_golden"] or
           r["orders"] or r["fills"] or r["trades"] or
           r["readiness"]!="NOT_TRADE_READY" for r in rows):
        raise C86Rejected("AUTHOR_OR_EXECUTION_PROMOTION")
    visit_counts=dict(sorted(Counter(r["physical_visit_class"] for r in rows).items()))
    return {"schema":"EMBER_C86_ORIGINAL153_FIRST_VALID_TEST_PROVENANCE",
            "source_crypto_contexts":153,
            "priority_counts":{str(k):counts[k] for k in range(4)},
            "physical_classes":visit_counts,
            "4h_author_first_valid_test_count":0,
            "1h_author_first_valid_test_count":0,
            "certified_owner_positive_goldens":0,
            "certified_owner_negative_goldens":0,
            "entries":0,"orders":0,"fills":0,"trades":0,
            "readiness":"NOT_TRADE_READY"}

def serialize_receipts(c73,c72,c81):
    return (json.dumps({"summary":summarize(inspect_all(c73,c72,c81)),
          "course_first_test_anchors":list(COURSE_ANCHORS),
          "receipts":inspect_all(c73,c72,c81)},sort_keys=True,
          ensure_ascii=False,indent=2)+"\n").encode("utf8")

def audit_stored_bytes(c73,c72,c81,archived):
    if type(archived) is not bytes:
        raise C86Rejected("ARCHIVE_BYTES_REQUIRED")
    original=serialize_receipts(c73,c72,c81)
    if archived!=original:
        raise C86Rejected("FROZEN_153_RECEIPTS_TAMPER_OR_DRIFT")
    return {"bytes":len(original),"sha256":sha256(original).hexdigest(),
            "cases":153,"readiness":"NOT_TRADE_READY"}
