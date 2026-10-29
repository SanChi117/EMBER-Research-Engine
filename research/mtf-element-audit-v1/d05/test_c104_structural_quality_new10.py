"""C104 causal preentry / original native3m source / portfolio adverse tests."""
import sys,unittest
from decimal import Decimal as D
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c104_structural_quality_rules as q
import c104_native3m_source as source
import c104_native3m_quality_research as runner
import c102_c103_native3m_new_symbol_transfer as old
from c91_continuous_causal_route_a_paper import OHLC
from c90_structural_fta_backtest import Swing
from test_c102_c103_native3m_new_symbol_transfer import csv_fixture
H=3600000
START=old.BEGIN_MS

def conditions(now=START+12*24*H,side="LONG",target="101",stop="99"):
    hours=tuple(OHLC(START+i*H,START+(i+1)*H,D("100"),
       D("110"),D("90"),D("101"),D("1")) for i in range(768))
    fours=q.four_hour(hours)
    when=now-5*H
    lows=(Swing(q.FOUR,"LOW",D("90"),when-7*H,when-4*H,2),
          Swing(q.FOUR,"LOW",D("91"),when-4*H,when-1*H,2))
    highs=(Swing(q.FOUR,"HIGH",D("109"),when-7*H,when-4*H,2),
           Swing(q.FOUR,"HIGH",D("108"),when-4*H,when-1*H,2))
    trade={"side":side,"entry_ms":now,"bos_close_ms":now,
       "raid_closed_ms":now-3*60000,"entry":"100","stop":stop,
       "target":target,"fta_confirmed_ms":now-H,
       "symbol":"NEARUSDT","exit_ms":now+H}
    return trade,hours,fours,lows,highs

class Adversarial(unittest.TestCase):
    def reject(self,f,e):
        with self.assertRaisesRegex((q.C104QualityError,source.C104SourceError,runner.C104Rejected),e):
            f()
    def test_01_ten_frozen_crypto(self):
        self.assertEqual(len(source.SYMBOLS),10)
    def test_02_32_days_320_zip(self):
        self.assertEqual((len(source.DAYS),source.EXPECTED),(32,320))
    def test_03_no_old_c93_btc_eth_sol_xrp_bch(self):
        self.assertFalse(set(source.SYMBOLS)&{"BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"})
    def test_04_no_old_c102_five(self):
        self.assertFalse(set(source.SYMBOLS)&set(old.SYMBOLS))
    def test_05_valid_original_3m(self):
        xs,p=source.daily("NEARUSDT","2026-09-26",fetch=csv_fixture("NEARUSDT"))
        self.assertEqual(len(xs),480)
        self.assertEqual(p["timeframe"],"NATIVE_3M")
    def test_06_reject_old_source_symbol(self):
        self.reject(lambda:source.daily("LINKUSDT","2026-09-26"),"UNREGISTERED")
    def test_07_reject_unregistered_date(self):
        self.reject(lambda:source.daily("NEARUSDT","2026-10-29"),"UNREGISTERED")
    def test_08_corrupt_checksum(self):
        f=csv_fixture("NEARUSDT")
        self.reject(lambda:source.daily("NEARUSDT","2026-09-26",fetch=lambda u: b"abc" if u.endswith(".CHECKSUM") else f(u)),"CHECKSUM")
    def test_09_gapped_source(self):
        f=csv_fixture("NEARUSDT",mutation=lambda r,i:r.__setitem__(0,str(int(r[0])+180000)) if i==4 else None)
        self.reject(lambda:source.daily("NEARUSDT","2026-09-26",fetch=f),"NATIVE3M_GAP")
    def test_10_bad_native_ohlc(self):
        f=csv_fixture("NEARUSDT",mutation=lambda r,i:r.__setitem__(2,"80") if i==4 else None)
        self.reject(lambda:source.daily("NEARUSDT","2026-09-26",fetch=f),"IMPOSSIBLE_SOURCE_OHLCV")
    def test_11_invalid_4h_length(self):
        self.reject(lambda:q.four_hour(tuple()),"COMPLETE_32")
    def test_12_valid_4h_full_192(self):
        t,h,f,lows,highs=conditions()
        self.assertEqual((len(h),len(f)),(768,192))
        self.assertEqual(f[0].start_ms,START)
    def test_13_4h_bars_fully_closed(self):
        t,h,f,lows,highs=conditions()
        self.assertEqual(f[4].close_ms,START+20*H)
    def test_14_long_slope_and_12h_reach(self):
        t,h,f,lows,highs=conditions()
        z=q.asof_quality(t,h,f,lows+highs)
        self.assertTrue(z["pass"])
        self.assertTrue(z["four_hour_direction_ok"])
    def test_15_unconfirmed_future_pivots_ignored(self):
        t,h,f,lows,highs=conditions()
        future=Swing(q.FOUR,"LOW",D("300"),t["entry_ms"],t["entry_ms"]+H,2)
        z=q.asof_quality(t,h,f,lows+highs+(future,))
        self.assertTrue(z["pass"])
    def test_16_no_pivots_no_direction(self):
        t,h,f,lows,highs=conditions()
        self.assertFalse(q.asof_quality(t,h,f,())["pass"])
    def test_17_wrong_low_slope(self):
        t,h,f,lows,highs=conditions()
        invalid=Swing(q.FOUR,"LOW",D("88"),lows[-1].pivot_closed_ms,
                     lows[-1].confirmed_ms,2)
        self.assertFalse(q.asof_quality(t,h,f,(lows[0],invalid)+highs)["four_hour_direction_ok"])
    def test_18_far_fta_rejected(self):
        t,h,f,lows,highs=conditions(target="150")
        self.assertFalse(q.asof_quality(t,h,f,lows+highs)["fta_12h_range_ok"])
    def test_19_target_untouched(self):
        t,h,f,lows,highs=conditions()
        before=t.copy()
        q.asof_quality(t,h,f,lows+highs)
        self.assertEqual(t,before)
    def test_20_futuristic_fta_rejected(self):
        t,h,f,lows,highs=conditions()
        t["fta_confirmed_ms"]=t["entry_ms"]+1
        self.reject(lambda:q.asof_quality(t,h,f,lows+highs),"FUTURE_1H_FTA")
    def test_21_bos_same_entry(self):
        t,h,f,lows,highs=conditions()
        t["bos_close_ms"]+=180000
        self.reject(lambda:q.asof_quality(t,h,f,lows+highs),"BOS_ENTRY")
    def test_22_invalid_long_structure(self):
        t,h,f,lows,highs=conditions(stop="102")
        self.reject(lambda:q.asof_quality(t,h,f,lows+highs),"INVALID_STRUCTURAL")
    def test_23_missing_1h_context(self):
        t,h,f,lows,highs=conditions()
        self.reject(lambda:q.asof_quality(t,h[:3],f,lows+highs),"ASOF_WARMUP")
    def test_24_per_symbol_busy_slot(self):
        t,h,f,lows,highs=conditions()
        a={**t,"preentry_quality":{"pass":True}}
        b={**a,"entry_ms":a["entry_ms"]+H//2}
        self.assertEqual(len(q.select_symbol([a,b])),1)
    def test_25_quality_gate_drops_fail(self):
        t,h,f,lows,highs=conditions()
        a={**t,"preentry_quality":{"pass":False}}
        self.assertEqual(q.select_symbol([a],True),[])
    def test_26_portfolio_same_side_cluster(self):
        t,h,f,lows,highs=conditions()
        a=dict(t);b={**t,"symbol":"UNIUSDT"}
        done,blocked=q.cap_direction([a,b])
        self.assertEqual((len(done),len(blocked)),(1,1))
    def test_27_portfolio_opposite_side_parallel_allowed(self):
        t,h,f,lows,highs=conditions()
        a=dict(t);b={**t,"symbol":"UNIUSDT","side":"SHORT"}
        done,blocked=q.cap_direction([a,b])
        self.assertEqual((len(done),len(blocked)),(2,0))
    def test_28_portfolio_after_prior_close(self):
        t,h,f,lows,highs=conditions()
        a=dict(t);b={**t,"symbol":"UNIUSDT","entry_ms":t["exit_ms"]}
        self.assertEqual(len(q.cap_direction([a,b])[0]),2)
    def test_29_bad_direction_portfolio(self):
        t,h,f,lows,highs=conditions()
        self.reject(lambda:q.cap_direction([{**t,"side":"WAIT"}]),"UNKNOWN_SIDE")
    def test_30_unchanged_C93_C102_sha(self):
        runner.check_sha()
    def test_31_4h_pivot_values_do_not_redefine_tp(self):
        t,h,f,lows,highs=conditions()
        z=q.asof_quality(t,h,f,lows+highs)
        self.assertNotIn("suggested_tp",z)
        self.assertEqual(t["target"],"101")
    def test_32_primary_never_trade_approved(self):
        score={"25":{"n":0,"sum_r":0,"pf":None,"dd_1pct_risk_pct":0},
               "40":{"n":0,"sum_r":0,"pf":None,"dd_1pct_risk_pct":0},
               "fold_early_n":0,"fold_late_n":0}
        z=runner.accept({"scores":score},{"scores":score})
        self.assertFalse(z["passes_historical_screen"])
        self.assertFalse(z["live_approved"])
if __name__=="__main__":unittest.main()
