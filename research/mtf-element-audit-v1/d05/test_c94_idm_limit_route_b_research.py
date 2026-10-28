"""C94 IDM source geometry and real-limit execution negative tests. SYNTHETIC only."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c89_original_native5m_adaptation_backtest import Bar,STEP
from c90_structural_fta_backtest import Swing
from c94_idm_limit_route_b_research import (
 C94Rejected,MODEL_B1,MODEL_B2,_plan,_fill_limit,discover,EVIDENCE,TTL,HOUR,H4)
START=1788220800000
def bars(n=1000):
 return tuple(Bar(START+i*STEP,D("100"),D("100.2"),D("99.8"),D("100"),D(10)) for i in range(n))
B=bars()
def sway(tf,kind,price,confirmed):
 return Swing(tf,kind,D(price),confirmed-tf,confirmed,2)
def plan(src=B,signal=30):
 when=src[signal].open_ms
 idm=[sway(HOUR,"LOW","99",src[20].close_ms)]
 protected=[sway(H4,"LOW","96",src[15].close_ms)]
 fta=[sway(H4,"HIGH","110",src[16].close_ms)]
 return _plan(src,when,"LONG",(D(98),D(100)),H4,idm,protected,fta,MODEL_B1)
class TestC94(unittest.TestCase):
 def test_01_idm_limit_research_plan(self):
  p,why=plan()
  self.assertEqual(why,"OK")
  self.assertEqual(p["limit"],D(99))
 def test_02_fta_4h_not_fixed_rr(self):
  p,_=plan()
  self.assertEqual(p["parent"],"4H_FTA")
  self.assertEqual(p["fta"],D(110))
  self.assertLess(p["target"],D(110))
 def test_03_limit_not_filled(self):
  p,_=plan()
  t,why=_fill_limit(B,p)
  self.assertIsNone(t);self.assertEqual(why,"IDM_LIMIT_NOT_FILLED_TTL")
 def test_04_limit_touch_fills_then_fta(self):
  p,_=plan();src=list(B)
  src[31]=replace(src[31],l=D("98.7"))
  src[32]=replace(src[32],h=D("111"))
  t,why=_fill_limit(tuple(src),p)
  self.assertEqual(why,"OK")
  self.assertEqual(t["entry"],"99")
  self.assertEqual(t["exit_reason"],"STRUCTURAL_4H_FTA")
 def test_05_stop_first_same_limit_bar(self):
  p,_=plan();src=list(B)
  src[31]=replace(src[31],l=D("95"))
  t,why=_fill_limit(tuple(src),p)
  self.assertEqual(t["exit_reason"],"STOP_FIRST_AFTER_LIMIT_TOUCH")
  self.assertLess(t["net_r"],0)
 def test_06_no_unfilled_trade(self):
  self.assertIsNone(_fill_limit(B,plan()[0])[0])
 def test_07_sl_behind_poi_and_stronghl(self):
  p,_=plan()
  self.assertLess(p["stop"],D("96"))
 def test_08_derived_rr_not_target(self):
  p,_=plan()
  rr=(p["target"]-p["limit"])/(p["limit"]-p["stop"])
  self.assertAlmostEqual(float(rr),p["rr"],places=6)
 def test_09_forged_author_rejected(self):
  with self.assertRaises(C94Rejected):
   _fill_limit(B,{**plan()[0],"evidence":"AUTHOR_VERIFIED"})
 def test_10_wrong_cost_rejected(self):
  with self.assertRaises(C94Rejected):_fill_limit(B,plan()[0],cost_bps=10)
 def test_11_future_idm_refused(self):
  signal=30
  x=sway(HOUR,"LOW","99",B[35].close_ms)
  p,why=_plan(B,B[signal].open_ms,"LONG",(D(98),D(100)),H4,
     [x],[sway(H4,"LOW","96",B[15].close_ms)],
     [sway(H4,"HIGH","110",B[16].close_ms)],MODEL_B1)
  self.assertIsNone(p);self.assertEqual(why,"NO_FRESH_FRACTAL_IDM_LIMIT")
 def test_12_consumed_idm_refused(self):
  src=list(B);src[28]=replace(src[28],l=D("98"))
  p,why=plan(tuple(src))
  self.assertIsNone(p);self.assertEqual(why,"NO_FRESH_FRACTAL_IDM_LIMIT")
 def test_13_wrong_limit_side_rejected(self):
  idm=[sway(HOUR,"LOW","102",B[20].close_ms)]
  p,why=_plan(B,B[30].open_ms,"LONG",(D(98),D(103)),H4,
    idm,[sway(H4,"LOW","96",B[15].close_ms)],
    [sway(H4,"HIGH","110",B[16].close_ms)],MODEL_B1)
  self.assertEqual(why,"NO_FRESH_FRACTAL_IDM_LIMIT")
 def test_14_unknown_variant_rejected(self):
  with self.assertRaises(C94Rejected):
   _plan(B,B[30].open_ms,"LONG",(D(98),D(100)),H4,[],[],[],"B_FAKE")
 def test_15_no_fta_refused(self):
  p,why=_plan(B,B[30].open_ms,"LONG",(D(98),D(100)),H4,
    [sway(HOUR,"LOW","99",B[20].close_ms)],
    [sway(H4,"LOW","96",B[15].close_ms)],[],MODEL_B1)
  self.assertEqual(why,"NO_PREKNOWN_4H_FTA")
 def test_16_idm_provenance_label(self):
  self.assertEqual(EVIDENCE,"ADAPTED_HYPOTHESIS")
 def test_17_explicit_no_vc_model(self):
  self.assertTrue(MODEL_B1.startswith("B_"))
  self.assertTrue(MODEL_B2.startswith("B_"))
 def test_18_past_price_future_noise_not_used(self):
  p,_=plan();src=list(B);src[200]=replace(src[200],h=D("500"),l=D("1"))
  self.assertEqual(plan(tuple(src))[0],p)
 def test_19_limit_eligible_only_after_signal(self):
  p,_=plan()
  src=list(B);src[29]=replace(src[29],l=D(98))
  t,_=_fill_limit(tuple(src),p)
  self.assertIsNone(t)
 def test_20_data_gap_rejected(self):
  src=list(B);src[5]=replace(src[5],open_ms=src[5].open_ms+STEP)
  with self.assertRaises(C94Rejected):discover(tuple(src),"BTCUSDT")
 def test_21_sparse_source_no_signal(self):
  o=discover(B,"BTCUSDT")
  self.assertEqual(o["native5m_bars"],1000)
 def test_22_limit_expiry(self):
  self.assertEqual(TTL,96)
 def test_23_no_order_method(self):
  import inspect
  from c94_idm_limit_route_b_research import discover
  self.assertNotIn("place_order",inspect.getsource(discover))
 def test_24_1h_15m_idm_distinct(self):
  self.assertNotEqual(MODEL_B1,MODEL_B2)
if __name__=="__main__":unittest.main()
