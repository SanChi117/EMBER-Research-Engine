"""C87 source-only Route A adapted shadow gate, full crypto + hostile QA."""
import json,unittest
from pathlib import Path
from dataclasses import replace
from c83_owner_course_text_crosswalk import source_matched_queue,C83Rejected
from c87_adapted_route_a_shadow_gate import (
 C87Rejected,AuthorClaim,reject_unverified_claim,classify_all,summarize,
 witness,serialize_witness,audit_witness,POLICY,HOLDOUT_START_MS,
 ALIGNED,OPPOSITE,AMBIGUOUS,_classify)
R=Path(__file__).resolve().parents[1]
A=(R/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()
B=(R/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json").read_bytes()
C=(R/"evidence/c81/C81_FROZEN153_INDEPENDENT_REVIEW_QUEUE_SOURCE_ONLY.json").read_bytes()
D=(R/"evidence/c86/C86_ORIGINAL153_4H_1H_FIRST_TEST_SOURCE_RECEIPTS.json").read_bytes()
Q=source_matched_queue(A,B,C)
Q0=next(x for x in Q if x.priority==0)
Q1=next(x for x in Q if x.priority==1)
Q2=next(x for x in Q if x.priority==2)
Q3=next(x for x in Q if x.priority==3)
C86=json.loads(D)["receipts"]
R0=next(r for r in C86 if r["case_key"]==Q0.source_key)
BASE=AuthorClaim(Q0.source_key)
class TestRealOriginal153(unittest.TestCase):
    def test_01_exact_source_group_counts(self):
        self.assertEqual(summarize(classify_all(A,B,C,D))["priority"],{"0":12,"1":23,"2":71,"3":47})
    def test_02_exact_153_unique(self):
        self.assertEqual(len({r["case_key"] for r in classify_all(A,B,C,D)}),153)
    def test_03_frozen_c86_bytes_required(self):
        with self.assertRaises(C87Rejected):classify_all(A,B,C,D.decode())
    def test_04_c86_tamper_rejected(self):
        with self.assertRaises(Exception):classify_all(A,B,C,D+b"x")
    def test_05_c73_tamper_rejected(self):
        with self.assertRaises(Exception):classify_all(A+b"x",B,C,D)
    def test_06_c72_tamper_rejected(self):
        with self.assertRaises(Exception):classify_all(A,B+b"x",C,D)
    def test_07_c81_tamper_rejected(self):
        with self.assertRaises(Exception):classify_all(A,B,C+b"x",D)
    def test_08_p0_never_author_trigger(self):
        self.assertTrue(all(r["15m_trigger_vs_direct_vc"]=="UNRESOLVED_NOT_OWNER_VERIFIED" for r in classify_all(A,B,C,D) if r["priority"]==0))
    def test_09_p0_5m_never_owner_vc(self):
        self.assertTrue(all(r["5m_volume_confirmation"]=="UNRESOLVED_NOT_OWNER_VERIFIED" for r in classify_all(A,B,C,D) if r["priority"]==0))
    def test_10_all_4h_unknown(self):
        self.assertEqual(sum(r["first_valid_4h_poi_test"]=="UNKNOWN_NOT_PROVEN" for r in classify_all(A,B,C,D)),153)
    def test_11_all_1h_unknown(self):
        self.assertEqual(sum(r["first_valid_1h_poi_test"]=="UNKNOWN_NOT_PROVEN" for r in classify_all(A,B,C,D)),153)
    def test_12_original5m_source_geometry_complete(self):
        expected={"ALIGNED_SOURCE_GEOMETRY_ONLY":4,
                  "OPPOSITE_SOURCE_GEOMETRY":5,
                  "MULTIKIND_AMBIGUOUS_SOURCE_GEOMETRY":3}
        actual={key:sum(r["technical_5m_geometry"]==key for r in classify_all(A,B,C,D)) for key in expected}
        self.assertEqual(actual,expected)
    def test_13_multiple_episode_withheld(self):
        d=classify_all(A,B,C,D)
        self.assertEqual(sum(r["native_source_decision"]=="WITHHOLD_REVISIT_FIRST_VALID_UNPROVEN" for r in d),3)
    def test_14_single_visit_aligned_only_human_review(self):
        d=classify_all(A,B,C,D)
        self.assertTrue(all(r["native_source_decision"]=="PRIORITIZED_FOR_HUMAN_MEDIA_REVIEW_ONLY" for r in d if r["priority"]==0 and r["technical_5m_geometry"]=="ALIGNED_SOURCE_GEOMETRY_ONLY" and Q[[x.source_key for x in Q].index(r["case_key"])].visits_before_source15m==1))
    def test_15_p1_no_source_confirmation(self):
        d=classify_all(A,B,C,D)
        self.assertEqual(sum(r["native_source_decision"]=="WITHHOLD_NO_CLOSED_15M_VC_OR_TRIGGER" for r in d),23)
    def test_16_p2_no_matching_parent(self):
        d=classify_all(A,B,C,D)
        self.assertEqual(sum(r["native_source_decision"]=="WITHHOLD_OPPOSITE_OR_AMBIGUOUS_1H_PARENT" for r in d),71)
    def test_17_p3_no_selected_parent(self):
        d=classify_all(A,B,C,D)
        self.assertEqual(sum(r["native_source_decision"]=="WITHHOLD_NO_SELECTED_NEW_1H_POI" for r in d),47)
    def test_18_no_entries_any(self):
        self.assertTrue(all(r["provisional_entry"] is None and not r["orders"] and not r["trades"] for r in classify_all(A,B,C,D)))
    def test_19_no_pnl_claim(self):
        self.assertIs(summarize(classify_all(A,B,C,D))["paper_profit_metrics_valid"],False)
    def test_20_cover_partitions_not_pnl_oos(self):
        self.assertEqual(sum(summarize(classify_all(A,B,C,D))["source_coverage"].values()),153)
    def test_21_determinism(self):
        self.assertEqual(serialize_witness(A,B,C,D),serialize_witness(A,B,C,D))
    def test_22_witness_regeneration(self):
        data=serialize_witness(A,B,C,D)
        self.assertEqual(audit_witness(A,B,C,D,data)["source_contexts"],153)
    def test_23_witness_tamper(self):
        with self.assertRaises(C87Rejected):audit_witness(A,B,C,D,serialize_witness(A,B,C,D)+b"x")
    def test_24_author_separation(self):
        self.assertEqual(summarize(classify_all(A,B,C,D))["positive_owner_goldens"],0)
    def test_25_policy_hypothesis(self):
        self.assertEqual(POLICY["evidence_class"],"ADAPTED_HYPOTHESIS")
    def test_26_policy_owner_source_link(self):
        self.assertTrue(POLICY["owner_text_drive_id"])
    def test_27_policy_route_b_isolated(self):
        self.assertEqual(POLICY["route"],"A")
        self.assertTrue(POLICY["route_b_exclusion_drive_id"])
    def test_28_summary_manual_forged(self):
        r=classify_all(A,B,C,D);r[0]["provisional_entry"]="0.001"
        with self.assertRaises(C87Rejected):summarize(r)
    def test_29_summary_forged_author_positive(self):
        r=classify_all(A,B,C,D);r[0]["certified_author_positive"]=True
        with self.assertRaises(C87Rejected):summarize(r)
    def test_30_summary_forged_trade(self):
        r=classify_all(A,B,C,D);r[0]["trades"]=[123]
        with self.assertRaises(C87Rejected):summarize(r)
    def test_31_summary_forged_timing_semantics(self):
        r=classify_all(A,B,C,D);r[0]["first_valid_4h_poi_test"]="VALID"
        with self.assertRaises(C87Rejected):summarize(r)
    def test_32_source_case_duplicate(self):
        r=classify_all(A,B,C,D);r[0]["case_key"]=r[1]["case_key"]
        with self.assertRaises(C87Rejected):summarize(r)
    def test_33_ambiguous_15m_never_direct_vc(self):
        self.assertTrue(all(r["15m_trigger_vs_direct_vc"]!="DIRECT_15M_VC" for r in classify_all(A,B,C,D)))
    def test_34_source_cases_never_author_evidence(self):
        self.assertTrue(all(r["evidence_class"]=="ADAPTED_HYPOTHESIS" for r in classify_all(A,B,C,D)))
    def test_35_coverage_is_not_optimization(self):
        self.assertEqual(HOLDOUT_START_MS,1789862400000)
    def test_36_original_source_immutability(self):
        self.assertEqual(len(json.loads(D)["receipts"]),153)
    def test_37_direct_claim_quarantine(self):
        self.assertFalse(reject_unverified_claim(BASE)["entry_allowed"])
    def test_38_negative_claim_self_attestation(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,claimed_owner_negative=True))
    def test_39_positive_claim_self_attestation(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,claimed_owner_positive=True))
    def test_40_4h_source_index_not_author(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,claimed_parent_4h_valid=True))
    def test_41_1h_touch_not_valid_author(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,claimed_first_1h_valid=True))
    def test_42_5m_technical_not_owner_vc(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,claimed_5m_vc=True))
    def test_43_15m_trigger_claim_rejected(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,claimed_15m_trigger=True))
    def test_44_15m_direct_vc_claim_rejected(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,claimed_direct_15m_vc=True))
    def test_45_route_b_rejected(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,claimed_route="B"))
    def test_46_route_c_rejected(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,claimed_route="C"))
    def test_47_proposed_entry_forbidden(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,proposed_entry="100"))
    def test_48_proposed_sl_forbidden(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,proposed_sl="100"))
    def test_49_proposed_tp_forbidden(self):
        with self.assertRaises(C87Rejected):
            reject_unverified_claim(replace(BASE,proposed_tp="100"))
    def test_50_invalid_evidence_state_mutation(self):
        r=json.loads(D)["receipts"]
        a=next(z for z in r if z["case_key"]==Q0.source_key)
        a["4h_author_valid_first_test"]="OWNER_VALID"
        with self.assertRaises(C87Rejected):_classify(a,Q0)
    def test_51_unknown_5m_enum(self):
        with self.assertRaises(C87Rejected):
            _classify(R0,replace(Q0,first5m_kind="AUTHOR_VC"))
    def test_52_source_3m_to_5m_future(self):
        with self.assertRaises(C87Rejected):
            _classify(R0,replace(Q0,first5m_known_ms=Q0.source15m_known_ms-1))
    def test_53_source_zero_visits(self):
        with self.assertRaises(C87Rejected):
            _classify(R0,replace(Q0,visits_before_source15m=0))
    def test_54_source_nonmatching_case(self):
        with self.assertRaises(C87Rejected):
            _classify(R0,Q1)
    def test_55_author_4h_positive_source_spoof(self):
        with self.assertRaises(C87Rejected):
            _classify({**R0,"author_positive_golden":True},Q0)
    def test_56_author_1h_negative_source_spoof(self):
        with self.assertRaises(C87Rejected):
            _classify({**R0,"author_negative_golden":True},Q0)
    def test_57_source_entry_spoof(self):
        with self.assertRaises(C87Rejected):
            _classify({**R0,"orders":["FAKE"]},Q0)
    def test_58_total_priority_physical_nontrades(self):
        r=classify_all(A,B,C,D)
        self.assertEqual(sum(x["first_physical_1h_contact"] for x in r if x["priority"]==3),23)
    def test_59_source_5m_earlier_than_15m(self):
        with self.assertRaises(C87Rejected):
            _classify(R0,replace(Q0,first5m_known_ms=Q0.source15m_known_ms))
    def test_60_source_same_time_first3m(self):
        with self.assertRaises(C87Rejected):
            _classify(R0,replace(Q0,source15m_known_ms=Q0.first_original_3m_close_ms))
if __name__=="__main__":unittest.main()
