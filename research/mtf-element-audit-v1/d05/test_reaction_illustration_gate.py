"""D05/C04 contradiction probes: reaction illustrations cannot self-certify a trade."""
import copy
import json
import pathlib
import unittest

from reaction_illustration_gate import (
    D05ReactionRejected, evaluate_sequence, validate_source_cases
)

ROOT = pathlib.Path(__file__).resolve().parent

def load(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))

class CourseReactionSemantics(unittest.TestCase):
    def setUp(self):
        self.source=load("C04_LEVEL_REACTION_SOURCE_CASES.json")
        self.c02=load("C02_SOURCE_IMAGE_INVENTORY.json")

    def test_source_illustration_manifest_passes_without_market_trade(self):
        x=validate_source_cases(self.source,self.c02)
        self.assertEqual(x["source_level_cases"],8)
        self.assertEqual(x["academic_market_approvals"],0)
        self.assertEqual(x["ready_trade_plans"],0)
        self.assertGreaterEqual(x["negative_derived"],2)

    def test_source_text_qualitative_illustration_no_absolute_bar_time_needed(self):
        s=self.source
        self.assertFalse(s["acceptance"]["uses_absolute_market_timestamps"])
        self.assertFalse(s["acceptance"]["needs_historical_forex_ohlcv_for_illustration_purpose"])

    def test_first_retest_vs_second_retest_not_equivalent(self):
        a=self.source["cases"][2]
        b=self.source["cases"][3]
        self.assertEqual(evaluate_sequence(a["family"],a["events"]),"FIRST_TEST_HAS_COURSE_PRIORITY_NOT_GUARANTEE")
        self.assertEqual(evaluate_sequence(b["family"],b["events"]),"NOT_FIRST_TEST_DO_NOT_MISLABEL")

    def test_weak_mb_not_auto_discarded_as_poilevel(self):
        a=self.source["cases"][1]
        self.assertEqual(evaluate_sequence(a["family"],a["events"]),"MITIGATION_BLOCK_NOT_STRONG_VC")
        self.assertIn("not a ban",a["limits"][0].lower())

    def test_imb_gap_vs_overlapping_wicks(self):
        a=self.source["cases"][4]
        b=self.source["cases"][5]
        self.assertEqual(evaluate_sequence(a["family"],a["events"]),"IMB_CANDIDATE_GEOMETRY_ONLY")
        self.assertEqual(evaluate_sequence(b["family"],b["events"]),"NOT_IMB_THREE_CANDLE_GAP")

    def test_order_of_snr_confirmation_is_not_reversed(self):
        a=self.source["cases"][0]
        broken=list(a["events"])
        broken[2],broken[3]=broken[3],broken[2]
        self.assertEqual(evaluate_sequence("SNR",broken),"NEEDS_SOURCE_SEQUENCE")

    def test_invented_fixed_imb_depth_is_not_source_confirmation(self):
        candidate=["THREE_CANDLES","WICK_GAP_BETWEEN_FIRST_AND_THIRD","MANDATORY_FIFTY_PERCENT_RETRACE"]
        self.assertEqual(evaluate_sequence("IMB",candidate),"NEEDS_SOURCE_GEOMETRY")

    def test_source_image_sha_match_required(self):
        wrong=copy.deepcopy(self.source)
        wrong["figures"][0]["sha256"]="f"*64
        with self.assertRaisesRegex(D05ReactionRejected,"FIGURE_NOT_SHA_LINKED"):
            validate_source_cases(wrong,self.c02)

    def test_futures_execution_gate_cannot_be_waived(self):
        wrong=copy.deepcopy(self.source)
        wrong["separate_automatic_trading_requirement"]="NOT_REQUIRED"
        with self.assertRaisesRegex(D05ReactionRejected,"FUTURES_EXECUTION_GATE_BYPASSED"):
            validate_source_cases(wrong,self.c02)

    def test_cannot_approve_course_chart_as_market_case(self):
        wrong=copy.deepcopy(self.source)
        wrong["acceptance"]["academic_market_patterns_independently_approved"]=1
        with self.assertRaisesRegex(D05ReactionRejected,"UNPROVEN_TRADE"):
            validate_source_cases(wrong,self.c02)

    def test_cannot_infer_trade_plan_from_reaction_figure(self):
        wrong=copy.deepcopy(self.source)
        wrong["acceptance"]["automatic_trade_plans_allowed"]=1
        with self.assertRaisesRegex(D05ReactionRejected,"UNPROVEN_TRADE"):
            validate_source_cases(wrong,self.c02)

    def test_dont_relabel_derived_contrast_as_author_positive(self):
        wrong=copy.deepcopy(self.source)
        wrong["cases"][3]["positive"]=True
        with self.assertRaisesRegex(D05ReactionRejected,"NEGATIVE_NOT_MARKED"):
            validate_source_cases(wrong,self.c02)

    def test_candle_order_conflict_cannot_be_auto_resolved(self):
        wrong=copy.deepcopy(self.source)
        wrong["source_conflicts"][0]["resolution"]="RESOLVED_TRADING_BUYSELL"
        with self.assertRaisesRegex(D05ReactionRejected,"SNR_AMBIGUITY_HIDDEN"):
            validate_source_cases(wrong,self.c02)

    def test_mb_errata_keeps_original_c02_immutable(self):
        errata=self.source["errata"][0]
        images=[x for x in self.c02["items"] if x["id"] in errata["image_ids"]]
        self.assertEqual(len(images),2)
        self.assertTrue(all(x["sha256"] in {f["sha256"] for f in self.source["figures"]} for x in images))
        self.assertIn("Mitigation Block",errata["corrected_subject"])

    def test_no_course_family_without_primary_source(self):
        with self.assertRaisesRegex(D05ReactionRejected,"UNSUPPORTED_COURSE_FAMILY"):
            evaluate_sequence("BOS",["PRICE_TOUCH","REACTION"])

    def test_claim_cannot_disagree_with_trace(self):
        wrong=copy.deepcopy(self.source)
        wrong["cases"][0]["claim"]="STRONG_SNR_AUTOMATIC_TRADE"
        with self.assertRaisesRegex(D05ReactionRejected,"SOURCE_SEQUENCE_VERSUS_CLAIM"):
            validate_source_cases(wrong,self.c02)

if __name__=="__main__":
    unittest.main(verbosity=2)
