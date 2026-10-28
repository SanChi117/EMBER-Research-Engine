"""C92 original monthly evidence loader adversarial tests; all fixtures synthetic."""
import unittest
from calendar import monthrange
from datetime import datetime,timezone
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
from c92_extended_original_native5m_full_continuous import (
 C92Rejected,MARKETS,MONTHS,_monthly_archive,MAX_ZIP_BYTES,
 TOTAL_MONTHLY,run)
from c89_original_native5m_adaptation_backtest import STEP
def fixture(sym="BTCUSDT",mon="2026-04",truncate=0,offset=0,wrong_name=False):
 yy,mm=map(int,mon.split("-"))
 n=monthrange(yy,mm)[1]*288-truncate
 start=int(datetime(yy,mm,1,tzinfo=timezone.utc).timestamp()*1000)+offset
 lines=(f"{start+i*STEP},100,101,99,100,1\n" for i in range(n))
 data="".join(lines).encode()
 b=BytesIO()
 with ZipFile(b,"w",ZIP_DEFLATED) as z:
  z.writestr((sym+"-5m-"+mon+(".other" if wrong_name else ".csv")),data)
 raw=b.getvalue()
 def fetch(url):
  if url.endswith(".CHECKSUM"):
   return (sha256(raw).hexdigest()+"  "+sym+"-5m-"+mon+".zip\n").encode()
  return raw
 return fetch
class TestC92(unittest.TestCase):
 def test_01_real_month_count_contract(self):
  p,m=_monthly_archive("BTCUSDT","2026-04",fetch=fixture())
  self.assertEqual(len(p),8640);self.assertEqual(m["bars"],8640)
 def test_02_31day_count(self):
  p,m=_monthly_archive("BTCUSDT","2026-05",fetch=fixture(mon="2026-05"))
  self.assertEqual(len(p),8928)
 def test_03_zip_digest_present(self):
  _,m=_monthly_archive("BTCUSDT","2026-04",fetch=fixture())
  self.assertEqual(len(m["zip_sha256"]),64)
 def test_04_provider_checksum_verified(self):
  f=fixture()
  def bad(url):
   return b"0"*64+b"  BTCUSDT-5m-2026-04.zip" if url.endswith(".CHECKSUM") else f(url)
  with self.assertRaises(C92Rejected):
   _monthly_archive("BTCUSDT","2026-04",fetch=bad)
 def test_05_wrong_zip_member(self):
  with self.assertRaises(C92Rejected):
   _monthly_archive("BTCUSDT","2026-04",fetch=fixture(wrong_name=True))
 def test_06_incomplete_month(self):
  with self.assertRaises(C92Rejected):
   _monthly_archive("BTCUSDT","2026-04",fetch=fixture(truncate=1))
 def test_07_shifted_month(self):
  with self.assertRaises(C92Rejected):
   _monthly_archive("BTCUSDT","2026-04",fetch=fixture(offset=STEP))
 def test_08_invalid_symbol(self):
  with self.assertRaises(C92Rejected):
   _monthly_archive("FAKEUSDT","2026-04",fetch=fixture())
 def test_09_unregistered_month(self):
  with self.assertRaises(C92Rejected):
   _monthly_archive("BTCUSDT","2025-04",fetch=fixture())
 def test_10_nonbinary_http_response(self):
  with self.assertRaises(C92Rejected):
   _monthly_archive("BTCUSDT","2026-04",fetch=lambda u:"plain-text")
 def test_11_zero_bytes(self):
  with self.assertRaises(C92Rejected):
   _monthly_archive("BTCUSDT","2026-04",fetch=lambda u:b"")
 def test_12_bad_zip(self):
  def fetch(url):
   return b"badsha BTCUSDT-5m-2026-04.zip" if url.endswith("CHECKSUM") else b"zip"
  with self.assertRaises(C92Rejected):
   _monthly_archive("BTCUSDT","2026-04",fetch=fetch)
 def test_13_expected_5_markets(self):
  self.assertEqual(set(MARKETS),{"BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"})
 def test_14_expected_25_extra(self):
  self.assertEqual(len(MONTHS)*len(MARKETS),TOTAL_MONTHLY)
 def test_15_no_executable_orders(self):
  import inspect
  from c92_extended_original_native5m_full_continuous import load_extended_original
  txt=inspect.getsource(load_extended_original)
  self.assertNotIn("place_order",txt)
 def test_16_no_rr_target(self):
  import inspect
  from c92_extended_original_native5m_full_continuous import run
  self.assertNotIn("fixed_rr",inspect.getsource(run))
if __name__=="__main__":unittest.main()
