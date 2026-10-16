"""F03 negative mutation tests for independently sourced Binance USD-M 5m ZIP."""
from __future__ import annotations
from dataclasses import FrozenInstanceError
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import csv
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from f03_5m_original_source import (
    parse_5m_source,verify_original_5m,source_5m_imbs,FiveMinuteRejected
)
BASE="https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/5m/"
URL=BASE+"BTCUSDT-5m-2026-10-02.zip"
NAME="BTCUSDT-5m-2026-10-02.csv"
START=1790899200000
STEP=300000
def example():
    return [[str(START+i*STEP),"100","102","99","101","1",str(START+(i+1)*STEP-1),
             "101","10","0.5","50","0"] for i in range(288)]
def bundle(rows=None,extras=False,filename=NAME):
    values=example() if rows is None else rows
    fh=BytesIO()
    with zipfile.ZipFile(fh,"w",zipfile.ZIP_DEFLATED) as zipfileobj:
        payload="\n".join(",".join(v) for v in values)+"\n"
        zipfileobj.writestr(filename,payload)
        if extras:zipfileobj.writestr("other.csv","x")
    raw=fh.getvalue()
    return raw,(sha256(raw).hexdigest()+"  BTCUSDT-5m-2026-10-02.zip").encode("ascii")
def run(rows=None,**kw):
    raw,checksum=bundle(rows,**kw)
    return verify_original_5m(URL,raw,checksum)
class FiveMinuteOriginalSourceTests(unittest.TestCase):
    def test_valid_288_complete_rows_utc_known_5m(self):
        x=run()
        self.assertEqual(len(x.rows),288)
        self.assertEqual(x.rows[-1].bar.end,START+86400000)
        self.assertEqual(x.rows[0].volume,1)
        self.assertEqual(x.readiness,"NOT_TRADE_READY")

    def test_source_first_second_third_candle_wick_gap_only_at_third_close(self):
        rows=example()
        rows[2][1:5]=["104","105","103","104"]
        x=run(rows)
        self.assertEqual(source_5m_imbs(x,START+2*STEP),())
        c=source_5m_imbs(x,START+3*STEP)
        self.assertTrue(c)
        self.assertEqual(c[0].known,START+3*STEP)
        self.assertEqual((c[0].lo,c[0].hi),(102,103))

    def test_original_source_no_imb_when_no_gap(self):
        self.assertEqual(source_5m_imbs(run(),START+10*STEP),())

    def test_source_prefix_cannot_inspect_after_asof(self):
        rows=example()
        rows[8][1:5]=["104","105","103","104"]
        a=source_5m_imbs(run(rows),START+8*STEP)
        b=source_5m_imbs(run(rows),START+9*STEP)
        self.assertNotIn(START+9*STEP,[k.known for k in a])
        self.assertIn(START+9*STEP,[k.known for k in b])

    def test_checksum_diff_rejected(self):
        raw,checksum=bundle()
        with self.assertRaisesRegex(FiveMinuteRejected,"SOURCE_CHECKSUM_MISMATCH"):
            verify_original_5m(URL,raw,("0"*64+"  BTCUSDT-5m-2026-10-02.zip").encode())

    def test_wrong_checksum_filename_rejected(self):
        raw,checksum=bundle()
        with self.assertRaisesRegex(FiveMinuteRejected,"INVALID_REMOTE_CHECKSUM"):
            verify_original_5m(URL,raw,checksum.replace(b"BTCUSDT-5m",b"ETHUSDT-5m"))

    def test_path_cannot_be_spot(self):
        bad=URL.replace("/futures/um/","/spot/")
        with self.assertRaisesRegex(FiveMinuteRejected,"NOT_APPROVED_FUTURES_SYMBOL_OR_5M_PATH"):
            parse_5m_source(bad)

    def test_path_cannot_replace_5m_with_15m(self):
        with self.assertRaisesRegex(FiveMinuteRejected,"NOT_APPROVED_FUTURES_SYMBOL_OR_5M_PATH"):
            parse_5m_source(URL.replace("/5m/","/15m/"))

    def test_unapproved_instrument_rejected(self):
        with self.assertRaisesRegex(FiveMinuteRejected,"NOT_APPROVED_FUTURES_SYMBOL_OR_5M_PATH"):
            parse_5m_source(URL.replace("BTCUSDT","MEMEUSDT"))

    def test_url_query_or_redirect_forgery_rejected(self):
        with self.assertRaisesRegex(FiveMinuteRejected,"NOT_TRUSTED_BINANCE_5M_FUTURES_PATH"):
            parse_5m_source(URL+"?alt=1")
        with self.assertRaisesRegex(FiveMinuteRejected,"NOT_TRUSTED_BINANCE_5M_FUTURES_PATH"):
            parse_5m_source(URL.replace("https://","http://"))

    def test_invalid_day_rejected(self):
        with self.assertRaisesRegex(FiveMinuteRejected,"INVALID_UTC_DATE"):
            parse_5m_source(URL.replace("2026-10-02","2026-02-31"))

    def test_287_rows_cannot_be_declared_a_complete_day(self):
        with self.assertRaisesRegex(FiveMinuteRejected,"NOT_COMPLETE_288_FIVE_MINUTE_CANDLES"):
            run(example()[:-1])

    def test_289_rows_rejected(self):
        with self.assertRaisesRegex(FiveMinuteRejected,"NOT_COMPLETE_288_FIVE_MINUTE_CANDLES"):
            run(example()+[example()[-1]])

    def test_missing_middle_candle_detected(self):
        values=example()
        values.pop(100)
        values.append(values[-1])
        with self.assertRaisesRegex(FiveMinuteRejected,"SOURCE_TIME_GRID_GAP_OR_CLOSE_ERROR"):
            run(values)

    def test_wrong_bar_close_time_rejected(self):
        values=example()
        values[10][6]=str(int(values[10][6])+1)
        with self.assertRaisesRegex(FiveMinuteRejected,"SOURCE_TIME_GRID_GAP_OR_CLOSE_ERROR"):
            run(values)

    def test_broken_ohlc_rejected(self):
        values=example()
        values[30][3]="110"
        with self.assertRaisesRegex(FiveMinuteRejected,"IMPOSSIBLE_RAW_OHLC"):
            run(values)

    def test_negative_volume_rejected(self):
        values=example()
        values[30][5]="-100"
        with self.assertRaisesRegex(FiveMinuteRejected,"INVALID_NUMBER_volume"):
            run(values)

    def test_nan_quote_volume_rejected(self):
        values=example()
        values[30][7]="NaN"
        with self.assertRaisesRegex(FiveMinuteRejected,"INVALID_NUMBER_quote_volume"):
            run(values)

    def test_missing_raw_futures_fields_rejected(self):
        values=example()
        values[30]=values[30][:-1]
        with self.assertRaisesRegex(FiveMinuteRejected,"WRONG_RAW_FUTURES_ROW_FIELDS"):
            run(values)

    def test_extraneous_zip_member_rejected(self):
        with self.assertRaisesRegex(FiveMinuteRejected,"BAD_ZIP_MEMBERS_OR_SIZE"):
            run(extras=True)

    def test_unexpected_zip_file_rejected(self):
        with self.assertRaisesRegex(FiveMinuteRejected,"BAD_ZIP_MEMBERS_OR_SIZE"):
            run(filename="../../outside.csv")

    def test_invalid_asof_or_future_day_rejected(self):
        p=run()
        with self.assertRaisesRegex(FiveMinuteRejected,"5M_AS_OF_NOT_CLOSED"):
            source_5m_imbs(p,START+1)
        with self.assertRaisesRegex(FiveMinuteRejected,"5M_AS_OF_OUTSIDE_ATTESTED_DAY"):
            source_5m_imbs(p,START+86400000+STEP)

    def test_bars_are_frozen_no_implicit_trade_entry(self):
        p=run()
        with self.assertRaises(FrozenInstanceError):
            p.readiness="READY"
        with self.assertRaises(FrozenInstanceError):
            p.rows[0].raw_id="changed"
        self.assertEqual(p.academic_status,"SOURCE_5M_ONLY_VC_NOT_CERTIFIED")

if __name__=="__main__":
    unittest.main(verbosity=2)
