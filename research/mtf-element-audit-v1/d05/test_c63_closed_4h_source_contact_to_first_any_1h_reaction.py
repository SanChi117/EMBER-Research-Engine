"""C63 anti-lookahead 4H first-original3m -> first ANY source VC/BOS.
Nothing here author labels genuine POI/StrongHL/SL/TP or orders.
"""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c16_c08_monthly_daily_htf_lineage import (
    DerivedClosedTF,TF_MS,SEPT_START)
from c62_academic_snr_rb_imb_liquidity_source_separation import (
    observe_hourly_source_poi_split)
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    SourceReactionEvent,source_first_any_after_contact,
    bos_source_events_from_closed_original_1h,
    convert_c62_closed_source_events,
    HOUR,THREE,MAX_WINDOW_MS)
O=SEPT_START+12*HOUR
SHA="a"*64
def rid(t):return SHA+":"+str(t)
TOUCH=O+THREE
def evt(kind="BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE",side="LONG",
        at=O+2*HOUR,**kw):
    length=HOUR if kind.startswith("BOS_") else 2*HOUR if kind.startswith("RB") else 3*HOUR
    return replace(SourceReactionEvent(
        kind,side,at,at+length,rid(at),"TECHNICAL_ONLY"),
        **kw)
def check(events=(),asof=O+36*HOUR,contact=TOUCH,side="LONG"):
    return source_first_any_after_contact(
        symbol="BTCUSDT",side=side,zone_known_ms=O,
        first_original3m_id=rid(TOUCH-THREE) if contact else None,
        first_contact_known_ms=contact,events=events,as_of_ms=asof)
def candle(i,op,hi,lo,cl):
    t=SEPT_START+i*HOUR
    return DerivedClosedTF("BTCUSDT","1h",t,t+HOUR,
        D(str(op)),D(str(hi)),D(str(lo)),D(str(cl)),D("1"),
        tuple(rid(t+k*TF_MS["15m"]) for k in range(4)),
        (SHA,))
def bars():
    return (
        candle(0,100,112,96,108),candle(1,108,115,104,112),
        candle(2,111,113,100,101),candle(3,101,111,98,109),
        candle(4,109,119,105,118),candle(5,118,123,113,121))

class FirstAnyTest(unittest.TestCase):
    def test_first_any_same_source(self):
        z=check((evt(),))
        self.assertEqual(z.status,"FIRST_ANY_SAME_SIDE_SOURCE_ONLY")
        self.assertFalse(z.has_author_stronghl)
        self.assertEqual(z.orders,())
    def test_first_any_opposite_source_not_cherry_picked(self):
        z=check((evt(side="SHORT",at=O+1*HOUR),
                 evt(side="LONG",at=O+4*HOUR)))
        self.assertEqual(z.status,"FIRST_ANY_OPPOSITE_SIDE_SOURCE_ONLY")
        self.assertEqual(z.first_any_side,"SHORT")
        self.assertEqual(z.first_any_source_event_known_ms,O+2*HOUR)
    def test_same_close_ambiguous_no_favorable_priority(self):
        z=check((evt(side="SHORT"),evt(side="LONG")))
        self.assertEqual(z.status,"FIRST_ANY_BOTH_SIDES_AMBIGUOUS")
        self.assertEqual(len(z.first_any_source_events),2)
    def test_duplicate_same_side_close_remains_first_any(self):
        z=check((evt(),evt()))
        self.assertEqual(z.status,"FIRST_ANY_SAME_SIDE_SOURCE_ONLY")
        self.assertEqual(len(z.first_any_source_events),2)
    def test_no_4h_touch_never_assume_traded(self):
        z=check((),contact=None)
        self.assertEqual(z.status,"NO_4H_SOURCE_FIRST_CONTACT")
        self.assertFalse(z.had_source_contact_inefficiency_only)
    def test_source_without_event_complete_24h(self):
        z=check(())
        self.assertEqual(z.status,"FULL_WINDOW_NO_SOURCE_EVENT")
        self.assertTrue(z.fully_observed_24h_window)
    def test_source_without_event_short_history_right_censored(self):
        z=check((),asof=O+6*HOUR)
        self.assertEqual(z.status,"RIGHT_CENSORED_NO_SOURCE_EVENT")
        self.assertFalse(z.fully_observed_24h_window)
    def test_event_only_after_window_right_censor_no_event(self):
        z=check((evt(at=O+30*HOUR),),asof=O+36*HOUR)
        self.assertEqual(z.status,"FULL_WINDOW_NO_SOURCE_EVENT")
    def test_event_pattern_begins_before_first_closed_contact_is_ignored(self):
        z=check((evt(at=O),evt(at=O+2*HOUR)))
        self.assertEqual(z.first_any_source_event_known_ms,O+3*HOUR)
    def test_event_ending_after_asof_forbidden(self):
        with self.assertRaisesRegex(ValueError,"FUTURE"):
            check((evt(at=O+9*HOUR),),asof=O+6*HOUR)
    def test_future_event_not_hidden_by_empty_original_contact(self):
        with self.assertRaisesRegex(ValueError,"FUTURE"):
            check((evt(at=O+40*HOUR),),contact=None)
    def test_4h_known_at_same_time_as_touch_forbidden(self):
        with self.assertRaisesRegex(ValueError,"FIRST_ORIGINAL"):
            check((evt(),),contact=O)
    def test_original_touch_row_forged(self):
        with self.assertRaisesRegex(ValueError,"FIRST_ORIGINAL"):
            source_first_any_after_contact(symbol="BTCUSDT",side="LONG",
                zone_known_ms=O,first_original3m_id=rid(O+THREE),
                first_contact_known_ms=TOUCH,events=(),as_of_ms=O+30*HOUR)
    def test_wrong_pair_side_forgery(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED"):
            check((),side="FAKE")
    def test_author_vc_forgery_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_OR_FUTURE"):
            check((evt(is_author_vc=True),))
    def test_author_bos_forgery_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_OR_FUTURE"):
            check((evt(is_author_bos=True),))
    def test_author_stronghl_forgery_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_OR_FUTURE"):
            check((evt(is_author_stronghl=True),))
    def test_orders_forgery_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_OR_FUTURE"):
            check((evt(orders=("FAKE",)),))
    def test_wrong_event_raw_id_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_OR_FUTURE"):
            check((evt(raw_first_original15m_id=rid(O+50*HOUR)),))
    def test_wrong_event_duration_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_OR_FUTURE"):
            check((evt(fully_known_ms=O+8*HOUR),))
    def test_open_1h_event_time_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_OR_FUTURE"):
            check((evt(fully_known_ms=O+2*HOUR+1),))
    def test_bad_asof_alignment_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED"):
            check((),asof=O+36*HOUR+1)
    def test_first_source_event_at_exact_24h_window_inclusive(self):
        z=check((evt(at=TOUCH+MAX_WINDOW_MS-HOUR),),asof=O+30*HOUR)
        self.assertEqual(z.status,"FIRST_ANY_SAME_SIDE_SOURCE_ONLY")
    def test_technical_event_not_author_stronghl_even_after_source_vc(self):
        z=check((evt(),))
        self.assertFalse(z.has_author_selected_poi or
                         z.has_author_first_valid_poi_test or
                         z.has_author_vc_or_bos or z.has_author_stronghl or
                         z.author_trade_approved)
    def test_no_event_cannot_be_implied_from_bare_pivot(self):
        z=check(())
        self.assertEqual(z.first_any_source_events,())

class SourceEventGeneratorTest(unittest.TestCase):
    def test_bos_only_after_preknown_strict_fractal_close(self):
        q=bars()
        x=bos_source_events_from_closed_original_1h(q,as_of_ms=q[-1].known_at_ms)
        self.assertTrue(x)
        self.assertTrue(all(z.kind=="BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE" for z in x))
        self.assertTrue(all(z.raw_first_original15m_id==rid(z.first_pattern_bar_start_ms) for z in x))
    def test_bos_physical_prefix_matches_cutoff(self):
        q=bars()
        self.assertEqual(
            bos_source_events_from_closed_original_1h(q,as_of_ms=q[4].known_at_ms),
            bos_source_events_from_closed_original_1h(q[:5],as_of_ms=q[4].known_at_ms))
    def test_generated_c62_source_event_untrusted_author_vc_is_rejected(self):
        q=bars()
        v=observe_hourly_source_poi_split(q,as_of_ms=q[-1].known_at_ms)
        x=convert_c62_closed_source_events(v,q,as_of_ms=q[-1].known_at_ms)
        self.assertTrue(all(not z.is_author_stronghl and not z.is_author_vc for z in x))
    def test_generated_c62_full_prefix_equals_physical(self):
        q=bars()
        full=observe_hourly_source_poi_split(q,as_of_ms=q[4].known_at_ms)
        cut=observe_hourly_source_poi_split(q[:5],as_of_ms=q[4].known_at_ms)
        self.assertEqual(
            convert_c62_closed_source_events(full,q,as_of_ms=q[4].known_at_ms),
            convert_c62_closed_source_events(cut,q[:5],as_of_ms=q[4].known_at_ms))
if __name__=="__main__":unittest.main()
