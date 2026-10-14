import sys, pathlib, unittest
from dataclasses import replace
from decimal import Decimal as D
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from strict_bar_closed import ClosedBar, TF_MS, UTC_WEEK_ANCHOR_MS
from strict_tf_d02 import snapshot_htf,native_snapshot,confirmed_pivots,D02Rejected

def t(iso):return int(datetime.fromisoformat(iso.replace('Z','+00:00')).timestamp()*1000)
START=t('2026-04-06T00:00:00Z') # Monday UTC

def candles(tf,n,start=START,symbol='BTCUSDT'):
    p=TF_MS[tf];o=[]
    for i in range(n):
        x=D(100+i);v=D(i+1)
        o.append(ClosedBar(symbol,tf,start+i*p,start+(i+1)*p,x,x+2,x-2,x+1,v))
    return o

class D02Tests(unittest.TestCase):
    def test_15m_to_1h(self):
        r=snapshot_htf(candles('15m',8),'1h',as_of_utc=START+8*TF_MS['15m'])
        self.assertEqual(len(r.bars),2)
        self.assertEqual([x.child_count for x in r.bars],[4,4])
        self.assertEqual((r.bars[0].open,r.bars[0].close,r.bars[0].high,r.bars[0].low,r.bars[0].volume),
            (D(100),D(104),D(105),D(98),D(10)))
    def test_15m_to_4h(self): self.assertEqual(snapshot_htf(candles('15m',32),'4h',as_of_utc=START+32*TF_MS['15m']).bars[0].child_count,16)
    def test_15m_to_1d(self): self.assertEqual(snapshot_htf(candles('15m',96),'1d',as_of_utc=START+TF_MS['1d']).bars[0].child_count,96)
    def test_15m_to_1w(self): self.assertEqual(snapshot_htf(candles('15m',672),'1w',as_of_utc=START+TF_MS['1w']).bars[0].child_count,672)
    def test_1d_to_1w(self): self.assertEqual(snapshot_htf(candles('1d',7),'1w',as_of_utc=START+TF_MS['1w']).bars[0].child_count,7)
    def test_3m_to_15m(self):self.assertEqual(snapshot_htf(candles('3m',5),'15m',as_of_utc=START+TF_MS['15m']).bars[0].child_count,5)
    def test_5m_to_15m(self):self.assertEqual(snapshot_htf(candles('5m',3),'15m',as_of_utc=START+TF_MS['15m']).bars[0].child_count,3)
    def test_15m_cannot_substitute_3m(self):
        with self.assertRaisesRegex(D02Rejected,'UNSUPPORTED_AGGREGATION'): snapshot_htf(candles('15m',4),'3m',as_of_utc=START+TF_MS['1h'])
    def test_same_tf_cannot_aggregate(self):
        with self.assertRaisesRegex(D02Rejected,'UNSUPPORTED_AGGREGATION'): snapshot_htf(candles('15m',4),'15m',as_of_utc=START+TF_MS['1h'])
    def test_native_htf_future_ignored(self):
        c=candles('1h',3)
        r=native_snapshot(c,as_of_utc=START+TF_MS['1h'])
        self.assertEqual(len(r.bars),1);self.assertEqual(r.ignored_future_bars,2)
    def test_no_future_closed_bucket(self):
        r=snapshot_htf(candles('15m',8),'1h',as_of_utc=START+TF_MS['1h']+TF_MS['15m'])
        self.assertEqual(len(r.bars),1)
        self.assertEqual(r.trailing_partial_buckets,1)
    def test_cut_at_last_closed_child(self):
        r=snapshot_htf(candles('15m',8),'1h',as_of_utc=START+TF_MS['1h']+TF_MS['15m']-1)
        self.assertEqual(len(r.bars),1); self.assertEqual(r.ignored_future_bars,4)
    def test_no_leading_partial_bucket(self):
        c=candles('15m',8,start=START+TF_MS['15m'])
        r=snapshot_htf(c,'1h',as_of_utc=c[-1].close_exclusive_ms)
        self.assertEqual(len(r.bars),1);self.assertEqual(r.leading_partial_buckets,1);self.assertEqual(r.trailing_partial_buckets,1)
    def test_parent_bucket_partial_only(self):
        r=snapshot_htf(candles('15m',2),'1h',as_of_utc=START+TF_MS['15m']*2)
        self.assertEqual(len(r.bars),0)
    def test_week_starts_monday_not_sunday(self):
        sunday=t('2026-04-05T00:00:00Z'); c=candles('1d',8,start=sunday)
        r=snapshot_htf(c,'1w',as_of_utc=sunday+8*TF_MS['1d'])
        self.assertEqual(len(r.bars),1);self.assertEqual(r.bars[0].open_at_ms,START);self.assertEqual(r.leading_partial_buckets,1)
    def test_week_rollover_sunday_close_exact(self):
        sunday=t('2026-04-12T00:00:00Z');c=candles('1d',1,start=sunday)
        r=snapshot_htf(c,'1w',as_of_utc=sunday+TF_MS['1d'])
        self.assertEqual(len(r.bars),0);self.assertEqual(r.leading_partial_buckets,1)
    def test_missing_child_rejected(self):
        c=candles('15m',12);del c[4]
        with self.assertRaisesRegex(D02Rejected,'CHILD_GAP'):snapshot_htf(c,'1h',as_of_utc=START+3*TF_MS['1h'])
    def test_repeated_child_rejected(self):
        c=candles('15m',8);c.insert(2,c[1])
        with self.assertRaisesRegex(D02Rejected,'CHILD_UNSORTED_OR_DUPLICATE'):snapshot_htf(c,'1h',as_of_utc=START+2*TF_MS['1h'])
    def test_out_of_order_rejected(self):
        c=candles('15m',8);c[1],c[2]=c[2],c[1]
        with self.assertRaisesRegex(D02Rejected,'CHILD_GAP'):snapshot_htf(c,'1h',as_of_utc=START+2*TF_MS['1h'])
    def test_mixed_symbol_rejected(self):
        c=candles('15m',8);c[5]=replace(c[5],symbol='ETHUSDT')
        with self.assertRaisesRegex(D02Rejected,'CHILD_IDENTITY_MISMATCH'):snapshot_htf(c,'1h',as_of_utc=START+2*TF_MS['1h'])
    def test_mixed_tf_rejected(self):
        c=candles('15m',8);c[5]=replace(c[5],timeframe='5m')
        with self.assertRaisesRegex(D02Rejected,'CHILD_IDENTITY_MISMATCH'):snapshot_htf(c,'1h',as_of_utc=START+2*TF_MS['1h'])
    def test_bad_child_close_time_rejected(self):
        c=candles('15m',8);c[2]=replace(c[2],close_exclusive_ms=c[2].close_exclusive_ms-1)
        with self.assertRaisesRegex(D02Rejected,'CHILD_CLOSE_MISMATCH'):snapshot_htf(c,'1h',as_of_utc=START+2*TF_MS['1h'])
    def test_off_grid_rejected(self):
        c=candles('15m',8);c[0]=replace(c[0],open_at_ms=c[0].open_at_ms+1)
        with self.assertRaisesRegex(D02Rejected,'CHILD_OFF_GRID'):snapshot_htf(c,'1h',as_of_utc=START+2*TF_MS['1h'])
    def test_float_bad_decimal_rejected(self):
        c=candles('15m',8);c[0]=replace(c[0],volume=0.5)
        with self.assertRaisesRegex(D02Rejected,'CHILD_BAD_DECIMAL'):snapshot_htf(c,'1h',as_of_utc=START+2*TF_MS['1h'])
    def test_wrong_ohlc_rejected(self):
        c=candles('15m',8);c[0]=replace(c[0],high=D(0))
        with self.assertRaisesRegex(D02Rejected,'CHILD_INVALID_OHLCV'):snapshot_htf(c,'1h',as_of_utc=START+2*TF_MS['1h'])
    def test_integer_time_bool_rejected(self):
        c=candles('15m',8);c[0]=replace(c[0],open_at_ms=True)
        with self.assertRaisesRegex(D02Rejected,'NONINTEGER_CHILD_TIME'):snapshot_htf(c,'1h',as_of_utc=START+2*TF_MS['1h'])
    def test_asof_zone_rejected(self):
        with self.assertRaisesRegex(Exception,'AMBIGUOUS_OR_NON_UTC_TIME'):snapshot_htf(candles('15m',4),'1h',as_of_utc='2026-04-06T03:00:00+03:00')
    def test_future_ohlc_mutation_cannot_change_asof(self):
        c=candles('15m',12);asof=START+TF_MS['1h'];baseline=snapshot_htf(c,'1h',as_of_utc=asof)
        for i in range(4,12):c[i]=replace(c[i],high=D(100000000),volume=D(99999999))
        self.assertEqual(baseline,snapshot_htf(c,'1h',as_of_utc=asof))
    def test_asof_border_1ms(self):
        c=candles('15m',4)
        r1=snapshot_htf(c,'1h',as_of_utc=START+TF_MS['1h']-1)
        r2=snapshot_htf(c,'1h',as_of_utc=START+TF_MS['1h'])
        self.assertEqual(len(r1.bars),0);self.assertEqual(len(r2.bars),1)
    def test_missing_initial_bar_rejected_when_source_window_bound(self):
        c=candles('15m',8)[1:]
        with self.assertRaisesRegex(D02Rejected,'SOURCE_START_MISMATCH'):
            snapshot_htf(c,'1h',as_of_utc=START+2*TF_MS['1h'],expected_source_start_utc=START)
    def test_missing_final_bar_rejected_at_closed_asof(self):
        c=candles('15m',8)[:-1]
        with self.assertRaisesRegex(D02Rejected,'STALE_OR_MISSING_RECENT_CHILDREN'):
            snapshot_htf(c,'1h',as_of_utc=START+2*TF_MS['1h'])
    def test_stale_native_htf_rejected(self):
        c=candles('1d',2)
        with self.assertRaisesRegex(D02Rejected,'STALE_NATIVE_HTF_HISTORY'):
            native_snapshot(c,as_of_utc=START+3*TF_MS['1d'])
    def test_no_bars_fails(self):
        with self.assertRaisesRegex(D02Rejected,'NO_SOURCE_BARS'):snapshot_htf([],'1h',as_of_utc=START)
    def test_pivot_confirmation_delay(self):
        c=candles('15m',5);c[2]=replace(c[2],high=D(10000))
        snap=native_snapshot(c,as_of_utc=c[-1].close_exclusive_ms)
        earlier=confirmed_pivots(snap,left=1,right=2,as_of_utc=c[3].close_exclusive_ms)
        now=confirmed_pivots(snap,left=1,right=2,as_of_utc=c[4].close_exclusive_ms)
        self.assertFalse(any(p.pivot_open_at_ms==c[2].open_at_ms for p in earlier))
        hit=[p for p in now if p.pivot_open_at_ms==c[2].open_at_ms and p.side=='HIGH']
        self.assertEqual(len(hit),1);self.assertEqual(hit[0].confirmed_at_ms,c[4].close_exclusive_ms)
    def test_pivot_tie_not_arbitrarily_selected(self):
        c=candles('15m',5);c[2]=replace(c[2],high=D(10000));c[3]=replace(c[3],high=D(10000))
        snap=native_snapshot(c,as_of_utc=c[-1].close_exclusive_ms)
        self.assertFalse(any(p.pivot_open_at_ms==c[2].open_at_ms and p.side=='HIGH' for p in confirmed_pivots(snap,left=1,right=2)))
    def test_pivot_earlier_asof_than_snapshot(self):
        snap=native_snapshot(candles('15m',5),as_of_utc=START+5*TF_MS['15m'])
        with self.assertRaisesRegex(D02Rejected,'ASOF_EXCEEDS_SNAPSHOT'):confirmed_pivots(snap,left=1,right=1,as_of_utc=START+6*TF_MS['15m'])
    def test_pivot_bad_lookaround(self):
        snap=native_snapshot(candles('15m',5),as_of_utc=START+5*TF_MS['15m'])
        with self.assertRaisesRegex(D02Rejected,'BAD_PIVOT_LOOKAROUND'):confirmed_pivots(snap,left=0,right=1)
    def test_manual_native_future_suffix_invisible(self):
        c=candles('1d',3);now=START+TF_MS['1d']
        snap=native_snapshot(c,as_of_utc=now)
        self.assertEqual(snap.bars[0].close_exclusive_ms,now)
    def test_week_anchor_constant(self):
        self.assertEqual(UTC_WEEK_ANCHOR_MS,4*TF_MS['1d'])

if __name__=='__main__':unittest.main()
