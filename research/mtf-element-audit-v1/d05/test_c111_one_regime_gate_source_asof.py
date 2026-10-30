"""C111 pre-market 20 negative tests of C109 regime gate and original source.
No access to actual 2025 C111 trade labels is necessary to pass these proofs.
"""
import sys,unittest
from pathlib import Path
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parent))
from c91_continuous_causal_route_a_paper import OHLC
import c111_frozen_c109_1d4h_regime_gate as f
import c109_simple_p4_core_vs_original_research as core
import c105_parent4h_structural_geometry as h4
from test_c105_parent4h_only_geometry import parent,fixtures

def series(prices,tf,start=0):
    return tuple(OHLC(start+i*tf,start+(i+1)*tf,D(str(x)),
        D(str(x))+D("1"),D(str(x))-D("1"),D(str(x)),D("1"))
        for i,x in enumerate(prices))
UP4=series([100,101,102,103,104,105,106],h4.H4,17*h4.H4)
DOWN4=series([106,105,104,103,102,101,100],h4.H4,17*h4.H4)
UP1=series([100,101,102,103],h4.D1)
DOWN1=series([103,102,101,100],h4.D1)
CLOCK=4*h4.D1

class Gate111(unittest.TestCase):
    def test_01_strategy_c109_source_immutable_sha(self):
        self.assertTrue(f.pins())
    def test_02_two_frozen_different_64day_source_windows(self):
        self.assertEqual(len(f.WINDOWS),2)
        self.assertEqual([x[0] for x in f.WINDOWS],["WIN_A","WIN_B"])
        self.assertEqual(f.WINDOWS[0][1].strftime("%Y-%m-%d"),"2025-03-01")
        self.assertEqual(f.WINDOWS[1][2].strftime("%Y-%m-%d"),"2025-09-03")
    def test_03_source_count_1536_original_zips_and_rows(self):
        self.assertEqual((f.EXPECTED_TOTAL_ZIPS,f.EXPECTED_TOTAL_BARS),(1536,737280))
    def test_04_no_new_trading_formations(self):
        src=(Path(__file__).parent/"c111_frozen_c109_1d4h_regime_gate.py").read_text()
        self.assertNotIn("request.security(",src)
        self.assertNotIn("lookahead_on",src)
        self.assertNotIn("place_order(",src)
    def test_05_long_align_pass_unambiguous_direction(self):
        ok,why,proof=f.regime_from_completed("LONG",CLOCK,UP4,UP1)
        self.assertTrue(ok);self.assertEqual(why,"ALIGNED_TREND_AT_ASOF_H1_CLOSE")
        self.assertEqual(proof["4h_6_step_efficiency"],"1")
    def test_06_short_align_pass_unambiguous_direction(self):
        self.assertTrue(f.regime_from_completed("SHORT",CLOCK,DOWN4,DOWN1)[0])
    def test_07_long_reject_reverse_4h_structure(self):
        self.assertEqual(f.regime_from_completed("LONG",CLOCK,DOWN4,UP1)[1],
                         "4H_DIRECTION_OPPOSES_SETUP")
    def test_08_short_reject_reverse_4h_structure(self):
        self.assertEqual(f.regime_from_completed("SHORT",CLOCK,UP4,DOWN1)[1],
                         "4H_DIRECTION_OPPOSES_SETUP")
    def test_09_bearish_d1_overrides_bullish_h4(self):
        self.assertEqual(f.regime_from_completed("LONG",CLOCK,UP4,DOWN1)[1],
                         "1D_DIRECTION_OPPOSES_SETUP")
    def test_10_bullish_d1_overrides_bearish_h4(self):
        self.assertEqual(f.regime_from_completed("SHORT",CLOCK,DOWN4,UP1)[1],
                         "1D_DIRECTION_OPPOSES_SETUP")
    def test_11_4h_low_directional_efficiency_chop_rejected(self):
        chop=series([100,104,99,105,98,106,101],h4.H4,17*h4.H4)
        ok,why,p=f.regime_from_completed("LONG",CLOCK,chop,UP1)
        self.assertFalse(ok);self.assertEqual(why,"4H_PRICE_PATH_CHOPPY")
        self.assertLess(D(p["4h_6_step_efficiency"]),D(1)/D(3))
    def test_12_all_4h_closes_flat_rejected_fail_closed(self):
        still=series([100]*7,h4.H4,17*h4.H4)
        self.assertEqual(f.regime_from_completed("LONG",CLOCK,still,UP1)[1],
                         "FLAT_OR_ZERO_MOVEMENT")
    def test_13_insufficient_completed_d1_rejected(self):
        self.assertEqual(f.regime_from_completed("LONG",CLOCK,UP4,UP1[:3])[1],
                         "UNAVAILABLE_FULLY_CLOSED_H4_D1_HISTORY")
    def test_14_insufficient_completed_4h_rejected(self):
        self.assertEqual(f.regime_from_completed("LONG",CLOCK,UP4[:6],UP1)[1],
                         "UNAVAILABLE_FULLY_CLOSED_H4_D1_HISTORY")
    def test_15_last_d1_not_available_before_its_close(self):
        asof=UP1[-1].close_ms-1
        self.assertFalse(f.regime_from_completed("LONG",asof,UP4,UP1)[0])
    def test_16_last_4h_bar_not_available_before_close(self):
        # Deliberately use a synthetic 1D history already fully closed: 4H
        # future-close candle may never be observed before it is completed.
        h_future=tuple(OHLC(x.start_ms+10*h4.D1,x.close_ms+10*h4.D1,
               x.o,x.h,x.l,x.c,x.vol) for x in UP4)
        self.assertFalse(f.regime_from_completed("LONG",CLOCK,h_future,UP1)[0])
    def test_17_1h_4h_closed_bar_boundary_allowed(self):
        asof=UP4[-1].close_ms
        self.assertTrue(f.regime_from_completed("LONG",asof,UP4,UP1)[0])
    def test_18_calendar_scope_restores_original_even_on_error(self):
        saved={p:getattr(core,p) for p in f.CAL_FIELDS}
        with self.assertRaisesRegex(RuntimeError,"test"):
            with f.scoped_new_window(f.WINDOWS[0]):
                self.assertEqual(core.DAYS[0],"2025-03-01")
                self.assertEqual(core.DAYS[-1],"2025-05-03")
                raise RuntimeError("test")
        self.assertEqual(saved,{p:getattr(core,p) for p in f.CAL_FIELDS})
    def test_19_no_tp_or_sl_mutation_in_standard_parent(self):
        now,closed,sw,rows,starts=fixtures()
        plan,reason=h4.parent_plan(parent(),now,D("100"),closed,sw,rows,starts)
        self.assertEqual((reason,plan["stop_source_tf"],plan["target_source_tf"]),
                         ("OK","4H","4H"))
        self.assertEqual((h4.PAD,h4.BPS),(D("0.15"),(14,25,40)))
    def test_20_fail_closed_invalid_direction(self):
        with self.assertRaisesRegex(f.C111Rejected,"BAD_DIRECTION_OR_CLOCK"):
            f.regime_from_completed("BUY",CLOCK,UP4,UP1)
if __name__=="__main__":unittest.main()
