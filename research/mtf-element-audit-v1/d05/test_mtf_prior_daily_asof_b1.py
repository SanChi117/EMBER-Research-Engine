"""B1/C08: previous daily is known only after its close; never same-day hint.

These are synthetic source-contract tests, not academic directional bias.
"""
from dataclasses import FrozenInstanceError,replace
from decimal import Decimal
from pathlib import Path
import sys,unittest
H=Path(__file__).resolve().parent
sys.path[:0]=[str(H),str(H.parents[1]/"mtf-course-v05"/"src")]
from course_primitives_v05 import Bar
from mtf_c08_aggregation_b1 import Source15m
from mtf_prior_daily_asof_b1 import PreviousDayEvidence,join_previous_closed_daily,KnownDailyRejected
STEP=900_000
DAY=86_400_000
START=1790899200000
def lastday():
    return PreviousDayEvidence(Bar(START-DAY,START,100,112,98,108,"1d"),"BTCUSDT","attested-original-c08-daily")
def day(n=96):
    result=[]
    for i in range(n):
        start=START+i*STEP
        op=105+i%5
        result.append(Source15m(Bar(start,start+STEP,op,op+2,op-2,op+1,"15m"),
                      Decimal("1.25"),f"15m-{i}","BTCUSDT"))
    return result
def joined(n,asof=None,xs=None,prior=None):
    return join_previous_closed_daily(lastday() if prior is None else prior,
         day(n) if xs is None else xs,START+n*STEP if asof is None else asof)

class PriorDailySourceAsOf(unittest.TestCase):
    def test_at_0015_daily_closed_but_no_hourly_complete(self):
        x=joined(1)
        self.assertEqual(x.prior_daily_known_at_ms,START)
        self.assertIsNone(x.last_closed_1h)
        self.assertIsNone(x.last_closed_4h)
        self.assertIsNone(x.current_1d)
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_at_0100_hourly_known_but_fourhour_missing(self):
        x=joined(4)
        self.assertEqual(x.last_closed_1h.known_at_ms,START+4*STEP)
        self.assertIsNone(x.last_closed_4h)
    def test_at_0345_fourhour_is_still_unknown(self):
        x=joined(15)
        self.assertIsNone(x.last_closed_4h)
    def test_at_0400_closed_fourhour_becomes_known(self):
        x=joined(16)
        self.assertEqual(x.last_closed_4h.known_at_ms,START+16*STEP)
    def test_at_2345_daily_still_previous_day(self):
        x=joined(95)
        self.assertEqual(x.prior_daily_bar.end,START)
        self.assertIsNone(x.current_1d)
        self.assertLessEqual(x.last_closed_4h.known_at_ms,x.as_of_ms)
    def test_at_next_midnight_prev_day_is_now_stale(self):
        with self.assertRaisesRegex(KnownDailyRejected,"DAILY_CONTEXT_NOT_VALID_AT_AS_OF"):
            joined(96)
    def test_trying_to_use_same_day_open_daily_as_context(self):
        fake=PreviousDayEvidence(Bar(START,START+DAY,110,120,100,115,"1d"),
                                 "BTCUSDT","future-daily")
        with self.assertRaisesRegex(KnownDailyRejected,"NOT_PREVIOUS_UTC_DAY_SOURCE"):
            joined(4,prior=fake)
    def test_decision_before_first_15m_close_rejected(self):
        with self.assertRaisesRegex(KnownDailyRejected,"DAILY_CONTEXT_NOT_VALID_AT_AS_OF"):
            joined(4,asof=START)
    def test_future_intraday_suffix_not_used_before_asof(self):
        a=joined(4)
        b=joined(96,asof=START+4*STEP)
        self.assertEqual(a,b)
    def test_missing_current_child_data_cannot_claim_1hour(self):
        xs=day(4)[:3]
        with self.assertRaisesRegex(KnownDailyRejected,"INTRADAY_SOURCE_REJECTED_MISSING_BAR_BEFORE_AS_OF"):
            joined(4,xs=xs)
    def test_wrong_instrument_cannot_link_daily_to_hourly(self):
        p=replace(lastday(),symbol="ETHUSDT")
        with self.assertRaisesRegex(KnownDailyRejected,"PREVIOUS_AND_INTRADAY_MARKET_MISMATCH"):
            joined(4,prior=p)
    def test_wrong_daily_source_market_rejected(self):
        p=replace(lastday(),market="SPOT")
        with self.assertRaisesRegex(KnownDailyRejected,"PREVIOUS_NOT_BINANCE_FUTURES"):
            joined(4,prior=p)
    def test_midnight_gap_cannot_create_false_day_context(self):
        xs=day(4)[1:]
        with self.assertRaisesRegex(KnownDailyRejected,"NOT_PREVIOUS_UTC_DAY_SOURCE"):
            joined(4,xs=xs)
    def test_untested_1d_cannot_become_academic_bias(self):
        x=joined(16)
        self.assertIn("NOT_ACADEMIC_DAILY_BIAS",x.status)
        with self.assertRaises(FrozenInstanceError):
            x.readiness="READY"
    def test_daily_source_id_is_preserved_without_fabricated_signature(self):
        x=joined(4)
        self.assertEqual(x.prior_daily_source_id,"attested-original-c08-daily")
    def test_incorrect_daily_calendar_alignment_rejected(self):
        p=replace(lastday(),bar=Bar(START-DAY+STEP,START+STEP,100,112,98,108,"1d"))
        with self.assertRaisesRegex(KnownDailyRejected,"INVALID_DAILY_BAR_IDENTITY"):
            joined(4,prior=p)
if __name__=="__main__":
    unittest.main(verbosity=2)
