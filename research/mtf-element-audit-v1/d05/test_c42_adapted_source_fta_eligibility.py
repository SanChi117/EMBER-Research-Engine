"""C42 source-only eligibility policy truth-table and adversarial tests."""
import unittest
from dataclasses import replace
from c21b_original_3m_raid_break_geometry import THREE
from c41_source_only_bos_reaction_fta_join import scan_original_c41_source_matrix
from c42_adapted_source_fta_eligibility import (
    ELIGIBILITY_POLICIES, decide_source_eligibility,
    apply_source_eligibility,scan_original_source_eligibility)
from test_c21b_native_3m_vs_5m import make3

class C42EligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=make3(size=220)
        cls.parent=scan_original_c41_source_matrix(cls.src,as_of_ms=cls.src.as_of_ms)
        cls.out=apply_source_eligibility(cls.parent)
        cls.real=cls.parent.routes[0].observations[0]

    def scenario(self,state="NO_PRIOR_SOURCE_TOUCH"):
        c=self.real
        if state=="NO_PREKNOWN_FTA_CANDIDATE":
            return replace(c,potential_1h_obstacle_kind=None,
                potential_1h_obstacle_source_known_ms=None,
                original_potential_1h_source_first_native3m_row_id=None,
                source_prior_touch_classification=state,
                first_prior_touch_original_native3m_row_id=None,
                first_prior_full_sweep_or_traversal_ms=None)
        return replace(c,potential_1h_obstacle_kind="BSL_1H_FRACTAL",
            potential_1h_obstacle_source_known_ms=c.bos_bar_start_ms-20*THREE,
            original_potential_1h_source_first_native3m_row_id="SOURCE_FIRST_ID",
            source_prior_touch_classification=state,
            first_prior_touch_original_native3m_row_id=("TOUCH_SOURCE_ID" if state!="NO_PRIOR_SOURCE_TOUCH" else None),
            first_prior_full_sweep_or_traversal_ms=(c.bos_bar_start_ms-THREE
                if state=="PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL" else None))

    def verdicts(self,c):
        return tuple(decide_source_eligibility(c,p).eligible for p in ELIGIBILITY_POLICIES)

    def test_three_explicit_adapted_policy_ids(self):
        self.assertEqual(len(ELIGIBILITY_POLICIES),3)
        self.assertEqual(len(set(ELIGIBILITY_POLICIES)),3)
    def test_no_candidate_all_policies_refuse(self):
        c=self.scenario("NO_PREKNOWN_FTA_CANDIDATE")
        self.assertEqual(self.verdicts(c),(False,False,False))
    def test_no_touch_observed_all_allow(self):
        self.assertEqual(self.verdicts(self.scenario()),(True,True,True))
    def test_boundary_touch_only_first_two_allow(self):
        self.assertEqual(self.verdicts(self.scenario("PRIOR_BOUNDARY_TOUCH")),(True,True,False))
    def test_prior_sweep_only_unfiltered_allows(self):
        self.assertEqual(self.verdicts(self.scenario("PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL")),(True,False,False))
    def test_all_decisions_only_known_after_original_bos_close(self):
        c=self.scenario()
        for policy in ELIGIBILITY_POLICIES:
            d=decide_source_eligibility(c,policy)
            self.assertEqual(d.decision_known_at_ms,c.bos_bar_closed_known_ms)
            self.assertGreater(d.decision_known_at_ms,c.bos_bar_start_ms)
    def test_no_forged_author_labels_or_orders(self):
        for route in self.out.routes:
            for c in route.observations:
                self.assertEqual((c.orders,c.trades),((),()))
                self.assertFalse(c.author_freshness_approved)
                for d in c.decisions:
                    self.assertFalse(d.author_fta_freshness_approved or d.author_target_approved or d.order_allowed)
    def test_matrix_36_routes_and_nested_gate_counts(self):
        self.assertEqual(len(self.out.routes),36)
        self.assertEqual(self.out.parent_route_count,36)
        for r in self.out.routes:
            a,b,c=(r.policy_eligible_counts[p] for p in ELIGIBILITY_POLICIES)
            self.assertGreaterEqual(a,b)
            self.assertGreaterEqual(b,c)
            self.assertEqual(r.parent_contexts,len(r.observations))
    def test_paper_mode_unconditional(self):
        self.assertEqual(self.out.readiness,"NOT_TRADE_READY")
        self.assertEqual((self.out.author_fta_goldens,self.out.orders,self.out.trades),(0,(),()))
    def test_scanner_equals_standalone_gate(self):
        self.assertEqual(scan_original_source_eligibility(self.src,as_of_ms=self.src.as_of_ms),self.out)
    def test_unknown_policy_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_ADAPTED_ELIGIBILITY_POLICY"):
            decide_source_eligibility(self.scenario(),"MAKE_MONEY")
    def test_fake_ready_parent_rejected(self):
        with self.assertRaisesRegex(ValueError,"ACADEMIC_DRIFT_OR_FORGED_READY"):
            apply_source_eligibility(replace(self.parent,readiness="READY"))
    def test_fake_parent_order_rejected(self):
        with self.assertRaisesRegex(ValueError,"ACADEMIC_DRIFT_OR_FORGED_READY"):
            apply_source_eligibility(replace(self.parent,orders=("fake",)))
    def test_future_obstacle_not_allowed(self):
        c=replace(self.scenario(),potential_1h_obstacle_source_known_ms=self.real.bos_bar_start_ms+THREE)
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_UNPROVEN_SOURCE_OBSTACLE"):
            self.verdicts(c)
    def test_touch_state_forgery_no_touch_but_row_exists(self):
        c=replace(self.scenario(),first_prior_touch_original_native3m_row_id="HIDDEN_TOUCH")
        with self.assertRaisesRegex(ValueError,"TOUCH_STATE_EVIDENCE_CONTRADICTION"):
            self.verdicts(c)
    def test_boundary_state_requires_real_source_touch_id(self):
        c=replace(self.scenario("PRIOR_BOUNDARY_TOUCH"),first_prior_touch_original_native3m_row_id=None)
        with self.assertRaisesRegex(ValueError,"TOUCH_STATE_EVIDENCE_CONTRADICTION"):
            self.verdicts(c)
    def test_sweep_without_source_touch_id_refused(self):
        c=replace(self.scenario("PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL"),
                  first_prior_touch_original_native3m_row_id=None)
        with self.assertRaisesRegex(ValueError,"TOUCH_STATE_EVIDENCE_CONTRADICTION"):
            self.verdicts(c)
    def test_future_sweep_at_bos_start_refused(self):
        c=replace(self.scenario("PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL"),
                  first_prior_full_sweep_or_traversal_ms=self.real.bos_bar_start_ms)
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_PREKNOWN_TRAVERSAL"):
            self.verdicts(c)
    def test_author_promotion_refused(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_OR_ORDER"):
            self.verdicts(replace(self.scenario(),author_fta_approved=True))
    def test_fake_early_bos_close_refused(self):
        with self.assertRaisesRegex(ValueError,"INVALID_BOS_SOURCE_CHRONOLOGY"):
            self.verdicts(replace(self.scenario(),bos_bar_closed_known_ms=self.real.bos_bar_start_ms))
    def test_unconfirmed_reaction_invented_refused(self):
        c=replace(self.scenario(),source_reaction_confirmed=False,
                  first_reaction_closed_known_ms=self.real.bos_bar_start_ms,
                  first_reaction_original_native3m_row_id="FAKE")
        with self.assertRaisesRegex(ValueError,"INVENTED_REACTION"):
            self.verdicts(c)
    def test_missing_parent_route_refused(self):
        with self.assertRaisesRegex(ValueError,"PARENT_36_ROUTES_MISSING"):
            apply_source_eligibility(replace(self.parent,routes=self.parent.routes[:-1]))
    def test_duplicate_route_key_refused(self):
        routes=list(self.parent.routes)
        routes[-1]=routes[-2]
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_UNKNOWN_SOURCE_ROUTE"):
            apply_source_eligibility(replace(self.parent,routes=tuple(routes)))
    def test_future_event_as_of_rejected(self):
        routes=list(self.parent.routes)
        route=routes[0]
        obs=list(route.observations)
        obs[0]=replace(obs[0],bos_bar_closed_known_ms=self.parent.as_of_ms+THREE)
        routes[0]=replace(route,observations=tuple(obs))
        with self.assertRaisesRegex(ValueError,"WRONG_ROUTE_SYMBOL_OR_FUTURE"):
            apply_source_eligibility(replace(self.parent,routes=tuple(routes)))
    def test_wrong_route_ids_rejected(self):
        routes=list(self.parent.routes)
        route=routes[0]
        obs=list(route.observations)
        obs[0]=replace(obs[0],fta_hypothesis_id="FORGED")
        routes[0]=replace(route,observations=tuple(obs))
        with self.assertRaisesRegex(ValueError,"WRONG_ROUTE_SYMBOL_OR_FUTURE"):
            apply_source_eligibility(replace(self.parent,routes=tuple(routes)))

if __name__=="__main__": unittest.main()
