"""C22B source adjudication negatives; no author BOS goldens."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from test_c21b_native_3m_vs_5m import make3
from c21_native3m_source_bridge import THREE,SEPT_START
from c22b_source_inventory import audit_rival_pivots

class C22BSourceInventoryTests(unittest.TestCase):
    def test_single_research_pivot_not_approved(self):
        x=make3()
        r=audit_rival_pivots(x,as_of_ms=x.as_of_ms)
        self.assertGreater(r["observed_parent_edges"],0)
        self.assertEqual(r["author_approved_trades"],0)
        self.assertEqual(r["source_author_goldens"],0)
        self.assertEqual(r["readiness"],"NOT_TRADE_READY")
    def test_multi_pivot_same_candle_cross(self):
        x=make3()
        bars=x.original_3m_closed
        change=replace(bars[122],low=D(97))
        x=replace(x,original_3m_closed=bars[:122]+(change,)+bars[123:])
        r=audit_rival_pivots(x,as_of_ms=x.as_of_ms)
        self.assertGreater(r["multiple_eligible_parent_edges"],0)
        self.assertGreater(r["same_bar_multiple_crossings"],0)
