"""C83 real frozen source P0 crosswalk; all negatives fail closed."""
from dataclasses import replace
from dataclasses import asdict
from pathlib import Path
import json,unittest
from c83_owner_course_text_crosswalk import (
    source_matched_queue,make_p0,inspect_all,C83Rejected,COURSE_CITATIONS,
)
ROOT=Path(__file__).resolve().parents[1]
a=(ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()
b=(ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_bytes()
c=(ROOT/"evidence/c81/C81_FROZEN153_INDEPENDENT_REVIEW_QUEUE_SOURCE_ONLY.json").read_bytes()
Q=source_matched_queue(a,b,c)
P0=tuple(x for x in Q if x.priority==0)
class TestC83Crosswalk(unittest.TestCase):
    def test_01_full_p0_and_all_source(self):
        out,summary=inspect_all(a,b,c)
        self.assertEqual(len(out),12)
        self.assertEqual(summary["source_total_contexts"],153)
        self.assertEqual(summary["entries_allowed"],0)
        self.assertEqual(summary["author_crypto_timestamp_labels_verified"],0)
    def test_02_all_keys_unique_and_source_provenance(self):
        out,_=inspect_all(a,b,c)
        self.assertEqual(len({x.case_key for x in out}),12)
        self.assertEqual(tuple(x.case_key for x in out),tuple(x.source_key for x in P0))
    def test_03_15m_half_imb_half_snr(self):
        _,out=inspect_all(a,b,c)
        self.assertEqual(out["15m_geometries"],{"IMB":6,"SNR":6})
    def test_04_5m_aligned_4_opposite_5_ambiguous_3(self):
        _,out=inspect_all(a,b,c)
        self.assertEqual(out["5m_geometries"],{
            "MULTIPLE_KINDS_AMBIGUOUS":3,
            "OPPOSITE_SIDE_GEOMETRY":5,
            "SAME_SIDE_GEOMETRY":4})
    def test_05_1h_RB_9_SNR_3(self):
        _,out=inspect_all(a,b,c)
        self.assertEqual(out["poi_kind"],{
            "1H_NEW_VC_RB_SOURCE":9,"1H_NEW_VC_SNR_SOURCE":3})
    def test_06_repeat_visits_still_unverified(self):
        rows,_=inspect_all(a,b,c)
        self.assertEqual(sorted(x.physical_visit_episodes for x in rows),
                         [1]*9+[2]*2+[4])
        self.assertTrue(all("OWNER_CONFIRM_NO_REVISIT_AS_FIRST_VALID_TEST" in x.next_required_proof
                            for x in rows if x.physical_visit_episodes>1))
    def test_07_reject_aligned_geometry_as_author_vc(self):
        rows,_=inspect_all(a,b,c)
        self.assertTrue(all(x.author_5m_vc is False for x in rows))
        self.assertTrue(all(x.exact_course_media_timestamp_attested is False for x in rows))
        self.assertTrue(all(x.readiness=="NOT_TRADE_READY" and not x.entry_allowed
                            and not x.orders and not x.trades for x in rows))
    def test_08_course_anchors_not_fabricated_timestamp_goldens(self):
        self.assertEqual(len(COURSE_CITATIONS),7)
        rows,_=inspect_all(a,b,c)
        self.assertTrue(all("1H_FIRST_TEST" in x.course_rule_anchors and
                            "NO_TRIGGER_DIRECT_15M_VC" in x.course_rule_anchors for x in rows))
    def test_09_deterministic(self):
        self.assertEqual(inspect_all(a,b,c),inspect_all(a,b,c))

def tamper(change):
    def run(self):
        with self.assertRaises(C83Rejected):
            make_p0(replace(P0[0],**change))
    return run
NEG={
"fake_author_verified":dict(author_verified=True),
"fake_authenticated_source":dict(author_source_authenticated=True),
"fake_author_label":dict(claimed_author_label="VALID_FIRST_POI_TEST"),
"fake_anchor":dict(owner_document_anchor="author:page2"),
"fake_review":dict(reviewer_attestations=("done",)),
"fake_trade":dict(trades=("TRADE",)),
"fake_order":dict(orders=("BUY",)),
"fake_fill":dict(fills=("YES",)),
"fake_entry_allowed":dict(entry_allowed=True),
"fake_readiness":dict(readiness="READY"),
"fake_3m_before_poi":dict(first_original_3m_close_ms=1),
"fake_15m_before_3m":dict(source15m_known_ms=1),
"fake_5m_before_15m":dict(first5m_known_ms=1),
"bad_episode":dict(visits_before_source15m=0),
"boolean_episode":dict(visits_before_source15m=True),
"unsupported_poi_kind":dict(poi_kind="CUSTOM"),
"unsupported_15m_kind":dict(source15m_kind="AUTHOR_VC"),
"unsupported_5m_kind":dict(first5m_kind="AUTHOR_VC"),
"wrong_source_key":dict(source_key="FAKE/1"),
"wrong_priority":dict(priority=2),
}
for name,change in NEG.items():
    setattr(TestC83Crosswalk,"test_negative_"+name,tamper(change))
class TestWholeSourceTamper(unittest.TestCase):
    def test_changed_original_C73_byte(self):
        with self.assertRaises(C83Rejected):source_matched_queue(a+b"x",b,c)
    def test_changed_original_C72_byte(self):
        with self.assertRaises(C83Rejected):source_matched_queue(a,b+b"x",c)
    def test_changed_C81_source_json(self):
        fake=json.loads(c)
        fake[0]["author_verified"]=True
        with self.assertRaises(C83Rejected):
            source_matched_queue(a,b,json.dumps(fake).encode())
    def test_removed_one_C81_item(self):
        fake=json.loads(c)[1:]
        with self.assertRaises(C83Rejected):source_matched_queue(a,b,json.dumps(fake).encode())
    def test_invalid_C81_source_json(self):
        with self.assertRaises(C83Rejected):source_matched_queue(a,b,b"not-json")
    def test_queue_item_not_p0(self):
        x=next(q for q in Q if q.priority==1)
        with self.assertRaises(C83Rejected):make_p0(x)
if __name__=="__main__":unittest.main()
