"""C20C source-only calendar diagnostics."""
import unittest
from test_c20b_closed_1h_5m_source_geometry import synthetic
from c20c_context_observations import review_calendar_context

class C20CContextTests(unittest.TestCase):
    def test_original_geometry_has_no_author_approval(self):
        line=synthetic()
        result=review_calendar_context(line,as_of_ms=line.as_of_ms)
        self.assertGreater(result.observed_breaks,0)
        self.assertEqual(result.readiness,"NOT_TRADE_READY")
        self.assertEqual(result.author_session_status,"UNKNOWN_SOURCE_TIMEZONE")
        self.assertEqual(result.author_fta_status,"UNKNOWN_SOURCE_FTA")
        self.assertEqual(result.author_bos_status,"UNKNOWN_SOURCE_BOS_LABELS")

    def test_each_candidate_has_one_utc_day_class(self):
        line=synthetic()
        x=review_calendar_context(line,as_of_ms=line.as_of_ms)
        self.assertEqual(x.observed_breaks,
                         x.same_utc_day+x.previous_utc_day+x.older_utc_day)

    def test_no_break_before_raid_is_confirmed(self):
        from c20_original_32day_native5m_lineage import SEPT_START
        line=synthetic()
        result=review_calendar_context(line,as_of_ms=SEPT_START+7*3600000)
        self.assertEqual(result.observed_breaks,0)

    def test_subbar_future_timestamp_rejected(self):
        line=synthetic()
        with self.assertRaisesRegex(ValueError,"FUTURE_OR_UNCLOSED"):
            review_calendar_context(line,as_of_ms=line.as_of_ms-1)

    def test_false_ready_source_rejected(self):
        from dataclasses import replace
        line=replace(synthetic(),readiness="READY")
        with self.assertRaisesRegex(ValueError,"FORGED_C20A_SOURCE_APPROVAL"):
            review_calendar_context(line,as_of_ms=line.as_of_ms)
