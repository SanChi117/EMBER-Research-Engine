"""C107 diagnostics only: negative tests proving mismatch and freezing both prior model witnesses."""
import sys,hashlib,unittest
from pathlib import Path
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c107_original_p4_false_signal_forensics as f
import c105_parent4h_structural_geometry as p4
from c91_continuous_causal_route_a_paper import _fvg,_vc
from test_c105_parent4h_only_geometry import bar

class C107RootCauseTests(unittest.TestCase):
    def bad(self,fn,label):
        with self.assertRaisesRegex(f.C107Error,label):fn()
    def test_01_original_41_two_witnesses_unchanged(self):
        z=f.frozen();self.assertEqual((len(z["C105"]["trades"]),len(z["C106"]["trades"])),(25,16))
    def test_02_prior_4h_parent_screens_both_trade_cohorts(self):
        z=f.frozen()
        self.assertTrue(all(t["stop_source_tf"]==t["target_source_tf"]=="4H"
                for k in z for t in z[k]["trades"]))
    def test_03_exact_stop_4h_close_equal_far_edge_is_not_invalidated(self):
        self.assertFalse(f.parent_invalidated_by_closed4("LONG",D("98"),D("98"),D("99")))
        self.assertFalse(f.parent_invalidated_by_closed4("SHORT",D("99"),D("98"),D("99")))
    def test_04_stop_wick_below_but_4h_close_recovered_long(self):
        # Stop 97.8 touched by native3m wick low=97, but closed H4=98.4 > FVG far=98
        self.assertFalse(f.parent_invalidated_by_closed4("LONG",D("98.4"),D("98"),D("99")))
    def test_05_stop_wick_above_but_4h_close_recovered_short(self):
        # Stop 99.2 touched by 3m wick=100, but 4H close=98.5 within gap
        self.assertFalse(f.parent_invalidated_by_closed4("SHORT",D("98.5"),D("98"),D("99")))
    def test_06_true_4h_long_invalidated_only_on_h4_close(self):
        self.assertTrue(f.parent_invalidated_by_closed4("LONG",D("97.9"),D("98"),D("99")))
    def test_07_true_4h_short_invalidated_only_on_h4_close(self):
        self.assertTrue(f.parent_invalidated_by_closed4("SHORT",D("99.1"),D("98"),D("99")))
    def test_08_invalid_side_no_h4_fallback(self):
        self.bad(lambda:f.parent_invalidated_by_closed4("BUY",D("98"),D("98"),D("99")),"UNREGISTERED_4H")
    def test_09_bad_zone_type_rejected(self):
        self.bad(lambda:f.parent_invalidated_by_closed4("LONG",98,D("98"),D("99")),"INVALID_4H")
    def test_10_4h_fvg_accepted_without_middle_impulse(self):
        tf=p4.H4
        # LONG FVG geometry; middle is bearish. Exactly the original C91 _fvg.
        a=bar(0,tf,o="97",h="100",l="96",c="99")
        mid=bar(tf,tf,o="102",h="105",l="99",c="101")
        z=bar(2*tf,tf,o="104",h="107",l="103",c="106")
        self.assertEqual(_fvg((a,mid,z)),("LONG",D("100"),D("103")))
        self.assertFalse(f.fvg_middle_momentum("LONG",mid))
    def test_11_4h_short_fvg_accepted_without_middle_impulse(self):
        tf=p4.H4
        a=bar(0,tf,o="108",h="110",l="106",c="107")
        mid=bar(tf,tf,o="101",h="110",l="100",c="105")
        z=bar(2*tf,tf,o="99",h="102",l="98",c="100")
        self.assertEqual(_fvg((a,mid,z)),("SHORT",D("102"),D("106")))
        self.assertFalse(f.fvg_middle_momentum("SHORT",mid))
    def test_12_15m_snr_break_previous_single_candle_not_structural_swing(self):
        tf=p4.M15
        x=(bar(0,tf,o="100",h="115",l="98",c="102"),
           bar(tf,tf,o="102",h="110",l="100",c="104"),
           bar(2*tf,tf,o="104",h="109",l="100",c="108"),
           bar(3*tf,tf,o="108",h="111",l="107",c="110"))
        # Close 110 > previous candle high 109, but < older 115 or 110.
        self.assertEqual(_vc(x,"LONG"),"SNR")
        self.assertLess(x[-1].c,x[0].h)
    def test_13_first_touch_c105_any_edge_intersection(self):
        z=p4.Parent("LONG",D("98"),D("99"),0,"synthetic")
        self.assertTrue(p4.first_touch(z,bar(p4.M15,p4.M15,o="100",h="101",l="99",c="100")))
    def test_14_h1_rejection_can_close_inside_parent_fvg(self):
        z=p4.Parent("LONG",D("98"),D("99"),0,"synthetic",
                 first_touch_ms=p4.H,state="WAIT_1H_REJECTION")
        candle=bar(p4.H,p4.H,o="98.3",h="99.5",l="98.1",c="98.7")
        self.assertTrue(p4.rejection(z,candle))
        self.assertLess(candle.c,z.upper)
    def test_15_exact_closed4_alignment_stop_between_4h_boundaries(self):
        self.assertEqual(f.ceil_closed4(p4.H4+3*p4.THREE),2*p4.H4)
    def test_16_stop_at_4h_close_is_same_close(self):
        self.assertEqual(f.ceil_closed4(2*p4.H4),2*p4.H4)
    def test_17_bad_source_timestamp_rejected(self):
        self.bad(lambda:f.ceil_closed4(-1),"INVALID_SOURCE_TIMESTAMP")
    def test_18_frozen_crypto_research_nonzero_original_4h_RR(self):
        z=f.frozen()
        self.assertTrue(all(t["derived_rr"]>=1.25 for k in z for t in z[k]["trades"]))
    def test_19_original_c105_engine_sources_immutable(self):
        import c106_parent4h_semantic_transfer as c106
        c106.check_frozen()
    def test_20_never_promote_paper_to_live(self):
        z=f.frozen()
        self.assertTrue(all(not z[k]["admission"]["live_approved"] for k in z))
if __name__=="__main__":unittest.main()
