"""C99: synthetic checks for 32-day original-source C route window stability."""
import unittest
from datetime import datetime,timezone
from decimal import Decimal as D
from pathlib import Path
from c21_native3m_source_bridge import Original3mRow,THREE
from c99_native3m_window_depth_stability import (
 C99Rejected,ENDINGS,DAY,WINDOW_DAYS,WARMUP_DAYS,EXIT_EMBARGO,
 OCT3,_window,signature,compare,validate_witness,when,dumps)
def trade(entry=None,symbol="BTCUSDT"):
 if entry is None:entry=when("2026-10-05")
 return {"symbol":symbol,"route":"C_1H_WICK_RAID_NATIVE3M_BOS","side":"SHORT",
  "entry_ms":entry,"exit_ms":entry+THREE,"entry":"100",
  "stop":"102","target":"96","fta":"96",
  "derived_rr":2.0,"net_r":-1.0,"exit_reason":"STOP_FIRST_SAME_3M",
  "raid_fractal_known_ms":entry-3600000,"bos_close_ms":entry,
  "fta_confirmed_ms":entry-3600000}
def rows():
 start=when("2026-09-01")
 return tuple(Original3mRow("BTCUSDT",start+i*THREE,start+(i+1)*THREE,
  D(100),D(101),D(99),D(100),D(1),"a"*64,"a"*64)
  for i in range(56*24*60//3))
class TestC99(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=rows()
 def test_01_all_three_times_pre_registered(self):
  self.assertEqual(ENDINGS,("2026-10-10","2026-10-18","2026-10-27"))
 def test_02_oct_window_exact_32days(self):
  x=_window(self.source,when("2026-10-27"))
  self.assertEqual(len(x),15360)
  self.assertEqual(x[0].start_ms,when("2026-09-25"))
 def test_03_earlier_window_exact_32days(self):
  x=_window(self.source,when("2026-10-10"))
  self.assertEqual(x[0].start_ms,when("2026-09-08"))
 def test_04_source_shorter_rejected(self):
  with self.assertRaises(C99Rejected):
   _window(self.source[:100],when("2026-10-27"))
 def test_05_source_end_incomplete_rejected(self):
  with self.assertRaises(C99Rejected):
   _window(self.source,when("2026-10-28"))
 def test_06_source_misalignment_rejected(self):
  from dataclasses import replace
  x=list(self.source);x[17]=replace(x[17],known_ms=x[17].known_ms+THREE)
  with self.assertRaises(C99Rejected):
   _window(tuple(x),when("2026-10-10"))
 def test_07_matching_preknown_trade_invariant(self):
  a=[trade()]
  b=[trade()]
  r=compare(a,b,when("2026-10-10"),when("2026-10-18"))
  self.assertTrue(r["identical"])
 def test_08_different_structural_sl_rejected(self):
  a=trade();b={**a,"stop":"103"}
  r=compare([a],[b],when("2026-10-18"),when("2026-10-27"))
  self.assertFalse(r["identical"])
  self.assertEqual(r["different_first_only"],1)
 def test_09_different_tp_rejected(self):
  a=trade();b={**a,"target":"94"}
  r=compare([a],[b],when("2026-10-10"),when("2026-10-27"))
  self.assertFalse(r["identical"])
 def test_10_different_netR_rejected(self):
  a=trade();b={**a,"net_r":1.5}
  r=compare([a],[b],when("2026-10-10"),when("2026-10-27"))
  self.assertFalse(r["identical"])
 def test_11_first_window_boundary_trade_excluded(self):
  x=trade(when("2026-10-10")-THREE)
  r=compare([x],[],when("2026-10-10"),when("2026-10-18"))
  self.assertTrue(r["identical"])
  self.assertEqual(r["union_trades"],0)
 def test_12_previous_month_trade_excluded(self):
  x=trade(when("2026-10-02"))
  r=compare([x],[],when("2026-10-10"),when("2026-10-18"))
  self.assertTrue(r["identical"])
 def test_13_duplicate_source_outcome_rejected(self):
  x=trade()
  with self.assertRaises(C99Rejected):
   compare([x,x],[x],when("2026-10-18"),when("2026-10-27"))
 def test_14_no_fake_success_from_zero_samples(self):
  r=compare([],[],when("2026-10-10"),when("2026-10-18"))
  self.assertFalse(r["sufficient_n"])
 def test_15_minimum_warmup_7days(self):
  self.assertEqual(WARMUP_DAYS,7)
  self.assertEqual(EXIT_EMBARGO,12*3600000)
 def test_16_unregistered_boundaries_rejected(self):
  with self.assertRaises(C99Rejected):
   compare([],[],when("2026-10-11"),when("2026-10-27"))
 def test_17_forged_missing_trade_field_rejected(self):
  x=trade();x.pop("stop")
  with self.assertRaises(C99Rejected):signature(x)
 def test_18_real_c98_witness_240_and_native3m_120(self):
  from c95_integrated_paper_three_routes import read_and_pin
  f=Path(__file__).resolve().parents[1]/"evidence/c98/C98_NEW_OCT_SOURCE_ABC_CLOSED_HOLDOUT.json"
  x=read_and_pin(f,"9b95735407465c46b1a2fdb6e4e8875bfdd2c428588f6205bf1212d35c0b9e97")
  self.assertEqual(len(validate_witness(x)),120)
 def test_19_forged_sha_meta_rejected(self):
  from c95_integrated_paper_three_routes import read_and_pin
  f=Path(__file__).resolve().parents[1]/"evidence/c98/C98_NEW_OCT_SOURCE_ABC_CLOSED_HOLDOUT.json"
  x=read_and_pin(f,"9b95735407465c46b1a2fdb6e4e8875bfdd2c428588f6205bf1212d35c0b9e97")
  x["new_archive_count"]=239
  with self.assertRaises(C99Rejected):validate_witness(x)
 def test_20_deterministic_json(self):
  self.assertEqual(dumps({"b":2,"a":1}),dumps({"a":1,"b":2}))
if __name__=="__main__":unittest.main()
