"""B1/C07 adversarial 1h/4h/1d exact closed-source aggregation tests.

Synthetic source bars prove arithmetic and no-lookahead only, not Binance
provenance. Separate remote ZIP witness is needed for the latter.
"""
from __future__ import annotations
from dataclasses import FrozenInstanceError,replace
from decimal import Decimal
from pathlib import Path
import sys, unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parents[1]/"mtf-course-v05"/"src"))
from course_primitives_v05 import Bar
from mtf_c08_aggregation_b1 import Source15m,derive_closed_mtf_from_15m,MTFSourceRejected

STEP=900_000
DAY=86_400_000
T=1790812800000

def series(n=96):
    result=[]
    for i in range(n):
        start=T+i*STEP
        opened=100+(i%4)
        closed=opened+1
        high=closed+1
        low=opened-1
        candle=Bar(start,start+STEP,opened,high,low,closed,"15m")
        result.append(Source15m(candle,Decimal("0.125"),f"fixture:{i}","BTCUSDT"))
    return result

class ClosedMtfSourceGeometry(unittest.TestCase):
    def test_one_day_yields_24_1h_6_4h_one_daily(self):
        a=derive_closed_mtf_from_15m(series(),T+DAY)
        self.assertEqual((len(a.bars_1h),len(a.bars_4h),len(a.bars_1d)),(24,6,1))
        self.assertEqual((a.pending_1h_slots,a.pending_4h_slots,a.pending_1d_slots),(0,0,0))
        self.assertEqual(a.readiness,"NOT_TRADE_READY")

    def test_volume_is_decimal_exact_and_source_rows_traceable(self):
        a=derive_closed_mtf_from_15m(series(),T+DAY)
        self.assertEqual(a.bars_1h[0].volume,Decimal("0.500"))
        self.assertEqual(a.bars_4h[0].volume,Decimal("2.000"))
        self.assertEqual(a.bars_1d[0].volume,Decimal("12.000"))
        self.assertEqual(len(a.bars_4h[0].source_member_ids),16)
        self.assertEqual(len(a.bars_1d[0].source_member_ids),96)

    def test_ohlc_derived_from_closed_members_only(self):
        a=derive_closed_mtf_from_15m(series(),T+DAY)
        first=a.bars_1h[0].bar
        self.assertEqual((first.o,first.h,first.l,first.c),(100,105,99,104))
        self.assertEqual(first.start,T)
        self.assertEqual(first.end,T+4*STEP)
        self.assertEqual(a.bars_1h[0].known_at_ms,first.end)

    def test_three_15m_slots_produce_no_1h_close(self):
        a=derive_closed_mtf_from_15m(series(3),T+3*STEP)
        self.assertEqual((len(a.bars_1h),len(a.bars_4h),len(a.bars_1d)),(0,0,0))
        self.assertEqual((a.pending_1h_slots,a.pending_4h_slots,a.pending_1d_slots),(3,3,3))

    def test_four_15m_closes_create_1h_but_not_4h(self):
        a=derive_closed_mtf_from_15m(series(4),T+4*STEP)
        self.assertEqual((len(a.bars_1h),len(a.bars_4h),len(a.bars_1d)),(1,0,0))
        self.assertEqual(a.bars_1h[0].known_at_ms,T+4*STEP)

    def test_sixteen_15m_closes_create_4h(self):
        a=derive_closed_mtf_from_15m(series(16),T+16*STEP)
        self.assertEqual((len(a.bars_1h),len(a.bars_4h),len(a.bars_1d)),(4,1,0))
        self.assertEqual(a.bars_4h[0].known_at_ms,T+16*STEP)

    def test_ninety_five_bar_daily_not_yet_known(self):
        a=derive_closed_mtf_from_15m(series(95),T+95*STEP)
        self.assertEqual(len(a.bars_1d),0)
        self.assertEqual(a.pending_1d_slots,95)

    def test_future_suffix_is_not_part_of_closed_prefix(self):
        xs=series(8)
        a=derive_closed_mtf_from_15m(xs[:4],T+4*STEP)
        b=derive_closed_mtf_from_15m(xs,T+4*STEP)
        self.assertEqual(a,b)

    def test_volume_only_from_closed_candles(self):
        xs=series(5)
        xs[-1]=replace(xs[-1],volume=Decimal("10000000000"))
        res=derive_closed_mtf_from_15m(xs,T+4*STEP)
        self.assertEqual(res.bars_1h[0].volume,Decimal("0.500"))

    def test_missing_15m_in_group_is_fail_closed(self):
        xs=series(4)
        with self.assertRaisesRegex(MTFSourceRejected,"SOURCE_15M_GAP_OR_MIXED_TF"):
            derive_closed_mtf_from_15m([xs[0],xs[1],xs[3]],T+4*STEP)

    def test_missing_end_bar_prevents_false_closure(self):
        with self.assertRaisesRegex(MTFSourceRejected,"MISSING_BAR_BEFORE_AS_OF"):
            derive_closed_mtf_from_15m(series(3),T+4*STEP)

    def test_undocumented_midnight_prefix_rejected(self):
        xs=series(5)[1:]
        with self.assertRaisesRegex(MTFSourceRejected,"UNKNOWN_DAY_START_HISTORY"):
            derive_closed_mtf_from_15m(xs,T+5*STEP)

    def test_mixed_symbol_rejected_not_false_btc_htf(self):
        xs=series(4)
        xs[2]=replace(xs[2],symbol="ETHUSDT")
        with self.assertRaisesRegex(MTFSourceRejected,"CROSS_INSTRUMENT_OR_MARKET_SOURCE"):
            derive_closed_mtf_from_15m(xs,T+4*STEP)

    def test_spot_and_foreign_venue_rejected(self):
        xs=series(4)
        xs[0]=replace(xs[0],market="SPOT")
        with self.assertRaisesRegex(MTFSourceRejected,"NOT_BINANCE_USDM_FUTURES"):
            derive_closed_mtf_from_15m(xs,T+4*STEP)
        xs[0]=replace(xs[0],venue="KRAKEN",market="USDM_FUTURES")
        with self.assertRaisesRegex(MTFSourceRejected,"NOT_BINANCE_USDM_FUTURES"):
            derive_closed_mtf_from_15m(xs,T+4*STEP)

    def test_invalid_source_volume_rejected(self):
        xs=series(4)
        xs[1]=replace(xs[1],volume=Decimal("-1"))
        with self.assertRaisesRegex(MTFSourceRejected,"BAD_VOLUME_OR_SOURCE_PROVENANCE"):
            derive_closed_mtf_from_15m(xs,T+4*STEP)
        xs[1]=replace(xs[1],volume=Decimal("NaN"))
        with self.assertRaisesRegex(MTFSourceRejected,"BAD_VOLUME_OR_SOURCE_PROVENANCE"):
            derive_closed_mtf_from_15m(xs,T+4*STEP)

    def test_repeated_raw_id_not_acceptable(self):
        xs=series(4)
        xs[3]=replace(xs[3],member_id="fixture:0")
        with self.assertRaisesRegex(MTFSourceRejected,"REUSED_SOURCE_ROW_ID"):
            derive_closed_mtf_from_15m(xs,T+4*STEP)

    def test_asof_requires_actual_closed_15m_time(self):
        with self.assertRaisesRegex(MTFSourceRejected,"AS_OF_NOT_15M_CLOSE_BOUNDARY"):
            derive_closed_mtf_from_15m(series(4),T+4*STEP-1)

    def test_bad_source_bar_type_rejected_instead_of_crash(self):
        xs=series(4)
        xs[0]=replace(xs[0],bar=None)
        with self.assertRaisesRegex(MTFSourceRejected,"INVALID_CANDLE_TYPE"):
            derive_closed_mtf_from_15m(xs,T+4*STEP)

    def test_reject_mixed_five_minute_bars(self):
        xs=series(4)
        xs[2]=replace(xs[2],bar=Bar(T+2*STEP,T+2*STEP+300_000,100,103,99,101,"5m"))
        with self.assertRaisesRegex(MTFSourceRejected,"NOT_ALIGNED_15M_SOURCE"):
            derive_closed_mtf_from_15m(xs,T+4*STEP)

    def test_immutable_htf_records_cannot_claim_ready(self):
        res=derive_closed_mtf_from_15m(series(4),T+4*STEP)
        with self.assertRaises(FrozenInstanceError):
            res.bars_1h[0].readiness="READY"
        self.assertIn("NOT_DAILY_BIAS_OR_VC",res.bars_1h[0].course_label)

    def test_empty_unknown_source_fail_closed(self):
        with self.assertRaisesRegex(MTFSourceRejected,"INVALID_15M_SOURCES"):
            derive_closed_mtf_from_15m([],T+STEP)

if __name__=="__main__":
    unittest.main(verbosity=2)
