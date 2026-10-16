"""C21A original 3m source negatives; synthetic rows are not goldens."""
from __future__ import annotations
import hashlib,io,unittest,zipfile
from dataclasses import replace
from c21_native3m_source_bridge import (
    checked_url,read_original_3m,C21Rejected,PERIODS,STARTS,THREE,DAY)
SYM="BTCUSDT"

def sample(period="2026-10-01",modify=None,extra=False):
    url=checked_url(SYM,period)
    n=(30*DAY if period=="2026-09" else DAY)//THREE
    base=STARTS[PERIODS.index(period)]
    rows=[f"{base+i*THREE},100,101,99,100,0.6,{base+(i+1)*THREE-1},101,3,0.5,50,0"
          for i in range(n)]
    if modify is not None:modify(rows)
    name=url.rsplit("/",1)[-1]
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(name[:-4]+".csv","\n".join(rows)+"\n")
        if extra:z.writestr("rogue.csv","bad")
    binary=buff.getvalue()
    check=(hashlib.sha256(binary).hexdigest()+"  "+name).encode()
    return url,binary,check

class C21SourceNegatives(unittest.TestCase):
    def test_daily_480_contiguous_native_3m(self):
        url,raw,checksum=sample()
        x=read_original_3m(url,raw,checksum,symbol=SYM,period="2026-10-01")
        self.assertEqual(len(x.rows),480)
        self.assertEqual(x.rows[0].known_ms,STARTS[1]+THREE)
        self.assertEqual(x.rows[-1].known_ms,STARTS[2])
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_wrong_host_rejected(self):
        url,raw,check=sample()
        with self.assertRaisesRegex(C21Rejected,"UNTRUSTED"):
            read_original_3m(url.replace("data.binance.vision","evil.invalid"),
                             raw,check,symbol=SYM,period="2026-10-01")
    def test_wrong_3m_checksum_rejected(self):
        url,raw,check=sample()
        with self.assertRaisesRegex(C21Rejected,"ZIP_SHA_MISMATCH"):
            read_original_3m(url,raw,("0"*64+"  BTCUSDT-3m-2026-10-01.zip").encode(),
                             symbol=SYM,period="2026-10-01")
    def test_missing_grid_candle_rejected(self):
        url,raw,check=sample(modify=lambda r:r.pop())
        with self.assertRaisesRegex(C21Rejected,"INCOMPLETE_3M"):
            read_original_3m(url,raw,check,symbol=SYM,period="2026-10-01")
    def test_extra_zip_member_rejected(self):
        url,raw,check=sample(extra=True)
        with self.assertRaisesRegex(C21Rejected,"UNSAFE_ORIGINAL_3M_ZIP"):
            read_original_3m(url,raw,check,symbol=SYM,period="2026-10-01")

    def test_wrong_period_rejected(self):
        url,raw,check=sample()
        with self.assertRaisesRegex(C21Rejected,"UNTRUSTED"):
            read_original_3m(url,raw,check,symbol=SYM,period="2026-10-02")

    def test_gap_in_original_csv_rejected(self):
        def modify(r):r[7]=r[8]
        url,raw,check=sample(modify=modify)
        with self.assertRaisesRegex(C21Rejected,"GAPPED"):
            read_original_3m(url,raw,check,symbol=SYM,period="2026-10-01")

    def test_nonfinite_ohlcv_rejected(self):
        def modify(r):r[0]=r[0].replace(",100,101,99,",",nan,101,99,")
        url,raw,check=sample(modify=modify)
        with self.assertRaisesRegex(C21Rejected,"NONFINITE"):
            read_original_3m(url,raw,check,symbol=SYM,period="2026-10-01")

    def test_source_column_count_rejected(self):
        def modify(r):r[4]+=",extraneous"
        url,raw,check=sample(modify=modify)
        with self.assertRaisesRegex(C21Rejected,"12_COLUMNS"):
            read_original_3m(url,raw,check,symbol=SYM,period="2026-10-01")
