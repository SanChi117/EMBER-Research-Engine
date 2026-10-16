"""B1/C16 synthetic/adversarial tests; synthetic fixtures are NEVER market proof."""
from __future__ import annotations
import hashlib,io,sys,unittest,zipfile
from dataclasses import FrozenInstanceError,replace
from decimal import Decimal
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
from c16_c08_monthly_daily_htf_lineage import (
 SEPT_START,OCT_START,END,DAY,TF_MS,HTFSourceRejected,NativeKline,
 NativeSourceArchive,c08_bound_archive,extended_32day_prefix)
S="BTCUSDT"
SHA1="a"*64;SHA2="b"*64;SHA3="c"*64
HASHES=(SHA1,SHA2,SHA3)

def fixture(tf="15m",symbol=S):
    period=TF_MS[tf];width=96 if tf=="15m" else 1
    pieces=[]
    for j,(start,n) in enumerate(((SEPT_START,30*width),(OCT_START,width),(OCT_START+DAY,width))):
        raw=tuple(NativeKline(symbol,tf,start+i*period,start+(i+1)*period,
                              Decimal(100),Decimal(105),Decimal(95),
                              Decimal(100),Decimal(1 if tf=="15m" else 96),
                              HASHES[j]+":"+str(start+i*period),HASHES[j])
                  for i in range(n))
        pieces.append(NativeSourceArchive(symbol,tf,start,
                      OCT_START if j==0 else start+DAY,
                      "https://data.binance.vision/data/futures/um/"+
                      ("monthly" if j==0 else "daily")+
                      f"/klines/{symbol}/{tf}/{symbol}-{tf}-"+
                      ("2026-09" if j==0 else "2026-10-01" if j==1 else "2026-10-02")+".zip",
                      HASHES[j],HASHES[j],raw))
    return tuple(pieces)

def setup():return fixture("15m"),fixture("1d")
def run(a=None,b=None,asof=END):
    x,y=setup()
    return extended_32day_prefix(a if a is not None else x,
                                 b if b is not None else y,asof)

class C16NativeMonthlyDailyHTF(unittest.TestCase):
    def test_32day_original_continuous_five_timeframe_counts(self):
        q=run()
        self.assertEqual(tuple(map(len,(q.native_15m_closed,q.derived_1h_closed,
                              q.derived_4h_closed,q.native_1d_closed))),
                         (3072,768,192,32))
        self.assertEqual(q.crosschecked_native_1d,32)
        self.assertEqual(q.readiness,"NOT_TRADE_READY")
    def test_start_of_first_month_no_future_candle(self):
        q=run(asof=SEPT_START)
        self.assertEqual((len(q.native_15m_closed),len(q.native_1d_closed)),(0,0))
    def test_before_end_of_first_daily_no_known_daily(self):
        q=run(asof=SEPT_START+DAY-900000)
        self.assertEqual(len(q.native_1d_closed),0)
    def test_first_daily_after_full_close(self):
        q=run(asof=SEPT_START+DAY)
        self.assertEqual(len(q.native_1d_closed),1)
    def test_4h_not_closed_at_3h_45m(self):
        q=run(asof=SEPT_START+TF_MS["4h"]-900000)
        self.assertEqual(len(q.derived_4h_closed),0)
    def test_first_4h_at_4h_close(self):
        self.assertEqual(len(run(asof=SEPT_START+TF_MS["4h"]).derived_4h_closed),1)
    def test_september_month_exactly_30_closed_daily(self):
        q=run(asof=OCT_START)
        self.assertEqual((len(q.native_15m_closed),len(q.native_1d_closed),
                         len(q.derived_4h_closed)),(2880,30,180))
    def test_oct_first_close_had_31_daily(self):
        q=run(asof=OCT_START+DAY)
        self.assertEqual(len(q.native_1d_closed),31)
        self.assertEqual(q.native_1d_closed[-1].known_at_ms,OCT_START+DAY)
    def test_oct_second_plus_1h_only_31_days(self):
        q=run(asof=OCT_START+DAY+TF_MS["1h"])
        self.assertEqual((len(q.native_1d_closed),len(q.derived_4h_closed)),(31,186))
    def test_4h_sources_are_sixteen_exact_15m_ids(self):
        q=run()
        self.assertTrue(all(len(x.source_native_15m_rows)==16 for x in q.derived_4h_closed))
    def test_month_day_boundary_has_distinct_archive_sha(self):
        q=run()
        self.assertEqual(q.derived_4h_closed[179].source_native_15m_zip_shas,(SHA1,))
        self.assertEqual(q.derived_4h_closed[180].source_native_15m_zip_shas,(SHA2,))
    def test_derived_4h_volume_not_declared_1d_volume(self):
        q=run()
        self.assertEqual(q.derived_4h_closed[0].volume,Decimal(16))
        self.assertEqual(q.native_1d_closed[0].volume,Decimal(96))
    def test_forged_daily_high_detected_cross_stream(self):
        a,b=setup();monthly=list(b[0].rows)
        monthly[1]=replace(monthly[1],high=Decimal(130))
        with self.assertRaisesRegex(HTFSourceRejected,"NATIVE_1D_VS_DERIVED_15M_OHLCV_MISMATCH"):
            run(a=a,b=(replace(b[0],rows=tuple(monthly)),)+b[1:])
    def test_forged_daily_volume_detected_cross_stream(self):
        a,b=setup();monthly=list(b[0].rows)
        monthly[1]=replace(monthly[1],volume=Decimal(98))
        with self.assertRaisesRegex(HTFSourceRejected,"NATIVE_1D_VS_DERIVED_15M_OHLCV_MISMATCH"):
            run(a=a,b=(replace(b[0],rows=tuple(monthly)),)+b[1:])
    def test_source_interval_gap_rejected(self):
        a,b=setup();monthly=list(a[0].rows)
        monthly[6]=replace(monthly[6],start_ms=monthly[6].start_ms+900000)
        with self.assertRaisesRegex(HTFSourceRejected,"SOURCE_CANDLE_ROW_LINEAGE_OR_GRID_MISMATCH"):
            run(a=(replace(a[0],rows=tuple(monthly)),)+a[1:],b=b)
    def test_source_id_mismatch_rejected(self):
        a,b=setup();monthly=list(a[0].rows)
        monthly[6]=replace(monthly[6],origin_raw_row_id="FORGED")
        with self.assertRaisesRegex(HTFSourceRejected,"SOURCE_CANDLE_ROW_LINEAGE_OR_GRID_MISMATCH"):
            run(a=(replace(a[0],rows=tuple(monthly)),)+a[1:],b=b)
    def test_zip_sha_mismatch_from_rows_rejected(self):
        a,b=setup();monthly=list(a[0].rows)
        monthly[6]=replace(monthly[6],origin_zip_sha256="e"*64)
        with self.assertRaisesRegex(HTFSourceRejected,"SOURCE_CANDLE_ROW_LINEAGE_OR_GRID_MISMATCH"):
            run(a=(replace(a[0],rows=tuple(monthly)),)+a[1:],b=b)
    def test_cross_symbol_rejected(self):
        with self.assertRaisesRegex(HTFSourceRejected,"MIXED_MARKET_OR_SYMBOL"):
            run(a=fixture("15m"),b=fixture("1d","ETHUSDT"))
    def test_duplicate_month_source_rejected(self):
        a,b=setup()
        with self.assertRaisesRegex(HTFSourceRejected,"INVALID_ARCHIVE_PERIOD_SIZE"):
            run(a=(a[0],a[0],a[2]),b=b)
    def test_missing_month_source_rejected(self):
        a,b=setup()
        with self.assertRaisesRegex(HTFSourceRejected,"MISSING_REQUIRED_MONTH_AND_TWO_DAYS"):
            run(a=a[1:],b=b)
    def test_missing_september_kline_rejected(self):
        a,b=setup()
        with self.assertRaisesRegex(HTFSourceRejected,"INVALID_ARCHIVE_PERIOD_SIZE"):
            run(a=(replace(a[0],rows=a[0].rows[:-1]),)+a[1:],b=b)
    def test_wrong_tf_archive_rejected(self):
        a,b=setup()
        with self.assertRaisesRegex(HTFSourceRejected,"INVALID_NATIVE_TIMEFRAME_ARCHIVE_SET"):
            run(a=a,b=(replace(b[0],tf="15m"),)+b[1:])
    def test_unauthorized_ready_field_rejected(self):
        a,b=setup()
        with self.assertRaisesRegex(HTFSourceRejected,"INVALID_NATIVE_TIMEFRAME_ARCHIVE_SET"):
            run(a=(replace(a[0],readiness="READY"),)+a[1:],b=b)
    def test_asof_after_history_rejected(self):
        with self.assertRaisesRegex(HTFSourceRejected,"INVALID_OR_FUTURE_ASOF"):
            run(asof=END+900000)
    def test_asof_incomplete_15m_rejected(self):
        with self.assertRaisesRegex(HTFSourceRejected,"INVALID_OR_FUTURE_ASOF"):
            run(asof=OCT_START+1)
    def test_no_future_leak_when_oct2_source_changes(self):
        a,b=setup()
        altered=list(a[2].rows)
        altered[0]=replace(altered[0],high=Decimal(300))
        future=(a[0],a[1],replace(a[2],rows=tuple(altered)))
        past=run(a=a,b=b,asof=OCT_START)
        other=run(a=future,b=b,asof=OCT_START)
        self.assertEqual(past,other)
    def test_past_never_affected_by_later_1d_discrepancy(self):
        a,b=setup()
        later=list(b[2].rows)
        later[0]=replace(later[0],volume=Decimal(110))
        y=(b[0],b[1],replace(b[2],rows=tuple(later)))
        prior=run(a=a,b=b,asof=OCT_START)
        other=run(a=a,b=y,asof=OCT_START)
        self.assertEqual(prior,other)
    def test_frozen_output_cannot_be_trade_ready(self):
        q=run()
        with self.assertRaises(FrozenInstanceError):
            q.readiness="READY"
        with self.assertRaises(FrozenInstanceError):
            q.derived_4h_closed[0].author_status="AUTHOR_APPROVED"
    def test_unknown_symbol_rejected(self):
        a,b=setup()
        with self.assertRaisesRegex(HTFSourceRejected,"MIXED_MARKET_OR_SYMBOL"):
            run(a=fixture("15m","FAKEUSDT"),b=fixture("1d","FAKEUSDT"))
    def test_c08_archive_requires_checksum_and_exact_receipt_sha(self):
        url="https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-02.zip"
        name="BTCUSDT-1d-2026-10-02.csv"
        start=OCT_START+DAY
        csvrow=f"{start},100,110,90,100,2,{start+DAY-1},200,1,1,1,0\n"
        bio=io.BytesIO()
        with zipfile.ZipFile(bio,"w",zipfile.ZIP_DEFLATED) as z:z.writestr(name,csvrow)
        data=bio.getvalue()
        digest=hashlib.sha256(data).hexdigest()
        checksum=f"{digest}  BTCUSDT-1d-2026-10-02.zip\n".encode()
        # A fully self-declared fixture can pass mechanical receipt matching,
        # but this is NOT actual Git-pinned C08 provenance!
        mock={"url":url,"status":"HTTPS_CHECKSUM_AND_ALL_COLUMNS_REPLAYED",
              "normalized_all_11_columns_matched":True,"symbol":"BTCUSDT",
              "tf":"1d","rows":1,"zip_sha256":digest,
              "raw_csv_sha256":hashlib.sha256(csvrow.encode()).hexdigest()}
        p=c08_bound_archive(url,data,checksum,mock)
        self.assertEqual(len(p.rows),1)
        self.assertEqual(p.rows[0].known_at_ms,start+DAY)
        with self.assertRaisesRegex(HTFSourceRejected,"NOT_AN_IMMUTABLE_C08_RECEIPT_MATCH"):
            c08_bound_archive(url,data,checksum,dict(mock,zip_sha256="0"*64))
        with self.assertRaisesRegex(HTFSourceRejected,"NOT_VALID_ORIGINAL_C08_BINANCE_ARCHIVE"):
            c08_bound_archive(url,data,checksum.replace(digest.encode(),b"0"*64),mock)
if __name__=="__main__":
    unittest.main(verbosity=2)
