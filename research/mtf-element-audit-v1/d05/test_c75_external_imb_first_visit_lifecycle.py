"""C75 external FVG hypothesis: negative/adversarial source-only tests."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c72_original_native5m_source_vc_after15m_gate import Original5m
from c75_external_imb_first_visit_lifecycle import (
    scan_native_fvg, inspect_fvg_visits, classify_c73_fork, C75Rejected)

B = 1788220800000
STEP = 300000
SHA = "a" * 64


def row(i, op, hi, lo, cl, *, symbol="BTCUSDT", sha=SHA, known=None):
    at = B + i * STEP
    return Original5m(symbol, at, at + STEP if known is None else known,
                      D(str(op)), D(str(hi)), D(str(lo)),
                      D(str(cl)), D("1"), sha, sha + ":" + str(at))


def pack():
    return (row(0, 95, 100, 90, 96),
            row(1, 100, 110, 99, 108),
            row(2, 104, 112, 102, 111),
            row(3, 110, 114, 101, 112),
            row(4, 111, 115, 101, 114),
            row(5, 114, 116, 113, 115),
            row(6, 113, 118, 100.8, 117),
            row(7, 103, 113, 98, 99))


def first(rows):
    candidates = scan_native_fvg(rows, tf="5m", as_of_ms=rows[-1].known_ms)
    return next(x for x in candidates if x.known_ms == B + 3 * STEP)


class C75FVGSourceOnly(unittest.TestCase):
    def test_01_geometry(self):
        z = first(pack()[:3])
        self.assertEqual((z.side, z.lower, z.upper), ("LONG", D("100"), D("102")))
        self.assertFalse(z.author_imb_vc)
        self.assertEqual(z.evidence_class, "ADAPTED_HYPOTHESIS")

    def test_02_single_visit(self):
        rows = pack()[:5]
        x = inspect_fvg_visits(first(rows), rows, as_of_ms=rows[-1].known_ms)
        self.assertEqual((x.separate_visits, x.state), (1, "FIRST_VISIT_SOURCE_ONLY"))
        self.assertIsNone(x.first_repeat_id)
        self.assertEqual((x.orders, x.fills, x.trades), ((), (), ()))

    def test_03_distinct_revisit_after_fully_outside_bar(self):
        rows = pack()[:7]
        x = inspect_fvg_visits(first(rows), rows, as_of_ms=rows[-1].known_ms)
        self.assertEqual((x.separate_visits, x.state), (2, "REPEATED_VISIT_SOURCE_ONLY"))
        self.assertEqual(x.first_repeat_id, rows[6].raw_id)

    def test_04_closed_beyond_zone_is_not_a_trade(self):
        rows = pack()
        x = inspect_fvg_visits(first(rows), rows, as_of_ms=rows[-1].known_ms)
        self.assertEqual(x.state, "CLOSED_THROUGH_FVG_NOT_AUTHOR")
        self.assertIsNotNone(x.first_close_through_id)
        self.assertFalse(x.owner_first_valid_test)

    def test_05_no_future_bar_in_first_three(self):
        rows = pack()[:3]
        with self.assertRaises(C75Rejected):
            scan_native_fvg(rows, tf="5m", as_of_ms=rows[-1].known_ms - 1)

    def test_06_no_premature_gap_first_two(self):
        rows = pack()[:2]
        self.assertEqual(scan_native_fvg(rows, tf="5m", as_of_ms=rows[-1].known_ms), ())

    def test_07_gap_zero_size_not_fvg(self):
        rows = (pack()[0], pack()[1], row(2, 104, 110, 100, 107))
        self.assertEqual(scan_native_fvg(rows, tf="5m", as_of_ms=rows[-1].known_ms), ())

    def test_08_bearish_gap_symmetry(self):
        rows = (row(0, 95, 100, 90, 94), row(1, 92, 93, 80, 82),
                row(2, 80, 85, 70, 78))
        x = first(rows)
        self.assertEqual((x.side, x.lower, x.upper), ("SHORT", D("85"), D("90")))

    def test_09_future_touched_no_retroactive_label(self):
        rows = pack()[:3]
        x = inspect_fvg_visits(first(rows), rows, as_of_ms=rows[-1].known_ms)
        self.assertEqual((x.separate_visits, x.state), (0, "NO_TEST_RIGHT_CENSORED"))

    def test_10_5m_synthetic_is_never_author_vc(self):
        x = inspect_fvg_visits(first(pack()), pack(), as_of_ms=pack()[-1].known_ms)
        self.assertFalse(x.owner_5m_vc)
        self.assertFalse(x.owner_15m_trigger)
        self.assertEqual(x.readiness, "NOT_TRADE_READY")

    def test_11_wrong_fvg_zone_rejected(self):
        rows = pack()
        with self.assertRaises(C75Rejected):
            inspect_fvg_visits(replace(first(rows), lower=D("99")), rows,
                               as_of_ms=rows[-1].known_ms)


def corrupt(mutator):
    def run(self):
        rows = list(pack()[:3])
        rows[1] = mutator(rows[1])
        with self.assertRaises(C75Rejected):
            scan_native_fvg(tuple(rows), tf="5m", as_of_ms=rows[-1].known_ms)
    return run


CORRUPT = {
    "cross_symbol": lambda x: replace(x, symbol="ETHUSDT"),
    "cross_venue_id": lambda x: replace(x, raw_id="WRONG"),
    "spoof_sha": lambda x: replace(x, zip_sha="Z" * 64),
    "wrong_known_ms": lambda x: replace(x, known_ms=x.known_ms + 1),
    "shifted_time": lambda x: replace(x, start_ms=x.start_ms + 1),
    "unclosed_future": lambda x: replace(x, known_ms=x.known_ms + 9999999),
    "negative_volume": lambda x: replace(x, volume=D("-1")),
    "nan_price": lambda x: replace(x, low=D("NaN")),
    "infinite_price": lambda x: replace(x, close=D("Infinity")),
    "impossible_ohlc": lambda x: replace(x, high=D("1")),
    "zero_price": lambda x: replace(x, low=D("0")),
    "bad_precision": lambda x: replace(x, close=108),
    "bad_sha_length": lambda x: replace(x, zip_sha="a" * 63),
}

for name, mutator in CORRUPT.items():
    setattr(C75FVGSourceOnly, "test_corrupt_" + name, corrupt(mutator))


class C75Tampering(unittest.TestCase):
    def test_wrong_tf(self):
        rows = pack()[:3]
        with self.assertRaises(C75Rejected):
            scan_native_fvg(rows, tf="15m", as_of_ms=rows[-1].known_ms)

    def test_wrong_native3m_tf(self):
        rows = pack()[:3]
        with self.assertRaises(C75Rejected):
            scan_native_fvg(rows, tf="3m", as_of_ms=rows[-1].known_ms)

    def test_unordered_source(self):
        rows = pack()
        with self.assertRaises(C75Rejected):
            scan_native_fvg((rows[1], rows[0], rows[2]), tf="5m",
                            as_of_ms=rows[2].known_ms)

    def test_cross_fvg_symbol(self):
        rows = pack()
        with self.assertRaises(C75Rejected):
            inspect_fvg_visits(replace(first(rows), symbol="SOLUSDT"), rows,
                               as_of_ms=rows[-1].known_ms)

    def test_promoted_zone(self):
        rows = pack()
        with self.assertRaises(C75Rejected):
            inspect_fvg_visits(replace(first(rows), evidence_class="AUTHOR_VERIFIED"),
                               rows, as_of_ms=rows[-1].known_ms)

    def test_boolean_asof(self):
        rows = pack()[:3]
        with self.assertRaises(C75Rejected):
            scan_native_fvg(rows, tf="5m", as_of_ms=True)

    def test_malformed_c73_author(self):
        with self.assertRaises(C75Rejected):
            classify_c73_fork({"readiness":"NOT_TRADE_READY", "author_15m_trigger":True})

    def test_c73_other_route_rejected(self):
        c = fake_c73()
        c["route_b_idm_used"] = True
        with self.assertRaises(C75Rejected):
            classify_c73_fork(c)

    def test_c73_fake_order_rejected(self):
        c = fake_c73()
        c["orders"] = ["LONG"]
        with self.assertRaises(C75Rejected):
            classify_c73_fork(c)

    def test_c73_first_vs_repeat_source_only(self):
        c = fake_c73()
        self.assertEqual(classify_c73_fork(c)[0], "SOURCE_FIRST_VISIT")
        c["state"] = "NEW_1H_POI_FIRST_15M_PATTERN_REVISITED_SOURCE_POI_NOT_OWNER_VALID"
        c["episodes_before_first_15m_pattern"] = 2
        self.assertEqual(classify_c73_fork(c)[0], "SOURCE_REVISIT")

    def test_c73_invalid_repeat_count(self):
        c = fake_c73()
        c["state"] = "NEW_1H_POI_FIRST_15M_PATTERN_REVISITED_SOURCE_POI_NOT_OWNER_VALID"
        with self.assertRaises(C75Rejected):
            classify_c73_fork(c)


def fake_c73():
    c = dict(state="NEW_1H_POI_FIRST_15M_PATTERN_SINGLE_SOURCE_VISIT_NOT_OWNER_VALID",
             readiness="NOT_TRADE_READY", episodes_before_first_15m_pattern=1,
             orders=[], fills=[], trades=[])
    for k in ("author_15m_trigger", "author_15m_vc",
              "author_1h_poi_valid_first_test", "author_5m_vc", "author_entry",
              "author_stronghl", "author_structural_sl", "route_b_idm_used",
              "route_c_raid_bos_used"):
        c[k] = False
    return c


if __name__ == "__main__":
    unittest.main()
