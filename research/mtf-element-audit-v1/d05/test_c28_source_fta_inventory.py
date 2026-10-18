"""C28 source IMB and FTA containment tests. 21 independent negative controls."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace as NS
from c20b_hourly_fractal_source_observer import HourSource
from c21_native3m_source_bridge import THREE,SEPT_START
from c28_source_fta_inventory import (
    classic_1h_imb,gap_history,price_interval_overlap,Gap,inspect_c28,
    _witness,_sha_all)
from test_c21b_native_3m_vs_5m import make3

H=3600000
def h(i,*,high="100",low="90",op="95",close="95"):
    return HourSource(i*H,(i+1)*H,D(op),D(high),D(low),D(close),
        tuple("native-"+str(i)+":"+str(j) for j in range(20)))
def gap(kind="BULL_CLASSIC_IMB",low="100",top="105",known=H):
    return Gap(kind,D(low),D(top),0,known-H,known,
               ("h00","h01","h02"))
def bar(i,*,low="98",high="110",close="102"):
    return NS(start_ms=i*THREE,known_ms=(i+1)*THREE,
              low=D(low),high=D(high),close=D(close),
              raw_id="original-"+str(i))

class C28OriginalSourceControls(unittest.TestCase):
    def test_bullish_1h_gap_causal_three_hour_source(self):
        x=classic_1h_imb((h(0,high="100",low="90"),h(1),
            h(2,high="115",low="105",op="107",close="110")))
        self.assertEqual(len(x),1)
        self.assertEqual((x[0].kind,x[0].bottom,x[0].top),
            ("BULL_CLASSIC_IMB",D("100"),D("105")))
        self.assertEqual(x[0].known_ms,3*H)
        self.assertEqual(len(x[0].original_1h_row_ids),3)
    def test_bearish_gap_causal_three_hour_source(self):
        x=classic_1h_imb((h(0,high="100",low="90"),h(1),
            h(2,high="85",low="75",op="80",close="80")))
        self.assertEqual((x[0].kind,x[0].bottom,x[0].top),
                         ("BEAR_CLASSIC_IMB",D("85"),D("90")))
    def test_shared_wick_boundary_is_no_imb(self):
        x=classic_1h_imb((h(0,high="100",low="90"),h(1),
            h(2,high="110",low="100",op="105",close="105")))
        self.assertEqual(x,())
    def test_noncontiguous_hour_refused(self):
        with self.assertRaisesRegex(ValueError,"NONCONTIGUOUS"):
            classic_1h_imb((h(0),h(2),h(3)))
    def test_open_1h_refused(self):
        h0=replace(h(0),close_ms=H-THREE)
        with self.assertRaisesRegex(ValueError,"NONCONTIGUOUS"):
            classic_1h_imb((h0,h(1),h(2)))
    def test_missing_20_native3m_sources_refused(self):
        with self.assertRaisesRegex(ValueError,"MISSING_SOURCE"):
            classic_1h_imb((replace(h(0),native_rows=("only1",)),))
    def test_nonfinite_hour_price_refused(self):
        with self.assertRaisesRegex(ValueError,"BAD_1H_PRICE"):
            classic_1h_imb((replace(h(0),high=D("NaN")),))
    def test_impossible_hour_ohlc_refused(self):
        with self.assertRaisesRegex(ValueError,"IMPOSSIBLE_1H_PRICE"):
            classic_1h_imb((replace(h(0),low=D("99")),))
    def test_no_future_gap_known_at(self):
        with self.assertRaisesRegex(ValueError,"UNPREKNOWN"):
            gap_history(gap(known=3*H),(),before_ms=2*H)
    def test_gap_first_touch_is_one_known_closed_3m(self):
        x=gap_history(gap(known=THREE),(
            bar(1,low="110",high="115"),bar(2,low="104",high="110"),
            bar(3,low="99",high="111")),before_ms=4*THREE)
        self.assertEqual(x.first_touch_ms,2*THREE)
        self.assertEqual(x.first_full_traversal_ms,3*THREE)
        self.assertEqual(x.state,"FULL_WICK_TRAVERSAL_OBSERVED")
    def test_zone_equality_is_touch_not_full_traversal(self):
        x=gap_history(gap(known=THREE),
            (bar(1,low="105",high="120"),),before_ms=2*THREE)
        self.assertEqual(x.state,"PRIOR_WICK_TOUCH_OBSERVED")
        self.assertIsNone(x.first_full_traversal_ms)
    def test_future_touch_after_asof_excluded(self):
        x=gap_history(gap(known=THREE),(
            bar(1,low="110",high="115"),bar(2,low="101",high="104")),
            before_ms=2*THREE)
        self.assertEqual(x.state,"NO_PRIOR_WICK_TOUCH_OBSERVED")
    def test_corrupt_unclosed_or_reordered_native3m_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNORDERED"):
            gap_history(gap(known=THREE),(bar(2),bar(1)),before_ms=4*THREE)
    def test_invalid_gap_bounds_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNPREKNOWN"):
            gap_history(gap(low="105",top="100"),(),before_ms=2*THREE)
    def test_strict_zone_overlap_not_single_price_boundary(self):
        x=gap(known=H)
        self.assertFalse(price_interval_overlap(x,"LONG",D("95"),D("100")))
        self.assertTrue(price_interval_overlap(x,"LONG",D("95"),D("103")))
        self.assertFalse(price_interval_overlap(x,"SHORT",D("110"),D("105")))
    def test_target_wrong_side_rejected(self):
        with self.assertRaisesRegex(ValueError,"TARGET_WRONG_SIDE"):
            price_interval_overlap(gap(),"LONG",D("110"),D("100"))
    def test_missing_target_is_not_replaced_with_imaginary_fta(self):
        self.assertFalse(price_interval_overlap(gap(),"LONG",D("95"),None))
    def test_no_tolerance_from_author_gap_fraction(self):
        x=gap()
        self.assertFalse(price_interval_overlap(x,"LONG",D("95"),D("99.999999999")))
    def test_full_witness_digest_is_sensitive_to_first_touch(self):
        g=gap(known=THREE)
        a=_witness(g,gap_history(g,(bar(1,low="110",high="115"),),before_ms=2*THREE))
        b=_witness(g,gap_history(g,(bar(1,low="100",high="115"),),before_ms=2*THREE))
        self.assertNotEqual(_sha_all((a,)),_sha_all((b,)))
    def test_synthetic_original_data_cannot_approve_trade(self):
        r=inspect_c28(make3(),as_of_ms=make3().as_of_ms)
        self.assertEqual(r.author_approved_trades,0)
        self.assertEqual(r.readiness,"NOT_TRADE_READY")
        self.assertTrue(all(not c.author_approved and
            c.candidate_ranking_status=="AUTHOR_FTA_PRIORITY_UNKNOWN" for c in r.cases))
    def test_physically_truncated_source_asof_equivalence(self):
        source=make3();cut=SEPT_START+141*THREE
        truncated=replace(source,as_of_ms=cut,original_3m_closed=source.original_3m_closed[:141])
        self.assertEqual(inspect_c28(source,as_of_ms=cut),
                         inspect_c28(truncated,as_of_ms=cut))
    def test_forged_ready_or_original_row_tamper_refused(self):
        source=make3()
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            inspect_c28(replace(source,readiness="READY"),as_of_ms=source.as_of_ms)
        rows=source.original_3m_closed
        tampered=replace(source,original_3m_closed=rows[:101]+
                        (replace(rows[101],raw_id="FORGED"),)+rows[102:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_c28(tampered,as_of_ms=tampered.as_of_ms)

if __name__=="__main__":unittest.main()
