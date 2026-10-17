"""C25 original-source/session DST/FTA negative controls, PAPER ONLY."""
import unittest
from dataclasses import replace
from datetime import datetime,timezone
from decimal import Decimal
from c21_native3m_source_bridge import SEPT_START,THREE
from c25_session_freshness_target_source import (
    inspect_c25,scenario,_nearest_geometric_target,ZONES)
from c20b_hourly_fractal_source_observer import HourFractal
from test_c21b_native_3m_vs_5m import make3

def at(s):
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()*1000)

class C25AuthorTimeUnresolved(unittest.TestCase):
    def test_previous_day_is_not_any_previous_session(self):
        r=scenario(at("2026-10-16T18:00:00"),at("2026-10-17T10:00:00"),"UTC")
        self.assertTrue(r.pivot_was_previous_local_day)
        self.assertFalse(r.pivot_in_previous_09_17_session)
    def test_precise_session_timezone_changes_previous_day(self):
        p=at("2026-10-16T22:00:00")
        r=at("2026-10-17T10:00:00")
        self.assertTrue(scenario(p,r,"UTC").pivot_was_previous_local_day)
        self.assertFalse(scenario(p,r,"Europe/Kyiv").pivot_was_previous_local_day)
    def test_london_dst_changes_utc_offset(self):
        a=scenario(at("2026-03-27T10:00:00"),at("2026-03-28T10:00:00"),"Europe/London")
        b=scenario(at("2026-03-29T10:00:00"),at("2026-03-30T10:00:00"),"Europe/London")
        self.assertEqual(a.raid_local_utc_offset_minutes,0)
        self.assertEqual(b.raid_local_utc_offset_minutes,60)
    def test_kyiv_dst_changes_utc_offset(self):
        a=scenario(at("2026-03-27T10:00:00"),at("2026-03-28T10:00:00"),"Europe/Kyiv")
        b=scenario(at("2026-03-29T10:00:00"),at("2026-03-30T10:00:00"),"Europe/Kyiv")
        self.assertEqual(a.raid_local_utc_offset_minutes,120)
        self.assertEqual(b.raid_local_utc_offset_minutes,180)
    def test_invented_author_zone_and_future_fractal_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNATTESTED_ZONE"):
            scenario(at("2026-10-16T10:00:00"),at("2026-10-17T10:00:00"),"Europe/Invented")
        with self.assertRaisesRegex(ValueError,"FUTURE_PARENT"):
            scenario(1000,1000,"UTC")
    def test_fta_target_cannot_use_future_1h_fractal(self):
        pivot=HourFractal("SSL",Decimal("90"),100,500,())
        too_late=HourFractal("SSL",Decimal("99"),200,900,())
        found=_nearest_geometric_target((pivot,too_late),"SHORT",Decimal("100"),600)
        self.assertEqual(found,pivot)
        self.assertIsNone(_nearest_geometric_target((too_late,),"SHORT",Decimal("100"),600))
    def test_wrong_side_and_equal_target_excluded(self):
        pivots=(HourFractal("BSL",Decimal("100"),100,500,()),
            HourFractal("SSL",Decimal("100"),100,500,()))
        self.assertIsNone(_nearest_geometric_target(pivots,"LONG",Decimal("100"),600))
        self.assertIsNone(_nearest_geometric_target(pivots,"SHORT",Decimal("100"),600))
    def test_source_research_cannot_approve_author_trade(self):
        x=make3()
        r=inspect_c25(x,as_of_ms=x.as_of_ms)
        self.assertEqual(r.author_approved_trades,0)
        self.assertEqual(r.readiness,"NOT_TRADE_READY")
        self.assertTrue(all(len(c.zones)==3 for c in r.cases))
        self.assertTrue(all(not c.author_session_attested and not c.author_fta_attested
                            and not c.author_stop_buffer_attested
                            and not c.author_approved_trade for c in r.cases))
    def test_no_future_prefix(self):
        x=make3()
        cut=SEPT_START+141*THREE
        trunc=replace(x,as_of_ms=cut,original_3m_closed=x.original_3m_closed[:141])
        self.assertEqual(inspect_c25(x,as_of_ms=cut),inspect_c25(trunc,as_of_ms=cut))
    def test_fake_ready_and_forged_native_row_rejected(self):
        x=make3()
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            inspect_c25(replace(x,readiness="READY"),as_of_ms=x.as_of_ms)
        rows=x.original_3m_closed
        wrong=replace(x,original_3m_closed=rows[:100]+(replace(rows[100],raw_id="fake"),)+rows[101:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_c25(wrong,as_of_ms=wrong.as_of_ms)
