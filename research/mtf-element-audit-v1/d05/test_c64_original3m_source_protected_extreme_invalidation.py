"""C64 no-author source extreme + preconfirmation and postevent invalidation negatives."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21_native3m_source_bridge import Original3mRow,THREE
from c16_c08_monthly_daily_htf_lineage import DerivedClosedTF,TF_MS,SEPT_START
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    SourceReactionChain,SourceReactionEvent)
from c64_original3m_source_protected_extreme_invalidation import (
    inspect_original_source_protected_extreme,STATUS)
H=TF_MS["1h"];O=SEPT_START+12*H;SHA="a"*64
def rid(t):return SHA+":"+str(t)
def row(i,*,op="100",hi="105",lo="95",cl="100"):
    t=O+i*THREE
    return Original3mRow("BTCUSDT",t,t+THREE,D(op),D(hi),D(lo),
        D(cl),D("10"),rid(t),SHA)
def hrow(i,*,cl="100"):
    t=O+i*H
    return DerivedClosedTF("BTCUSDT","1h",t,t+H,
        D("100"),D("110"),D("80"),D(cl),D("100"),
        tuple(rid(t+k*TF_MS["15m"]) for k in range(4)),(SHA,))
def event(side="LONG"):
    return SourceReactionEvent("BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE",
        side,O+H,O+2*H,rid(O+H),"SYNTHETIC_SOURCE_NOT_AUTHOR")
def chain(side="LONG"):
    e=event(side)
    return SourceReactionChain("BTCUSDT","LONG",O,rid(O),O+THREE,
      O+THREE+24*H,True,
      "FIRST_ANY_SAME_SIDE_SOURCE_ONLY" if side=="LONG" else "FIRST_ANY_OPPOSITE_SIDE_SOURCE_ONLY",
      O+2*H,(e,),side,True)
def fixture(*,at=O+26*H,side="LONG",wick=True,body=True):
    n=(at-O)//THREE
    rows=[row(i,lo="90" if i==0 else "95") for i in range(n)]
    if wick and n>40:rows[40]=row(40,lo="89")
    if body and n>45:rows[45]=row(45,lo="86",cl="88")
    hours=[hrow(i,cl="88" if i==2 and body else "100") for i in range((at-O)//H)]
    return chain(side),tuple(rows),tuple(hours),at
def apply(*,model=None,rows=None,hours=None,asof=None):
    a,b,c,t=fixture()
    return inspect_original_source_protected_extreme(
        a if model is None else model,b if rows is None else rows,
        c if hours is None else hours,as_of_ms=t if asof is None else asof)

class SourceProtectedTests(unittest.TestCase):
    def test_candidate_extreme_frozen_only_when_first_source_event_closed(self):
        z=apply()
        self.assertEqual(z.source_candidate_direction_extreme,"90")
        self.assertEqual(z.original_native3m_extreme_witness_id,rid(O))
        self.assertEqual(z.source_extreme_frozen_at_ms,O+2*H)
        self.assertEqual(z.source_status,"SOURCE_ANCHOR_KNOWN_AT_REACTION_CLOSE")
    def test_wick_breach_never_author_flow_invalidation(self):
        z=apply()
        self.assertEqual(z.first_postevent_wick_breach_id,rid(O+2*H))
        self.assertTrue(z.wick_breach_not_OF_invalidation)
        self.assertFalse(z.author_labeled_OF_invalidation)
    def test_original_3m_close_breach_independent_from_wick(self):
        z=apply()
        self.assertEqual(z.first_postevent_3m_close_beyond_id,rid(O+45*THREE))
        self.assertNotEqual(z.first_postevent_wick_breach_id,z.first_postevent_3m_close_beyond_id)
    def test_first_closed_1h_beyond_is_separate_event(self):
        z=apply()
        self.assertEqual(z.first_postevent_1h_close_beyond_id,rid(O+2*H))
        self.assertEqual(z.readiness,"NOT_TRADE_READY")
    def test_wick_only_does_not_force_3m_close_break(self):
        a,b,h,t=fixture(body=False)
        z=inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
        self.assertEqual(z.first_postevent_wick_breach_id,rid(O+2*H))
        self.assertIsNone(z.first_postevent_3m_close_beyond_id)
        self.assertIsNone(z.first_postevent_1h_close_beyond_id)
    def test_unbreached_after_event_remains_unbreached(self):
        a,b,h,t=fixture(body=False,wick=False)
        z=inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
        self.assertIsNone(z.first_postevent_wick_breach_id)
        self.assertIsNone(z.first_postevent_3m_close_beyond_id)
    def test_24h_observation_complete_if_source_physically_contiguous(self):
        self.assertTrue(apply().full_24h_postevent_source_observed)
    def test_truncated_source_is_right_censored(self):
        a,b,h,t=fixture(at=O+8*H)
        z=inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
        self.assertFalse(z.full_24h_postevent_source_observed)
        self.assertEqual(z.observed_postevent_window_end_ms,t)
    def test_no_future_breach_when_physical_cutoff_shortened(self):
        a,b,h,t=fixture(at=O+26*H)
        cut=O+2*H
        q=inspect_original_source_protected_extreme(a,b[:(cut-O)//THREE],h[:2],as_of_ms=cut)
        self.assertIsNone(q.first_postevent_wick_breach_id)
    def test_mid_confirmation_breach_vetoes_protection(self):
        a,b,h,t=fixture(body=False,wick=False)
        bb=list(b);bb[20]=row(20,lo="89")
        z=inspect_original_source_protected_extreme(a,tuple(bb),h,as_of_ms=t)
        self.assertEqual(z.source_status,"SOURCE_ANCHOR_BREACHED_BEFORE_EVENT_CONFIRMATION")
        self.assertEqual(z.source_preactivation_breach_first3m_id,rid(O+H))
        self.assertIsNone(z.first_postevent_wick_breach_id)
    def test_future_bar_after_asof_rejected(self):
        a,b,h,t=fixture()
        with self.assertRaisesRegex(ValueError,"PHYSICAL_SOURCE_PREFIX"):
            inspect_original_source_protected_extreme(a,b,h,as_of_ms=t-H)
    def test_original_3m_gap_rejected(self):
        a,b,h,t=fixture()
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            inspect_original_source_protected_extreme(a,b[:11]+b[12:],h,as_of_ms=t)
    def test_original_3m_bad_sha_rejected(self):
        a,b,h,t=fixture()
        x=list(b);x[1]=replace(x[1],raw_id="INVALID")
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            inspect_original_source_protected_extreme(a,tuple(x),h,as_of_ms=t)
    def test_original_3m_nan_rejected(self):
        a,b,h,t=fixture()
        x=list(b);x[1]=replace(x[1],low=D("NaN"))
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            inspect_original_source_protected_extreme(a,tuple(x),h,as_of_ms=t)
    def test_original_3m_negative_volume_rejected(self):
        a,b,h,t=fixture()
        x=list(b);x[1]=replace(x[1],volume=D("-1"))
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            inspect_original_source_protected_extreme(a,tuple(x),h,as_of_ms=t)
    def test_original_1h_future_rejected(self):
        a,b,h,t=fixture()
        with self.assertRaisesRegex(ValueError,"FAKE_OR_FUTURE"):
            inspect_original_source_protected_extreme(a,b,h+(hrow(26),),as_of_ms=t)
    def test_original_1h_wrong_native15m_event_id_rejected(self):
        a,b,h,t=fixture()
        e=replace(event(),raw_first_original15m_id=rid(O+H+TF_MS["15m"]))
        a=replace(a,first_any_source_events=(e,))
        with self.assertRaisesRegex(ValueError,"SOURCE_EVENT_NOT_AN_ORIGINAL_1H_ID"):
            inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
    def test_no_first_contact_no_source_anchor(self):
        a,b,h,t=fixture()
        a=replace(a,original_first3m_contact_id=None,first3m_contact_closed_ms=None,
                  first_any_source_events=(),first_any_source_event_known_ms=None,
                  first_any_side=None,status="NO_4H_SOURCE_FIRST_CONTACT")
        z=inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
        self.assertEqual(z.source_status,"NO_ORIGINAL_4H_FIRST_CONTACT")
        self.assertIsNone(z.source_extreme_frozen_at_ms)
    def test_no_event_does_not_invent_anchor(self):
        a,b,h,t=fixture()
        a=replace(a,first_any_source_events=(),first_any_source_event_known_ms=None,
                  first_any_side=None,status="FULL_WINDOW_NO_SOURCE_EVENT")
        z=inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
        self.assertEqual(z.source_status,"NO_1H_REACTION_NO_PROTECTED_CANDIDATE")
    def test_ambiguous_both_side_no_protected_direction(self):
        a,b,h,t=fixture()
        a=replace(a,first_any_source_events=(event("LONG"),event("SHORT")),
                  first_any_side="BOTH",status="FIRST_ANY_BOTH_SIDES_AMBIGUOUS")
        z=inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
        self.assertEqual(z.source_status,"FIRST_ANY_AMBIGUOUS_NO_PROTECTED_DIRECTION")
        self.assertIsNone(z.source_candidate_direction_extreme)
    def test_early_pattern_pretending_reaction_not_promoted(self):
        a,b,h,t=fixture()
        fake=replace(event(),first_pattern_bar_start_ms=O,raw_first_original15m_id=rid(O))
        a=replace(a,first_any_source_events=(fake,))
        z=inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
        self.assertEqual(z.source_status,"REACTION_START_NOT_AFTER_CONTACT")
    def test_opposite_first_event_anchors_high_not_original_long_low(self):
        a,b,h,t=fixture(body=False,wick=False,side="SHORT")
        z=inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
        self.assertEqual(z.event_side,"SHORT")
        self.assertEqual(z.source_candidate_direction_extreme,"105")
        self.assertEqual(z.source_status,"SOURCE_ANCHOR_KNOWN_AT_REACTION_CLOSE")
    def test_author_StrongHL_forgery_rejected(self):
        a,b,h,t=fixture()
        a=replace(a,has_author_stronghl=True)
        with self.assertRaisesRegex(ValueError,"FORGED_SOURCE_CHAIN"):
            inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
    def test_author_orders_forgery_rejected(self):
        a,b,h,t=fixture()
        a=replace(a,orders=("fake",))
        with self.assertRaisesRegex(ValueError,"FORGED_SOURCE_CHAIN"):
            inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
    def test_first_contact_id_wrong_time_rejected(self):
        a,b,h,t=fixture()
        a=replace(a,original_first3m_contact_id=rid(O+THREE))
        with self.assertRaisesRegex(ValueError,"CONTACT_ID_OR_TIME"):
            inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
    def test_source_3m_asof_unaligned_rejected(self):
        a,b,h,t=fixture()
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_ORIGINAL3M"):
            inspect_original_source_protected_extreme(a,b,h,as_of_ms=t+1)
    def test_source_1h_wrong_asof_prefix_rejected(self):
        a,b,h,t=fixture()
        with self.assertRaisesRegex(ValueError,"ORIGINAL_1H_MUST_END_AT_ASOF"):
            inspect_original_source_protected_extreme(a,b,h[:-1],as_of_ms=t)
    def test_first_event_is_NOT_trade_even_if_no_breach(self):
        a,b,h,t=fixture(body=False,wick=False)
        z=inspect_original_source_protected_extreme(a,b,h,as_of_ms=t)
        self.assertFalse(z.author_labeled_stronghl or z.author_labeled_stop_loss)
        self.assertEqual((z.orders,z.trades,z.fills),((),(),()))
if __name__=="__main__":unittest.main()
