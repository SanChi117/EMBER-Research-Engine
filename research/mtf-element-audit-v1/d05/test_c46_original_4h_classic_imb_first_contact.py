"""C46 original 3m to 4H classic IMB, known-time, first-contact proof tests."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21b_original_3m_raid_break_geometry import _source,_hours,THREE
from c46_original_4h_classic_imb_first_contact import (
    FourBar,FourHourImbCandidate,FOUR,aggregate_original_4h,
    classic_three_fourhour_imb,original_first_contact,inspect_original_4h_imb_source)
from test_c21b_native_3m_vs_5m import make3

def fours(hi1="105",low3="108",hi3="112",low1="95"):
    return tuple(FourBar(k*FOUR,(k+1)*FOUR,
        D(hi1 if k==0 else "107" if k==1 else hi3),
        D(low1 if k==0 else "100" if k==1 else low3),
        "FIRST_"+str(k),"LAST_"+str(k)) for k in range(3))

class C46OriginalNative4hTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=make3(size=500)
        cls.rows=_source(cls.src,cls.src.as_of_ms)
        cls.fours=aggregate_original_4h(_hours(cls.rows))
        cls.out=inspect_original_4h_imb_source(cls.src,as_of_ms=cls.src.as_of_ms)

    def test_bullish_4h_gap_is_source_native(self):
        vals=classic_three_fourhour_imb(fours())
        self.assertEqual(len(vals),1)
        self.assertEqual((vals[0].side,vals[0].bottom,vals[0].top),("LONG","105","108"))
    def test_bearish_4h_gap_is_source_native(self):
        bars=fours("105","82","90","95")
        vals=classic_three_fourhour_imb(bars)
        self.assertEqual(len(vals),1)
        self.assertEqual((vals[0].side,vals[0].bottom,vals[0].top),("SHORT","90","95"))
    def test_no_wick_gap_not_fvg(self):
        self.assertEqual(classic_three_fourhour_imb(fours("105","104","112","95")),())
    def test_source_candidate_known_only_at_third_closed_4h(self):
        c=classic_three_fourhour_imb(fours())[0]
        self.assertEqual(c.fully_known_ms,3*FOUR)
    def test_candidate_carries_three_first_and_last_original_ids(self):
        c=classic_three_fourhour_imb(fours())[0]
        self.assertEqual(c.three_original_source_first_native3m_ids,("FIRST_0","FIRST_1","FIRST_2"))
        self.assertEqual(c.three_original_source_last_native3m_ids,("LAST_0","LAST_1","LAST_2"))
    def test_source_4h_aggregation_from_original_3m_closed_hourly(self):
        self.assertEqual(self.out.complete_original_4h_candles,len(self.fours))
        self.assertEqual(self.out.complete_original_4h_candles,6)
        self.assertEqual(self.fours[0].known_ms-self.fours[0].start_ms,FOUR)
    def test_trailing_incomplete_4h_not_used(self):
        self.assertEqual(len(self.fours),len(_hours(self.rows))//4)
    def test_adapted_original4h_never_author_poi_certified(self):
        self.assertFalse(any(x.candidate.author_poi_certified or x.academic_poi_test_certified
            or x.academic_volume_confirmation_certified for x in self.out.observations))
    def test_original_research_remains_not_trade_ready(self):
        self.assertEqual(self.out.readiness,"NOT_TRADE_READY")
        self.assertEqual((self.out.author_poi_goldens,self.out.orders,self.out.trades),(0,(),()))
    def test_original_complete_prefix_expected_length(self):
        self.assertEqual(self.out.original_native3m_closed,len(self.rows))
    def test_source_first_touch_never_before_zone_known(self):
        self.assertTrue(all(x.first_contact_bar_start_ms is None or
            x.first_contact_bar_start_ms>=x.candidate.fully_known_ms
            for x in self.out.observations))
    def test_full_scanner_is_deterministic_for_same_original(self):
        self.assertEqual(inspect_original_4h_imb_source(self.src,as_of_ms=self.src.as_of_ms),self.out)
    def test_missing_4h_source_hour_closure_rejected(self):
        hs=list(_hours(self.rows))
        hs[3]=replace(hs[3],close_ms=hs[3].close_ms+1)
        with self.assertRaisesRegex(ValueError,"INVALID_HOUR_OR_NATIVE3M_SOURCE"):
            aggregate_original_4h(tuple(hs))
    def test_non_aligned_fourbar_source_rejected(self):
        vals=list(fours())
        vals[1]=replace(vals[1],start_ms=vals[1].start_ms+1)
        with self.assertRaisesRegex(ValueError,"NOT_ORIGINAL_CLOSED_4H_GRID"):
            classic_three_fourhour_imb(tuple(vals))
    def test_candidate_must_be_proven_before_contact(self):
        rows=self.rows
        c=FourHourImbCandidate("LONG",str(rows[400].low),str(rows[400].high),
            self.rows[0].start_ms+2*FOUR,self.rows[0].start_ms,
            self.rows[0].start_ms+FOUR,self.rows[0].start_ms+2*FOUR,
            ("1","2","3"),("4","5","6"))
        x=original_first_contact(rows,c,rows[-1].known_ms)
        self.assertTrue(x.has_complete_original3m_prefix_after_known)
        if x.first_contact_bar_start_ms is not None:
            self.assertGreaterEqual(x.first_contact_bar_start_ms,c.fully_known_ms)
            self.assertIsNotNone(x.first_contact_original3m_id)
    def test_future_unclosed_4h_source_rejected(self):
        c=FourHourImbCandidate("LONG","1","2",self.rows[-1].known_ms+FOUR,0,FOUR,2*FOUR,
            ("1","2","3"),("4","5","6"))
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_PARTIAL_4H"):
            original_first_contact(self.rows,c,self.rows[-1].known_ms)
    def test_author_poi_forgery_rejected(self):
        c=FourHourImbCandidate("LONG","1","2",self.rows[0].start_ms+FOUR,0,FOUR,2*FOUR,
            ("1","2","3"),("4","5","6"),author_poi_certified=True)
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_POI"):
            original_first_contact(self.rows,c,self.rows[-1].known_ms)
    def test_original_prefix_must_be_complete(self):
        c=FourHourImbCandidate("LONG","1","2",self.rows[0].start_ms+FOUR,0,FOUR,2*FOUR,
            ("1","2","3"),("4","5","6"))
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_OR_FUTURE_SOURCE_PREFIX"):
            original_first_contact(self.rows,c,self.rows[-1].known_ms+THREE)
    def test_changed_zone_inverted_bounds_rejected(self):
        c=FourHourImbCandidate("LONG","2","1",self.rows[0].start_ms+FOUR,0,FOUR,2*FOUR,
            ("1","2","3"),("4","5","6"))
        with self.assertRaisesRegex(ValueError,"FORGED_ZONE_BOUNDARY"):
            original_first_contact(self.rows,c,self.rows[-1].known_ms)
    def test_zero_directional_trade_claims(self):
        for obs in self.out.observations:
            self.assertEqual((obs.orders,obs.trades,obs.readiness),((),(),"NOT_TRADE_READY"))
    def test_4h_source_three_candle_requires_close(self):
        self.assertFalse(classic_three_fourhour_imb(fours())[0].author_poi_certified)
    def test_first_contact_is_not_course_verified_first_test(self):
        for obs in self.out.observations:
            self.assertFalse(obs.academic_poi_test_certified)
    def test_fully_closed_4h_source_uses_80_original_3m_bars(self):
        self.assertEqual(FOUR//THREE,80)
    def test_empty_four_bars_has_no_zones(self):
        self.assertEqual(classic_three_fourhour_imb(()),())
    def test_earlier_asof_results_not_more_zones(self):
        earlier=inspect_original_4h_imb_source(self.src,as_of_ms=self.src.as_of_ms-THREE*80)
        self.assertLessEqual(earlier.candidate_count,self.out.candidate_count)

if __name__=="__main__":unittest.main()
