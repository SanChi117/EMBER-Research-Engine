"""Z01 adversarial tests: fully closed clocks, 5M pivots and paired control."""
import csv
from decimal import Decimal as D
from hashlib import sha256
from io import BytesIO
from unittest import TestCase
from zipfile import ZipFile

import structural_reaction_source as e

def bar(ms, span, o=100, hi=101, lo=99, close=100):
    return e.Bar(ms,ms+span,D(str(o)),D(str(hi)),D(str(lo)),
                 D(str(close)),D(1))

def zone(side="LONG"):
    return e.Zone("Z",side,0,D(98),D(102),D(100),
                  D(94) if side=="LONG" else D(106),
                  D(115) if side=="LONG" else D(85),
                  D(5),D(90),D(120),"NEUTRAL")

def native_zip(day="2025-05-05",bad_clock=False):
    start=e.stamp(day)
    name=f"BNBUSDT-1m-{day}.csv"
    rows=[]
    for i in range(1440):
        ms=start+i*e.MINUTE+(1 if bad_clock and i==400 else 0)
        rows.append([ms,"100","102","99","100","5",ms+e.MINUTE-1,
                     "500","10","2","200","0"])
    stream=BytesIO()
    with ZipFile(stream,"w") as z:
        text="\n".join(",".join(map(str,row)) for row in rows)+"\n"
        z.writestr(name,text.encode())
    blob=stream.getvalue()
    return blob,f"{sha256(blob).hexdigest()}  BNBUSDT-1m-{day}.zip".encode()

class Z01Tests(TestCase):
    def test_00_source_calendar_is_frozen(self):
        self.assertTrue(e.validate_constants())
        self.assertEqual(e.SOURCE_ZIPS,1452)
        self.assertEqual(e.SOURCE_1M_BARS,2090880)
    def test_01_real_1m_and_5m_not_fake_3m(self):
        rows=tuple(bar(i*e.MINUTE,e.MINUTE) for i in range(15))
        self.assertEqual(len(e.aggregate(rows,e.THREE)),5)
        self.assertEqual(len(e.aggregate(rows,e.FIVE)),3)
        self.assertEqual(len(e.aggregate(rows,e.FIFTEEN)),1)
    def test_02_5m_from_3m_is_refused(self):
        rows=tuple(bar(i*e.THREE,e.THREE) for i in range(5))
        with self.assertRaises(e.Z01Error):
            e.aggregate(rows,e.FIVE)
    def test_03_partial_mtf_refused(self):
        rows=tuple(bar(i*e.MINUTE,e.MINUTE) for i in range(4))
        with self.assertRaises(e.Z01Error):
            e.aggregate(rows,e.FIVE)
    def test_04_closed_4h_2right_pivot(self):
        highs=[101,103,110,105,104,107]
        z=tuple(bar(i*e.FOUR,e.FOUR,100,h,90 if i!=2 else 89,100) for i,h in enumerate(highs))
        s=e.swings(z,e.FOUR)
        p=[x for x in s if x.kind=="HIGH" and x.price==110]
        self.assertEqual(len(p),1)
        self.assertEqual(p[0].confirmed_ms,5*e.FOUR)
    def test_05_1d_structure_is_neutral_without_source(self):
        self.assertEqual(e.d1_structure([]),"NEUTRAL")
    def test_06_1d_hh_hl_is_classified(self):
        s=[e.Swing("HIGH",D(105),10,20),e.Swing("HIGH",D(110),30,40),
           e.Swing("LOW",D(90),15,25),e.Swing("LOW",D(96),35,45)]
        self.assertEqual(e.d1_structure(s),"UP_HH_HL")
    def test_07_1d_lh_ll_is_classified(self):
        s=[e.Swing("HIGH",D(110),10,20),e.Swing("HIGH",D(105),30,40),
           e.Swing("LOW",D(96),15,25),e.Swing("LOW",D(90),35,45)]
        self.assertEqual(e.d1_structure(s),"DOWN_LH_LL")
    def test_08_first_touch_1m_asof(self):
        m=(bar(0,e.MINUTE,108,110,105,108),
           bar(e.MINUTE,e.MINUTE,103,104,99,100))
        hit,reason=e.first_touch(zone(),m,(),0,2*e.MINUTE)
        self.assertEqual(reason,"OK")
        self.assertEqual(hit,(1,2*e.MINUTE))
    def test_09_4h_pre_touch_invalidation(self):
        z=zone()
        m=(bar(0,e.MINUTE,108,110,105,108),
           bar(e.MINUTE,e.MINUTE,108,109,105,107))
        f=(bar(0,e.MINUTE,110,111,95,93),)
        hit,reason=e.first_touch(z,m,f,0,5*e.MINUTE)
        self.assertIsNone(hit)
        self.assertEqual(reason,"PRE_TOUCH_4H_INVALIDATED")
    def test_10_pretrend_is_required(self):
        level,why=e.pretrend_and_level("LONG",100,())
        self.assertIsNone(level)
        self.assertEqual(why,"INSUFFICIENT_PRETOUCH_5M_PIVOTS")
    def test_11_pretrend_wrong_side_rejected(self):
        piv=[e.Swing("HIGH",D(100),0,10),e.Swing("HIGH",D(110),20,30),
             e.Swing("LOW",D(90),0,10),e.Swing("LOW",D(95),20,30)]
        level,why=e.pretrend_and_level("LONG",40,piv)
        self.assertIsNone(level)
        self.assertEqual(why,"NO_OPPOSITE_5M_DOWNTREND")
    def test_12_pretrend_5m_level_frozen(self):
        piv=[e.Swing("HIGH",D(108),0,10),e.Swing("HIGH",D(104),20,30),
             e.Swing("LOW",D(100),0,10),e.Swing("LOW",D(96),20,30),
             e.Swing("HIGH",D(150),40,1000000)]
        level,reason=e.pretrend_and_level("LONG",40,piv)
        self.assertEqual((level,reason),(D(104),"OK"))
    def test_13_5m_break_needs_completed_candle(self):
        touch=10*e.FIVE
        piv=[e.Swing("HIGH",D(108),0,10),e.Swing("HIGH",D(104),20,30),
             e.Swing("LOW",D(100),0,10),e.Swing("LOW",D(96),20,30)]
        five=[bar(i*e.FIVE,e.FIVE,103,105,99,103) for i in range(12)]
        five[10]=bar(10*e.FIVE,e.FIVE,103,105,99,105)
        minute=tuple(bar(touch+i*e.MINUTE,e.MINUTE,103,105,99,103)
                     for i in range(20))
        at,reason=e.find_choc(zone(),touch,minute,five,piv)
        self.assertEqual(reason,"OK")
        self.assertEqual(at,11*e.FIVE)
    def test_14_5m_break_after_stop_disallowed(self):
        touch=10*e.FIVE
        piv=[e.Swing("HIGH",D(108),0,10),e.Swing("HIGH",D(104),20,30),
             e.Swing("LOW",D(100),0,10),e.Swing("LOW",D(96),20,30)]
        five=[bar(i*e.FIVE,e.FIVE,103,105,99,103) for i in range(12)]
        five[10]=bar(10*e.FIVE,e.FIVE,103,105,93,105)
        minute=[bar(touch+i*e.MINUTE,e.MINUTE,103,105,99,103)
                for i in range(20)]
        minute[0]=bar(touch,e.MINUTE,103,105,93,103)
        at,reason=e.find_choc(zone(),touch,tuple(minute),five,piv)
        self.assertIsNone(at)
        self.assertEqual(reason,"STOP_BEFORE_5M_CONFIRMATION")
    def test_15_h4_sl_tp_derived_not_fixed_rr(self):
        z=zone()
        p,why=e.plan(z,D(100))
        self.assertEqual(why,"OK")
        self.assertEqual(p["risk"],D(6))
        self.assertEqual(p["target"],D(115))
    def test_16_h4_wrong_target_rejected(self):
        z=e.Zone("Z","LONG",0,D(98),D(102),D(100),D(94),
                 D(98),D(5),D(90),D(120),"NEUTRAL")
        p,why=e.plan(z,D(100))
        self.assertIsNone(p)
        self.assertEqual(why,"H4_SL_TP_WRONG_SIDE")
    def test_17_simulator_stop_first_same3m(self):
        bars=(bar(0,e.THREE,100,118,93,100),)
        t,why=e.simulate(zone(),bars,0,"A0_FIRST_TOUCH",0,100)
        self.assertEqual(why,"OK")
        self.assertEqual(t["exit_reason"],"STOP_FIRST_NATIVE3M")
    def test_18_simulator_gap_through_h4_stop_cannot_vanish(self):
        bars=(bar(0,e.THREE,90,101,89,92),)
        t,why=e.simulate(zone(),bars,0,"A0_FIRST_TOUCH",0,100)
        self.assertEqual(why,"OK")
        self.assertEqual(t["exit_reason"],"PREENTRY_STOP_GAP_LOSS")
        self.assertLessEqual(t["gross_r"],-1)
    def test_19_simulator_target_on_second_3m(self):
        bars=(bar(0,e.THREE,100,110,99,105),
              bar(e.THREE,e.THREE,105,118,104,116))
        t,why=e.simulate(zone(),bars,0,"B1_5M_CONFIRM_15M_EXEC",0,100)
        self.assertEqual(why,"OK")
        self.assertEqual(t["exit_reason"],"4H_TARGET")
    def test_20_score_has_same_denominator_when_zero_fills(self):
        ledger=[{"trade":None},{"trade":None},{"trade":None}]
        a=e.score(ledger,25)
        self.assertEqual((a["opportunities"],a["fills"],a["zero_fills"]),(3,0,3))
        self.assertIsNone(a["pf"])
    def test_21_25bps_cost_worse_than_14(self):
        t={"entry":"100","stop":"94","gross_r":2.0,"fold":"EARLY"}
        rec=[{"trade":t}]
        self.assertGreater(e.score(rec,14)["net_r"],e.score(rec,25)["net_r"])
    def test_22_exact_provider_checksum_required(self):
        blob,check=native_zip()
        with self.assertRaises(e.Z01Error):
            e.parse_daily_zip(blob,"BNBUSDT","2025-05-05",b"bad checksum")
    def test_23_native_1m_complete_file_and_sha(self):
        blob,check=native_zip()
        bars,receipt=e.parse_daily_zip(blob,"BNBUSDT","2025-05-05",check)
        self.assertEqual(len(bars),1440)
        self.assertEqual(receipt["zip_sha256"],sha256(blob).hexdigest())
        self.assertEqual(bars[-1].close_ms,e.stamp("2025-05-06"))
    def test_24_native1m_source_clock_poison_fails(self):
        blob,check=native_zip(bad_clock=True)
        with self.assertRaises(e.Z01Error):
            e.parse_daily_zip(blob,"BNBUSDT","2025-05-05",check)
    def test_25_five_to_3m_partial_cannot_pass(self):
        rows=tuple(bar(i*e.FIVE,e.FIVE) for i in range(15))
        with self.assertRaises(e.Z01Error):
            e.aggregate(rows,e.THREE)
