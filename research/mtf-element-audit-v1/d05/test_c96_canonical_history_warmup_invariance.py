"""C96 adversarial warmup and prefix causality tests; fixture bars SYNTHETIC."""
import unittest
from datetime import datetime,timezone
from decimal import Decimal as D
from unittest.mock import patch
from c89_original_native5m_adaptation_backtest import Bar,STEP
from c96_canonical_history_warmup_invariance import (
  C96Rejected,CANONICAL_START,EVAL_START,PREFIX_CUTOFF,MIN_WEEKLY_BARS,
  MIN_CLOSED_DAILY,A_EMBARGO,B_EMBARGO,STATUS,stamp,validate_calendar,
  _complete,_signature,prefix_test,anchor_comparison,dumps,SOURCES)
def bars(start,count):
 return tuple(Bar(start+i*STEP,D(100),D(101),D(99),D(100),D(10)) for i in range(count))
def sample(route="A",entry=EVAL_START+3600000,r=-1):
 return dict(symbol="BTCUSDT",route=route+"_TEST",entry_ms=entry,exit_ms=entry+3*STEP,
             entry="100",stop="98",target="103",fta="103",
             derived_rr=1.5,net_r=r,exit_reason="STOP")
class TestC96(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pre=bars(CANONICAL_START,(PREFIX_CUTOFF-CANONICAL_START)//STEP)
  cls.full=cls.pre+bars(PREFIX_CUTOFF,4)
 def test_01_calendar_anchored_after_warmup(self):
  x=validate_calendar(self.pre,"BTCUSDT",minimum_end=PREFIX_CUTOFF)
  self.assertGreaterEqual(x["min_full_days_at_evaluation"],MIN_CLOSED_DAILY)
  self.assertGreaterEqual(x["min_closed_full_weeks_at_evaluation"],MIN_WEEKLY_BARS)
 def test_02_september_only_rejected(self):
  with self.assertRaisesRegex(C96Rejected,"CANONICAL"):
   validate_calendar(bars(PREFIX_CUTOFF,300),"BTCUSDT",minimum_end=PREFIX_CUTOFF)
 def test_03_future_horizon_required(self):
  with self.assertRaisesRegex(C96Rejected,"HORIZON"):
   validate_calendar(self.pre[:300],"BTCUSDT",minimum_end=PREFIX_CUTOFF)
 def test_04_missing_calendar_bar_rejected(self):
  b=self.pre[:4]+self.pre[5:]
  with self.assertRaisesRegex(C96Rejected,"GAP"):
   validate_calendar(b,"BTCUSDT",minimum_end=PREFIX_CUTOFF)
 def test_05_no_shorter_anchor_variance_bypass(self):
  x=self.pre[288:]
  with self.assertRaises(C96Rejected):
   validate_calendar(x,"BTCUSDT",minimum_end=PREFIX_CUTOFF)
 def test_06_exact_prefix_invariant(self):
  foo={sym:self.full for sym in SOURCES}
  pre={sym:self.pre for sym in SOURCES}
  frozen={sym:{"trades":[]} for sym in SOURCES}
  with patch("c96_canonical_history_warmup_invariance.discover_a",return_value={"trades":[]}):
   result=prefix_test(foo,pre,"A",full_outputs=frozen)
  self.assertTrue(result["all_consistent"])
  self.assertTrue(result["uses_source_pinned_full_results"])
 def test_07_changed_prefix_rejected(self):
  from dataclasses import replace
  bad=list(self.pre);bad[7]=replace(bad[7],h=D(400))
  foo={sym:self.full for sym in SOURCES}
  pre={sym:tuple(bad) if sym=="BTCUSDT" else self.pre for sym in SOURCES}
  with self.assertRaisesRegex(C96Rejected,"SOURCE_BYTES_OR_PREFIX_CHANGED"):
   prefix_test(foo,pre,"A",full_outputs={sym:{"trades":[]} for sym in SOURCES})
 def test_08_comparison_detects_missing_trade(self):
  src={sym:self.full for sym in SOURCES}
  pre={sym:self.pre for sym in SOURCES}
  full_outputs={sym:{"trades":[sample()] if sym=="BTCUSDT" else []} for sym in SOURCES}
  with patch("c96_canonical_history_warmup_invariance.discover_a",return_value={"trades":[]}):
   x=prefix_test(src,pre,"A",full_outputs=full_outputs)
  self.assertFalse(x["all_consistent"])
  self.assertFalse(x["by_symbol"]["BTCUSDT"]["consistent"])
 def test_09_mature_only_no_boundary_forgery(self):
  ts=PREFIX_CUTOFF-A_EMBARGO+STEP
  self.assertEqual(_complete([sample(entry=ts)],PREFIX_CUTOFF,A_EMBARGO),[])
 def test_10_mature_trade_retained(self):
  t=sample()
  self.assertEqual(len(_complete([t],PREFIX_CUTOFF,A_EMBARGO)),1)
 def test_11_exposure_embargo_B_includes_limit_ttl(self):
  self.assertGreater(B_EMBARGO,A_EMBARGO)
 def test_12_no_rr_target_in_c96(self):
  self.assertEqual(STATUS,"RESEARCH_ONLY_WARMUP_CONTRACT")
 def test_13_filename_manifest_no_partial_pass(self):
  with self.assertRaises(C96Rejected):
   validate_calendar("not-source","BTCUSDT")
 def test_14_april_anchor_warmup_contract(self):
  self.assertEqual(CANONICAL_START,stamp(2026,4,1))
  self.assertEqual(EVAL_START,stamp(2026,6,15))
 def test_15_calendar_diff_without_suffix_does_not_create_pnl(self):
  x=anchor_comparison({sym:self.full for sym in SOURCES},
    {sym:bars(PREFIX_CUTOFF,300) for sym in SOURCES})
  self.assertEqual(len(x["five_rejected"]),5)
 def test_16_same_signature_no_hash_drift(self):
  self.assertEqual(_signature(sample()),_signature(dict(reversed(list(sample().items())))))
 def test_17_json_canonical(self):
  self.assertEqual(dumps({"x":1,"y":2}),dumps({"y":2,"x":1}))
 def test_18_negative_bias_paper_only(self):
  x=sample();self.assertEqual(x["net_r"],-1)
if __name__=="__main__":unittest.main()
