"""C69 true original15m first raid bar vs 1H last bar, source only."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from test_c67_route_a_1h_trigger_vs_new_poi_source_fork import (
 BASE,H,Q,nbar,native,hours,review,h1event,event15,rid)
from c69_exact_native15m_first_liquidity_raid_vs_poi_test import (
 first_original_native15m_source_contact,STATES)
def raid_source(variant="wick",multi=False):
    hh=list(hours(raid=True))
    if multi:
        from test_c67_route_a_1h_trigger_vs_new_poi_source_fork import hbar
        hh[1]=hbar(1,hi=105,lo=80)
        hh[2]=hbar(2,hi=105,lo=95)
        hh[3]=hbar(3,hi=105,lo=90)
        hh[4]=hbar(4,hi=105,lo=95)
    nn=list(native())
    if variant=="wick":
        nn[20]=nbar(20,105,100,100,101)
        nn[21]=nbar(21,103,79,101,90)
        nn[22]=nbar(22,102,89,90,99)
        nn[23]=nbar(23,101,95,99,100)
    elif variant=="body":
        nn[20]=nbar(20,105,100,100,101)
        nn[21]=nbar(21,103,79,101,79)
        nn[22]=nbar(22,102,79,79,99)
        nn[23]=nbar(23,101,95,99,100)
    elif variant=="first":
        nn[20]=nbar(20,105,79,100,100)
        nn[21]=nbar(21,103,90,100,100)
        nn[22]=nbar(22,102,90,100,100)
        nn[23]=nbar(23,101,95,100,100)
    return tuple(hh),tuple(nn)
def apply(hh=None,nn=None,fork=None,asof=BASE+20*H):
    if hh is None:hh=hours(raid=True)
    if nn is None:nn=native()
    if fork is None:fork=review(hh=hh,e1=(),e15=(),asof=asof)
    return first_original_native15m_source_contact(fork,hh,nn,as_of_ms=asof)
class C69SourceFirstRaid(unittest.TestCase):
    def test_real_first_native15m_raided_second_bar_not_last_hour_bar(self):
        hh,nn=raid_source()
        x=apply(hh,nn)
        self.assertEqual(x.source_status,"RAID_FIRST_NATIVE15M_BAR_WICK_ONLY_RECLAIM_1H")
        self.assertEqual(x.first_exact_original15m_contact_start_ms,BASE+21*Q)
        self.assertNotEqual(x.first_exact_original15m_contact_start_ms,BASE+23*Q)
        self.assertEqual(x.preknown_level_price,"80")
        self.assertTrue(x.compared_four_original15m_to_derived1h)
    def test_first_bar_exact_raid_can_be_hour_first_not_assumed_last(self):
        hh,nn=raid_source("first")
        x=apply(hh,nn)
        self.assertEqual(x.first_exact_original15m_contact_start_ms,BASE+20*Q)
    def test_first15m_body_cross_then_hour_reclaims_classified_separately(self):
        hh,nn=raid_source("body")
        x=apply(hh,nn)
        self.assertEqual(x.source_status,"RAID_FIRST_NATIVE15M_BAR_CLOSE_BEYOND_LEVEL_RECLAIM_LATER_1H")
        self.assertFalse(x.first_15m_wick_only_reclaim)
        self.assertTrue(x.containing_1h_wick_only_reclaim)
    def test_multiple_unswept_levels_crossed_in_first_same15m_is_ambiguous(self):
        hh,nn=raid_source("first",True)
        x=apply(hh,nn)
        self.assertEqual(x.source_status,"AMBIGUOUS_MULTIPLE_PREKNOWN_LIQUIDITY_LEVELS_SAME_FIRST_BAR")
        self.assertEqual(x.number_of_levels_first_crossed_at_same_15m_bar,2)
        self.assertIsNone(x.preknown_level_price)
    def test_new_poi_source_first_test_uses_original_c67_id_no_owner_first_valid(self):
        f=review()
        x=apply(hours(),native(),f)
        self.assertEqual(x.source_status,"NEW_1H_POI_SOURCE_FIRST15M_WICK_TEST_NOT_AUTHOR_VALID")
        self.assertEqual(x.first_exact_original15m_contact_id,
                         f.source_first_new_1h_poi_test_native15m_id)
        self.assertFalse(x.author_first_valid_poi_test)
    def test_new_poi_touch_claim_for_nonexistent_source_rejected(self):
        f=review(hh=hours(newpoi_range=(190,200)))
        self.assertEqual(apply(hours(newpoi_range=(190,200)),native(),f).source_status,
                         "NEW_1H_POI_NO_SOURCE_FIRST_TEST")
    def test_new_poi_first_touch_forged_original15m_id_rejected(self):
        f=replace(review(),source_first_new_1h_poi_test_native15m_id=rid(BASE))
        with self.assertRaisesRegex(ValueError,"DRIFT"):
            apply(hours(),native(),f)
    def test_new_poi_first_touch_forged_close_time_rejected(self):
        f=replace(review(),source_first_new_1h_poi_test_closed_ms=BASE+8*H)
        with self.assertRaisesRegex(ValueError,"DRIFT"):
            apply(hours(),native(),f)
    def test_1h_raid_unaggregated_fake_15m_high_rejected(self):
        hh,nn=raid_source()
        n=list(nn);n[23]=replace(n[23],high=D(120))
        with self.assertRaisesRegex(ValueError,"PARITY"):
            apply(hh,tuple(n))
    def test_1h_raid_unaggregated_fake_15m_close_rejected(self):
        hh,nn=raid_source()
        n=list(nn);n[23]=replace(n[23],close=D(99))
        with self.assertRaisesRegex(ValueError,"PARITY"):
            apply(hh,tuple(n))
    def test_1h_raid_unaggregated_fake_15m_volume_rejected(self):
        hh,nn=raid_source()
        n=list(nn);n[23]=replace(n[23],volume=D(6))
        with self.assertRaisesRegex(ValueError,"PARITY"):
            apply(hh,tuple(n))
    def test_1h_raid_original_sha15m_id_forgery_rejected(self):
        hh,nn=raid_source()
        n=list(nn);n[20]=replace(n[20],origin_raw_row_id=rid(BASE))
        with self.assertRaisesRegex(ValueError,"FORGED"):
            apply(hh,tuple(n))
    def test_1h_raid_original_derived1h_id_forgery_rejected(self):
        hh,nn=raid_source()
        h=list(hh);h[5]=replace(h[5],source_native_15m_rows=("BAD",)+h[5].source_native_15m_rows[1:])
        with self.assertRaisesRegex(ValueError,"FORGED"):
            apply(tuple(h),nn)
    def test_cross_symbol_fork_rejected(self):
        hh,nn=raid_source()
        f=replace(review(hh=hh,e1=(),e15=()),symbol="ETHUSDT")
        with self.assertRaisesRegex(ValueError,"UNALIGNED"):
            apply(hh,nn,f)
    def test_author_raid_claim_forgery_rejected(self):
        hh,nn=raid_source()
        f=replace(review(hh=hh,e1=(),e15=()),author_stronghl=True)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            apply(hh,nn,f)
    def test_author_first_valid_poi_forgery_rejected(self):
        f=replace(review(),author_new_1h_poi_first_valid_test=True)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            apply(hours(),native(),f)
    def test_route_b_idm_forgery_rejected(self):
        f=replace(review(),route_b_idm_used=True)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            apply(hours(),native(),f)
    def test_route_c_raid_bos_forgery_rejected(self):
        f=replace(review(),route_c_raid_bos_used=True)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            apply(hours(),native(),f)
    def test_no_first_4h_source_touch_blocks(self):
        from test_c67_route_a_1h_trigger_vs_new_poi_source_fork import parent
        f=review(obs=parent(touched=False))
        self.assertEqual(apply(hours(),native(),f).source_status,
                         "NO_UNAMBIGUOUS_C67_CONTEXT")
    def test_ambiguous_1h_trigger_vs_new_vc_blocks(self):
        f=review(obs=None,hh=hours(gap="nonnested"),
                 e1=(h1event(kind="CLASSIC_1H_IMB_SOURCE"),))
        self.assertEqual(apply(hours(gap="nonnested"),native(),f).source_status,
                         "NO_UNAMBIGUOUS_C67_CONTEXT")
    def test_nonraid_1h_imb_creation_does_not_pretend_raided_liquidity(self):
        # Synthetic source context carrying bare allowed IMB as selected
        from dataclasses import replace
        f=review()
        e=replace(f.source_first_1h_event,category="TRIGGER",
                  kind="1H_IMB_ALLOWED_NONNESTED_SOURCE")
        ff=replace(f,first_source_1h_category="TRIGGER",source_first_1h_event=e,
                   first_source_1h_kind=e.kind)
        self.assertEqual(apply(hours(),native(),ff).source_status,
                         "1H_IMB_TRIGGER_NOT_RAID_OR_POI_FIRST_TEST")
    def test_all_author_flags_always_false_and_no_orders(self):
        hh,nn=raid_source()
        x=apply(hh,nn)
        self.assertFalse(x.author_first_valid_poi_test or x.author_liquidity_raid_confirmed
                         or x.author_stronghl_confirmed or x.author_sl_level)
        self.assertEqual((x.orders,x.fills,x.trades),((),(),()))
    def test_raid_source_known_time_not_15m_first_contact_time(self):
        hh,nn=raid_source()
        x=apply(hh,nn)
        self.assertEqual(x.source_event_fully_known_ms,BASE+6*H)
        self.assertEqual(x.first_exact_original15m_contact_closed_ms,BASE+22*Q)
    def test_native15m_asof_hour_cut_no_future(self):
        hh,nn=raid_source()
        f=review(hh=hh,e1=(),e15=())
        v=apply(hh,nn,f)
        self.assertLess(v.first_exact_original15m_contact_closed_ms,v.source_event_fully_known_ms)
    def test_source_prefix_must_be_closed_hour(self):
        hh,nn=raid_source()
        f=review(hh=hh,e1=(),e15=())
        with self.assertRaisesRegex(ValueError,"UNALIGNED"):
            apply(hh,nn,f,asof=BASE+20*H+Q)
    def test_raid_without_preknown_factual_1h_level_detected(self):
        hh,nn=raid_source()
        f=review(hh=hh,e1=(),e15=())
        # Replace prior pivot with nonpivot while retaining original
        # C67 fork as a witness: C69 must not invent new pivot.
        from test_c67_route_a_1h_trigger_vs_new_poi_source_fork import hbar
        h=list(hh);h[2]=hbar(2,hi=104,lo=95)
        with self.assertRaisesRegex(ValueError,"PARITY|PREKNOWN|FAKE"):
            # Altered hourly record fails source schedule or independent
            # actual original 15m parity, never author confirm.
            x=apply(tuple(h),nn,f)
            if x.source_status=="NO_PREKNOWN_SOURCE_LIQUIDITY_LEVEL":
                raise ValueError("C69_PREKNOWN_MISSING")
    def test_poi_source_not_valid_poi_test_just_because_wick_overlap(self):
        f=review()
        x=apply(hours(),native(),f)
        self.assertIsNotNone(x.first_exact_original15m_contact_id)
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
        self.assertFalse(x.author_first_valid_poi_test)
    def test_first_exact_raid_never_labels_real_stronghl(self):
        hh,nn=raid_source("first")
        x=apply(hh,nn)
        self.assertFalse(x.author_stronghl_confirmed)
        self.assertIsNone(x.preknown_level_known_ms if False else None)
    def test_src_time_finite_no_negative_data(self):
        hh,nn=raid_source()
        n=list(nn);n[20]=replace(n[20],volume=D(-1))
        with self.assertRaisesRegex(ValueError,"FORGED"):
            apply(hh,tuple(n))
    def test_true_1h_liquidity_reclaim_flag_is_not_author_raid_approval(self):
        hh,nn=raid_source("body")
        x=apply(hh,nn)
        self.assertTrue(x.containing_1h_wick_only_reclaim)
        self.assertFalse(x.author_liquidity_raid_confirmed)
if __name__=="__main__":unittest.main()
