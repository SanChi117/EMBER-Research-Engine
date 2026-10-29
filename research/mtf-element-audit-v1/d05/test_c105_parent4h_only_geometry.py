"""C105 prior-to-outcomes negative tests: SAME 4H parent SL/TP, no future TF, original native3m paper."""
import sys,unittest
from pathlib import Path
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parent))
from c21_native3m_source_bridge import Original3mRow
from c90_structural_fta_backtest import Swing
from c91_continuous_causal_route_a_paper import OHLC
from test_c102_c103_native3m_new_symbol_transfer import csv_fixture
import c105_parent4h_structural_geometry as m
import c105_parent4h_native3m_source as s
import c105_parent4h_native3m_research as run
import c104_native3m_source as old
from c102_c103_native3m_new_symbol_transfer import BEGIN_MS

def bar(at,tf,o="100",h="102",l="98",c="100"):
    return OHLC(at,at+tf,D(o),D(h),D(l),D(c),D("1"))
def parent(side="LONG"):
    return m.Parent(side,D("98"),D("99"),BEGIN_MS-2*m.H4,"zone-p4")
def fixtures(side="LONG"):
    now=BEGIN_MS+9*m.D1
    prev=now-16*m.H4
    four=tuple(bar(prev+i*m.H4,m.H4) for i in range(16))
    sw=(Swing(m.H4,"HIGH",D("120"),now-10*m.H4,now-8*m.H4,2),
        Swing(m.H4,"LOW",D("80"),now-10*m.H4,now-8*m.H4,2))
    start=now-30*m.THREE
    native=tuple(Original3mRow("BNBUSDT",start+i*m.THREE,start+(i+1)*m.THREE,
        D("100"),D("102"),D("98"),D("100"),D("1"),"raw","sha")
        for i in range(30))
    return now,four,sw,native,tuple(x.start_ms for x in native)
def no_trade_future_cond():
    now,f,sw,rows,starts=fixtures()
    return m.parent_plan(parent(),now,D("100"),f,sw,rows,starts)
class C105Adversarial(unittest.TestCase):
    def expect(self,fn,code):
        with self.assertRaisesRegex((m.C105Rejected,run.C105Rejected),code):
            fn()
    def test_01_ten_new_frozen_symbols(self):
        self.assertEqual(len(s.SYMBOLS),10)
        self.assertEqual(s.EXPECTED,320)
        self.assertEqual(len(s.DAYS),32)
        self.assertNotIn("BTCUSDT",s.SYMBOLS)
    def test_02_no_c104_symbols(self):
        self.assertFalse(set(s.SYMBOLS)&set(old.SYMBOLS))
    def test_03_scope_loader_restore_after_failure(self):
        prior=old.SYMBOLS
        def broken(url):raise RuntimeError("fake network")
        with self.assertRaises(RuntimeError):
            s.original_all(fetch=broken)
        self.assertEqual(old.SYMBOLS,prior)
    def test_04_whole_original_daily_crypto_source(self):
        original=old.SYMBOLS
        old.SYMBOLS=s.SYMBOLS
        try:
            a,meta=old.daily("BNBUSDT","2026-09-26",fetch=csv_fixture("BNBUSDT"))
        finally:old.SYMBOLS=original
        self.assertEqual(len(a),480)
        self.assertEqual(meta["bars"],480)
    def test_05_accept_only_original_native3m_type(self):
        self.expect(lambda:m.aggregate(tuple([bar(0,m.THREE)]),m.H4),"NATIVE3M_TYPE")
    def test_06_reject_unknown_aggregation_tf(self):
        self.expect(lambda:m.aggregate(tuple([bar(0,m.THREE)]),2*m.H),"UNREGISTERED")
    def test_07_reject_wrong_week_alignment(self):
        self.expect(lambda:m.aggregate(tuple([bar(0,m.THREE)]),m.W1,0),"BAD_UTC")
    def test_08_original_3m_to_15m_full(self):
        a,_,_,_,_=fixtures()
        rows=tuple(Original3mRow("BNBUSDT",a+i*m.THREE,a+(i+1)*m.THREE,
          D("100"),D("101"),D("99"),D("100"),D("1"),"x","y") for i in range(10))
        xs=m.aggregate(rows,m.M15)
        self.assertEqual(len(xs),2)
        self.assertEqual(xs[0].close_ms,a+m.M15)
    def test_09_only_closed_3m_omit_partial_4h(self):
        a,_,_,_,_=fixtures()
        rows=tuple(Original3mRow("BNBUSDT",a+i*m.THREE,a+(i+1)*m.THREE,
          D("100"),D("101"),D("99"),D("100"),D("1"),"x","y") for i in range(79))
        self.assertEqual(len(m.aggregate(rows,m.H4)),0)
    def test_10_14_true_ranges_4h(self):
        _,four,_,_,_=fixtures()
        self.assertEqual(m.four_atr(four),D("4"))
    def test_11_4h_atr_must_be_full(self):
        _,four,_,_,_=fixtures()
        self.expect(lambda:m.four_atr(four[:10]),"H4_ATR_WARMUP")
    def test_12_three_4h_fvg_long(self):
        a,b,c=bar(0,m.H4,h="100",l="95"),bar(m.H4,m.H4),bar(2*m.H4,m.H4,h="106",l="101",c="103")
        day=(bar(-2*m.D1,m.D1,c="99"),bar(-m.D1,m.D1,c="100"))
        week=(bar(-m.W1,m.W1,o="99",c="100"),)
        z,why=m.zone_from_three((a,b,c),day,week)
        self.assertEqual(why,"OK")
        self.assertEqual((z.side,z.lower,z.upper),("LONG",D("100"),D("101")))
    def test_13_no_unclosed_daily_weekly_context(self):
        a,b,c=bar(0,m.H4,h="100",l="95"),bar(m.H4,m.H4),bar(2*m.H4,m.H4,h="106",l="101",c="103")
        z,why=m.zone_from_three((a,b,c),(),())
        self.assertIsNone(z)
        self.assertIn("CONFLICT",why)
    def test_14_no_fvg_false_zone(self):
        a,b,c=bar(0,m.H4),bar(m.H4,m.H4),bar(2*m.H4,m.H4)
        z,why=m.zone_from_three((a,b,c),(),())
        self.assertIsNone(z)
        self.assertEqual(why,"NO_4H_FVG")
    def test_15_first_touch_requires_after_creation(self):
        z=parent()
        self.assertFalse(m.first_touch(z,bar(z.created_ms-m.M15,m.M15)))
        self.assertTrue(m.first_touch(z,bar(z.created_ms,m.M15)))
    def test_16_rejection_must_be_completed_hour_after_touch(self):
        z=parent();z.state="WAIT_1H_REJECTION";z.first_touch_ms=BEGIN_MS+8*m.H
        self.assertFalse(m.rejection(z,bar(z.first_touch_ms-m.H,m.H,o="98",h="100",l="97",c="100")))
        self.assertTrue(m.rejection(z,bar(z.first_touch_ms,m.H,o="98",h="100",l="97",c="100")))
    def test_17_reject_unconfirmed_15m(self):
        z=parent();z.state="WAIT_15M_VC";z.rejection_ms=BEGIN_MS+4*m.H
        last=tuple(bar(z.rejection_ms+(i-3)*m.M15,m.M15) for i in range(4))
        self.assertFalse(m.vc(z,last))
    def test_18_both_exit_sources_4h(self):
        now,f,sw,rows,starts=fixtures()
        plan,why=m.parent_plan(parent(),now,D("100"),f,sw,rows,starts)
        self.assertEqual(why,"OK")
        self.assertEqual((plan["stop_source_tf"],plan["target_source_tf"]),("4H","4H"))
        self.assertEqual(plan["stop"],"97.40")
        self.assertEqual(plan["target"],"119.40")
    def test_19_no_fixed_rr_tp(self):
        now,f,sw,rows,starts=fixtures()
        plan,_=m.parent_plan(parent(),now,D("100"),f,sw,rows,starts)
        self.assertEqual(D(plan["target"]),D("120")-D("0.15")*m.four_atr(f))
        self.assertGreater(plan["derived_rr"],m.MIN_RR)
    def test_20_no_4h_fta_no_trade(self):
        now,f,sw,rows,starts=fixtures()
        p,why=m.parent_plan(parent(),now,D("100"),f,(),rows,starts)
        self.assertIsNone(p)
        self.assertEqual(why,"NO_UNCONSUMED_CONFIRMED_4H_FTA")
    def test_21_future_4h_pivot_hidden(self):
        now,f,sw,rows,starts=fixtures()
        future=Swing(m.H4,"HIGH",D("110"),now-m.H4,now+m.H4,2)
        plan,_=m.parent_plan(parent(),now,D("100"),f,sw+(future,),rows,starts)
        self.assertEqual(plan["fta"],"120")
    def test_22_consumed_4h_target_rejected(self):
        now,f,sw,rows,starts=fixtures()
        pivot=Swing(m.H4,"HIGH",D("101"),now-12*m.H4,now-9*m.H4,2)
        p,why=m.parent_plan(parent(),now,D("100"),f,(pivot,),rows,starts)
        self.assertIsNone(p)
        self.assertEqual(why,"NO_UNCONSUMED_CONFIRMED_4H_FTA")
    def test_23_ban_future_4h_bar_in_stop_calculation(self):
        now,f,sw,rows,starts=fixtures()
        bad=f+(bar(now,m.H4),)
        self.expect(lambda:m.parent_plan(parent(),now,D("100"),bad,sw,rows,starts),"FUTURE_OR_UNCONFIRMED")
    def test_24_stops_have_no_3m_or_15m_data_dependency(self):
        now,f,sw,rows,starts=fixtures()
        plan,_=m.parent_plan(parent(),now,D("100"),f,sw,rows,starts)
        self.assertEqual(plan["pad_source"],"ATR_FULLY_CLOSED_4H")
        self.assertEqual(plan["stop_source"],"4H_FVG_FAR_EDGE")
    def test_25_stop_first_if_both_hit_native3m(self):
        now,f,sw,rows,starts=fixtures()
        plan,_=m.parent_plan(parent(),now,D("100"),f,sw,rows,starts)
        candle=Original3mRow("BNBUSDT",now,now+m.THREE,D("100"),D("130"),D("90"),D("100"),D("1"),"x","x")
        out=m.simulate((candle,),0,"LONG",plan)
        self.assertEqual(out["exit_reason"],"STOP_FIRST_SAME_3M")
        self.assertLess(out["net_r"],0)
    def test_26_no_next_open_invented(self):
        now,f,sw,rows,starts=fixtures()
        plan,_=m.parent_plan(parent(),now,D("100"),f,sw,rows,starts)
        candle=Original3mRow("BNBUSDT",now,now+m.THREE,D("101"),D("102"),D("99"),D("101"),D("1"),"x","x")
        self.expect(lambda:m.simulate((candle,),0,"LONG",plan),"NEXT_ORIGINAL")
    def test_27_no_fee_after_discovery_unknown_bps(self):
        now,f,sw,rows,starts=fixtures()
        plan,_=m.parent_plan(parent(),now,D("100"),f,sw,rows,starts)
        candle=Original3mRow("BNBUSDT",now,now+m.THREE,D("100"),D("101"),D("99"),D("100"),D("1"),"x","x")
        self.expect(lambda:m.simulate((candle,),0,"LONG",plan,2),"UNREGISTERED_FEE")
    def test_28_exact_horizon_48h(self):
        self.assertEqual(m.MAX_HOLD,960)
    def test_29_prior_c93_c102_c104_immutable_sha(self):
        run.frozen_source_checks()
    def test_30_screen_no_trades_must_fail(self):
        scores={"25":{"n":0,"sum_r":0,"pf":None,"dd_1pct_risk_pct":0},
            "40":{"n":0,"sum_r":0,"pf":None,"dd_1pct_risk_pct":0},
            "fold_early_n":0,"fold_late_n":0}
        outcome=run.admission(scores)
        self.assertFalse(outcome["passes_historical_screen"])
        self.assertFalse(outcome["live_approved"])
if __name__=="__main__":unittest.main()
