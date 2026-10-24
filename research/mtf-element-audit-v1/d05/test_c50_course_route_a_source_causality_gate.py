"""C50 course evidence gap and C47/C49 precise source causal relation tests."""
from dataclasses import replace
import unittest
from c21b_original_3m_raid_break_geometry import THREE,HOUR
from c36_adapted_slot_registry import ACADEMIC_CORE_ID
from c47_post_4h_contact_1h_imb_source_link import (
 OneHourImbSource,FourToOneSourceObservation,C47SourceJoin)
from c49_original3m_post_contact_directional_close import (
 C49DirectionalCloseObservation,C49ParentReactionSource,C49SourceReview,HORIZONS)
from c50_course_route_a_source_causality_gate import (
 classify_original_context,review_course_1h_source_causality,MODES,BLOCKERS,CITED_RULE_IDS)
ORIGIN=40000*HOUR
ASOF=ORIGIN+50*HOUR
TOUCH=ORIGIN+THREE
EXIT=ORIGIN+3*THREE

def onehour(start=ORIGIN+HOUR,side="LONG"):
    return OneHourImbSource(side,"100","102",start,start+HOUR,start+2*HOUR,
        start+3*HOUR,("1h-a","1h-b","1h-c"),("1h-x","1h-y","1h-z"))

def c47(*,touch=True,source=True,start=ORIGIN+HOUR):
    h=onehour(start) if touch and source else None
    return FourToOneSourceObservation("SYNTHUSDT","LONG",ORIGIN,
        ("parent-a","parent-b","parent-c"),"native3m:first" if touch else None,
        TOUCH if touch else None,1 if h else 0,h)

def reaction(*,touch=True,exit_close=EXIT,side="FAVORABLE"):
    rows=[]
    for name,window in HORIZONS:
        valid=touch and exit_close is not None and exit_close<=TOUCH+window
        status=("NO_PARENT_4H_FIRST_CONTACT_AS_OF" if not touch else
            ("FIRST_LATER_FAVORABLE_3M_CLOSE" if side=="FAVORABLE" else
             "FIRST_LATER_ADVERSE_3M_CLOSE") if valid else
             "NO_LATER_DIRECTIONAL_CLOSE_HORIZON_COMPLETE")
        rows.append(C49DirectionalCloseObservation(name,window,ASOF,status,
            "3m:exit" if valid else None,exit_close if valid else None,
            "105" if valid else None,valid and side=="FAVORABLE",
            valid and side=="ADVERSE"))
    return C49ParentReactionSource("LONG",ORIGIN,
        "native3m:first" if touch else None,TOUCH if touch else None,tuple(rows))

def parents(a=None,b=None):
    x=c47() if a is None else a
    y=reaction() if b is None else b
    return (
      C47SourceJoin("SYNTHUSDT",ASOF,10000,100,1,
          int(x.original4h_first_contact_native3m_id is not None),
          int(x.first_post_contact_1h_imb_source is not None),0,ACADEMIC_CORE_ID,(x,)),
      C49SourceReview("SYNTHUSDT",ASOF,10000,1,
          int(y.source_original3m_first_contact_id is not None),3,(y,))
    )

class C50TextGateAndCausalProvenance(unittest.TestCase):
    def result(self,a=None,b=None):
        return classify_original_context(c47() if a is None else a,
            reaction() if b is None else b,as_of_ms=ASOF)
    def blocked(self,part,a=None,b=None):
        with self.assertRaisesRegex(ValueError,part):self.result(a,b)
    def test_source_long_exit_precedes_later_1h_technical_imb(self):
        self.assertEqual(self.result().mode,"FIRST_DIRECTIONAL_3M_CLOSE_BEFORE_1H_IMB_CLOSE")
    def test_adverse_exit_precedes_later_1h_too(self):
        x=self.result(b=reaction(side="ADVERSE"))
        self.assertEqual(x.mode,"FIRST_DIRECTIONAL_3M_CLOSE_BEFORE_1H_IMB_CLOSE")
        self.assertEqual(x.first_12h_direction,"ADVERSE")
    def test_no_touch_is_explicit(self):
        x=self.result(c47(touch=False,source=False),reaction(touch=False))
        self.assertEqual(x.mode,"NO_ORIGINAL_4H_FIRST_3M_CONTACT")
    def test_touch_no_12h_event_explicit(self):
        x=self.result(b=reaction(exit_close=None))
        self.assertEqual(x.mode,"CONTACT_NO_DIRECTIONAL_3M_CLOSE_WITHIN_12H")
    def test_exit_no_followup_1h(self):
        self.assertEqual(self.result(a=c47(source=False)).mode,"DIRECTIONAL_CLOSE_NO_LATER_1H_IMB")
    def test_later_1h_after24h_is_late_not_timely(self):
        self.assertEqual(self.result(a=c47(start=ORIGIN+22*HOUR)).mode,
            "FIRST_1H_IMB_CLOSED_AFTER_24H_OBSERVATION_WINDOW")
    def test_1h_technical_imb_before_exit(self):
        x=self.result(b=reaction(exit_close=ORIGIN+5*HOUR))
        self.assertEqual(x.mode,"FIRST_1H_IMB_CLOSE_BEFORE_DIRECTIONAL_3M_CLOSE")
    def test_equal_close_is_distinct_same_time(self):
        x=self.result(b=reaction(exit_close=ORIGIN+4*HOUR))
        self.assertEqual(x.mode,"FIRST_DIRECTIONAL_3M_CLOSE_AT_1H_IMB_CLOSE")
    def test_all_classification_modes_explicit(self):
        self.assertEqual(len(MODES),7)
    def test_declared_required_author_course_sources_all_present(self):
        self.assertEqual(len(CITED_RULE_IDS),9)
    def test_all_necessary_author_evidence_blocked(self):
        x=self.result()
        self.assertEqual(x.course_source_blockers,BLOCKERS)
        self.assertEqual(len(BLOCKERS),6)
        self.assertFalse(x.course_author_poi_test_verified or
            x.course_author_1h_volume_confirmation_verified or x.source_trade_ready)
    def test_technical_positive_is_not_trade_or_order(self):
        x=self.result()
        self.assertEqual((x.orders,x.trades,x.readiness),((),(),"NOT_TRADE_READY"))
    def test_exact_parent_first_contact_id_kept(self):
        x=self.result()
        self.assertEqual(x.first_3m_contact_id,"native3m:first")
        self.assertEqual(x.parent_4h_original3m_ids,("parent-a","parent-b","parent-c"))
    def test_exact_frozen_original_1h_source_id(self):
        self.assertEqual(self.result().first_later_1h_imb_first_original3m_id,"1h-a")
    def test_mismatched_4h_side_rejected(self):
        self.blocked("ORIGINAL_4H_SOURCE_OR_TIME_MISMATCH",
            replace(c47(),original4h_zone_side="SHORT"))
    def test_mismatched_4h_known_time_rejected(self):
        self.blocked("ORIGINAL_4H_SOURCE_OR_TIME_MISMATCH",
            replace(c47(),original4h_zone_known_ms=ORIGIN-4*HOUR))
    def test_mismatched_contact_id_rejected(self):
        self.blocked("MISMATCHED_ORIGINAL_FIRST_3M_CONTACT",
            replace(c47(),original4h_first_contact_native3m_id="fake"))
    def test_mismatched_contact_known_rejected(self):
        self.blocked("MISMATCHED_ORIGINAL_FIRST_3M_CONTACT",
            replace(c47(),original4h_first_contact_closed_known_ms=TOUCH+THREE))
    def test_forged_parent_poi_author_approval_rejected(self):
        self.blocked("FORGED_ACADEMIC_CONTEXT_OR_TRADE",
            replace(c47(),course_typed_poi_approved=True))
    def test_forged_3m_reaction_author_approval_rejected(self):
        self.blocked("FORGED_ACADEMIC_CONTEXT_OR_TRADE",
            b=replace(reaction(),academic_valid_reaction=True))
    def test_forged_1h_volume_confirmation_rejected(self):
        x=c47()
        self.blocked("FORGED_OR_FUTURE_ORIGINAL_1H_SOURCE",
            replace(x,first_post_contact_1h_imb_source=
                replace(x.first_post_contact_1h_imb_source,academic_vc_certified=True)))
    def test_forged_trade_rejected(self):
        self.blocked("FORGED_ACADEMIC_CONTEXT_OR_TRADE",replace(c47(),trades=("fake",)))
    def test_1h_first_source_precontact_rejected(self):
        x=c47()
        self.blocked("FORGED_OR_FUTURE_ORIGINAL_1H_SOURCE",
            replace(x,first_post_contact_1h_imb_source=onehour(start=ORIGIN-HOUR)))
    def test_future_1h_source_rejected(self):
        x=c47()
        self.blocked("FORGED_OR_FUTURE_ORIGINAL_1H_SOURCE",
            replace(x,first_post_contact_1h_imb_source=onehour(start=ASOF-HOUR)))
    def test_future_3m_price_source_rejected(self):
        original=reaction(exit_close=None)
        altered=list(original.window_observations)
        altered[2]=replace(altered[2],status="FIRST_LATER_FAVORABLE_3M_CLOSE",
            first_later_event_original3m_id="forged-future",first_later_event_close_known_ms=ASOF+THREE,
            first_later_event_close_price="105",favorable_3m_close=True)
        self.blocked("FUTURE_OR_FORGED_3M_DIRECTIONAL_CLOSE",
            b=replace(original,window_observations=tuple(altered)))
    def test_exit_before_contact_rejected(self):
        self.blocked("FUTURE_OR_FORGED_3M_DIRECTIONAL_CLOSE",
            b=reaction(exit_close=TOUCH))
    def test_first_12h_response_cannot_be_older_than12h(self):
        bad=reaction(exit_close=TOUCH+12*HOUR+THREE)
        modified=list(bad.window_observations)
        modified[2]=replace(modified[2],status="FIRST_LATER_FAVORABLE_3M_CLOSE",
            first_later_event_original3m_id="future-event",
            first_later_event_close_known_ms=TOUCH+12*HOUR+THREE,
            first_later_event_close_price="105",
            favorable_3m_close=True)
        self.blocked("FUTURE_OR_FORGED_3M_DIRECTIONAL_CLOSE",
            b=replace(bad,window_observations=tuple(modified)))
    def test_wrong_12h_event_source_id_status_rejected(self):
        x=reaction()
        r=list(x.window_observations)
        r[2]=replace(r[2],first_later_event_original3m_id=None)
        self.blocked("FUTURE_OR_FORGED_3M_DIRECTIONAL_CLOSE",
            b=replace(x,window_observations=tuple(r)))
    def test_future_horizon_mismatch_rejected(self):
        x=reaction();v=list(x.window_observations)
        v[0]=replace(v[0],horizon_id="SNEAK_LOOKAHEAD")
        self.blocked("FORGED_OR_MISALIGNED_C49_SOURCE_HORIZON",
            b=replace(x,window_observations=tuple(v)))
    def test_1h_wrong_source_side_rejected(self):
        x=c47()
        self.blocked("FORGED_OR_FUTURE_ORIGINAL_1H_SOURCE",
            replace(x,first_post_contact_1h_imb_source=onehour(side="SHORT")))
    def test_bare_1h_count_without_source_rejected(self):
        self.blocked("ORPHAN_LATER_1H_COUNT",
            replace(c47(source=False),post_contact_same_side_1h_candidate_count=1))
    def test_no_touch_with_later_1h_source_rejected(self):
        x=c47(touch=False,source=False)
        self.blocked("FICTITIOUS_FOLLOWUP_WITHOUT_TOUCH",
            replace(x,first_post_contact_1h_imb_source=onehour(),post_contact_same_side_1h_candidate_count=1),
            reaction(touch=False))
    def test_untrusted_plain_dicts_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_C47_C49_SOURCE_JOIN"):
            classify_original_context({},reaction(),as_of_ms=ASOF)
    def test_join_accepts_source_parents_no_trading(self):
        a,b=parents()
        y=review_course_1h_source_causality(a,b)
        self.assertEqual(y.classified_context_count,1)
        self.assertEqual(y.source_contexts[0].mode,"FIRST_DIRECTIONAL_3M_CLOSE_BEFORE_1H_IMB_CLOSE")
        self.assertEqual((y.orders,y.trades,y.readiness),((),(),"NOT_TRADE_READY"))
    def test_join_rejects_parent_counts_drift(self):
        a,b=parents()
        with self.assertRaisesRegex(ValueError,"PARENT_SOURCE_PROVENANCE_DRIFT"):
            review_course_1h_source_causality(replace(a,original_source4h_candidates=2),b)
    def test_join_rejects_parent_asof_mismatch(self):
        a,b=parents()
        with self.assertRaisesRegex(ValueError,"PARENT_SOURCE_PROVENANCE_DRIFT"):
            review_course_1h_source_causality(a,replace(b,as_of_ms=ASOF+THREE))
    def test_join_rejects_fake_author_source_goldens(self):
        a,b=parents()
        with self.assertRaisesRegex(ValueError,"FORGED_COURSE_AUTHOR_APPROVAL"):
            review_course_1h_source_causality(replace(a,author_vc_goldens=1),b)
    def test_join_disallowed_order_kept_zero(self):
        a,b=parents();y=review_course_1h_source_causality(a,b)
        self.assertEqual((y.author_verified_poi_count,y.author_verified_1h_vc_count,
            y.author_verified_entry_count),(0,0,0))
    def test_side_never_confuses_late_price_with_author_confirmation(self):
        x=self.result(b=reaction(side="ADVERSE",exit_close=ORIGIN+5*HOUR))
        self.assertFalse(x.course_author_poi_test_verified)
        self.assertFalse(x.course_author_1h_volume_confirmation_verified)
        self.assertEqual(x.first_12h_direction,"ADVERSE")
if __name__=="__main__":unittest.main()
