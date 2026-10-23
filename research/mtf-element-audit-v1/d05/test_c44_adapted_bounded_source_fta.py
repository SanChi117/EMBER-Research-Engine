"""C44 no-lookahead bounded source FTA research negative and truth-table tests."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace
from c21b_original_3m_raid_break_geometry import _source,_hours,THREE,HOUR
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted
from c39_adapted_preknown_fta_source import PotentialObstacle
from c40_pre_bos_fta_touch_state import TouchAudit
from c43_adapted_per_candidate_fta_rerank import CandidateObservation
from c44_adapted_bounded_source_fta import (
    DAY,FOUR,POLICIES,ClosedRange,CandidateBound,
    completed_native_candle_ranges,latest_completed_range,bound_info,eligible,
    scan_original_c44_bounded_source)
from test_c21b_native_3m_vs_5m import make3

def synthetic_candidate(state="NO_PRIOR_SOURCE_TOUCH",known=0,level="101",distance="1"):
    src=PotentialObstacle("BSL_1H_FRACTAL",known,level,"a-original","z-original",distance)
    hit=TouchAudit("BTCUSDT","LATEST_CONFIRMED_V1","CLOSEST_PRIOR_1H_OBSTACLE_V1",
        "BOS-native3m","BSL_1H_FRACTAL",level,known,None,None,None,state)
    return CandidateObservation(src,hit)

def research_event(start=25*HOUR,close="100",side="LONG"):
    return SimpleNamespace(break_bar_start_ms=start,break_bar_closed_known_ms=start+THREE,
                           break_close=close,side=side)

def reference(kind="4H",low="99",high="102",close=24*HOUR):
    return ClosedRange(kind,close-(FOUR if kind=="4H" else DAY),close,
        D(low),D(high),"source0","sourceLast")

def metrics(age=1*HOUR,dist="1",state="NO_PRIOR_SOURCE_TOUCH",start=25*HOUR):
    return CandidateBound("BSL_1H_FRACTAL","101","first","last",start-age,age,dist,state)

class C44BoundedNegative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=make3(size=220)
        cls.output=scan_original_c44_bounded_source(cls.source,as_of_ms=cls.source.as_of_ms)
        cls.hours=_hours(_source(cls.source,cls.source.as_of_ms))

    def test_36_original_source_routes(self):
        self.assertEqual(len(self.output.routes),36)
        self.assertEqual(len(set((r.bos,r.reaction,r.fta) for r in self.output.routes)),36)
    def test_four_explicit_adapted_policies(self):
        self.assertEqual(len(POLICIES),4)
        self.assertEqual(len(set(POLICIES)),4)
    def test_no_trades_or_author_poi_goldens(self):
        self.assertEqual((self.output.orders,self.output.trades,
            self.output.author_poi_goldens,self.output.academic_author_fta_goldens),((),(),0,0))
        self.assertEqual(self.output.readiness,"NOT_TRADE_READY")
    def test_decisions_not_known_before_break_close(self):
        for rt in self.output.routes:
            for c in rt.contexts:
                for d in c.decisions:
                    self.assertEqual(d.decision_known_at_ms,c.original_bos_closed_ms)
                    self.assertGreater(d.decision_known_at_ms,c.original_bos_start_ms)
    def test_route_policy_counts_match_events(self):
        for route in self.output.routes:
            for i,p in enumerate(POLICIES):
                self.assertEqual(route.selected_count_by_policy[p],
                    sum(c.decisions[i].selected_candidate is not None for c in route.contexts))
    def test_no_fake_orders_in_selected_contexts(self):
        for rt in self.output.routes:
            for c in rt.contexts:
                self.assertEqual((c.orders,c.trades),((),()))
                for d in c.decisions:
                    self.assertFalse(d.author_fta_verified or d.author_poi_verified or d.trade_allowed)
    def test_24h_1pct_passes_exact_bounds(self):
        self.assertTrue(eligible(metrics(age=24*HOUR,dist="1"),POLICIES[0],None,None))
    def test_24h_1pct_excludes_old_candidate(self):
        self.assertFalse(eligible(metrics(age=24*HOUR+1,dist="1"),POLICIES[0],None,None))
    def test_24h_1pct_excludes_far_candidate(self):
        self.assertFalse(eligible(metrics(age=HOUR,dist="1.000001"),POLICIES[0],None,None))
    def test_72h_3pct_accepts_2pct_older_than_24h(self):
        self.assertFalse(eligible(metrics(age=48*HOUR,dist="2"),POLICIES[0],None,None))
        self.assertTrue(eligible(metrics(age=48*HOUR,dist="2"),POLICIES[1],None,None))
    def test_72h_3pct_rejects_72h_plus_1ms(self):
        self.assertFalse(eligible(metrics(age=72*HOUR+1,dist="2"),POLICIES[1],None,None))
    def test_72h_3pct_rejects_3pct_plus_epsilon(self):
        self.assertFalse(eligible(metrics(age=HOUR,dist="3.000001"),POLICIES[1],None,None))
    def test_touch_history_always_required(self):
        for p in POLICIES:
            self.assertFalse(eligible(metrics(state="PRIOR_BOUNDARY_TOUCH"),p,reference(),reference("1D")))
    def test_prev4h_range_proxy_accepts_inside(self):
        self.assertTrue(eligible(metrics(),POLICIES[2],reference("4H"),reference("1D")))
    def test_prev4h_range_proxy_rejects_outside(self):
        self.assertFalse(eligible(metrics(),POLICIES[2],reference("4H","80","90"),reference("1D")))
    def test_prev1d_range_proxy_accepts_inside(self):
        self.assertTrue(eligible(metrics(),POLICIES[3],reference("4H"),reference("1D")))
    def test_prev1d_range_proxy_rejects_outside(self):
        self.assertFalse(eligible(metrics(),POLICIES[3],reference("4H"),reference("1D","80","90")))
    def test_no_completed_htf_not_invented(self):
        self.assertFalse(eligible(metrics(),POLICIES[2],None,reference("1D")))
        self.assertFalse(eligible(metrics(),POLICIES[3],reference("4H"),None))
    def test_unknown_policy_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_BOUNDED_POLICY"):
            eligible(metrics(),"AUTHOR_ADOPTED",None,None)
    def test_source_age_is_based_on_bos_start_not_close(self):
        c=synthetic_candidate(known=HOUR,level="101",distance="1")
        record=bound_info(c,research_event(25*HOUR))
        self.assertEqual(record.source_age_at_bos_start_ms,24*HOUR)
    def test_distance_is_decimal_percentage_from_retrospective_close(self):
        c=synthetic_candidate(known=HOUR,level="101",distance="1")
        v=bound_info(c,research_event(25*HOUR))
        self.assertEqual(D(v.distance_from_retrospective_bos_close_pct),D("1"))
    def test_forged_delta_relative_to_original_c39_rejected(self):
        c=synthetic_candidate(known=HOUR,level="102",distance="1")
        with self.assertRaisesRegex(ValueError,"C39_DISTANCE_SOURCE_DRIFT"):
            bound_info(c,research_event())
    def test_future_original_1h_source_rejected(self):
        c=synthetic_candidate(known=26*HOUR,level="101",distance="1")
        with self.assertRaisesRegex(ValueError,"FUTURE_SOURCE_CANDIDATE"):
            bound_info(c,research_event())
    def test_author_fake_fta_rejected(self):
        c=synthetic_candidate(known=HOUR)
        c=replace(c,source=replace(c.source,author_priority_attested=True))
        with self.assertRaisesRegex(ValueError,"FORGED_SOURCE_OR_TRADE"):
            bound_info(c,research_event())
    def test_htf_4h_requires_completely_closed_original_hours(self):
        hrs=_hours(_source(self.source,self.source.as_of_ms))
        ranges=completed_native_candle_ranges(hrs,"4H")
        self.assertTrue(all(v.close_ms%FOUR==0 and v.close_ms-v.start_ms==FOUR for v in ranges))
        self.assertTrue(all(v.source_first_native3m_row_id and v.source_last_native3m_row_id for v in ranges))
    def test_htf_one_day_cannot_use_incomplete_day(self):
        self.assertEqual(completed_native_candle_ranges(self.hours,"1D"),())
    def test_htf_future_4h_bar_not_admitted(self):
        x=reference(close=24*HOUR)
        y=reference(close=28*HOUR)
        self.assertEqual(latest_completed_range((x,y),25*HOUR),x)
    def test_htf_not_yet_closed_returns_none(self):
        self.assertIsNone(latest_completed_range((reference(close=28*HOUR),),25*HOUR))
    def test_modified_1h_source_grid_rejected(self):
        hours=list(self.hours)
        hours[3]=replace(hours[3],close_ms=hours[3].close_ms+1)
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_CLOSED_HTF_SOURCE_TIME"):
            completed_native_candle_ranges(tuple(hours),"4H")
    def test_24h_bound_subset_of_72h_bound(self):
        for dist in ("0.5","1","1.0001","2","3","3.0001"):
            for age in (0,HOUR,24*HOUR,24*HOUR+1,72*HOUR,72*HOUR+1):
                v=metrics(age,dist)
                if eligible(v,POLICIES[0],None,None):
                    self.assertTrue(eligible(v,POLICIES[1],None,None))
    def test_full_scanner_deterministic_same_asof(self):
        self.assertEqual(scan_original_c44_bounded_source(
            self.source,as_of_ms=self.source.as_of_ms),self.output)

if __name__=="__main__":unittest.main()
