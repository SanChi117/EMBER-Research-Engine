"""C32 separate price-reach vs close-then-limit research routes, no fake fills."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21_native3m_source_bridge import THREE,SEPT_START
from c21b_original_3m_raid_break_geometry import observe_native3m_raid_break
from c32_dual_bos_route_source import study_bos_routes,inspect_c32
from test_c21b_native_3m_vs_5m import make3

def example():
    source=make3()
    event=next(e for e in observe_native3m_raid_break(source,as_of_ms=source.as_of_ms).potential_breaks
               if e.pivot_center_ms==SEPT_START+3600000)
    return source,event

class C32TwoBOSPaths(unittest.TestCase):
    def test_market_route_never_fills_from_3m_wick(self):
        src,e=example()
        x=study_bos_routes(e,src.original_3m_closed)
        self.assertFalse(x.market_cross.market_order_allowed)
        self.assertIsNone(x.market_cross.simulated_fill_price)
        self.assertIsNone(x.market_cross.actual_tick_cross_ms)
        self.assertEqual(x.market_cross.status,"SOURCE_OHLC_REACH_ONLY_MARKET_TICK_CROSS_NOT_PROVEN")
    def test_close_route_only_known_after_bar_close(self):
        src,e=example()
        x=study_bos_routes(e,src.original_3m_closed)
        self.assertEqual(x.close_then_limit.earliest_possible_order_after_ms,e.break_known_ms)
        self.assertTrue(x.close_then_limit.source_close_beyond_pivot)
        self.assertEqual(x.close_then_limit.selected_close_3m_row_id,e.source_original_3m_row_id)
    def test_limit_price_cannot_be_inferred_from_close(self):
        src,e=example()
        z=study_bos_routes(e,src.original_3m_closed).close_then_limit
        self.assertIsNone(z.author_limit_price)
        self.assertIsNone(z.author_limit_expiry)
        self.assertIsNone(z.inferred_retest_fill)
        self.assertFalse(z.limit_order_allowed)
    def test_both_routes_keep_orders_zero(self):
        src,e=example()
        z=study_bos_routes(e,src.original_3m_closed)
        self.assertEqual(z.chosen_route,"NONE_UNTIL_AUTHOR_SOURCE_ATTESTED")
        self.assertFalse(z.author_route_approved)
        self.assertEqual(z.orders,())
        self.assertEqual(z.trades,())
        self.assertEqual(z.readiness,"NOT_TRADE_READY")
    def test_baseline_cross_at_selected_break_bar(self):
        src,e=example()
        z=study_bos_routes(e,src.original_3m_closed)
        self.assertEqual(z.market_cross.first_source_wick_reach_bar_ms,e.break_start_ms)
        self.assertFalse(z.market_cross.first_wick_reach_was_before_research_close_bar)
    def test_wick_only_precedes_closed_bos_without_proving_market_order(self):
        src,e=example()
        rows=list(src.original_3m_closed)
        k=next(i for i,b in enumerate(rows) if b.start_ms==e.break_start_ms)
        assert k>0
        rows[k-1]=replace(rows[k-1],open=D("100"),high=D("101"),
                 low=e.swing.level-D("1"),close=D("100"))
        z=study_bos_routes(e,tuple(rows))
        self.assertEqual(z.market_cross.first_source_wick_reach_bar_ms,rows[k-1].start_ms)
        self.assertTrue(z.market_cross.first_wick_reach_was_before_research_close_bar)
        self.assertFalse(z.market_cross.first_source_bar_closed_beyond_selected_pivot)
        self.assertFalse(z.market_cross.market_order_allowed)
        self.assertEqual(z.close_then_limit.selected_close_bar_ms,e.break_start_ms)
    def test_equal_wick_level_is_not_cross(self):
        src,e=example()
        rows=list(src.original_3m_closed)
        k=next(i for i,b in enumerate(rows) if b.start_ms==e.break_start_ms)
        rows[k-1]=replace(rows[k-1],open=D("100"),high=D("101"),
                   low=e.swing.level,close=D("100"))
        z=study_bos_routes(e,tuple(rows))
        self.assertEqual(z.market_cross.first_source_wick_reach_bar_ms,e.break_start_ms)
    def test_open_already_beyond_is_not_tick_cross_proof(self):
        src,e=example()
        rows=list(src.original_3m_closed)
        k=next(i for i,b in enumerate(rows) if b.start_ms==e.break_start_ms)
        rows[k-1]=replace(rows[k-1],open=e.swing.level-D("1"),
            high=D("101"),low=e.swing.level-D("2"),close=D("100"))
        z=study_bos_routes(e,tuple(rows))
        self.assertTrue(z.market_cross.first_wick_reach_was_already_touched_at_bar_open)
        self.assertEqual(z.market_cross.first_source_bar_open_side,"OPEN_ALREADY_BEYOND_SELECTED_PIVOT")
        self.assertIsNone(z.market_cross.actual_tick_cross_ms)
    def test_same_bar_raid_extreme_is_unknown_not_valid_trade(self):
        src,e=example()
        rows=list(src.original_3m_closed)
        k=next(i for i,b in enumerate(rows) if b.start_ms==e.break_start_ms)
        rows[k]=replace(rows[k],high=e.raid_extreme+D("1"))
        z=study_bos_routes(e,tuple(rows))
        self.assertTrue(z.market_cross.first_source_bar_also_exceeded_raid_extreme)
        self.assertEqual(z.market_cross.status,"SOURCE_OHLC_REACH_ONLY_MARKET_TICK_CROSS_NOT_PROVEN")
        self.assertEqual(z.orders,())
    def test_bos_future_selected_swing_rejected(self):
        src,e=example()
        with self.assertRaisesRegex(ValueError,"NONCAUSAL"):
            study_bos_routes(replace(e,swing=replace(e.swing,known_ms=e.break_start_ms+THREE)),
                src.original_3m_closed)
    def test_bos_before_raid_confirmation_rejected(self):
        src,e=example()
        with self.assertRaisesRegex(ValueError,"NONCAUSAL"):
            study_bos_routes(replace(e,raid_confirmed_ms=e.break_start_ms+THREE),
                src.original_3m_closed)
    def test_wrong_side_bos_level_rejected(self):
        src,e=example()
        with self.assertRaisesRegex(ValueError,"NO_STRICT_BOS"):
            study_bos_routes(replace(e,raid_level=e.swing.level),src.original_3m_closed)
    def test_wrong_side_1h_raid_rejected(self):
        src,e=example()
        with self.assertRaisesRegex(ValueError,"BAD_RAID"):
            study_bos_routes(replace(e,pivot_kind="SSL"),src.original_3m_closed)
    def test_body_raid_not_a_wick_raid_rejected(self):
        src,e=example()
        with self.assertRaisesRegex(ValueError,"NO_STRICT_BOS"):
            study_bos_routes(replace(e,raid_extreme=e.raid_level),src.original_3m_closed)
    def test_negative_price_not_admitted(self):
        src,e=example()
        with self.assertRaisesRegex(ValueError,"INVALID_DECIMAL"):
            study_bos_routes(replace(e,raid_level=D("-1")),src.original_3m_closed)
    def test_wrong_original_closed_break_row_rejected(self):
        src,e=example()
        with self.assertRaisesRegex(ValueError,"SOURCE_ROW_MISMATCH"):
            study_bos_routes(replace(e,source_original_3m_row_id="forged"),src.original_3m_closed)
    def test_non_tuple_original_3m_rejected(self):
        src,e=example()
        with self.assertRaisesRegex(ValueError,"UNTRUSTED"):
            study_bos_routes(e,list(src.original_3m_closed))
    def test_invalidated_source_cannot_make_dual_route(self):
        src=make3(invalid=True)
        got=inspect_c32(src,as_of_ms=src.as_of_ms)
        self.assertEqual(got.orders_created,0)
        self.assertEqual(got.trades_created,0)
    def test_historical_prefix_physically_equal_to_expanded_source(self):
        src=make3()
        cut=SEPT_START+141*THREE
        truncated=replace(src,as_of_ms=cut,original_3m_closed=src.original_3m_closed[:141])
        self.assertEqual(inspect_c32(src,as_of_ms=cut),
                         inspect_c32(truncated,as_of_ms=cut))
    def test_future_unclosed_asof_rejected(self):
        src=make3()
        with self.assertRaisesRegex(ValueError,"FUTURE_UNCLOSED"):
            inspect_c32(src,as_of_ms=src.as_of_ms-1)
    def test_forged_ready_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            src=replace(make3(),readiness="READY")
            inspect_c32(src,as_of_ms=src.as_of_ms)
    def test_original_3m_row_hash_tamper_rejected(self):
        src=make3()
        rows=src.original_3m_closed
        damaged=replace(src,original_3m_closed=rows[:7]+(replace(rows[7],raw_id="bad"),)+rows[8:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_c32(damaged,as_of_ms=damaged.as_of_ms)
    def test_inspect_cases_stay_not_trade_ready(self):
        src=make3()
        result=inspect_c32(src,as_of_ms=src.as_of_ms)
        self.assertEqual(result.author_market_cross_approved,0)
        self.assertEqual(result.author_limit_retest_approved,0)
        self.assertEqual(result.orders_created,0)
        self.assertEqual(result.trades_created,0)
        self.assertEqual(result.readiness,"NOT_TRADE_READY")
        self.assertEqual(result.strict_c21_parent_edges,len(result.cases))
if __name__=="__main__":unittest.main()
