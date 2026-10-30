import csv,hashlib,io,unittest
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime, timezone
from unittest.mock import patch
from decimal import Decimal as D
import c114_monthly_vs_daily_4tf_forensic as m

def fake_15m(*,volume="15",corrupt=False,skip=False):
    out=io.StringIO();w=csv.writer(out)
    start=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)
    count=31*96-(1 if skip else 0)
    for i in range(count):
        t=start+i*900000
        w.writerow([t,100,101,99,100,volume,t+899999,
                    "1500",15,"7.5","750",0])
    stem="BNBUSDT-15m-2025-01"
    buff=io.BytesIO()
    with ZipFile(buff,"w",compression=ZIP_DEFLATED) as z:
        z.writestr(stem+".csv",out.getvalue().encode())
    data=buff.getvalue()
    sha=hashlib.sha256(data).hexdigest()
    base="https://data.binance.vision/data/futures/um/monthly/klines/BNBUSDT/15m/"
    return lambda url:{base+stem+".zip":data,base+stem+".zip.CHECKSUM":(("0"*64 if corrupt else sha)+"  "+stem+".zip").encode()}[url]

class MonthlyForensicTests(unittest.TestCase):
    def test_real_monthly_calendar_and_single_day_extraction(self):
        z,r=m.monthly("15m",fetch=fake_15m())
        self.assertEqual(len(z),96)
        self.assertEqual(r["month_rows"],2976)
        self.assertEqual(z[0]["start_ms"],1736812800000)
        self.assertEqual(z[54]["base_volume"],D(15))
        self.assertEqual(z[-1]["end_ms"],1736899200000)
    def test_monthly_provider_checksum_cannot_be_skipped(self):
        with self.assertRaises(m.MonthlyForensicError):m.monthly("15m",fetch=fake_15m(corrupt=True))
    def test_monthly_no_truncated_rows(self):
        with self.assertRaises(m.MonthlyForensicError):m.monthly("15m",fetch=fake_15m(skip=True))
    def test_monthly_no_unregistered_tf(self):
        with self.assertRaises(m.MonthlyForensicError):m.monthly("2m",fetch=fake_15m())
if __name__=="__main__":unittest.main()
