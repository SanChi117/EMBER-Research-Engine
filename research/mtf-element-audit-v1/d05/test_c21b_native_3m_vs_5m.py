"""C21B synthetic adversarial tests; NO academic author BOS goldens."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from collections import Counter
from c21_native3m_source_bridge import C21Native3mResult,Original3mRow,THREE,SEPT_START
from c21b_original_3m_raid_break_geometry import observe_native3m_raid_break
from c21b_3m_5m_geometry_compare import compare_original_3m_and_5m
from test_c20b_closed_1h_5m_source_geometry import synthetic

SHA="a"*64
HOUR=3600000
def make3(size=200,body=False,early_only=False,invalid=False):
    out=[]
    for i in range(size):
        hour,j=divmod(i,20)
        o,h,l,c=D(100),D(102),D(98),D(100)
        if hour==1 and j==10:h=D(110)
        if hour==5 and j==10:h=D(111)
        if hour==5 and j==19 and body:o,h,l,c=D(100),D(112),D(99),D(112)
        if hour==6 and j==15:l=D(96)
        if hour==7 and j==0:
            o,h,l,c=D(100),D(101),D(94),D(95)
            if invalid:h=D(113)
        if hour==5 and j==14 and early_only:
            o,h,l,c=D(100),D(101),D(94),D(95)
        at=SEPT_START+i*THREE
        out.append(Original3mRow("BTCUSDT",at,at+THREE,o,h,l,c,D(1),
                                 SHA+":"+str(at),SHA))
    return C21Native3mResult("BTCUSDT",SEPT_START+size*THREE,tuple(out),
                              (SHA,"b"*64,"c"*64),3072,32)

class C21BOriginalThreeMinuteGeometry(unittest.TestCase):
    def test_3m_close_break_after_1h_next_candle_confirmation(self):
        x=make3()
        result=observe_native3m_raid_break(x,as_of_ms=x.as_of_ms)
        events=[a for a in result.potential_breaks if a.pivot_center_ms==SEPT_START+HOUR]
        self.assertTrue(events)
        e=events[0]
        self.assertEqual(e.side,"SHORT")
        self.assertEqual(e.raid_confirmed_ms,SEPT_START+7*HOUR)
        self.assertEqual(e.break_start_ms,SEPT_START+7*HOUR)
        self.assertEqual(e.break_known_ms,SEPT_START+7*HOUR+THREE)
        self.assertLess(e.swing.level,e.raid_level)
        self.assertLess(e.break_close,e.swing.level)
        self.assertEqual(result.author_bos_approved,result.trades)
        self.assertEqual(result.readiness,"NOT_TRADE_READY")
    def test_no_future_3m_break_before_first_complete_3m(self):
        x=make3()
        early=observe_native3m_raid_break(x,as_of_ms=SEPT_START+7*HOUR)
        self.assertFalse(early.potential_breaks)
    def test_break_at_3m_close_not_intrabar(self):
        x=make3()
        a=observe_native3m_raid_break(x,as_of_ms=SEPT_START+7*HOUR+THREE)
        self.assertTrue(a.potential_breaks)
    def test_body_breach_not_accepted(self):
        x=make3(body=True)
        r=observe_native3m_raid_break(x,as_of_ms=x.as_of_ms)
        self.assertFalse(any(y.pivot_center_ms==SEPT_START+HOUR for y in r.potential_breaks))
    def test_wick_invalidates_break_first(self):
        x=make3(invalid=True)
        r=observe_native3m_raid_break(x,as_of_ms=x.as_of_ms)
        self.assertFalse(any(y.pivot_center_ms==SEPT_START+HOUR for y in r.potential_breaks))
    def test_3m_subbar_asof_rejected(self):
        x=make3()
        with self.assertRaisesRegex(ValueError,"FUTURE_UNCLOSED_3M"):
            observe_native3m_raid_break(x,as_of_ms=x.as_of_ms-1)
    def test_ready_forgery_rejected(self):
        x=replace(make3(),readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            observe_native3m_raid_break(x,as_of_ms=x.as_of_ms)
    def test_source_row_hash_forgery_rejected(self):
        x=make3()
        a=x.original_3m_closed
        x=replace(x,original_3m_closed=a[:14]+(replace(a[14],raw_id="forged"),)+a[15:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            observe_native3m_raid_break(x,as_of_ms=x.as_of_ms)

    def test_hourly_original_3m_and_5m_price_parity(self):
        t=make3()
        f=synthetic()
        c=compare_original_3m_and_5m(t,f,as_of_ms=t.as_of_ms)
        self.assertGreater(c.native3m_cand_edges,0)
        self.assertGreater(c.native5m_cand_edges,0)
        self.assertGreater(c.same_parent_with_both,0)
        self.assertEqual(c.readiness,"NOT_TRADE_READY")
        self.assertEqual(c.author_trades,0)
    def test_cross_tf_asof_must_be_common_closed_15m(self):
        t=make3()
        with self.assertRaisesRegex(ValueError,"COMMON_ASOF"):
            compare_original_3m_and_5m(t,synthetic(),as_of_ms=t.as_of_ms-THREE)
    def test_cross_tf_wrong_source_symbol_rejected(self):
        t=make3()
        f=replace(synthetic(),symbol="ETHUSDT")
        with self.assertRaises(ValueError):
            compare_original_3m_and_5m(t,f,as_of_ms=t.as_of_ms)
    def test_3m_future_suffix_invariance(self):
        full=make3()
        cut=SEPT_START+141*THREE
        smaller=replace(full,as_of_ms=cut,original_3m_closed=full.original_3m_closed[:141])
        a=observe_native3m_raid_break(full,as_of_ms=cut)
        b=observe_native3m_raid_break(smaller,as_of_ms=cut)
        self.assertEqual(a,b)
    def test_comparison_same_parent_is_not_independent_trade(self):
        c=compare_original_3m_and_5m(make3(),synthetic(),
                                       as_of_ms=SEPT_START+10*HOUR)
        self.assertEqual(c.same_parent_with_both+c.only_3m_parent,c.native3m_cand_edges)
        self.assertEqual(c.same_parent_with_both+c.only_5m_parent,c.native5m_cand_edges)
        self.assertEqual(c.earliest_3m_before_5m+c.earliest_5m_before_3m+
                         c.simultaneous_close,c.same_parent_with_both)
