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

    def test_older_unbroken_pivot_is_not_equivalent_cross(self):
        x=make3()
        bars=x.original_3m_closed
        change=replace(bars[122],low=D(94))
        x=replace(x,original_3m_closed=bars[:122]+(change,)+bars[123:])
        r=audit_rival_pivots(x,as_of_ms=x.as_of_ms)
        self.assertGreater(r["multiple_eligible_parent_edges"],0)
        self.assertLessEqual(r["same_bar_multiple_crossings"],r["multiple_eligible_parent_edges"])
    def test_before_1h_confirmed_no_swing_trade(self):
        x=make3()
        r=audit_rival_pivots(x,as_of_ms=SEPT_START+7*3600000)
        self.assertEqual(r["observed_parent_edges"],0)
    def test_nonclosed_3m_asof_rejected(self):
        x=make3()
        with self.assertRaisesRegex(ValueError,"FUTURE_UNCLOSED"):
            audit_rival_pivots(x,as_of_ms=x.as_of_ms-1)
    def test_source_row_sha_forgery_rejected(self):
        x=make3()
        b=x.original_3m_closed
        x=replace(x,original_3m_closed=b[:80]+(replace(b[80],raw_id="fake"),)+b[81:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            audit_rival_pivots(x,as_of_ms=x.as_of_ms)
    def test_fake_ready_is_refused(self):
        x=replace(make3(),readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            audit_rival_pivots(x,as_of_ms=x.as_of_ms)
    def test_early_prefix_does_not_use_future(self):
        x=make3()
        cut=SEPT_START+141*THREE
        a=audit_rival_pivots(x,as_of_ms=cut)
        prefix=replace(x,as_of_ms=cut,original_3m_closed=x.original_3m_closed[:141])
        b=audit_rival_pivots(prefix,as_of_ms=cut)
        self.assertEqual(a,b)
