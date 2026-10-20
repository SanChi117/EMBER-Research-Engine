"""C37 independent 3m bar-by-bar adapted BOS scanner: no future, no fills."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21b_original_3m_raid_break_geometry import (
    _source,_hours,_swings,observe_native3m_raid_break)
from c20b_hourly_fractal_source_observer import observe_fractals_and_first_breach
from c21_native3m_source_bridge import THREE,SEPT_START
from c36_adapted_pivot_hypotheses import VARIANTS
from c37_native_adapted_bos_event_scanner import (
    scan_original_3m_adapted,_scan_one,_choose,_eligible,
    _adapted_event_key,_c21_event_key)
from test_c21b_native_3m_vs_5m import make3

def source_and_raid(**kw):
    source=make3(**kw)
    rows=_source(source,source.as_of_ms)
    hours=_hours(rows)
    _,raids=observe_fractals_and_first_breach(hours)
    raid=next(r for r in raids if r.fractal.kind=="BSL" and
              r.fractal.center_ms==SEPT_START+3600000)
    return source,rows,raid,_swings(rows)

class C37IndependentChronologicalEventScanTests(unittest.TestCase):
    def test_four_route_scans_present(self):
        x=make3()
        result=scan_original_3m_adapted(x,as_of_ms=x.as_of_ms)
        self.assertEqual(tuple(z.hypothesis_id for z in result.routes),VARIANTS)
    def test_latest_precisely_matches_C21_original_parent(self):
        x=make3()
        r=scan_original_3m_adapted(x,as_of_ms=x.as_of_ms)
        frozen=observe_native3m_raid_break(x,as_of_ms=x.as_of_ms)
        self.assertEqual(tuple(_adapted_event_key(e) for e in r.routes[0].events),
                         tuple(_c21_event_key(e) for e in frozen.potential_breaks))
    def test_true_no_author_selection(self):
        x=scan_original_3m_adapted(make3(),as_of_ms=make3().as_of_ms)
        self.assertEqual(x.author_bos_approved,0)
        self.assertEqual(x.paper_signals,0)
        self.assertEqual((x.orders,x.trades),((),()))
        self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_all_four_variants_never_create_trade(self):
        r=scan_original_3m_adapted(make3(),as_of_ms=make3().as_of_ms)
        for route in r.routes:
            self.assertEqual(route.readiness,"NOT_TRADE_READY")
            self.assertEqual((route.orders,route.trades),((),()))
            for e in route.events:
                self.assertFalse(e.paper_trade_allowed)
                self.assertFalse(e.author_bos_approved)
                self.assertEqual((e.orders,e.trades),((),()))
    def test_break_known_only_after_full_3m_close(self):
        x=make3()
        r=scan_original_3m_adapted(x,as_of_ms=x.as_of_ms)
        for route in r.routes:
            for e in route.events:
                self.assertEqual(e.break_bar_closed_known_ms,
                                 e.break_bar_start_ms+THREE)
                self.assertGreaterEqual(x.as_of_ms,e.break_bar_closed_known_ms)
    def test_swing_right_candle_known_by_break_bar_start(self):
        x=make3()
        for route in scan_original_3m_adapted(x,as_of_ms=x.as_of_ms).routes:
            self.assertTrue(all(e.swing_confirmed_ms<=e.break_bar_start_ms
                                for e in route.events))
    def test_initial_asof_no_future_3m_bos(self):
        x=make3()
        cut=SEPT_START+7*3600000
        z=scan_original_3m_adapted(x,as_of_ms=cut)
        self.assertTrue(all(not route.events for route in z.routes))
    def test_one_closed_bar_changes_observability(self):
        x=make3()
        at=SEPT_START+7*3600000
        before=scan_original_3m_adapted(x,as_of_ms=at)
        after=scan_original_3m_adapted(x,as_of_ms=at+THREE)
        self.assertEqual(len(before.routes[0].events),0)
        self.assertGreaterEqual(len(after.routes[0].events),1)
    def test_physical_prefix_equal_to_full_asof(self):
        x=make3()
        cut=SEPT_START+141*THREE
        physically=replace(x,as_of_ms=cut,original_3m_closed=x.original_3m_closed[:141])
        a=scan_original_3m_adapted(x,as_of_ms=cut)
        b=scan_original_3m_adapted(physically,as_of_ms=cut)
        self.assertEqual(a,b)
    def test_pre_raid_no_event(self):
        x=make3()
        z=scan_original_3m_adapted(x,as_of_ms=SEPT_START+5*3600000)
        self.assertTrue(all(len(route.events)==0 for route in z.routes))
    def test_body_breach_not_wick_raid(self):
        x=make3(body=True)
        r=scan_original_3m_adapted(x,as_of_ms=x.as_of_ms)
        self.assertTrue(all(not any(e.raid_fractal_center_ms==SEPT_START+3600000
            for e in route.events) for route in r.routes))
    def test_raid_extreme_invalidates_break_even_same_bar(self):
        x=make3(invalid=True)
        r=scan_original_3m_adapted(x,as_of_ms=x.as_of_ms)
        self.assertTrue(all(not any(e.raid_fractal_center_ms==SEPT_START+3600000
            for e in route.events) for route in r.routes))
    def test_wrong_signed_swing_never_eligible(self):
        x,rows,raid,swings=source_and_raid()
        for s in swings:
            if s.kind=="HIGH":
                self.assertFalse(_eligible(raid,s,True))
    def test_reject_swing_center_before_1h_raid(self):
        x,rows,raid,swings=source_and_raid()
        from c21b_original_3m_raid_break_geometry import ThreeSwing
        s=ThreeSwing("LOW",D("99"),raid.first_breach_ms-THREE,
                     raid.first_breach_close_ms,("a","b","c"))
        self.assertFalse(_eligible(raid,s,True))
    def test_reject_swing_on_wrong_raid_side(self):
        x,rows,raid,swings=source_and_raid()
        from c21b_original_3m_raid_break_geometry import ThreeSwing
        s=ThreeSwing("LOW",raid.fractal.level,raid.first_breach_ms,
                     raid.first_breach_close_ms,("a","b","c"))
        self.assertFalse(_eligible(raid,s,True))
    def test_reject_unknown_selection_variant(self):
        x,rows,raid,swings=source_and_raid()
        with self.assertRaisesRegex(ValueError,"C37_UNKNOWN_ROUTE"):
            _scan_one(raid,rows,swings,"CUSTOM_PROFIT_OPTIMIZED")
    def test_selection_bsl_deep_below_nearest(self):
        from c21b_original_3m_raid_break_geometry import ThreeSwing
        s1=ThreeSwing("LOW",D("94"),SEPT_START+THREE,SEPT_START+3*THREE,("a","b","c"))
        s2=ThreeSwing("LOW",D("96"),SEPT_START+5*THREE,SEPT_START+7*THREE,("d","e","f"))
        self.assertEqual(_choose(s1,s2,"DEEP_RAID_SIDE_V1",True),s1)
        self.assertEqual(_choose(s1,s2,"NEAREST_RAID_SIDE_V1",True),s2)
    def test_selection_ssl_deep_above_nearest(self):
        from c21b_original_3m_raid_break_geometry import ThreeSwing
        s1=ThreeSwing("HIGH",D("104"),SEPT_START+THREE,SEPT_START+3*THREE,("a","b","c"))
        s2=ThreeSwing("HIGH",D("106"),SEPT_START+5*THREE,SEPT_START+7*THREE,("d","e","f"))
        self.assertEqual(_choose(s1,s2,"DEEP_RAID_SIDE_V1",False),s2)
        self.assertEqual(_choose(s1,s2,"NEAREST_RAID_SIDE_V1",False),s1)
    def test_latest_vs_earliest_switch(self):
        from c21b_original_3m_raid_break_geometry import ThreeSwing
        s1=ThreeSwing("LOW",D("94"),SEPT_START+THREE,SEPT_START+3*THREE,("a","b","c"))
        s2=ThreeSwing("LOW",D("96"),SEPT_START+5*THREE,SEPT_START+7*THREE,("d","e","f"))
        self.assertEqual(_choose(s1,s2,"LATEST_CONFIRMED_V1",True),s2)
        self.assertEqual(_choose(s1,s2,"EARLIEST_CONFIRMED_V1",True),s1)
    def test_unconfirmed_1h_raid_returns_none(self):
        x,rows,raid,swings=source_and_raid()
        y=replace(raid,confirmed_at_ms=None)
        self.assertIsNone(_scan_one(y,rows,swings,"LATEST_CONFIRMED_V1"))
    def test_removed_future_3m_rows_preserve_prefix(self):
        x=make3()
        cut=SEPT_START+7*3600000+THREE
        full=scan_original_3m_adapted(x,as_of_ms=cut)
        n=(cut-SEPT_START)//THREE
        cropped=replace(x,as_of_ms=cut,original_3m_closed=x.original_3m_closed[:n])
        self.assertEqual(full,scan_original_3m_adapted(cropped,as_of_ms=cut))
    def test_nonclosed_candle_source_rejected(self):
        x=make3()
        with self.assertRaisesRegex(ValueError,"FUTURE_UNCLOSED"):
            scan_original_3m_adapted(x,as_of_ms=x.as_of_ms-1)
    def test_forged_price_sha_rejected(self):
        x=make3()
        p=x.original_3m_closed
        fake=replace(x,original_3m_closed=p[:13]+(
            replace(p[13],raw_id="forged"),)+p[14:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            scan_original_3m_adapted(fake,as_of_ms=x.as_of_ms)
    def test_ready_forgery_rejected(self):
        x=replace(make3(),readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            scan_original_3m_adapted(x,as_of_ms=x.as_of_ms)
    def test_scan_uses_frozen_academic_core_identity(self):
        from c36_adapted_slot_registry import ACADEMIC_CORE_ID,FROZEN_C33_SHA
        x=make3()
        r=scan_original_3m_adapted(x,as_of_ms=x.as_of_ms)
        self.assertEqual(r.academic_core_sha256,ACADEMIC_CORE_ID)
        self.assertEqual(r.frozen_academic_source_git_blob,FROZEN_C33_SHA)
    def test_provenance_bar_id_pinned_to_native_sha(self):
        x=make3()
        r=scan_original_3m_adapted(x,as_of_ms=x.as_of_ms)
        ids={row.raw_id for row in x.original_3m_closed}
        for route in r.routes:
            for e in route.events:
                self.assertIn(e.swing_center_native3m_row_id,ids)
                self.assertIn(e.break_original_native3m_row_id,ids)
    def test_c21_original_event_count_never_wrong(self):
        x=make3()
        a=scan_original_3m_adapted(x,as_of_ms=x.as_of_ms)
        b=observe_native3m_raid_break(x,as_of_ms=x.as_of_ms)
        self.assertEqual(a.original_C21_research_event_count,len(b.potential_breaks))

if __name__=="__main__":unittest.main()
