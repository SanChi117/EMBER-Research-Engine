"""C74 adversarial author-golden checks: unverified is never a trade."""
import unittest
from copy import deepcopy
from c74_author_academic_golden_failclosed import (
    C73_SHA, ROUTE_A_ID, POI_ID, FIELDS, C74Rejected,
    evaluate_author_academic_golden as evaluate,
    PINNED_AUTHOR_CRYPTO_GOLDENS,
)


def base():
    return dict(
        symbol="BTCUSDT", venue="BINANCE_USDM", route="A",
        poi_tf="1h", poi_kind="IMB", poi_source_id="SYNTHETIC_POI_EXAMPLE",
        parent_4h_source_id="SYNTHETIC_PARENT_EXAMPLE",
        parent_4h_vc_label="UNVERIFIED",
        poi_created_ms=1000000, first_raw3m_id="SYNTHETIC_RAW3M_1",
        first_raw3m_closed_ms=1180000, source_visit_episodes=1,
        repeat_raw3m_id=None, first_15m_event_kind="RAW_IMB",
        first_15m_pattern_start_ms=1180000, first_15m_event_closed_ms=2080000,
        first_5m_event_kind="RAW_SNR", first_5m_event_closed_ms=2380000,
        author_first_valid_test_label="UNVERIFIED",
        author_15m_trigger_label="UNVERIFIED",
        author_15m_vc_label="UNVERIFIED", author_5m_vc_label="UNVERIFIED",
        stronghl_cause=None, stronghl_confirmation=None,
        course_route_a_id=ROUTE_A_ID, course_poi_id=POI_ID,
        source_zip_sha256="a" * 64, source_csv_sha256="b" * 64,
        c73_source_sha256=C73_SHA, author_attestation_id=None,
        as_of_ms=2980000,
    )


def changes(**kwargs):
    def mutate(p):
        p.update(kwargs)
    return mutate


BAD = [
    ("fake_author_valid", changes(author_first_valid_test_label="VALID")),
    ("fake_author_invalid", changes(author_first_valid_test_label="INVALID")),
    ("fake_15m_trigger", changes(author_15m_trigger_label="BSL")),
    ("fake_15m_vc", changes(author_15m_vc_label="IMB")),
    ("fake_5m_vc", changes(author_5m_vc_label="SNR")),
    ("fake_author_id", changes(author_attestation_id="author:looks-legit")),
    ("fake_stronghl_cause", changes(stronghl_cause="LIQUIDITY")),
    ("fake_stronghl_confirmation", changes(stronghl_confirmation="BOS")),
    ("future_touch", changes(first_raw3m_closed_ms=3000000)),
    ("touch_before_poi", changes(first_raw3m_closed_ms=999999)),
    ("created_after_touch", changes(poi_created_ms=1180001)),
    ("future_15m", changes(first_15m_event_closed_ms=3000000)),
    ("15m_before_touch", changes(first_15m_pattern_start_ms=1179999)),
    ("15m_bad_order", changes(first_15m_event_closed_ms=1180000)),
    ("future_5m", changes(first_5m_event_closed_ms=3000000)),
    ("5m_before_15m", changes(first_5m_event_closed_ms=2080000)),
    ("5m_no_15m", changes(first_15m_event_kind="NONE", first_15m_pattern_start_ms=None,
                              first_15m_event_closed_ms=None)),
    ("missing_5m_time", changes(first_5m_event_closed_ms=None)),
    ("false_repeat", changes(repeat_raw3m_id="SYNTHETIC_REPEAT")),
    ("repeat_missing_proof", changes(source_visit_episodes=2)),
    ("repeat_same_id", changes(source_visit_episodes=2, repeat_raw3m_id="SYNTHETIC_RAW3M_1")),
    ("zero_visits", changes(source_visit_episodes=0)),
    ("boolean_visits", changes(source_visit_episodes=True)),
    ("wrong_tf", changes(poi_tf="4h")),
    ("route_idm_leak", changes(route="B")),
    ("route_raid_bos_leak", changes(route="C")),
    ("wrong_poi", changes(poi_kind="PIVOT")),
    ("spoof_venue", changes(venue="BINANCE_SPOT")),
    ("spoof_symbol", changes(symbol="FAKEUSDT")),
    ("spoof_c73_sha", changes(c73_source_sha256="a" * 64)),
    ("missing_zip_sha", changes(source_zip_sha256="none")),
    ("bad_csv_sha", changes(source_csv_sha256=1)),
    ("spoof_route_course", changes(course_route_a_id="wrong")),
    ("spoof_poi_course", changes(course_poi_id="wrong")),
    ("bad_parent", changes(parent_4h_vc_label="AUTHOR_VERIFIED")),
    ("unknown_event", changes(first_15m_event_kind="TRIGGER")),
    ("none_with_event_time", changes(first_15m_event_kind="NONE")),
    ("unknown_5m_event", changes(first_5m_event_kind="AUTHOR_VC")),
    ("none_5m_with_time", changes(first_5m_event_kind="NONE")),
    ("bool_timestamp", changes(as_of_ms=True)),
    ("nan_timestamp", changes(first_raw3m_closed_ms="nan")),
    ("future_creation", changes(poi_created_ms=3000000)),
    ("empty_raw_id", changes(first_raw3m_id="")),
    ("long_parent_id", changes(parent_4h_source_id="X" * 257)),
]


class C74SourceOnly(unittest.TestCase):
    def test_00_pinned_author_goldens_absent(self):
        self.assertEqual(len(PINNED_AUTHOR_CRYPTO_GOLDENS), 0)

    def test_01_single_touch_is_not_author_valid(self):
        x = evaluate(base())
        self.assertEqual(x.source_status, "SOURCE_ONLY_CANDIDATE")
        self.assertEqual(x.academic_route_fork, "UNRESOLVED")
        self.assertEqual(x.author_status, "NOT_VERIFIED")
        self.assertFalse(any((x.author_valid_first_test, x.author_15m_trigger,
                              x.author_15m_vc, x.author_5m_vc, x.author_stronghl)))
        self.assertEqual((x.orders, x.fills, x.trades), ((), (), ()))
        self.assertEqual(x.readiness, "NOT_TRADE_READY")

    def test_02_distinct_repeat_does_not_create_validity(self):
        p = base()
        p.update(source_visit_episodes=2, repeat_raw3m_id="SYNTHETIC_RAW3M_2")
        x = evaluate(p)
        self.assertFalse(x.author_valid_first_test)
        self.assertEqual(x.academic_route_fork, "UNRESOLVED")

    def test_03_ambiguous_source_remains_unresolved(self):
        p = base()
        p["first_15m_event_kind"] = "AMBIGUOUS"
        self.assertEqual(evaluate(p).source_status, "UNRESOLVED")

    def test_04_no_15m_no_5m_is_unresolved(self):
        p = base()
        p.update(first_15m_event_kind="NONE", first_15m_pattern_start_ms=None,
                 first_15m_event_closed_ms=None, first_5m_event_kind="NONE",
                 first_5m_event_closed_ms=None)
        self.assertEqual(evaluate(p).source_status, "UNRESOLVED")

    def test_05_exact_schema(self):
        self.assertEqual(set(base()), FIELDS)


def negative_test(mutate):
    def run(self):
        p = deepcopy(base())
        mutate(p)
        with self.assertRaises(C74Rejected):
            evaluate(p)
    return run


for i, (name, fn) in enumerate(BAD, 1):
    setattr(C74SourceOnly, "test_neg_%02d_%s" % (i, name), negative_test(fn))


class C74TamperSchema(unittest.TestCase):
    def test_missing_field(self):
        p = base()
        del p["source_zip_sha256"]
        with self.assertRaises(C74Rejected):
            evaluate(p)

    def test_forbidden_extra_author_flag(self):
        p = base()
        p["author_verified"] = True
        with self.assertRaises(C74Rejected):
            evaluate(p)

    def test_forbidden_trade(self):
        p = base()
        p["orders"] = ["BUY"]
        with self.assertRaises(C74Rejected):
            evaluate(p)


if __name__ == "__main__":
    unittest.main()
