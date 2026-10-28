"""C89 hypothetical event-conditioned Binance 5m backtest negative tests.

Synthetic 5m unit fixtures explicitly NOT historical Binance evidence.
"""
import unittest,json
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
from c89_original_native5m_adaptation_backtest import (
 Bar,C89Rejected,STEP,parse_original5m_csv,read_exact_archive,
 _scenario_one,_safe_http,load_original_native5m,SPLIT,MAKER,
 RR_VALUES,COST_BPS)
ROOT=Path(__file__).resolve().parents[1]
C73=(ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json").read_bytes()

def base_bars(n=170,base=100):
    return tuple(Bar(1788000000000+i*STEP,D(base),D(base+0.2),D(base-0.2),
                     D(base),D(10)) for i in range(n))
B=base_bars()
EVENT={"case_key":"BTCUSDT/TEST_CASE_SYNTHETIC","priority":0,
       "symbol":"BTCUSDT","side":"LONG","first5m_known_ms":B[20].open_ms,
       "poi_low":"98","poi_high":"99","readiness":"NOT_TRADE_READY"}
def fake_outcome(bars,**args):
    return _scenario_one(bars,{**EVENT,**args},rr=1.5,cost_bps=14)

class TestC89(unittest.TestCase):
 def test_01_closed_forward_next_bar(self):
    b=list(B);b[20]=replace(b[20],h=D(103.5),c=D(103))
    t=fake_outcome(tuple(b))
    self.assertEqual(t["entry_open_ms"],EVENT["first5m_known_ms"])
 def test_02_exit_rule_on_next_bar(self):
    b=list(B);b[20]=replace(b[20],h=D(104),c=D(103))
    t=fake_outcome(tuple(b))
    self.assertEqual(t["exit_reason"],"TP")
 def test_03_pre_signal_bar_does_not_trigger(self):
    b=list(B);b[19]=replace(b[19],h=D(130),l=D(50),c=D(100))
    t=fake_outcome(tuple(b))
    self.assertEqual(t["exit_reason"],"TIME_LIMIT")
 def test_04_stop_first_both_touch(self):
    b=list(B);b[20]=replace(b[20],h=D(105),l=D(96),c=D(102))
    t=fake_outcome(tuple(b))
    self.assertEqual(t["exit_reason"],"STOP_PRIORITY_IF_SAME_BAR")
    self.assertLess(t["net_r"],0)
 def test_05_long_stop_open_gap(self):
    b=list(B);b[20]=replace(b[20],o=D(96),h=D(97),l=D(95),c=D(96))
    # entry at 96, stop anchored below 96; no artificial existing stop fill
    t=fake_outcome(tuple(b),poi_low="94",poi_high="95");self.assertEqual(t["entry"],"96")
 def test_06_costs_reduce_net_result(self):
    a=_scenario_one(B,EVENT,rr=1.5,cost_bps=7)
    b=_scenario_one(B,EVENT,rr=1.5,cost_bps=25)
    self.assertGreater(a["net_r"],b["net_r"])
 def test_07_fee_zero_equals_gross(self):
    t=_scenario_one(B,EVENT,rr=1.5,cost_bps=0)
    self.assertAlmostEqual(t["net_r"],t["gross_r"])
 def test_08_short_scenario(self):
    t=fake_outcome(B,side="SHORT",poi_low="101",poi_high="102")
    self.assertEqual(t["side"],"SHORT")
 def test_09_wrong_side(self):
    with self.assertRaises(C89Rejected):fake_outcome(B,side="SIDEWAYS")
 def test_10_inverse_zone(self):
    with self.assertRaises(C89Rejected):fake_outcome(B,poi_low="101",poi_high="99")
 def test_11_missing_next_bar(self):
    x=fake_outcome(B,first5m_known_ms=B[-1].close_ms)
    self.assertEqual(x["status"],"NO_NEXT_BAR_NO_TRADE")
 def test_12_unavailable_warmup(self):
    x=fake_outcome(B,first5m_known_ms=B[8].open_ms)
    self.assertEqual(x["status"],"ATR_WARMUP_UNAVAILABLE")
 def test_13_wrong_close_alignment(self):
    with self.assertRaises(C89Rejected):fake_outcome(B,first5m_known_ms=B[20].open_ms+1)
 def test_14_wrong_priority(self):
    with self.assertRaises(C89Rejected):fake_outcome(B,priority=2)
 def test_15_live_status_rejected(self):
    with self.assertRaises(C89Rejected):fake_outcome(B,readiness="TRADE_READY")
 def test_16_negative_rr(self):
    with self.assertRaises(C89Rejected):_scenario_one(B,EVENT,rr=0.5,cost_bps=14)
 def test_17_negative_cost(self):
    with self.assertRaises(C89Rejected):_scenario_one(B,EVENT,rr=2.0,cost_bps=-1)
 def test_18_nontuple_bar_input(self):
    with self.assertRaises(C89Rejected):_scenario_one(list(B),EVENT,rr=1.5,cost_bps=14)
 def test_19_nan_zone(self):
    with self.assertRaises(C89Rejected):fake_outcome(B,poi_low="NaN")
 def test_20_risk_far_reject(self):
    x=fake_outcome(B,poi_low="40",poi_high="99")
    self.assertEqual(x["status"],"STOP_OUTSIDE_PREDECLARED_BOUNDS")
 def test_21_gap_inside_forward_chain(self):
    b=list(B);b[25]=replace(b[25],open_ms=b[25].open_ms+STEP)
    with self.assertRaises(C89Rejected):fake_outcome(tuple(b))
 def test_22_parser_consecutive(self):
    raw=(f"{B[0].open_ms},100,102,99,101,10\n{B[1].open_ms},101,103,100,102,11\n").encode()
    q=parse_original5m_csv(raw,"BTCUSDT")
    self.assertEqual(len(q),2)
 def test_23_parser_duplicate_reject(self):
    raw=(f"{B[0].open_ms},100,102,99,101,10\n{B[0].open_ms},101,103,100,102,11\n").encode()
    with self.assertRaises(C89Rejected):parse_original5m_csv(raw,"BTCUSDT")
 def test_24_parser_gap_reject(self):
    raw=(f"{B[0].open_ms},100,102,99,101,10\n{B[2].open_ms},101,103,100,102,11\n").encode()
    with self.assertRaises(C89Rejected):parse_original5m_csv(raw,"BTCUSDT")
 def test_25_parser_negative_volume(self):
    raw=f"{B[0].open_ms},100,102,99,101,-1\n".encode()
    with self.assertRaises(C89Rejected):parse_original5m_csv(raw,"BTCUSDT")
 def test_26_parser_nonfinite(self):
    raw=f"{B[0].open_ms},100,NaN,99,101,10\n".encode()
    with self.assertRaises(C89Rejected):parse_original5m_csv(raw,"BTCUSDT")
 def test_27_parser_impossible(self):
    raw=f"{B[0].open_ms},100,102,99,104,10\n".encode()
    with self.assertRaises(C89Rejected):parse_original5m_csv(raw,"BTCUSDT")
 def test_28_parser_wrong_market(self):
    with self.assertRaises(C89Rejected):parse_original5m_csv(b"x","FAKEUSDT")
 def test_29_no_url_injection(self):
    with self.assertRaises(C89Rejected):_safe_http("https://evil.example/steal")
 def test_30_frozen_c73_tamper(self):
    with self.assertRaises(C89Rejected):load_original_native5m(C73+b"x",fetch=lambda x:b"abc")
 def test_31_bogus_zip_sha_rejected(self):
    z={"zip_sha256":"0"*64,"raw_csv_sha256":"0"*64,"url":"x","native5m_bars":1}
    with self.assertRaises(C89Rejected):read_exact_archive(b"bad","BTCUSDT",z)
 def test_32_predeclared_grid_and_split(self):
    self.assertEqual(COST_BPS,(7,14,25))
    self.assertEqual(RR_VALUES,(1.5,2.0))
    self.assertEqual(SPLIT,1789862400000)
if __name__=="__main__":unittest.main()
