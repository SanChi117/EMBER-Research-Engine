"""Never turn a verified provider checksum into imagined interval agreement."""
import csv
import hashlib
import io
import unittest
from zipfile import ZipFile,ZIP_DEFLATED
from decimal import Decimal as D
import c114_volume_discrepancy_forensic as x

def stub_fetch(volume_5m_extra=None,wrong_high_5m=None,corrupt_checksum=False,
               omit_one_1m=False):
    cache={}
    for tf,step in x.TIMEFRAMES.items():
        stem=f"{x.SYMBOL}-{tf}-{x.DATE}"
        csvout=io.StringIO()
        w=csv.writer(csvout)
        total=86400000//step
        for i in range(total-(1 if omit_one_1m and tf=="1m" else 0)):
            stamp=1736812800000+i*step  # Jan 14 2025 midnight UTC
            val=D(step)/D(60000)
            if tf=="5m" and i==54*3 and volume_5m_extra:
                val+=D(volume_5m_extra)
            high=D(101)
            if tf=="5m" and i==54*3 and wrong_high_5m:
                high+=D(wrong_high_5m)
            w.writerow([stamp,100,high,99,100,str(val),stamp+step-1,
                        str(val*D(100)),int(D(step)/D(60000)),str(val/D(2)),str(val*D(50)),0])
        csvbytes=csvout.getvalue().encode()
        b=io.BytesIO()
        with ZipFile(b,"w",compression=ZIP_DEFLATED) as archive:
            archive.writestr(stem+".csv",csvbytes)
        data=b.getvalue()
        digest=hashlib.sha256(data).hexdigest()
        cache[x.BASE+x.SYMBOL+"/"+tf+"/"+stem+".zip"]=data
        cache[x.BASE+x.SYMBOL+"/"+tf+"/"+stem+".zip.CHECKSUM"]=(("0"*64 if corrupt_checksum else digest)+"  "+stem+".zip\n").encode()
    return lambda url:cache[url]

class ForensicSourceTests(unittest.TestCase):
    def test_four_original_timeframes_identical_on_synthetic_stream(self):
        r=x.run(fetch=stub_fetch())
        self.assertTrue(r["diagnostics"]["strict_ohlc_equal_all_four"])
        self.assertEqual(r["diagnostics"]["anomalous_bucket_count"],0)
        self.assertEqual(r["computed_strategy_trades"],0)
        self.assertFalse(r["can_authorize_modified_c114_gate"])
    def test_5m_volume_mismatch_flagged_not_tolerated_silently(self):
        r=x.run(fetch=stub_fetch(volume_5m_extra="7"))
        z=r["diagnostics"]
        self.assertEqual(z["anomalous_bucket_count"],1)
        self.assertTrue(z["strict_ohlc_equal_all_four"])
        self.assertIn("base_volume",z["known_incident_bucket_1330"]["fields"])
        self.assertEqual(z["known_incident_bucket_1330"]["fields"]["base_volume"]["one_minute_agrees_with"],["3m","15m"])
        self.assertFalse(r["live_approved"])
    def test_5m_high_mismatch_always_flagged(self):
        r=x.run(fetch=stub_fetch(wrong_high_5m="10"))
        self.assertEqual(r["diagnostics"]["ohlc_mismatch_count"],1)
        self.assertFalse(r["diagnostics"]["strict_ohlc_equal_all_four"])
    def test_provided_sha_must_match_binary(self):
        with self.assertRaises(x.ForensicError):
            x.run(fetch=stub_fetch(corrupt_checksum=True))
    def test_no_missing_one_minute_bar(self):
        with self.assertRaises(x.ForensicError):
            x.run(fetch=stub_fetch(omit_one_1m=True))
    def test_fixed_day_and_interval_population(self):
        z=x.run(fetch=stub_fetch())
        self.assertEqual({tf:v["native_rows"] for tf,v in z["receipts"].items()},
                         {"1m":1440,"3m":480,"5m":288,"15m":96})
        self.assertEqual(z["diagnostics"]["total_15m_buckets"],96)
if __name__=="__main__":unittest.main()
