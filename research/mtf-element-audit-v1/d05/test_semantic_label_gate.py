import json
import pathlib
import unittest
from semantic_label_gate import D05Rejected,validate_chart_case,summarize_candidates

ROOT=pathlib.Path(__file__).resolve().parent
TEMPLATE={
    'case_id':'SCHEMA_ONLY_TEST_NOT_REAL_CHART',
    'course_uri':'https://example.org/source-ref-only',
    'course_section':'schema fixture',
    'raw_chart_uri':'https://example.org/no-real-image',
    'raw_chart_sha256':'a'*64,
    'raw_chart_kind':'ORIGINAL_NUMERIC_AUTHOR_CHART',
    'symbol':'BTCUSDT','market_type':'FUTURES_UM',
    'model_id':'R03_RAID_BOS','side':'SHORT','tf':'3m',
    'event_origin_at':'2026-10-11T13:00:00Z',
    'event_known_at':'2026-10-11T13:05:00Z',
    'decision_as_of':'2026-10-11T13:05:00Z',
    'zone_low':100,'zone_high':105,'event_price':104,
    'annotated_object':'synthetic QA fixture only',
    'case_kind':'POSITIVE','negative_reason':None,
    'rule_reference':'schema-contract','independent_review_status':'PENDING'
}
def c(**changes):
    return {**TEMPLATE,**changes}

class D05SourceGate(unittest.TestCase):
    def test_valid_schema_cannot_approve_itself(self):
        self.assertEqual(validate_chart_case(c()),
          'SCHEMA_VALID_NEEDS_INDEPENDENT_VISUAL_REVIEW')

    def test_screenshot_is_not_original_price_scale(self):
        with self.assertRaisesRegex(D05Rejected,'SCHEMATIC_SCREENSHOT_NOT_GOLDEN'):
            validate_chart_case(c(raw_chart_kind='COURSE_PAGE_SCREENSHOT'))

    def test_future_confirmed_event_cannot_be_used(self):
        with self.assertRaisesRegex(D05Rejected,'LOOKAHEAD'):
            validate_chart_case(c(event_known_at='2026-10-11T13:06:00Z'))

    def test_bad_zone_blocked(self):
        with self.assertRaisesRegex(D05Rejected,'INVALID_ZONE'):
            validate_chart_case(c(zone_high=99))

    def test_unverified_source_hash_blocked(self):
        with self.assertRaisesRegex(D05Rejected,'UNVERIFIABLE'):
            validate_chart_case(c(raw_chart_sha256='not-valid'))

    def test_spot_blocked(self):
        with self.assertRaisesRegex(D05Rejected,'NOT_FROZEN'):
            validate_chart_case(c(market_type='SPOT'))

    def test_no_unexplained_negative_case(self):
        with self.assertRaisesRegex(D05Rejected,'NEGATIVE_WITHOUT_REASON'):
            validate_chart_case(c(case_kind='NEGATIVE'))

    def test_manual_self_approval_blocked(self):
        with self.assertRaisesRegex(D05Rejected,'SELF_APPROVED'):
            validate_chart_case(c(independent_review_status='APPROVED'))

    def test_existing_six_images_remain_unverified(self):
        doc=json.loads((ROOT/'C01_VISUAL_CANDIDATES.json').read_text(encoding='utf8'))
        self.assertEqual(summarize_candidates(doc)['numeric_golden_cases_accepted'],0)

    def test_schema_requires_real_source_attribution(self):
        bad=c()
        del bad['course_uri']
        with self.assertRaisesRegex(D05Rejected,'MISSING_SOURCE'):
            validate_chart_case(bad)

if __name__=='__main__':
    unittest.main(verbosity=2)
