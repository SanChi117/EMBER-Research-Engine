"""D01 tests with hostile fixtures; no trading code, PnL, or hyperparameters."""
from __future__ import annotations
import csv, hashlib, pathlib, sys, tempfile, unittest
from dataclasses import replace
from datetime import datetime, timezone

BASE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE/'tools'))
from strict_bar_closed import Provenance, read_closed_bars, utc_ms, D01Rejected, TF_MS

START = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
H = ('open_time','close_time','open','high','low','close','volume','symbol')
def make(n=4, step=900000, start=START):
    return [dict(open_time=str(start+i*step),close_time=str(start+(i+1)*step-1),
        open='100.000', high='101.200',low='99.800',close='100.123',volume='12.500',symbol='BTCUSDT') for i in range(n)]

class D01Contract(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=pathlib.Path(self.tmp.name)/'bars.csv'
        self.rows=make()
        self.as_of=START+4*900000

    def save(self, rows=None, fields=H):
        with self.path.open('w',newline='',encoding='utf8') as f:
            w=csv.DictWriter(f,fieldnames=list(fields),extrasaction='ignore');w.writeheader();w.writerows(self.rows if rows is None else rows)
        digest=hashlib.sha256(self.path.read_bytes()).hexdigest()
        return Provenance('BINANCE','FUTURES_UM','BTCUSDT','15m','fixture: constructed 2026-04-01',digest)

    def check(self, expected, *,rows=None,fields=H,as_of=None,provenance_mut=None):
        prov=self.save(rows,fields)
        if provenance_mut:prov=replace(prov,**provenance_mut)
        with self.assertRaises(D01Rejected) as ctx:
            read_closed_bars(self.path, prov, as_of_utc=self.as_of if as_of is None else as_of)
        self.assertEqual(ctx.exception.code,expected)

    def test_01_valid_closed(self):
        p=self.save();b=read_closed_bars(self.path,p,as_of_utc=self.as_of)
        self.assertEqual(len(b),4);self.assertEqual(str(b[0].volume),'12.500')
        self.assertEqual(b[-1].close_exclusive_ms,self.as_of)

    def test_02_missing_volume_cell(self):
        r=make();r[1]['volume']='';self.check('MISSING_VOLUME',rows=r)
    def test_03_missing_volume_column(self):
        self.check('MISSING_COLUMNS',fields=[k for k in H if k!='volume'])
    def test_04_nonfinite(self):
        for raw in ('NaN','Infinity','-Infinity'):
            r=make();r[0]['close']=raw
            with self.subTest(raw=raw):self.check('NONFINITE_CLOSE',rows=r)
    def test_05_negative_volume(self):
        r=make();r[1]['volume']='-0.1';self.check('INVALID_OHLCV',rows=r)
    def test_06_invalid_ohlc(self):
        r=make();r[1]['high']='99';self.check('INVALID_OHLCV',rows=r)
    def test_07_shifted_grid(self):
        r=make();[x.update(open_time=str(int(x['open_time'])+300000),close_time=str(int(x['close_time'])+300000)) for x in r]
        self.check('OFF_TIMEFRAME_GRID',rows=r)
    def test_08_unfinished_asof(self):
        self.check('NOT_CLOSED_AS_OF',as_of=self.as_of-1)
    def test_09_duplicate_timestamp(self):
        r=make();r.append(dict(r[-1]));self.check('UNSORTED_OR_DUPLICATE_TIMESTAMP',rows=r,as_of=self.as_of+900000)
    def test_10_unsorted_rows(self):
        r=make();r[1],r[2]=r[2],r[1];self.check('MISSING_BARS',rows=r)
    def test_11_gap(self):
        r=make();r.pop(1);self.check('MISSING_BARS',rows=r)
    def test_12_wrong_market(self):
        self.check('WRONG_MARKET_TYPE',provenance_mut={'market_type':'SPOT'})
    def test_13_wrong_symbol(self):
        r=make();r[2]['symbol']='ETHUSDT';self.check('SYMBOL_MISMATCH',rows=r)
    def test_14_unknown_tf(self):
        self.check('UNKNOWN_TIMEFRAME',provenance_mut={'timeframe':'17m'})
    def test_15_digest_mismatch(self):
        self.check('CSV_DIGEST_MISMATCH',provenance_mut={'expected_csv_sha256':'0'*64})
    def test_16_missing_source(self):
        self.check('SOURCE_NOT_DECLARED',provenance_mut={'source_description':' '})
    def test_17_bad_close_time(self):
        r=make();r[1]['close_time']=str(int(r[1]['close_time'])-2);self.check('INCONSISTENT_CLOSE_TIME',rows=r)
    def test_18_missing_close_time(self):
        self.check('MISSING_COLUMNS',fields=[k for k in H if k!='close_time'])
    def test_19_ambiguous_timezone(self):
        self.check('AMBIGUOUS_OR_NON_UTC_TIME',as_of='2026-04-01T01:00:00+03:00')
    def test_20_naive_timezone(self):
        self.check('AMBIGUOUS_OR_NON_UTC_TIME',as_of='2026-04-01T01:00:00')
    def test_21_boolean_timestamp(self):
        self.check('BAD_TIME_TYPE',as_of=True)
    def test_22_fractional_timestamp(self):
        self.check('BAD_TIME_TYPE',as_of=float(self.as_of))
    def test_23_d01_accepts_utc_Z(self):
        p=self.save();r=read_closed_bars(self.path,p,as_of_utc='2026-04-01T01:00:00Z');self.assertEqual(len(r),4)
    def test_24_week_monday_accept(self):
        week=int(datetime(2026,3,30,tzinfo=timezone.utc).timestamp()*1000)
        r=make(2,TF_MS['1w'],week);p=replace(self.save(r),timeframe='1w')
        self.assertEqual(len(read_closed_bars(self.path,p,as_of_utc=week+2*TF_MS['1w'])),2)
    def test_25_week_sunday_reject(self):
        sun=int(datetime(2026,3,29,tzinfo=timezone.utc).timestamp()*1000)
        r=make(2,TF_MS['1w'],sun);p=replace(self.save(r),timeframe='1w')
        with self.assertRaises(D01Rejected) as x:read_closed_bars(self.path,p,as_of_utc=sun+2*TF_MS['1w'])
        self.assertEqual(x.exception.code,'OFF_TIMEFRAME_GRID')
    def test_26_different_file_after_digest(self):
        p=self.save();self.path.write_bytes(self.path.read_bytes().replace(b'12.500',b'12.501',1))
        with self.assertRaises(D01Rejected) as x:read_closed_bars(self.path,p,as_of_utc=self.as_of)
        self.assertEqual(x.exception.code,'CSV_DIGEST_MISMATCH')
    def test_27_zero_bars(self):
        p=self.save([])
        with self.assertRaises(D01Rejected) as x:read_closed_bars(self.path,p,as_of_utc=self.as_of)
        self.assertEqual(x.exception.code,'ZERO_BARS')
    def test_28_exact_last_close_allowed(self):
        p=self.save();self.assertEqual(len(read_closed_bars(self.path,p,as_of_utc=self.as_of)),4)
    def test_29_no_earlier_bars_after_future_injection(self):
        r=make();r[2]['open_time']=str(START+20*900000);r[2]['close_time']=str(START+21*900000-1)
        self.check('NOT_CLOSED_AS_OF',rows=r)
    def test_30_utf8_bom(self):
        p=self.save();self.path.write_bytes(b'\xef\xbb\xbf'+self.path.read_bytes())
        p=replace(p,expected_csv_sha256=hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(len(read_closed_bars(self.path,p,as_of_utc=self.as_of)),4)

if __name__=='__main__':unittest.main()