"""C43 indexed source candidate first-touches, alternatives, chronology & fail-closed guards."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c21b_original_3m_raid_break_geometry import _source, THREE
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted
from c39_adapted_preknown_fta_source import PotentialObstacle
from c40_pre_bos_fta_touch_state import TouchAudit
from c42_adapted_source_fta_eligibility import ELIGIBILITY_POLICIES
from c43_adapted_per_candidate_fta_rerank import (
    Original3mFirstTouchIndex,CandidateObservation,_reorder,_allow,
    choose_ranked_candidate,scan_original_per_candidate_fta_rerank,
    audit_individual_candidate,_source_registry,FRACTALS,IMBS)
from test_c21b_native_3m_vs_5m import make3

def candidate(kind,state,num):
    s=PotentialObstacle(kind,THREE*2,str(D(100+num)),f"first{num}",f"last{num}",str(num))
    t=TouchAudit("BTCUSDT","LATEST_CONFIRMED_V1","CLOSEST_PRIOR_1H_OBSTACLE_V1",
        "BOSROW",kind,s.source_level,s.source_known_ms,
        THREE*3 if state!="NO_PRIOR_SOURCE_TOUCH" else None,
        "TOUCHROW" if state!="NO_PRIOR_SOURCE_TOUCH" else None,
        THREE*4 if state=="PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL" else None,state)
    return CandidateObservation(s,t)

class C43SourcePerCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=make3(size=220)
        cls.rows=_source(cls.src,cls.src.as_of_ms)
        cls.bos=scan_original_3m_adapted(cls.src,as_of_ms=cls.src.as_of_ms)
        cls.out=scan_original_per_candidate_fta_rerank(cls.src,as_of_ms=cls.src.as_of_ms)
        cls.index=Original3mFirstTouchIndex(cls.rows)

    def test_36_source_routes_all_present(self):
        self.assertEqual(len(self.out.routes),36)
        self.assertEqual(len(set((x.bos,x.reaction,x.fta) for x in self.out.routes)),36)
    def test_three_stable_policy_names(self):
        self.assertEqual(self.out.adapted_policies,ELIGIBILITY_POLICIES)
    def test_nested_counts(self):
        for r in self.out.routes:
            a,b,c=[r.selected_by_policy[p] for p in ELIGIBILITY_POLICIES]
            self.assertGreaterEqual(a,b)
            self.assertGreaterEqual(b,c)
    def test_counts_correspond_to_contexts(self):
        for r in self.out.routes:
            self.assertEqual(r.parent_contexts,len(r.contexts))
            for i,p in enumerate(ELIGIBILITY_POLICIES):
                self.assertEqual(r.selected_by_policy[p],
                    sum(c.decisions[i].selected_candidate is not None for c in r.contexts))
    def test_parent_original_bos_closes_are_decision_times(self):
        for route in self.out.routes:
            for c in route.contexts:
                self.assertEqual(c.bos_bar_closed_known_ms,c.bos_bar_start_ms+THREE)
                self.assertTrue(all(d.known_at_ms==c.bos_bar_closed_known_ms for d in c.decisions))
    def test_unfiltered_candidate_never_substituted(self):
        for r in self.out.routes:
            for c in r.contexts:
                d=c.decisions[0]
                self.assertFalse(d.substituted_after_original_gate_rejection)
                self.assertEqual(d.selected_candidate,c.original_c39_candidate)
    def test_no_author_fta_order_or_trades(self):
        self.assertEqual((self.out.author_fta_goldens,self.out.orders,self.out.trades),(0,(),()))
        self.assertEqual(self.out.readiness,"NOT_TRADE_READY")
        for route in self.out.routes:
            for c in route.contexts:
                self.assertEqual((c.orders,c.trades),((),()))
                for decision in c.decisions:
                    self.assertFalse(decision.author_fta_approved or decision.order_allowed)
    def test_first_touch_index_finds_proper_first_high(self):
        x=self.rows[10]
        i=self.index.find_first(10,11,high_floor=x.high)
        self.assertEqual(i,10)
    def test_first_touch_index_strict_high_equal_not_sweep(self):
        x=self.rows[10]
        self.assertIsNone(self.index.find_first(10,11,high_floor=x.high,high_strict=True))
    def test_first_touch_index_strict_low_equal_not_sweep(self):
        x=self.rows[10]
        self.assertIsNone(self.index.find_first(10,11,low_cap=x.low,low_strict=True))
    def test_first_touch_gap_both_wicks_same_bar(self):
        x=self.rows[10]
        self.assertEqual(self.index.find_first(10,11,low_cap=x.low,high_floor=x.high),10)
    def test_gap_requires_both_conditions_on_same_original3m_bar(self):
        x=self.rows[10]
        low=x.low
        high=x.high
        self.assertIsNone(self.index.find_first(10,11,low_cap=low-1,high_floor=high+1))
    def test_empty_search_window_returns_none(self):
        self.assertIsNone(self.index.find_first(10,10,high_floor=self.rows[10].high))
    def test_invalid_native_window_rejected(self):
        with self.assertRaisesRegex(ValueError,"NATIVE3M_RANGE_INVALID"):
            self.index.find_first(11,10,low_cap=D(1))
    def test_non_contiguous_original_grid_rejected(self):
        rows=list(self.rows)
        rows[6]=replace(rows[6],start_ms=rows[6].start_ms+1)
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_NATIVE3M_GRID"):
            Original3mFirstTouchIndex(tuple(rows))
    def test_closest_priority_retains_distance_sort(self):
        a=candidate(FRACTALS[0],"NO_PRIOR_SOURCE_TOUCH",1)
        b=candidate(IMBS[0],"NO_PRIOR_SOURCE_TOUCH",2)
        self.assertEqual(_reorder((a,b),"CLOSEST_PRIOR_1H_OBSTACLE_V1"),(a,b))
    def test_fractal_family_priority_is_local_adaptation(self):
        a=candidate(IMBS[0],"NO_PRIOR_SOURCE_TOUCH",1)
        b=candidate(FRACTALS[0],"NO_PRIOR_SOURCE_TOUCH",2)
        self.assertEqual(_reorder((a,b),"FRACTAL_FAMILY_PRIORITY_V1"),(b,a))
    def test_imb_family_priority_is_local_adaptation(self):
        a=candidate(FRACTALS[0],"NO_PRIOR_SOURCE_TOUCH",1)
        b=candidate(IMBS[0],"NO_PRIOR_SOURCE_TOUCH",2)
        self.assertEqual(_reorder((a,b),"CLASSIC_IMB_FAMILY_PRIORITY_V1"),(b,a))
    def test_strict_gate_skips_swept_candidate_to_fresh_alternate(self):
        a=candidate(FRACTALS[0],"PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL",1)
        b=candidate(IMBS[0],"NO_PRIOR_SOURCE_TOUCH",2)
        self.assertEqual(choose_ranked_candidate((a,b),ELIGIBILITY_POLICIES[1]),(1,b))
    def test_no_touch_gate_skips_boundary_touched_first(self):
        a=candidate(FRACTALS[0],"PRIOR_BOUNDARY_TOUCH",1)
        b=candidate(IMBS[0],"NO_PRIOR_SOURCE_TOUCH",2)
        self.assertEqual(choose_ranked_candidate((a,b),ELIGIBILITY_POLICIES[2]),(1,b))
    def test_no_touch_gate_no_alternative_returns_none(self):
        a=candidate(FRACTALS[0],"PRIOR_BOUNDARY_TOUCH",1)
        b=candidate(IMBS[0],"PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL",2)
        self.assertIsNone(choose_ranked_candidate((a,b),ELIGIBILITY_POLICIES[2]))
    def test_any_preknown_policy_selects_first_even_if_crossed(self):
        a=candidate(FRACTALS[0],"PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL",1)
        b=candidate(IMBS[0],"NO_PRIOR_SOURCE_TOUCH",2)
        self.assertEqual(choose_ranked_candidate((a,b),ELIGIBILITY_POLICIES[0]),(0,a))
    def test_forged_candidate_type_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_RANKED_CANDIDATE"):
            choose_ranked_candidate(("unknown",),ELIGIBILITY_POLICIES[0])
    def test_unknown_touch_policy_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_TOUCH_POLICY"):
            choose_ranked_candidate((candidate(FRACTALS[0],"NO_PRIOR_SOURCE_TOUCH",1),),"GOLDEN")
    def test_unknown_touch_state_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_INDIVIDUAL_CANDIDATE_TOUCH"):
            _allow("AUTHOR_CERTIFIED",ELIGIBILITY_POLICIES[0])
    def test_original_scanner_stability_on_same_source(self):
        self.assertEqual(scan_original_per_candidate_fta_rerank(self.src,as_of_ms=self.src.as_of_ms),self.out)
    def test_no_unregistered_duplicate_route_promotion(self):
        self.assertTrue(all(len(set(p.eligibility_policy_id for p in c.decisions))==3
            for r in self.out.routes for c in r.contexts))
    def test_candidate_registry_includes_both_directional_gap_boundaries(self):
        # Direct proof that original 1H source gap may be evaluated from
        # either direction, but never with an invented source row ID.
        from c28_source_fta_inventory import classic_1h_imb
        from c43_adapted_per_candidate_fta_rerank import _hours
        gaps=classic_1h_imb(_hours(self.rows))
        reg=_source_registry((),gaps)
        for g in gaps:
            for px in (g.bottom,g.top):
                key=(g.kind,g.known_ms,str(px),g.original_1h_row_ids[0],g.original_1h_row_ids[-1])
                self.assertIn(key,reg)

if __name__=="__main__": unittest.main()
