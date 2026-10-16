"""B1/C15: multi-TF original Futures 5m -> 15m/1h/4h/1d strict as-of tests."""
from __future__ import annotations
from dataclasses import FrozenInstanceError,replace
from decimal import Decimal
from pathlib import Path
import sys,unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parents[1]/"mtf-course-v05"/"src"))
from test_c10_two_day_original_5m_context import make,T,DAY,PERIOD
from c15_closed_multi_tf_source_grid import (
    closed_mtf_prefix,MtfLineageRejected,TF_MS)

def source():
    return make(0),make(1)
def scan(at=T+2*DAY,first=None,second=None):
    a,b=source()
    return closed_mtf_prefix(a if first is None else first,
                             b if second is None else second,at)

class C15OriginalMultiTf(unittest.TestCase):
    def test_full_2day_five_level_closed_counts(self):
        q=scan()
        self.assertEqual([len(q.candles(t)) for t in ("5m","15m","1h","4h","1d")],
                         [576,192,48,12,2])
        self.assertEqual(q.readiness,"NOT_TRADE_READY")
    def test_daily_two_candles_cannot_claim_htf_context(self):
        q=scan()
        self.assertEqual(q.daily_coverage,"TWO_DAILY_CANDLES_INSUFFICIENT_AUTHOR_HTF_CONTEXT")
        self.assertEqual(q.author_route_status,"NO_AUTHOR_LABELLED_PARENT_POI_STRONGHL_OR_VC")
    def test_midnight_first_daily_only(self):
        q=scan(at=T+DAY)
        self.assertEqual([len(q.candles(t)) for t in ("5m","15m","1h","4h","1d")],
                         [288,96,24,6,1])
        self.assertEqual(q.daily_coverage,"ONE_DAILY_CANDLE_INSUFFICIENT_AUTHOR_HTF_CONTEXT")
    def test_before_first_midnight_zero_daily(self):
        q=scan(at=T+DAY-PERIOD)
        self.assertEqual(len(q.candles("1d")),0)
        self.assertEqual(q.daily_coverage,"NO_CLOSED_DAILY_CANDLE")
    def test_at_first_open_no_candles(self):
        q=scan(at=T)
        self.assertTrue(all(len(q.candles(tf))==0 for tf in TF_MS))
    def test_asof_partial_second_day_precise_closed_counts(self):
        q=scan(at=T+DAY+6*3600000+15*60000)
        self.assertEqual([len(q.candles(t)) for t in TF_MS],[363,121,30,7,1])
    def test_no_4h_candle_before_4h_close(self):
        q=scan(at=T+4*3600000-PERIOD)
        self.assertEqual(len(q.candles("4h")),0)
    def test_first_4h_on_4h_close(self):
        q=scan(at=T+4*3600000)
        self.assertEqual(len(q.candles("4h")),1)
    def test_no_1h_before_first_hour_closed(self):
        self.assertEqual(len(scan(at=T+3600000-PERIOD).candles("1h")),0)
    def test_first_15m_after_three_original_5m(self):
        self.assertEqual(len(scan(at=T+2*PERIOD).candles("15m")),0)
        self.assertEqual(len(scan(at=T+3*PERIOD).candles("15m")),1)
    def test_1d_is_exactly_288_sources(self):
        q=scan()
        self.assertTrue(all(len(d.source_5m_ids)==288 for d in q.candles("1d")))
    def test_each_4h_has_48_5m_sources_and_known_at(self):
        q=scan()
        self.assertTrue(all(len(d.source_5m_ids)==48 and
                            d.known_at_ms==d.start_ms+TF_MS["4h"] for d in q.candles("4h")))
    def test_closed_5m_source_exactly_matches_single_bar(self):
        q=scan()
        a=source()[0]
        self.assertEqual(q.candles("5m")[0].source_5m_ids,(a.rows[0].raw_id,))
        self.assertEqual(q.candles("5m")[0].archive_zip_sha256s,(a.zip_sha256,))
    def test_utc_day_boundary_keeps_only_correct_native_archive(self):
        q=scan()
        a,b=source()
        self.assertEqual(q.candles("1d")[0].archive_zip_sha256s,(a.zip_sha256,))
        self.assertEqual(q.candles("1d")[1].archive_zip_sha256s,(b.zip_sha256,))
    def test_decimal_aggregation_volume_15m_1h_4h_1d(self):
        q=scan()
        self.assertEqual([q.candles(t)[0].volume for t in TF_MS],
                         [Decimal("1"),Decimal("3"),Decimal("12"),
                          Decimal("48"),Decimal("288")])
    def test_high_low_wick_aggregation_preserves_raw_extremes(self):
        a,b=source()
        c=make(1,override={3:(100,130,90,102)})
        q=scan(first=a,second=c)
        candle=q.candles("4h")[6]
        self.assertEqual((candle.high,candle.low),(Decimal("130"),Decimal("90")))
    def test_no_future_suffix_lookahead_in_first_day(self):
        a,b=source()
        future=make(1,override={200:(100,145,95,100)})
        x=scan(at=T+DAY,first=a,second=b)
        y=scan(at=T+DAY,first=a,second=future)
        for tf in TF_MS:
            self.assertEqual(x.candles(tf),y.candles(tf))
    def test_mutated_csv_close_rejected_before_aggregation(self):
        a,b=source();rows=list(b.rows)
        fake=list(rows[4].original_csv_row);fake[4]="80"
        rows[4]=replace(rows[4],original_csv_row=tuple(fake))
        with self.assertRaisesRegex(MtfLineageRejected,"RAW_CSV_5M_BAR_CONTRADICTION"):
            scan(first=a,second=replace(b,rows=tuple(rows)))
    def test_mutated_csv_volume_rejected(self):
        a,b=source();rows=list(b.rows)
        fake=list(rows[4].original_csv_row);fake[5]="900"
        rows[4]=replace(rows[4],original_csv_row=tuple(fake))
        with self.assertRaisesRegex(MtfLineageRejected,"RAW_CSV_5M_BAR_CONTRADICTION"):
            scan(first=a,second=replace(b,rows=tuple(rows)))
    def test_mutated_csv_timestamp_rejected(self):
        a,b=source();rows=list(b.rows)
        fake=list(rows[4].original_csv_row);fake[0]="0"
        rows[4]=replace(rows[4],original_csv_row=tuple(fake))
        with self.assertRaisesRegex(MtfLineageRejected,"RAW_CSV_5M_BAR_CONTRADICTION"):
            scan(first=a,second=replace(b,rows=tuple(rows)))
    def test_malformed_raw_row_rejected(self):
        a,b=source();rows=list(b.rows)
        rows[4]=replace(rows[4],original_csv_row=("a","b"))
        with self.assertRaisesRegex(MtfLineageRejected,"INVALID_ORIGINAL_CSV_FIELDS"):
            scan(first=a,second=replace(b,rows=tuple(rows)))
    def test_nan_volume_rejected(self):
        a,b=source();rows=list(b.rows)
        raw=list(rows[4].original_csv_row);raw[5]="NaN"
        rows[4]=replace(rows[4],original_csv_row=tuple(raw))
        with self.assertRaisesRegex(MtfLineageRejected,"NONFINITE_RAW_OHLCV"):
            scan(first=a,second=replace(b,rows=tuple(rows)))
    def test_bad_row_volume_negative_rejected(self):
        a,b=source();rows=list(b.rows)
        raw=list(rows[4].original_csv_row);raw[5]="-10"
        rows[4]=replace(rows[4],original_csv_row=tuple(raw),volume=Decimal("-10"))
        with self.assertRaisesRegex(MtfLineageRejected,"RAW_CSV_5M_BAR_CONTRADICTION"):
            scan(first=a,second=replace(b,rows=tuple(rows)))
    def test_price_outside_high_low_rejected(self):
        a,b=source();rows=list(b.rows)
        raw=list(rows[4].original_csv_row);raw[2]="50"
        rows[4]=replace(rows[4],original_csv_row=tuple(raw))
        with self.assertRaisesRegex(MtfLineageRejected,"RAW_CSV_5M_BAR_CONTRADICTION"):
            scan(first=a,second=replace(b,rows=tuple(rows)))
    def test_source_self_claiming_approved_rejected(self):
        a,b=source()
        with self.assertRaisesRegex(MtfLineageRejected,"FORGED_SOURCE_ACADEMIC_READY"):
            scan(first=replace(a,readiness="READY"),second=b)
    def test_source_self_claiming_vc_rejected(self):
        a,b=source()
        with self.assertRaisesRegex(MtfLineageRejected,"FORGED_SOURCE_ACADEMIC_READY"):
            scan(first=replace(a,academic_status="AUTHOR_VC_APPROVED"),second=b)
    def test_different_market_symbols_rejected(self):
        with self.assertRaisesRegex(MtfLineageRejected,"INVALID_TWO_DAY_OR_ASOF_SOURCE"):
            scan(first=make(0),second=make(1,symbol="ETHUSDT"))
    def test_same_day_duplicate_rejected(self):
        with self.assertRaisesRegex(MtfLineageRejected,"INVALID_TWO_DAY_OR_ASOF_SOURCE"):
            scan(first=make(0),second=make(0))
    def test_wrong_future_asof_rejected(self):
        with self.assertRaisesRegex(MtfLineageRejected,"INVALID_TWO_DAY_OR_ASOF_SOURCE"):
            scan(at=T+2*DAY+PERIOD)
    def test_partial_five_minute_asof_rejected(self):
        with self.assertRaisesRegex(MtfLineageRejected,"INVALID_TWO_DAY_OR_ASOF_SOURCE"):
            scan(at=T+DAY+PERIOD+1)
    def test_no_other_timeframe_route_introduced(self):
        with self.assertRaisesRegex(MtfLineageRejected,"UNKNOWN_TIMEFRAME"):
            scan().candles("2h")
    def test_return_is_frozen_never_ready(self):
        q=scan()
        with self.assertRaises(FrozenInstanceError):
            q.readiness="READY"
        with self.assertRaises(FrozenInstanceError):
            q.candles("1d")[0].price_source_status="NATIVE_BINANCE_1D_AUTHOR_APPROVED"

if __name__=="__main__":
    unittest.main(verbosity=2)
