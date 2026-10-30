"""C116 source-level adversarial tests, no market outcomes."""
import csv
from decimal import Decimal as D
from hashlib import sha256
from io import BytesIO
import unittest
from zipfile import ZipFile,ZIP_DEFLATED
import c116_original_1m_source_and_exact_resampler as x
import c116_canonical_1m_4h_poi_5m_choch_replay as wrapper
import c114_independent_poi_native5m_choch_research as econ

def rows(count=15,start=0,zip_sha="a"*64):
    return tuple(x.NativeOne("BNBUSDT",start+i*x.MINUTE,start+(i+1)*x.MINUTE,
                             D(100),D(103),D(97),D(100),D(1),zip_sha)
                 for i in range(count))

def fake_zip(date="2025-01-01"):
    from datetime import datetime,timezone
    stem=f"BNBUSDT-1m-{date}"
    start=int(datetime.strptime(date,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
    chunks=[]
    for i in range(1440):
        t=start+i*x.MINUTE
        chunks.append(f"{t},100,101,99,100,1,{t+x.MINUTE-1},100,1,1,100,0")
    csvblob=("\n".join(chunks)+"\n").encode()
    buf=BytesIO()
    with ZipFile(buf,"w",ZIP_DEFLATED) as z:
        z.writestr(stem+".csv",csvblob)
    raw=buf.getvalue()
    digest=sha256(raw).hexdigest()
    def fetch(url):
        return (f"{digest}  {stem}.zip\n").encode() if url.endswith(".CHECKSUM") else raw
    return fetch,digest

class C116OneMinuteContracts(unittest.TestCase):
    def test_three_and_five_derived_from_single_original_minute(self):
        a,b=x.resample(rows())
        self.assertEqual(len(a),5)
        self.assertEqual(len(b),3)
        self.assertTrue(x.verify_joint_15m(a,b)["price_and_volume_equal"])
        self.assertEqual(a[0].source_zip_sha256 if hasattr(a[0],"source_zip_sha256") else a[0].zip_sha,
                         "a"*64)

    def test_source_1m_provenance_never_claims_original_3m5m(self):
        a,b=x.resample(rows())
        self.assertFalse(x.verify_joint_15m(a,b)["independent_original_3m_or_5m_consumed"])

    def test_native_minute_gap_fails(self):
        a=list(rows())
        q=a[6]
        a[6]=x.NativeOne(q.symbol,q.start_ms+x.MINUTE,q.known_ms+x.MINUTE,
                         q.open,q.high,q.low,q.close,q.volume,q.zip_sha256)
        with self.assertRaises(x.C116SourceError):x.resample(tuple(a))

    def test_source_minutes_must_start_at_15m_boundary(self):
        with self.assertRaises(x.C116SourceError):
            x.resample(rows(start=x.MINUTE))

    def test_joined_15m_ohlcv_mismatch_is_fatal(self):
        a,b=x.resample(rows())
        b=list(b);z=b[-1]
        b[-1]=type(z)(z.open_ms,z.o,z.h,D(96),z.c,z.volume)
        with self.assertRaises(x.C116SourceError):x.verify_joint_15m(a,tuple(b))

    def test_daily_original_zip_checksum_and_1440_rows(self):
        fetch,sha=fake_zip()
        bars,meta=x.daily("BNBUSDT","2025-01-01",fetch=fetch)
        self.assertEqual(len(bars),1440)
        self.assertEqual(meta["zip_sha256"],sha)
        self.assertEqual(meta["source_interval"],"ORIGINAL_NATIVE_1M")

    def test_bad_provider_checksum_is_rejected(self):
        fetch,_=fake_zip()
        def changed(url):
            return b"0"*64+b"  BNBUSDT-1m-2025-01-01.zip" if url.endswith("CHECKSUM") else fetch(url)
        with self.assertRaises(x.C116SourceError):
            x.daily("BNBUSDT","2025-01-01",fetch=changed)

    def test_exact_15m_internal_parity_multiple_intervals(self):
        a,b=x.resample(rows(count=30))
        self.assertEqual(x.verify_joint_15m(a,b)["derived_15m_buckets"],2)

    def test_c114_execution_unchanged_and_paper_only(self):
        self.assertEqual(econ.BOOT_SEED,11420261030)
        self.assertEqual(econ.LANDMARK,6*econ.H)
        self.assertEqual(econ.BPS,(14,25,40))
        self.assertFalse(wrapper.canonical_original_1m.__doc__=="Original3m")

if __name__=="__main__":unittest.main()
