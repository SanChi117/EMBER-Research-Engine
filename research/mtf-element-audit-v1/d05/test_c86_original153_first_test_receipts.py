"""C86 independent source-pinned 4H/1H first-test provenance adversarial tests."""
from dataclasses import replace
from pathlib import Path
import json,unittest
from c83_owner_course_text_crosswalk import source_matched_queue,C83Rejected
from c86_original153_first_test_receipts import (
 C86Rejected,receipt,inspect_all,summarize,serialize_receipts,audit_stored_bytes,PROOF_GAPS,COURSE_ANCHORS)
ROOT=Path(__file__).resolve().parents[1]
A=(ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()
B=(ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_bytes()
C=(ROOT/"evidence/c81/C81_FROZEN153_INDEPENDENT_REVIEW_QUEUE_SOURCE_ONLY.json").read_bytes()
Q=source_matched_queue(A,B,C)
P={p:next(x for x in Q if x.priority==p) for p in (0,1,2,3)}
RAW_P3=next((x for x in Q if x.priority==3 and x.first_original_3m_id is not None),None)
class TestOriginalSourceAndReceipts(unittest.TestCase):
    def test_01_receipts_full_153(self):
        self.assertEqual(len(inspect_all(A,B,C)),153)
    def test_02_categories_unmodified(self):
        self.assertEqual(summarize(inspect_all(A,B,C))["priority_counts"],{"0":12,"1":23,"2":71,"3":47})
    def test_03_all_research_paper(self):
        self.assertTrue(all(x["readiness"]=="NOT_TRADE_READY" and
          x["author_positive_golden"] is False and x["author_negative_golden"] is False and
          not x["orders"] and not x["trades"] for x in inspect_all(A,B,C)))
    def test_04_first_4h_author_test_unknown(self):
        self.assertTrue(all(x["4h_author_valid_first_test"]=="UNKNOWN_NOT_PROVEN" for x in inspect_all(A,B,C)))
    def test_05_first_1h_author_test_unknown(self):
        self.assertTrue(all(x["1h_author_valid_first_test"]=="UNKNOWN_NOT_PROVEN" for x in inspect_all(A,B,C)))
    def test_06_c46_parent_is_index_not_author_test(self):
        self.assertTrue(all(x["4h_parent_source_status"]=="C46_TECHNICAL_INDEX_ONLY_NO_AUTHOR_FIRST_TEST" for x in inspect_all(A,B,C)))
    def test_07_raw3m_closure_proven_not_valid_test(self):
        r=receipt(P[0])
        self.assertEqual(r["raw_native_3m"]["native_closed_ms"]-r["raw_native_3m"]["native_open_ms"],180000)
        self.assertIn("NOT_OWNER_VALID",r["raw_native_3m"]["observation"])
    def test_08_p0_multiple_visits_are_not_promoted(self):
        r=inspect_all(A,B,C)
        self.assertEqual(sorted(x["physical_episode_count_before_source15m"] for x in r if x["priority"]==0),[1]*9+[2,2,4])
        self.assertTrue(all(x["1h_author_valid_first_test"]=="UNKNOWN_NOT_PROVEN" for x in r if x["physical_episode_count_before_source15m"] in (2,4)))
    def test_09_selected_with_3m_first_contact_not_author(self):
        r=inspect_all(A,B,C)
        self.assertEqual(sum(x["raw_native_3m"] is not None for x in r if x["priority"] in (0,1)),35)
        self.assertEqual(sum(x["author_positive_golden"] for x in r),0)
    def test_10_p1_has_no_15m_5m(self):
        self.assertEqual(sum(x["priority"]==1 and x["15m_source_known_ms"] is None and x["5m_source_known_ms"] is None for x in inspect_all(A,B,C)),23)
    def test_11_p2_unselected_not_certified(self):
        self.assertTrue(all(x["1h_author_valid_first_test"]=="UNKNOWN_NOT_PROVEN" for x in inspect_all(A,B,C) if x["priority"]==2))
    def test_12_p3_zero_new_poi_not_all_negative_goldens(self):
        self.assertTrue(all(x["1h_poi_source"] is None and x["author_negative_golden"] is False for x in inspect_all(A,B,C) if x["priority"]==3))
    def test_13_orphan_raw3m_technical_in_p3(self):
        self.assertIsNotNone(RAW_P3)
        self.assertEqual(receipt(RAW_P3)["physical_visit_class"],"NO_SELECTED_POI_RAW3M_EXISTS")
    def test_14_each_receipt_has_original_case_key(self):
        self.assertEqual([x["case_key"] for x in inspect_all(A,B,C)],[x.source_key for x in Q])
    def test_15_real_course_anchor_proof_gaps(self):
        self.assertEqual(len(COURSE_ANCHORS),5)
        self.assertTrue(all(len(r["missing_owner_proofs"])==len(PROOF_GAPS) for r in inspect_all(A,B,C)))
    def test_16_replay_deterministic(self):
        self.assertEqual(serialize_receipts(A,B,C),serialize_receipts(A,B,C))
    def test_17_forged_c73_source_bytes(self):
        with self.assertRaises(C83Rejected):inspect_all(A+b"x",B,C)
    def test_18_forged_c72_source_bytes(self):
        with self.assertRaises(C83Rejected):inspect_all(A,B+b"x",C)
    def test_19_forged_c81_source_bytes(self):
        with self.assertRaises(C83Rejected):inspect_all(A,B,C+b"x")
    def test_20_forged_native5m_source_time_from_c81(self):
        q=json.loads(C);q[0]["first5m_known_ms"]=q[0]["source15m_known_ms"]-1
        with self.assertRaises(C83Rejected):inspect_all(A,B,json.dumps(q).encode())
    def test_21_forced_golden_receipt_blocked(self):
        r=inspect_all(A,B,C)
        r[0]["4h_author_valid_first_test"]="AUTHOR_VERIFIED"
        with self.assertRaises(C86Rejected):summarize(r)
    def test_22_counterfeit_negative_golden_receipt_blocked(self):
        r=inspect_all(A,B,C)
        r[0]["author_negative_golden"]=True
        with self.assertRaises(C86Rejected):summarize(r)
    def test_23_fake_trade_in_receipt_blocked(self):
        r=inspect_all(A,B,C);r[0]["orders"]=["BUY"]
        with self.assertRaises(C86Rejected):summarize(r)
    def test_24_receipt_byte_readback_rejects_tamper(self):
        data=serialize_receipts(A,B,C)
        with self.assertRaises(C86Rejected):
            audit_stored_bytes(A,B,C,data+b"x")
    def test_25_receipt_byte_readback_valid(self):
        z=audit_stored_bytes(A,B,C,serialize_receipts(A,B,C))
        self.assertEqual(z["cases"],153)
    def test_26_wrong_source_count(self):
        x=inspect_all(A,B,C)[1:]
        with self.assertRaises(C86Rejected):summarize(x)
    def test_27_source_15m_never_promoted_to_author(self):
        self.assertTrue(all(x["15m_author_trigger_or_vc"]=="UNKNOWN_NOT_PROVEN" for x in inspect_all(A,B,C)))
    def test_28_full_receipt_provenance_no_missing_owner_media_invention(self):
        d=json.loads(serialize_receipts(A,B,C))
        self.assertEqual(d["summary"]["4h_author_first_valid_test_count"],0)
        self.assertEqual(d["summary"]["1h_author_first_valid_test_count"],0)
        self.assertTrue(all(x["4h_source_first_valid_test_closed_ms"] is None for x in d["receipts"]))
def _negative(changes,p=0):
    def do(self):
        with self.assertRaises(C86Rejected):receipt(replace(P[p],**changes))
    return do
NEG={
"spoofed_author_verified":(0,dict(author_verified=True)),
"spoofed_author_authenticated":(0,dict(author_source_authenticated=True)),
"spoofed_owner_anchor":(0,dict(owner_document_anchor="fake-owner")),
"spoofed_author_label":(0,dict(claimed_author_label="VALID_POI")),
"spoofed_review":(0,dict(reviewer_attestations=("reviewed",))),
"spoofed_order":(0,dict(orders=("BUY",))),
"spoofed_fill":(0,dict(fills=("FAKE",))),
"spoofed_trade":(0,dict(trades=("FAKE",))),
"spoofed_entry":(0,dict(entry_allowed=True)),
"spoofed_readiness":(0,dict(readiness="READY")),
"wrong_side":(0,dict(side="FLAT")),
"wrong_case_key":(0,dict(source_key="BTCUSDT/-1")),
"boolean_parent_index":(0,dict(index=True)),
"bad_source_kind":(0,dict(poi_kind="1H_FAKE")),
"inverted_zone":(0,dict(poi_low="999999999",poi_high="0")),
"nan_zone":(0,dict(poi_low="NaN")),
"bad_3m_id":(0,dict(first_original_3m_id="fake:1234")),
"3m_id_missing":(0,dict(first_original_3m_id=None)),
"3m_id_without_close":(0,dict(first_original_3m_close_ms=None)),
"3m_wrong_bar_close":(0,dict(first_original_3m_close_ms=1790000000000)),
"3m_before_1h_created":(0,dict(first_original_3m_close_ms=1)),
"1h_future_creation":(0,dict(poi_created_ms=1799999999999)),
"source15m_earlier":(0,dict(source15m_known_ms=1)),
"source5m_earlier":(0,dict(first5m_known_ms=1)),
"source15m_wrong_grid":(0,dict(source15m_known_ms=P[0].source15m_known_ms+1)),
"source5m_wrong_grid":(0,dict(first5m_known_ms=P[0].first5m_known_ms+1)),
"bool_visit_count":(0,dict(visits_before_source15m=True)),
"zero_visit_count":(0,dict(visits_before_source15m=0)),
"p1_future_15m":(1,dict(source15m_known_ms=P[0].source15m_known_ms)),
"p2_fake_touch":(2,dict(first_original_3m_id=P[0].first_original_3m_id,first_original_3m_close_ms=P[0].first_original_3m_close_ms)),
"p3_fake_parent":(3,dict(poi_kind="1H_NEW_VC_RB_SOURCE")),
"p3_ghost_creation":(3,dict(poi_created_ms=1790000000000)),
"p3_future_15m":(3,dict(source15m_known_ms=1790000000000)),
}
for key,(priority,changes) in NEG.items():
    setattr(TestOriginalSourceAndReceipts,"test_negative_"+key,_negative(changes,priority))
if __name__=="__main__":unittest.main()
