"""ISO01 adversarial identity/state tests; no market or trade goldens."""
from dataclasses import replace
import unittest

from c56_crypto_native5m_1h_raid_bos_cross_tf import (
    BARRIERS, C56CrossTimeframeParent, MISSING, TYPES,
)
from iso01_route_c_parent_object_state import (
    BOTH, ONLY_3M, ONLY_5M, UNKNOWN_3M, UNKNOWN_5M,
    ISO01RouteCParentState, NativeSourceCoverage,
    build_parent_state_registry, identify_route_c_parent_state, parent_identity,
)

HOUR = 3_600_000
THREE = 180_000
FIVE = 300_000
O = 1_788_220_800_000
B = O + 5 * HOUR
CONFIRMED = B + 2 * HOUR
K = B + 3 * HOUR
AS_OF = K + 24 * HOUR
A = "a" * 64 + ":"
F = "b" * 64 + ":"


def parent(**changes):
    value = C56CrossTimeframeParent(
        "BTCUSDT", "BSL", O, B, CONFIRMED,
        A + str(K), K + THREE, F + str(K), K + FIVE, TYPES[0],
    )
    return replace(value, **changes)


def only3():
    return parent(original_5m_bos_raw_id=None, original_5m_bos_known_ms=None,
                  source_status=MISSING[0])


def only5():
    return parent(original_3m_bos_raw_id=None, original_3m_bos_known_ms=None,
                  source_status=MISSING[1])


def coverage(tf, *, complete=True, through=AS_OF, rows=100):
    return NativeSourceCoverage(tf, complete, through, rows)


def identify(p=None, *, c3=None, c5=None, as_of=AS_OF):
    return identify_route_c_parent_state(
        p or parent(), as_of_ms=as_of,
        coverage_3m=c3 or coverage("3m"),
        coverage_5m=c5 or coverage("5m"),
    )


class ISO01ParentObjectState(unittest.TestCase):
    def refuse(self, label, p=None, **kwargs):
        with self.assertRaisesRegex(ValueError, label):
            identify(p, **kwargs)

    def test_valid_dual_observation(self):
        state = identify()
        self.assertEqual(state.observation_state, BOTH)
        self.assertEqual(state.parent.source_status, TYPES[0])

    def test_parent_id_is_stable_sha_identity(self):
        self.assertRegex(parent_identity(parent()), r"^iso01-1h-[a-f0-9]{64}$")
        self.assertEqual(parent_identity(parent()), parent_identity(parent()))

    def test_child_event_does_not_rename_parent(self):
        other = parent(original_3m_bos_raw_id=A + str(K + HOUR),
                       original_3m_bos_known_ms=K + HOUR + THREE)
        self.assertEqual(parent_identity(parent()), parent_identity(other))

    def test_different_1h_parent_has_different_identity(self):
        self.assertNotEqual(parent_identity(parent()),
                            parent_identity(parent(first_1h_breach_ms=B + HOUR,
                                                   raid_closed_known_ms=CONFIRMED + HOUR)))

    def test_only_3m_with_complete_5m_is_observed_detector_absence(self):
        self.assertEqual(identify(only3()).observation_state, ONLY_3M)

    def test_only_3m_with_incomplete_5m_is_unknown(self):
        state = identify(only3(), c5=coverage("5m", complete=False))
        self.assertEqual(state.observation_state, UNKNOWN_5M)
        self.assertEqual(state.timing_interpretation, "MISSING_5M_NOT_OBSERVABLE_AT_AS_OF")

    def test_stale_5m_coverage_cannot_prove_absence(self):
        state = identify(only3(), c5=coverage("5m", through=AS_OF - FIVE))
        self.assertEqual(state.observation_state, UNKNOWN_5M)

    def test_only_5m_with_complete_3m(self):
        self.assertEqual(identify(only5()).observation_state, ONLY_5M)

    def test_only_5m_with_incomplete_3m_is_unknown(self):
        self.assertEqual(identify(only5(), c3=coverage("3m", complete=False)).observation_state,
                         UNKNOWN_3M)

    def test_same_close_is_not_merged_into_one_child(self):
        known = K + 15 * 60_000
        p = parent(original_3m_bos_known_ms=known,
                   original_3m_bos_raw_id=A + str(known - THREE),
                   original_5m_bos_known_ms=known,
                   original_5m_bos_raw_id=F + str(known - FIVE),
                   source_status=TYPES[2])
        state = identify(p)
        self.assertEqual(state.observation_state, BOTH)
        self.assertEqual(state.timing_interpretation,
                         "SAME_CLOSED_KNOWLEDGE_TIME_DISTINCT_NATIVE_EVENTS")

    def test_earlier_5m_is_timing_not_direction_contradiction(self):
        p = parent(original_3m_bos_known_ms=K + HOUR,
                   original_3m_bos_raw_id=A + str(K + HOUR - THREE),
                   source_status=TYPES[1])
        self.assertEqual(identify(p).timing_interpretation,
                         "DIFFERENT_CLOSED_KNOWLEDGE_TIMES_NOT_CONTRADICTION")

    def test_no_author_or_trade_promotion(self):
        state = identify()
        self.assertFalse(state.author_object_identity_approved or state.author_bos_approved)
        self.assertEqual((state.orders, state.fills, state.trades), ((), (), ()))
        self.assertEqual(state.readiness, "NOT_TRADE_READY")

    def test_untrusted_parent_rejected(self):
        self.refuse("UNTRUSTED_C56_PARENT", {"symbol": "BTCUSDT"})

    def test_fx_parent_rejected(self):
        self.refuse("UNSUPPORTED_MARKET", parent(symbol="EURUSD"))

    def test_unknown_liquidity_kind_rejected(self):
        self.refuse("UNSUPPORTED_MARKET", parent(raid_type="EQH"))

    def test_future_parent_rejected(self):
        self.refuse("FUTURE_1H_PARENT", as_of=CONFIRMED - HOUR)

    def test_wrong_parent_confirmation_rejected(self):
        self.refuse("FUTURE_1H_PARENT", parent(raid_closed_known_ms=CONFIRMED + HOUR))

    def test_pivot_not_preknown_rejected(self):
        self.refuse("FUTURE_1H_PARENT", parent(first_1h_pivot_center_ms=B - HOUR))

    def test_author_approval_rejected(self):
        self.refuse("PROMOTION_FORBIDDEN", parent(author_bos_approved=True))

    def test_order_promotion_rejected(self):
        self.refuse("PROMOTION_FORBIDDEN", parent(orders=({"side": "SHORT"},)))

    def test_readiness_promotion_rejected(self):
        self.refuse("PROMOTION_FORBIDDEN", parent(readiness="READY"))

    def test_missing_barriers_rejected(self):
        self.refuse("PROMOTION_FORBIDDEN", parent(blockers=()))

    def test_partial_child_event_rejected(self):
        self.refuse("PARTIAL_5M_EVENT", parent(original_5m_bos_known_ms=None))

    def test_parent_without_children_rejected(self):
        p = parent(original_3m_bos_raw_id=None, original_3m_bos_known_ms=None,
                   original_5m_bos_raw_id=None, original_5m_bos_known_ms=None,
                   source_status=MISSING[0])
        self.refuse("WITHOUT_ANY_CHILD", p)

    def test_status_event_mismatch_rejected(self):
        self.refuse("STATUS_EVENT_MISMATCH", parent(source_status=TYPES[1]))

    def test_bad_raw_id_rejected(self):
        self.refuse("BAD_ORIGINAL_3m_RAW_ID", parent(original_3m_bos_raw_id="forged"))

    def test_raw_id_open_time_mismatch_rejected(self):
        self.refuse("RAW_ID_NOT_NATIVE_BAR_OPEN",
                    parent(original_3m_bos_raw_id=A + str(K + THREE)))

    def test_future_child_rejected(self):
        self.refuse("FUTURE_OR_PRE_PARENT_3M",
                    parent(original_3m_bos_known_ms=AS_OF + THREE,
                           original_3m_bos_raw_id=A + str(AS_OF)))

    def test_child_before_parent_confirmation_rejected(self):
        self.refuse("FUTURE_OR_PRE_PARENT_3M",
                    parent(original_3m_bos_known_ms=CONFIRMED - THREE,
                           original_3m_bos_raw_id=A + str(CONFIRMED - 2 * THREE)))

    def test_child_known_exactly_at_parent_confirmation_rejected(self):
        self.refuse("FUTURE_OR_PRE_PARENT_3M",
                    parent(original_3m_bos_known_ms=CONFIRMED,
                           original_3m_bos_raw_id=A + str(CONFIRMED - THREE)))

    def test_same_source_hash_across_native_tf_rejected(self):
        self.refuse("BORROWED_CROSS_TF_RAW_ID",
                    parent(original_5m_bos_raw_id=A + str(K)))

    def test_wrong_coverage_timeframe_rejected(self):
        self.refuse("WRONG_5m_COVERAGE", c5=coverage("3m"))

    def test_future_coverage_rejected(self):
        self.refuse("FUTURE_OR_UNALIGNED_5m", c5=coverage("5m", through=AS_OF + FIVE))

    def test_unaligned_coverage_rejected(self):
        self.refuse("FUTURE_OR_UNALIGNED_5m", c5=coverage("5m", through=AS_OF - 1))

    def test_empty_coverage_rejected(self):
        self.refuse("INVALID_3m_COVERAGE", c3=coverage("3m", rows=0))

    def test_nonboolean_coverage_rejected(self):
        self.refuse("INVALID_3m_COVERAGE", c3=coverage("3m", complete=1))

    def test_registry_rejects_duplicate_parent(self):
        state = identify()
        with self.assertRaisesRegex(ValueError, "DUPLICATE_1H_PARENT"):
            build_parent_state_registry((state, state))

    def test_registry_rejects_forged_identity(self):
        state = identify()
        forged = replace(state, parent_id="iso01-1h-" + "0" * 64)
        with self.assertRaisesRegex(ValueError, "FORGED_PARENT_ID"):
            build_parent_state_registry((forged,))

    def test_registry_rejects_forged_observation_or_trade_fields(self):
        state = identify()
        for changes in ({"observation_state": ONLY_3M}, {"readiness": "READY"},
                        {"orders": ({"side": "SHORT"},)}):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ValueError, "FORGED_STATE_FIELDS"):
                    build_parent_state_registry((replace(state, **changes),))

    def test_registry_deterministic_and_typed(self):
        states = (identify(parent(first_1h_pivot_center_ms=O + HOUR)), identify())
        result = build_parent_state_registry(states)
        self.assertEqual(len(result), 2)
        self.assertEqual(result, build_parent_state_registry(reversed(states)))
        self.assertTrue(all(isinstance(x, ISO01RouteCParentState) for x in result))


if __name__ == "__main__":
    unittest.main()
