"""C97 independent precommitted regime/cost risk filter negative tests.

Synthetic price bars never count as real evidence. Real frozen source unit
cases already verified in C95, original Binance BTC is run via C97 CI.
"""
import unittest
from copy import deepcopy
from decimal import Decimal as D
from pathlib import Path
from c89_original_native5m_adaptation_backtest import Bar,STEP
from c91_continuous_causal_route_a_paper import OHLC,D1
from c97_robustness_regime_cost_gate import (
 C97Rejected,REGIME_RETURN_PCT,COST_SCENARIOS,MIN_ROUTE_TRADES,
 MIN_TRADE_PER_EVAL_BIN,utc,regime_at,_monthly,
 _cost_case,_score,_calendar_fold,BINS,dumps,analyze)
from c95_integrated_paper_three_routes import A_SHA,B_SHA,C_SHA,read_and_pin
ROOT=Path(__file__).resolve().parents[1]
def t(entry=100,stop=98,net=1,clock=0):
 return {"entry":str(entry),"stop":str(stop),"net_r":net,
         "entry_ms":clock,"exit_ms":clock+600000,"symbol":"BTCUSDT","route":"A_FIX"}
def day(i,close=100):
 x=utc("2026-06-01")+i*D1
 return OHLC(x,x+D1,D(100),D(101),D(99),D(close),D(10))
class TestC97(unittest.TestCase):
 def test_01_source_fee14_unchanged(self):
  self.assertEqual(_cost_case(t(),14)["net_r"],1)
 def test_02_25bps_cost_worse(self):
  self.assertLess(_cost_case(t(),25)["net_r"],_cost_case(t(),14)["net_r"])
 def test_03_40bps_cost_worse(self):
  self.assertLess(_cost_case(t(),40)["net_r"],_cost_case(t(),25)["net_r"])
 def test_04_unsupported_cost_rejected(self):
  with self.assertRaises(C97Rejected):_cost_case(t(),10)
 def test_05_unsafe_zero_stop(self):
  with self.assertRaises(C97Rejected):_cost_case(t(stop=100),25)
 def test_06_different_structural_risk_has_correct_cost(self):
  a=_cost_case(t(stop=99),25)
  b=_cost_case(t(stop=95),25)
  self.assertLess(a["net_r"],b["net_r"])
 def test_07_regime_up_strictly_closed(self):
  candles=[day(i,close=100+(5 if i>=7 else 0)) for i in range(9)]
  t0=[x.close_ms for x in candles]
  self.assertEqual(regime_at(candles,t0,t0[7]),"BTC_UP_7D")
 def test_08_regime_future_bar_ignored(self):
  candles=[day(i,close=100+(15 if i==8 else 0)) for i in range(9)]
  ends=[x.close_ms for x in candles]
  self.assertEqual(regime_at(candles,ends,ends[7]),"BTC_RANGE_7D")
 def test_09_regime_down(self):
  c=[day(i,close=100-(5 if i>=7 else 0)) for i in range(9)]
  self.assertEqual(regime_at(c,[x.close_ms for x in c],c[7].close_ms),"BTC_DOWN_7D")
 def test_10_regime_warmup(self):
  c=[day(i) for i in range(7)]
  self.assertEqual(regime_at(c,[x.close_ms for x in c],c[-1].close_ms),"WARMUP_MISSING")
 def test_11_score_empty_not_proof(self):
  self.assertEqual(_score([])["n"],0)
  self.assertIsNone(_score([])["pf"])
 def test_12_score_negative(self):
  s=_score([t(net=-1),t(net=-1)])
  self.assertEqual(s["n"],2);self.assertLess(s["sum_r"],0)
 def test_13_score_partial_win(self):
  s=_score([t(net=2),t(net=-1)])
  self.assertEqual(s["pf"],2)
 def test_14_equal_periods_are_explicit(self):
  self.assertEqual(len(BINS),3)
  self.assertEqual(BINS[0][1],"2026-06-15")
 def test_15_fold_no_future_exit(self):
  x=t(clock=utc("2026-08-01")-300000)
  self.assertEqual(len(_calendar_fold([x],"2026-07-01","2026-08-01")),0)
 def test_16_epoch_month(self):
  self.assertEqual(_monthly(utc("2026-09-18")),"2026-09")
 def test_17_gate_thresholds_nonzero(self):
  self.assertGreaterEqual(MIN_ROUTE_TRADES,30)
  self.assertGreaterEqual(MIN_TRADE_PER_EVAL_BIN,10)
 def test_18_no_optimization_of_rr(self):
  self.assertEqual(COST_SCENARIOS,(14,25,40))
  self.assertEqual(REGIME_RETURN_PCT,D(3))
 def test_19_immutable_json(self):
  self.assertEqual(dumps({"a":1,"b":2}),dumps({"b":2,"a":1}))
 def test_20_real_archives_loaded_with_no_trading_order(self):
  a=read_and_pin(ROOT/"evidence/c92/C92_APR_OCT_5_SYMBOL_FULL_CAUSAL_STRATEGY_REPLAY.json",A_SHA)
  b=read_and_pin(ROOT/"evidence/c94/C94_ORIGINAL_BINANCE_IDM_LIMIT_BOTH_MODELS_PAPER.json",B_SHA)
  c=read_and_pin(ROOT/"evidence/c93/C93_ORIGINAL_NATIVE3M_ROUTE_C_BOS_PAPER_REPLAY.json",C_SHA)
  self.assertEqual((a["all"]["count"],b["all"]["count"],c["all"]["count"]),(34,15,58))
if __name__=="__main__":unittest.main()
