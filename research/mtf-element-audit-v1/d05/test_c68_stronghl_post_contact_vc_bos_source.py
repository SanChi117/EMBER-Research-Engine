"""C68 strict source chronology negative tests; no owner StrongHL upgrade."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from test_c67_route_a_1h_trigger_vs_new_poi_source_fork import (
    BASE,H,Q,SHA,rid,parent,review,hours,native,event15,h1event,nbar)
from c68_stronghl_post_contact_vc_bos_source import (
    observe_source_stronghl_after_contact,STATES)
from c63_closed_4h_source_contact_to_first_any_1h_reaction import SourceReactionEvent
from c66_native15m_route_a_source_event_chain import Source15Event

def run(fork=None,nn=None,e15=None,e1=(),asof=BASE+20*H):
    if fork is None:fork=review(asof=asof)
    return observe_source_stronghl_after_contact(
      fork,nn if nn is not None else native(n=(asof-BASE)//Q),
      e15 if e15 is not None else (event15(),),
      e1,as_of_ms=asof)

def bos(start=BASE+8*H,side="LONG"):
    return SourceReactionEvent("BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE",
          side,start,start+H,rid(start),"STRICT_PREKNOWN_SOURCE_NOT_AUTHOR")

class C68Adversarial(unittest.TestCase):
    def test_new1h_poi_15m_contact_then_15m_imb_confirmation_candidate(self):
        x=run()
        self.assertEqual(x.source_status,"SOURCE_EXTREME_WITH_POST_CONTACT_CONFIRMATION_NOT_AUTHOR")
        self.assertEqual(x.source_first_any_confirmation_kind,"15M_CLASSIC_IMB_SOURCE_ONLY")
        self.assertIsNotNone(x.source_extreme_anchor_price)
        self.assertFalse(x.author_verified_stronghl)
        self.assertEqual((x.orders,x.fills,x.trades),((),(),()))
    def test_confirmation_must_be_after_first_source_touch(self):
        x=run(e15=(event15(start=BASE+7*H),))
        self.assertEqual(x.source_status,"NO_POST_CONTACT_SOURCE_CONFIRMATION_RIGHT_CENSORED")
    def test_earliest_15m_opposite_not_later_favorable_selected(self):
        x=run(e15=(event15(side="SHORT"),event15(start=BASE+9*H)))
        self.assertEqual(x.source_status,"FIRST_ANY_SOURCE_CONFIRMATION_OPPOSITE_SIDE")
        self.assertIsNone(x.source_extreme_anchor_price)
    def test_earliest_15m_dual_sides_unresolved(self):
        x=run(e15=(event15(),event15(side="SHORT")))
        self.assertEqual(x.source_status,"FIRST_ANY_SOURCE_CONFIRMATION_BOTH_SIDES_AMBIGUOUS")
    def test_earliest_1h_bos_source_candidate(self):
        x=run(e15=(),e1=(bos(),))
        self.assertEqual(x.source_first_any_confirmation_kind,"1H_SOURCE_BOS_PREKNOWN_FRACTAL_CLOSE")
        self.assertEqual(x.source_status,"SOURCE_EXTREME_WITH_POST_CONTACT_CONFIRMATION_NOT_AUTHOR")
        self.assertFalse(x.author_verified_vc_or_bos)
    def test_1h_bos_proxy_opposite_first_not_author_break(self):
        x=run(e15=(),e1=(bos(side="SHORT"),))
        self.assertEqual(x.source_status,"FIRST_ANY_SOURCE_CONFIRMATION_OPPOSITE_SIDE")
        self.assertFalse(x.author_verified_of)
    def test_bos_future_started_before_source_contact_rejected_by_filter(self):
        x=run(e15=(),e1=(bos(start=BASE+6*H),))
        self.assertEqual(x.source_status,"NO_POST_CONTACT_SOURCE_CONFIRMATION_RIGHT_CENSORED")
    def test_c67_first_opposite_1h_context_no_stronghl(self):
        f=review(e1=(h1event(side="SHORT"),))
        x=run(fork=f)
        self.assertEqual(x.source_status,"NO_C67_SINGLE_SOURCE_CONTACT")
    def test_c67_both_1h_sides_not_stronghl(self):
        f=review(e1=(h1event(side="SHORT"),h1event(side="LONG")))
        x=run(fork=f)
        self.assertEqual(x.source_status,"NO_C67_SINGLE_SOURCE_CONTACT")
    def test_source_trigger_ltf_confirmation_requires_later_bars(self):
        f=review(hh=hours(raid=True),e1=(),e15=(event15(),))
        x=run(fork=f)
        self.assertEqual(x.source_contact_kind,"ADAPTED_1H_RAID_LAST_NATIVE15M_BAR")
        self.assertEqual(x.source_status,"SOURCE_EXTREME_WITH_POST_CONTACT_CONFIRMATION_NOT_AUTHOR")
    def test_non_raid_1h_gap_creation_does_not_prove_liquidity_contact(self):
        # Use C67 source-ambiguous 1H IMB context, if no selected raid.
        f=review(hh=hours(gap="nonnested"),obs=parent(hi=110),
                 e1=(h1event(kind="CLASSIC_1H_IMB_SOURCE"),))
        x=run(fork=f)
        self.assertEqual(x.source_status,"NO_C67_SINGLE_SOURCE_CONTACT")
    def test_source_no_parent_touch_veto(self):
        f=review(obs=parent(touched=False))
        self.assertEqual(run(fork=f).source_status,"NO_C67_SINGLE_SOURCE_CONTACT")
    def test_source_new_poi_without_15m_test_veto(self):
        f=review(hh=hours(newpoi_range=(190,200)))
        self.assertEqual(run(fork=f).source_status,"NO_C67_SINGLE_SOURCE_CONTACT")
    def test_no_confirmation_full_window_is_not_success(self):
        asof=BASE+42*H
        f=review(hh=hours(n=42),nn=native(n=168),asof=asof,e15=())
        x=run(fork=f,nn=native(168),e15=(),asof=asof)
        self.assertEqual(x.source_status,"NO_POST_CONTACT_SOURCE_CONFIRMATION_FULL_WINDOW")
    def test_no_confirmation_incomplete_window_right_censored(self):
        x=run(e15=())
        self.assertEqual(x.source_status,"NO_POST_CONTACT_SOURCE_CONFIRMATION_RIGHT_CENSORED")
        self.assertFalse(x.source_fully_observed_window)
    def test_preconfirmation_wick_breach_veto(self):
        a=list(native());a[32]=nbar(32,hi=105,lo=80)
        x=run(nn=tuple(a))
        self.assertEqual(x.source_status,"SOURCE_ANCHOR_BREACHED_BEFORE_CONFIRMATION_CLOSED")
        self.assertIsNone(x.source_anchor_protected_only_after_ms)
    def test_low_equal_anchor_not_breach(self):
        x=run()
        self.assertEqual(x.source_status,"SOURCE_EXTREME_WITH_POST_CONTACT_CONFIRMATION_NOT_AUTHOR")
    def test_preconfirmation_source_extreme_protected_only_after_closed_event(self):
        x=run()
        self.assertEqual(x.source_anchor_protected_only_after_ms,event15().known_ms)
    def test_source_extreme_min_price_for_long(self):
        a=list(native());a[29]=nbar(29,hi=105,lo=91)
        x=run(nn=tuple(a))
        self.assertEqual(x.source_extreme_anchor_price,"91")
        self.assertEqual(x.source_extreme_first_original15m_id,rid(BASE+29*Q))
    def test_source_extreme_max_for_short_with_opposite_source_case(self):
        # C67 first 1H source event direction opposite to parent is vetoed,
        # so a fabricated short confirmation cannot become strong high.
        f=review(e1=(h1event(side="SHORT"),))
        self.assertEqual(run(fork=f,e15=(event15(side="SHORT"),)).source_status,
                         "NO_C67_SINGLE_SOURCE_CONTACT")
    def test_fake_author_1h_vc_poi_rejected(self):
        f=replace(review(),author_new_1h_vc_poi=True)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            run(fork=f)
    def test_fake_author_4h_poi_first_valid_retest_rejected(self):
        f=replace(review(),author_4h_poi_first_valid_test=True)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            run(fork=f)
    def test_fake_author_stronghl_claim_rejected(self):
        f=replace(review(),author_stronghl=True)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            run(fork=f)
    def test_fake_author_15m_vc_claim_rejected(self):
        e=replace(event15(),author_volume_confirmation=True)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            run(e15=(e,))
    def test_fake_15m_order_claim_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            run(e15=(replace(event15(),orders=("BUY",)),))
    def test_fake_author_1h_bos_claim_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            run(e15=(),e1=(replace(bos(),is_author_bos=True),))
    def test_fake_original15m_raw_sha_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            run(e15=(replace(event15(),first_original15m_id=rid(BASE)),))
    def test_fake_1h_bos_source_raw_sha_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            run(e15=(),e1=(replace(bos(),raw_first_original15m_id="FAKE"),))
    def test_future_15m_source_confirmation_rejected(self):
        with self.assertRaisesRegex(ValueError,"FUTURE"):
            run(e15=(event15(start=BASE+21*H),))
    def test_future_1h_bos_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"FUTURE"):
            run(e15=(),e1=(bos(start=BASE+21*H),))
    def test_cross_symbol_fork_cannot_borrow_source_prices(self):
        f=replace(review(),symbol="SOLUSDT")
        with self.assertRaisesRegex(ValueError,"MISMATCH"):
            run(fork=f)
    def test_original15m_gap_in_raw_history_rejected(self):
        a=native()
        with self.assertRaisesRegex(ValueError,"FORGED"):
            run(nn=a[:2]+a[3:])
    def test_ltf_full_bar_prefix_asof_no_lookahead(self):
        x=run()
        self.assertLessEqual(x.source_first_any_confirmation_known_ms,BASE+20*H)
        self.assertFalse(x.route_b_idm_evaluated or x.route_c_raid_bos_evaluated)
if __name__=="__main__":unittest.main()
