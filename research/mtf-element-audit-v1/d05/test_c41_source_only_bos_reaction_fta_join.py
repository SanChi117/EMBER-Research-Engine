"""C41 negative chronology / original-row source join tests, no trades."""
import unittest
from dataclasses import replace
from c21b_original_3m_raid_break_geometry import _source, THREE
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted
from c38_adapted_post_raid_reaction import scan_adapted_reactions
from c39_adapted_preknown_fta_source import scan_original_preknown_fta
from c40_pre_bos_fta_touch_state import inspect_original_fta_prior_touch, STATES
from c41_source_only_bos_reaction_fta_join import (
    join_c41_source_records,scan_original_c41_source_matrix)
from test_c21b_native_3m_vs_5m import make3

class C41SourceJoins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=make3(size=220)
        cls.asof=cls.src.as_of_ms
        cls.rows=_source(cls.src,cls.asof)
        cls.b=scan_original_3m_adapted(cls.src,as_of_ms=cls.asof)
        cls.r=scan_adapted_reactions(cls.src,as_of_ms=cls.asof)
        cls.f=scan_original_preknown_fta(cls.src,as_of_ms=cls.asof)
        cls.t=inspect_original_fta_prior_touch(cls.src,as_of_ms=cls.asof)
        cls.result=join_c41_source_records(cls.b,cls.r,cls.f,cls.t,cls.rows)

    def join(self, *, b=None,r=None,f=None,t=None,rows=None):
        return join_c41_source_records(
            b if b is not None else self.b,
            r if r is not None else self.r,
            f if f is not None else self.f,
            t if t is not None else self.t,
            rows if rows is not None else self.rows)

    def test_exactly_36_routes_with_all_variants(self):
        self.assertEqual(self.result.route_count,36)
        self.assertEqual(len(set((v.bos,v.reaction,v.fta) for v in self.result.routes)),36)
    def test_parent_cardinality_for_each_of_36(self):
        self.assertTrue(all(len(v.observations)==v.parent_bos_contexts for v in self.result.routes))
    def test_reaction_obstacle_counts_consistent(self):
        for route in self.result.routes:
            self.assertEqual(sum(w.source_reaction_confirmed for w in route.observations),route.source_confirmed_reactions)
            self.assertEqual(sum(w.potential_1h_obstacle_kind is not None for w in route.observations),route.with_preknown_obstacle)
    def test_no_execution_or_instructor_promotion(self):
        self.assertEqual((self.result.author_goldens,self.result.orders,self.result.trades),(0,(),()))
        self.assertEqual(self.result.readiness,"NOT_TRADE_READY")
        for route in self.result.routes:
            self.assertEqual((route.orders,route.trades),((),()))
            for w in route.observations:
                self.assertFalse(w.author_bos_approved or w.author_reaction_approved or w.author_fta_approved or w.paper_signal_allowed)
                self.assertEqual((w.orders,w.trades),((),()))
    def test_pre_bos_reaction_is_not_current_break_bar(self):
        for route in self.result.routes:
            for w in route.observations:
                if w.source_reaction_confirmed:
                    self.assertLessEqual(w.first_reaction_closed_known_ms,w.bos_bar_start_ms)
                    self.assertNotEqual(w.first_reaction_original_native3m_row_id,w.original_bos_native3m_row_id)
    def test_all_obstacle_sources_known_before_bos_start(self):
        for route in self.result.routes:
            for w in route.observations:
                if w.potential_1h_obstacle_source_known_ms is not None:
                    self.assertLessEqual(w.potential_1h_obstacle_source_known_ms,w.bos_bar_start_ms)
                self.assertIn(w.source_prior_touch_classification,STATES)
    def test_forged_symbol_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_SYMBOL_DRIFT"):
            self.join(r=replace(self.r,symbol="FORGED"))
    def test_forged_asof_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_ASOF_DRIFT"):
            self.join(r=replace(self.r,as_of_ms=self.asof+THREE))
    def test_research_module_cannot_be_ready(self):
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            self.join(r=replace(self.r,readiness="READY"))
    def test_forged_author_goldens_refused(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_OR_EXECUTION_READY"):
            self.join(f=replace(self.f,author_approved_targets=1))
    def test_forged_order_refused(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_OR_EXECUTION_READY"):
            self.join(b=replace(self.b,orders=("fake",)))
    def test_deleted_reaction_route_refused(self):
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_PARENT_ROUTE_COUNT"):
            self.join(r=replace(self.r,routes=self.r.routes[:-1]))
    def test_duplicate_fta_route_refused(self):
        x=list(self.f.routes)
        x[-1]=x[-2]
        with self.assertRaisesRegex(ValueError,"DUPLICATED_ROUTE_ID"):
            self.join(f=replace(self.f,routes=tuple(x)))
    def test_parent_original_bos_raw_id_cannot_change(self):
        routes=list(self.b.routes)
        events=list(routes[0].events)
        events[0]=replace(events[0],break_original_native3m_row_id="FAKE_BOS_ROW_SHA")
        routes[0]=replace(routes[0],events=tuple(events))
        with self.assertRaisesRegex(ValueError,"CROSS_MODULE_EVENT_OR_ID_MISMATCH"):
            self.join(b=replace(self.b,routes=tuple(routes)))
    def test_reaction_original_row_id_cannot_change(self):
        x=list(self.r.routes);first=x[0];ev=list(first.observations)
        ev[0]=replace(ev[0],original_bos_break_row_id="FAKE")
        x[0]=replace(first,observations=tuple(ev))
        with self.assertRaisesRegex(ValueError,"CROSS_MODULE_EVENT_OR_ID_MISMATCH"):
            self.join(r=replace(self.r,routes=tuple(x)))
    def test_touch_can_not_claim_author_freshness(self):
        t=dict(self.t)
        routes=list(t["routes"]);one=dict(routes[0])
        obs=list(one["observations"])
        obs[0]=replace(obs[0],author_freshness_certified=True)
        one["observations"]=tuple(obs);routes[0]=one;t["routes"]=tuple(routes)
        with self.assertRaisesRegex(ValueError,"FORGED_CHILD_AUTHOR_OR_EXECUTION"):
            self.join(t=t)
    def test_reaction_future_bar_refused(self):
        x=list(self.r.routes)
        found=False
        for idx,route in enumerate(x):
            obs=list(route.observations)
            for j,w in enumerate(obs):
                if w.condition_satisfied:
                    obs[j]=replace(w,first_confirmed_reaction_bar_closed_ms=w.bos_break_bar_start_ms+THREE)
                    x[idx]=replace(route,observations=tuple(obs))
                    found=True
                    break
            if found:break
        self.assertTrue(found,"C41 synthetic fixture must include positive adapted reaction")
        with self.assertRaisesRegex(ValueError,"REACTION_FUTURE_OR_SOURCE_ID"):
            self.join(r=replace(self.r,routes=tuple(x)))
    def test_bos_future_bar_closed_beyond_source_asof_refused(self):
        b=replace(self.b,as_of_ms=self.asof+THREE)
        with self.assertRaisesRegex(ValueError,"SOURCE_ASOF_DRIFT"):
            self.join(b=b)
    def test_full_source_scanner_matches_component_join(self):
        computed=scan_original_c41_source_matrix(self.src,as_of_ms=self.asof)
        self.assertEqual(computed,self.result)

if __name__=="__main__":unittest.main()
