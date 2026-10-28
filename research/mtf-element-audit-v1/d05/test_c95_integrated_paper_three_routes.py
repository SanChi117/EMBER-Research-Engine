"""C95 integrated real-source A/B/C secure PAPER portfolio and counterexamples."""
import unittest
from pathlib import Path
from copy import deepcopy
from c95_integrated_paper_three_routes import (
 C95Rejected,A_SHA,B_SHA,C_SHA,START,END,SPLIT,PRIORITY,
 _play,_metrics,_flat,_validate,integrated,from_frozen,read_and_pin,
 _period,DAY_R_LIMIT,WEEK_R_LIMIT)
ROOT=Path(__file__).resolve().parents[1]
def trade(route="A",entry=START+10000,exit=START+20000,result=-1.0,symbol="BTCUSDT"):
 return {"symbol":symbol,"source_route":route,"route":route+"_SYNTH",
         "entry_ms":entry,"exit_ms":exit,"net_r":result}
class TestC95(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.a=read_and_pin(ROOT/"evidence/c92/C92_APR_OCT_5_SYMBOL_FULL_CAUSAL_STRATEGY_REPLAY.json",A_SHA)
  cls.b=read_and_pin(ROOT/"evidence/c94/C94_ORIGINAL_BINANCE_IDM_LIMIT_BOTH_MODELS_PAPER.json",B_SHA)
  cls.c=read_and_pin(ROOT/"evidence/c93/C93_ORIGINAL_NATIVE3M_ROUTE_C_BOS_PAPER_REPLAY.json",C_SHA)
  cls.r=integrated(cls.a,cls.b,cls.c)
 def test_01_original_source_counts(self):
  self.assertEqual(self.a["source_bars"],266400)
  self.assertEqual(self.b["original_bars"],266400)
  self.assertEqual(self.c["full_native_3m_bars"],76800)
 def test_02_original_3_model_counts(self):
  self.assertEqual(self.a["all"]["count"],34)
  self.assertEqual(self.b["all"]["count"],15)
  self.assertEqual(self.c["all"]["count"],58)
 def test_03_sha256_pinned(self):
  self.assertEqual(len(A_SHA),64)
  self.assertEqual(len(B_SHA),64)
  self.assertEqual(len(C_SHA),64)
 def test_04_invalid_source_sha_refused(self):
  with self.assertRaises(C95Rejected):
   read_and_pin(ROOT/"evidence/c93/C93_ORIGINAL_NATIVE3M_ROUTE_C_BOS_PAPER_REPLAY.json",A_SHA)
 def test_05_real_source_readiness(self):
  self.assertTrue(self.r["nontradeable"])
  self.assertFalse(self.r["ready_for_live"])
 def test_06_three_routes_separated(self):
  self.assertEqual(set(self.r["models"]),{"A","B","C"})
 def test_07_structural_targets_only(self):
  self.assertFalse(self.a["fixed_rr_targets"])
  self.assertFalse(self.b["fixed_rr_target"])
  self.assertFalse(self.c["fixed_rr_target"])
 def test_08_all_six_permutations_two_risks(self):
  self.assertEqual(len(self.r["portfolio_sensitivity"]),12)
 def test_09_original_3m_no_5m_substitution(self):
  self.assertTrue(all(t["source_tf"]=="NATIVE_3M"
    for v in self.c["by_symbol"].values() for t in v["trades"]))
 def test_10_all_preselected_none(self):
  self.assertEqual(self.a["source_selection"],"ALL_CONTINUOUS_NATIVE5M_NO_C73_P0_EVENT_SELECTION")
 def test_11_no_early_trades_outside_common_window(self):
  for r in self.r["portfolio_sensitivity"].values():
   self.assertTrue(all(START<=x["entry_ms"]<END for x in r["trades"]))
 def test_12_global_one_no_overlap(self):
  for r in self.r["portfolio_sensitivity"].values():
   a=r["trades"]
   self.assertTrue(all(x["exit_ms"]<=y["entry_ms"] for x,y in zip(a,a[1:])))
 def test_13_no_orders(self):
  self.assertEqual(self.r["orders"],[])
  self.assertEqual(self.r["fills"],[])
  self.assertEqual(self.r["live_trades"],[])
 def test_14_conflicting_source_a_rejected(self):
  o=deepcopy(self.a);o["fixed_rr_targets"]=True
  with self.assertRaises(C95Rejected):_validate(o,self.b,self.c)
 def test_15_legacy_fixed_rr_b_rejected(self):
  o=deepcopy(self.b);o["fixed_rr_target"]=True
  with self.assertRaises(C95Rejected):_validate(self.a,o,self.c)
 def test_16_fake_3m_c_rejected(self):
  o=deepcopy(self.c);o["full_native_3m_bars"]=46080
  with self.assertRaises(C95Rejected):_validate(self.a,self.b,o)
 def test_17_cross_route_trade_rejected(self):
  o=deepcopy(self.c)
  sym=next(s for s,v in o["by_symbol"].items() if v["trades"])
  o["by_symbol"][sym]["trades"][0]["route"]="A_FAKE"
  with self.assertRaises(C95Rejected):_validate(self.a,self.b,o)
 def test_18_tie_order_deterministic(self):
  x=[trade("C"),trade("A"),trade("B")]
  a,_=_play(x,priority=("A","B","C"),limits=False)
  b,_=_play(x,priority=("C","B","A"),limits=False)
  self.assertEqual(a[0]["source_route"],"A")
  self.assertEqual(b[0]["source_route"],"C")
 def test_19_future_trade_does_not_block_earlier(self):
  x=[trade("A",START+50000,START+70000),
     trade("B",START+10000,START+20000)]
  a,_=_play(x,limits=False)
  self.assertEqual(len(a),2)
 def test_20_global_overlap_reject(self):
  x=[trade("A",START+10000,START+50000),
     trade("B",START+20000,START+30000,symbol="ETHUSDT")]
  a,rej=_play(x,limits=False)
  self.assertEqual(len(a),1)
  self.assertEqual(rej["GLOBAL_POSITION_OVERLAP"],1)
 def test_21_daily_stop_after_realized_only(self):
  x=[trade("A",START+10000,START+20000,-2.1),
     trade("B",START+30000,START+40000,1)]
  a,rejects=_play(x,limits=True)
  self.assertEqual(len(a),1)
  self.assertEqual(rejects["PREDECLARED_DAILY_WEEKLY_STOP"],1)
 def test_22_daily_limit_does_not_anticipate_future_loss(self):
  x=[trade("A",START+10000,START+50000,-2.1),
     trade("B",START+30000,START+35000,1,symbol="ETHUSDT")]
  a,_=_play(x,global_one=False,limits=True)
  self.assertEqual(len(a),2)
 def test_23_risk_controls_are_not_tp(self):
  self.assertLess(DAY_R_LIMIT,0)
  self.assertLess(WEEK_R_LIMIT,0)
 def test_24_empty_hypothetical_metrics(self):
  self.assertEqual(_metrics([])["trades"],0)
 def test_25_historical_paper_nav_not_capital_claim(self):
  m=_metrics([trade(result=-1)])
  self.assertLess(m["illustrative_1pct_risk_compounded_equity_pct"],0)
 def test_26_freeze_source_window(self):
  self.assertEqual(SPLIT,1789862400000)
  self.assertLess(START,SPLIT)
  self.assertLess(SPLIT,END)
 def test_27_non_pristine_out_of_sample_label(self):
  self.assertIn("NOT_PRISTINE",self.r["source_precalibrated_with_history"])
 def test_28_real_source_counterfactual_priority(self):
  for k,v in self.r["portfolio_sensitivity"].items():
   self.assertEqual(v["results"]["trades"],len(v["trades"]))
 def test_29_limit_fill_mandatory_B(self):
  self.assertTrue(self.b["limit_fill_mandatory"])
 def test_30_all_models_have_1h_fta(self):
  self.assertTrue(all(t["fta_tf"]=="4h" for m in self.b["by_symbol"].values() for t in m["trades"]))
if __name__=="__main__":unittest.main()
