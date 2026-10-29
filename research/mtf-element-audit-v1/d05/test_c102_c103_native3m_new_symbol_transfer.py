"""C102/C103 adversarial negatives: source provenance, causal costs and trade selection."""
import copy
import hashlib
import io
import sys
import unittest
import zipfile
from decimal import Decimal as D
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c102_c103_native3m_new_symbol_transfer as m

def trade(stop="99",delay=12,entry=100,side="LONG",start=1800000000000):
    t={"symbol":"LINKUSDT","side":side,"source_tf":"NATIVE_3M",
       "route":"C_1H_WICK_RAID_NATIVE3M_BOS",
       "entry":str(entry),"stop":str(stop),"target":str(entry+2 if side=="LONG" else entry-2),
       "bos_close_ms":start,"entry_ms":start,"raid_closed_ms":start-delay*60000,
       "exit_ms":start+20*m.THREE,"net_r":1.2}
    return t

def csv_fixture(symbol="LINKUSDT",date="2026-09-26",mutation=None):
    start=m.timestamp(date)
    lines=[]
    for k in range(480):
        at=start+k*m.THREE
        r=[str(at),"100","101","99","100","1",str(at+m.THREE-1),
           "100","1","0.5","50","0"]
        if mutation:
            mutation(r,k)
        lines.append(",".join(r))
    raw=("\n".join(lines)+"\n").encode()
    fn=f"{symbol}-3m-{date}"
    bio=io.BytesIO()
    with zipfile.ZipFile(bio,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(fn+".csv",raw)
    blob=bio.getvalue();digest=hashlib.sha256(blob).hexdigest()
    def fetch(url):
        if url.endswith(".CHECKSUM"):return (digest+"  "+fn+".zip\n").encode()
        return blob
    return fetch

class Tests(unittest.TestCase):
    def reject(self,call,msg):
        with self.assertRaisesRegex(m.C102Rejected,msg):call()

    def test_01_only_whitelisted_symbols(self):
        self.reject(lambda:m.native_daily("BTCUSDT","2026-09-26"),"UNREGISTERED")

    def test_02_only_registered_dates(self):
        self.reject(lambda:m.native_daily("LINKUSDT","2026-10-29"),"UNREGISTERED")

    def test_03_true_480_native3m(self):
        xs,meta=m.native_daily("LINKUSDT","2026-09-26",fetch=csv_fixture())
        self.assertEqual(len(xs),480)
        self.assertEqual(xs[0].start_ms,m.BEGIN_MS)
        self.assertEqual(xs[-1].known_ms,m.BEGIN_MS+m.DAY_MS)
        self.assertEqual(meta["timeframe"],"NATIVE_3M")

    def test_04_corrupt_zip_checksum(self):
        f=csv_fixture()
        def tamper(url):
            v=f(url)
            return b"0"*64+b"  LINKUSDT-3m-2026-09-26.zip" if url.endswith(".CHECKSUM") else v
        self.reject(lambda:m.native_daily("LINKUSDT","2026-09-26",fetch=tamper),"CHECKSUM")

    def test_05_csv_header_not_480(self):
        f=csv_fixture(mutation=lambda r,k: r.__setitem__(6,"0") if k==2 else None)
        self.reject(lambda:m.native_daily("LINKUSDT","2026-09-26",fetch=f),"NATIVE3M_CLOCK")

    def test_06_candle_gap(self):
        f=csv_fixture(mutation=lambda r,k:r.__setitem__(0,str(int(r[0])+m.THREE)) if k==2 else None)
        self.reject(lambda:m.native_daily("LINKUSDT","2026-09-26",fetch=f),"NATIVE3M_CLOCK")

    def test_07_ohlc_high_bad(self):
        f=csv_fixture(mutation=lambda r,k:r.__setitem__(2,"98") if k==7 else None)
        self.reject(lambda:m.native_daily("LINKUSDT","2026-09-26",fetch=f),"IMPOSSIBLE_ORIGINAL")

    def test_08_negative_volume(self):
        f=csv_fixture(mutation=lambda r,k:r.__setitem__(5,"-1") if k==7 else None)
        self.reject(lambda:m.native_daily("LINKUSDT","2026-09-26",fetch=f),"IMPOSSIBLE_ORIGINAL")

    def test_09_nan_price(self):
        f=csv_fixture(mutation=lambda r,k:r.__setitem__(4,"NaN") if k==7 else None)
        self.reject(lambda:m.native_daily("LINKUSDT","2026-09-26",fetch=f),"NONFINITE")

    def test_10_missing_csv_fields(self):
        f=csv_fixture(mutation=lambda r,k:r.pop() if k==7 else None)
        self.reject(lambda:m.native_daily("LINKUSDT","2026-09-26",fetch=f),"WRONG_BINANCE_CSV")

    def test_11_unregistered_variant(self):
        self.reject(lambda:m.eligible(trade(),"RR2_FIXED"),"UNREGISTERED_VARIANT")

    def test_12_baseline_keeps_valid(self):
        self.assertTrue(m.eligible(trade(),"BASELINE"))

    def test_13_cost_valid(self):
        self.assertTrue(m.eligible(trade(stop="99"),"V_COST"))

    def test_14_cost_invalid(self):
        self.assertFalse(m.eligible(trade(stop="99.8"),"V_COST"))

    def test_15_cost_boundary(self):
        self.assertTrue(m.eligible(trade(stop="99.5"),"V_COST"))

    def test_16_clock_valid(self):
        self.assertTrue(m.eligible(trade(delay=12),"V_CLOCK"))

    def test_17_clock_boundary(self):
        self.assertTrue(m.eligible(trade(delay=15),"V_CLOCK"))

    def test_18_clock_invalid(self):
        self.assertFalse(m.eligible(trade(delay=18),"V_CLOCK"))

    def test_19_clock_combo_false(self):
        self.assertFalse(m.eligible(trade(stop="99.8",delay=12),"V_BOTH"))

    def test_20_clock_combo_valid(self):
        self.assertTrue(m.eligible(trade(stop="99",delay=12),"V_BOTH"))

    def test_21_wrong_tf(self):
        t=trade();t["source_tf"]="NATIVE_5M"
        self.reject(lambda:m.eligible(t,"BASELINE"),"INCOMPATIBLE")

    def test_22_bos_after_entry(self):
        t=trade();t["bos_close_ms"]+=m.THREE
        self.reject(lambda:m.eligible(t,"V_CLOCK"),"INVALID_PREENTRY")

    def test_23_raid_after_bos(self):
        t=trade();t["raid_closed_ms"]+=20*60000
        self.reject(lambda:m.eligible(t,"BASELINE"),"INVALID_PREENTRY")

    def test_24_target_wrong_side(self):
        t=trade();t["target"]="98"
        self.reject(lambda:m.eligible(t,"BASELINE"),"INVALID_STRUCTURAL")

    def test_25_zero_risk(self):
        t=trade();t["stop"]=t["entry"]
        self.reject(lambda:m.eligible(t,"BASELINE"),"INVALID_PREENTRY")

    def test_26_short_valid(self):
        self.assertTrue(m.eligible(trade(side="SHORT",stop="101"),"BASELINE"))

    def test_27_future_selection_never_chooses_overlap(self):
        a=trade(start=1800000000000)
        b=trade(start=1800000000000+5*m.THREE)
        self.assertEqual(len(m.select_sequential([a,b],"BASELINE")),1)

    def test_28_filter_frees_slot_for_next_setup(self):
        a=trade(stop="99.8",start=1800000000000)
        b=trade(stop="99",start=1800000000000+5*m.THREE)
        picked=m.select_sequential([a,b],"V_COST")
        self.assertEqual([x["entry_ms"] for x in picked],[b["entry_ms"]])

    def test_29_cost_25_gt_14_decreases_netR(self):
        a=trade()
        self.assertLess(m.price_stress(a,25)["net_r"],a["net_r"])

    def test_30_cost_40_gt_25(self):
        a=trade()
        self.assertLess(m.price_stress(a,40)["net_r"],m.price_stress(a,25)["net_r"])

    def test_31_invalid_cost(self):
        self.reject(lambda:m.price_stress(trade(),17),"UNREGISTERED_COST")

    def test_32_cost_monotonic_no_change_target(self):
        a=trade()
        b=m.price_stress(a,40)
        self.assertEqual((a["stop"],a["target"]),(b["stop"],b["target"]))

    def test_33_no_fixedRR_parameter(self):
        a=trade()
        self.assertNotIn("fixed_rr",m.price_stress(a,25))

    def test_34_crypto_32_days_exact(self):
        self.assertEqual((len(m.DAYS),m.EXPECTED_ZIPS), (32,160))

    def test_35_no_future_window(self):
        self.assertEqual(m.END_MS-m.BEGIN_MS,32*m.DAY_MS)

if __name__=="__main__":
    unittest.main()
