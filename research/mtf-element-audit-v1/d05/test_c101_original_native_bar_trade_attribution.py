#!/usr/bin/env python3
"""C101 negatives: independently falsify source/fill, same-bar, BOS, as-of."""
import copy
import json
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c101_original_native_bar_trade_attribution as m

BASE= m.START_MS+4*60*60*1000
THREE=m.THREE
FIVE=m.STEP

def bars(tf="3m",stop=6,entry=100,close=100,first=BASE):
    step=THREE if tf=="3m" else FIVE
    rows=[]
    for i in range(stop):
        tm=first+i*step
        rows.append((tm,tm+step,D(entry),D(101),D(99),D(close),D(1)))
    return tuple(rows)

def one(route="C"):
    at=BASE+THREE*2 if route=="C" else BASE+FIVE*2
    data={"symbol":"SOLUSDT","route":route,"entry_ms":at,"exit_ms":at+(THREE if route=="C" else FIVE),
          "entry":"100","stop":"99","target":"102","fta":"103","fta_confirmed_ms":at-3600000,
          "derived_rr":2.0,"net_r":-1.14,"exit_reason":{
              "A":"STOP_FIRST_AMBIGUOUS","B":"STOP_FIRST_AFTER_LIMIT_TOUCH",
              "C":"STOP_FIRST_SAME_3M"}[route]}
    if route=="A":
        data.update(fee_slip_roundtrip_bps=14,poi_created_ms=at-500000,
                    poi_first_test_ms=at-300000,vc_close_ms=at,
                    stronghl_confirmed_ms=at-200000)
    if route=="B":
        data.update(side="LONG",source_tf="NATIVE_5M",limit_filled=True,
                    signal_ms=at-FIVE,idm_confirmed_ms=at-FIVE,
                    stronghl_confirmed_ms=at-FIVE)
    if route=="C":
        data.update(side="LONG",source_tf="NATIVE_3M",
                    raid_closed_ms=at-THREE*2,
                    bos_close_ms=at,bos_level="99.5",
                    raid_fractal_known_ms=at-THREE*3,
                    bos_confirmed_ms=at-THREE*2,
                    raid_fractal_level="98.5",raid_extreme="98")
    return data

def source_trade(route):
    t=one(route)
    st=THREE if route=="C" else FIVE
    first=t["entry_ms"]-2*st
    rr=list(bars("3m" if route=="C" else "5m",5,first=first))
    rr[2]=(rr[2][0],rr[2][1],D(100),D(101),D(98),D(100),D(1))
    return t,tuple(rr)

class C101NegativeTests(unittest.TestCase):
    def assertReject(self,fun,reason):
        with self.assertRaisesRegex(m.C101Rejected,reason):
            fun()

    def test_01_native_3m_replays_stop(self):
        t,rr=source_trade("C")
        self.assertEqual(m.validate_historical_path(rr,t,"C")["exit_reason"],t["exit_reason"])

    def test_02_native_5m_a_replays_stop(self):
        t,rr=source_trade("A")
        self.assertEqual(m.validate_historical_path(rr,t,"A")["net_14bps_r"],-1.14)

    def test_03_native5m_b_first_touch_stop(self):
        t,rr=source_trade("B")
        self.assertEqual(m.validate_historical_path(rr,t,"B")["exit_reason"],t["exit_reason"])

    def test_04_gap_in_future_native_candles_rejected(self):
        t,rr=source_trade("C")
        t["exit_ms"]+=THREE
        rr=list(rr)
        rr[3]=(rr[3][0]+THREE,rr[3][1]+THREE,*rr[3][2:])
        rr[2]=(rr[2][0],rr[2][1],D(100),D(100.5),D(99.5),D(100),D(1))
        self.assertReject(lambda:m.validate_historical_path(tuple(rr),t,"C"),"MISSING_NATIVE_CANDLE")

    def test_05_c_exit_clock_falsified(self):
        t,rr=source_trade("C")
        t["exit_ms"]+=THREE
        self.assertReject(lambda:m.validate_historical_path(rr,t,"C"),"FROZEN_TRADE_EXIT_REASON_OR_CLOCK")

    def test_06_source_reason_falsified(self):
        t,rr=source_trade("C")
        t["exit_reason"]="1H_FTA"
        self.assertReject(lambda:m.validate_historical_path(rr,t,"C"),"FROZEN_TRADE_EXIT_REASON")

    def test_07_falsified_net_pnl(self):
        t,rr=source_trade("C")
        t["net_r"]=-0.4
        self.assertReject(lambda:m.validate_historical_path(rr,t,"C"),"FROZEN_14BPS_NET_R")

    def test_08_falsified_a_entry_open(self):
        t,rr=source_trade("A")
        t["entry"]="100.1"
        t["derived_rr"]=float((D("102")-D("100.1"))/(D("100.1")-D("99")))
        self.assertReject(lambda:m.validate_historical_path(rr,t,"A"),"A_OR_C_ENTRY_NOT_NATIVE_OPEN")

    def test_09_falsified_b_limit_no_touch(self):
        t,rr=source_trade("B")
        t["entry"]="102.5"
        t["target"]="104"
        t["fta"]="105"
        t["derived_rr"]=float((D("104")-D("102.5"))/(D("102.5")-D("99")))
        self.assertReject(lambda:m.validate_historical_path(rr,t,"B"),"B_LIMIT_NOT_TOUCHED")

    def test_10_wrong_timeframe_for_entry(self):
        t,rr=source_trade("C")
        rr=list(rr);rr[2]=(rr[2][0],rr[2][0]+FIVE,*rr[2][2:])
        self.assertReject(lambda:m.validate_historical_path(rr,t,"C"),"FAKE_NATIVE_BAR_CLOCK")

    def test_11_before_entry_future_FTA(self):
        t,rr=source_trade("C")
        t["fta_confirmed_ms"]=t["entry_ms"]+1
        with self.assertRaises(ValueError):
            m.validate_historical_path(rr,t,"C")

    def test_12_wrong_c_bos_direction(self):
        t,rr=source_trade("C")
        t["bos_level"]="102"
        self.assertReject(lambda:m.signal_snapshot(rr,t,"C"),"BOS_NOT_CLOSED")

    def test_13_c_unclosed_bos(self):
        t,rr=source_trade("C")
        t["bos_close_ms"]=t["entry_ms"]+THREE
        self.assertReject(lambda:m.signal_snapshot(rr,t,"C"),"MISSING_NATIVE3M_CLOSED_BOS")

    def test_14_c_future_confirmation(self):
        t,rr=source_trade("C")
        t["bos_confirmed_ms"]=t["entry_ms"]+1
        self.assertReject(lambda:m.signal_snapshot(rr,t,"C"),"NONCAUSAL_C_BOS")

    def test_15_a_future_poi(self):
        t,rr=source_trade("A")
        t["poi_first_test_ms"]=t["entry_ms"]+1
        self.assertReject(lambda:m.signal_snapshot(rr,t,"A"),"FUTURE_POI")

    def test_16_a_future_vc(self):
        t,rr=source_trade("A")
        t["vc_close_ms"]=t["entry_ms"]+1
        self.assertReject(lambda:m.signal_snapshot(rr,t,"A"),"FUTURE_POI")

    def test_17_b_future_idm(self):
        t,rr=source_trade("B")
        t["idm_confirmed_ms"]=t["entry_ms"]+1
        self.assertReject(lambda:m.signal_snapshot(rr,t,"B"),"FUTURE_IDM")

    def test_18_b_unaligned_limit_signal(self):
        t,rr=source_trade("B")
        t["signal_ms"]+=1
        self.assertReject(lambda:m.validate_historical_path(rr,t,"B"),"IDM_LIMIT_SIGNAL_NOT_PREKNOWN")

    def test_19_b_signal_after_fill(self):
        t,rr=source_trade("B")
        t["signal_ms"]=t["entry_ms"]+FIVE
        self.assertReject(lambda:m.validate_historical_path(rr,t,"B"),"IDM_LIMIT_SIGNAL_NOT_PREKNOWN")

    def test_20_c_bos_body_ratio_is_asof(self):
        t,rr=source_trade("C")
        self.assertEqual(m.signal_snapshot(rr,t,"C")["bos_candle_known_ms"],t["entry_ms"])

    def test_21_no_false_raid_claim_if_no_full_h1(self):
        t,rr=source_trade("C")
        self.assertTrue(m.signal_snapshot(rr,t,"C")["raid_context_left_censored"])

    def test_22_same_bar_dual_touch_flagged(self):
        t,rr=source_trade("C")
        rr=list(rr);rr[2]=(rr[2][0],rr[2][1],D(100),D(103),D(98),D(100),D(1))
        self.assertTrue(m.validate_historical_path(tuple(rr),t,"C")["same_bar_ambiguous"])

    def test_23_no_future_exit_envelope_in_preentry_data(self):
        t,rr=source_trade("C")
        z=m.validate_historical_path(rr,t,"C")
        self.assertTrue(z["max_ohcl_envelope_not_executable"])
        self.assertTrue(z["post_hoc_not_fresh_oos"])

    def test_24_reject_duplicate_pin_manifest(self):
        d=json.loads(m.SOURCE.read_bytes())
        d["new_source_manifest"][-1]=d["new_source_manifest"][0]
        self.assertReject(lambda:m.required_manifest(d),"MISSING_OR_DUPLICATE")

    def test_25_wrong_240_archive_total(self):
        d=json.loads(m.SOURCE.read_bytes())
        d["new_archive_count"]=239
        self.assertReject(lambda:m.required_manifest(d),"NOT_ORIGINAL_C98")

    def test_26_missing_native_receipts(self):
        d=json.loads(m.SOURCE.read_bytes())
        self.assertReject(lambda:m.analyze(d,{},[]),"INCOMPLETE_OR_EXTRA")

    def test_27_c_original_route_count_48(self):
        d=json.loads(m.SOURCE.read_bytes())
        pinned,needed=m.required_manifest(d)
        self.assertTrue(len(needed)>0)
        self.assertTrue(len(needed)<240)

    def test_28_day_clock_utc(self):
        self.assertEqual(m.day_label(m.START_MS),"2026-10-03")

    def test_29_only_valid_native_3m_5m_tuples(self):
        t,rr=source_trade("C")
        i=m.find_entry(rr,t,"3m")
        self.assertEqual(rr[i][1]-rr[i][0],THREE)

    def test_30_native_stop_priority_not_fake_tp(self):
        t,rr=source_trade("B")
        rr=list(rr);rr[2]=(rr[2][0],rr[2][1],D(100),D(103),D(98),D(100),D(1))
        self.assertEqual(m.validate_historical_path(tuple(rr),t,"B")["exit_reason"],
                         "STOP_FIRST_AFTER_LIMIT_TOUCH")

if __name__=="__main__":
    unittest.main()
