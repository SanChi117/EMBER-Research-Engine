"""C80 adversarial 100% frozen real-source case fixtures, not owner goldens."""
import json
from pathlib import Path
from copy import deepcopy
from dataclasses import replace
import unittest
from c80_owner_golden_intake import (review,audit_batch,C80Rejected,
    C73_SHA,C72_BLOB,COURSE_A,POI_COURSE,FIELDS,PINNED_AUTHOR_CASE_ATTESTATIONS)

ROOT=Path(__file__).resolve().parents[1]
a=json.loads((ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_text())
b=json.loads((ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_text())
old={(m["symbol"],q["original_c46_4h_parent_index"]):dict(q,symbol=m["symbol"])
     for m in b["markets"] for q in m["original_parent_source_cases"]}
FIX=[(dict(q,symbol=m["symbol"]),old[m["symbol"],q["original_c46_4h_parent_index"]])
     for m in a["markets"] for q in m["original_parent_source_cases"]]

def fixture(kind="pattern",claim="15M_TRIGGER",polarity="POSITIVE"):
    for m,n in FIX:
        if kind=="pattern" and m["first_source15m_event_fully_known_ms"] is None:continue
        if kind=="touch" and m["original_first_source3m_touch_closed_ms"] is None:continue
        if kind=="no_touch" and m["original_first_source3m_touch_closed_ms"] is not None:continue
        p={
        "symbol":m["symbol"],"context_index":m["original_c46_4h_parent_index"],
        "source_side":m["side"],"claim":claim,"polarity":polarity,
        "c73_sha256":C73_SHA,"c72_blob_sha1":C72_BLOB,
        "poi_created_ms":m["source_1h_poi_created_at_ms"],
        "original3m_touch_id":m["original_first_source3m_touch_id"],
        "original3m_touch_closed_ms":m["original_first_source3m_touch_closed_ms"],
        "source15m_event_closed_ms":m["first_source15m_event_fully_known_ms"],
        "source5m_event_closed_ms":n["first_any_5m_event_known_ms"],
        "course_route_a_id":COURSE_A,"course_poi_id":POI_COURSE,
        "source_document_url":None,"source_document_sha256":None,
        "author_label_anchor":None,"source_scope":"BINANCE_USDM_ORIGINAL_FROZEN",
        "source_reviewer_attestation":None}
        return p,deepcopy(m),deepcopy(n)
    raise AssertionError("missing fixture "+kind)

class C80(unittest.TestCase):
    def test_00_zero_owner_crypto_positive_or_negative_goldens(self):
        self.assertEqual(len(PINNED_AUTHOR_CASE_ATTESTATIONS),0)
    def test_01_source_case_positive_claim_not_verification(self):
        p,m,n=fixture()
        r=review(p,m,n)
        self.assertTrue(r.source_price_linked)
        self.assertFalse(r.actual_author_authentication)
        self.assertFalse(r.entry_allowed)
        self.assertEqual(r.status,"UNVERIFIED_OWNER_LABEL")
        self.assertEqual(r.readiness,"NOT_TRADE_READY")
    def test_02_genuine_source_negative_claim_unverified(self):
        p,m,n=fixture("no_touch","1H_POI_VALID_FIRST_TEST","NEGATIVE")
        r=review(p,m,n)
        self.assertEqual(r.polarity,"NEGATIVE")
        self.assertFalse(r.actual_author_authentication)
    def test_03_source_wick_no_author_test(self):
        p,m,n=fixture("touch","1H_POI_VALID_FIRST_TEST")
        r=review(p,m,n)
        self.assertFalse(r.author_valid_first_test)
    def test_04_5m_claim_with_original_source_still_unverified(self):
        p,m,n=fixture("pattern","POST_TRIGGER_5M_VC")
        r=review(p,m,n)
        self.assertFalse(r.author_5m_vc)
    def test_05_fake_attestation_sha_cannot_promote(self):
        p,m,n=fixture()
        p.update(source_document_sha256="f"*64,
                 source_reviewer_attestation="a"*64,
                 source_document_url="https://example.org/fake-attestation",
                 author_label_anchor="page 3")
        self.assertFalse(review(p,m,n).actual_author_authentication)
    def test_06_same_event_positive_and_negative_conflict_rejected(self):
        p,m,n=fixture()
        a1=review(p,m,n)
        a2=replace(a1,polarity="NEGATIVE")
        with self.assertRaises(C80Rejected):audit_batch((a1,a2))
    def test_07_one_negative_intake_is_not_true_negative(self):
        p,m,n=fixture("no_touch","1H_POI_VALID_FIRST_TEST","NEGATIVE")
        z=audit_batch((review(p,m,n),))
        self.assertEqual(z["author_authenticated"],0)
        self.assertEqual(z["claimed_polarity_counts"]["NEGATIVE"],1)
    def test_08_frozen_153_case_negative_source_claims(self):
        receipts=[]
        for m,n in FIX:
            p={"symbol":m["symbol"],"context_index":m["original_c46_4h_parent_index"],
               "source_side":m["side"],"claim":"1H_POI_VALID_FIRST_TEST",
               "polarity":"NEGATIVE","c73_sha256":C73_SHA,"c72_blob_sha1":C72_BLOB,
               "poi_created_ms":m["source_1h_poi_created_at_ms"],
               "original3m_touch_id":m["original_first_source3m_touch_id"],
               "original3m_touch_closed_ms":m["original_first_source3m_touch_closed_ms"],
               "source15m_event_closed_ms":m["first_source15m_event_fully_known_ms"],
               "source5m_event_closed_ms":n["first_any_5m_event_known_ms"],
               "course_route_a_id":COURSE_A,"course_poi_id":POI_COURSE,
               "source_document_url":None,"source_document_sha256":None,
               "author_label_anchor":None,"source_scope":"BINANCE_USDM_ORIGINAL_FROZEN",
               "source_reviewer_attestation":None}
            receipts.append(review(p,m,n))
        self.assertEqual(len(receipts),153)
        self.assertEqual(audit_batch(tuple(receipts))["intake_claims"],153)
    def test_09_missing_first_touch_cannot_claim_positive(self):
        p,m,n=fixture("no_touch","1H_POI_VALID_FIRST_TEST")
        with self.assertRaises(C80Rejected):review(p,m,n)
    def test_10_nothing_authenticates_emulated_author_reference(self):
        p,m,n=fixture()
        p["author_label_anchor"]="I am the course author: VALID"
        self.assertEqual(review(p,m,n).status,"UNVERIFIED_OWNER_LABEL")
    def test_11_spoofed_output_rejected(self):
        p,m,n=fixture()
        z=review(p,m,n)
        with self.assertRaises(C80Rejected):audit_batch((replace(z,entry_allowed=True),))

def mutation(k,v,kind="pattern"):
    def test(self):
        p,m,n=fixture(kind)
        p[k]=v
        with self.assertRaises(C80Rejected):review(p,m,n)
    return test

BAD={
"bad_symbol":("symbol","NOTCRYPTO"),
"bad_context_index":("context_index",-2),
"bool_context_index":("context_index",True),
"bad_side":("source_side","BOTH"),
"bad_claim":("claim","AUTHOR_APPROVED"),
"bad_polarity":("polarity","AUTHOR_VERIFIED"),
"bad_source_scope":("source_scope","BINANCE_SPOT"),
"wrong_C73_sha":("c73_sha256","a"*64),
"wrong_C72_blob":("c72_blob_sha1","a"*40),
"wrong_course_id":("course_route_a_id","unknown"),
"wrong_poi_id":("course_poi_id","unknown"),
"wrong_poi_timestamp":("poi_created_ms",1000000),
"wrong_rawid":("original3m_touch_id","faked"),
"wrong_raw_time":("original3m_touch_closed_ms",123),
"wrong_15m_clock":("source15m_event_closed_ms",123),
"wrong_5m_clock":("source5m_event_closed_ms",123),
"bad_url":("source_document_url","http://example.com"),
"long_url":("source_document_url","https://"+"a"*600),
"bad_doc_sha":("source_document_sha256","notsha"),
"bad_attestation":("source_reviewer_attestation","faked_author"),
"bad_label_anchor":("author_label_anchor",""),
"bad_label_anchor_type":("author_label_anchor",1),
"bad_3m_time_type":("original3m_touch_closed_ms",True),
"bad_15m_time_type":("source15m_event_closed_ms","123"),
"bad_5m_time_type":("source5m_event_closed_ms",True),
"bad_created_time_type":("poi_created_ms",True),
}
for k,(field,value) in BAD.items():setattr(C80,"test_negative_"+k,mutation(field,value))

class C80Tamper(unittest.TestCase):
    def test_missing_field(self):
        p,m,n=fixture()
        del p["claim"]
        with self.assertRaises(C80Rejected):review(p,m,n)
    def test_extra_verified_flag(self):
        p,m,n=fixture()
        p["author_verified"]=True
        with self.assertRaises(C80Rejected):review(p,m,n)
    def test_4h_route_c_not_allowed(self):
        p,m,n=fixture()
        n["route_c_raid_bos_used"]=True
        with self.assertRaises(C80Rejected):review(p,m,n)
    def test_source_status_spoof(self):
        p,m,n=fixture()
        n["readiness"]="READY"
        with self.assertRaises(C80Rejected):review(p,m,n)
    def test_borrow_other_case_source(self):
        p,m,n=fixture()
        m["original_c46_4h_parent_index"]=999
        with self.assertRaises(C80Rejected):review(p,m,n)
    def test_forged_c73_author(self):
        p,m,n=fixture()
        m["author_1h_poi_valid_first_test"]=True
        with self.assertRaises(C80Rejected):review(p,m,n)
    def test_forged_c72_author(self):
        p,m,n=fixture()
        n["author_5m_vc"]=True
        with self.assertRaises(C80Rejected):review(p,m,n)
    def test_none_case_positive_15m_rejected(self):
        p,m,n=fixture("no_touch","15M_TRIGGER")
        with self.assertRaises(C80Rejected):review(p,m,n)
    def test_injected_author_approval_output_rejected(self):
        p,m,n=fixture()
        z=review(p,m,n)
        with self.assertRaises(C80Rejected):audit_batch((replace(z,author_15m_trigger=True),))
    def test_route_mix_batch(self):
        p,m,n=fixture()
        z=review(p,m,n)
        with self.assertRaises(C80Rejected):audit_batch([z])

if __name__=="__main__":unittest.main()
