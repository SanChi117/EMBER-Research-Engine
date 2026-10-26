"""C82 source-only owner review requests: no spoofed course approval."""
import unittest,hashlib
from dataclasses import replace
from pathlib import Path
from c81_source_authenticated_review_queue import build
from c82_independent_owner_media_request import prepare,review_all,C82Rejected

ROOT=Path(__file__).resolve().parents[1]
C73=(ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()
C72=(ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_bytes()
ITEMS=build(C73,C72)
PIN=hashlib.sha256(b"C81_SOURCE_REVIEW_QUEUE_V1").hexdigest()

class TestC82(unittest.TestCase):
    def test_all_153_source_packets_no_author_claims(self):
        q=review_all(ITEMS,pinned_source_sha256=PIN)
        self.assertEqual(len(q),153)
        self.assertEqual([sum(x.priority==k for x in q) for k in (0,1,2,3)],[12,23,71,47])
        self.assertTrue(all(not x.entry_allowed and not x.positive_golden and
                            not x.negative_golden and not x.orders and not x.trades
                            and x.readiness=="NOT_TRADE_READY" for x in q))
    def test_12_P0_have_source_after_parent_and_author_requests(self):
        for x in ITEMS[:12]:
            r=prepare(x,pinned_source_sha256=PIN)
            self.assertEqual(r.chronology_status,"SOURCE_SEQUENCE_ONLY_3M_TO_15M_TO_5M")
            self.assertTrue(any("NEGATIVE" in v for v in r.media_required))
    def test_23_P1_touch_not_golden(self):
        q=[x for x in ITEMS if x.priority==1]
        self.assertEqual(len(q),23)
        self.assertTrue(all(prepare(x,pinned_source_sha256=PIN).chronology_status=="SOURCE_TOUCH_ONLY_NO_CONFIRMED_15M" for x in q))
    def test_71_opposite_ambiguous_not_author_negative(self):
        q=[x for x in ITEMS if x.priority==2]
        self.assertEqual(len(q),71)
        self.assertTrue(all(not prepare(x,pinned_source_sha256=PIN).negative_golden for x in q))
    def test_47_no_new_1h_poi_without_trade(self):
        q=[x for x in ITEMS if x.priority==3]
        self.assertEqual(len(q),47)
        self.assertTrue(all(not prepare(x,pinned_source_sha256=PIN).entry_allowed for x in q))
    def test_bitwise_deterministic(self):
        self.assertEqual(review_all(ITEMS,pinned_source_sha256=PIN),review_all(ITEMS,pinned_source_sha256=PIN))
def bad(mutation,priority=0):
    def run(self):
        x=next(x for x in ITEMS if x.priority==priority)
        with self.assertRaises(C82Rejected):
            prepare(mutation(x),pinned_source_sha256=PIN)
    return run
for label,priority,change in [
 ("fake_author_verified",0,dict(author_verified=True)),
 ("fake_auth_source",0,dict(author_source_authenticated=True)),
 ("fake_entry_allowed",0,dict(entry_allowed=True)),
 ("fake_owner_anchor",0,dict(owner_document_anchor="page 3")),
 ("fake_claim",0,dict(claimed_author_label="VALID")),
 ("fake_reviewer",0,dict(reviewer_attestations=("self",))),
 ("fake_order",0,dict(orders=("BUY",))),
 ("fake_fill",0,dict(fills=("yes",))),
 ("fake_trade",0,dict(trades=("LONG",))),
 ("fake_readiness",0,dict(readiness="READY")),
 ("wrong_source_id",0,dict(source_key="OTHER")),
 ("wrong_priority",0,dict(priority=8)),
 ("future_poi",0,dict(poi_created_ms=9999999999999)),
 ("early_5m",0,dict(first5m_known_ms=1)),
 ("early_15m",0,dict(source15m_known_ms=1)),
 ("bool_visit",0,dict(visits_before_source15m=True)),
 ("no_visit_count",0,dict(visits_before_source15m=None)),
 ("p1_fake_15m",1,dict(source15m_known_ms=123)),
 ("p2_fake_5m",2,dict(first5m_known_ms=123)),
 ("p3_fake_15m",3,dict(source15m_known_ms=123))
]:
    setattr(TestC82,"test_negative_"+label,bad(lambda x,c=change:replace(x,**c),priority))
class TestSourceCorruption(unittest.TestCase):
    def test_unauthorized_pin(self):
        with self.assertRaises(C82Rejected):prepare(ITEMS[0],pinned_source_sha256="a"*64)
    def test_bad_pin(self):
        with self.assertRaises(C82Rejected):prepare(ITEMS[0],pinned_source_sha256="bad")
    def test_fake_record_type(self):
        with self.assertRaises(C82Rejected):prepare(dict(source_key="BTCUSDT/1"),pinned_source_sha256=PIN)
    def test_truncated_source(self):
        with self.assertRaises(C82Rejected):review_all(ITEMS[:12],pinned_source_sha256=PIN)
    def test_duplicate_case(self):
        with self.assertRaises(C82Rejected):review_all((ITEMS[0],)+ITEMS[:-1],pinned_source_sha256=PIN)

if __name__=="__main__":unittest.main()
