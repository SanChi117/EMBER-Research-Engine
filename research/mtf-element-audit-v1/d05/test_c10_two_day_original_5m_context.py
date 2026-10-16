"""B1/C10: 2 UTC day original-futures source continuity / as-of counterexamples."""
from __future__ import annotations
from dataclasses import FrozenInstanceError,replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys,unittest,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from course_primitives_v05 import Bar
from f03_5m_original_source import verify_original_5m,DAY,PERIOD
from c10_two_day_original_5m_context import review_two_day_5m,TwoDayRejected
T=1790812800000
BASE="https://data.binance.vision/data/futures/um/daily/klines/"
def make(day,symbol="BTCUSDT",pattern=False,override=None):
    date="2026-10-01" if day==0 else "2026-10-02"
    filename=f"{symbol}-5m-{date}.zip"
    url=f"{BASE}{symbol}/5m/{filename}"
    start=T+day*DAY
    rows=[]
    for i in range(288):
        o,h,l,c=100,101,99,100
        if pattern and day==0 and i==20*12+6:h=110
        if pattern and day==1 and i==1*12+6:h=112
        if pattern and day==1 and i==18:l=97
        if pattern and day==1 and i==29:o,h,l,c=100,101,95,96
        if override is not None and i in override:o,h,l,c=override[i]
        rows.append(",".join((str(start+i*PERIOD),str(o),str(h),str(l),str(c),
            "1",str(start+(i+1)*PERIOD-1),"100","10","0.5","50","0")))
    buff=BytesIO()
    with zipfile.ZipFile(buff,"w",zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(filename[:-4]+".csv","\n".join(rows)+"\n")
    b=buff.getvalue()
    check=(sha256(b).hexdigest()+"  "+filename).encode()
    return verify_original_5m(url,b,check)
def review(first=None,second=None,when=T+2*DAY):
    return review_two_day_5m(first if first is not None else make(0,pattern=True),
                              second if second is not None else make(1,pattern=True),when)
class TwoDays5mSourceTests(unittest.TestCase):
    def test_two_complete_days_576_bars_and_48_hours(self):
        x=review()
        self.assertEqual((x.closed_5m_count,x.closed_1h_count),(576,48))
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_real_price_synthetic_raid_created_from_prior_day_fractal(self):
        q=review()
        self.assertGreaterEqual(q.second_day_raid_count,1)
        self.assertEqual(q.first_day_raid_count,0)
    def test_replay_at_second_day_0100_cannot_use_0200_raid(self):
        q=review(when=T+DAY+3600000)
        self.assertEqual(q.second_day_raid_count,0)
    def test_second_day_raid_known_only_after_1h_ends(self):
        q=review(when=T+DAY+2*3600000)
        self.assertGreaterEqual(q.second_day_raid_count,1)
    def test_after_raid_causal_closed_5m_bos_candidate(self):
        q=review()
        self.assertGreaterEqual(len(q.source_raid_bos),1)
        self.assertTrue(all(x.raid_known<x.bos_known for x in q.source_raid_bos))
    def test_5m_bos_known_only_at_bar_close_not_before(self):
        q=review(when=T+DAY+29*PERIOD)
        self.assertFalse(q.source_raid_bos)
        q=review(when=T+DAY+30*PERIOD)
        self.assertTrue(q.source_raid_bos)
    def test_day1_only_prefix_no_second_day_raids(self):
        a=review(when=T+DAY)
        self.assertEqual(a.closed_5m_count,288)
        self.assertEqual(a.second_day_raid_count,0)
    def test_12_mins_is_not_valid_5m_decision(self):
        with self.assertRaisesRegex(TwoDayRejected,"AS_OF_NOT_CLOSED"):
            review(when=T+DAY+12*60000)
    def test_out_of_range_after_two_days_rejected(self):
        with self.assertRaisesRegex(TwoDayRejected,"AS_OF_NOT_CLOSED"):
            review(when=T+2*DAY+PERIOD)
    def test_cross_symbol_rejected(self):
        with self.assertRaisesRegex(TwoDayRejected,"CROSS_MARKET_SYMBOL_OR_SOURCE_DAY"):
            review(second=make(1,symbol="ETHUSDT"))
    def test_reversed_day_source_rejected(self):
        with self.assertRaisesRegex(TwoDayRejected,"MISSING_OR_OVERLAPPING_UTC_DAY"):
            review(first=make(1),second=make(0))
    def test_repeated_same_day_source_rejected(self):
        with self.assertRaisesRegex(TwoDayRejected,"MISSING_OR_OVERLAPPING_UTC_DAY"):
            review(first=make(0),second=make(0))
    def test_first_bar_source_hash_lineage_cannot_be_self_rewritten(self):
        x=make(0)
        changed=list(x.rows)
        changed[5]=replace(changed[5],raw_id="fake")
        with self.assertRaisesRegex(TwoDayRejected,"ORIGINAL_5M_ROW_TIME_OR_LINEAGE_MISMATCH"):
            review(first=replace(x,rows=tuple(changed)))
    def test_gap_or_double_record_is_not_576_history(self):
        x=make(0)
        values=list(x.rows)
        values[88]=replace(values[88],bar=Bar(T+89*PERIOD,T+90*PERIOD,100,101,99,100,"5m"))
        with self.assertRaisesRegex(TwoDayRejected,"ORIGINAL_5M_ROW_TIME_OR_LINEAGE_MISMATCH"):
            review(first=replace(x,rows=tuple(values)))
    def test_287_bar_first_day_rejected(self):
        x=make(0)
        with self.assertRaisesRegex(TwoDayRejected,"INCOMPLETE_OR_MALFORMED_5M_ARCHIVE_PROOF"):
            review(first=replace(x,rows=x.rows[:-1]))
    def test_mislabelled_source_market_url_rejected(self):
        x=make(0)
        with self.assertRaisesRegex(TwoDayRejected,"INVALID_5M_FUTURES_SOURCE_PATH"):
            review(first=replace(x,archive_url=x.archive_url.replace("/futures/um/","/spot/")))
    def test_past_price_events_not_changed_by_future_day_suffix(self):
        first=make(0,pattern=True)
        a=review(first=first,second=make(1,pattern=True),when=T+DAY)
        b=review(first=first,second=make(1,pattern=True,override={200:(100,150,99,100)}),when=T+DAY)
        self.assertEqual((a.confirmed_1h_pivots,a.confirmed_1h_raids,a.source_raid_bos),
                         (b.confirmed_1h_pivots,b.confirmed_1h_raids,b.source_raid_bos))
    def test_second_day_archive_source_proof_is_not_first_day(self):
        q=review()
        self.assertTrue(q.source_raid_bos)
        self.assertTrue(all(e.original_day_zip_sha256==make(1,pattern=True).zip_sha256
                            for e in q.source_raid_bos))
    def test_failed_no_higher_timeframe_context_cannot_claim_ready(self):
        x=review()
        self.assertIn("NOT_AUTHOR_STRONGHL_VC_POI",x.approval)
        with self.assertRaises(FrozenInstanceError):
            x.readiness="READY"
if __name__=="__main__":
    unittest.main(verbosity=2)
