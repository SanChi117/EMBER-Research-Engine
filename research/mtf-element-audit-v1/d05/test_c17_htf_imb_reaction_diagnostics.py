"""C17 engineering unit cases: SYNTHETIC prices, never author/Futures goldens."""
from dataclasses import replace
from decimal import Decimal as D
import unittest
from c16_c08_monthly_daily_htf_lineage import (
    SEPT_START, DAY, NativeKline, DerivedClosedTF, ExtendedHTFReview)
from c17_htf_imb_reaction_diagnostics import diagnose_htf_imb,C17Rejected,AUTHOR_UNKNOWN

S="BTCUSDT"
SHA="a"*64
STEP=14_400_000
def k4(i, o, h, l, c):
    t=SEPT_START+i*STEP
    return DerivedClosedTF(S,"4h",t,t+STEP,D(o),D(h),D(l),D(c),D(16),
          tuple(SHA+":"+str(t+j*900_000) for j in range(16)),(SHA,))
def k1(i, o, h, l, c):
    t=SEPT_START+i*DAY
    return NativeKline(S,"1d",t,t+DAY,D(o),D(h),D(l),D(c),D(96),
                        SHA+":"+str(t),SHA)
def review(four=(),daily=(),asof=None):
    if asof is None:
        asof=max([x.known_at_ms for x in (*four,*daily)] or [SEPT_START])
    return ExtendedHTFReview(S,asof,(),tuple(daily),(),tuple(four),len(daily))
def basic():
    # Third candle forms LONG geometric gap [102,104]. Later touch is separate.
    return (k4(0,100,102,98,100),k4(1,101,105,99,103),
            k4(2,105,108,104,106))
def go(four=None,daily=(),asof=None,chosen=None):
    q=review(basic() if four is None else four,daily,asof)
    return diagnose_htf_imb(q,as_of_ms=q.as_of_ms if chosen is None else chosen)

class C17ClosedHTF(unittest.TestCase):
    def test_gap_third_candle_closure_required(self):
        self.assertEqual(len(go(four=basic()[:2]).candidates_4h),0)
        self.assertEqual(len(go().candidates_4h),1)
    def test_long_gap_wick_geometry(self):
        x=go().candidates_4h[0]
        self.assertEqual((x.side,x.zone_low,x.zone_high),("LONG",D(102),D(104)))
        self.assertEqual(x.known_at_ms,basic()[2].known_at_ms)
        self.assertEqual(x.author_status,AUTHOR_UNKNOWN)
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_frozen_v05_middle_candle_color_not_required(self):
        xs=(basic()[0],k4(1,103,105,99,101),basic()[2])
        self.assertEqual(len(go(four=xs).candidates_4h),1)
    def test_no_automatic_parent_or_trading_order(self):
        x=go().candidates_4h[0]
        self.assertEqual(x.parent_attribution,"AUTHOR_PARENT_NOT_DEFINED")
        self.assertFalse(hasattr(x,"entry_price"))
    def test_no_later_contact_is_not_a_failure_to_detect(self):
        x=go().candidates_4h[0]
        self.assertEqual((x.contact_state,len(x.contacts)),("NO_SUBSEQUENT_CONTACT_OBSERVED",0))
    def test_first_subsequent_contact(self):
        x=go(four=basic()+(k4(3,105,106,101,103),)).candidates_4h[0]
        self.assertEqual((x.contact_state,x.first_contact_known_at_ms,x.later_contacts),
                         ("FIRST_CONTACT_OBSERVED_ONLY",SEPT_START+4*STEP,0))
        self.assertEqual(x.contacts[0].close_location,"INSIDE_ZONE")
    def test_second_contact_is_not_first(self):
        xs=basic()+(k4(3,105,106,101,103),k4(4,103,105,101,103))
        x=go(four=xs).candidates_4h[0]
        self.assertEqual([c.ordinal for c in x.contacts],[1,2])
        self.assertEqual(x.contact_state,"REPEATED_CONTACTS_OBSERVED")
    def test_close_below_zone_not_called_author_invalidation(self):
        xs=basic()+(k4(3,105,105,99,100),)
        self.assertEqual(go(four=xs).candidates_4h[0].contacts[0].close_location,"BELOW_ZONE")
    def test_close_above_zone_not_called_author_rejection(self):
        xs=basic()+(k4(3,105,108,103,107),)
        self.assertEqual(go(four=xs).candidates_4h[0].contacts[0].close_location,"ABOVE_ZONE")
    def test_no_contact_outside_zone(self):
        xs=basic()+(k4(3,110,115,109,111),)
        self.assertEqual(len(go(four=xs).candidates_4h[0].contacts),0)
    def test_no_future_suffix_changes_past(self):
        xs=basic()+(k4(3,105,106,101,103),)
        base=go(four=xs,chosen=basic()[-1].known_at_ms)
        suffix=go(four=xs+(k4(4,103,105,101,103),),
                  chosen=basic()[-1].known_at_ms)
        self.assertEqual(base,suffix)
    def test_short_gap_detected(self):
        xs=(k4(0,100,105,98,100),k4(1,99,100,94,96),
            k4(2,90,94,88,91))
        x=go(four=xs).candidates_4h[0]
        self.assertEqual((x.side,x.zone_low,x.zone_high),("SHORT",D(94),D(98)))
    def test_no_gap_does_not_create_candidate(self):
        xs=basic()[:2]+(k4(2,102,108,100,106),)
        self.assertEqual(len(go(four=xs).candidates_4h),0)
    def test_daily_candidate_separate_from_fourhour(self):
        ds=(k1(0,100,102,98,100),k1(1,101,105,99,103),
            k1(2,105,108,104,106))
        q=go(four=(),daily=ds)
        self.assertEqual((len(q.candidates_1d),len(q.candidates_4h)),(1,0))
        self.assertEqual(q.candidates_1d[0].tf,"1d")
    def test_daily_first_contact_only_after_day_three(self):
        ds=(k1(0,100,102,98,100),k1(1,101,105,99,103),
            k1(2,105,108,104,106),k1(3,105,107,101,103))
        self.assertEqual(go(four=(),daily=ds).candidates_1d[0].contacts[0].ordinal,1)
    def test_asof_at_two_completed_bars(self):
        self.assertEqual(len(go(chosen=SEPT_START+2*STEP).candidates_4h),0)
    def test_partial_asof_rejected(self):
        with self.assertRaisesRegex(C17Rejected,"INVALID_OR_FUTURE_ASOF"):
            go(chosen=SEPT_START+2*STEP+1)
    def test_future_asof_rejected(self):
        with self.assertRaisesRegex(C17Rejected,"INVALID_OR_FUTURE_ASOF"):
            go(chosen=SEPT_START+4*STEP)
    def test_wrong_tf_rejected(self):
        xs=(replace(basic()[0],tf="1h"),)+basic()[1:]
        with self.assertRaisesRegex(C17Rejected,"WRONG_TF_SYMBOL_OR_ALIGNMENT"):
            go(four=xs)
    def test_wrong_symbol_rejected(self):
        xs=(replace(basic()[0],symbol="ETHUSDT"),)+basic()[1:]
        with self.assertRaisesRegex(C17Rejected,"WRONG_TF_SYMBOL_OR_ALIGNMENT"):
            go(four=xs)
    def test_missing_history_rejected(self):
        xs=(basic()[0],basic()[2])
        with self.assertRaisesRegex(C17Rejected,"INCOMPLETE_OR_OVERLAPPING_HTF_HISTORY"):
            go(four=xs)
    def test_undeclared_future_bar_rejected(self):
        xs=basic()
        with self.assertRaisesRegex(C17Rejected,"SOURCE_CONTAINS_FUTURE_OR_UNCLOSED_BAR"):
            diagnose_htf_imb(review(xs,asof=xs[1].known_at_ms),
                             as_of_ms=xs[1].known_at_ms)
    def test_wrong_4h_source_sha_rejected(self):
        xs=(replace(basic()[0],source_native_15m_zip_shas=("CORRUPT",)),)+basic()[1:]
        with self.assertRaisesRegex(C17Rejected,"INVALID_4H_15M_LINEAGE"):
            go(four=xs)
    def test_forged_4h_lineage_rejected(self):
        xs=(replace(basic()[0],source_native_15m_rows=("forged",)*16),)+basic()[1:]
        with self.assertRaisesRegex(C17Rejected,"FORGED_4H_SOURCE_ROW_SHA"):
            go(four=xs)
    def test_corrupted_native_1d_sha_rejected(self):
        ds=(replace(k1(0,100,102,98,100),origin_zip_sha256="bad"),)
        with self.assertRaisesRegex(C17Rejected,"INVALID_ORIGIN_NATIVE_DAILY_SHA"):
            go(four=(),daily=ds)
    def test_tampered_raw_price_rejected(self):
        xs=(replace(basic()[0],high=D(99)),)+basic()[1:]
        with self.assertRaisesRegex(C17Rejected,"IMPOSSIBLE_HTF_OHLCV"):
            go(four=xs)
    def test_fake_approved_author_rejected(self):
        x=review(basic())
        with self.assertRaisesRegex(C17Rejected,"FORGED_AUTHOR_OR_SOURCE_APPROVAL"):
            diagnose_htf_imb(replace(x,author_status="APPROVED"),as_of_ms=x.as_of_ms)
    def test_fake_approved_trade_rejected(self):
        x=review(basic())
        with self.assertRaisesRegex(C17Rejected,"FORGED_AUTHOR_OR_SOURCE_APPROVAL"):
            diagnose_htf_imb(replace(x,readiness="READY"),as_of_ms=x.as_of_ms)
    def test_fake_c16_daily_match_count_rejected(self):
        x=review(basic())
        with self.assertRaisesRegex(C17Rejected,"FORGED_AUTHOR_OR_SOURCE_APPROVAL"):
            diagnose_htf_imb(replace(x,crosschecked_native_1d=1),as_of_ms=x.as_of_ms)
    def test_unaligned_date_source_rejected(self):
        xs=(replace(basic()[0],start_ms=basic()[0].start_ms+900_000),)+basic()[1:]
        with self.assertRaisesRegex(C17Rejected,"WRONG_TF_SYMBOL_OR_ALIGNMENT"):
            go(four=xs)
    def test_repeated_candidate_not_merged_by_nearest(self):
        # Engine returns every objectively present overlapping geometric gap.
        xs=basic()+(k4(3,107,110,106,109),)
        self.assertEqual(len(go(four=xs).candidates_4h),2)
if __name__=="__main__":
    unittest.main()
