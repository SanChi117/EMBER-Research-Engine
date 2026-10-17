"""C27 source-family falsification: no invented author EQ tolerance or UTC session."""
import unittest
from dataclasses import replace
from datetime import datetime,timezone
from decimal import Decimal as D
from types import SimpleNamespace as NS
from c20b_hourly_fractal_source_observer import HourFractal,HourSource
from c21_native3m_source_bridge import SEPT_START,THREE
from c27_target_families_source import (
    _known_same_price_pairs,previous_zone_extrema,inspect_c27,_local_dt,HOUR)
from test_c21b_native_3m_vs_5m import make3

def when(s):
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()*1000)

def pivot(kind,price,center,known):
    return HourFractal(kind,D(price),center,known,("original-"+str(center),))

def row(ms,high="99",low="90",close="95"):
    return NS(start_ms=ms,known_ms=ms+THREE,high=D(high),low=D(low),
              close=D(close),raw_id="original-"+str(ms))

def hours_for(start,count=48):
    return tuple(HourSource(start+i*HOUR,start+(i+1)*HOUR,
        D("100"),D(str(105+i%7)),D(str(80-i%9)),D("95"),
        ("original-hour-"+str(i),)) for i in range(count))

class C27SourceFamilyNegativeControls(unittest.TestCase):
    def test_one_pivot_is_not_eqh(self):
        self.assertEqual(_known_same_price_pairs(
            (pivot("BSL","110",1,10),),"LONG",D("100"),40,
            (row(10),)),())
    def test_exact_pair_witness_is_not_author_eq_tolerance(self):
        ps=(pivot("BSL","110",1,10),pivot("BSL","110.0",20,30))
        x=_known_same_price_pairs(ps,"LONG",D("100"),40,
                                  (row(10),row(13),row(30)))
        self.assertEqual(len(x),1)
        self.assertEqual(x[0].family,"EXACT_1H_EQH_WITNESS")
        self.assertEqual(x[0].status,"EXACT_PRICE_PAIR_ONLY_AUTHOR_EQ_TOLERANCE_UNKNOWN")
    def test_near_equal_is_not_exact_equal_and_no_atr_tolerance(self):
        ps=(pivot("BSL","110",1,10),pivot("BSL","110.01",20,30))
        self.assertEqual(_known_same_price_pairs(ps,"LONG",D("100"),40,(row(10),)),())
    def test_unconfirmed_second_swing_never_pairs(self):
        ps=(pivot("SSL","90",1,10),pivot("SSL","90",20,45))
        self.assertEqual(_known_same_price_pairs(ps,"SHORT",D("100"),40,(row(10),)),())
    def test_wrong_side_pair_is_excluded(self):
        ps=(pivot("SSL","90",1,10),pivot("SSL","90",20,30))
        self.assertEqual(_known_same_price_pairs(ps,"LONG",D("100"),40,(row(10),)),())
    def test_short_eql_pair_is_recorded_not_approved(self):
        ps=(pivot("SSL","90",1,10),pivot("SSL","90",20,30))
        x=_known_same_price_pairs(ps,"SHORT",D("100"),40,(row(10),row(30)))
        self.assertEqual(x[0].family,"EXACT_1H_EQL_WITNESS")
        self.assertEqual(x[0].price_side,"SHORT_BELOW")
    def test_exact_pair_with_prior_wick_cross_not_labeled_live(self):
        ps=(pivot("BSL","100",1,10),pivot("BSL","100",20,30))
        x=_known_same_price_pairs(ps,"LONG",D("90"),40,
                                  (row(10,high="101"),row(30)))
        self.assertEqual(x[0].before_break_cross_state,"WICK_CROSS")
    def test_corrupt_finite_decimal_or_raw_rows_rejected(self):
        ps=(pivot("BSL","NaN",1,10),pivot("BSL","NaN",20,30))
        with self.assertRaisesRegex(ValueError,"CORRUPTED_FRACTAL"):
            _known_same_price_pairs(ps,"LONG",D("90"),40,(row(10),))
    def test_calendar_previous_day_and_09_17_distinct(self):
        h=hours_for(when("2026-10-15T00:00:00"),72)
        r=previous_zone_extrema(h,(),zone="UTC",raid_ms=when("2026-10-17T10:00:00"),
              break_start_ms=when("2026-10-17T11:00:00"),side="LONG",entry=D("100"))
        self.assertEqual(len(r),4)
        self.assertEqual({x.required_closed_1h_hours for x in r},{8,24})
        self.assertTrue(all(x.value is not None for x in r))
        self.assertNotEqual(r[0].value,r[2].value)
    def test_incomplete_calendar_explicitly_unknown(self):
        h=hours_for(when("2026-10-16T10:00:00"),12)
        r=previous_zone_extrema(h,(),zone="UTC",raid_ms=when("2026-10-17T10:00:00"),
            break_start_ms=when("2026-10-17T11:00:00"),side="SHORT",entry=D("90"))
        self.assertTrue(all(x.status=="UNKNOWN_SOURCE_INCOMPLETE" for x in r))
        self.assertTrue(all(x.value is None for x in r))
    def test_dst_kyiv_shifts_previous_calendar(self):
        t=when("2026-10-17T22:00:00")
        self.assertNotEqual(_local_dt(t,"UTC").date(),_local_dt(t,"Europe/Kyiv").date())
    def test_invalid_author_zone_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_AUTHOR_TIMEZONE"):
            previous_zone_extrema((),(),zone="Europe/Fiction",raid_ms=10,
                 break_start_ms=20,side="LONG",entry=D("100"))
    def test_invalid_raid_break_order_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_TIMESTAMP"):
            previous_zone_extrema((),(),zone="UTC",raid_ms=20,
                break_start_ms=20,side="LONG",entry=D("100"))
    def test_c27_source_has_no_trade_approval(self):
        r=inspect_c27(make3(),as_of_ms=make3().as_of_ms)
        self.assertEqual(r.readiness,"NOT_TRADE_READY")
        self.assertEqual(r.author_approved_trades,0)
        self.assertTrue(all(not x.author_target_approved for x in r.cases))
        self.assertTrue(all("AUTHOR_EQ_TOLERANCE_UNKNOWN" in x.unknowns for x in r.cases))
    def test_physically_truncated_asof_prefix_equivalent(self):
        source=make3()
        cut=SEPT_START+141*THREE
        y=replace(source,as_of_ms=cut,original_3m_closed=source.original_3m_closed[:141])
        self.assertEqual(inspect_c27(source,as_of_ms=cut),
                         inspect_c27(y,as_of_ms=cut))
    def test_false_ready_rejected(self):
        source=make3()
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            inspect_c27(replace(source,readiness="READY"),as_of_ms=source.as_of_ms)
    def test_original_source_row_id_tampering_rejected(self):
        source=make3()
        rows=source.original_3m_closed
        forged=replace(source,original_3m_closed=rows[:99]+
                      (replace(rows[99],raw_id="TAMPER"),)+rows[100:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_c27(forged,as_of_ms=forged.as_of_ms)
    def test_original_source_sha_tampering_rejected(self):
        source=make3()
        forged=replace(source,original_zip_shas=("a"*64,)+source.original_zip_shas[1:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_c27(forged,as_of_ms=forged.as_of_ms)

if __name__=="__main__":unittest.main()
