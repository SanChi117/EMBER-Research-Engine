"""C55: no source label upgrades, no future raids or premature 3m BOS."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c20b_hourly_fractal_source_observer import HourFractal,FirstWickObservation
from c21b_original_3m_raid_break_geometry import ThreeSwing,ThreeBreak
from c55_crypto_1h_liquidity_raid_bos_lifecycle import (
 classify_raid,audit_original_1h_liquidity_and_3m_bos,
 STATES,BLOCKERS,ROUTE,HOUR,THREE)
ASOF=12*HOUR
def ids():
 return tuple("a"*64+":"+str(i*THREE) for i in range(60))
def p(kind="BSL"):
 return HourFractal(kind,D("110") if kind=="BSL" else D("90"),
     HOUR,3*HOUR,ids())
def raid(kind="BSL",state="WICK_FRACTAL_GEOMETRY"):
 base=p(kind)
 if state=="NO_FIRST_BREACH":
  return FirstWickObservation(base,None,None,None,None,state)
 return FirstWickObservation(base,4*HOUR,5*HOUR,
    6*HOUR if state=="WICK_FRACTAL_GEOMETRY" else None,
    D("115") if kind=="BSL" else D("85"),state)
def br(kind="BSL"):
 w=raid(kind)
 swing=ThreeSwing("LOW" if kind=="BSL" else "HIGH",
                  D("100") if kind=="BSL" else D("102"),
                  4*HOUR+THREE,4*HOUR+3*THREE,
                  tuple("b"*64+":"+str(4*HOUR+i*THREE) for i in (0,1,2)))
 return ThreeBreak(kind,HOUR,4*HOUR,6*HOUR,
   w.extreme,w.fractal.level,
   "SHORT" if kind=="BSL" else "LONG",
   swing,6*HOUR,6*HOUR+THREE,
   D("99") if kind=="BSL" else D("103"),
   "c"*64+":"+str(6*HOUR))
class C55Original1hLiquidityLifecycleTests(unittest.TestCase):
 def check(self,a=None,b=None,asof=ASOF):
  return classify_raid(raid() if a is None else a,b,
       symbol="BTCUSDT",as_of_ms=asof)
 def reject(self,text,a=None,b=None,asof=ASOF):
  with self.assertRaisesRegex(ValueError,text):self.check(a,b,asof)
 def test_no_first_breach_explicit(self):
  self.assertEqual(self.check(raid(state="NO_FIRST_BREACH")).source_state,STATES[0])
 def test_first_body_breach_terminal(self):
  self.assertEqual(self.check(raid(state="FIRST_BREACH_BODY")).source_state,STATES[1])
 def test_wick_needs_following_onehour_candle(self):
  self.assertEqual(self.check(raid(state="WICK_NEEDS_FOLLOWING_CLOSED_HOUR")).source_state,STATES[2])
 def test_wick_nonfractal_is_not_confirmed(self):
  self.assertEqual(self.check(raid(state="WICK_NONFRACTAL")).source_state,STATES[3])
 def test_raid_confirmed_but_no_adapted_bos(self):
  self.assertEqual(self.check(raid()).source_state,STATES[4])
 def test_raid_and_adapted_closed_3m_break_observed(self):
  self.assertEqual(self.check(raid(),br()).source_state,STATES[5])
 def test_ssl_long_inverted_symmetric(self):
  x=self.check(raid("SSL"),br("SSL"))
  self.assertEqual(x.hourly_liquidity_kind,"SSL")
  self.assertEqual(x.source_state,STATES[5])
 def test_preknown_pivot_ms_before_breach(self):
  x=self.check(raid(),br())
  self.assertLess(x.hourly_liquidity_known_ms,x.first_breach_start_ms)
 def test_raid_requires_fully_closed_next_1h(self):
  x=self.check(raid(),br())
  self.assertEqual(x.first_raid_confirmed_known_ms,6*HOUR)
 def test_3m_break_requires_preknown_swing(self):
  x=self.check(raid(),br())
  self.assertLessEqual(x.adapted_swing_known_ms,6*HOUR)
 def test_event_source_id_preserved(self):
  self.assertEqual(self.check(raid(),br()).adapted_break_original3m_id,br().source_original_3m_row_id)
 def test_author_bos_not_promoted_by_positive_research_geometry(self):
  self.assertFalse(self.check(raid(),br()).academic_bos_verified)
 def test_author_entry_not_promoted_by_positive_research_geometry(self):
  self.assertFalse(self.check(raid(),br()).academic_entry_verified)
 def test_no_trade_execution_fields(self):
  x=self.check(raid(),br())
  self.assertEqual((x.orders,x.trades,x.readiness),((),(),"NOT_TRADE_READY"))
 def test_five_source_semantic_blockers_remain(self):
  self.assertEqual(len(BLOCKERS),5)
  self.assertEqual(self.check(raid(),br()).source_blockers,BLOCKERS)
 def test_route_c_only_without_A_or_B_mutation(self):
  self.assertEqual(self.check(raid(),br()).route,ROUTE)
 def test_cannot_accept_fake_dict_raid(self):
  with self.assertRaisesRegex(ValueError,"UNTRUSTED_FIRST_WICK_SOURCE"):
   classify_raid({},None,symbol="BTCUSDT",as_of_ms=ASOF)
 def test_not_a_valid_positive_fractal_level_nan(self):
  a=raid()
  self.reject("UNTRUSTED_PREKNOWN_1H_LIQUIDITY",replace(a,fractal=replace(a.fractal,level=D("NaN"))))
 def test_not_valid_fake_liquidity_side(self):
  a=raid();self.reject("UNTRUSTED_PREKNOWN_1H_LIQUIDITY",
   replace(a,fractal=replace(a.fractal,kind="POI_FROM_FOREX")))
 def test_pivot_not_known_before_asof(self):
  a=raid();self.reject("UNTRUSTED_PREKNOWN_1H_LIQUIDITY",
   replace(a,fractal=replace(a.fractal,known_ms=13*HOUR)))
 def test_need_60_raw_ids_for_three_1h_source_candles(self):
  a=raid();self.reject("UNTRUSTED_PREKNOWN_1H_LIQUIDITY",
   replace(a,fractal=replace(a.fractal,source_rows=ids()[:2])))
 def test_future_first_raid_breach_rejected(self):
  a=raid();self.reject("FIRST_BREACH_NOT_CAUSALLY_PREKNOWN",
   replace(a,first_breach_ms=13*HOUR,first_breach_close_ms=14*HOUR))
 def test_raid_breach_before_fractal_known_rejected(self):
  a=raid();self.reject("FIRST_BREACH_NOT_CAUSALLY_PREKNOWN",
   replace(a,first_breach_ms=2*HOUR,first_breach_close_ms=3*HOUR))
 def test_no_first_breach_with_forged_confirmation_rejected(self):
  a=raid(state="NO_FIRST_BREACH")
  self.reject("FORGED_EVENT_WITHOUT_FIRST_BREACH",replace(a,confirmed_at_ms=6*HOUR))
 def test_partial_raid_timestamps_rejected(self):
  self.reject("PARTIAL_FIRST_BREACH_SOURCE",replace(raid(),first_breach_close_ms=None))
 def test_raid_does_not_cross_liquidity_strictly_rejected(self):
  a=raid();self.reject("FIRST_BREACH_NOT_CAUSALLY_PREKNOWN",replace(a,extreme=D("110")))
 def test_wick_confirmation_requires_next_1h_close(self):
  self.reject("NOT_A_CLOSED_FOLLOWING_1H_CONFIRMATION",
   replace(raid(),confirmed_at_ms=5*HOUR))
 def test_premature_nonfractal_confirmation_rejected(self):
  self.reject("PREMATURE_OR_FORGED_1H_RAID_CONFIRMATION",
   replace(raid(state="WICK_NONFRACTAL"),confirmed_at_ms=6*HOUR))
 def test_no_preconfirmed_bos_allowed(self):
  self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(state="WICK_NONFRACTAL"),br())
 def test_wrong_parent_fractal_center_rejected(self):
  self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),
    replace(br(),pivot_center_ms=2*HOUR))
 def test_wrong_parent_side_rejected(self):
  self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),replace(br(),side="LONG"))
 def test_wrong_raid_extreme_rejected(self):
  self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),replace(br(),raid_extreme=D("999")))
 def test_swing_not_yet_known_when_bos_candle_started_rejected(self):
  q=br();self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),
    replace(q,swing=replace(q.swing,known_ms=q.break_start_ms+THREE)))
 def test_swing_before_raid_start_rejected(self):
  q=br();self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),
    replace(q,swing=replace(q.swing,center_ms=3*HOUR)))
 def test_3m_break_candle_starts_before_1h_confirmation_rejected(self):
  q=br();self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),
    replace(q,break_start_ms=5*HOUR,break_known_ms=5*HOUR+THREE,
      source_original_3m_row_id="c"*64+":"+str(5*HOUR)))
 def test_3m_break_only_known_at_3m_close(self):
  q=br();self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),
    replace(q,break_known_ms=q.break_start_ms))
 def test_3m_break_cannot_use_future_asof(self):
  self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),br(),asof=6*HOUR)
 def test_invalid_3m_source_raw_id_time_rejected(self):
  self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),
     replace(br(),source_original_3m_row_id="c"*64+":1234567890000"))
 def test_false_bos_price_close_rejected(self):
  self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),replace(br(),break_close=D("100")))
 def test_wrong_swing_kind_rejected(self):
  q=br();self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),
    replace(q,swing=replace(q.swing,kind="HIGH")))
 def test_fake_author_bos_status_rejected(self):
  self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),
    replace(br(),status="AUTHOR_CERTIFIED_BOS"))
 def test_incomplete_3m_swing_id_rejected(self):
  q=br();self.reject("FUTURE_OR_FORGED_ADAPTED_BOS_EVENT",raid(),
    replace(q,swing=replace(q.swing,native3m_ids=q.swing.native3m_ids[:2])))
 def test_lifecycle_uses_original_C21_result_only(self):
  with self.assertRaisesRegex(ValueError,"NOT_ORIGINAL_C21_CRYPTO_SOURCE"):
   audit_original_1h_liquidity_and_3m_bos({},as_of_ms=ASOF)
if __name__=="__main__":unittest.main()
