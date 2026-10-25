"""C55 independent negative/causal tests for original crypto 1H raid and source3m BOS."""
from dataclasses import replace
import unittest
from c37_native_adapted_bos_event_scanner import AdaptedClosedBreak
from c36_adapted_pivot_hypotheses import VARIANTS
from c55_crypto_1h_liquidity_raid_3m_bos_route_c_guard import (
  adapted_3m_and_explicit_unassessed_5m,validate_adapted_original_3m_break,
  HOUR,THREE,STATES,COURSE_C_ROUTES,BLOCKERS)
START=1788220800000
B=START+5*HOUR
C=B+HOUR
K=B+3*HOUR
PREFIX="a"*64
def event(**kw):
    vals={"hypothesis_id":VARIANTS[0],"symbol":"BTCUSDT",
      "raid_fractal_kind":"BSL","raid_fractal_center_ms":START,
      "raid_first_breach_ms":B,"raid_confirmed_ms":B+2*HOUR,
      "raid_level":"100","raid_extreme":"101","side":"SHORT",
      "swing_center_ms":C,"swing_confirmed_ms":C+2*THREE,
      "swing_level":"99","swing_center_native3m_row_id":PREFIX+":"+str(C),
      "break_bar_start_ms":K,"break_bar_closed_known_ms":K+THREE,
      "break_close":"98","break_original_native3m_row_id":PREFIX+":"+str(K)}
    vals.update(kw)
    return AdaptedClosedBreak(**vals)
class C55CryptoOriginalOneHourRaidThreeMinuteBreak(unittest.TestCase):
    def refuse(self,msg,**kw):
        with self.assertRaisesRegex(ValueError,msg):
            adapted_3m_and_explicit_unassessed_5m(event(**kw))
    def test_crypto_1h_BSL_then_3m_bos_research_is_not_trade(self):
        a,b=adapted_3m_and_explicit_unassessed_5m(event())
        self.assertEqual(a.route_c_mode,COURSE_C_ROUTES[0])
        self.assertEqual(a.source_status,STATES[0])
        self.assertEqual((a.orders,a.trades,a.readiness),((),(),"NOT_TRADE_READY"))
    def test_separate_5m_bos_is_unassessed_never_3m_reuse(self):
        a,b=adapted_3m_and_explicit_unassessed_5m(event())
        self.assertEqual(b.route_c_mode,COURSE_C_ROUTES[1])
        self.assertEqual(b.source_status,STATES[1])
        self.assertIsNone(b.source_original3m_break_bar_id)
        self.assertIsNone(b.data_source_timeframe)
    def test_pivot_fully_known_before_raid(self):
        a,_=adapted_3m_and_explicit_unassessed_5m(event())
        self.assertEqual(a.candidate_1h_liquidity_fully_known_ms,START+2*HOUR)
        self.assertLess(a.candidate_1h_liquidity_fully_known_ms,B)
    def test_wick_raid_known_only_after_following_hour(self):
        a,_=adapted_3m_and_explicit_unassessed_5m(event())
        self.assertEqual(a.raid_wick_fully_confirmed_ms,B+2*HOUR)
        self.assertLess(a.raid_wick_fully_confirmed_ms,K)
    def test_first3m_break_known_at_closed_bar(self):
        a,_=adapted_3m_and_explicit_unassessed_5m(event())
        self.assertEqual(a.source_original3m_break_bar_closed_ms,K+THREE)
    def test_author_bos_never_inferred(self):
        a,b=adapted_3m_and_explicit_unassessed_5m(event())
        self.assertFalse(a.academic_BOS_author_verified or b.academic_BOS_author_verified)
        self.assertFalse(a.author_course_entry_ready or b.author_course_entry_ready)
    def test_evidence_blockers_preserved(self):
        self.assertEqual(len(BLOCKERS),4)
        self.assertEqual(adapted_3m_and_explicit_unassessed_5m(event())[0].blocker_reasons,BLOCKERS)
    def test_all_four_adapted_variants_source_only(self):
        for v in VARIANTS:
            x,y=adapted_3m_and_explicit_unassessed_5m(event(hypothesis_id=v))
            self.assertEqual((x.source_hypothesis,y.source_hypothesis),(v,v))
    def test_SSL_inverted_raid_long_valid(self):
        x,_=adapted_3m_and_explicit_unassessed_5m(event(
            raid_fractal_kind="SSL",raid_level="100",raid_extreme="99",
            side="LONG",swing_level="101",break_close="102"))
        self.assertEqual((x.raid_type,x.route_c_mode),("SSL","C_1H_RAID_3M_BOS"))
    def test_noncrypto_symbol_rejected(self):
        self.refuse("FORGED_CRYPTO_SOURCE_OR_AUTHOR_ENTRY",symbol="EURUSD")
    def test_source_not_C37_adapted_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_C37_EVENT"):
            adapted_3m_and_explicit_unassessed_5m({"symbol":"BTCUSDT"})
    def test_fake_author_BOS_rejected(self):
        self.refuse("FORGED_CRYPTO_SOURCE_OR_AUTHOR_ENTRY",author_bos_approved=True)
    def test_fake_paper_trade_rejected(self):
        self.refuse("FORGED_CRYPTO_SOURCE_OR_AUTHOR_ENTRY",paper_trade_allowed=True)
    def test_fake_actual_orders_rejected(self):
        self.refuse("FORGED_CRYPTO_SOURCE_OR_AUTHOR_ENTRY",orders=("BUY",))
    def test_unsupported_variant_rejected(self):
        self.refuse("FORGED_CRYPTO_SOURCE_OR_AUTHOR_ENTRY",hypothesis_id="AUTHOR_BOS")
    def test_wrong_BSL_entry_side_rejected(self):
        self.refuse("RAID_DIRECTION_AND_ENTRY_SIDE_MISMATCH",side="LONG")
    def test_pivot_known_after_first_raid_rejected(self):
        self.refuse("LOOKAHEAD_PIVOT_RAID_OR_3M_BOS",raid_first_breach_ms=START+HOUR)
    def test_first_breach_1h_alignment_rejected(self):
        self.refuse("LOOKAHEAD_PIVOT_RAID_OR_3M_BOS",raid_first_breach_ms=B+THREE)
    def test_raid_unconfirmed_same_hour_rejected(self):
        self.refuse("LOOKAHEAD_PIVOT_RAID_OR_3M_BOS",raid_confirmed_ms=B+HOUR)
    def test_bos_before_complete_raid_confirmation_rejected(self):
        self.refuse("LOOKAHEAD_PIVOT_RAID_OR_3M_BOS",break_bar_start_ms=B+HOUR)
    def test_unconfirmed_3m_swing_used_in_BOS_start_rejected(self):
        self.refuse("LOOKAHEAD_PIVOT_RAID_OR_3M_BOS",swing_confirmed_ms=K+THREE)
    def test_unclosed_3m_BOS_bar_rejected(self):
        self.refuse("LOOKAHEAD_PIVOT_RAID_OR_3M_BOS",break_bar_closed_known_ms=K)
    def test_swing_prior_to_raid_rejected(self):
        self.refuse("LOOKAHEAD_PIVOT_RAID_OR_3M_BOS",swing_center_ms=START)
    def test_bos_source_ID_start_mismatch_rejected(self):
        self.refuse("BAD_ORIGINAL_CRYPTO_RAW3M_CANDLE_ID",break_original_native3m_row_id=PREFIX+":"+str(K+THREE))
    def test_wrong_swing_source_id_timestamp_rejected(self):
        self.refuse("BAD_ORIGINAL_CRYPTO_RAW3M_CANDLE_ID",swing_center_native3m_row_id=PREFIX+":"+str(C+THREE))
    def test_foreign_fx_source_id_rejected(self):
        self.refuse("BAD_ORIGINAL_CRYPTO_RAW3M_CANDLE_ID",break_original_native3m_row_id="EURUSD_OANDA")
    def test_BSL_raid_requires_strict_wick_extreme(self):
        self.refuse("WICK_BOS_PRICE_GEOMETRY_INVALID",raid_extreme="100")
    def test_BSL_break_close_must_be_below_preknown_swing(self):
        self.refuse("WICK_BOS_PRICE_GEOMETRY_INVALID",break_close="99")
    def test_SSL_break_close_above_swing(self):
        self.refuse("WICK_BOS_PRICE_GEOMETRY_INVALID",raid_fractal_kind="SSL",
            side="LONG",raid_extreme="99",swing_level="101",break_close="100")
    def test_negative_nonfinite_market_level_rejected(self):
        self.refuse("INVALID_CRYPTO_SOURCE_LEVEL",break_close="NaN")
    def test_all_source_outputs_NOT_TRADE_READY(self):
        self.assertTrue(all(q.readiness=="NOT_TRADE_READY" for q in
            adapted_3m_and_explicit_unassessed_5m(event())))
if __name__=="__main__": unittest.main()
