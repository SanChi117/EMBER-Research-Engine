"""Synthetic C20 adversarial tests. NOT author-labelled Binance Futures goldens."""
from __future__ import annotations
import unittest,io,zipfile,hashlib
from dataclasses import replace
from decimal import Decimal as D
from c20_original_32day_native5m_lineage import (
    C20Rejected,parse_original_native5m,reconcile_32day_native5m,MONTH_ROW_COUNT,
    FIVE,DATES,SLOTS,END,NativeFiveMinute)
from c16_c08_monthly_daily_htf_lineage import (
    NativeKline,ExtendedHTFReview,_combine,DAY)
SYM="BTCUSDT"
SHA15="b"*64
BASE="https://data.binance.vision/data/futures/um/"

def data(period="2026-09",symbol=SYM):
    name=f"{symbol}-5m-{period}"
    url=f"{BASE}{'monthly' if period=='2026-09' else 'daily'}/klines/{symbol}/5m/{name}.zip"
    start=SLOTS[DATES.index(period)]
    n=MONTH_ROW_COUNT if period=="2026-09" else DAY//FIVE
    rows=[f"{start+i*FIVE},100,101,99,100,1,{start+(i+1)*FIVE-1},101,3,0.5,50,0"
          for i in range(n)]
    return url,rows

def zipped(name,rows,extra=False):
    o=io.BytesIO()
    with zipfile.ZipFile(o,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(name+".csv","\n".join(rows)+"\n")
        if extra:z.writestr("bad.csv","x")
    raw=o.getvalue()
    return raw,(hashlib.sha256(raw).hexdigest()+"  "+name+".zip").encode()

def parsed(period,rows=None,extra=False):
    url,standard=data(period)
    name=url.rsplit("/",1)[-1][:-4]
    raw,sha=zipped(name,standard if rows is None else rows,extra)
    return parse_original_native5m(url,raw,sha,symbol=SYM,period=period)

def review(original):
    bars=[]
    for i in range(0,len(original),3):
        three=original[i:i+3]
        at=three[0].start_ms
        bars.append(NativeKline(SYM,"15m",at,three[-1].known_at_ms,
                   three[0].open,max(x.high for x in three),
                   min(x.low for x in three),three[-1].close,
                   sum((x.volume for x in three),D(0)),
                   SHA15+":"+str(at),SHA15))
    native15=tuple(bars)
    h=tuple(_combine(native15[i:i+4],"1h") for i in range(0,len(native15),4))
    f=tuple(_combine(native15[i:i+16],"4h") for i in range(0,len(native15),16))
    daily_derived=tuple(_combine(native15[i:i+96],"1d") for i in range(0,len(native15),96))
    native_daily=tuple(NativeKline(SYM,"1d",x.start_ms,x.known_at_ms,x.open,x.high,x.low,
        x.close,x.volume,SHA15+":"+str(x.start_ms),SHA15) for x in daily_derived)
    return ExtendedHTFReview(SYM,END,native15,native_daily,h,f,len(native_daily))

class C20OriginalLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=parsed("2026-09")
        cls.b=parsed("2026-10-01")
        cls.c=parsed("2026-10-02")
        cls.three=(cls.a,cls.b,cls.c)
        cls.all=tuple(x for ar in cls.three for x in ar.rows)
        cls.source=review(cls.all)
    def test_monthly_original_8640_rows(self):
        self.assertEqual(len(self.a.rows),8640)
        self.assertEqual(self.a.rows[0].start_ms,SLOTS[0])
        self.assertEqual(self.a.rows[-1].known_at_ms,SLOTS[1])
    def test_oct_two_native_288_complete_days(self):
        self.assertEqual(len(self.b.rows),288)
        self.assertEqual(self.c.rows[-1].known_at_ms,END)
    def test_month_has_unique_zip_and_raw_csv_sha(self):
        self.assertEqual(len({x.zip_sha256 for x in self.three}),3)
        self.assertTrue(all(len(x.raw_csv_sha256)==64 for x in self.three))
    def test_exact_3072_native_c08_15m_triples(self):
        x=reconcile_32day_native5m(self.three,self.source,as_of_ms=END)
        self.assertEqual(len(x.original_5m_closed),9216)
        self.assertEqual(x.original_15m_equalities,3072)
        self.assertEqual(x.verified_original_1d_equalities,32)
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
        self.assertEqual(x.bos_status,"BOS_5M_NOT_YET_AUTHOR_CERTIFIED")
    def test_prefix_5m_asof_stricter_than_15m(self):
        t=SLOTS[1]+FIVE
        x=reconcile_32day_native5m(self.three,self.source,as_of_ms=t)
        self.assertEqual(len(x.original_5m_closed),8641)
        self.assertEqual(x.original_5m_closed[-1].known_at_ms,t)
        self.assertEqual(x.original_15m_equalities,3072)
    def test_future_5m_asof_rejected(self):
        with self.assertRaisesRegex(C20Rejected,"NOT_A_CLOSED_5M_ASOF"):
            reconcile_32day_native5m(self.three,self.source,as_of_ms=END+FIVE)
    def test_unclosed_5m_asof_rejected(self):
        with self.assertRaisesRegex(C20Rejected,"NOT_A_CLOSED_5M_ASOF"):
            reconcile_32day_native5m(self.three,self.source,as_of_ms=END-1)
    def test_missing_sept_archive_rejected(self):
        with self.assertRaisesRegex(C20Rejected,"MISSING_NATIVE_SEPTEMBER_PLUS_OCTOBER_5M"):
            reconcile_32day_native5m(self.three[1:],self.source,as_of_ms=END)
    def test_mismatched_archive_zip_sha_rejected(self):
        a=replace(self.b,zip_sha256="c"*64)
        with self.assertRaisesRegex(C20Rejected,"ALTERED_GAPPED_OR_FORGED_ORIGINAL_5M_ROW"):
            reconcile_32day_native5m((self.a,a,self.c),self.source,as_of_ms=END)
    def test_fake_source_author_ready_rejected(self):
        a=replace(self.b,readiness="READY")
        with self.assertRaisesRegex(C20Rejected,"WRONG_SYMBOL_OR_5M_ARCHIVE_SET"):
            reconcile_32day_native5m((self.a,a,self.c),self.source,as_of_ms=END)
    def test_mutated_native5m_price_vs_15m_parity(self):
        row=self.a.rows[300]
        altered=replace(row,high=D(120))
        a=replace(self.a,rows=self.a.rows[:300]+(altered,)+self.a.rows[301:])
        with self.assertRaisesRegex(C20Rejected,"NATIVE_5M_VS_C08_15M_OHLCV_PARITY_FAIL"):
            reconcile_32day_native5m((a,self.b,self.c),self.source,as_of_ms=END)
    def test_altered_original15m_c08_price_rejected(self):
        s=self.source
        change=replace(s.native_15m_closed[0],high=D(102))
        with self.assertRaisesRegex(C20Rejected,"INVALID_NATIVE_15M_C08_LINEAGE"):
            reconcile_32day_native5m(self.three,replace(s,native_15m_closed=(change,)+s.native_15m_closed[1:]),as_of_ms=END)
    def test_missing_5m_bar_rejected(self):
        a=replace(self.a,rows=self.a.rows[:-1])
        with self.assertRaisesRegex(C20Rejected,"INCOMPLETE_5M_ROWS_FOR_SOURCE_PERIOD"):
            reconcile_32day_native5m((a,self.b,self.c),self.source,as_of_ms=END)
    def test_5m_source_timestamp_mutation_rejected(self):
        row=self.a.rows[10]
        a=replace(self.a,rows=self.a.rows[:10]+(replace(row,start_ms=row.start_ms+FIVE),)+self.a.rows[11:])
        with self.assertRaisesRegex(C20Rejected,"ALTERED_GAPPED_OR_FORGED_ORIGINAL_5M_ROW"):
            reconcile_32day_native5m((a,self.b,self.c),self.source,as_of_ms=END)
    def test_untrusted_host_rejected(self):
        url,rs=data()
        name="BTCUSDT-5m-2026-09"
        raw,sha=zipped(name,rs)
        with self.assertRaisesRegex(C20Rejected,"UNTRUSTED_5M_ARCHIVE_HOST_OR_PATH"):
            parse_original_native5m(url.replace("data.binance.vision","evil.test"),raw,sha,symbol=SYM,period="2026-09")
    def test_wrong_market_path_rejected(self):
        url,rs=data()
        raw,sha=zipped("BTCUSDT-5m-2026-09",rs)
        with self.assertRaisesRegex(C20Rejected,"WRONG_5M_MARKET_SYMBOL_OR_ARCHIVE_PERIOD"):
            parse_original_native5m(url.replace("/futures/um/","/spot/"),raw,sha,symbol=SYM,period="2026-09")
    def test_checksum_corruption_rejected(self):
        url,rs=data()
        raw,_=zipped("BTCUSDT-5m-2026-09",rs)
        with self.assertRaisesRegex(C20Rejected,"WRONG_5M_ZIP_SHA_OR_CHECKSUM"):
            parse_original_native5m(url,raw,("f"*64+"  BTCUSDT-5m-2026-09.zip").encode(),symbol=SYM,period="2026-09")
    def test_wrong_month_5m_archive_size_rejected(self):
        url,rs=data()
        raw,sha=zipped("BTCUSDT-5m-2026-09",rs[:-1])
        with self.assertRaisesRegex(C20Rejected,"INCOMPLETE_NATIVE_5M_PERIOD"):
            parse_original_native5m(url,raw,sha,symbol=SYM,period="2026-09")
    def test_gap_inside_real_csv_rejected(self):
        url,rs=data()
        rs[1]=rs[1].replace(str(SLOTS[0]+FIVE),str(SLOTS[0]+2*FIVE),1)
        raw,sha=zipped("BTCUSDT-5m-2026-09",rs)
        with self.assertRaisesRegex(C20Rejected,"GAPPED_OR_UNCLOSED_5M_SOURCE_GRID"):
            parse_original_native5m(url,raw,sha,symbol=SYM,period="2026-09")
    def test_more_than_one_zip_member_rejected(self):
        url,rs=data()
        raw,sha=zipped("BTCUSDT-5m-2026-09",rs,extra=True)
        with self.assertRaisesRegex(C20Rejected,"UNSAFE_5M_ZIP_MEMBER"):
            parse_original_native5m(url,raw,sha,symbol=SYM,period="2026-09")
    def test_cross_symbol_rejected(self):
        with self.assertRaisesRegex(C20Rejected,"WRONG_SYMBOL_OR_5M_ARCHIVE_SET"):
            reconcile_32day_native5m((self.a,replace(self.b,symbol="ETHUSDT"),self.c),self.source,as_of_ms=END)
    def test_nonfinite_price_rejected(self):
        url,rs=data()
        rs[0]=rs[0].replace(",100,101,99,100,",",nan,101,99,100,",1)
        raw,sha=zipped("BTCUSDT-5m-2026-09",rs)
        with self.assertRaisesRegex(C20Rejected,"NONFINITE_5M_NATIVE_NUMBER"):
            parse_original_native5m(url,raw,sha,symbol=SYM,period="2026-09")
    def test_self_declared_approved_c16_rejected(self):
        with self.assertRaisesRegex(C20Rejected,"INVALID_NATIVE_15M_C08_LINEAGE"):
            reconcile_32day_native5m(self.three,replace(self.source,readiness="READY"),as_of_ms=END)
if __name__=="__main__":unittest.main()
