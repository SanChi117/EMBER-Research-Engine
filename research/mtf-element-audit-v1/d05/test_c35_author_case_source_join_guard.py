"""C35 fail-closed instructor 2023 cases vs C33 original 2026 USD-M source."""
import unittest
from dataclasses import replace
from datetime import datetime,timezone
from c35_author_case_source_join_guard import (
    InstructorCaseClaim,review_author_case_claim,default_missing_original_backtest,
    INSTRUCTOR_BACKTEST_REF,C33_ORIGINAL_START_MS,C33_ORIGINAL_END_MS,
    INSTRUCTOR_BACKTEST_TITLE_PERIOD_START_MS,INSTRUCTOR_BACKTEST_TITLE_PERIOD_END_MS)

A23=1672531200000
J23=1688169600000
S26=1788220800000
O26=1790985600000

def example(**kw):
    return replace(InstructorCaseClaim(INSTRUCTOR_BACKTEST_REF),**kw)
def audit(**kw):
    return review_author_case_claim(example(**kw))
def complete_example(**kw):
    return example(source_status="EXTERNAL_UNVERIFIED_LABEL",
       author_source_sha256="a"*64,author_explicit_case_label="POSITIVE",
       market_symbol="EURUSD",market_venue="FX",
       market_provider="UNVERIFIED_AUTHOR_CHART",
       chart_iana_timezone="Europe/Kyiv",
       instructor_case_start_ms=J23,
       instructor_case_end_ms=J23+3600000,
       instructor_selected_3m_bos_level="1.12345",
       source_3m_original_bar_sha="SOURCE_UNVERIFIED",
       source_1h_original_bar_sha="SOURCE_UNVERIFIED",
       instructor_first_fta_level="1.11500",
       instructor_stop_level="1.12600",**kw)

class C35AuthorSourceJoinGuard(unittest.TestCase):
    def test_default_no_author_positive(self):
        self.assertFalse(default_missing_original_backtest().has_verified_author_bos_positive)
    def test_default_no_author_negative(self):
        self.assertFalse(default_missing_original_backtest().has_verified_author_bos_negative)
    def test_default_no_trade_or_signal(self):
        a=default_missing_original_backtest()
        self.assertEqual(a.readiness,"NOT_TRADE_READY")
        self.assertEqual(a.orders,())
        self.assertEqual(a.trades,())
        self.assertFalse(a.joined_to_frozen_c33)
    def test_default_reports_original_unavailable(self):
        self.assertIn("INSTRUCTOR_2023_BACKTEST_SOURCE_UNAVAILABLE",
                      default_missing_original_backtest().case_evidence_gaps)
    def test_2023_author_backtest_title_period(self):
        self.assertEqual(INSTRUCTOR_BACKTEST_TITLE_PERIOD_START_MS,A23)
        self.assertEqual(INSTRUCTOR_BACKTEST_TITLE_PERIOD_END_MS,1690848000000)
        self.assertIn("2023-01-2023-07",INSTRUCTOR_BACKTEST_REF)
    def test_2026_source_exact_32_day_endpoints(self):
        self.assertEqual((C33_ORIGINAL_START_MS,C33_ORIGINAL_END_MS),(S26,O26))
    def test_2023_heading_does_not_overlap_2026_archive(self):
        self.assertFalse(default_missing_original_backtest().course_title_period_overlaps_frozen_c33)
    def test_authored_2023_case_cannot_join_2026(self):
        x=review_author_case_claim(complete_example())
        self.assertFalse(x.case_within_frozen_c33_period)
        self.assertIn("CASE_TIME_NOT_IN_FROZEN_C33_2026_SOURCE_WINDOW",x.case_evidence_gaps)
    def test_misdated_2026_claim_still_not_author_approved(self):
        p=complete_example()
        p=replace(p,instructor_case_start_ms=S26+120000,
                  instructor_case_end_ms=S26+180000)
        x=review_author_case_claim(p)
        self.assertTrue(x.case_within_frozen_c33_period)
        self.assertFalse(x.joined_to_frozen_c33)
        self.assertFalse(x.has_verified_author_bos_positive)
        self.assertFalse(x.has_verified_author_bos_negative)
    def test_same_symbol_usdm_venue_claim_does_not_authorize(self):
        p=replace(complete_example(),market_symbol="BTCUSDT",
                  market_venue="BINANCE_USDM",market_provider="BINANCE",
                  instructor_case_start_ms=S26,
                  instructor_case_end_ms=S26+180000)
        x=review_author_case_claim(p)
        self.assertFalse(x.joined_to_frozen_c33)
        self.assertFalse(x.has_verified_author_bos_positive)
    def test_external_positive_label_does_not_become_positive_golden(self):
        x=review_author_case_claim(complete_example())
        self.assertFalse(x.has_verified_author_bos_positive)
        self.assertIn("CLAIM_NOT_INDEPENDENTLY_AUTHENTICATED_AS_AUTHOR",
                      x.case_evidence_gaps)
    def test_external_negative_label_does_not_become_negative_golden(self):
        p=replace(complete_example(),author_explicit_case_label="NEGATIVE")
        x=review_author_case_claim(p)
        self.assertFalse(x.has_verified_author_bos_negative)
    def test_forged_SHA_does_not_certify_source(self):
        x=review_author_case_claim(complete_example())
        self.assertEqual(x.source_case_label_status,"NEEDS_AUTHOR_BOS_GOLDENS")
    def test_missing_case_specific_timestamp_not_inferred_from_title(self):
        x=default_missing_original_backtest()
        self.assertIsNone(x.case_within_frozen_c33_period)
        self.assertIn("SOURCE_NOT_SHOWN_INSTRUCTOR_CASE_START_MS",x.case_evidence_gaps)
    def test_missing_exact_bos_pivot_is_obstruction(self):
        x=audit()
        self.assertIn("SOURCE_NOT_SHOWN_INSTRUCTOR_SELECTED_3M_BOS_LEVEL",x.case_evidence_gaps)
    def test_missing_symbol_and_timezone_obstructions(self):
        x=audit()
        self.assertIn("SOURCE_NOT_SHOWN_MARKET_SYMBOL",x.case_evidence_gaps)
        self.assertIn("SOURCE_NOT_SHOWN_CHART_IANA_TIMEZONE",x.case_evidence_gaps)
    def test_missing_source_3m_and_1h_sha_obstructions(self):
        x=audit()
        self.assertIn("SOURCE_NOT_SHOWN_SOURCE_3M_ORIGINAL_BAR_SHA",x.case_evidence_gaps)
        self.assertIn("SOURCE_NOT_SHOWN_SOURCE_1H_ORIGINAL_BAR_SHA",x.case_evidence_gaps)
    def test_missing_fta_and_stop_obstructions(self):
        x=audit()
        self.assertIn("SOURCE_NOT_SHOWN_INSTRUCTOR_FIRST_FTA_LEVEL",x.case_evidence_gaps)
        self.assertIn("SOURCE_NOT_SHOWN_INSTRUCTOR_STOP_LEVEL",x.case_evidence_gaps)
    def test_missing_case_start_or_end_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_PARTIAL_CASE_TIMESTAMP"):
            audit(instructor_case_start_ms=J23)
        with self.assertRaisesRegex(ValueError,"C35_PARTIAL_CASE_TIMESTAMP"):
            audit(instructor_case_end_ms=J23)
    def test_end_equal_start_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_CASE_END_NOT_AFTER_START"):
            audit(instructor_case_start_ms=J23,instructor_case_end_ms=J23)
    def test_end_before_start_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_CASE_END_NOT_AFTER_START"):
            audit(instructor_case_start_ms=J23,instructor_case_end_ms=J23-180000)
    def test_timestamp_boolean_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_INVALID_"):
            audit(instructor_case_start_ms=True,instructor_case_end_ms=J23)
    def test_timestamp_negative_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_INVALID_"):
            audit(instructor_case_start_ms=-1,instructor_case_end_ms=J23)
    def test_timestamp_string_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_INVALID_"):
            audit(instructor_case_start_ms="2023-07-01",instructor_case_end_ms=J23)
    def test_wrong_instructor_url_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_NOT_ORIGINAL_INSTRUCTOR_BACKTEST_REF"):
            audit(original_author_source_url="https://example.org/ict-backtest")
    def test_unknown_source_status_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_UNTRUSTED_SOURCE_STATUS"):
            audit(source_status="AUTHOR_READY")
    def test_ready_flag_cannot_be_passed_in_claim(self):
        with self.assertRaises(TypeError):
            InstructorCaseClaim(INSTRUCTOR_BACKTEST_REF,readiness="READY")
    def test_malformed_sha_uppercase_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_INVALID_AUTHOR_SOURCE_SHA256"):
            audit(author_source_sha256="A"*64)
    def test_malformed_sha_short_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_INVALID_AUTHOR_SOURCE_SHA256"):
            audit(author_source_sha256="f"*63)
    def test_empty_market_symbol_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_INVALID_MARKET_SYMBOL"):
            audit(market_symbol="")
    def test_nonstring_pivot_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_INVALID_INSTRUCTOR_SELECTED"):
            audit(instructor_selected_3m_bos_level=123)
    def test_external_list_untrusted_rejected(self):
        with self.assertRaisesRegex(ValueError,"C35_UNTRUSTED_AUTHOR_CASE"):
            review_author_case_claim({"author":True})
    def test_2026_period_start_inside_and_end_exclusive(self):
        p=complete_example()
        x=review_author_case_claim(replace(p,instructor_case_start_ms=S26,
                                          instructor_case_end_ms=S26+180000))
        self.assertTrue(x.case_within_frozen_c33_period)
        y=review_author_case_claim(replace(p,instructor_case_start_ms=O26,
                                          instructor_case_end_ms=O26+180000))
        self.assertFalse(y.case_within_frozen_c33_period)
    def test_2023_period_end_still_not_2026_overlap(self):
        p=complete_example()
        x=review_author_case_claim(replace(p,instructor_case_start_ms=1690848000000-180000,
                                          instructor_case_end_ms=1690848000000))
        self.assertFalse(x.case_within_frozen_c33_period)
    def test_refusing_source_2026_as_author_2023_trade_even_with_all_values(self):
        p=complete_example()
        x=review_author_case_claim(replace(p,
            source_status="CASE_METADATA_ONLY",
            author_explicit_case_label="POSITIVE",
            market_symbol="SOLUSDT",
            market_provider="BINANCE",
            instructor_case_start_ms=S26+3600000,
            instructor_case_end_ms=S26+3600000+180000))
        self.assertFalse(x.joined_to_frozen_c33)
        self.assertFalse(x.has_verified_author_bos_positive)
        self.assertEqual(x.orders,())
        self.assertEqual(x.trades,())
if __name__=="__main__":unittest.main()
