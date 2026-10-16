"""D05/C14 adversarial source-label gate.

Source *schemes* are meaningful author concept examples; neither raw OHLCV
nor an independent author annotated USD-M Futures market entry dataset.
"""
from __future__ import annotations
import json,unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from copy import deepcopy
from c14_qualitative_stronghl_source_gate import (
 SOURCE,C04,C03,QualitativeRejected,SourceConceptVerdict,
 audit_qualitative_source_cases,evaluate_qualitative_stronghl,
 check_frozen_source_illustrations)
DATA=json.loads(SOURCE.read_text(encoding="utf8"))
ILL=json.loads(C04.read_text(encoding="utf8"))
IMG=json.loads(C03.read_text(encoding="utf8"))
def one(key):
    return deepcopy(next(x for x in DATA["cases"] if x["case_id"]==key))
def scan(cases=None,meta=None,c04=None,c03=None):
    f=deepcopy(DATA if meta is None else meta)
    if cases is not None:f["cases"]=cases
    return audit_qualitative_source_cases(f,ILL if c04 is None else c04,IMG if c03 is None else c03)
class SourceStrongHLC14(unittest.TestCase):
    def test_all_13_course_cases_are_conceptually_adjudicated(self):
        q=scan()
        self.assertEqual(len(q.cases),13)
        self.assertEqual(q.not_author_annotated_market_events,13)
        self.assertEqual(q.labelled_futures_market_cases,0)
        self.assertFalse(q.trade_ready)
    def test_three_original_text_cases_accepted_as_source_only(self):
        for name in ("SHL-LIQ-VC-IMB","SHL-INEFF-VC-SNR","SHL-LIQ-BOS","SHL-INEFF-BOS"):
            with self.subTest(name=name):
                v=evaluate_qualitative_stronghl(one(name),DATA,ILL)
                self.assertEqual(v.source_only_result,"AUTHOR_TEXT_CONSISTENT_ONLY")
                self.assertFalse(v.author_stronghl_approved)
    def test_bos_alternative_not_silently_required_to_be_imb(self):
        a=evaluate_qualitative_stronghl(one("SHL-BOS-IS-NOT-IMB"),DATA,ILL)
        self.assertEqual(a.source_only_result,"AUTHOR_TEXT_CONSISTENT_ONLY")
    def test_liquidity_contact_alone_not_stronghl(self):
        a=evaluate_qualitative_stronghl(one("SHL-RAID-NO-CONFIRM"),DATA,ILL)
        self.assertEqual(a.source_only_result,"MISSING_MOVEMENT_CONFIRMATION")
    def test_poi_alone_without_contact_not_stronghl(self):
        a=evaluate_qualitative_stronghl(one("SHL-POI-NO-CONTACT"),DATA,ILL)
        self.assertEqual(a.source_only_result,"MISSING_LIQUIDITY_OR_INEFFICIENCY_CONTACT")
    def test_volume_spike_not_volume_confirmation(self):
        a=evaluate_qualitative_stronghl(one("SHL-RAW-VOLUME-NOT-VC"),DATA,ILL)
        self.assertEqual(a.source_only_result,"NO_SOURCE_APPROVED_VC_GEOMETRY")
    def test_higher_tf_confirmation_not_source_approved(self):
        a=evaluate_qualitative_stronghl(one("SHL-CONFIRM-UPPER-TF"),DATA,ILL)
        self.assertEqual(a.source_only_result,"UNSUPPORTED_UPPER_TF_CONFIRMATION_IN_SOURCE")
    def test_mb_is_weak_illustration_not_no_possible_reaction(self):
        a=evaluate_qualitative_stronghl(one("SHL-MB-WEAK-NOT-STRONG"),DATA,ILL)
        self.assertEqual(a.source_only_result,"CONTEXT_NOT_STRONG_SOURCE_ILLUSTRATION")
    def test_candle_order_conflict_blocks_source_signoff(self):
        a=evaluate_qualitative_stronghl(one("SHL-SNR-CANDLE-ORDER"),DATA,ILL)
        self.assertEqual(a.source_only_result,"UNRESOLVED_AUTHOR_TEXT_IMAGE_CONFLICT")
    def test_second_zone_return_never_first(self):
        a=evaluate_qualitative_stronghl(one("SHL-REPEATED-FIRST-TEST"),DATA,ILL)
        self.assertEqual(a.source_only_result,"LATER_TEST_CANNOT_BE_LABELLED_FIRST")
    def test_possible_reaction_is_not_guaranteed(self):
        a=evaluate_qualitative_stronghl(one("SHL-FIRST-TEST-MAY-FAIL"),DATA,ILL)
        self.assertEqual(a.source_only_result,"POSSIBLE_RESPONSE_NOT_GUARANTEED")
    def test_72_images_remain_schemes_or_unreplayed_forex(self):
        q=scan()
        self.assertEqual(q.original_images_reviewed,72)
        self.assertEqual(IMG["numeric_forex_total"],6)
    def test_unmodified_original_artifacts_load_through_independent_read(self):
        self.assertEqual(scan(),check_frozen_source_illustrations())
    def test_reject_self_declared_market_bar_attestation(self):
        a=one("SHL-LIQ-BOS")
        a["author_bars_independently_aligned"]=True
        with self.assertRaisesRegex(QualitativeRejected,"FAKE_MARKET_OR_AUTHOR_ATTESTATION"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_reject_self_declared_futures_raw_price(self):
        a=one("SHL-LIQ-BOS");a["binance_futures_raw_prices"]=True
        with self.assertRaisesRegex(QualitativeRejected,"FAKE_MARKET_OR_AUTHOR_ATTESTATION"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_reject_forged_author_approved(self):
        a=one("SHL-LIQ-BOS");a["author_stronghl_approved"]=True
        with self.assertRaisesRegex(QualitativeRejected,"FAKE_MARKET_OR_AUTHOR_ATTESTATION"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_source_must_be_text_or_schematic(self):
        a=one("SHL-LIQ-BOS");a["source_kind"]="BINANCE_RAW_PRICE"
        with self.assertRaisesRegex(QualitativeRejected,"FAKE_MARKET_OR_AUTHOR_ATTESTATION"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_source_uri_unknown_rejected(self):
        a=one("SHL-LIQ-BOS");a["source_uri"]="https://malicious.example/author-label"
        with self.assertRaisesRegex(QualitativeRejected,"UNREGISTERED_PRIMARY_SOURCE"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_wrong_registered_uri_not_allowed(self):
        a=one("SHL-LIQ-BOS");a["source_uri"]=DATA["primary_sources"]["IMB"]
        with self.assertRaisesRegex(QualitativeRejected,"MISMATCHED_CONCEPT_TEXT_SOURCE"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_figure_outside_frozen_C04_not_usable(self):
        a=one("SHL-LIQ-VC-IMB");a["figure_ref"]="AUTHOR_APPROVED_UPLOADED_SCREENSHOT"
        with self.assertRaisesRegex(QualitativeRejected,"IMAGE_NOT_IN_FROZEN_SOURCE_CASES"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_missing_original_snr_conflict_not_silent_approval(self):
        a=one("SHL-SNR-CANDLE-ORDER")
        source=deepcopy(ILL);source["source_conflicts"]=[]
        with self.assertRaisesRegex(QualitativeRejected,"SNR_CONFLICT_NOT_DOCUMENTED"):
            evaluate_qualitative_stronghl(a,DATA,source)
    def test_snr_fake_consistent_figure_rejected(self):
        a=one("SHL-SNR-CANDLE-ORDER");a["figure_ref"]="POI-FVG-ILLUSTRATION"
        with self.assertRaisesRegex(QualitativeRejected,"SNR_NOT_SUPPORTED_BY_CONFLICT_IMAGE"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_weak_mb_cannot_be_positive_author_approved(self):
        a=one("SHL-MB-WEAK-NOT-STRONG");a["classification"]="CONCEPT_POSITIVE"
        with self.assertRaisesRegex(QualitativeRejected,"WEAK_MB_NOT_SOURCE_SUPPORTED"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_wrong_expected_outcome_refused(self):
        a=one("SHL-RAID-NO-CONFIRM");a["expected"]="AUTHOR_TEXT_CONSISTENT_ONLY"
        with self.assertRaisesRegex(QualitativeRejected,"SOURCE_CONCEPT_EXPECTATION_MISMATCH"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_claimed_positive_must_not_be_negative_control(self):
        a=one("SHL-LIQ-BOS");a["classification"]="TEXT_DERIVED_NEGATIVE"
        with self.assertRaisesRegex(QualitativeRejected,"POSITIVE_TEXT_CASE_MISCLASSIFIED"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_missing_contact_not_author_price_label(self):
        a=one("SHL-POI-NO-CONTACT");a["classification"]="CONCEPT_POSITIVE"
        with self.assertRaisesRegex(QualitativeRejected,"TEXT_NEGATIVE_NOT_AUTHOR_PRICE_LABEL"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_future_timeframe_unknown_not_fabricated(self):
        a=one("SHL-LIQ-BOS");a["confirm_tf"]="TIMESTAMPED_5M_REAL"
        with self.assertRaisesRegex(QualitativeRejected,"UNKNOWN_TF_RELATION"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_new_invented_confirmation_type_rejected(self):
        a=one("SHL-LIQ-BOS");a["confirmation"]="EMA_VOL_SPIKE"
        with self.assertRaisesRegex(QualitativeRejected,"UNSUPPORTED_AUTHOR_CONFIRMATION"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_new_arbitrary_contact_type_rejected(self):
        a=one("SHL-LIQ-BOS");a["contact"]="PRICE_MOMENTUM_5M"
        with self.assertRaisesRegex(QualitativeRejected,"UNSUPPORTED_CONTACT_KIND"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_invalid_case_id_rejected(self):
        a=one("SHL-LIQ-BOS");a["case_id"]="APPROVED:ALERT"
        with self.assertRaisesRegex(QualitativeRejected,"BAD_CASE_ID"):
            evaluate_qualitative_stronghl(a,DATA,ILL)
    def test_registry_duplicate_identifier_rejected(self):
        cases=deepcopy(DATA["cases"]);cases[1]["case_id"]=cases[0]["case_id"]
        with self.assertRaisesRegex(QualitativeRejected,"DUPLICATE_SOURCE_CASE_ID"):
            scan(cases)
    def test_missing_source_case_rejected(self):
        with self.assertRaisesRegex(QualitativeRejected,"INCOMPLETE_SOURCE_CASE_REGISTRY"):
            scan(DATA["cases"][:-1])
    def test_forged_zero_market_labels_to_one_rejected(self):
        source=deepcopy(DATA);source["academic_futures_golden_labels"]=1
        with self.assertRaisesRegex(QualitativeRejected,"NOT_AN_UNAPPROVED_SOURCE_SCHEMATIC_DATASET"):
            scan(meta=source)
    def test_source_schema_unknown_rejected(self):
        source=deepcopy(DATA);source["schema"]="AUTHOR_APPROVED_V2"
        with self.assertRaisesRegex(QualitativeRejected,"NOT_AN_UNAPPROVED_SOURCE_SCHEMATIC_DATASET"):
            scan(meta=source)
    def test_original_c04_cannot_be_promoted_to_futures(self):
        source=deepcopy(ILL);source["acceptance"]["academic_market_patterns_independently_approved"]=1
        with self.assertRaisesRegex(QualitativeRejected,"CHANGED_OR_FALSE_ORIGINAL_C04_SCOPE"):
            scan(c04=source)
    def test_original_c03_cannot_be_promoted_to_futures(self):
        source=deepcopy(IMG);source["approved_academic_futures_cases"]=1
        with self.assertRaisesRegex(QualitativeRejected,"CHANGED_OR_FALSE_ORIGINAL_C03_SCOPE"):
            scan(c03=source)
    def test_qualitative_source_outcome_and_readiness_frozen(self):
        a=scan()
        with self.assertRaises(FrozenInstanceError):a.trade_ready=True
        with self.assertRaises(FrozenInstanceError):a.cases[0].author_stronghl_approved=True
if __name__=="__main__":
    unittest.main(verbosity=2)
