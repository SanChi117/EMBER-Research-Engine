"""C59 synthetic author-text constraints and tamper probes. Never price goldens."""
import unittest
from dataclasses import replace
from c59_academic_stronghl_first_test_semantic_gate import (
    AcademicStructureCase,Relation,SOURCE_STATUSES,
    course_stronghl_firsttest_gate,nested_original_imb_relation,source_parent_contract)

def case(**overrides):
    c=AcademicStructureCase(
      route="A_4H_TRIGGER_15M_VC",parent_poi_kind="SNR",
      parent_context_tf="4H",parent_was_known=True,
      first_valid_poi_test_confirmed=True,
      independent_author_poi_selection=True,
      price_contact_kind="LIQUIDITY",contact_known_ms=200,
      confirming_movement_kind="VC_POI",confirming_movement_known_ms=300,
      confirming_movement_tf="1H",confirmed_extreme_kind="STRONG_LOW",
      strong_extreme_source_verified=True,lower_tf_trigger_kind="BSL")
    return replace(c,**overrides)

def evidence(inside="INSIDE",contact=True,child=True):
    bottom,top="100","110"
    c={"bottom":bottom,"top":top,"side":"LONG",
        "fully_known_ms":1000,
        "source_status":"C46_NATIVE_4H_CLASSIC_IMB_GEOMETRY_ONLY",
        "three_original_source_first_native3m_ids":["a","b","c"],
        "author_poi_certified":False,"orders":[],"trades":[]}
    z={"candidate":c,
        "academic_poi_test_certified":False,
        "academic_volume_confirmation_certified":False,
        "first_contact_original3m_id":"contact" if contact else None,
        "first_contact_closed_known_ms":2800 if contact else None,
        "first_contact_bar_start_ms":2700 if contact else None,
        "orders":[],"trades":[],"readiness":"NOT_TRADE_READY"}
    h={"fully_known_ms":4200,"bottom":"102","top":"105",
       "side":"LONG","academic_vc_certified":False,"orders":[],"trades":[]}
    if inside=="OVERLAP":h["top"]="115"
    if inside=="OUTSIDE":h["bottom"]="115";h["top"]="120"
    w={"original4h_zone_known_ms":1000,"original4h_zone_side":"LONG",
       "original4h_zone_first_raw3m_ids":["a","b","c"],
       "original4h_first_contact_native3m_id":z["first_contact_original3m_id"],
       "original4h_first_contact_closed_known_ms":z["first_contact_closed_known_ms"],
       "first_post_contact_1h_imb_source":h if child else None,
       "course_typed_poi_approved":False,
       "course_first_valid_test_approved":False,
       "course_volume_confirmation_approved":False,
       "author_chart_golden_count":0,"orders":[],"trades":[],
       "readiness":"NOT_TRADE_READY"}
    l={"four_hour_gap_fully_known_ms":1000,"technical_4h_imb_side":"LONG",
       "technical_4h_imb_bottom":bottom,"technical_4h_imb_top":top,
       "first_contact_original3m_id":z["first_contact_original3m_id"],
       "first_contact_bar_start_ms":z["first_contact_bar_start_ms"],
       "preknown_inside_1h_liquidity":[],
       "author_typed_poi_verified":False,"author_stronghl_verified":False,
       "academic_idm_approved":False,"orders":[],"trades":[],
       "readiness":"NOT_TRADE_READY"}
    if not contact:w["first_post_contact_1h_imb_source"]=None
    return z,w,l

class CourseSemanticNegativeTests(unittest.TestCase):
    def check(self,code,**kw):
        z=course_stronghl_firsttest_gate(case(**kw))
        self.assertIn(code,z.blockers)
        self.assertEqual((z.author_poi_approved,z.strong_high_low_approved,
            z.approved_signal,z.orders,z.trades,z.readiness),
            (False,False,False,(),(),"NOT_TRADE_READY"))
    def test_text_complete_synthetic_case_is_NEVER_author_golden(self):
        z=course_stronghl_firsttest_gate(case())
        self.assertTrue(z.text_constraints_met)
        self.assertEqual(z.blockers,())
        self.assertFalse(z.strong_high_low_approved or z.approved_signal)
        self.assertEqual(z.readiness,"NOT_TRADE_READY")
    def test_bare_pivot_has_no_StrongHL(self):
        self.check("C59_BARE_PIVOT_NOT_STRONG_HIGH_LOW",strong_extreme_source_verified=False)
    def test_missing_structural_strong_high_low(self):
        self.check("C59_BARE_PIVOT_NOT_STRONG_HIGH_LOW",confirmed_extreme_kind=None)
    def test_fake_external_Poi_not_selected(self):
        self.check("C59_UNSELECTED_CONTEXT_NOT_AUTHOR_POI",independent_author_poi_selection=False)
    def test_unclosed_poi_unknown(self):
        self.check("C59_UNSELECTED_CONTEXT_NOT_AUTHOR_POI",parent_was_known=False)
    def test_first_source_touch_is_not_author_first_valid_test(self):
        self.check("C59_FIRST_VALID_POI_TEST_NOT_PROVEN",first_valid_poi_test_confirmed=False)
    def test_contact_must_be_inefficiency_or_liquidity(self):
        self.check("C59_STRONGHL_CONTACT_NOT_LIQUIDITY_OR_INEFFICIENCY",price_contact_kind="BARE_PIVOT")
    def test_no_contact_time(self):
        self.check("C59_STRONGHL_CONTACT_MISSING_CLOSED_TIME",contact_known_ms=None)
    def test_no_formation_without_confirming_vc_poi_or_bos(self):
        self.check("C59_STRONGHL_NO_VC_POI_OR_BOS_CONFIRMATION",confirming_movement_kind=None)
    def test_mere_high_low_price_does_not_confirm_movement(self):
        self.check("C59_STRONGHL_NO_VC_POI_OR_BOS_CONFIRMATION",confirming_movement_kind="SWING")
    def test_confirmation_after_contact_not_same_time(self):
        self.check("C59_STRONGHL_CONFIRMED_BEFORE_OR_AT_CONTACT",confirming_movement_known_ms=200)
    def test_confirmation_before_contact_rejected(self):
        self.check("C59_STRONGHL_CONFIRMED_BEFORE_OR_AT_CONTACT",confirming_movement_known_ms=199)
    def test_futureless_confirmation_clock_absent(self):
        self.check("C59_STRONGHL_CONFIRMED_BEFORE_OR_AT_CONTACT",confirming_movement_known_ms=None)
    def test_unknown_confirmation_tf(self):
        self.check("C59_STRONGHL_CONFIRMATION_TF_UNKNOWN",confirming_movement_tf=None)
    def test_wrong_course_routeA_trigger(self):
        self.check("C59_ROUTE_A_TRIGGER_MODEL_MIX",lower_tf_trigger_kind="IDM")
    def test_A_no_trigger_branch_is_distinct(self):
        self.check("C59_ROUTE_A_TRIGGER_MODEL_MIX",
                   route="A_4H_NO_TRIGGER_1H_VC",lower_tf_trigger_kind="BSL")
    def test_A_no_trigger_correct_text_but_no_golden(self):
        x=course_stronghl_firsttest_gate(case(
            route="A_4H_NO_TRIGGER_1H_VC",lower_tf_trigger_kind=None))
        self.assertTrue(x.text_constraints_met)
        self.assertFalse(x.approved_signal)
    def test_inside_1h_IMB_not_trigger_when_parent_4h_IMB(self):
        self.check("C59_1H_IMB_INSIDE_4H_IMB_NOT_VALID_ROUTE_A_TRIGGER",
                   parent_poi_kind="IMB",lower_tf_trigger_kind="IMB",
                   child_imb_relation=Relation.INSIDE)
    def test_overlap_with_4h_IMB_not_cleared_as_valid(self):
        self.check("C59_1H_IMB_INSIDE_4H_IMB_NOT_VALID_ROUTE_A_TRIGGER",
                   parent_poi_kind="IMB",lower_tf_trigger_kind="IMB",
                   child_imb_relation=Relation.OVERLAP)
    def test_unproven_relation_does_not_pass_imb_trigger(self):
        self.check("C59_1H_IMB_INSIDE_4H_IMB_NOT_VALID_ROUTE_A_TRIGGER",
                   parent_poi_kind="IMB",lower_tf_trigger_kind="IMB",
                   child_imb_relation=None)
    def test_inside_after_4h_SNR_does_not_trigger_imb_specific_rule(self):
        x=course_stronghl_firsttest_gate(case(
            parent_poi_kind="SNR",lower_tf_trigger_kind="IMB",
            child_imb_relation=Relation.INSIDE))
        self.assertTrue(x.text_constraints_met)
        self.assertFalse(x.approved_signal)
    def test_4h_imb_outside_1h_imb_only_text_consistent(self):
        x=course_stronghl_firsttest_gate(case(
            parent_poi_kind="IMB",lower_tf_trigger_kind="IMB",
            child_imb_relation=Relation.OUTSIDE))
        self.assertTrue(x.text_constraints_met)
        self.assertFalse(x.approved_signal)
    def test_routeB_direct_IDM_does_not_inherit_A_final_vc(self):
        x=course_stronghl_firsttest_gate(case(
           route="B_4H_VC_1H_IDM",lower_tf_trigger_kind="IDM"))
        self.assertTrue(x.text_constraints_met)
        self.assertEqual(x.orders,())
    def test_routeB_refuses_routeA_trigger(self):
        self.check("C59_ROUTE_B_MUST_KEEP_IDM_SEPARATE",
                   route="B_4H_VC_1H_IDM",lower_tf_trigger_kind="IMB")
    def test_routeB_1h_context_distinct(self):
        x=course_stronghl_firsttest_gate(case(
            route="B_1H_VC_15M_IDM",parent_context_tf="1H",
            lower_tf_trigger_kind="IDM"))
        self.assertTrue(x.text_constraints_met)
        self.assertFalse(x.approved_signal)
    def test_routeB_1h_wrong_parent_4h(self):
        self.check("C59_WRONG_POI_CONTEXT_TF",
                  route="B_1H_VC_15M_IDM",lower_tf_trigger_kind="IDM")
    def test_forged_author_golden_strict_rejection(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_GOLDEN"):
            course_stronghl_firsttest_gate(case(author_chart_golden_verified=True))
    def test_forced_order_strict_rejection(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_GOLDEN"):
            course_stronghl_firsttest_gate(case(place_order=True))
    def test_invalid_unknown_route_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_ROUTE"):
            course_stronghl_firsttest_gate(case(route="C_1H_RAID_3M_BOS"))
    def test_untrusted_case_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED"):
            course_stronghl_firsttest_gate({})
    def test_1h_imb_inside_4h_bounds_touch_is_inside(self):
        self.assertIs(nested_original_imb_relation("100","110","100","109"),Relation.INSIDE)
    def test_1h_imb_outside(self):
        self.assertIs(nested_original_imb_relation("100","110","111","112"),Relation.OUTSIDE)
    def test_1h_imb_overlaps(self):
        self.assertIs(nested_original_imb_relation("100","110","109","111"),Relation.OVERLAP)
    def test_bad_price_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_ORIGINAL_ZONE_PRICE"):
            nested_original_imb_relation("NaN","110","103","104")
    def test_reversed_price_rejected(self):
        with self.assertRaisesRegex(ValueError,"REVERSED_SOURCE_ZONE"):
            nested_original_imb_relation("110","100","103","104")
    def test_negative_price_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_ORIGINAL_ZONE_PRICE"):
            nested_original_imb_relation("-100","110","103","104")

class FrozenLineageAdversaries(unittest.TestCase):
    def run_source(self,where="INSIDE",contact=True,child=True):
        return source_parent_contract(*evidence(where,contact,child))
    def test_source_nested_strict_veto(self):
        z=self.run_source()
        self.assertEqual(z["status"],SOURCE_STATUSES[2])
        self.assertFalse(z["course_author_routeA_trigger"])
        self.assertFalse(z["course_author_strongHL"])
    def test_source_overlap_veto(self):
        self.assertEqual(self.run_source("OVERLAP")["status"],SOURCE_STATUSES[3])
    def test_source_outside_remains_geometry_only(self):
        self.assertEqual(self.run_source("OUTSIDE")["status"],SOURCE_STATUSES[4])
    def test_source_first_contact_without_later_1h(self):
        self.assertEqual(self.run_source(child=False)["status"],SOURCE_STATUSES[1])
    def test_source_without_first_contact_no_child(self):
        self.assertEqual(self.run_source(contact=False)["status"],SOURCE_STATUSES[0])
    def test_forged_late_first_contact_id(self):
        a,b,c=evidence();c["first_contact_original3m_id"]="future"
        with self.assertRaisesRegex(ValueError,"PARENT_ID_DRIFT"):
            source_parent_contract(a,b,c)
    def test_forged_4h_zone_price(self):
        a,b,c=evidence();c["technical_4h_imb_top"]="200"
        with self.assertRaisesRegex(ValueError,"PARENT_ID_DRIFT"):
            source_parent_contract(a,b,c)
    def test_forged_author_in_C46(self):
        a,b,c=evidence();a["academic_poi_test_certified"]=True
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_AUTHOR"):
            source_parent_contract(a,b,c)
    def test_forged_author_in_C58(self):
        a,b,c=evidence();c["author_stronghl_verified"]=True
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_AUTHOR"):
            source_parent_contract(a,b,c)
    def test_fake_1h_author_vc_promotion(self):
        a,b,c=evidence();b["first_post_contact_1h_imb_source"]["academic_vc_certified"]=True
        with self.assertRaisesRegex(ValueError,"FORGED_OR_PRE_CONTACT"):
            source_parent_contract(a,b,c)
    def test_time_travel_later_1h_before_contact(self):
        a,b,c=evidence();b["first_post_contact_1h_imb_source"]["fully_known_ms"]=2000
        with self.assertRaisesRegex(ValueError,"FORGED_OR_PRE_CONTACT"):
            source_parent_contract(a,b,c)
    def test_forged_order_rejected(self):
        a,b,c=evidence();a["orders"]=["fake"]
        with self.assertRaisesRegex(ValueError,"FORGED_ORDERS"):
            source_parent_contract(a,b,c)
    def test_untrusted_dict_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_SOURCE"):
            source_parent_contract([],{},{})

if __name__=="__main__":unittest.main()
