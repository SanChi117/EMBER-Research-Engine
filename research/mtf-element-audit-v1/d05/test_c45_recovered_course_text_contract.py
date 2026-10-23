"""C45 independent positive TEXT-consistency and negative author-claim gates.

All positives are handcrafted text-rule synthetic cases, NOT approved trades.
"""
import unittest
from dataclasses import replace
from c45_recovered_course_text_contract import (
    recovered_text_claims,CourseContextCase,evaluate_text_contract,
    source_only_c44_compatibility,TEXT_ROUTE_MODES)

def route_a():
    return CourseContextCase(
        mode="A_4H_TRIGGER_15M_VC",context_kind="IMB",context_tf="4H",
        context_is_tested=True,verified_typed_poi_source=True,
        context_source_kind="ACADEMIC_TYPED_POI",
        trigger_tf="1H",trigger_kind="BSL",
        volume_confirmation_tf="15M",volume_confirmation_kind="SNR",
        entry_tf="15M",target_tf="4H",target_kind="FTA",
        stop_kind="BEHIND_STRONG_HIGH_LOW",confirmed_strong_hl=True)

def route_b():
    return replace(route_a(),mode="B_4H_VC_1H_IDM",
        trigger_tf="1H",trigger_kind="IDM",
        volume_confirmation_tf=None,volume_confirmation_kind=None,
        entry_tf="1H",direct_idm_within_or_ahead_poi=True)

def route_c():
    return replace(route_a(),mode="C_1H_RAID_3M_BOS",
        context_kind="LIQUIDITY",context_tf="1H",
        context_is_tested=False,verified_typed_poi_source=False,
        context_source_kind="1H_CLOSED_LIQUIDITY_FRACTAL",
        trigger_tf="3M",trigger_kind="3M_BOS",
        volume_confirmation_tf=None,volume_confirmation_kind=None,
        entry_tf="3M",target_tf="1H",target_kind="EQL",
        stop_kind="BEHIND_RAIDED_LIQUIDITY",confirmed_strong_hl=False,
        raid_wick=True,bos_position="BELOW_BSL_RAID",raid_kind="BSL")

def c44_context():
    return {"original_bos_3m_row_id":"native",
        "source_reaction_confirmed":True,"decisions":(),
        "original_bos_start_ms":123456789,
        "original_bos_closed_ms":123456789+180000,
        "orders":(),"trades":(),"readiness":"NOT_TRADE_READY"}

class C45AuthorCourseContractTests(unittest.TestCase):
    def assertBlocked(self,c,reason):
        x=evaluate_text_contract(c)
        self.assertFalse(x.text_only_rule_consistent)
        self.assertIn(reason,x.blockers)
        self.assertFalse(x.author_chart_golden_verified or x.source_trade_ready)
        self.assertEqual((x.orders,x.trades),((),()))
        self.assertEqual(x.readiness,"NOT_TRADE_READY")

    def test_recovered_nine_actual_drive_files(self):
        self.assertEqual(len({v["file"] for v in recovered_text_claims().values()}),9)
    def test_recovered_seventeen_text_claims(self):
        self.assertEqual(len(recovered_text_claims()),17)
    def test_route_modes_are_eight_named_variants(self):
        self.assertEqual(len(TEXT_ROUTE_MODES),8)
    def test_positive_route_a_4h_1h_15m_text_contract(self):
        x=evaluate_text_contract(route_a())
        self.assertTrue(x.text_only_rule_consistent)
        self.assertEqual(x.blockers,())
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_positive_route_a_4h_no_trigger_wait_only(self):
        x=evaluate_text_contract(replace(route_a(),mode="A_4H_NO_TRIGGER_1H_VC",
            trigger_tf=None,trigger_kind=None,volume_confirmation_tf="1H",
            volume_confirmation_kind="RB" if False else "SNR",
            entry_tf=None))
        self.assertTrue(x.text_only_rule_consistent)
        self.assertEqual(x.orders,())
    def test_positive_4h_no_trigger_1h_rb_context_vc(self):
        x=evaluate_text_contract(replace(route_a(),mode="A_4H_NO_TRIGGER_1H_VC",
            trigger_tf=None,trigger_kind=None,volume_confirmation_tf="1H",
            volume_confirmation_kind="RB",entry_tf=None))
        self.assertTrue(x.text_only_rule_consistent)
        self.assertFalse(x.source_trade_ready)

    def test_positive_route_a_1h_15m_5m_text_contract(self):
        x=evaluate_text_contract(replace(route_a(),mode="A_1H_TRIGGER_5M_VC",
            context_tf="1H",trigger_tf="15M",trigger_kind="SSL",
            volume_confirmation_tf="5M",entry_tf="5M",target_tf="1H"))
        self.assertTrue(x.text_only_rule_consistent)
    def test_positive_route_a_1h_no_trigger_15m_vc(self):
        x=evaluate_text_contract(replace(route_a(),mode="A_1H_NO_TRIGGER_15M_VC",
            context_tf="1H",trigger_tf=None,trigger_kind=None,target_tf="1H"))
        self.assertTrue(x.text_only_rule_consistent)
    def test_positive_route_b_4h_context_idm(self):
        self.assertTrue(evaluate_text_contract(route_b()).text_only_rule_consistent)
    def test_positive_route_b_1h_context_idm(self):
        x=evaluate_text_contract(replace(route_b(),mode="B_1H_VC_15M_IDM",
            context_tf="1H",trigger_tf="15M",entry_tf="15M",target_tf="1H"))
        self.assertTrue(x.text_only_rule_consistent)
    def test_positive_route_c_wick_1h_3m_bos_text(self):
        self.assertTrue(evaluate_text_contract(route_c()).text_only_rule_consistent)
    def test_positive_route_c_wick_1h_5m_bos_text(self):
        x=evaluate_text_contract(replace(route_c(),mode="C_1H_RAID_5M_BOS",
            trigger_tf="5M",trigger_kind="5M_BOS",entry_tf="5M"))
        self.assertTrue(x.text_only_rule_consistent)
    def test_route_a_no_poi_test_fails(self):
        self.assertBlocked(replace(route_a(),context_is_tested=False),
            "C45_PRIOR_TYPED_POI_TEST_NOT_EVIDENCED")
    def test_route_a_not_verified_typed_poi_fails(self):
        self.assertBlocked(replace(route_a(),verified_typed_poi_source=False),
            "C45_ADAPTED_CANDLE_RANGE_NOT_AUTHOR_POI")
    def test_previous_c44_closed_range_cannot_become_author_poi(self):
        self.assertBlocked(replace(route_a(),context_source_kind="C44_PRIOR_CLOSED_4H_RANGE_PROXY"),
            "C45_ADAPTED_CANDLE_RANGE_NOT_AUTHOR_POI")
    def test_liquidity_zone_not_bare_range(self):
        self.assertBlocked(replace(route_a(),context_kind="PREVIOUS_CLOSED_4H_RANGE"),
            "C45_CONTEXT_PAIRED_POI_TIMEFRAME_OR_TYPE_MISSING")
    def test_route_a_wrong_timeframe_target_fails(self):
        self.assertBlocked(replace(route_a(),target_tf="1H"),
            "C45_FTA_WRONG_PARENT_TIMEFRAME")
    def test_route_a_entry_vc_rejection_block_not_valid(self):
        self.assertBlocked(replace(route_a(),volume_confirmation_kind="RB"),
            "C45_ENTRY_VC_MUST_USE_IMB_OR_SNR")
    def test_route_a_invalid_trigger_fails(self):
        self.assertBlocked(replace(route_a(),trigger_kind="ANY_OLD_FRACTAL"),
            "C45_ROUTE_A_TRIGGER_MISSING_OR_FORGED")
    def test_route_a_invalid_entry_tf_fails(self):
        self.assertBlocked(replace(route_a(),entry_tf="3M"),
            "C45_ROUTE_A_ENTRY_TF_INVALID")
    def test_route_a_stronghl_requires_more_than_raw_pivot(self):
        self.assertBlocked(replace(route_a(),confirmed_strong_hl=False),
            "C45_STRONG_HL_NOT_A_BARE_PIVOT")
    def test_idm_requires_direct_trigger_not_final_vc(self):
        self.assertBlocked(replace(route_b(),volume_confirmation_kind="IMB",
            volume_confirmation_tf="5M"),"C45_IDM_MUST_NOT_BORROW_FINAL_ROUTE_A_VC")
    def test_idm_must_be_inside_ahead_parent_poi(self):
        self.assertBlocked(replace(route_b(),direct_idm_within_or_ahead_poi=False),
            "C45_IDM_NOT_IN_OR_AHEAD_OF_PARENT_POI")
    def test_idm_wrong_ltf_trigger_tf_rejected(self):
        self.assertBlocked(replace(route_b(),trigger_tf="15M"),
            "C45_IDM_WRONG_TIMEFRAME_OR_MISSING")
    def test_idm_wrong_context_stop_rejected(self):
        self.assertBlocked(replace(route_b(),stop_kind="RAW_SWING"),
            "C45_IDM_STOP_STRUCTURE_MISSING")
    def test_bos_without_wick_raid_rejected(self):
        self.assertBlocked(replace(route_c(),raid_wick=False),
            "C45_BOS_NO_CLEAN_1H_RAID_WICK")
    def test_bos_on_wrong_raid_side_rejected(self):
        self.assertBlocked(replace(route_c(),bos_position="INSIDE_SAME_WICK"),
            "C45_BOS_NOT_ON_CORRECT_SIDE_OF_RAID")
    def test_bos_bsl_vs_ssl_side_cannot_be_swapped(self):
        self.assertBlocked(replace(route_c(),raid_kind="SSL",bos_position="BELOW_BSL_RAID"),
            "C45_BOS_NOT_ON_CORRECT_SIDE_OF_RAID")
        self.assertTrue(evaluate_text_contract(replace(route_c(),raid_kind="SSL",
            bos_position="ABOVE_SSL_RAID")).text_only_rule_consistent)

    def test_bos_wrong_stop_rejected(self):
        self.assertBlocked(replace(route_c(),stop_kind="FIVE_MIN_PIVOT"),
            "C45_BOS_STOP_NOT_AFTER_RAIDED_LIQUIDITY")
    def test_bos_missing_1h_target_rejected(self):
        self.assertBlocked(replace(route_c(),target_tf="4H"),
            "C45_BOS_NO_CONTEXTUAL_1H_TARGET")
    def test_bos_without_3m_5m_trigger_rejected(self):
        self.assertBlocked(replace(route_c(),trigger_kind="1H_BOS"),
            "C45_BOS_WRONG_OR_MISSING_3M_5M_CROSS")
    def test_unknown_route_rejected_with_exception(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_COURSE_ROUTE"):
            evaluate_text_contract(replace(route_a(),mode="GUARANTEED_PROFIT"))
    def test_forged_author_chart_golden_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_GOLDEN"):
            evaluate_text_contract(replace(route_a(),academic_author_chart_golden_verified=True))
    def test_forged_order_permission_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_GOLDEN"):
            evaluate_text_contract(replace(route_b(),raw_order_approval=True))
    def test_c44_original_context_explicit_author_fields_missing(self):
        self.assertEqual(source_only_c44_compatibility(c44_context())["status"],
            "COURSE_AUTHOR_POI_EVIDENCE_NOT_PRESENT")
    def test_c44_order_promoted_to_ready_rejected(self):
        with self.assertRaisesRegex(ValueError,"C44_FORGED_EXECUTABLE_OUTPUT"):
            source_only_c44_compatibility(dict(c44_context(),orders=("fake",)))
    def test_c44_forged_author_poi_promotion_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_AUTHOR_GOLDEN"):
            source_only_c44_compatibility(dict(c44_context(),
                verified_typed_poi_source=True,context_is_tested=True,
                academic_author_chart_golden_verified=True))
    def test_c44_missing_raw3m_id_rejected(self):
        with self.assertRaisesRegex(ValueError,"MISSING_C44_SOURCE_EVENT_FIELDS"):
            source_only_c44_compatibility({"orders":(),"trades":(),
                "readiness":"NOT_TRADE_READY"})
    def test_all_synthetic_text_passes_never_ready(self):
        for x in [route_a(),route_b(),route_c()]:
            g=evaluate_text_contract(x)
            self.assertTrue(g.text_only_rule_consistent)
            self.assertFalse(g.author_chart_golden_verified or g.source_trade_ready)
            self.assertEqual((g.orders,g.trades),((),()))
    def test_course_poi_raw_claims_have_original_drive_source(self):
        claims=recovered_text_claims()
        self.assertIn("ROUTE-C-02",claims)
        self.assertEqual(claims["STRONG-01"]["file"],"Strong High & Low.txt")

if __name__=="__main__":unittest.main()
