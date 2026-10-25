"""C61 academic text contract, original 1D source gate, C46/C47/C59/C60 anti-fraud."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c16_c08_monthly_daily_htf_lineage import NativeKline,SEPT_START,DAY
from c61_academic_poi_context_first_valid_stronghl_contract import (
    AcademicPoiCase,academic_poi_lifecycle_contract,SourceDayContext,
    last_closed_original_day_before_zone,join_source_poi_context)

O=SEPT_START; SHA="f"*64; THREE=180000
def rid(t):return SHA+":"+str(t)
def case(**kw):
    p=AcademicPoiCase(
       route="A_4H_TRIGGER_15M_VC",source_kind="IMB",source_tf="4H",
       source_created_known_ms=O+8*3600000,parent_context_known_ms=O+4*3600000,
       parent_context_typed="RB",parent_context_author_verified=True,
       original_first_contact_known_ms=O+10*3600000,
       first_valid_test_author_verified=True,
       liquidity_or_inefficiency_contact_known_ms=O+10*3600000,
       liquidity_or_inefficiency_kind="LIQUIDITY",
       confirming_event_kind="VC_POI",confirming_event_known_ms=O+11*3600000,
       confirming_tf="1H",strong_extreme_kind="STRONG_LOW",
       stronghl_author_verified=True,source_visited_again=False)
    return replace(p,**kw)

def day(i):
    t=O+i*DAY
    return NativeKline("BTCUSDT","1d",t,t+DAY,D("100"),D("109"),D("92"),
        D("103"),D("55"),rid(t),SHA)

def forged_source(repeated=False,touch=True):
    known=O+12*3600000; t=known+THREE
    c={"fully_known_ms":known,"source_status":"C46_NATIVE_4H_CLASSIC_IMB_GEOMETRY_ONLY",
       "side":"LONG","bottom":"100","top":"110",
       "three_original_source_first_native3m_ids":[rid(known-12*3600000),
          rid(known-8*3600000),rid(known-4*3600000)],
       "author_poi_certified":False,"orders":[],"trades":[]}
    first=rid(t) if touch else None
    z={"candidate":c,"first_contact_original3m_id":first,
       "first_contact_closed_known_ms":t+THREE if touch else None,
       "orders":[],"trades":[],"academic_poi_test_certified":False,
       "academic_volume_confirmation_certified":False,"readiness":"NOT_TRADE_READY"}
    h={"original4h_zone_known_ms":known,"original4h_zone_side":"LONG",
       "original4h_zone_first_raw3m_ids":c["three_original_source_first_native3m_ids"],
       "original4h_first_contact_native3m_id":first,
       "first_post_contact_1h_imb_source":
           ({"fully_known_ms":known+4*3600000} if touch else None),
       "course_typed_poi_approved":False,"course_first_valid_test_approved":False,
       "course_volume_confirmation_approved":False,
       "orders":[],"trades":[],"readiness":"NOT_TRADE_READY"}
    k={"original_4h_known_ms":known,"original_4h_side":"LONG",
       "original_4h_first_native3m_ids":c["three_original_source_first_native3m_ids"],
       "first_original3m_contact_id":first,
       "post_contact_1h_imb_known_ms":known+4*3600000 if touch else None,
       "status":"LATER_1H_IMB_OUTSIDE_PARENT_GEOMETRY_ONLY" if touch
                 else "NO_4H_SOURCE_FIRST_CONTACT",
       "course_author_strongHL":False,"course_author_first_valid_test":False,
       "course_author_routeA_trigger":False,"course_author_routeB_IDM":False,
       "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"}
    visits=([{"first_original3m_raw_id":first,
         "first_bar_known_ms":t+THREE,
         "still_inside_at_source_end":False}] if touch else [])
    if repeated:visits.append({"first_original3m_raw_id":rid(t+2*THREE),
                        "first_bar_known_ms":t+3*THREE,
                        "still_inside_at_source_end":True})
    v={"zone_known_ms":known,"zone_bottom":"100","zone_top":"110",
       "technical_4h_zone_side":"LONG",
       "original_4h_first_row_ids":c["three_original_source_first_native3m_ids"],
       "first_contact_original3m_id":first,"all_closed_3m_visit_episodes":visits,
       "repeated_distinct_returns_after_first":max(0,len(visits)-1),
       "course_author_valid_first_test":False,
       "course_author_StrongHL":False,"academic_trade_signal":False,
       "orders":[],"trades":[],"readiness":"NOT_TRADE_READY"}
    ctx=SourceDayContext("BTCUSDT",known,rid(O),O+DAY,"109","92")
    return z,h,k,v,ctx

class AcademicContractTests(unittest.TestCase):
    def reject(self,code,**kwargs):
        q=academic_poi_lifecycle_contract(case(**kwargs))
        self.assertIn(code,q.blockers)
        self.assertFalse(q.author_verified_entry or q.author_verified_stronghl)
        self.assertEqual(q.readiness,"NOT_TRADE_READY")
    def test_text_valid_synthetic_is_never_author_trade(self):
        z=academic_poi_lifecycle_contract(case())
        self.assertTrue(z.text_preconditions_consistent)
        self.assertFalse(z.author_verified_entry or z.author_verified_stronghl)
        self.assertEqual(z.orders,())
    def test_missing_htf_context(self):
        self.reject("C61_UNVERIFIED_PRIOR_HTF_CONTEXT",parent_context_author_verified=False)
    def test_htf_context_after_child(self):
        self.reject("C61_UNVERIFIED_PRIOR_HTF_CONTEXT",parent_context_known_ms=O+9*3600000)
    def test_wrong_context_type(self):
        self.reject("C61_UNVERIFIED_PRIOR_HTF_CONTEXT",parent_context_typed="PIVOT")
    def test_unobserved_first_source_touch(self):
        self.reject("C61_UNVERIFIED_FIRST_SOURCE_CONTACT",original_first_contact_known_ms=None)
    def test_source_touched_before_formation(self):
        self.reject("C61_UNVERIFIED_FIRST_SOURCE_CONTACT",original_first_contact_known_ms=O+7*3600000)
    def test_no_author_first_valid_test(self):
        self.reject("C61_NOT_FIRST_VALID_POI_TEST",first_valid_test_author_verified=False)
    def test_revisit_after_first_does_not_retroactively_change_first_timestamp(self):
        z=academic_poi_lifecycle_contract(case(source_visited_again=True))
        self.assertTrue(z.text_preconditions_consistent)
        self.assertFalse(z.author_verified_first_valid_poi_test)
    def test_wrong_contact_type(self):
        self.reject("C61_LIQUIDITY_INEFFICIENCY_CONTACT_UNVERIFIED",liquidity_or_inefficiency_kind="BARE_WICK")
    def test_missing_contact_time(self):
        self.reject("C61_LIQUIDITY_INEFFICIENCY_CONTACT_UNVERIFIED",liquidity_or_inefficiency_contact_known_ms=None)
    def test_bad_contact_order(self):
        self.reject("C61_LIQUIDITY_INEFFICIENCY_CONTACT_UNVERIFIED",liquidity_or_inefficiency_contact_known_ms=O+7*3600000)
    def test_missing_vc_bos(self):
        self.reject("C61_STRONGHL_VC_BOS_WRONG_CHRONOLOGY",confirming_event_kind=None)
    def test_wrong_vc_kind(self):
        self.reject("C61_STRONGHL_VC_BOS_WRONG_CHRONOLOGY",confirming_event_kind="SWING")
    def test_vc_before_contact(self):
        self.reject("C61_STRONGHL_VC_BOS_WRONG_CHRONOLOGY",confirming_event_known_ms=O+9*3600000)
    def test_vc_at_contact(self):
        self.reject("C61_STRONGHL_VC_BOS_WRONG_CHRONOLOGY",confirming_event_known_ms=O+10*3600000)
    def test_unknown_vc_tf(self):
        self.reject("C61_STRONGHL_VC_BOS_WRONG_CHRONOLOGY",confirming_tf="30S")
    def test_bare_pivot_not_strong(self):
        self.reject("C61_BARE_PIVOT_NOT_STRONGHL",stronghl_author_verified=False)
    def test_missing_strong_direction(self):
        self.reject("C61_BARE_PIVOT_NOT_STRONGHL",strong_extreme_kind="PIVOT")
    def test_rb_without_liquidity_or_imb_raid_never_approved(self):
        self.reject("C61_RB_REQUIRES_RAID_OR_IMB_WORK",source_kind="RB")
    def test_rb_with_author_text_requirement_synthetically_consistent_not_signal(self):
        z=academic_poi_lifecycle_contract(case(source_kind="RB",rb_raid_or_imb_overlap_author_verified=True))
        self.assertTrue(z.text_preconditions_consistent)
        self.assertEqual(z.readiness,"NOT_TRADE_READY")
    def test_routeB_direct_idm_does_not_require_poi_first_test(self):
        z=academic_poi_lifecycle_contract(case(route="B_4H_VC_1H_IDM",
             original_first_contact_known_ms=None,first_valid_test_author_verified=False,
             direct_idm_known_ms=O+12*3600000))
        self.assertTrue(z.text_preconditions_consistent)
        self.assertFalse(z.author_verified_entry)
    def test_routeB_fails_if_limit_precedes_parent_vc_even_if_poi_not_tested(self):
        self.reject("C61_IDM_PRECEDES_CONFIRMED_PARENT_VC",
            route="B_4H_VC_1H_IDM",
            original_first_contact_known_ms=None,
            first_valid_test_author_verified=False,
            direct_idm_known_ms=O+10*3600000)
    def test_routeA_fails_if_vc_after_liquidity_but_before_original_first_test(self):
        self.reject("C61_ROUTE_A_OR_C_CONFIRMATION_BEFORE_FIRST_TEST",
            liquidity_or_inefficiency_contact_known_ms=O+8*3600000,
            confirming_event_known_ms=O+9*3600000)
    def test_routeA_requires_confirmation_strictly_after_first_test(self):
        self.reject("C61_ROUTE_A_OR_C_CONFIRMATION_BEFORE_FIRST_TEST",
            confirming_event_known_ms=O+10*3600000)
    def test_routeB_missing_idm(self):
        self.reject("C61_ROUTE_B_IDM_NOT_PROVEN",route="B_4H_VC_1H_IDM")
    def test_routeB_early_idm_time(self):
        self.reject("C61_ROUTE_B_IDM_NOT_PROVEN",route="B_4H_VC_1H_IDM",
                    direct_idm_known_ms=O+7*3600000)
    def test_unknown_route_forbidden(self):
        with self.assertRaisesRegex(ValueError,"INVALID_COURSE"):
            academic_poi_lifecycle_contract(case(route="UNTRUSTED"))
    def test_forbid_forged_author_price_golden(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR"):
            academic_poi_lifecycle_contract(case(author_price_golden=True))
    def test_forbid_forged_author_trade(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR"):
            academic_poi_lifecycle_contract(case(orders=("fake",)))
    def test_unknown_source_kind_forbidden(self):
        with self.assertRaisesRegex(ValueError,"INVALID_COURSE"):
            academic_poi_lifecycle_contract(case(source_kind="FAKE_POI"))

class NativeDailyPrefixTests(unittest.TestCase):
    def ctx(self,rows=None,t=O+DAY+12*3600000,asof=O+2*DAY):
        return last_closed_original_day_before_zone((day(0),day(1)) if rows is None else rows,
             symbol="BTCUSDT",zone_known_ms=t,as_of_ms=asof)
    def test_one_previous_closed_native_day_used(self):
        z=self.ctx()
        self.assertEqual(z.latest_prior_closed_native1d_id,rid(O))
        self.assertEqual((z.prior_day_high,z.prior_day_low),("109","92"))
        self.assertFalse(z.author_daily_context_approved)
    def test_first_day_no_past_daily_context_is_not_fake(self):
        q=self.ctx(t=O+12*3600000)
        self.assertIsNone(q.latest_prior_closed_native1d_id)
    def test_boundary_at_native_1d_close_daily_is_known(self):
        q=self.ctx(t=O+DAY)
        self.assertEqual(q.latest_prior_closed_native1d_id,rid(O))
    def test_never_future_native_daily_high(self):
        q=self.ctx(t=O+DAY-THREE)
        self.assertIsNone(q.prior_day_high)
    def test_reject_future_unclosed_native_day_in_passed_prefix(self):
        with self.assertRaisesRegex(ValueError,"UNCLOSED_NATIVE_1D"):
            self.ctx(asof=O+DAY+12*3600000)
    def test_reject_forged_raw_daily_id(self):
        rows=(replace(day(0),origin_raw_row_id=rid(O+DAY)),day(1))
        with self.assertRaisesRegex(ValueError,"UNCLOSED_NATIVE_1D"):
            self.ctx(rows=rows)
    def test_reject_bad_daily_high_nan(self):
        rows=(replace(day(0),high=D("NaN")),day(1))
        with self.assertRaisesRegex(ValueError,"UNCLOSED_NATIVE_1D"):
            self.ctx(rows=rows)
    def test_reject_noncontiguous_daily_prefix(self):
        rows=(day(0),day(2))
        with self.assertRaisesRegex(ValueError,"UNCLOSED_NATIVE_1D"):
            self.ctx(rows=rows)
    def test_reject_fake_1d_source_is_not_native(self):
        with self.assertRaisesRegex(ValueError,"UNCLOSED_NATIVE_1D"):
            self.ctx(rows=({"tf":"1d"},day(1)))

class OriginalCrossLineageTests(unittest.TestCase):
    def join(self,z=None):
        a=forged_source() if z is None else z
        return join_source_poi_context(*a)
    def reject(self,code,index,key,value):
        a=list(forged_source())
        if index<4:a[index][key]=value
        else:a[index]=value
        with self.assertRaisesRegex(ValueError,code):
            self.join(tuple(a))
    def test_original_join_never_promotes_author_or_order(self):
        z=self.join()
        self.assertEqual(z["source_visit_status"],"ONE_TECHNICAL_SOURCE_VISIT")
        self.assertFalse(z["course_fully_verified"])
        self.assertEqual(z["readiness"],"NOT_TRADE_READY")
    def test_revisited_source_but_not_author_first_valid_test(self):
        z=self.join(forged_source(repeated=True))
        self.assertEqual(z["source_visit_status"],"REVISITED_TECHNICAL_ZONE")
        self.assertFalse(z["author_first_valid_test"])
        self.assertTrue(z["last_source_visit_right_censored"])
    def test_no_first_touch_source_only(self):
        z=self.join(forged_source(touch=False))
        self.assertEqual(z["source_visit_status"],"NO_OBSERVED_FIRST_SOURCE_CONTACT")
    def test_c47_wrong_source_known_time(self):
        self.reject("PARENT_ID",1,"original4h_zone_known_ms",O+DAY)
    def test_c60_original_first_id_mismatch(self):
        self.reject("PARENT_ID",3,"first_contact_original3m_id","fake")
    def test_c59_fake_author_stronghl(self):
        self.reject("PRETENDS_AUTHOR_APPROVAL",2,"course_author_strongHL",True)
    def test_c47_fake_academic_context(self):
        self.reject("PRETENDS_AUTHOR_APPROVAL",1,"course_typed_poi_approved",True)
    def test_source_untrusted_wrong_type(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED"):
            join_source_poi_context({},None,{}, {},forged_source()[-1])
    def test_repeats_count_forgery(self):
        self.reject("FIRST_VISIT_AND_REVISIT",3,"repeated_distinct_returns_after_first",8)
    def test_c59_mismatched_later_1h(self):
        self.reject("FIRST_VISIT_AND_REVISIT",2,"post_contact_1h_imb_known_ms",O+9*3600000)
    def test_author_daily_context_forgery(self):
        a=list(forged_source())
        a[4]=replace(a[4],author_daily_context_approved=True)
        with self.assertRaisesRegex(ValueError,"PRETENDS_AUTHOR_APPROVAL"):
            self.join(tuple(a))
    def test_source_research_no_permission_to_issue_trade(self):
        z=self.join()
        self.assertEqual((z["orders"],z["trades"]),(0,0))
        self.assertFalse(z["author_strongHL"] or z["author_reaction_vc_or_bos"])

if __name__=="__main__":unittest.main()
