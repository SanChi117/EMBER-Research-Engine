"""C65 author-source OF rules, strict chronological + no-author negatives."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c16_c08_monthly_daily_htf_lineage import (
    DerivedClosedTF,NativeKline,TF_MS,SEPT_START,DAY)
from c62_academic_snr_rb_imb_liquidity_source_separation import SourceBlockCase
from c63_closed_4h_source_contact_to_first_any_1h_reaction import SourceReactionEvent
from c64_original3m_source_protected_extreme_invalidation import SourceProtectedExtremeAudit
from c65_of_last_link_target_invalidation_source import source_of_last_link_target_invalidation,STATES
H=TF_MS["1h"];O=SEPT_START+2*DAY; SHA="a"*64
def rid(t):return SHA+":"+str(t)
def bar(i,*,low=None,high=None,close=None):
    t=O+i*H
    l=D(str(low if low is not None else (85 if i==1 else 92)))
    h=D(str(high if high is not None else 110))
    cl=D(str(close if close is not None else 100))
    return DerivedClosedTF("BTCUSDT","1h",t,t+H,D("100"),
       max(h,cl),min(l,cl),cl,D("5"),
       tuple(rid(t+k*TF_MS["15m"]) for k in range(4)),(SHA,))
def market(*,target=True,closebreach=True):
    rows=[bar(i) for i in range(60)]
    if target:rows[15]=bar(15,high=125)
    if closebreach:rows[17]=bar(17,close=82,low=81)
    return tuple(rows)
def days(*,price=120):
    t=O-DAY
    return (NativeKline("BTCUSDT","1d",t,O,D("100"),D(str(price)),D("80"),D("105"),D("200"),rid(t),SHA),)
def anchor():
    return SourceProtectedExtremeAudit(
       "BTCUSDT","LONG","LONG",rid(O),O+10*H,
       "83",rid(O),O+10*H,None,
       "SOURCE_ANCHOR_KNOWN_AT_REACTION_CLOSE",
       None,None,None,O+34*H,True)
def block(kind="liq"):
    isliq=(kind=="liq")
    return SourceBlockCase(
      "RB","LONG",O+5*H,O+6*H,rid(O+4*H),rid(O+5*H),
      None,"PREKNOWN_1H_SSL_STRICT_PIVOT" if isliq else None,
      None if isliq else O+H,
      "LIQUIDITY_SOURCE_PROXY" if isliq else "WICK_ONLY_PREKNOWN_IMB_TEST_PROXY",
      "RB_WICK_ONLY_LIQUIDITY_SOURCE_PROXY" if isliq else "RB_WICK_ONLY_IMB_SOURCE_PROXY")
def blocks():return (block("liq"),block("imb"))
def opposite(at=O+19*H,kind="SNR_1H_SOURCE"):
    dur=3*H if kind in ("CLASSIC_1H_IMB_SOURCE","SNR_1H_SOURCE") else 2*H
    return SourceReactionEvent(kind,"SHORT",at-dur,at,rid(at-dur),"SOURCE_ONLY")
def observe(*,m=None,b=None,h=None,d=None,e=None,asof=None):
    q=market() if h is None else h
    return source_of_last_link_target_invalidation(
      anchor() if m is None else m,q,
      days() if d is None else d,
      blocks() if b is None else b,
      () if e is None else e,
      as_of_ms=q[-1].known_at_ms if asof is None else asof)
class C65FailclosedTests(unittest.TestCase):
    def test_full_context_has_close_after_target_proxy(self):
        q=observe()
        self.assertEqual(q.state,"SOURCE_FIRST_INVALIDATION_LINK_CLOSE_PROXY")
        self.assertEqual(q.source_htf_target_first_wick_reached_ms,O+16*H)
        self.assertEqual(q.source_first_any_invalidation_known_ms,O+18*H)
        self.assertFalse(q.author_of_invalidation_verified)
    def test_last_source_link_is_distinct_from_c64_source_extreme(self):
        q=observe()
        self.assertEqual(q.source_last_link_price,"85")
        self.assertNotEqual(q.source_last_link_price,anchor().source_candidate_direction_extreme)
    def test_does_not_select_latest_unclosed_1d_day(self):
        q=observe()
        self.assertEqual(q.source_original1d_htf_target_known_ms,O)
        self.assertEqual(q.source_original1d_htf_target_price,"120")
    def test_opposite_poi_first_not_replace_with_favorable_bos(self):
        q=observe(h=market(closebreach=False),e=(opposite(),))
        self.assertEqual(q.state,"SOURCE_FIRST_INVALIDATION_OPPOSITE_POI_PROXY")
        self.assertIsNotNone(q.opposite_source_poi_first_original15m_id)
    def test_same_close_two_invalidation_mechanisms_is_ambiguous(self):
        q=observe(e=(opposite(O+18*H),))
        self.assertEqual(q.state,"SOURCE_SIMULTANEOUS_TWO_INVALIDATION_PROXIES")
        self.assertEqual(q.source_first_any_invalidation_kind,"BOTH_SOURCE_PROXIES")
    def test_first_opposite_poi_not_retrospectively_filtered(self):
        q=observe(e=(opposite(O+17*H),))
        self.assertEqual(q.source_first_any_invalidation_kind,"OPPOSITE_SOURCE_POI_PROXY")
    def test_poi_pattern_began_before_target_does_not_count(self):
        q=observe(e=(opposite(O+18*H),))
        self.assertEqual(q.state,"SOURCE_FIRST_INVALIDATION_LINK_CLOSE_PROXY")
    def test_target_not_reached_is_not_automatic_reversal(self):
        q=observe(h=market(target=False,closebreach=False))
        self.assertEqual(q.state,"SOURCE_TARGET_NOT_REACHED_WITHIN_WINDOW")
        self.assertIsNone(q.source_first_any_invalidation_known_ms)
    def test_target_reached_no_bos_and_no_opposite_poi(self):
        q=observe(h=market(closebreach=False))
        self.assertEqual(q.state,"SOURCE_TARGET_REACHED_NO_INVALIDATION_FULL_WINDOW")
        self.assertIsNone(q.source_first_any_invalidation_kind)
    def test_target_reached_no_invalidation_right_censored(self):
        q=market(closebreach=False)[:24]
        z=observe(h=q)
        self.assertEqual(z.state,"SOURCE_TARGET_REACHED_NO_INVALIDATION_RIGHT_CENSORED")
        self.assertFalse(z.full_source_48h_window)
    def test_no_liquidity_work_blocks_of_link(self):
        q=observe(b=(block("imb"),))
        self.assertEqual(q.state,"NO_EARLIER_SOURCE_LIQUIDITY_WORK")
    def test_no_imb_work_blocks_of_link(self):
        q=observe(b=(block("liq"),))
        self.assertEqual(q.state,"NO_EARLIER_SOURCE_IMB_WORK")
    def test_bare_imb_gap_formation_not_imb_test_work(self):
        q=observe(b=(block("liq"),))
        self.assertIsNone(q.prior_imb_source_case_known_ms)
    def test_mb_source_is_not_liquidity_work(self):
        z=replace(block("liq"),source_class="MB_WEAKER_SOURCE_ONLY_NO_RAID_OR_IMB_NOT_VOLUME_CONFIRMATION")
        q=observe(b=(z,block("imb")))
        self.assertEqual(q.state,"NO_EARLIER_SOURCE_LIQUIDITY_WORK")
    def test_wrong_preknown_imb_time_rejected(self):
        z=replace(block("imb"),preknown_imb_reference_ms=O+7*H)
        with self.assertRaisesRegex(ValueError,"FUTURE_IMB_WORK"):
            observe(b=(block("liq"),z))
    def test_source_work_after_anchor_activation_not_admitted(self):
        x=replace(block("imb"),fully_known_ms=O+12*H)
        self.assertEqual(observe(b=(block("liq"),x)).state,"NO_EARLIER_SOURCE_IMB_WORK")
    def test_unconfirmed_c64_anchor_is_not_last_of_link(self):
        q=observe(m=replace(anchor(),source_status="SOURCE_ANCHOR_BREACHED_BEFORE_EVENT_CONFIRMATION"))
        self.assertEqual(q.state,"NO_C64_CONFIRMED_SOURCE_ANCHOR")
    def test_ambiguous_c64_parent_never_source_of_link(self):
        q=observe(m=replace(anchor(),source_status="FIRST_ANY_AMBIGUOUS_NO_PROTECTED_DIRECTION"))
        self.assertEqual(q.state,"NO_C64_CONFIRMED_SOURCE_ANCHOR")
    def test_source_anchor_fake_author_stronghl_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_C64"):
            observe(m=replace(anchor(),author_labeled_stronghl=True))
    def test_source_anchor_fake_order_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_C64"):
            observe(m=replace(anchor(),orders=("FAKE",)))
    def test_target_not_ahead_at_link_is_rejected(self):
        q=observe(d=days(price=105))
        self.assertEqual(q.state,"NO_PREKNOWN_OR_AHEAD_1D_TARGET")
    def test_native1d_known_only_after_link_not_allowed(self):
        q=observe(d=())
        self.assertEqual(q.state,"NO_PREKNOWN_OR_AHEAD_1D_TARGET")
    def test_future_native1d_forbidden(self):
        t=O+2*DAY
        bad=NativeKline("BTCUSDT","1d",t,t+DAY,D("100"),D("120"),D("80"),D("100"),D("1"),rid(t),SHA)
        with self.assertRaisesRegex(ValueError,"FUTURE_NATIVE_1D"):
            observe(d=(bad,))
    def test_native1d_mismatched_source_id_rejected(self):
        d=replace(days()[0],origin_raw_row_id="fake")
        with self.assertRaisesRegex(ValueError,"FUTURE_NATIVE_1D"):
            observe(d=(d,))
    def test_future_opposite_source_event_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_OR_FUTURE"):
            observe(e=(opposite(O+70*H),))
    def test_fake_author_bos_event_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_OR_FUTURE"):
            observe(e=(replace(opposite(),is_author_bos=True),))
    def test_opposite_event_of_wrong_side_does_not_invalidate(self):
        z=replace(opposite(),"side","LONG") if False else replace(opposite(),side="LONG")
        q=observe(h=market(closebreach=False),e=(z,))
        self.assertEqual(q.state,"SOURCE_TARGET_REACHED_NO_INVALIDATION_FULL_WINDOW")
    def test_source_close_before_htf_target_does_not_invalidate(self):
        m=list(market(target=False,closebreach=False))
        m[12]=bar(12,close=82,low=81)
        m[15]=bar(15,high=125)
        q=observe(h=tuple(m))
        self.assertEqual(q.state,"SOURCE_TARGET_REACHED_NO_INVALIDATION_FULL_WINDOW")
    def test_original_1h_gap_rejected(self):
        rows=market()
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            observe(h=rows[:5]+rows[6:])
    def test_invalid_1h_asof_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED"):
            observe(asof=O+60*H+1)
    def test_author_flags_never_certified_even_when_proxy_valid(self):
        q=observe()
        self.assertEqual((q.author_last_of_link_verified,q.author_htf_target_verified,
            q.author_opposite_poi_verified,q.author_of_invalidation_verified,
            q.author_stronghl_verified),(False,)*5)
        self.assertEqual((q.orders,q.trades),((),()))
if __name__=="__main__":unittest.main()
