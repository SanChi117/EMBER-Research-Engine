"""C30 fail-closed falsification: true prior known liquidity and IMB geometry only."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c20b_hourly_fractal_source_observer import HourSource,HourFractal
from c28_source_fta_inventory import Gap
from c21_native3m_source_bridge import THREE,SEPT_START
from c30_causal_wick_liquidity_imb import (
    _cross,_imb_cross,_first_pivot_cross,_first_gap_touch,
    source_pair_wick_evidence,inspect_c30,HOUR)
from test_c21b_native_3m_vs_5m import make3

def h(i,op="100",close="101",high="105",low="95"):
    return HourSource(i*HOUR,(i+1)*HOUR,D(op),D(high),D(low),D(close),
        tuple("original-"+str(i)+":"+str(j) for j in range(20)))
def pivot(kind="BSL",price="110",known=HOUR):
    return HourFractal(kind,D(price),-HOUR,known,
                       tuple("pivot-"+str(i) for i in range(60)))
def gap(kind="BULL_CLASSIC_IMB",bottom="100",top="105",known=HOUR):
    return Gap(kind,D(bottom),D(top),-2*HOUR,known-HOUR,known,
               ("source-first","source-middle","source-third"))

class C30SourceCausalControls(unittest.TestCase):
    def test_bsl_wick_strict(self):
        self.assertEqual(_cross(h(0,op="99",close="100",high="111"),"BSL",D("110")),"WICK_ONLY")
    def test_bsl_body_not_wick(self):
        self.assertEqual(_cross(h(0,op="109",close="111",high="112"),"BSL",D("110")),"BODY_THROUGH")
    def test_bsl_equal_is_not_sweep(self):
        self.assertEqual(_cross(h(0,high="110"),"BSL",D("110")),"EQUALITY_ONLY")
    def test_ssl_wick_strict(self):
        self.assertEqual(_cross(h(0,op="100",close="102",low="90"),"SSL",D("94")),"WICK_ONLY")
    def test_ssl_body_not_wick(self):
        self.assertEqual(_cross(h(0,op="96",close="92",low="90"),"SSL",D("94")),"BODY_THROUGH")
    def test_ssl_equal_not_sweep(self):
        self.assertEqual(_cross(h(0,low="94"),"SSL",D("94")),"EQUALITY_ONLY")
    def test_cross_none(self):
        self.assertEqual(_cross(h(0,high="105"),"BSL",D("110")),"NO_CROSS")
    def test_wrong_pivot_kind_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVALID_LEVEL"):
            _cross(h(0),"NOT_BSL",D("110"))
    def test_imb_bull_wick_from_above(self):
        self.assertEqual(_imb_cross(h(1,op="110",close="108",high="115",low="103"),gap()),"WICK_ONLY")
    def test_imb_bull_body_into_gap(self):
        self.assertEqual(_imb_cross(h(1,op="110",close="103",high="112",low="102"),gap()),"BODY_INTERACTION")
    def test_imb_bull_equality_only(self):
        self.assertEqual(_imb_cross(h(1,op="110",close="109",high="112",low="105"),gap()),"BOUNDARY_ONLY")
    def test_imb_bull_wrong_side_does_not_count_wick(self):
        self.assertEqual(_imb_cross(h(1,op="97",close="98",high="109",low="95"),gap()),"NO_INTERACTION")
    def test_imb_bear_wick_from_below(self):
        self.assertEqual(_imb_cross(h(1,op="96",close="99",high="102",low="92"),
            gap(kind="BEAR_CLASSIC_IMB")),"WICK_ONLY")
    def test_imb_bear_body_into_gap(self):
        self.assertEqual(_imb_cross(h(1,op="96",close="102",high="104",low="92"),
            gap(kind="BEAR_CLASSIC_IMB")),"BODY_INTERACTION")
    def test_imb_bear_wrong_side_is_not_wick_test(self):
        self.assertEqual(_imb_cross(h(1,op="110",close="108",high="115",low="98"),
            gap(kind="BEAR_CLASSIC_IMB")),"NO_INTERACTION")
    def test_imb_unclosed_third_hour_cannot_be_known(self):
        with self.assertRaisesRegex(ValueError,"GAP_NOT_KNOWN"):
            _imb_cross(h(1),gap(known=2*HOUR))
    def test_first_pivot_breach_must_follow_right_confirm(self):
        p=pivot(known=2*HOUR)
        self.assertEqual(_first_pivot_cross(p,(h(0,high="112"),h(1,high="112"),
            h(2,high="112"))),2*HOUR)
    def test_first_imb_touch_after_third_gap_hour_close(self):
        g=gap(known=2*HOUR)
        self.assertEqual(_first_gap_touch(g,(h(0,op="110",close="110",high="115",low="103"),
             h(1,op="110",close="110",high="115",low="103"),
             h(2,op="110",close="110",high="115",low="103"))),2*HOUR)
    def test_pair_raid_must_precede_or_equal_source_known_at(self):
        hours=(h(0,op="100",close="102"),h(1,op="110",close="108",high="115",low="103"),
               h(2,op="110",close="108",high="115",low="103"))
        pp=pivot("BSL",price="112",known=2*HOUR)
        result=source_pair_wick_evidence(hours,(pp,),())
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].distinct_liquidity_wick_interactions,0)
    def test_pair_known_first_strict_liquidity_wick_is_distinct_not_author_rb(self):
        hours=(h(0,op="100",close="102"),h(1,op="100",close="101",high="112"),
               h(2,op="102",close="99",high="109"))
        pp=pivot("BSL",price="110",known=HOUR)
        result=source_pair_wick_evidence(hours,(pp,),())
        pair=next(p for p in result if p.first_ms==HOUR)
        self.assertGreater(pair.first_cross_liquidity_wick_interactions,0)
        self.assertIn("NEEDS_AUTHOR",pair.academic_rb_status)
        self.assertEqual(pair.readiness,"NOT_TRADE_READY")
    def test_pair_imb_first_wick_not_any_color_reversal(self):
        hours=(h(0,op="100",close="101"),h(1,op="110",close="108",high="115",low="103"),
               h(2,op="110",close="108",high="115",low="103"),
               h(3,op="104",close="100",high="110",low="98"))
        g=gap(known=HOUR)
        result=source_pair_wick_evidence(hours,(),(g,))
        p=next(p for p in result if p.first_ms==0)
        self.assertEqual(p.imb_wick_first_tests,1)
        self.assertEqual(p.academic_snr_status,"NEEDS_AUTHOR_SNR_LEVEL_THIRD_CLOSE_AND_FIRST_TEST")
    def test_second_touch_not_relabelled_first(self):
        hours=(h(0,op="108",close="110",high="114",low="102"),
               h(1,op="110",close="108",high="115",low="103"),
               h(2,op="110",close="108",high="115",low="103"))
        g=gap(known=0)
        result=source_pair_wick_evidence(hours,(),(g,))
        self.assertEqual(result[0].imb_wick_first_tests,1)
        self.assertEqual(result[0].source_imb_wick_interactions,2)
    def test_not_assume_missing_liquidity_proves_mitigation_block(self):
        pair=source_pair_wick_evidence((h(0),h(1,op="102",close="98")),(),())[0]
        self.assertEqual(pair.distinct_liquidity_wick_interactions,0)
        self.assertIn("NEEDS_AUTHOR",pair.academic_snr_status)
    def test_c30_synthetic_source_is_not_author_trade_and_asof_prefix_equivalent(self):
        src=make3()
        result=inspect_c30(src,as_of_ms=src.as_of_ms)
        self.assertEqual(result.approved_trades,0)
        self.assertEqual(result.readiness,"NOT_TRADE_READY")
        cut=SEPT_START+141*THREE
        trunc=replace(src,as_of_ms=cut,original_3m_closed=src.original_3m_closed[:141])
        self.assertEqual(inspect_c30(src,as_of_ms=cut),inspect_c30(trunc,as_of_ms=cut))
    def test_forged_readiness_and_row_sha_tamper_refused(self):
        src=make3()
        with self.assertRaisesRegex(ValueError,"FORGED_READY"):
            inspect_c30(replace(src,readiness="READY"),as_of_ms=src.as_of_ms)
        rows=src.original_3m_closed
        altered=replace(src,original_3m_closed=rows[:103]+
            (replace(rows[103],raw_id="TAMPER"),)+rows[104:])
        with self.assertRaisesRegex(ValueError,"ALTERED_ORIGINAL_NATIVE3M_BAR"):
            inspect_c30(altered,as_of_ms=altered.as_of_ms)

if __name__=="__main__":unittest.main()
