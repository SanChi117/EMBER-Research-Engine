import unittest
from decimal import Decimal as D
from types import SimpleNamespace as NS
from unittest.mock import patch
import c115_price_only_provenance_reconciliation as x
import c114_independent_poi_native5m_choch_research as c114
from c89_original_native5m_adaptation_backtest import Bar

def candles(volume_mismatch=False,price_mismatch=False):
    three=[NS(start_ms=i*180000,known_ms=(i+1)*180000,
              open=D(100),high=D(104),low=D(96),close=D(100),volume=D(1))
           for i in range(5)]
    five=[Bar(i*300000,D(100),D(104),D(96),D(100),D(1)) for i in range(3)]
    if volume_mismatch:
        five=[Bar(b.open_ms,b.o,b.h,b.l,b.c,D(10)) for b in five]
    if price_mismatch:
        five[1]=Bar(five[1].open_ms,D(100),D(104),D(95),D(100),five[1].volume)
    return tuple(three),tuple(five)

class C115CausalPriceSourceOnly(unittest.TestCase):
    def test_original_clock_ohlc_parity(self):
        a,b=candles()
        z=x.independent_ohlc_price_parity(a,b)
        self.assertTrue(z["strict_ohlc_price_clock_parity"])
        self.assertEqual(z["aligned15m"],1)

    def test_large_volume_anomaly_must_be_explicit_and_nontrading(self):
        a,b=candles(volume_mismatch=True)
        z=x.independent_ohlc_price_parity(a,b)
        self.assertEqual(z["volume_nonidentical_buckets"],1)
        self.assertEqual(z["volume_buckets_drift_gt_1bp"],1)
        self.assertFalse(z["use_in_entry_or_exit"])
        self.assertTrue(D(z["max_relative_15m_volume_drift"])>D(".5"))

    def test_price_high_low_inequality_is_fatal(self):
        a,b=candles(price_mismatch=True)
        with self.assertRaisesRegex(x.C115Error,"PRICE_DISAGREEMENT"):
            x.independent_ohlc_price_parity(a,b)

    def test_zero_rows_fail_closed(self):
        with self.assertRaises(x.C115Error):
            x.independent_ohlc_price_parity((),())

    def test_utc_boundary_mismatch_is_fatal(self):
        a,b=candles()
        b=list(b);b[0]=Bar(1000,b[0].o,b[0].h,b[0].l,b[0].c,b[0].volume)
        with self.assertRaises(x.C115Error):
            x.independent_ohlc_price_parity(a,tuple(b))

    def test_core_original_parity_is_not_mutated(self):
        fn=c114.independent_15m_parity
        a,b=candles(volume_mismatch=True)
        with self.assertRaises(c114.C114Error):
            fn(a,b)
        self.assertIs(c114.independent_15m_parity,fn)

    def test_wrapper_releases_source_policy_on_core_error(self):
        fn=c114.independent_15m_parity
        with patch.object(c114,"run",side_effect=RuntimeError("synthetic")):
            with self.assertRaises(RuntimeError):x.run()
        self.assertIs(c114.independent_15m_parity,fn)

    def test_c114_economic_equations_unchanged(self):
        self.assertEqual(x.frozen.LANDMARK,6*x.frozen.H)
        self.assertEqual(x.frozen.BOOT_SEED,11420261030)
        self.assertEqual(x.frozen.REPS,2000)
        self.assertEqual(x.frozen.BPS,(14,25,40))

if __name__=="__main__":unittest.main()
