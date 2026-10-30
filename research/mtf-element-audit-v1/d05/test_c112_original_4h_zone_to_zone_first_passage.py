"""C112 pre-source 20 negative tests for as-of first passage between 4H FVG.
Never change original C109 4H stop or claim a structural 'level' is a 'zone'.
"""
import sys,unittest
from pathlib import Path
from decimal import Decimal as D
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c112_zone_to_zone_fvg_destination_audit as f
import c109_simple_p4_core_vs_original_research as original
import c105_parent4h_structural_geometry as h4
from test_c105_parent4h_only_geometry import bar,fixtures,parent

def source_opp():
    tf=h4.H4
    four=(bar(0,tf,o="105",h="110",l="105",c="107"),
          bar(tf,tf,o="106",h="108",l="100",c="102"),
          bar(2*tf,tf,o="99",h="100",l="98",c="99"))
    rows=(NS(start_ms=3*tf,known_ms=3*tf+h4.THREE,low=D("97"),high=D("99")),)
    return four,rows,(3*tf,)

class C112(unittest.TestCase):
    def test_01_frozen_C109_original_signal_source(self):
        self.assertTrue(f.frozen())
    def test_02_precommit_two_64day_2024_crypto_windows(self):
        self.assertEqual(len(f.WINDOWS),2)
        self.assertEqual(f.WINDOWS[0][1].strftime("%Y-%m-%d"),"2024-07-01")
        self.assertEqual(f.WINDOWS[1][2].strftime("%Y-%m-%d"),"2024-12-04")
    def test_03_1536_original_daily_native3m_source(self):
        self.assertEqual((f.ZIPS,f.SOURCE_BARS),(1536,737280))
    def test_04_scoped_full_data_dates_restored_no_strategy_change(self):
        keys=f.FIELDS
        saved={k:getattr(original,k) for k in keys}
        with f.scoped(f.WINDOWS[0]):
            self.assertEqual(original.DAYS[0],"2024-07-01")
            self.assertEqual(original.DAYS[-1],"2024-09-02")
        self.assertEqual(saved,{k:getattr(original,k) for k in keys})
    def test_05_scoped_source_restored_on_exception(self):
        saved={k:getattr(original,k) for k in f.FIELDS}
        with self.assertRaisesRegex(RuntimeError,"test"):
            with f.scoped(f.WINDOWS[1]):raise RuntimeError("test")
        self.assertEqual(saved,{k:getattr(original,k) for k in f.FIELDS})
    def test_06_opposing_4h_short_fvg_known_asof_long_entry(self):
        four,rows,starts=source_opp()
        zone,counts=f.gap_candidates_at_entry("LONG",D("99"),
                             3*h4.H4+h4.THREE,four,rows,starts)
        self.assertIsNotNone(zone)
        self.assertEqual((zone["side"],zone["low"],zone["high"],zone["near"]),
                         ("SHORT","100","105","100"))
        self.assertEqual(zone["created_ms"],3*h4.H4)
        self.assertEqual(counts["fresh_opposing"],1)
    def test_07_opposite_fvg_not_known_before_third_H4_close(self):
        four,rows,starts=source_opp()
        zone,counts=f.gap_candidates_at_entry("LONG",D("99"),
                             3*h4.H4-1,four,rows,starts)
        self.assertIsNone(zone)
    def test_08_opposite_zone_wick_already_touched_is_not_fresh(self):
        four,rows,starts=source_opp()
        was=(NS(start_ms=rows[0].start_ms,known_ms=rows[0].known_ms,
                high=D("102"),low=D("99")),)
        x,_=f.gap_candidates_at_entry("LONG",D("99"),3*h4.H4+h4.THREE,
                         four,was,starts)
        self.assertIsNone(x)
    def test_09_opposite_zone_behind_entry_rejected(self):
        four,rows,starts=source_opp()
        x,_=f.gap_candidates_at_entry("LONG",D("100"),
                  3*h4.H4+h4.THREE,four,rows,starts)
        self.assertIsNone(x)
    def test_10_other_direction_parent_zone_not_selected(self):
        four,rows,starts=source_opp()
        x,_=f.gap_candidates_at_entry("SHORT",D("110"),
                   3*h4.H4+h4.THREE,four,rows,starts)
        self.assertIsNone(x)
    def test_11_invalid_source_side_blocked(self):
        four,rows,starts=source_opp()
        with self.assertRaisesRegex(f.C112Rejected,"INVALID_FVG_SOURCE_SIDE"):
            f.gap_candidates_at_entry("BUY",D("99"),3*h4.H4+h4.THREE,
                          four,rows,starts)
    def test_12_raw_opposite_near_edge_first_visit_from_original_intrabar(self):
        zone={"near":"100"}
        tf=h4.THREE
        bars=(NS(start_ms=0,known_ms=tf,high=D("99.9"),low=D("97")),
              NS(start_ms=tf,known_ms=2*tf,high=D("100.1"),low=D("98")))
        self.assertEqual(f.unconditioned_first_visit(bars,(0,tf),0,3*tf,zone,"LONG"),2*tf)
    def test_13_raw_no_opposing_zone_near_edge_visit(self):
        zone={"near":"102"}
        tf=h4.THREE
        bars=(NS(start_ms=0,known_ms=tf,high=D("101"),low=D("97")),)
        self.assertIsNone(f.unconditioned_first_visit(bars,(0,),0,3*tf,zone,"LONG"))
    def test_14_missing_known_opposing_zone_means_no_fvg_target(self):
        at,four,sw,rows,starts=fixtures()
        base={"entry":"100","stop":"97.4","side":"LONG","atr4h":"4","entry_ms":rows[0].start_ms}
        x,why=f.zone_alt_trade(base,None,rows,starts,four)
        self.assertIsNone(x);self.assertEqual(why,"NO_KNOWN_FRESH_OPPOSING_4H_FVG")
    def test_15_alternative_target_far_ahead_not_fixed_rr(self):
        at,four,sw,rows,starts=fixtures()
        base={"entry":"100","stop":"97.4","side":"LONG","atr4h":"4",
              "entry_ms":rows[0].start_ms,"zone_created_ms":at-h4.H4,
              "parent_id":"parent","symbol":"BNBUSDT",
              "stop_source":"4H_FVG_FAR_EDGE",
              "pad_source":"ATR_FULLY_CLOSED_4H","target":"119.4",
              "exit_reason":"TIME_OUT_48H","derived_rr":7.4,"fta":"120"}
        zone={"near":"110","id":"opposite","created_ms":at-h4.H4,
              "low":"110","high":"112"}
        alt,why=f.zone_alt_trade(base,zone,rows,starts,four)
        self.assertEqual(why,"OK")
        self.assertEqual(alt["target"],"109.40")
        self.assertEqual(alt["stop"],base["stop"])
        self.assertEqual(alt["entry"],base["entry"])
        self.assertEqual(alt["target_source_tf"],"4H")
        self.assertNotEqual(alt["derived_rr"],base["derived_rr"])
    def test_16_nearby_gap_does_not_override_rr_gate(self):
        at,four,sw,rows,starts=fixtures()
        base={"entry":"100","stop":"97.4","side":"LONG","atr4h":"4",
              "entry_ms":rows[0].start_ms}
        zone={"near":"101","id":"too-close","created_ms":at-h4.H4,
              "low":"101","high":"103"}
        z,reason=f.zone_alt_trade(base,zone,rows,starts,four)
        self.assertIsNone(z)
        self.assertEqual(reason,"FRESH_FVG_DESTINATION_DERIVED_RR_LT_1_25")
    def test_17_unmodified_4h_exit_boundaries(self):
        now,four,sw,rows,starts=fixtures()
        plan,why=h4.parent_plan(parent(),now,D("100"),four,sw,rows,starts)
        self.assertEqual(why,"OK")
        self.assertEqual((plan["stop_source_tf"],plan["target_source_tf"]),
                          ("4H","4H"))
    def test_18_no_preexisting_source_manifests_may_be_inferred(self):
        self.assertEqual(len(original.SYMBOLS),12)
        self.assertEqual(f.CORE_SHA,"39bf28a44cec0356b256853514c532b8f37be48f3da3477a365bd19c4add5557")
    def test_19_original_period_rejects_missing_provider_manifest(self):
        with self.assertRaisesRegex(f.C112Rejected,"REQUIRED_ORIGINAL_768"):
            f.evaluate(f.WINDOWS[0],{},[])
    def test_20_not_copied_luxalgo_or_live_execution(self):
        src=(Path(__file__).parent/"c112_zone_to_zone_fvg_destination_audit.py").read_text()
        self.assertNotIn("request.security(",src)
        self.assertNotIn("place_order(",src)
if __name__=="__main__":unittest.main()
