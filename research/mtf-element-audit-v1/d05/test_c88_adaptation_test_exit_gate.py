"""C88 final engineering-complete vs semantic-unverified adaptation test gates."""
import unittest,json
from pathlib import Path
from c88_adaptation_test_exit_gate import (
 C88Rejected,acceptance,serialize_acceptance,check_frozen_acceptance,
 RELEASE_CONTRACT,GATES)
R=Path(__file__).resolve().parents[1]
FILES=[
 "evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json",
 "evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json",
 "evidence/c81/C81_FROZEN153_INDEPENDENT_REVIEW_QUEUE_SOURCE_ONLY.json",
 "evidence/c86/C86_ORIGINAL153_4H_1H_FIRST_TEST_SOURCE_RECEIPTS.json",
 "evidence/c87/C87_ADAPTED_ROUTE_A_ORIGINAL153_SHADOW_WITNESS.json",
 "evidence/c85/C85_ACADEMY_TEXT_ORIGINAL153_WITNESS.json"
]
DATA=tuple((R/p).read_bytes() for p in FILES)
class TestAdaptationExit(unittest.TestCase):
 def test_01_schema(self):
  self.assertEqual(acceptance(*DATA)["schema"],"C88_ROUTE_A_ADAPTATION_TEST_EXIT_V1")
 def test_02_source_count(self):
  self.assertEqual(acceptance(*DATA)["source_archive"]["source_contexts"],153)
 def test_03_no_claim_of_oos_profit(self):
  x=acceptance(*DATA);self.assertFalse(x["contract"]["profit_metrics_supported"]);self.assertIsNone(x["pnl"])
 def test_04_no_real_entry(self):
  x=acceptance(*DATA);self.assertFalse(x["contract"]["allowed_to_emit_trade_signal"])
 def test_05_no_real_orders(self):
  x=acceptance(*DATA);self.assertFalse(x["contract"]["allowed_to_route_orders"])
 def test_06_owner_goldens_still_missing(self):
  x=acceptance(*DATA);self.assertEqual(x["gates"]["SIGNED_POSITIVE_AND_NEGATIVE_CRYPTO_GOLDENS"],"BLOCKED_MISSING")
 def test_07_first_valid_poi_gate(self):
  x=acceptance(*DATA);self.assertEqual(x["gates"]["FIRST_VALID_4H_1H_OWNER_POI_TESTS"],"BLOCKED_UNVERIFIED")
 def test_08_15m_vc_gate(self):
  x=acceptance(*DATA);self.assertEqual(x["gates"]["LTF_15M_TRIGGER_OR_DIRECT_VC_AUTHOR_PROOF"],"BLOCKED_UNVERIFIED")
 def test_09_5m_vc_gate(self):
  x=acceptance(*DATA);self.assertEqual(x["gates"]["REAL_5M_OWNER_VC"],"BLOCKED_UNVERIFIED")
 def test_10_actual_3_priority_media_review_only(self):
  x=acceptance(*DATA);self.assertEqual(x["original_source_summary"]["decisions"]["PRIORITIZED_FOR_HUMAN_MEDIA_REVIEW_ONLY"],3)
 def test_11_actual_revisits(self):
  x=acceptance(*DATA);self.assertEqual(x["original_source_summary"]["decisions"]["WITHHOLD_REVISIT_FIRST_VALID_UNPROVEN"],3)
 def test_12_actual_153_coverage(self):
  x=acceptance(*DATA);self.assertEqual(sum(x["original_source_summary"]["source_coverage"].values()),153)
 def test_13_60_late_cases_not_proof_of_profit(self):
  x=acceptance(*DATA);self.assertEqual(x["original_source_summary"]["source_coverage"]["COVERAGE_LATE"],60)
  self.assertIn("not an OOS trading performance test",x["verification_note"])
 def test_14_no_entries_in_archive(self):
  x=acceptance(*DATA);self.assertEqual(x["original_source_summary"]["entries"],0)
 def test_15_readiness_block(self):
  self.assertEqual(acceptance(*DATA)["readiness"],"NOT_TRADE_READY")
 def test_16_bytes_deterministic(self):
  self.assertEqual(serialize_acceptance(*DATA),serialize_acceptance(*DATA))
 def test_17_self_archive_check(self):
  x=serialize_acceptance(*DATA);self.assertEqual(check_frozen_acceptance(*DATA,x)["bytes"],len(x))
 def test_18_tamper_archive_check(self):
  with self.assertRaises(C88Rejected):check_frozen_acceptance(*DATA,serialize_acceptance(*DATA)+b"!")
 def test_19_mutated_C85_text_claim(self):
  lst=list(DATA);lst[5]=lst[5]+b"x"
  with self.assertRaises(C88Rejected):acceptance(*lst)
 def test_20_mutated_C86_receipt(self):
  lst=list(DATA);lst[3]=lst[3]+b"x"
  with self.assertRaises(Exception):acceptance(*lst)
 def test_21_mutated_C87_shadow(self):
  lst=list(DATA);lst[4]=lst[4]+b"x"
  with self.assertRaises(Exception):acceptance(*lst)
 def test_22_mutated_C81_queue(self):
  lst=list(DATA);lst[2]=lst[2]+b"x"
  with self.assertRaises(Exception):acceptance(*lst)
 def test_23_mutated_C73_original(self):
  lst=list(DATA);lst[0]=lst[0]+b"x"
  with self.assertRaises(Exception):acceptance(*lst)
 def test_24_mutated_C72_original(self):
  lst=list(DATA);lst[1]=lst[1]+b"x"
  with self.assertRaises(Exception):acceptance(*lst)
 def test_25_no_b_or_c_route_merging(self):
  x=acceptance(*DATA);self.assertEqual(x["contract"]["research_route"],"A")
 def test_26_no_trade_controls_enforced(self):
  x=acceptance(*DATA);self.assertFalse(x["contract"]["allowed_to_autotrade"]);self.assertFalse(x["contract"]["allowed_to_choose_entry_sl_tp"])
 def test_27_required_authentic_source(self):
  x=acceptance(*DATA);self.assertTrue(x["contract"]["requires_owner_positive_and_negative_media"])
 def test_28_orig_5m_not_author(self):
  x=acceptance(*DATA);self.assertEqual(x["original_source_summary"]["positive_owner_goldens"],0)
 def test_29_time_partition_no_signal(self):
  x=acceptance(*DATA);self.assertEqual(x["original_source_summary"]["source_coverage"]["UNRESOLVED_SOURCE_TIME"],24)
 def test_30_completion_only_research(self):
  x=acceptance(*DATA);self.assertEqual(x["exit_status"],"ENGINEERING_COMPLETE_ACADEMIC_SEMANTIC_UNVERIFIED")
if __name__=="__main__":unittest.main()
