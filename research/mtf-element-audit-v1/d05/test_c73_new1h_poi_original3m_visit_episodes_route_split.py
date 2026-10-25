"""C73 original 3m first POI *visit* != author valid first test."""
import unittest
from dataclasses import replace
from test_c71_post_contact_closed_15m_vc_1h_bos_semantic_gate import build,run
from test_c67_route_a_1h_trigger_vs_new_poi_source_fork import (
    BASE,H,Q,nbar,hbar,review,event15,hours,native)
from test_c70_exact_native3m_first_raid_or_poi_source_wick import rows
from test_c72_original_native5m_source_vc_after15m_gate import (
    source,fake5,K_IMB,K_SNR_LIQ)
from c69_exact_native15m_first_liquidity_raid_vs_poi_test import first_original_native15m_source_contact
from c70_exact_native3m_first_raid_or_poi_source_wick import original3m_first_wick_within_c69
from c72_original_native5m_source_vc_after15m_gate import first_any_5m_after_provisional15m
from c73_new1h_poi_original3m_visit_episodes_route_split import (
    evaluate_new1h_source_poi_first_visit_and_route,C73Rejected,STATES)
def setup(raid=False,e15=None,e1=None,newpoi=None,outside=False,n=20):
    if outside:
        assert not raid and e15 is None and e1 is None
        z=list(build())
        h=list(z[3]);nn=list(z[4])
        h[7]=hbar(7,hi=110,lo=95,op=100,cl=100)
        for k in (29,30):
            nn[k]=nbar(k,hi=110,lo=107,op=110,cl=110)
        z[3]=tuple(h);z[4]=tuple(nn);z[5]=rows(z[4])
        f=review(hh=z[3],nn=z[4],e1=z[7],e15=z[6],asof=z[8])
        z[0]=f
        z[1]=first_original_native15m_source_contact(f,z[3],z[4],as_of_ms=z[8])
        z[2]=original3m_first_wick_within_c69(
            f,z[1],z[4],z[5],as_of_ms=z[8])
        z=tuple(z)
    elif newpoi is not None:
        h=hours(newpoi_range=newpoi)
        z=build() # replace first by properly rebuilt original source
        z=list(z);z[3]=h
        z[0]=review(hh=h,nn=z[4],e1=z[7],e15=z[6],asof=z[8])
        z[1]=first_original_native15m_source_contact(z[0],h,z[4],as_of_ms=z[8])
        z[2]=original3m_first_wick_within_c69(
            z[0],z[1],z[4],z[5],as_of_ms=z[8])
        z=tuple(z)
    else:z=build(raid=raid,e15=e15,e1=e1,n=n)
    c71=run(z)
    five=source(cut=z[8])
    at=c71.first_any_confirmed_event_ms
    events=(fake5(start=at),) if at is not None else ()
    c72=first_any_5m_after_provisional15m(c71,five,events)
    return z,c71,c72,five,events
def assess(pack=None):
    if pack is None:pack=setup()
    z,c71,c72,five,events=pack
    f,g,k,h,n,raw,e15,e1,asof=z
    return evaluate_new1h_source_poi_first_visit_and_route(
        f,g,k,c71,c72,raw,n,h,e15,e1,five,events,as_of_ms=asof)
class C73TypedCourseRouteSplit(unittest.TestCase):
    def test_01_first_original3m_touch_is_not_author_valid_test(self):
        x=assess()
        self.assertEqual(x.state,STATES[3])
        self.assertEqual(x.episodes_before_first_15m_pattern,1)
        self.assertFalse(x.author_1h_poi_valid_first_test)
    def test_02_single_contiguous_source_wick_visit_is_one_episode(self):
        x=assess()
        self.assertEqual(x.episodes_before_first_15m_pattern,1)
        self.assertTrue(x.source_continuous_visit_right_censored)
    def test_03_first_true_source3m_raw_SHA_recorded(self):
        x=assess()
        self.assertIsNotNone(x.original_first_source3m_touch_id)
        self.assertIsNotNone(x.original_first_source3m_touch_closed_ms)
    def test_04_original_1h_source_Poi_creation_before_wick(self):
        x=assess()
        self.assertLessEqual(x.source_1h_poi_created_at_ms,
                             x.original_first_source3m_touch_closed_ms)
    def test_05_15m_source_pattern_starts_after_first3m_touch(self):
        x=assess()
        self.assertGreaterEqual(x.first_source15m_event_pattern_start_ms,
                                x.original_first_source3m_touch_closed_ms)
    def test_06_provisional_5m_source_not_author_5m_vc(self):
        x=assess()
        self.assertEqual(x.source_first_5m_after_candidate_state,
                         "FIRST_5M_IMB_ALIGNED_NOT_AUTHOR_VC")
        self.assertFalse(x.author_5m_vc)
    def test_07_owner_15m_trigger_vs_15m_vc_neither_approved(self):
        x=assess()
        self.assertFalse(x.author_15m_trigger or x.author_15m_vc)
    def test_08_exact_source_3m_first_touch_does_not_create_structural_sl(self):
        x=assess()
        self.assertFalse(x.author_structural_sl or x.author_stronghl)
        self.assertEqual((x.orders,x.fills,x.trades),((),(),()))
    def test_09_two_physically_distinct_POI_visits_not_two_wicks_same_episode(self):
        x=assess(setup(outside=True))
        self.assertEqual(x.state,STATES[4])
        self.assertEqual(x.episodes_before_first_15m_pattern,2)
        self.assertIsNotNone(x.second_visit_original3m_id)
    def test_10_revisit_3m_id_is_different_than_first_original_touch(self):
        x=assess(setup(outside=True))
        self.assertNotEqual(x.second_visit_original3m_id,
                            x.original_first_source3m_touch_id)
    def test_11_revisit_before_first15m_event_does_not_become_author_valid(self):
        x=assess(setup(outside=True))
        self.assertFalse(x.author_1h_poi_valid_first_test or x.author_entry)
    def test_12_previous_1H_raid_route_cannot_rebrand_new_poi(self):
        x=assess(setup(raid=True))
        self.assertEqual(x.state,STATES[0])
        self.assertIsNone(x.episodes_before_first_15m_pattern)
    def test_13_no_source_1h_Poi_first3m_wick_remains_empty(self):
        x=assess(setup(newpoi=(190,200)))
        self.assertEqual(x.state,STATES[1])
        self.assertIsNone(x.original_first_source3m_touch_id)
    def test_14_first_opposite_15m_source_does_not_get_5m_route(self):
        x=assess(setup(e15=(event15(side="SHORT"),)))
        self.assertEqual(x.state,STATES[2])
        self.assertIsNone(x.episodes_before_first_15m_pattern)
    def test_15_no_15m_source_event_routes_censored_not_5m(self):
        x=assess(setup(e15=()))
        self.assertEqual(x.state,STATES[2])
    def test_16_same_time_two_kinds_15m_source_never_fabricates_route(self):
        x=assess(setup(e15=(event15(),event15(
            kind="15M_SNR_PRIOR_IMB_SOURCE_ONLY"))))
        self.assertEqual(x.state,STATES[2])
    def test_17_wrong_C71_source_status_rejected_after_recompute(self):
        z=list(setup());z[1]=replace(z[1],state="FIRST_ANY_SOURCE_OPPOSITE_DIRECTION")
        with self.assertRaisesRegex(C73Rejected,"C71_SOURCE_FIRST_ANY"):
            assess(tuple(z))
    def test_18_wrong_C71_15m_clock_rejected(self):
        z=list(setup());z[1]=replace(z[1],first_any_confirmed_event_ms=BASE)
        with self.assertRaisesRegex(C73Rejected,"C71_SOURCE_FIRST_ANY"):
            assess(tuple(z))
    def test_19_wrong_C72_5m_future_source_event_rejected(self):
        z=list(setup());z[2]=replace(z[2],first_any_5m_event_known_ms=BASE)
        with self.assertRaisesRegex(C73Rejected,"C72_FIRST_ANY"):
            assess(tuple(z))
    def test_20_wrong_C72_future_first5m_kind_rejected(self):
        z=list(setup());z[2]=replace(z[2],first_any_5m_kinds=("FAKE",))
        with self.assertRaisesRegex(C73Rejected,"C72_FIRST_ANY"):
            assess(tuple(z))
    def test_21_fake_author_1h_poi_valid_test_rejected(self):
        z=list(setup());z[1]=replace(z[1],author_1h_poi_valid_test=True)
        with self.assertRaisesRegex(C73Rejected,"AUTHOR_PROMOTION"):
            assess(tuple(z))
    def test_22_fake_author_15m_trigger_rejected(self):
        z=list(setup());z[2]=replace(z[2],author_15m_trigger=True)
        with self.assertRaisesRegex(C73Rejected,"AUTHOR_PROMOTION"):
            assess(tuple(z))
    def test_23_fake_author_5m_vc_rejected(self):
        z=list(setup());z[2]=replace(z[2],author_5m_vc=True)
        with self.assertRaisesRegex(C73Rejected,"AUTHOR_PROMOTION"):
            assess(tuple(z))
    def test_24_fake_trade_order_rejected(self):
        z=list(setup());z[2]=replace(z[2],orders=("LONG",))
        with self.assertRaisesRegex(C73Rejected,"AUTHOR_PROMOTION"):
            assess(tuple(z))
    def test_25_route_b_idm_forgery_rejected(self):
        z=list(setup());z[2]=replace(z[2],route_b_idm_used=True)
        with self.assertRaisesRegex(C73Rejected,"AUTHOR_PROMOTION"):
            assess(tuple(z))
    def test_26_route_c_raid_bos_forgery_rejected(self):
        z=list(setup());z[2]=replace(z[2],route_c_raid_bos_used=True)
        with self.assertRaisesRegex(C73Rejected,"AUTHOR_PROMOTION"):
            assess(tuple(z))
    def test_27_source_3m_first_wick_id_forgery_rejected(self):
        z=list(setup());v=list(z[0]);v[2]=replace(v[2],actual_first_native3m_id="FAKE")
        z[0]=tuple(v)
        with self.assertRaisesRegex(ValueError,"DRIFT|SOURCE|FORGED"):
            assess(tuple(z))
    def test_28_wrong_symbol_C72_review_rejected(self):
        z=list(setup());z[3]=replace(z[3],symbol="SOLUSDT")
        with self.assertRaisesRegex(C73Rejected,"PARENT_SOURCE"):
            assess(tuple(z))
    def test_29_tampered_first_5m_event_original_SHA_rejected(self):
        z=list(setup());z[4]=(replace(z[4][0],first_bar_id="FAKE"),)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            assess(tuple(z))
    def test_30_no_paper_or_live_orders_associated_with_first_source_POI(self):
        x=assess()
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
        self.assertFalse(x.author_entry or x.author_1h_poi_valid_first_test)
        self.assertFalse(x.route_b_idm_used or x.route_c_raid_bos_used)
if __name__=="__main__":unittest.main()
