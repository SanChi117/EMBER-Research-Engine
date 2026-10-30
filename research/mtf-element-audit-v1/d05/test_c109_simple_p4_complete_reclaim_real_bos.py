"""C109: locked-before-price test of single simple P4 core vs original C105.
Never repairs strategy from C109 market outcome; 4H SL/TP inherited unchanged.
"""
import sys,unittest,hashlib
from pathlib import Path
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c109_simple_p4_core_vs_original_research as m
import c105_parent4h_structural_geometry as h4
from c90_structural_fta_backtest import Swing
from c91_continuous_causal_route_a_paper import _vc
from test_c105_parent4h_only_geometry import bar,fixtures,parent

def z(side="LONG"):
    return h4.Parent(side,D("98"),D("99"),h4.H4,"P4",
                     first_touch_ms=2*h4.H,state="WAIT_1H_REJECTION")
def four15(t=0,break_high=True):
    tf=h4.M15
    return (
      bar(t,tf,o="99",h="104",l="98",c="100"),
      bar(t+tf,tf,o="100",h="106",l="98",c="102"),
      bar(t+2*tf,tf,o="102",h="104",l="100",c="103"),
      bar(t+3*tf,tf,o="103",h="108",l="101",c="107" if break_high else "104"),
    )
class C109Audit(unittest.TestCase):
    def bad(self,fn,msg):
        with self.assertRaisesRegex(m.C109Error,msg):fn()
    def test_01_original_c105_sources_frozen(self):
        self.assertTrue(m.frozen())
    def test_02_frozen_may_july_calendar_exact(self):
        self.assertEqual((m.DAYS[0],m.DAYS[-1],len(m.DAYS)),
            ("2026-05-01","2026-07-03",64))
    def test_03_original_daily_zip_and_bar_counts(self):
        self.assertEqual((m.ZIPS,m.BARS_PER_SYMBOL,len(m.SYMBOLS)),(768,30720,12))
    def test_04_prior_period_not_seen_C108(self):
        self.assertLess(m.END_MS,int(__import__("datetime").datetime(2026,8,20,
            tzinfo=__import__("datetime").timezone.utc).timestamp()*1000))
    def test_05_no_live_execution_or_luxalgo_modules(self):
        src=(Path(__file__).parent/"c109_simple_p4_core_vs_original_research.py").read_text()
        self.assertNotIn("lookahead_on",src)
        self.assertNotIn("request.security",src)
        self.assertNotIn("BinanceClient",src)
        self.assertNotIn("place_order(",src)
    def test_06_restore_strict_provider_whitelist_on_early_source_failure(self):
        import c104_native3m_source as d
        saved_symbols=d.SYMBOLS; saved_days=d.DAYS
        def offline(url):raise RuntimeError("offline")
        try:
            with self.assertRaises(RuntimeError):m.provider_3m(fetch=offline)
        finally:
            self.assertEqual(d.SYMBOLS,saved_symbols)
            self.assertEqual(d.DAYS,saved_days)
    def test_07_old_midpoint_1h_accepted_but_new_reclaim_rejected(self):
        x=z()
        closed=bar(2*h4.H,h4.H,o="98.2",h="99.3",l="97.9",c="98.7")
        self.assertTrue(h4.rejection(x,closed))
        self.assertFalse(m.full_reclaim(x,closed))
    def test_08_good_long_h1_close_beyond_full_4h_fvg_edge(self):
        self.assertTrue(m.full_reclaim(z(),bar(2*h4.H,h4.H,
                            o="98.2",h="100",l="97.9",c="99.3")))
    def test_09_good_short_h1_close_below_full_4h_fvg_edge(self):
        self.assertTrue(m.full_reclaim(z("SHORT"),bar(2*h4.H,h4.H,
                            o="98.7",h="99.2",l="97.0",c="97.8")))
    def test_10_same_child_first_touch_1h_close_is_not_available(self):
        q=z();q.first_touch_ms=3*h4.H
        self.assertFalse(m.full_reclaim(q,bar(2*h4.H,h4.H,
                              o="98.2",h="100",l="97.9",c="99.3")))
    def test_11_h1_reclaim_without_touch_of_parent_is_not_accepted(self):
        self.assertFalse(m.full_reclaim(z(),bar(2*h4.H,h4.H,
                              o="100",h="101",l="99.5",c="100.5")))
    def test_12_inverted_bearish_bar_not_long_reclaim(self):
        self.assertFalse(m.full_reclaim(z(),bar(2*h4.H,h4.H,
                              o="99.7",h="100.4",l="97",c="99.2")))
    def test_13_true_preconfirmed_15m_swing_break_replaces_onebar_snr(self):
        arr=four15(12*h4.M15)
        sw=Swing(h4.M15,"HIGH",D("105"),7*h4.M15,
                 11*h4.M15,2)
        x=m.new_signal_type("LONG",(),arr,(sw,))
        self.assertEqual(x[0],"CONFIRMED_15M_PIVOT_CLOSE_BREAK")
        self.assertEqual(x[1],sw)
    def test_14_future_pivot_confirmed_during_signal_bar_not_available(self):
        arr=four15(12*h4.M15)
        sw=Swing(h4.M15,"HIGH",D("105"),8*h4.M15,
                 arr[-1].close_ms,2)
        self.assertIsNone(m.new_signal_type("LONG",(),arr,(sw,)))
    def test_15_no_pivot_refuses_fake_one_candle_bos(self):
        arr=four15(12*h4.M15)
        self.assertTrue(arr[-1].c>arr[-2].h)
        self.assertIsNone(m.new_signal_type("LONG",(),arr,()))
    def test_16_price_only_wicks_through_structural_swing_is_not_BOS(self):
        arr=four15(12*h4.M15,break_high=False)
        sw=Swing(h4.M15,"HIGH",D("105"),7*h4.M15,
                 11*h4.M15,2)
        self.assertIsNone(m.new_signal_type("LONG",(),arr,(sw,)))
    def test_17_complete_three_closed_15m_gap_is_accepted(self):
        tf=h4.M15; a=bar(0,tf,o="99",h="101",l="97",c="100")
        b=bar(tf,tf,o="100",h="102",l="99",c="101")
        d=bar(2*tf,tf,o="101",h="106",l="103",c="105")
        o=bar(3*tf,tf,o="105",h="108",l="104",c="107")
        self.assertEqual(m.new_signal_type("LONG",(),(a,b,d,o),())[0],"IMB")
    def test_18_nonconsecutive_15m_protection(self):
        tf=h4.M15;arr=four15(12*tf)
        with self.assertRaisesRegex(m.C109Error,"NONCONSECUTIVE"):
            m.new_signal_type("LONG",(),(arr[0],arr[1],arr[2],bar(25*tf,tf)),())
    def test_19_4h_stop_and_4h_target_exact_unmodified_plan(self):
        now,f,s,rows,starts=fixtures()
        plan,why=h4.parent_plan(parent(),now,D("100"),f,s,rows,starts)
        self.assertEqual(why,"OK")
        self.assertEqual((plan["stop_source_tf"],plan["target_source_tf"]),("4H","4H"))
        self.assertEqual(plan["target"],"119.40")
    def test_20_one_model_one_fixed_atr_pad_risk_filter(self):
        self.assertEqual((h4.PAD,h4.MIN_RR,h4.MAX_AGE,h4.TTL,h4.BPS),
                         (D("0.15"),D("1.25"),48*h4.H,8*h4.H,(14,25,40)))
    def test_21_precommitted_insufficient_manifest_blocks_results(self):
        self.bad(lambda:m.analyze({},[]),"REQUIRES_FULL_PRECOMMITTED_768")
    def test_22_immutable_4h_trade_ready_evidence_earlier_failures_not_hidden(self):
        import c107_original_p4_false_signal_forensics as c107
        j=c107.frozen()
        self.assertEqual((len(j["C105"]["trades"]),len(j["C106"]["trades"])),(25,16))
    def test_23_confirmed_pivot_true_source_time_not_pivot_chart_index(self):
        x=Swing(h4.M15,"HIGH",D("105"),7*h4.M15,11*h4.M15,2)
        self.assertGreater(x.confirmed_ms,x.pivot_closed_ms)
    def test_24_empty_score_is_faithfully_rejected_not_won(self):
        a=m.score([])
        self.assertEqual(a["scores"]["25"]["n"],0)
        self.assertFalse(a["admission"]["passes_historical_screen"])
        self.assertFalse(a["admission"]["live_approved"])
if __name__=="__main__":unittest.main()
