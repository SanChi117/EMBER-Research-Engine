"""C22A falsify inferable tick timing from verified original 3m OHLC."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from test_c21b_native_3m_vs_5m import make3,SHA,HOUR
from c21_native3m_source_bridge import THREE,SEPT_START
from c22a_intrabar_vs_closed_3m_provenance import examine_crossing_bounds

class C22CrossingUncertaintyTests(unittest.TestCase):
    def test_closed_break_alone_has_unknown_intrabar_tick_time(self):
        line=make3()
        audit=examine_crossing_bounds(line,as_of_ms=line.as_of_ms)
        self.assertGreater(audit.candidate_parent_edges,0)
        w=next(x for x in audit.observations if x.parent_fractal_ms==SEPT_START+HOUR)
        self.assertEqual(w.close_break_start_ms,SEPT_START+7*HOUR)
        self.assertFalse(w.earlier_pre_close_reach)
        self.assertTrue(w.first_reachable_cross_close_confirmed)
        self.assertEqual(w.tick_timestamp,"UNOBSERVABLE_WITH_3M_OHLC")
        self.assertEqual(w.market_fill,"UNPROVEN_WITH_OHLC")
        self.assertEqual(audit.author_approved_bos,audit.author_approved_trades)
        self.assertEqual(audit.readiness,"NOT_TRADE_READY")
    def test_wick_precedes_closed_break_but_not_an_executable_fill(self):
        line=make3()
        bars=line.original_3m_closed
        wick=replace(bars[140],close=D(100))
        close=replace(bars[141],open=D(100),low=D(94),close=D(95))
        line=replace(line,original_3m_closed=bars[:140]+(wick,close)+bars[142:])
        audit=examine_crossing_bounds(line,as_of_ms=line.as_of_ms)
        w=next(x for x in audit.observations if x.parent_fractal_ms==SEPT_START+HOUR)
        self.assertEqual(w.first_reachable_cross_start_ms,SEPT_START+7*HOUR)
        self.assertEqual(w.close_break_start_ms,SEPT_START+7*HOUR+THREE)
        self.assertTrue(w.earlier_pre_close_reach)
        self.assertFalse(w.first_reachable_cross_close_confirmed)
        self.assertEqual(w.earlier_reach_bars,1)
        self.assertEqual(w.tick_timestamp,"UNOBSERVABLE_WITH_3M_OHLC")
    def test_next_hour_raid_confirmation_required(self):
        x=make3()
        a=examine_crossing_bounds(x,as_of_ms=SEPT_START+7*HOUR)
        self.assertEqual(a.candidate_parent_edges,0)
    def test_missing_closed_3m_candle_rejected(self):
        line=make3()
        with self.assertRaisesRegex(ValueError,"FUTURE_UNCLOSED_3M"):
            examine_crossing_bounds(line,as_of_ms=line.as_of_ms-1)
    def test_future_cutoff_rejected(self):
        x=make3()
        with self.assertRaisesRegex(ValueError,"FUTURE_UNCLOSED_3M"):
            examine_crossing_bounds(x,as_of_ms=x.as_of_ms+THREE)
    def test_original_3m_row_provenance_tamper_rejected(self):
        x=make3()
        bars=x.original_3m_closed
        x=replace(x,original_3m_closed=bars[:34]+(replace(bars[34],raw_id="fake"),)+bars[35:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            examine_crossing_bounds(x,as_of_ms=x.as_of_ms)
    def test_false_author_ready_rejected(self):
        x=replace(make3(),readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            examine_crossing_bounds(x,as_of_ms=x.as_of_ms)
    def test_prefix_replay_matches_full_history(self):
        full=make3()
        cut=SEPT_START+142*THREE
        prefix=replace(full,as_of_ms=cut,original_3m_closed=full.original_3m_closed[:142])
        self.assertEqual(examine_crossing_bounds(full,as_of_ms=cut),
                         examine_crossing_bounds(prefix,as_of_ms=cut))
    def test_counterfactual_invalidation_not_a_bos(self):
        r=examine_crossing_bounds(make3(invalid=True),as_of_ms=make3().as_of_ms)
        self.assertEqual(r.candidate_parent_edges,0)
