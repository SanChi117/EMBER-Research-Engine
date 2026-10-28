"""C91 continuous discovery: synthetic unit fixtures are NOT real Binance cases."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c89_original_native5m_adaptation_backtest import Bar,STEP
from c91_continuous_causal_route_a_paper import (
 C91Rejected,HOUR,H4,D1,WEEK,WEEK_ANCHOR,ROUTES,EVIDENCE,
 _aggregate,_fvg,_raid,_vc,_weekly_daily_context,_simulate,
 _metrics,discover_symbol,analyze,dumps,OHLC,SPLIT)

START=1788220800000  # 2026-09-01 UTC fully aligned
def bars(n=750):
 return tuple(Bar(START+i*STEP,D("100"),D("101"),D("99"),D("100"),D("10")) for i in range(n))
B=bars()
def h(start,op=100,high=101,low=99,close=100,tf=HOUR):
 return OHLC(start,start+tf,D(op),D(high),D(low),D(close),D(10))
def p(side="LONG"):
 return {"stop":D("98") if side=="LONG" else D("102"),
 "target":D("104") if side=="LONG" else D("96"),"fta":D("104") if side=="LONG" else D("96"),"fta_tf":"1h"}
class TestC91(unittest.TestCase):
 def test_01_continuous_15m_closed(self):
  q=_aggregate(B,3*STEP)
  self.assertEqual(len(q),250)
  self.assertEqual(q[0].close_ms,START+3*STEP)
 def test_02_continuous_1h_closed(self):
  q=_aggregate(B,HOUR)
  self.assertEqual(len(q),62)
  self.assertEqual(q[-1].close_ms,START+62*HOUR)
 def test_03_continuous_4h_closed(self):
  q=_aggregate(B,H4);self.assertEqual(len(q),15)
 def test_04_daily_only_completed(self):
  q=_aggregate(B,D1);self.assertEqual(len(q),2)
 def test_05_incomplete_week_not_classified(self):
  self.assertEqual(_aggregate(B,WEEK,WEEK_ANCHOR),())
 def test_06_up_fvg_strict_three(self):
  a=h(START,high=100,low=98)
  c=h(START+2*HOUR,high=107,low=105)
  self.assertEqual(_fvg((a,h(START+HOUR),c)),("LONG",D(100),D(105)))
 def test_07_down_fvg_strict_three(self):
  a=h(START,high=110,low=108)
  c=h(START+2*HOUR,high=104,low=103)
  self.assertEqual(_fvg((a,h(START+HOUR),c)),("SHORT",D(104),D(108)))
 def test_08_no_fvg_on_overlap(self):
  a=h(START);c=h(START+2*HOUR)
  self.assertIsNone(_fvg((a,h(START+HOUR),c)))
 def test_09_future_fvg_gapped_reject(self):
  with self.assertRaises(C91Rejected):_fvg((h(START),h(START+HOUR),h(START+4*HOUR)))
 def test_10_sweep_long_reaction(self):
  q=[h(START+i*HOUR) for i in range(4)]
  q.append(h(START+4*HOUR,op=99,high=102,low=98,close=101))
  self.assertTrue(_raid(tuple(q),"LONG"))
 def test_11_sweep_short_reaction(self):
  q=[h(START+i*HOUR) for i in range(4)]
  q.append(h(START+4*HOUR,op=101,high=102,low=98,close=99))
  self.assertTrue(_raid(tuple(q),"SHORT"))
 def test_12_sweep_without_rejection_is_false(self):
  q=[h(START+i*HOUR) for i in range(4)]
  q.append(h(START+4*HOUR,op=98,high=100,low=97,close=98))
  self.assertFalse(_raid(tuple(q),"LONG"))
 def test_13_vc_snr_long(self):
  x=[h(START+i*HOUR) for i in range(3)]
  x.append(h(START+3*HOUR,op=100,high=105,low=99,close=104))
  self.assertEqual(_vc(tuple(x),"LONG"),"SNR")
 def test_14_vc_snr_short(self):
  x=[h(START+i*HOUR) for i in range(3)]
  x.append(h(START+3*HOUR,op=100,high=101,low=95,close=96))
  self.assertEqual(_vc(tuple(x),"SHORT"),"SNR")
 def test_15_vc_does_not_accept_direction_mismatch(self):
  x=[h(START+i*HOUR) for i in range(3)]
  x.append(h(START+3*HOUR,op=100,high=105,low=99,close=104))
  self.assertEqual(_vc(tuple(x),"SHORT"),"")
 def test_16_context_no_week_false(self):
  d=[h(START+i*D1,tf=D1) for i in range(3)]
  self.assertFalse(_weekly_daily_context(d,(),"LONG",START+3*D1))
 def test_17_context_no_future(self):
  d=[h(START,tf=D1),h(START+D1,close=110,tf=D1)]
  w=[h(START,close=110,tf=WEEK)]
  self.assertFalse(_weekly_daily_context(d,w,"LONG",START+D1))
 def test_18_long_simulation_target_from_structure(self):
  x=list(B);x[30]=replace(x[30],h=D(105),l=D(99))
  t,reason=_simulate(tuple(x),30,"LONG",p(),14)
  self.assertEqual(reason,"OK");self.assertEqual(t["target"],"104")
  self.assertEqual(t["exit_reason"],"STRUCTURAL_FTA")
 def test_19_stop_priority(self):
  x=list(B);x[30]=replace(x[30],h=D(105),l=D(97))
  t,_=_simulate(tuple(x),30,"LONG",p(),14)
  self.assertEqual(t["exit_reason"],"STOP_FIRST_AMBIGUOUS")
 def test_20_net_fee_cost(self):
  t,_=_simulate(B,30,"LONG",p(),14)
  self.assertLess(t["net_r"],t["derived_rr"])
 def test_21_target_not_derived_from_rr(self):
  t,_=_simulate(B,30,"LONG",p(),14)
  self.assertEqual(t["target"],"104");self.assertNotEqual(t["derived_rr"],1.5)
 def test_22_broken_entry_gap_reject(self):
  x=list(B);x[30]=replace(x[30],o=D(106),h=D(107),l=D(105),c=D(106))
  v,reason=_simulate(tuple(x),30,"LONG",p(),14)
  self.assertIsNone(v);self.assertEqual(reason,"GAP_DESTROYS_STRUCTURAL_PLAN")
 def test_23_cost_invalid(self):
  with self.assertRaises(C91Rejected):_simulate(B,30,"LONG",p(),8)
 def test_24_min_rr_filters_not_expands_target(self):
  t,why=_simulate(B,30,"LONG",{**p(),"target":D("101")},14)
  self.assertIsNone(t);self.assertEqual(why,"DERIVED_RR_FILTER")
 def test_25_no_c73_case_selection(self):
  r=discover_symbol(B,"BTCUSDT")
  self.assertEqual(r["trades"],[])
  self.assertEqual(r["native5m_bars"],750)
 def test_26_reject_cross_market(self):
  with self.assertRaises(C91Rejected):discover_symbol(B,"FAKEUSDT")
 def test_27_reject_native5m_gap(self):
  x=list(B);x[10]=replace(x[10],open_ms=x[10].open_ms+STEP)
  with self.assertRaises(C91Rejected):discover_symbol(tuple(x),"BTCUSDT")
 def test_28_short_plan_cost(self):
  x,_=_simulate(B,30,"SHORT",p("SHORT"),14)
  self.assertEqual(x["target"],"96")
 def test_29_global_stats_do_not_claim_roi(self):
  r=_metrics([])
  self.assertIsNone(r["win_rate_pct"]);self.assertEqual(r["count"],0)
 def test_30_symmetric_event_route_isolation(self):
  self.assertEqual(len(ROUTES),3)
  self.assertTrue(all(x.startswith("A_") for x in ROUTES))
 def test_31_no_author_certification(self):
  self.assertEqual(EVIDENCE,"ADAPTED_HYPOTHESIS")
 def test_32_context_causal_week(self):
  d=[h(START,tf=D1),h(START+D1,close=110,tf=D1)]
  w=[h(START,close=110,tf=WEEK)]
  self.assertTrue(_weekly_daily_context(d,w,"LONG",START+7*D1))
 def test_33_json_deterministic(self):
  self.assertEqual(dumps({"x":1,"y":2}),dumps({"y":2,"x":1}))
 def test_34_incomplete_candles_not_counted(self):
  q=_aggregate(B[:11],HOUR);self.assertEqual(len(q),0)
 def test_35_5m_backward_entry_excluded(self):
  x=list(B)
  x[29]=replace(x[29],h=D(105))
  t,_=_simulate(tuple(x),30,"LONG",p(),14)
  self.assertNotEqual(t["exit_ms"],x[29].close_ms)
 def test_36_zero_lookahead_calendar_split(self):
  self.assertEqual(SPLIT,1789862400000)
 def test_37_aggregate_input_must_be_native(self):
  with self.assertRaises(C91Rejected):_aggregate(tuple(),HOUR+1)
 def test_38_no_pnl_trades_from_causal_sparse_source(self):
  s={k:B for k in ("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT")}
  x=analyze(s,[{"symbol":k} for k in range(15)])
  self.assertEqual(x["source_bars"],3750)
  self.assertFalse(x["fixed_rr_targets"])
  self.assertEqual(x["all"]["count"],0)
if __name__=="__main__":unittest.main()
