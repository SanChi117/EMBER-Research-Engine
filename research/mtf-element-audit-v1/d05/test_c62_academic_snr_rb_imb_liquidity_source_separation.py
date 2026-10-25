"""C62 strict source-only differentiation SNR/MB vs wick-only RB/IMB."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c16_c08_monthly_daily_htf_lineage import DerivedClosedTF,SEPT_START,TF_MS
from c62_academic_snr_rb_imb_liquidity_source_separation import (
    observe_hourly_source_poi_split)
H=TF_MS["1h"];O=SEPT_START
def candle(i,op,hi,lo,cl):
    t=O+i*H
    return DerivedClosedTF("BTCUSDT","1h",t,t+H,
       D(str(op)),D(str(hi)),D(str(lo)),D(str(cl)),D("5"),
       tuple("f"*64+":"+str(t+k*900000) for k in range(4)),
       ("f"*64,),)
def baseline():
    # pivot SSL at h1 low=90, confirmed by h2; first h3 wick sweeps 89
    return (candle(0,102,110,95,105),
            candle(1,104,112,90,106),
            candle(2,105,111,100,106),
            candle(3,105,108,89,101),
            candle(4,101,108,99,106),
            candle(5,106,116,103,115))
def run(rows=None,asof=None):
    z=baseline() if rows is None else rows
    return observe_hourly_source_poi_split(z,as_of_ms=z[-1].known_at_ms if asof is None else asof)
def matches(doc,cl):
    return [x for x in doc["technical_1h_snr_rb_separate_cases"] if x.source_class==cl]

class SourceSplitTest(unittest.TestCase):
    def test_c62_snr_sweeps_prior_confirmed_ssl_before_body_acceptance(self):
        z=run()
        found=matches(z,"SNR_ACCEPTED_CLOSE_WITH_SOURCE_LIQUIDITY_PROXY")
        self.assertEqual(len(found),1)
        self.assertEqual(found[0].side,"LONG")
        self.assertEqual(found[0].source_liquidity_reference,"PREKNOWN_1H_SSL_STRICT_PIVOT")
        self.assertEqual(found[0].fully_known_ms,O+6*H)
        self.assertFalse(found[0].author_volume_confirmation)
    def test_c62_rb_wick_strict_liquidity_vs_body_breach(self):
        z=run()
        found=matches(z,"RB_WICK_ONLY_LIQUIDITY_SOURCE_PROXY")
        self.assertEqual(len(found),1)
        self.assertEqual(found[0].side,"LONG")
        self.assertIsNone(found[0].confirmation_first_native15m_id)
    def test_same_pair_may_be_source_rb_and_snr_but_author_not_certified(self):
        z=run()
        pair=matches(z,"RB_WICK_ONLY_LIQUIDITY_SOURCE_PROXY")[0]
        snr=matches(z,"SNR_ACCEPTED_CLOSE_WITH_SOURCE_LIQUIDITY_PROXY")[0]
        self.assertEqual(pair.pair_first_native15m_id,snr.pair_first_native15m_id)
        self.assertNotEqual(pair.type,snr.type)
        self.assertEqual(z["orders"],0)
    def test_body_breach_is_not_rb_wick_only(self):
        q=list(baseline());q[3]=replace(q[3],close=D("88"),low=D("87"))
        z=run(tuple(q))
        self.assertFalse(matches(z,"RB_WICK_ONLY_LIQUIDITY_SOURCE_PROXY"))
    def test_body_breach_snr_may_still_test_liquidity_source(self):
        q=list(baseline());q[3]=replace(q[3],close=D("88"),low=D("87"))
        q[4]=replace(q[4],open=D("88"))
        z=run(tuple(q))
        self.assertTrue(matches(z,"SNR_ACCEPTED_CLOSE_WITH_SOURCE_LIQUIDITY_PROXY"))
    def test_no_late_followup_close_means_no_snr_or_mb(self):
        z=run(asof=O+5*H)
        self.assertFalse(any(x.type=="SNR_OR_MB" and x.pair_first_known_ms==O+4*H
          for x in z["technical_1h_snr_rb_separate_cases"]))
    def test_close_below_pair_extreme_not_snr_long(self):
        q=list(baseline());q[5]=replace(q[5],close=D("108"))
        z=run(tuple(q))
        self.assertFalse(matches(z,"SNR_ACCEPTED_CLOSE_WITH_SOURCE_LIQUIDITY_PROXY"))
    def test_pair_without_liquidity_returns_mb_not_strong_snr(self):
        q=(candle(0,100,105,96,98),
           candle(1,98,104,96,102),
           candle(2,103,110,102,109))
        z=run(q)
        self.assertTrue(matches(z,"MB_WEAKER_SOURCE_ONLY_NO_RAID_OR_IMB_NOT_VOLUME_CONFIRMATION"))
        self.assertFalse(matches(z,"SNR_ACCEPTED_CLOSE_WITH_SOURCE_LIQUIDITY_PROXY"))
    def test_pair_only_never_rb_wick_source_without_preknown_raid(self):
        q=(candle(0,100,105,96,98),candle(1,98,104,96,102))
        z=run(q)
        self.assertTrue(matches(z,"RB_TWO_OPPOSITE_HOURLY_CANDLES_WITHOUT_VERIFIED_WICK_RAID"))
    def test_imb_only_after_third_closed_1h_bar(self):
        q=(candle(0,90,100,85,98),
           candle(1,102,108,101,107),
           candle(2,113,120,112,118))
        z=run(q)
        self.assertEqual(len(z["technical_original_1h_imb_gaps"]),1)
        self.assertEqual(z["technical_original_1h_imb_gaps"][0].known_ms,O+3*H)
        self.assertEqual(z["technical_original_1h_imb_gaps"][0].side,"LONG")
    def test_imb_not_known_before_third_candle_closed(self):
        q=(candle(0,90,100,85,98),
           candle(1,102,108,101,107),
           candle(2,113,120,112,118))
        z=run(q,asof=O+2*H)
        self.assertEqual(z["technical_original_1h_imb_gaps"],())
    def test_consecutive_source_asof_matches_physically_shortened_prefix(self):
        q=baseline()
        self.assertEqual(run(q,asof=O+5*H),run(q[:5],asof=O+5*H))
    def test_no_author_certifications_from_any_technical_category(self):
        z=run()
        self.assertEqual(z["author_goldens"],0)
        self.assertEqual(z["readiness"],"NOT_TRADE_READY")
        self.assertTrue(all(not c.author_classified_poi and
            not c.author_stronghl and not c.orders and not c.trades for c in
            z["technical_1h_snr_rb_separate_cases"]))
    def test_foreign_source_symbol_rejected(self):
        q=list(baseline());q[1]=replace(q[1],symbol="ETHUSDT")
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            run(tuple(q))
    def test_open_1h_source_bar_rejected(self):
        q=list(baseline());q[1]=replace(q[1],known_at_ms=q[1].known_at_ms-1)
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            run(tuple(q))
    def test_source_negative_volume_rejected(self):
        q=list(baseline());q[2]=replace(q[2],volume=D("-1"))
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            run(tuple(q))
    def test_invalid_truncated_original15m_ids_rejected(self):
        q=list(baseline());q[2]=replace(q[2],source_native_15m_rows=("fake",))
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            run(tuple(q))
    def test_nonfinite_source_open_rejected(self):
        q=list(baseline());q[2]=replace(q[2],open=D("NaN"))
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            run(tuple(q))
    def test_missing_complete_hour_grid_rejected(self):
        q=baseline()
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            run(q[:2]+q[3:])
    def test_partial_asof_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED"):
            run(asof=O+4*H+10)
    def test_later_asof_cannot_use_future_original_candles(self):
        z=run(asof=O+3*H)
        self.assertFalse(any(x.fully_known_ms>O+3*H for x in z["technical_1h_snr_rb_separate_cases"]))
    def test_source_high_below_low_fails(self):
        q=list(baseline());q[2]=replace(q[2],high=D("90"))
        with self.assertRaisesRegex(ValueError,"FORGED_OR_UNCLOSED"):
            run(tuple(q))
if __name__=="__main__":unittest.main()
