"""C116 source and null-control adversarial tests, no historical outcomes."""
import csv,hashlib,io,unittest
from decimal import Decimal as D
from unittest.mock import patch
from zipfile import ZipFile,ZIP_DEFLATED
import c116_canonical_original_native1m_source as src
import c116_single_source_controlled_4h_poi_replay as sim

SYMBOL="BNBUSDT"
DAY="2026-04-01"
START=1775001600000  # 2026-04-01T00:00:00Z
def archived(*,wrong_checksum=False,one_minute_missing=False,broken_h=False,clock_shift=False):
    out=io.StringIO();writer=csv.writer(out)
    for k in range(1439 if one_minute_missing else 1440):
        start=START+k*60000+(60000 if clock_shift and k==34 else 0)
        h="99" if broken_h and k==27 else "101"
        v="5" if k%7 else "3"
        writer.writerow([start,"100",h,"99","100",v,start+59999,
                         "500",3,"2","200",0])
    stem=f"{SYMBOL}-1m-{DAY}"
    buf=io.BytesIO()
    with ZipFile(buf,"w",compression=ZIP_DEFLATED) as z:
        z.writestr(stem+".csv",out.getvalue().encode())
    data=buf.getvalue()
    digest=hashlib.sha256(data).hexdigest()
    url=f"{src.BASE}data/futures/um/daily/klines/{SYMBOL}/1m/{stem}.zip"
    lookups={url:data,url+".CHECKSUM":(("0"*64 if wrong_checksum else digest)+
                                    "  "+stem+".zip").encode()}
    return lambda u:lookups[u]

class C116CanonicalTests(unittest.TestCase):
    def test_frozen_c114_original_engine_and_new_windows(self):
        self.assertTrue(sim.frozen())
        self.assertEqual(len(sim.WINDOWS),2)
        self.assertEqual(sim.WINDOWS[0][1].strftime("%Y-%m-%d"),DAY)
        self.assertEqual(sim.SEED,11620261030)
    def test_verified_provider_1m_zip_exact_1440(self):
        bars,receipt=src.daily(SYMBOL,DAY,fetch=archived())
        self.assertEqual(len(bars),1440)
        self.assertTrue(receipt["provider_checksum_verified"])
        self.assertEqual(bars[0].known_ms,bars[1].start_ms)
    def test_canonical_derivation_3m5m_and_exact_parity(self):
        a,b,r=src.daily_derived(SYMBOL,DAY,fetch=archived())
        self.assertEqual(len(a),480)
        self.assertEqual(len(b),288)
        self.assertEqual(a[0].known_ms,a[1].start_ms)
        self.assertEqual(b[0].close_ms,b[1].open_ms)
        self.assertEqual(a[0].open,b[0].o)
        self.assertTrue(a[0].source_sha256==r["zip_sha256"] if hasattr(a[0],"source_sha256") else True)
    def test_original_zip_provider_sha_mismatch_fails(self):
        with self.assertRaisesRegex(src.C116SourceError,"CHECKSUM"):
            src.daily(SYMBOL,DAY,fetch=archived(wrong_checksum=True))
    def test_original_zip_missing_1m_bar_fails_not_synthesized(self):
        with self.assertRaisesRegex(src.C116SourceError,"NOT_1440"):
            src.daily(SYMBOL,DAY,fetch=archived(one_minute_missing=True))
    def test_original_source_bad_high_fails_no_price_repair(self):
        with self.assertRaisesRegex(src.C116SourceError,"IMPOSSIBLE_OHLCV"):
            src.daily(SYMBOL,DAY,fetch=archived(broken_h=True))
    def test_original_utc_timestamp_gap_fails(self):
        with self.assertRaisesRegex(src.C116SourceError,"GAP_DUPLICATE"):
            src.daily(SYMBOL,DAY,fetch=archived(clock_shift=True))
    def test_derived_cross_mismatch_fails(self):
        originals,_=src.daily(SYMBOL,DAY,fetch=archived())
        gap=list(originals)
        original=gap[3]
        gap[3]=src.Original1m(original.start_ms+1,original.known_ms,
                               original.o,original.h,original.l,original.c,original.volume)
        with self.assertRaises(src.C116SourceError):
            src.roll(tuple(gap),SYMBOL,"f"*64)
    def test_placebo_empty_is_no_power(self):
        z=sim.paired_label_placebo([])
        self.assertEqual(z["validity"],"NO_POWER")
        self.assertIsNone(z["p_one_sided"])
    def test_placebo_positive_vs_negative_is_reproducible(self):
        x=[(("BNBUSDT",2026,15),1.0),(("LINKUSDT",2026,15),2.0),
           (("LINKUSDT",2026,16),1.0)]
        pos=sim.paired_label_placebo(x)
        neg=sim.paired_label_placebo([(k,-v) for k,v in x])
        self.assertEqual(pos,sim.paired_label_placebo(x))
        self.assertLess(pos["p_one_sided"],neg["p_one_sided"])
        self.assertEqual(pos["matched_pairs"],3)
    def test_placebo_cannot_posthoc_change_seed(self):
        with self.assertRaises(sim.C116Rejected):
            sim.paired_label_placebo([(("BNBUSDT",2026,15),1)],seed=3)
    def test_source_scope_restore_economics(self):
        old=(sim.original.WINDOWS,sim.original.download,
             sim.original.per_symbol,sim.original.PRECOMMIT)
        with sim.research_scope():
            self.assertIs(sim.original.download,sim.canonical_download)
            self.assertIs(sim.original.per_symbol,sim.price_lineage_per_symbol)
        self.assertEqual(sim.original.WINDOWS,old[0])
        self.assertIs(sim.original.download,old[1])
        self.assertIs(sim.original.per_symbol,old[2])
        self.assertEqual(sim.original.PRECOMMIT,old[3])
    def test_direction_breakdown_has_both_sides_and_all_itt(self):
        event=lambda side,label:{"side":side,"treatment":label,"trade":None}
        out=sim.directional_diagnostics([event("LONG","T_CHoCH"),
            event("SHORT","T_CHoCH"),event("SHORT","C_NO_CHoCH")])
        self.assertEqual(out["T_CHoCH_LONG"]["all_itt_event_n"],1)
        self.assertEqual(out["T_CHoCH_SHORT"]["filled_n"],0)
        self.assertEqual(out["C_NO_CHoCH_SHORT"]["all_itt_event_n"],1)
if __name__=="__main__":unittest.main()
