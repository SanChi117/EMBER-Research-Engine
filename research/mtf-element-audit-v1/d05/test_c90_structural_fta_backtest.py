"""C90: 1H FTA + 15m StrongHL causal anti-lookahead and structural tests.

Only the integration CI uses SHA-verified real Binance files. Test fixtures
below are deliberately SYNTHETIC and are never called market positives.
"""
import unittest
from decimal import Decimal as D
from dataclasses import replace
from c89_original_native5m_adaptation_backtest import Bar,STEP
from c90_structural_fta_backtest import (
 ClosedBar,Swing,C90Rejected,PIVOT_WIDTHS,MIN_RR_FILTER,
 confirmed_swings,closed_tfs,atr5m,structure_at_signal,replay_plan,
 dumps,STATUS)

START=1800000000000
def demo():
    bs=[]
    for n in range(48*12):
        hour=n//12
        h=D("110") if hour==13 and n%12==0 else D("100.2")
        low=D("98") if hour==20 and n%12==0 else D("99.8")
        bs.append(Bar(START+n*STEP,D("100"),h,low,D("100"),D("1")))
    return tuple(bs)
B=demo()
SIG=START+25*3600000
E={"case_key":"SYNTHETIC/0","priority":0,"symbol":"BTCUSDT",
   "side":"LONG","poi_low":"97","poi_high":"99",
   "first5m_known_ms":SIG,"readiness":"NOT_TRADE_READY"}
def plan(bs=B,event=E,width=2):
    return structure_at_signal(bs,event,width=width)
class TestC90(unittest.TestCase):
 def test_01_course_target_tf_is_1h(self):
    x=plan();self.assertEqual(x["status"],"STRUCTURAL_PLAN_PAPER");self.assertEqual(x["fta_tf"],"1h")
 def test_02_stronghl_tf_15m(self):
    self.assertEqual(plan()["stronghl_tf"],"15m")
 def test_03_target_is_actual_obstacle_less_buffer(self):
    x=plan();self.assertEqual(D(x["fta"]),D("110"));self.assertLess(D(x["target"]),D("110"))
 def test_04_stop_behind_structure_and_poi(self):
    self.assertLess(D(plan()["stop"]),D(E["poi_low"]))
 def test_05_rr_calculated_not_set_fixed(self):
    x=plan()
    derived=(D(x["target"])-D(x["entry"]))/(D(x["entry"])-D(x["stop"]))
    self.assertAlmostEqual(float(derived),x["derived_rr"],places=5)
    self.assertNotIn(x["derived_rr"],(1.5,2.0))
 def test_06_decisions_ignore_future_highs(self):
    prior=plan()
    m=list(B);m[300]=replace(m[300],h=D("120"))
    self.assertEqual(plan(tuple(m)),prior)
 def test_07_future_bar_not_used_to_make_pivot(self):
    p=plan()
    m=list(B);m[25*12]=replace(m[25*12],h=D("125"))
    self.assertEqual(plan(tuple(m)),p)
 def test_08_partial_1h_excluded(self):
    partial=closed_tfs(B,SIG+STEP,3600000)
    self.assertEqual(partial[-1].close_ms,SIG)
 def test_09_partial_15m_excluded(self):
    partial=closed_tfs(B,SIG+STEP,900000)
    self.assertEqual(partial[-1].close_ms,SIG)
 def test_10_pivot_right_bars_confirmed(self):
    candles=closed_tfs(B,SIG,3600000)
    hi=[x for x in confirmed_swings(candles,3600000,2,SIG) if x.kind=="HIGH"]
    self.assertTrue(hi)
    self.assertTrue(all(x.confirmed_ms>x.pivot_closed_ms and x.confirmed_ms<=SIG for x in hi))
 def test_11_unconfirmed_pivot_rejected_from_future_bars(self):
    x=(ClosedBar(START,START+3600000,D(5),D(2),D(3)),
       ClosedBar(START+3600000,START+7200000,D(7),D(1),D(3)))
    with self.assertRaises(C90Rejected):
      confirmed_swings(x,3600000,2,START+3600000)
 def test_12_stop_first_same_bar_with_fta(self):
    p=plan();m=list(B)
    j=25*12
    m[j]=replace(m[j],h=D("112"),l=D("94"))
    a=replay_plan(tuple(m),p,cost_bps=14)
    self.assertEqual(a["exit_reason"],"STRUCTURAL_STOP_PRIORITY_AMBIGUOUS")
    self.assertLess(a["net_r"],0)
 def test_13_structural_fta_exit(self):
    p=plan();m=list(B);j=25*12
    m[j]=replace(m[j],h=D("112"),l=D("99.8"))
    a=replay_plan(tuple(m),p,cost_bps=14)
    self.assertEqual(a["exit_reason"],"STRUCTURAL_FTA")
 def test_14_cost_deducted(self):
    p=plan()
    a=replay_plan(B,p,cost_bps=7);b=replay_plan(B,p,cost_bps=25)
    self.assertGreater(a["net_r"],b["net_r"])
 def test_15_forward_only_exit(self):
    a=replay_plan(B,plan(),cost_bps=14)
    self.assertGreater(a["exit_close_ms"],SIG)
 def test_16_no_fta_rejected_not_fixed_rr(self):
    m=list(B);m[13*12]=replace(m[13*12],h=D("100.2"))
    self.assertEqual(plan(tuple(m))["status"],"NO_UNCONSUMED_1H_FTA")
 def test_17_fta_consumed_then_rejected(self):
    m=list(B);m[23*12]=replace(m[23*12],h=D("110.01"))
    self.assertEqual(plan(tuple(m))["status"],"NO_UNCONSUMED_1H_FTA")
 def test_18_low_rr_reject_never_widen_target(self):
    x=plan(B,{**E,"poi_low":"90","poi_high":"99"})
    self.assertEqual(x["status"],"STRUCTURAL_RR_BELOW_MIN_FILTER" if x["status"]=="STRUCTURAL_RR_BELOW_MIN_FILTER" else "STRUCTURAL_STOP_OUTSIDE_RISK_BOUNDS")
    if x["status"]=="STRUCTURAL_RR_BELOW_MIN_FILTER":
      self.assertLess(x["derived_rr"],1.25)
      self.assertLess(D(x["target"]),D("110"))
 def test_19_no_trade_plan_rejected_by_execution(self):
    with self.assertRaises(C90Rejected):
      replay_plan(B,{"status":"NO_UNCONSUMED_1H_FTA"},cost_bps=14)
 def test_20_false_forged_entry_rejected(self):
    with self.assertRaises(C90Rejected):
      replay_plan(B,{**plan(),"entry":"50"},cost_bps=14)
 def test_21_false_forged_target_side(self):
    with self.assertRaises(C90Rejected):
      replay_plan(B,{**plan(),"target":"90"},cost_bps=14)
 def test_22_unregistered_width(self):
    with self.assertRaises(C90Rejected):plan(width=10)
 def test_23_wrong_route_priority(self):
    with self.assertRaises(C90Rejected):plan(event={**E,"priority":3})
 def test_24_status_trade_ready_rejected(self):
    with self.assertRaises(C90Rejected):plan(event={**E,"readiness":"TRADE_READY"})
 def test_25_source_gaps_rejected(self):
    m=list(B);m[10]=replace(m[10],open_ms=m[10].open_ms+STEP)
    with self.assertRaises(C90Rejected):closed_tfs(tuple(m),SIG,3600000)
 def test_26_wrong_1h_poi_order(self):
    with self.assertRaises(C90Rejected):plan(event={**E,"poi_low":"110","poi_high":"80"})
 def test_27_nan_poi_rejected(self):
    with self.assertRaises(C90Rejected):plan(event={**E,"poi_low":"NaN"})
 def test_28_negative_cost_rejected(self):
    with self.assertRaises(C90Rejected):replay_plan(B,plan(),cost_bps=-1)
 def test_29_serialization_stable(self):
    self.assertEqual(dumps({"x":2,"y":1}),dumps({"y":1,"x":2}))
 def test_30_min_rr_is_filter_not_target(self):
    self.assertEqual(MIN_RR_FILTER,D("1.25"))
    self.assertEqual(PIVOT_WIDTHS,(2,3))
 def test_31_known_close_no_entry_in_same_bar(self):
    x=plan();self.assertEqual(x["signal_ms"],x["entry_open_ms"])
    self.assertEqual(x["signal_ms"],B[25*12-1].close_ms)
 def test_32_pivots_asof_exact(self):
    x=plan();self.assertLessEqual(x["fta_confirmed_ms"],SIG)
    self.assertLessEqual(x["stronghl_confirmed_ms"],SIG)
 def test_33_stronghl_missing_hard_reject(self):
    m=list(B);m[20*12]=replace(m[20*12],l=D("99.8"))
    self.assertEqual(plan(tuple(m))["status"],"NO_CONFIRMED_15M_STRONGHL_PROXY")
 def test_34_no_economic_alpha_claims(self):
    x=plan();self.assertEqual(x["evidence_class"],"ADAPTED_HYPOTHESIS")
 def test_35_no_trade_in_setup(self):
    x=plan();self.assertNotIn("orders",x);self.assertNotIn("fills",x)
 def test_36_frozen_classification_unchanged(self):
    self.assertEqual(STATUS,"ADAPTED_HYPOTHESIS_SOURCE_CONDITIONED_PAPER_ONLY")
if __name__=="__main__":unittest.main()
