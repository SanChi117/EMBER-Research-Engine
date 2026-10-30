"""C106: independent negative tests on source-inspired structural ideas.
Does NOT run the LuxAlgo Pine or claim TradingView-equivalent signal parity.
"""
import sys,json,hashlib,unittest
from pathlib import Path
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c106_structure_event_provenance as m
import c105_parent4h_native3m_research as c105

HERE=Path(__file__).resolve().parent
BASEROOT=HERE.parent
TF=m.H4
def c(i,o,h,l,cl,tf=TF):
    return m.Candle(i*tf,(i+1)*tf,D(str(o)),D(str(h)),D(str(l)),D(str(cl)))
def core():
    return (c(0,10,11,9,10),c(1,12,13,10,12),c(2,14,15,11,14),
            c(3,12,14,10,12),c(4,10,12,9,10))
def high_event():
    return m.confirmed_swings(core(),TF,5*TF)[0]
def pair():
    return (c(5,14,15,12,14),c(6,14,16,13,"15.1"))
class GuardrailTests(unittest.TestCase):
    def bad(self,call,err):
        with self.assertRaisesRegex(m.TemporalStructureError,err):call()
    def test_01_4h_timeframe_frozen(self):
        self.assertEqual((m.M15,m.H1,m.H4),(900000,3600000,14400000))
    def test_02_original_4h_pivot_only_after_right_two_close(self):
        s=high_event()
        self.assertEqual((s.pivot_bar_closed_ms,s.confirmed_at_ms,s.available_at_ms),
                         (3*TF,5*TF,5*TF))
    def test_03_first_four_bars_no_pivot_confirmed(self):
        self.assertEqual(m.confirmed_swings(core()[:4],TF,4*TF),())
    def test_04_closed_fifth_bar_confirms_one_high(self):
        self.assertEqual([(x.kind,str(x.level)) for x in m.confirmed_swings(core(),TF,5*TF)],
            [("HIGH","15")])
    def test_05_swing_pivot_cannot_be_backdated_to_price_bar(self):
        self.assertGreater(high_event().available_at_ms,high_event().pivot_bar_closed_ms)
    def test_06_unclosed_last_h4_is_not_fully_formed(self):
        self.bad(lambda:m.confirmed_swings(core(),TF,4*TF),"PARTIAL_UNCLOSED")
    def test_07_gap_in_h4_native_clock_disallowed(self):
        x=(core()[0],core()[2])
        self.bad(lambda:m.confirmed_swings(x,TF,5*TF),"CANDLE_CLOCK_GAP")
    def test_08_wrong_candle_geometry_disallowed(self):
        a=c(0,100,101,102,100)
        self.bad(lambda:m.checked((a,),TF,TF),"INVALID_ORIGINAL")
    def test_09_nonfinite_fails_closed_candle(self):
        a=m.Candle(0,TF,D("100"),D("NaN"),D("99"),D("100"))
        self.bad(lambda:m.checked((a,),TF,TF),"ONLY_FINITE")
    def test_10_wrong_tf_disallowed(self):
        self.bad(lambda:m.checked(core(),5*60000,10*TF),"UNREGISTERED")
    def test_11_fvg_requires_complete_three_candles(self):
        a=c(0,10,11,8,10);b=c(1,11,12,9,11);z=c(2,14,15,13,14)
        g=m.gap_from_three((a,b,z),TF,3*TF)
        self.assertEqual((g.side,str(g.low),str(g.high),g.available_at_ms),
                         ("LONG","11","13",3*TF))
    def test_12_fvg_does_not_exist_before_third_candle_close(self):
        a=c(0,10,11,8,10);b=c(1,11,12,9,11);z=c(2,14,15,13,14)
        self.bad(lambda:m.gap_from_three((a,b,z),TF,2*TF),"PARTIAL_UNCLOSED")
    def test_13_no_three_candle_gap_returns_none(self):
        self.assertIsNone(m.gap_from_three(core()[:3],TF,3*TF))
    def test_14_bearish_fvg_gap_is_structural(self):
        a=c(0,14,16,13,14);b=c(1,13,15,12,13);z=c(2,9,11,8,9)
        g=m.gap_from_three((a,b,z),TF,3*TF)
        self.assertEqual((g.side,str(g.low),str(g.high)),("SHORT","11","13"))
    def test_15_internal_and_external_events_keep_tf_identity(self):
        z=m.StructureEvent(m.M15,"HIGH","BEARISH",D(15),0,m.M15,m.M15)
        self.assertEqual(z.tf_ms,m.M15)
        self.assertNotEqual(z.tf_ms,TF)
    def test_16_previous_downtrend_high_break_is_choch(self):
        z=m.classify_completed_break(high_event(),*pair(),-1,7*TF)
        self.assertEqual((z.kind,z.side,z.crossed_at_ms),("CHoCH","BULLISH",7*TF))
    def test_17_previous_uptrend_high_break_is_bos(self):
        z=m.classify_completed_break(high_event(),*pair(),1,7*TF)
        self.assertEqual((z.kind,z.side),("BOS","BULLISH"))
    def test_18_previous_unknown_bias_high_break_is_bos(self):
        z=m.classify_completed_break(high_event(),*pair(),0,7*TF)
        self.assertEqual(z.kind,"BOS")
    def test_19_no_candle_close_break_no_bos(self):
        previous=c(5,14,15,12,14)
        current=c(6,14,15,12,14)
        self.assertIsNone(m.classify_completed_break(high_event(),previous,current,-1,7*TF))
    def test_20_future_break_bar_rejected(self):
        self.bad(lambda:m.classify_completed_break(high_event(),*pair(),-1,6*TF),
                 "PARTIAL_UNCLOSED")
    def test_21_pivot_confirmed_during_break_bar_must_not_count(self):
        prev,current=pair()
        future=m.StructureEvent(TF,"HIGH","BEARISH",D("15"),
                                2*TF,7*TF,7*TF)
        self.bad(lambda:m.classify_completed_break(future,prev,current,-1,7*TF),
                 "LEVEL_NOT_KNOWN")
    def test_22_wrong_prior_bias_rejected(self):
        self.bad(lambda:m.classify_completed_break(high_event(),*pair(),3,7*TF),
                 "CONFIRMED_PIVOT")
    def test_23_prior_bullish_bias_low_break_is_choch(self):
        lo=m.StructureEvent(TF,"LOW","BULLISH",D("9"),2*TF,5*TF,5*TF)
        prev=c(5,10,11,9,10);current=c(6,10,11,7,8)
        z=m.classify_completed_break(lo,prev,current,1,7*TF)
        self.assertEqual((z.kind,z.side),("CHoCH","BEARISH"))
    def test_24_new_4h_parent_incomplete_witness_rejected(self):
        self.bad(lambda:m.check_parent_hierarchy({"parent_tf":"1H"}),
                 "NON_4H_EXIT_PARENT")
    def test_25_c105_original_sha_immutable(self):
        p=HERE/"c105_parent4h_structural_geometry.py"
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
            "b86623b8a7bb8f2580c129e70edbc0dfcf0f68bafc90f94e726d999f0e5db7ac")
        c105.frozen_source_checks()
    def test_26_all_prior_c105_trade_exit_parents_and_causal_event_clock(self):
        z=json.loads((BASEROOT/"evidence/c105/C105_4H_PARENT_320_ORIGINAL_NATIVE3M_ZIPS.json").read_text())
        self.assertEqual(len(z["trades"]),25)
        self.assertTrue(all(m.check_parent_hierarchy(t) for t in z["trades"]))
    def test_27_reject_late_ftapivot_using_same_c105_trade(self):
        z=json.loads((BASEROOT/"evidence/c105/C105_4H_PARENT_320_ORIGINAL_NATIVE3M_ZIPS.json").read_text())
        t=dict(z["trades"][0]);t["fta_confirmed_ms"]=t["entry_ms"]+TF
        self.bad(lambda:m.check_parent_hierarchy(t),"FUTURE_OR_UNKNOWN_4H_FTA")
    def test_28_reject_3m_stop_in_4h_trade_witness(self):
        z=json.loads((BASEROOT/"evidence/c105/C105_4H_PARENT_320_ORIGINAL_NATIVE3M_ZIPS.json").read_text())
        t=dict(z["trades"][0]);t["stop_source_tf"]="3M"
        self.bad(lambda:m.check_parent_hierarchy(t),"NON_4H_EXIT_PARENT")
    def test_29_reject_15m_confirm_at_same_1h_reaction_clock(self):
        z=json.loads((BASEROOT/"evidence/c105/C105_4H_PARENT_320_ORIGINAL_NATIVE3M_ZIPS.json").read_text())
        t=dict(z["trades"][0]);t["fifteen_minute_vc_close_ms"]=t["one_hour_rejection_close_ms"]
        t["entry_ms"]=t["fifteen_minute_vc_close_ms"]
        self.bad(lambda:m.check_parent_hierarchy(t),"PARENT_CAUSAL_ORDER_BROKEN")
    def test_30_reference_license_noncommercial_no_copied_pine_source(self):
        code=(HERE/"c106_structure_event_provenance.py").read_text()
        self.assertIn("NO copied Pine implementation",code)
        self.assertNotIn("request.security",code)
        self.assertNotIn("lookahead_on",code)
if __name__=="__main__":unittest.main()
