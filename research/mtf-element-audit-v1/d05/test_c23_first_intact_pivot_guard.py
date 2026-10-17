"""C23 research source adversaries. No author-labelled BOS or executable trades."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21_native3m_source_bridge import THREE,SEPT_START
from c23_first_intact_pivot_guard import inspect_first_intact_pivots,_direction_broken
from test_c21b_native_3m_vs_5m import make3

class C23IntactPivotSourceTests(unittest.TestCase):
    def test_first_intact_partition_preserves_all_parent_edges(self):
        x=make3()
        r=inspect_first_intact_pivots(x,as_of_ms=x.as_of_ms)
        self.assertGreater(r.original_parent_edges,0)
        self.assertEqual(r.original_parent_edges,
            r.first_close_single_candidate_edges+r.first_close_multiple_candidate_edges+
            r.no_first_close_candidate_edges)
        self.assertEqual(r.total_eligible_before_first_break_test,
            r.still_close_intact_levels+r.previously_close_broken_levels)
        self.assertEqual(r.approved_trades,r.author_selected_pivots)
        self.assertEqual(r.readiness,"NOT_TRADE_READY")
    def test_strict_price_and_wick_cross_no_equal(self):
        x=make3().original_3m_closed[0]
        self.assertFalse(_direction_broken(x,D(100),"SHORT","close"))
        self.assertFalse(_direction_broken(x,D(100),"LONG","close"))
        self.assertTrue(_direction_broken(x,D(101),"SHORT","close"))
        self.assertTrue(_direction_broken(x,D(99),"LONG","close"))
        self.assertTrue(_direction_broken(x,D(99),"SHORT","low"))
        self.assertTrue(_direction_broken(x,D(101),"LONG","high"))
    def test_wick_and_prior_close_cross_are_not_equivalent(self):
        x=make3()
        rows=x.original_3m_closed
        close_changed=replace(rows[122],low=D(94),close=D(100))
        x=replace(x,original_3m_closed=rows[:122]+(close_changed,)+rows[123:])
        r=inspect_first_intact_pivots(x,as_of_ms=x.as_of_ms)
        self.assertGreaterEqual(r.previously_wick_breached_levels,r.previously_close_broken_levels)
        self.assertEqual(r.approved_trades,0)
    def test_early_asof_refuses_unconfirmed_1h_raid(self):
        x=make3()
        r=inspect_first_intact_pivots(x,as_of_ms=SEPT_START+7*3600000)
        self.assertEqual(r.original_parent_edges,0)
    def test_prefix_closed_source_invariance(self):
        x=make3()
        cut=SEPT_START+141*THREE
        independent=replace(x,as_of_ms=cut,original_3m_closed=x.original_3m_closed[:141])
        self.assertEqual(inspect_first_intact_pivots(x,as_of_ms=cut),
                         inspect_first_intact_pivots(independent,as_of_ms=cut))
    def test_unclosed_asof_refused(self):
        x=make3()
        with self.assertRaisesRegex(ValueError,"FUTURE_UNCLOSED"):
            inspect_first_intact_pivots(x,as_of_ms=x.as_of_ms-1)
    def test_raw_original_3m_sha_forgery_rejected(self):
        x=make3()
        bars=x.original_3m_closed
        x=replace(x,original_3m_closed=bars[:88]+(replace(bars[88],raw_id="forged"),)+bars[89:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_first_intact_pivots(x,as_of_ms=x.as_of_ms)
    def test_no_author_ready_bypass(self):
        x=replace(make3(),readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            inspect_first_intact_pivots(x,as_of_ms=x.as_of_ms)
