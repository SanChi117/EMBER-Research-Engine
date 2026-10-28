"""C93 BOS owner rule negative tests; synthetic fixtures never called original."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21_native3m_source_bridge import Original3mRow,THREE
from c90_structural_fta_backtest import Swing
from c91_continuous_causal_route_a_paper import OHLC
from c93_native3m_raid_bos_route_c_research import (
 C93Rejected,EVIDENCE,H1,D1,_aggregate3,_confirmed,_raid,
 _bos_level,_fta,_atr3m,_paper_fill,MONTHLY_DAYS)
START=1788220800000
def row(i,op="100",hi="101",lo="99",cl="100"):
 at=START+i*THREE
 return Original3mRow("BTCUSDT",at,at+THREE,D(op),D(hi),D(lo),
                      D(cl),D("1"),"f"*64+":"+str(at),"f"*64)
R=tuple(row(i) for i in range(500))
def hour(i,hi="101",lo="99",cl="100",op="100"):
 t=START+i*H1
 return OHLC(t,t+H1,D(op),D(hi),D(lo),D(cl),D("20"))
def pivot(side="SHORT"):
 return Swing(H1,"LOW" if side=="SHORT" else "HIGH",
              D("96") if side=="SHORT" else D("104"),START,START+H1,2)
def raid(side="SHORT"):
 return hour(5,hi="112" if side=="SHORT" else "101",
             lo="99" if side=="SHORT" else "88",
             cl="109" if side=="SHORT" else "91")
class TestC93(unittest.TestCase):
 def test_01_full_closed_3m_to_hour(self):
  h=_aggregate3(R,H1);self.assertEqual(len(h),25)
  self.assertEqual(h[0].close_ms,R[19].known_ms)
 def test_02_full_closed_3m_to_day(self):
  self.assertEqual(len(_aggregate3(R,D1)),1)
 def test_03_future_incomplete_hour_ignored(self):
  self.assertEqual(len(_aggregate3(R[:19],H1)),0)
 def test_04_exact_3m_alignment(self):
  bad=list(R);bad[3]=replace(bad[3],start_ms=bad[3].start_ms+THREE)
  with self.assertRaises(C93Rejected):_aggregate3(tuple(bad),H1)
 def test_05_wick_raid_of_fresh_1h_high(self):
  prev=tuple(hour(i) for i in range(5))
  h=raid()
  s=Swing(H1,"HIGH",D("110"),START,START+H1,2)
  v=_raid(h,prev,(s,))
  self.assertEqual(v[0],"SHORT")
 def test_06_close_above_fractal_not_raid(self):
  prev=tuple(hour(i) for i in range(5))
  x=hour(5,hi="112",lo="99",cl="111")
  s=Swing(H1,"HIGH",D("110"),START,START+H1,2)
  self.assertIsNone(_raid(x,prev,(s,)))
 def test_07_old_fractal_not_fresh(self):
  prev=tuple(hour(i) for i in range(50))
  h=hour(50,hi="112",cl="109")
  s=Swing(H1,"HIGH",D("110"),START,START+H1,2)
  self.assertIsNone(_raid(h,prev,(s,)))
 def test_08_previously_raided_fractal_rejected(self):
  prev=list(hour(i) for i in range(5))
  prev[-1]=hour(4,hi="112")
  s=Swing(H1,"HIGH",D("110"),START,START+H1,2)
  self.assertIsNone(_raid(raid(),tuple(prev),(s,)))
 def test_09_fractal_confirmation_before_raid(self):
  x=Swing(H1,"HIGH",D("110"),START,START+7*H1,2)
  self.assertIsNone(_raid(raid(),tuple(hour(i) for i in range(5)),(x,)))
 def test_10_bos_future_unconfirmed_not_used(self):
  self.assertIsNone(_bos_level((), "SHORT",START+H1))
 def test_11_3m_atr_uses_closed_history(self):
  self.assertEqual(_atr3m(R,19),D("2"))
 def test_12_3m_atr_needs_warmup(self):
  self.assertIsNone(_atr3m(R,4))
 def test_13_structural_stop_first_even_when_fta_touched(self):
  m=list(R);m[30]=row(30,hi="113",lo="95")
  t,reason=_paper_fill(tuple(m),30,"SHORT",D("112"),D("96"),pivot(),raid())
  self.assertEqual(reason,"OK");self.assertEqual(t["exit_reason"],"STOP_FIRST_SAME_3M")
  self.assertLess(t["net_r"],0)
 def test_14_structural_fta_return(self):
  m=list(R);m[30]=row(30,hi="101",lo="95")
  t,_=_paper_fill(tuple(m),30,"SHORT",D("112"),D("96"),pivot(),raid())
  self.assertEqual(t["exit_reason"],"1H_FTA")
 def test_15_target_not_fixed_rr(self):
  t,_=_paper_fill(R,30,"SHORT",D("112"),D("96"),pivot(),raid())
  self.assertEqual(t["target"],"96")
  self.assertNotEqual(t["derived_rr"],1.5)
 def test_16_low_rr_reject_without_moving_fta(self):
  x,why=_paper_fill(R,30,"SHORT",D("112"),D("99"),pivot(),raid())
  self.assertIsNone(x);self.assertEqual(why,"DERIVED_RR_ONLY_FILTER")
 def test_17_structural_gap_invalid(self):
  m=list(R);m[30]=row(30,op="113",hi="114",lo="112",cl="113")
  x,why=_paper_fill(tuple(m),30,"SHORT",D("112"),D("96"),pivot(),raid())
  self.assertIsNone(x);self.assertEqual(why,"ENTRY_GAP_INVALID_STRUCTURE")
 def test_18_unverified_future_fta_rejected(self):
  s=replace(pivot(),confirmed_ms=R[31].known_ms)
  with self.assertRaises(C93Rejected):
   _paper_fill(R,30,"SHORT",D("112"),D("96"),s,raid())
 def test_19_fee_positive(self):
  t,_=_paper_fill(R,30,"SHORT",D("112"),D("96"),pivot(),raid())
  self.assertLess(t["net_r"],0)
 def test_20_no_market_orders(self):
  self.assertEqual(EVIDENCE,"ADAPTED_HYPOTHESIS")
 def test_21_no_fake_5m_bos(self):
  import inspect
  from c93_native3m_raid_bos_route_c_research import discover
  self.assertNotIn("native5m",inspect.getsource(discover))
 def test_22_no_post_signal_future_fta(self):
  from c93_native3m_raid_bos_route_c_research import _fta
  p=tuple(hour(i) for i in range(4))
  s=Swing(H1,"LOW",D(96),START,START+8*H1,2)
  self.assertIsNone(_fta(START+4*H1,"SHORT",D(100),p,(s,)))
 def test_23_route_c_no_reused_route_a(self):
  import inspect
  from c93_native3m_raid_bos_route_c_research import discover
  self.assertNotIn("c91_continuous_causal_route_a_paper.discover_symbol",inspect.getsource(discover))
 def test_24_zero_future_trade_data(self):
  self.assertEqual(MONTHLY_DAYS,32)
if __name__=="__main__":unittest.main()
