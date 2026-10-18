"""C29 24 adversarial source/academic RB-SNR NON-approval controls."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c20b_hourly_fractal_source_observer import HourSource
from c21_native3m_source_bridge import SEPT_START,THREE
from c29_rb_snr_source_guards import (
    _pair_record,_digest,observe_opposite_pairs,structural_gates,inspect_c29,HOUR)
from test_c21b_native_3m_vs_5m import make3

def h(i,op="100",close="101",high="105",low="95"):
    return HourSource(i*HOUR,(i+1)*HOUR,D(op),D(high),D(low),D(close),
        tuple("source-"+str(i)+":"+str(j) for j in range(20)))

class C29AdversarialAcademicGates(unittest.TestCase):
    def test_buy_sell_pair_never_rb(self):
        a=h(0,op="100",close="101")
        b=h(1,op="103",close="99")
        p=_pair_record(a,b)
        self.assertEqual(p.direction,"BUY_THEN_SELL")
        self.assertEqual(p.rb_gate,"NEEDS_AUTHOR_WICK_RAID_OR_IMB_INTERACTION")
        self.assertFalse(p.author_approved)
    def test_sell_buy_and_next_closed_strict_bullish_envelope(self):
        a=h(0,op="103",close="99")
        b=h(1,op="100",close="101")
        third=h(2,op="104",close="107",high="110")
        p=_pair_record(a,b,third)
        self.assertEqual(p.direction,"SELL_THEN_BUY")
        self.assertTrue(p.stricter_envelope_follow_through)
        self.assertEqual(p.next_hour_known_ms,3*HOUR)
        self.assertEqual(p.snr_gate,"NEEDS_AUTHOR_LIQ_OR_FVG_AND_ZONE_SETTLEMENT")
    def test_sell_buy_third_close_equal_wick_top_not_confirmed(self):
        p=_pair_record(h(0,op="102",close="98"),
                      h(1,op="99",close="101"),h(2,op="102",close="105"))
        self.assertFalse(p.stricter_envelope_follow_through)
    def test_sell_buy_third_close_above_body_but_below_wick_top_not_full_envelope(self):
        p=_pair_record(h(0,op="103",close="99"),
                      h(1,op="100",close="102"),h(2,op="103",close="104"))
        self.assertFalse(p.stricter_envelope_follow_through)
    def test_buy_sell_strict_bearish_envelope_follow(self):
        p=_pair_record(h(0,op="100",close="102"),
            h(1,op="103",close="98"),h(2,op="96",close="94",low="90",high="100"))
        self.assertTrue(p.stricter_envelope_follow_through)
    def test_third_missing_is_not_false_author_snr(self):
        p=_pair_record(h(0,op="100",close="102"),h(1,op="103",close="99"))
        self.assertIsNone(p.next_hour_ms)
        self.assertIsNone(p.stricter_envelope_follow_through)
        self.assertEqual(structural_gates(p)["snr"],
            "NEEDS_AUTHOR_LIQ_FVG_CONTEXT_AND_AUTHORED_SETTLEMENT_LEVEL")
    def test_opposed_pair_without_wick_evidence_cannot_be_approved(self):
        p=_pair_record(h(0),h(1,op="103",close="98"))
        got=structural_gates(p)
        self.assertEqual(got["author_approved_trades"],0)
        self.assertIn("WICK",got["rb"])
    def test_caller_supplied_fake_wick_hint_cannot_promote(self):
        p=_pair_record(h(0),h(1,op="103",close="98"))
        got=structural_gates(p,wick_raid_evidence="I_SWEAR_IT_WAS_WICK",
            fvg_test_evidence="UNKNOWN",author_zone_level=D("102"))
        self.assertEqual(got["readiness"],"NOT_TRADE_READY")
        self.assertIn("NEEDS_AUTHOR",got["rb"])
    def test_forged_author_golden_is_rejected(self):
        p=_pair_record(h(0),h(1,op="103",close="98"))
        with self.assertRaisesRegex(ValueError,"AUTHOR_GOLDEN_NOT_PROVIDED"):
            structural_gates(p,author_labeled=True)
    def test_forged_source_pair_approved_rejected(self):
        p=_pair_record(h(0),h(1,op="103",close="98"))
        with self.assertRaisesRegex(ValueError,"FORGED_SOURCE_PAIR"):
            structural_gates(replace(p,author_approved=True))
    def test_body_only_snr_rule_cannot_be_applied_to_rb(self):
        p=_pair_record(h(0),h(1,op="103",close="98"),
             h(2,op="95",close="94",low="90"))
        v=structural_gates(p)
        self.assertNotEqual(v["snr"],v["rb"])
        self.assertEqual(v["author_approved_trades"],0)
    def test_mb_is_not_snr_volume_confirmation(self):
        p=_pair_record(h(0),h(1,op="103",close="98"))
        self.assertEqual(structural_gates(p)["mitigation_block"],
            "MB_NOT_SNR_VOLUME_CONFIRMATION")
    def test_first_poi_test_requires_authored_zone_not_pair_envelope(self):
        p=_pair_record(h(0),h(1,op="103",close="98"))
        self.assertEqual(structural_gates(p)["first_test"],
            "NEEDS_AUTHOR_POI_WICK_BOUNDS_AND_FIRST_TEST_LABEL")
    def test_same_color_pair_is_never_eligible(self):
        with self.assertRaisesRegex(ValueError,"NOT_OPPOSING"):
            _pair_record(h(0),h(1))
    def test_doji_pair_is_never_eligible(self):
        with self.assertRaisesRegex(ValueError,"NOT_OPPOSING"):
            _pair_record(h(0,op="100",close="100"),h(1,op="103",close="98"))
    def test_pair_must_be_adjacent(self):
        with self.assertRaisesRegex(ValueError,"NONCONTIGUOUS"):
            _pair_record(h(0),h(2,op="103",close="98"))
    def test_missing_native_3m_rows_rejected(self):
        with self.assertRaisesRegex(ValueError,"MISSING_20"):
            observe_opposite_pairs((replace(h(0),native_rows=("onlyone",)),),as_of_ms=HOUR)
    def test_nonfinite_price_rejected(self):
        with self.assertRaisesRegex(ValueError,"NONFINITE_DECIMAL"):
            observe_opposite_pairs((replace(h(0),high=D("NaN")),),as_of_ms=HOUR)
    def test_incorrect_ohlc_price_rejected(self):
        with self.assertRaisesRegex(ValueError,"IMPOSSIBLE_OHLC"):
            observe_opposite_pairs((replace(h(0),low=D("102")),),as_of_ms=HOUR)
    def test_noncontiguous_1h_rejected(self):
        with self.assertRaisesRegex(ValueError,"OPEN_OR_NONCONTIGUOUS"):
            observe_opposite_pairs((h(0),h(2)),as_of_ms=3*HOUR)
    def test_unclosed_third_does_not_leak_into_prefix(self):
        hours=(h(0),h(1,op="103",close="98"),h(2,op="94",close="92",low="90"))
        pairs=observe_opposite_pairs(hours,as_of_ms=2*HOUR)
        self.assertEqual(len(pairs),1)
        self.assertIsNone(pairs[0].next_hour_ms)
    def test_source_digest_changes_on_raw_lineage_change(self):
        p=_pair_record(h(0),h(1,op="103",close="98"))
        self.assertNotEqual(_digest((p,)),_digest((replace(p,first_row_id="tamper"),)))
    def test_original_source_cannot_be_trade_approved_and_prefix_is_stable(self):
        src=make3()
        original=inspect_c29(src,as_of_ms=src.as_of_ms)
        self.assertEqual(original.author_approved_trades,0)
        self.assertEqual(original.readiness,"NOT_TRADE_READY")
        cut=SEPT_START+141*THREE
        trunc=replace(src,as_of_ms=cut,original_3m_closed=src.original_3m_closed[:141])
        self.assertEqual(inspect_c29(src,as_of_ms=cut),inspect_c29(trunc,as_of_ms=cut))
    def test_forged_ready_and_original_source_tamper_blocked(self):
        src=make3()
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            inspect_c29(replace(src,readiness="READY"),as_of_ms=src.as_of_ms)
        rows=src.original_3m_closed
        altered=replace(src,original_3m_closed=rows[:103]+
            (replace(rows[103],raw_id="forged"),)+rows[104:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_c29(altered,as_of_ms=altered.as_of_ms)
if __name__=="__main__":
    unittest.main()
