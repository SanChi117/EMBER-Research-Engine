"""C48 finite 6/24/72h windows, no future and no author VC approval."""
import unittest
from dataclasses import replace
from c21b_original_3m_raid_break_geometry import HOUR,THREE
from c47_post_4h_contact_1h_imb_source_link import (
    FourToOneSourceObservation,OneHourImbSource,scan_original_4h_first_contact_to_later_1h_source)
from c48_adapted_post_contact_1h_source_windows import (
    WINDOWS,evaluate_source_window,inspect_c47_source_windows,OUTCOMES)
from test_c21b_native_3m_vs_5m import make3
ANCHOR=4*HOUR*10000
TOUCH=ANCHOR+2*THREE
P6=WINDOWS[0][0];P24=WINDOWS[1][0];P72=WINDOWS[2][0]

def parent(*,first=True,with_1h=True,late_first_hour_at=ANCHOR+HOUR):
    c=None
    if first and with_1h:
        c=OneHourImbSource("LONG","103","105",late_first_hour_at,
            late_first_hour_at+HOUR,late_first_hour_at+2*HOUR,
            late_first_hour_at+3*HOUR,
            ("A","B","C"),("X","Y","Z"))
    return FourToOneSourceObservation("TEST","LONG",ANCHOR,
        ("4HA","4HB","4HC"),
        "3M_TOUCH" if first else None,TOUCH if first else None,
        1 if c is not None else 0,c)

class C48BoundedSourceOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=make3(size=500)
        cls.c47=scan_original_4h_first_contact_to_later_1h_source(cls.src,
           as_of_ms=cls.src.as_of_ms)
        cls.result=inspect_c47_source_windows(cls.c47,as_of_ms=cls.src.as_of_ms)

    def test_exactly_three_preregistered_hours(self):
        self.assertEqual([x[1]//HOUR for x in WINDOWS],[6,24,72])
    def test_positive_first_1h_source_within_all_three_windows(self):
        for policy,_ in WINDOWS:
            v=evaluate_source_window(parent(),as_of_ms=ANCHOR+4*HOUR,policy=policy)
            self.assertTrue(v.passes_research_source_window)
            self.assertEqual(v.state,"LATER_1H_SOURCE_WITHIN_WINDOW")
    def test_positive_lag_known_only_after_full_third_1h_close(self):
        v=evaluate_source_window(parent(),as_of_ms=ANCHOR+4*HOUR,policy=P6)
        self.assertEqual(v.observed_first_1h_lag_ms,4*HOUR-2*THREE)
        self.assertEqual(v.selected_first_1h_raw_native3m_id,"A")
    def test_late_1h_source_excluded_6h_but_included_24h(self):
        v=parent(late_first_hour_at=ANCHOR+6*HOUR)
        self.assertEqual(evaluate_source_window(v,as_of_ms=ANCHOR+9*HOUR,policy=P6).state,
            "FIRST_LATER_1H_SOURCE_AFTER_WINDOW")
        self.assertTrue(evaluate_source_window(v,as_of_ms=ANCHOR+9*HOUR,policy=P24).passes_research_source_window)
    def test_late_1h_source_excluded_24h_but_included_72h(self):
        v=parent(late_first_hour_at=ANCHOR+30*HOUR)
        self.assertFalse(evaluate_source_window(v,as_of_ms=ANCHOR+33*HOUR,policy=P24).passes_research_source_window)
        self.assertTrue(evaluate_source_window(v,as_of_ms=ANCHOR+33*HOUR,policy=P72).passes_research_source_window)
    def test_later_than_72h_excluded_all_three(self):
        v=parent(late_first_hour_at=ANCHOR+74*HOUR)
        for policy,_ in WINDOWS:
            self.assertFalse(evaluate_source_window(v,as_of_ms=ANCHOR+77*HOUR,
                policy=policy).passes_research_source_window)
    def test_future_parent_not_admitted(self):
        v=evaluate_source_window(parent(),as_of_ms=ANCHOR-THREE,policy=P24)
        self.assertEqual(v.state,"PARENT_4H_SOURCE_NOT_YET_KNOWN")
        self.assertIsNone(v.selected_first_1h_raw_native3m_id)
    def test_future_first_contact_not_revealed(self):
        v=evaluate_source_window(parent(),as_of_ms=ANCHOR,policy=P6)
        self.assertEqual(v.state,"NO_ORIGINAL_3M_CONTACT_KNOWN_AS_OF")
        self.assertFalse(v.passes_research_source_window)
        self.assertIsNone(v.selected_first_1h_raw_native3m_id)
    def test_future_1h_when_6h_window_open_stays_unknown(self):
        x=evaluate_source_window(parent(),as_of_ms=ANCHOR+2*HOUR,policy=P6)
        self.assertEqual(x.state,"WINDOW_OPEN_NO_1H_SOURCE_KNOWN")
        self.assertIsNone(x.observed_first_1h_lag_ms)
        self.assertIsNone(x.selected_first_1h_raw_native3m_id)
    def test_future_1h_appears_only_at_third_1h_close(self):
        before=evaluate_source_window(parent(),as_of_ms=ANCHOR+4*HOUR-THREE,policy=P6)
        after=evaluate_source_window(parent(),as_of_ms=ANCHOR+4*HOUR,policy=P6)
        self.assertFalse(before.passes_research_source_window)
        self.assertTrue(after.passes_research_source_window)
    def test_no_parent_contact_source_not_qualified(self):
        x=evaluate_source_window(parent(first=False,with_1h=False),
            as_of_ms=ANCHOR+HOUR*100,policy=P72)
        self.assertEqual(x.state,"NO_ORIGINAL_3M_CONTACT_KNOWN_AS_OF")
    def test_contact_without_any_1h_candidate_window_open(self):
        x=evaluate_source_window(parent(with_1h=False),as_of_ms=ANCHOR+HOUR,policy=P24)
        self.assertEqual(x.state,"WINDOW_OPEN_NO_1H_SOURCE_KNOWN")
    def test_contact_without_any_1h_candidate_window_elapsed(self):
        x=evaluate_source_window(parent(with_1h=False),as_of_ms=ANCHOR+80*HOUR,policy=P72)
        self.assertEqual(x.state,"WINDOW_ELAPSED_WITHOUT_1H_SOURCE")
    def test_future_1h_after_expiry_cannot_fake_timely_source(self):
        x=parent(late_first_hour_at=ANCHOR+10*HOUR)
        before=evaluate_source_window(x,as_of_ms=ANCHOR+7*HOUR,policy=P6)
        after=evaluate_source_window(x,as_of_ms=ANCHOR+13*HOUR,policy=P6)
        self.assertEqual(before.state,"WINDOW_ELAPSED_WITHOUT_1H_SOURCE")
        self.assertEqual(after.state,"FIRST_LATER_1H_SOURCE_AFTER_WINDOW")
        self.assertFalse(before.passes_research_source_window or after.passes_research_source_window)
    def test_source_lag_not_shown_before_candidate_known(self):
        a=evaluate_source_window(parent(late_first_hour_at=ANCHOR+70*HOUR),
            as_of_ms=ANCHOR+24*HOUR,policy=P72)
        self.assertIsNone(a.observed_first_1h_lag_ms)
        self.assertIsNone(a.selected_first_1h_raw_native3m_id)
    def test_three_windows_nested_when_source_known(self):
        for shift in (1,5,10,25,75):
            s=parent(late_first_hour_at=ANCHOR+shift*HOUR)
            snap=ANCHOR+(shift+3)*HOUR
            passed=[evaluate_source_window(s,as_of_ms=snap,policy=pid).passes_research_source_window for pid,_ in WINDOWS]
            self.assertLessEqual(int(passed[0]),int(passed[1]))
            self.assertLessEqual(int(passed[1]),int(passed[2]))
    def test_no_author_vc_approved_even_when_window_passes(self):
        x=evaluate_source_window(parent(),as_of_ms=ANCHOR+4*HOUR,policy=P72)
        self.assertFalse(x.author_volume_confirmation_certified or x.author_poi_test_certified)
        self.assertEqual((x.trades,x.orders,x.readiness),((),(),"NOT_TRADE_READY"))
    def test_forged_parent_poi_approval_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_APPROVAL"):
            evaluate_source_window(replace(parent(),course_typed_poi_approved=True),
                as_of_ms=ANCHOR+4*HOUR,policy=P6)
    def test_forged_parent_trades_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_AUTHOR_APPROVAL"):
            evaluate_source_window(replace(parent(),trades=("fake",)),
                as_of_ms=ANCHOR+4*HOUR,policy=P6)
    def test_forged_author_1h_vc_rejected(self):
        v=parent()
        with self.assertRaisesRegex(ValueError,"FORGED_OR_PRECONTACT"):
            evaluate_source_window(replace(v,first_post_contact_1h_imb_source=
                replace(v.first_post_contact_1h_imb_source,academic_vc_certified=True)),
                as_of_ms=ANCHOR+4*HOUR,policy=P6)
    def test_1h_source_before_contact_rejected(self):
        v=parent()
        with self.assertRaisesRegex(ValueError,"FORGED_OR_PRECONTACT"):
            evaluate_source_window(replace(v,first_post_contact_1h_imb_source=
                replace(v.first_post_contact_1h_imb_source,first_hour_start_ms=ANCHOR)),
                as_of_ms=ANCHOR+4*HOUR,policy=P6)
    def test_1h_wrong_direction_rejected(self):
        v=parent()
        with self.assertRaisesRegex(ValueError,"FORGED_OR_PRECONTACT"):
            evaluate_source_window(replace(v,first_post_contact_1h_imb_source=
                replace(v.first_post_contact_1h_imb_source,side="SHORT")),
                as_of_ms=ANCHOR+4*HOUR,policy=P6)
    def test_missing_parent_source_id_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_PARENT_SOURCE_PROVENANCE"):
            evaluate_source_window(replace(parent(),original4h_zone_first_raw3m_ids=("x","","z")),
                as_of_ms=ANCHOR+4*HOUR,policy=P6)
    def test_fictitious_first_contact_rejected(self):
        with self.assertRaisesRegex(ValueError,"FICTITIOUS_FIRST_CONTACT"):
            evaluate_source_window(replace(parent(first=False,with_1h=False),
                original4h_first_contact_native3m_id="invented"),
                as_of_ms=ANCHOR+4*HOUR,policy=P6)
    def test_missing_1h_candidate_with_nonzero_count_rejected(self):
        with self.assertRaisesRegex(ValueError,"MISSING_FIRST_1H_CANDIDATE"):
            evaluate_source_window(replace(parent(),first_post_contact_1h_imb_source=None),
                as_of_ms=ANCHOR+4*HOUR,policy=P6)
    def test_unknown_window_parameter_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_PREREGISTERED"):
            evaluate_source_window(parent(),as_of_ms=ANCHOR+4*HOUR,policy="BEST_PNL_TUNED")
    def test_unclosed_3m_snapshot_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"NOT_CLOSED_NATIVE3M"):
            evaluate_source_window(parent(),as_of_ms=ANCHOR+THREE+1,policy=P6)
    def test_source_parent_integration_consistency(self):
        x=self.result
        self.assertEqual(x.source_parent_context_count,self.c47.original_source4h_candidates)
        self.assertEqual(x.completed_source_parent_contacts,self.c47.original_source4h_first_contacts)
        self.assertEqual(x.policy_count,3)
        self.assertEqual(len(x.outcomes),x.source_parent_context_count)
    def test_integration_status_all_known_states(self):
        for x in self.result.outcomes:
            self.assertEqual(len(x.policy_decisions),3)
            self.assertTrue(all(y.state in OUTCOMES for y in x.policy_decisions))
    def test_integration_nesting_for_each_parent(self):
        for x in self.result.outcomes:
            a,b,c=(v.passes_research_source_window for v in x.policy_decisions)
            self.assertLessEqual(int(a),int(b))
            self.assertLessEqual(int(b),int(c))
    def test_integration_no_orders_trades(self):
        self.assertEqual((self.result.orders,self.result.trades,self.result.readiness),
            ((),(),"NOT_TRADE_READY"))
        self.assertTrue(all(v.orders==v.trades==() for v in self.result.outcomes))
    def test_integration_determinism_same_original_source(self):
        self.assertEqual(inspect_c47_source_windows(self.c47,as_of_ms=self.src.as_of_ms),self.result)
    def test_asof_earlier_does_not_show_later_1h_original_id(self):
        early=self.src.as_of_ms-5*HOUR
        rv=inspect_c47_source_windows(self.c47,as_of_ms=early)
        for obs in rv.outcomes:
            for v in obs.policy_decisions:
                self.assertTrue(v.selected_first_1h_raw_native3m_id is None or
                    v.observed_first_1h_lag_ms is not None)
    def test_report_future_asof_beyond_frozen_parent_rejected(self):
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_PARTIAL_PARENT_ASOF"):
            inspect_c47_source_windows(self.c47,as_of_ms=self.src.as_of_ms+THREE)
    def test_forged_C47_parent_author_goldens_rejected(self):
        with self.assertRaisesRegex(ValueError,"FORGED_PARENT_TRADE_OR_VC"):
            inspect_c47_source_windows(replace(self.c47,author_vc_goldens=1),
                as_of_ms=self.src.as_of_ms)
    def test_all_policies_explicit_adapted_not_course_authored(self):
        self.assertTrue(all(name.startswith("C48_ADAPTED_") for name,_ in WINDOWS))
if __name__=="__main__":unittest.main()
