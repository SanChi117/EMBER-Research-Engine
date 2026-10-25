"""C67 explicit independent Route A branch tests, never authorize trades."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c16_c08_monthly_daily_htf_lineage import (
    DerivedClosedTF,NativeKline,SEPT_START,TF_MS)
from c46_original_4h_classic_imb_first_contact import (
    FourHourImbCandidate,PoiContactObservation)
from c63_closed_4h_source_contact_to_first_any_1h_reaction import SourceReactionEvent
from c66_native15m_route_a_source_event_chain import Source15Event
from c67_route_a_1h_trigger_vs_new_poi_source_fork import (
    observe_1h_route_a_source_events,route_a_fork_1h_to_15m,FORK_STATES)
H=TF_MS["1h"];Q=TF_MS["15m"];M3=180000
BASE=SEPT_START+8*H;SHA="a"*64
def rid(t):return SHA+":"+str(t)
def hbar(i,hi=105,lo=95,op=100,cl=100):
    t=BASE+i*H
    return DerivedClosedTF("BTCUSDT","1h",t,t+H,
      D(str(op)),D(str(hi)),D(str(lo)),D(str(cl)),D(20),
      tuple(rid(t+j*Q) for j in range(4)),(SHA,))
def nbar(i,hi=105,lo=95,op=100,cl=100):
    t=BASE+i*Q
    return NativeKline("BTCUSDT","15m",t,t+Q,
      D(str(op)),D(str(hi)),D(str(lo)),D(str(cl)),D(5),rid(t),SHA)
def hours(raid=False,gap=None,newpoi_range=None,n=20):
    a=[hbar(i) for i in range(n)]
    if raid:
        a[1]=hbar(1,hi=105,lo=96)
        a[2]=hbar(2,hi=104,lo=80)
        a[3]=hbar(3,hi=105,lo=96)
        a[5]=hbar(5,hi=105,lo=79,op=100,cl=100)
    if gap=="nested":
        a[5]=hbar(5,hi=100,lo=94)
        a[6]=hbar(6,hi=110,lo=99)
        a[7]=hbar(7,hi=116,lo=109,op=112,cl=113)
    if gap=="nonnested":
        a[5]=hbar(5,hi=100,lo=94)
        a[6]=hbar(6,hi=115,lo=99)
        a[7]=hbar(7,hi=122,lo=117,op=118,cl=119)
    if newpoi_range is not None:
        lo,hi=newpoi_range
        a[5]=hbar(5,hi=hi,lo=lo,op=hi-2,cl=hi-1)
        a[6]=hbar(6,hi=hi,lo=lo,op=hi-2,cl=hi-1)
    return tuple(a)
def native(n=80):
    return tuple(nbar(i) for i in range(n))
def parent(touched=True,lo=90,hi=120,side="LONG"):
    x=FourHourImbCandidate(side,str(lo),str(hi),BASE,
        BASE-12*H,BASE-8*H,BASE-4*H,
        tuple(rid(BASE-i*4*H) for i in (3,2,1)),
        tuple(rid(BASE-i*4*H-M3) for i in (2,1,0)))
    return PoiContactObservation(x,BASE if touched else None,
        BASE+M3 if touched else None,rid(BASE) if touched else None,
        True,"SYNTHETIC_SOURCE_TOUCH" if touched else "UNTOUCHED")
def h1event(kind="RB_1H_SOURCE",side="LONG",start=BASE+5*H):
    duration=3*H if kind in ("CLASSIC_1H_IMB_SOURCE","SNR_1H_SOURCE") else 2*H
    return SourceReactionEvent(kind,side,start,start+duration,rid(start),
        "SYNTHETIC_SOURCE_NOT_AUTHOR")
def event15(start=BASE+8*H,side="LONG",kind="15M_CLASSIC_IMB_SOURCE_ONLY"):
    return Source15Event(kind,side,start,start+3*Q,rid(start),rid(start+2*Q),
                         None,"SYNTHETIC_ORIGINAL_SHA_SOURCE_ONLY")
def review(obs=None,hh=None,nn=None,e1=None,e15=None,asof=BASE+20*H):
    return route_a_fork_1h_to_15m(
       obs if obs is not None else parent(),
       hh if hh is not None else hours(),
       nn if nn is not None else native(),
       e1 if e1 is not None else (h1event(),),
       e15 if e15 is not None else (event15(),),
       as_of_ms=asof)
class C67Adversarial(unittest.TestCase):
    def test_1h_raid_is_trigger_source_not_new_vc(self):
        v,n=observe_1h_route_a_source_events(parent(),hours(raid=True),(),as_of_ms=BASE+20*H)
        self.assertEqual(n,0)
        self.assertTrue(any(x.kind=="1H_SSL_RAID_SOURCE" for x in v))
        self.assertFalse(any(x.category=="NEW_1H_VC_POI" for x in v))
    def test_1h_trigger_then_15m_source_same_direction_not_author(self):
        q=review(hh=hours(raid=True),e1=(),e15=(event15(),))
        self.assertEqual(q.state,"TRIGGER_FIRST_15M_IMB_SNR_SAME_SOURCE")
        self.assertFalse(q.author_1h_trigger or q.author_15m_volume_confirmation)
        self.assertEqual((q.orders,q.fills,q.trades),((),(),()))
    def test_1h_trigger_then_15m_source_opposite_retained(self):
        q=review(hh=hours(raid=True),e1=(),e15=(
            event15(side="SHORT"),event15(BASE+9*H,side="LONG")))
        self.assertEqual(q.state,"TRIGGER_FIRST_15M_IMB_SNR_OPPOSITE_SOURCE")
    def test_1h_trigger_first_both_direction_15m_ambiguous(self):
        q=review(hh=hours(raid=True),e1=(),e15=(
            event15(),event15(side="SHORT")))
        self.assertEqual(q.state,"TRIGGER_FIRST_15M_BOTH_SIDES_AMBIGUOUS")
    def test_1h_trigger_no_15m_24h_right_censored(self):
        q=review(hh=hours(raid=True),e1=(),e15=())
        self.assertEqual(q.state,"TRIGGER_FIRST_NO_15M_SOURCE_RIGHT_CENSORED")
    def test_1h_trigger_no_15m_24h_full_window(self):
        q=review(hh=hours(raid=True,n=40),nn=native(n=160),
                 e1=(),e15=(),asof=BASE+40*H)
        self.assertEqual(q.state,"TRIGGER_FIRST_NO_15M_SOURCE_FULL_WINDOW")
    def test_1h_imb_fully_inside_4h_imb_is_forbidden_trigger(self):
        v,n=observe_1h_route_a_source_events(
            parent(),hours(gap="nested"),
            (h1event(kind="CLASSIC_1H_IMB_SOURCE"),),as_of_ms=BASE+20*H)
        self.assertGreater(n,0)
        self.assertFalse(any(x.kind=="1H_IMB_ALLOWED_NONNESTED_SOURCE" for x in v))
        self.assertTrue(any(x.category=="NEW_1H_VC_POI" for x in v))
    def test_1h_imb_partly_outside_4h_imb_is_not_nested(self):
        v,n=observe_1h_route_a_source_events(
            parent(hi=110),hours(gap="nonnested"),
            (h1event(kind="CLASSIC_1H_IMB_SOURCE"),),as_of_ms=BASE+20*H)
        self.assertTrue(any(x.kind=="1H_IMB_ALLOWED_NONNESTED_SOURCE" for x in v))
    def test_nonnested_1h_imb_is_ambiguous_trigger_vs_vc(self):
        q=review(obs=parent(hi=110),hh=hours(gap="nonnested"),
            e1=(h1event(kind="CLASSIC_1H_IMB_SOURCE"),))
        self.assertEqual(q.state,"FIRST_ANY_1H_TRIGGER_AND_VC_AMBIGUOUS")
    def test_new_1h_rb_source_requires_later_touch_before_15m(self):
        q=review()
        self.assertEqual(q.first_source_1h_category,"NEW_1H_VC_POI")
        self.assertEqual(q.first_source_1h_kind,"1H_NEW_VC_RB_SOURCE")
        self.assertIsNotNone(q.source_first_new_1h_poi_test_native15m_id)
        self.assertEqual(q.state,"NEW_1H_VC_FIRST_SOURCE_TEST_15M_TRIGGER_NEEDS_5M_VC")
        self.assertFalse(q.author_new_1h_poi_first_valid_test)
    def test_new_1h_poi_no_test_no_child_events_promoted(self):
        q=review(hh=hours(newpoi_range=(190,200)))
        self.assertEqual(q.state,"NEW_1H_VC_NO_SUBSEQUENT_POI_SOURCE_TEST")
        self.assertIsNone(q.first_15m_after_gate_kind)
    def test_new_1h_poi_test_no_ltf_vc_is_not_entry(self):
        q=review(e15=())
        self.assertEqual(q.state,"NEW_1H_VC_FIRST_SOURCE_TEST_NO_15M_CANDIDATE")
        self.assertFalse(q.author_new_1h_vc_poi)
    def test_new_1h_poi_test_15m_snr_requires_owner_classification(self):
        q=review(e15=(event15(kind="15M_SNR_LIQUIDITY_SOURCE_ONLY"),))
        self.assertEqual(q.state,"NEW_1H_VC_FIRST_SOURCE_TEST_15M_VC_NO_TRIGGER")
        self.assertFalse(q.author_15m_volume_confirmation)
    def test_new_1h_poi_first_15m_opposite_not_ignored(self):
        q=review(e15=(event15(side="SHORT"),event15(start=BASE+9*H)))
        self.assertEqual(q.state,"NEW_1H_VC_FIRST_SOURCE_TEST_15M_OPPOSITE_SOURCE")
        self.assertEqual(q.first_15m_after_gate_side,"SHORT")
    def test_new_1h_poi_first_15m_opposite_and_same_tie_ambiguous(self):
        q=review(e15=(event15(),event15(side="SHORT")))
        self.assertEqual(q.state,"NEW_1H_VC_FIRST_SOURCE_TEST_15M_TWO_SIDES_AMBIGUOUS")
        self.assertFalse(q.author_15m_volume_confirmation)
    def test_new_1h_poi_15m_event_pretouch_pattern_rejected(self):
        q=review(e15=(event15(start=BASE+7*H),))
        self.assertIsNone(q.first_15m_after_gate_kind)
    def test_before_4h_first_source_touch_no_candidate(self):
        q=review(obs=parent(touched=False))
        self.assertEqual(q.state,"NO_4H_SOURCE_FIRST_TOUCH")
    def test_first_opposite_side_1h_source_is_not_converted_long(self):
        q=review(e1=(h1event(side="SHORT"),))
        self.assertEqual(q.state,"FIRST_ANY_1H_SOURCE_OPPOSITE_SIDE")
    def test_first_two_sides_1h_source_ambiguous(self):
        q=review(e1=(h1event(side="SHORT"),h1event(side="LONG")))
        self.assertEqual(q.state,"FIRST_ANY_1H_TWO_SIDES_AMBIGUOUS")
    def test_first_1h_mixed_trigger_and_vc_same_time_blocks_entry(self):
        # 1h raid bar and 1h RB event are both known at i6
        q=review(hh=hours(raid=True),e1=(h1event(start=BASE+4*H),))
        self.assertEqual(q.state,"FIRST_ANY_1H_TRIGGER_AND_VC_AMBIGUOUS")
    def test_no_1h_events_full_24h_window(self):
        q=review(e1=(),e15=())
        self.assertEqual(q.state,"NO_1H_SOURCE_FORK_RIGHT_CENSORED")
    def test_no_1h_events_right_censored_protected(self):
        q=review(hh=hours(n=10),nn=native(40),e1=(),e15=(),
                 asof=BASE+10*H)
        self.assertEqual(q.state,"NO_1H_SOURCE_FORK_RIGHT_CENSORED")
    def test_owner_fake_4h_certification_rejected(self):
        o=parent()
        with self.assertRaisesRegex(ValueError,"FORGERY"):
            review(obs=replace(o,academic_poi_test_certified=True))
    def test_owner_fake_1h_vc_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID"):
            review(e1=(replace(h1event(),is_author_vc=True),))
    def test_owner_fake_15m_entry_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            review(e15=(replace(event15(),author_entry=True),))
    def test_owner_fake_orders_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            review(e15=(replace(event15(),orders=("FAKE",)),))
    def test_future_1h_source_event_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID"):
            review(e1=(h1event(start=BASE+20*H),))
    def test_future_15m_event_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            review(e15=(event15(BASE+21*H),))
    def test_native15_wrong_source_id_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED"):
            review(e15=(replace(event15(),last_original15m_id=rid(BASE)),))
    def test_fake_1h_gap_wick_geometry_rejected(self):
        with self.assertRaisesRegex(ValueError,"GEOMETRY"):
            review(e1=(h1event(kind="CLASSIC_1H_IMB_SOURCE"),))
    def test_no_lookahead_15m_source_cut_historical(self):
        a=review(hh=hours(n=10),nn=native(40),e15=(),
                asof=BASE+10*H)
        self.assertFalse(a.author_15m_volume_confirmation)
    def test_route_b_and_route_c_not_mixed_into_route_a(self):
        q=review()
        self.assertFalse(q.route_b_idm_used or q.route_c_raid_bos_used)
    def test_all_source_1h_events_need_original_15m_sha(self):
        with self.assertRaisesRegex(ValueError,"INVALID"):
            review(e1=(replace(h1event(),raw_first_original15m_id="INVALID"),))
    def test_new_poi_touch_is_not_owner_valid_first_retest(self):
        q=review()
        self.assertTrue(q.source_first_new_1h_poi_test_native15m_id)
        self.assertFalse(q.author_new_1h_poi_first_valid_test)
    def test_nested_1h_imb_still_cannot_create_owner_trigger(self):
        q=review(hh=hours(gap="nested"),
          e1=(h1event(kind="CLASSIC_1H_IMB_SOURCE"),))
        self.assertFalse(q.author_1h_trigger)
        self.assertEqual(q.nested_1h_imb_4h_trigger_vetoed,1)
if __name__=="__main__":unittest.main()
