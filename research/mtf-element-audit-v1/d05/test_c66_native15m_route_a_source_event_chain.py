"""C66 native15m source-only Route A lower-TF chronology and author veto."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c16_c08_monthly_daily_htf_lineage import NativeKline,TF_MS,SEPT_START
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    SourceReactionEvent,source_first_any_after_contact)
from c66_native15m_route_a_source_event_chain import (
    scan_original15m_source,route_a_15m_source_review,Source15Event,Q,H)
BASE=SEPT_START+8*H
SHA="a"*64
THREE=180000
def rid(t):return SHA+":"+str(t)
def make_bar(i,op=100,hi=102,lo=98,cl=100,vol=20):
    t=BASE+i*Q
    return NativeKline("BTCUSDT","15m",t,t+Q,
        *tuple(D(str(v)) for v in (op,hi,lo,cl,vol)),rid(t),SHA)
def bars(style="liquidity",n=24):
    a=[make_bar(i) for i in range(n)]
    if style=="liquidity":
        a[0]=make_bar(0,100,106,90,101)
        a[1]=make_bar(1,101,105,80,99)
        a[2]=make_bar(2,99,105,91,100)
        a[8]=make_bar(8,100,105,79,95)
        a[9]=make_bar(9,95,107,94,106)
        a[10]=make_bar(10,106,113,101,110)
    elif style=="gap":
        a[0]=make_bar(0,90,100,87,98)
        a[1]=make_bar(1,98,108,97,105)
        a[2]=make_bar(2,116,121,115,118)
        a[3]=make_bar(3,118,120,116,117)
        for i in range(4,8):a[i]=make_bar(i,118,122,116,118)
        a[8]=make_bar(8,121,124,112,118)
        a[9]=make_bar(9,118,127,117,125)
        a[10]=make_bar(10,125,131,120,130)
    elif style=="bare":
        a[8]=make_bar(8,100,105,95,96)
        a[9]=make_bar(9,96,107,94,106)
        a[10]=make_bar(10,106,113,101,110)
    return tuple(a)
def chain(side="LONG",status=None,touch=True):
    event=SourceReactionEvent("BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE",
        side,BASE+H,BASE+2*H,rid(BASE+H),"SYNTHETIC_ONLY")
    return source_first_any_after_contact(symbol="BTCUSDT",side="LONG",
        zone_known_ms=BASE,
        first_original3m_id=rid(BASE) if touch else None,
        first_contact_known_ms=BASE+THREE if touch else None,
        events=(event,),as_of_ms=BASE+6*H)
def make_event(known=BASE+11*Q,side="LONG",kind="15M_CLASSIC_IMB_SOURCE_ONLY"):
    return Source15Event(kind,side,known-3*Q,known,rid(known-3*Q),
        rid(known-Q),None,"SYNTHETIC_ONLY")
def classify(ev=None,ch=None,asof=BASE+6*H):
    return route_a_15m_source_review(ch or chain(),ev if ev is not None else (),
                                    as_of_ms=asof)

class C66Native15Adversarial(unittest.TestCase):
    def test_native15_strict_three_wick_gap_after_third_closes(self):
        q=bars("gap")
        v=scan_original15m_source(q,as_of_ms=q[-1].known_at_ms)
        self.assertTrue(any(x.kind=="15M_CLASSIC_IMB_SOURCE_ONLY" and
            x.pattern_start_ms==BASE and x.known_ms==BASE+3*Q for x in v))
    def test_native15_imb_does_not_exist_before_final_third_close(self):
        q=bars("gap")
        v=scan_original15m_source(q,as_of_ms=BASE+2*Q)
        self.assertFalse(any(x.pattern_start_ms==BASE and x.kind=="15M_CLASSIC_IMB_SOURCE_ONLY" for x in v))
    def test_snr_requires_prior_unswept_liquidity_work(self):
        q=bars()
        v=scan_original15m_source(q,as_of_ms=q[-1].known_at_ms)
        self.assertTrue(any(x.kind=="15M_SNR_LIQUIDITY_SOURCE_ONLY" and
             x.pattern_start_ms==BASE+8*Q and x.known_ms==BASE+11*Q for x in v))
    def test_snr_source_prior_imb_work_separate_from_liquidity(self):
        q=bars("gap")
        v=scan_original15m_source(q,as_of_ms=q[-1].known_at_ms)
        self.assertTrue(any(x.kind=="15M_SNR_PRIOR_IMB_SOURCE_ONLY" and
             x.pattern_start_ms==BASE+8*Q and x.known_ms==BASE+11*Q for x in v))
    def test_mb_without_liquidity_or_imb_not_volume_confirmation(self):
        q=bars("bare")
        v=scan_original15m_source(q,as_of_ms=q[-1].known_at_ms)
        self.assertFalse(any(x.kind.startswith("15M_SNR") and x.pattern_start_ms==BASE+8*Q for x in v))
    def test_all_native_source_event_ids_bound_to_price_candles(self):
        q=bars("liquidity")
        v=scan_original15m_source(q,as_of_ms=q[-1].known_at_ms)
        for x in v:
            self.assertEqual(x.first_original15m_id,rid(x.pattern_start_ms))
            self.assertEqual(x.last_original15m_id,rid(x.known_ms-Q))
    def test_asof_full_list_equals_physically_truncated_original(self):
        q=bars()
        cut=BASE+12*Q
        a=scan_original15m_source(q,as_of_ms=cut)
        z=scan_original15m_source(q[:12],as_of_ms=cut)
        self.assertEqual(a,z)
    def test_ltf_first_same_direction_remains_technical_not_trade(self):
        z=classify((make_event(),))
        self.assertEqual(z.route_a_branch_status,"FIRST_ANY_15M_SOURCE_SAME_DIRECTION")
        self.assertFalse(z.route_a_author_15m_vc)
        self.assertEqual((z.orders,z.trades,z.fills),((),(),()))
    def test_first_opposite_event_is_not_cherry_picked_away(self):
        z=classify((make_event(side="SHORT"),make_event(known=BASE+13*Q)))
        self.assertEqual(z.route_a_branch_status,"FIRST_ANY_15M_SOURCE_OPPOSITE_DIRECTION")
        self.assertEqual(z.first_any_native15m_side,"SHORT")
    def test_simultaneous_source_15m_two_sides_ambiguous(self):
        z=classify((make_event(),make_event(side="SHORT")))
        self.assertEqual(z.route_a_branch_status,"FIRST_ANY_15M_SOURCE_BOTH_DIRECTIONS")
        self.assertEqual(len(z.first_any_native15m_events),2)
    def test_opposite_first1h_context_blocks_route_a_source_ltf(self):
        z=classify((make_event(),),chain("SHORT"))
        self.assertEqual(z.route_a_branch_status,"OPPOSITE_1H_SOURCE_DIRECTION")
    def test_ambiguous_first1h_context_does_not_infer_entry(self):
        c=chain()
        z=replace(c,status="FIRST_ANY_BOTH_SIDES_AMBIGUOUS",
                  first_any_side="BOTH",
                  first_any_source_events=(c.first_any_source_events[0],
                      replace(c.first_any_source_events[0],side="SHORT")))
        self.assertEqual(classify((make_event(),),z).route_a_branch_status,
                         "AMBIGUOUS_1H_SOURCE_DIRECTION")
    def test_no_4h_first_contact_no_15m_branch(self):
        z=classify((make_event(),),chain(touch=False))
        self.assertEqual(z.route_a_branch_status,"NO_4H_FIRST_SOURCE_TOUCH")
    def test_1h_event_missing_remains_unresolved_not_signal(self):
        c=replace(chain(),status="FULL_WINDOW_NO_SOURCE_EVENT",
            first_any_source_event_known_ms=None,
            first_any_source_events=(),first_any_side=None)
        self.assertEqual(classify((make_event(),),c).route_a_branch_status,
                         "NO_FIRST_CLOSED_1H_SOURCE_EVENT")
    def test_author_1h_source_poi_claim_is_blocked(self):
        c=replace(chain(),has_author_vc_or_bos=True)
        with self.assertRaisesRegex(ValueError,"FORGED"):
            classify((make_event(),),c)
    def test_author_15m_volume_confirmation_forgery_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            classify((replace(make_event(),author_volume_confirmation=True),))
    def test_author_15m_entry_forgery_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            classify((replace(make_event(),author_entry=True),))
    def test_15m_order_forgery_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            classify((replace(make_event(),orders=("FAKE",)),))
    def test_future_15m_event_rejected_even_when_outside_window(self):
        with self.assertRaisesRegex(ValueError,"FUTURE"):
            classify((make_event(known=BASE+8*H),))
    def test_wrong_first_raw15_source_id_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            classify((replace(make_event(),first_original15m_id=rid(BASE)),))
    def test_wrong_last_raw15_source_id_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            classify((replace(make_event(),last_original15m_id=rid(BASE)),))
    def test_bad_15m_event_duration_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            classify((replace(make_event(),known_ms=BASE+12*Q),))
    def test_15m_event_pattern_before_1h_closes_not_admitted(self):
        z=classify((make_event(known=BASE+7*Q),make_event(known=BASE+12*Q)))
        self.assertEqual(z.first_any_native15m_technical_event_ms,BASE+12*Q)
    def test_15m_no_event_right_censored(self):
        z=classify()
        self.assertEqual(z.route_a_branch_status,"NO_15M_SOURCE_CANDIDATE_RIGHT_CENSORED")
    def test_15m_no_event_full_window(self):
        z=classify((),asof=BASE+27*H)
        self.assertEqual(z.route_a_branch_status,"NO_15M_SOURCE_CANDIDATE_FULL_WINDOW")
    def test_15m_source_not_allowed_to_evaluate_route_b(self):
        z=classify((make_event(),))
        self.assertFalse(z.route_b_idm_evaluated or z.route_c_raid_bos_evaluated)
    def test_native15_forged_raw_sha_rejected(self):
        q=list(bars());q[1]=replace(q[1],origin_raw_row_id="FAKE")
        with self.assertRaisesRegex(ValueError,"FORGED"):
            scan_original15m_source(tuple(q),as_of_ms=q[-1].known_at_ms)
    def test_native15_negative_volume_rejected(self):
        q=list(bars());q[1]=replace(q[1],volume=D("-1"))
        with self.assertRaisesRegex(ValueError,"FORGED"):
            scan_original15m_source(tuple(q),as_of_ms=q[-1].known_at_ms)
    def test_native15_nonfinite_price_rejected(self):
        q=list(bars());q[1]=replace(q[1],low=D("NaN"))
        with self.assertRaisesRegex(ValueError,"FORGED"):
            scan_original15m_source(tuple(q),as_of_ms=q[-1].known_at_ms)
    def test_native15_source_gap_rejected(self):
        q=bars();s=q[:5]+q[6:]
        with self.assertRaisesRegex(ValueError,"FORGED"):
            scan_original15m_source(s,as_of_ms=q[-1].known_at_ms)
    def test_unclosed_native15_source_asof_rejected(self):
        q=bars()
        with self.assertRaisesRegex(ValueError,"INVALID"):
            scan_original15m_source(q,as_of_ms=q[-1].known_at_ms+1)
    def test_first1h_event_missing_original_chronology_rejected(self):
        c=replace(chain(),first_any_source_events=())
        with self.assertRaisesRegex(ValueError,"FORGED"):
            classify((make_event(),),c)
    def test_right_censored_15m_source_not_author_success(self):
        z=classify(())
        self.assertFalse(z.window_full or z.route_a_author_1h_trigger or
                         z.route_a_author_new_1h_vc_poi_test or z.author_15m_stronghl)
if __name__=="__main__":unittest.main()
