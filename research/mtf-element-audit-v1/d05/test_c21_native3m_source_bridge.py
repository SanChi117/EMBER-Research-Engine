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

from c21_native3m_source_bridge import reconcile_native_3m,END
from test_c20_original_32day_native5m_lineage import parsed,review

class C21ExactPriceParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=tuple(read_original_3m(*sample(p),symbol=SYM,period=p)
                    for p in PERIODS)
        fives=tuple(x for p in PERIODS for x in parsed(p).rows)
        cls.c08=review(fives)

    def test_original_three_to_fifteen_ohlcv(self):
        result=reconcile_native_3m(self.a,self.c08,as_of_ms=END)
        self.assertEqual(len(result.original_3m_closed),15360)
        self.assertEqual(result.native_15m_ohlcv_equalities,3072)
        self.assertEqual(result.native_1d_equalities,32)
        self.assertEqual(result.author_bos_approved,result.trade_approved)
        self.assertEqual(result.readiness,"NOT_TRADE_READY")

    def test_closed_3m_prefix(self):
        cut=STARTS[2]+THREE
        r=reconcile_native_3m(self.a,self.c08,as_of_ms=cut)
        self.assertEqual(len(r.original_3m_closed),31*480+1)
        self.assertEqual(r.original_3m_closed[-1].known_ms,cut)

    def test_source_3m_price_mutation_rejected(self):
        first=self.a[0]
        r=replace(first.rows[10],high=first.rows[10].high+1)
        change=replace(first,rows=first.rows[:10]+(r,)+first.rows[11:])
        with self.assertRaisesRegex(C21Rejected,"OHLCV_DRIFT"):
            reconcile_native_3m((change,)+self.a[1:],self.c08,as_of_ms=END)

    def test_missing_source_row_rejected(self):
        first=self.a[0]
        with self.assertRaisesRegex(C21Rejected,"INCOMPLETE_3M_SOURCE_ROWS"):
            reconcile_native_3m((replace(first,rows=first.rows[:-1]),)+self.a[1:],
                                self.c08,as_of_ms=END)

    def test_source_future_asof_rejected(self):
        with self.assertRaisesRegex(C21Rejected,"FUTURE_OR_NONCLOSED"):
            reconcile_native_3m(self.a,self.c08,as_of_ms=END+THREE)

    def test_3m_source_cannot_upgrade_author_ready(self):
        x=replace(self.a[1],readiness="READY")
        with self.assertRaisesRegex(C21Rejected,"WRONG_ORIGINAL_3M_ARCHIVE"):
            reconcile_native_3m((self.a[0],x,self.a[2]),self.c08,as_of_ms=END)
