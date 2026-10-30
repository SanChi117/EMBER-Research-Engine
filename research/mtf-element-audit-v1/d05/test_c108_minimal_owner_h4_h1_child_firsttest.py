"""C108 pre-price 25 negative/positive semantic proofs, ONLY owner-linked minimal route.
Unmodified old C105/C106/C107 engines and original 41 PAPER trades.
"""
import sys,unittest,hashlib
from pathlib import Path
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c108_parent_h1_child_first_test_geometry as m
import c108_owner_child_native3m_paper_research as r
import c105_parent4h_structural_geometry as h4
import c104_native3m_source as orig
from test_c105_parent4h_only_geometry import bar,parent,fixtures
from c21_native3m_source_bridge import Original3mRow
from test_c102_c103_native3m_new_symbol_transfer import csv_fixture

def x():
    return m.LinkedParent("LONG",D("98"),D("99"),0,"parent-p4")
def child_bars(t=0):
    # 1H bullish FVG [bar0.high=101, bar2.low=102], not nested in [98,99].
    return (bar(t,h4.H,o="99",h="101",l="97",c="100"),
            bar(t+h4.H,h4.H,o="101",h="105",l="100",c="104"),
            bar(t+2*h4.H,h4.H,o="103",h="106",l="102",c="105"))
class C108Minimal(unittest.TestCase):
    def bad(self,f,part):
        with self.assertRaisesRegex((m.C108Reject,r.C108Error),part):f()
    def test_01_exact_unseen_historical_dates(self):
        self.assertEqual((r.DAYS[0],r.DAYS[-1],len(r.DAYS)),("2026-08-20","2026-09-20",32))
    def test_02_same_ten_fixed_symbols(self):
        self.assertEqual(len(r.UNIVERSE),10)
        self.assertEqual(len(set(r.UNIVERSE)),10)
    def test_03_unmodified_original_h4_owner_code(self):
        r.check_freeze()
    def test_04_legacy_original_provider_state_restored_error(self):
        sym=orig.SYMBOLS;days=orig.DAYS
        def no_data(url):raise RuntimeError("original source offline")
        with self.assertRaises(RuntimeError):
            r.load_native_original(fetch=no_data)
        self.assertEqual(orig.SYMBOLS,sym)
        self.assertEqual(orig.DAYS,days)
    def test_05_original_provider_daily_480_reusable(self):
        prev_s,prev_d=orig.SYMBOLS,orig.DAYS
        try:
            orig.SYMBOLS=r.UNIVERSE;orig.DAYS=r.DAYS
            # csv_fixture returns deterministic original-provider-formatted complete rows
            rows,meta=orig.daily("BNBUSDT","2026-08-20",fetch=csv_fixture("BNBUSDT"))
            self.assertEqual((len(rows),meta["bars"]),(480,480))
        finally:
            orig.SYMBOLS,orig.DAYS=prev_s,prev_d
    def test_06_4h_first_touch_cannot_be_on_birth(self):
        z=x();z.created_ms=h4.H4
        self.assertFalse(m.parent_touch(z,bar(0,h4.H4,h="100",l="98")))
    def test_07_4h_parent_first_physical_touch(self):
        z=x()
        self.assertTrue(m.parent_touch(z,bar(h4.M15,h4.M15,h="100",l="99")))
    def test_08_parent_unconfirmed_h1_does_not_create_child(self):
        z=x();z.state="WAIT_1H_CHILD";z.first_touch_ms=3*h4.H
        item,why=m.child_from_closed_h1(z,child_bars())
        self.assertIsNone(item);self.assertEqual(why,"H1_CHILD_NOT_CLOSED_AFTER_4H_TOUCH")
    def test_09_first_child_1h_imb_born_after_h4_parent_test(self):
        z=x();z.state="WAIT_1H_CHILD";z.first_touch_ms=h4.H
        item,why=m.child_from_closed_h1(z,child_bars(h4.H))
        self.assertEqual((why,item[0],item[1],item[2]),("OK",D("101"),D("102"),4*h4.H))
    def test_10_no_opposite_child_1h_fvg(self):
        z=x();z.state="WAIT_1H_CHILD";z.first_touch_ms=h4.H
        a=bar(h4.H,h4.H,o="106",h="109",l="104",c="106")
        b=bar(2*h4.H,h4.H,o="102",h="106",l="99",c="100")
        c=bar(3*h4.H,h4.H,o="99",h="101",l="97",c="98")
        item,why=m.child_from_closed_h1(z,(a,b,c))
        self.assertEqual(why,"NO_MATCHING_1H_IMB")
    def test_11_nested_1h_child_explicit_source_veto(self):
        z=x();z.state="WAIT_1H_CHILD";z.first_touch_ms=h4.H
        a=bar(h4.H,h4.H,o="97",h="98.2",l="96",c="98")
        b=bar(2*h4.H,h4.H,o="98",h="99",l="97",c="98.7")
        c=bar(3*h4.H,h4.H,o="98.8",h="99.1",l="98.5",c="99")
        item,why=m.child_from_closed_h1(z,(a,b,c))
        self.assertEqual(why,"NESTED_4H_IMB_1H_IMB_VETO")
    def test_12_adopt_child_after_real_h1_close_only(self):
        z=x();z.state="WAIT_1H_CHILD";z.first_touch_ms=h4.H
        item,_=m.child_from_closed_h1(z,child_bars(h4.H))
        m.adopt_child(z,item)
        self.assertEqual(z.child_created_ms,4*h4.H)
        self.assertEqual(z.state,"WAIT_CHILD_FIRST_TEST")
        self.assertIn(":H1:",z.child_id)
    def test_13_child_cannot_be_touched_at_birth(self):
        z=x();z.state="WAIT_1H_CHILD";z.first_touch_ms=h4.H
        item,_=m.child_from_closed_h1(z,child_bars(h4.H));m.adopt_child(z,item)
        self.assertFalse(m.child_first_touch(z,bar(4*h4.H-h4.M15,h4.M15,o="103",h="104",l="101",c="103")))
    def test_14_first_child_test_only_after_creation(self):
        z=x();z.state="WAIT_1H_CHILD";z.first_touch_ms=h4.H
        item,_=m.child_from_closed_h1(z,child_bars(h4.H));m.adopt_child(z,item)
        m.adopt_child_first_test(z,bar(4*h4.H,h4.M15,o="103",h="104",l="101",c="103"))
        self.assertEqual((z.child_first_test_ms,z.state),(4*h4.H+h4.M15,"WAIT_15M_DIRECT_IMB"))
    def test_15_second_child_test_never_admitted(self):
        z=x();z.state="WAIT_1H_CHILD";z.first_touch_ms=h4.H
        item,_=m.child_from_closed_h1(z,child_bars(h4.H));m.adopt_child(z,item)
        candle=bar(4*h4.H,h4.M15,o="103",h="104",l="101",c="103")
        m.adopt_child_first_test(z,candle)
        self.bad(lambda:m.adopt_child_first_test(z,candle),"FIRST_1H_CHILD")
    def test_16_no_direct_vc_on_same_child_test_close(self):
        z=x();z.state="WAIT_15M_DIRECT_IMB";z.child_first_test_ms=4*h4.H+h4.M15
        arr=(bar(4*h4.H-2*h4.M15,h4.M15,o="100",h="101",l="99",c="100"),
             bar(4*h4.H-h4.M15,h4.M15,o="101",h="103",l="100",c="102"),
             bar(4*h4.H,h4.M15,o="102",h="105",l="103",c="104"))
        self.assertFalse(m.direct_15m_imb(z,arr))
    def test_17_direct_15m_imb_only_after_real_child_test(self):
        z=x();z.state="WAIT_15M_DIRECT_IMB";z.child_first_test_ms=4*h4.H
        arr=(bar(4*h4.H,h4.M15,o="100",h="101",l="99",c="100"),
             bar(4*h4.H+h4.M15,h4.M15,o="101",h="103",l="100",c="102"),
             bar(4*h4.H+2*h4.M15,h4.M15,o="102",h="105",l="103",c="104"))
        self.assertTrue(m.direct_15m_imb(z,arr))
    def test_18_previous_candle_high_break_only_is_NOT_direct_imb(self):
        z=x();z.state="WAIT_15M_DIRECT_IMB";z.child_first_test_ms=4*h4.H
        arr=(bar(4*h4.H,h4.M15,o="100",h="115",l="99",c="101"),
             bar(4*h4.H+h4.M15,h4.M15,o="101",h="110",l="100",c="104"),
             bar(4*h4.H+2*h4.M15,h4.M15,o="104",h="111",l="103",c="110.5"))
        self.assertFalse(m.direct_15m_imb(z,arr))
    def test_19_4h_close_zone_invalidation_true(self):
        z=x();self.assertTrue(m.parent_invalidated(z,bar(h4.H4,h4.H4,o="98",h="100",l="96",c="97")))
    def test_20_4h_low_wick_not_4h_close_invalidation(self):
        z=x();self.assertFalse(m.parent_invalidated(z,bar(h4.H4,h4.H4,o="98",h="100",l="95",c="98.5")))
    def test_21_protective_stop_kept_on_3m_without_4h_invalidity(self):
        z=x();a=m.protective_stop_semantics(z,"STOP_FIRST_SAME_3M",
             bar(h4.H4,h4.H4,o="98",h="100",l="95",c="98.5"))
        self.assertTrue(a["protective_stop_triggered"])
        self.assertEqual(a["parent_validity_at_4h_close"],"STILL_VALID")
        self.assertIn("NEVER_WIDEN",a["risk_policy"])
    def test_22_original_4h_stop_tp_unchanged(self):
        now,f,sw,rows,starts=fixtures()
        z=x();z.created_ms=h4.H4
        plan,why=h4.parent_plan(z,now,D("100"),f,sw,rows,starts)
        self.assertEqual((plan["stop_source_tf"],plan["target_source_tf"]),("4H","4H"))
    def test_23_parent_age_48h(self):
        z=x();self.assertEqual(m.eligible_ttl(z,49*h4.H),"PARENT_48H_EXPIRED")
    def test_24_after_test_ttl_8h(self):
        z=x();z.first_touch_ms=h4.H
        self.assertEqual(m.eligible_ttl(z,10*h4.H),"PARENT_FIRST_TOUCH_8H_TTL_EXPIRED")
    def test_25_no_new_luxalgo_indicators_or_live_orders(self):
        data=(Path(__file__).resolve().parent/"c108_owner_child_native3m_paper_research.py").read_text()
        self.assertNotIn("lookahead_on",data)
        self.assertNotIn("request.security",data)
        self.assertNotIn("bos_choch",data)
        self.assertNotIn("LIVE_ORDER",data)
if __name__=="__main__":unittest.main()
