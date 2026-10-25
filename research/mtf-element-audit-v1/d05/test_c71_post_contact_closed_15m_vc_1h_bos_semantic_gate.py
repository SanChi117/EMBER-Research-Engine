"""C71 adversarial chronology Route A source != owner VC/BOS."""
import unittest
from dataclasses import replace
from test_c67_route_a_1h_trigger_vs_new_poi_source_fork import (
    BASE,H,Q,rid,hours,native,review,event15,parent,h1event)
from test_c69_exact_native15m_first_liquidity_raid_vs_poi_test import raid_source
from test_c70_exact_native3m_first_raid_or_poi_source_wick import rows
from test_c68_stronghl_post_contact_vc_bos_source import bos
from c69_exact_native15m_first_liquidity_raid_vs_poi_test import first_original_native15m_source_contact
from c70_exact_native3m_first_raid_or_poi_source_wick import original3m_first_wick_within_c69
from c71_post_contact_closed_15m_vc_1h_bos_semantic_gate import classify_after_original3m_contact,STATES
def build(raid=False,e15=None,e1=None,n=20,asof=None):
    if asof is None:asof=BASE+n*H
    if raid:
        h,x=raid_source()
        if n!=20:
            # synthetic 1H raid 5H with longer record while preserving OHLCV
            h=list(hours(raid=True,n=n));x=list(native(n*4))
            _,s=raid_source()
            x[20:24]=s[20:24]
            h=tuple(h);x=tuple(x)
    else:h=hours(n=n);x=native(n*4)
    one=() if raid else (h1event(),)
    if e15 is None:e15=(event15(),)
    fork=review(hh=h,nn=x,e1=one,e15=e15,asof=asof)
    c69=first_original_native15m_source_contact(fork,h,x,as_of_ms=asof)
    raw=rows(x)
    c70=original3m_first_wick_within_c69(fork,c69,x,raw,as_of_ms=asof)
    return fork,c69,c70,h,x,raw,tuple(e15),tuple(e1 if e1 is not None else one),asof
def run(z=None,**kwargs):
    if z is None:z=build(**kwargs)
    f,g,k,h,n,raw,e15,e1,asof=z
    return classify_after_original3m_contact(f,g,k,n,raw,h,e15,e1,as_of_ms=asof)
class C71SourceNotOwnerVC(unittest.TestCase):
    def test_new_1h_poi_first_15m_imb_not_author_vc_or_5m_confirmation(self):
        x=run()
        self.assertEqual(x.state,"FIRST_ANY_NEW1H_POI_15M_IMB_TRIGGER_VS_VC_UNRESOLVED")
        self.assertFalse(x.author_1h_poi_valid_test or x.author_15m_trigger
                         or x.author_15m_vc or x.author_5m_vc)
        self.assertEqual(x.orders,())
    def test_new_1h_poi_15m_snr_not_owner_vc_without_actual_retest(self):
        x=run(e15=(event15(kind="15M_SNR_LIQUIDITY_SOURCE_ONLY"),))
        self.assertEqual(x.state,"FIRST_ANY_NEW1H_POI_15M_SNR_TRIGGER_VS_VC_UNRESOLVED")
        self.assertFalse(x.author_15m_vc)
    def test_raid_branch_first_15m_imb_source_not_author_entry(self):
        x=run(raid=True)
        self.assertEqual(x.state,"FIRST_ANY_15M_IMB_ALIGNED_NOT_AUTHOR_VC")
        self.assertFalse(x.author_4h_poi_valid_test or x.author_1h_trigger)
    def test_raid_branch_first_15m_snr_source_not_author_entry(self):
        x=run(raid=True,e15=(event15(kind="15M_SNR_PRIOR_IMB_SOURCE_ONLY"),))
        self.assertEqual(x.state,"FIRST_ANY_15M_SNR_ALIGNED_NOT_AUTHOR_VC")
    def test_first_opposite_15m_source_never_ignore_for_later_favorable(self):
        x=run(e15=(event15(side="SHORT"),event15(start=BASE+9*H)))
        self.assertEqual(x.state,"FIRST_ANY_SOURCE_OPPOSITE_DIRECTION")
        self.assertEqual(x.first_any_source_event_sides,("SHORT",))
    def test_first_both_sides_15m_same_close_ambiguous(self):
        x=run(e15=(event15(side="SHORT"),event15()))
        self.assertEqual(x.state,"FIRST_ANY_SOURCE_TWO_DIRECTIONS_AMBIGUOUS")
    def test_first_1h_bos_closed_before_later_15m_does_not_become_15m_vc(self):
        x=run(e15=(event15(start=BASE+9*H),), e1=(h1event(),bos(start=BASE+8*H)))
        self.assertEqual(x.state,"FIRST_ANY_1H_BOS_PROXY_NOT_AUTHOR_VC_OR_BOS")
        self.assertFalse(x.author_1h_bos or x.author_15m_vc)
    def test_opposite_1h_bos_first_is_not_favorable(self):
        x=run(e15=(event15(start=BASE+9*H),), e1=(h1event(),bos(start=BASE+8*H,side="SHORT")))
        self.assertEqual(x.state,"FIRST_ANY_SOURCE_OPPOSITE_DIRECTION")
    def test_1h_bos_and_15m_source_same_close_no_cross_tf_cherry_pick(self):
        x=run(e15=(event15(start=BASE+8*H+Q),),
              e1=(h1event(),bos(start=BASE+8*H)))
        self.assertEqual(x.state,"FIRST_ANY_SOURCE_SAME_TIME_15M_AND_1H_BOS_AMBIGUOUS")
    def test_15m_source_same_time_two_kinds_unresolved(self):
        x=run(e15=(event15(),event15(kind="15M_SNR_PRIOR_IMB_SOURCE_ONLY")))
        self.assertEqual(x.state,"FIRST_ANY_SOURCE_SAME_TIME_MULTIPLE_15M_KINDS_AMBIGUOUS")
    def test_pre_contact_pattern_started_before_native3m_gate_ignored(self):
        x=run(e15=(event15(start=BASE+6*H),))
        self.assertEqual(x.state,"NO_FIRST_ANY_SOURCE_POST_GATE_RIGHT_CENSORED")
    def test_hour_raided_before_full_1h_close_never_backdate_15m_event(self):
        z=build(raid=True,e15=(event15(start=BASE+5*H+2*Q),))
        x=run(z)
        self.assertEqual(x.state,"NO_FIRST_ANY_SOURCE_POST_GATE_RIGHT_CENSORED")
        self.assertEqual(x.earliest_event_pattern_start_gate_ms,BASE+6*H)
        self.assertLess(x.source_first3m_contact_closed_ms,x.earliest_event_pattern_start_gate_ms)
    def test_no_post_source_event_right_censored(self):
        x=run(e15=(),e1=())
        self.assertEqual(x.state,"NO_FIRST_ANY_SOURCE_POST_GATE_RIGHT_CENSORED")
        self.assertFalse(x.fully_observed_window)
    def test_no_post_source_event_full_24h(self):
        x=run(n=50,e15=(),e1=())
        self.assertEqual(x.state,"NO_FIRST_ANY_SOURCE_POST_GATE_FULL_WINDOW")
        self.assertTrue(x.fully_observed_window)
    def test_unknown_4h_first_source_contact_failclosed(self):
        from dataclasses import replace
        z=list(build())
        f=review(obs=parent(touched=False))
        # valid source C70 still belongs to old parent; mismatch refused.
        z[0]=f
        with self.assertRaisesRegex(ValueError,"DRIFT|PARENT|MISMATCH"):
            run(tuple(z))
    def test_ambiguous_C69_multiple_preknown_levels_cannot_create_source_vc(self):
        h,n=raid_source("first",multi=True)
        f=review(hh=h,nn=n,e1=(),e15=(event15(),))
        g=first_original_native15m_source_contact(f,h,n,as_of_ms=BASE+20*H)
        raw=rows(n);k=original3m_first_wick_within_c69(f,g,n,raw,as_of_ms=BASE+20*H)
        x=run((f,g,k,h,n,raw,(event15(),),(),BASE+20*H))
        self.assertEqual(x.state,"NO_UNAMBIGUOUS_ORIGINAL3M_CONTACT")
    def test_C70_forged_3m_raw_wick_cannot_pass_independent_recomputation(self):
        z=list(build())
        z[2]=replace(z[2],actual_first_native3m_id="FAKE")
        with self.assertRaisesRegex(ValueError,"DRIFT"):
            run(tuple(z))
    def test_C70_backdated_3m_claim_is_not_accepted(self):
        z=list(build())
        z[2]=replace(z[2],earliest_source_claim_eligible_ms=BASE)
        with self.assertRaisesRegex(ValueError,"DRIFT"):
            run(tuple(z))
    def test_fake_15m_author_volume_confirmation_rejected(self):
        z=list(build());z[6]=(replace(event15(),author_volume_confirmation=True),)
        with self.assertRaisesRegex(ValueError,"AUTHOR"):
            run(tuple(z))
    def test_fake_15m_placed_order_rejected(self):
        z=list(build());z[6]=(replace(event15(),orders=("BUY",)),)
        with self.assertRaisesRegex(ValueError,"AUTHOR"):
            run(tuple(z))
    def test_fake_15m_start_raw_ID_rejected(self):
        z=list(build());z[6]=(replace(event15(),first_original15m_id=rid(BASE)),)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            run(tuple(z))
    def test_fake_1h_owner_bos_claim_rejected(self):
        z=list(build());z[7]=(replace(bos(),is_author_bos=True),)
        with self.assertRaisesRegex(ValueError,"AUTHOR"):
            run(tuple(z))
    def test_fake_1h_bos_wrong_native15m_provenance_rejected(self):
        z=list(build());z[7]=(replace(bos(),raw_first_original15m_id="FAKE"),)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            run(tuple(z))
    def test_future_15m_event_rejected_before_display(self):
        z=list(build());z[6]=(event15(start=BASE+21*H),)
        with self.assertRaisesRegex(ValueError,"FUTURE"):
            run(tuple(z))
    def test_future_1h_bos_rejected_before_display(self):
        z=list(build());z[7]=(bos(start=BASE+21*H),)
        with self.assertRaisesRegex(ValueError,"FUTURE"):
            run(tuple(z))
    def test_route_B_IDM_cannot_be_carried_into_route_A(self):
        z=list(build());z[0]=replace(z[0],route_b_idm_used=True)
        with self.assertRaisesRegex(ValueError,"AUTHOR_PROMOTED"):
            run(tuple(z))
    def test_route_C_raid_BOS_cannot_be_carried_into_route_A(self):
        z=list(build());z[0]=replace(z[0],route_c_raid_bos_used=True)
        with self.assertRaisesRegex(ValueError,"AUTHOR_PROMOTED"):
            run(tuple(z))
    def test_source_author_poI_first_valid_is_never_claimed_by_wick(self):
        x=run()
        self.assertFalse(x.author_4h_poi_valid_test or x.author_1h_poi_valid_test)
        self.assertFalse(x.author_1h_trigger or x.author_15m_vc or x.author_5m_vc)
        self.assertFalse(x.author_stronghl or x.author_1h_bos)
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_five_original3m_to15m_price_parity_inherited_not_forged(self):
        x=run()
        self.assertTrue(x.source_first_3m_native15m_decimal_parity)
        self.assertIsNotNone(x.source_first3m_contact_id)
    def test_earliest_closed_source_time_never_before_gate(self):
        x=run()
        self.assertGreaterEqual(x.first_any_confirmed_event_ms,
                                x.earliest_event_pattern_start_gate_ms)
        self.assertEqual((x.orders,x.fills,x.trades),((),(),()))
if __name__=="__main__":unittest.main()
