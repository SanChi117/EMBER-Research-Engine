"""C110 10 before-market-source proofs: C109 engine byte unchanged, only dates scoped."""
import unittest,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c110_blind_unchanged_c109_second_regime as x
import c109_simple_p4_core_vs_original_research as core
import c105_parent4h_structural_geometry as p4

class C110Tests(unittest.TestCase):
    def test_01_original_c109_core_sha_pinned(self):
        self.assertTrue(x.source_code_verified())
    def test_02_new_calendar_64_unseen_historical_days(self):
        self.assertEqual((len(x.NEW_DAYS),x.NEW_DAYS[0],x.NEW_DAYS[-1]),
                         (64,"2025-11-01","2026-01-03"))
    def test_03_unchanged_symbols_in_12_coins(self):
        self.assertEqual(len(core.SYMBOLS),12)
        self.assertEqual((core.ZIPS,core.BARS_PER_SYMBOL),(768,30720))
    def test_04_same_4h_stop_and_fta_source(self):
        self.assertEqual((p4.PAD,p4.MIN_RR),(core.D("0.15"),core.D("1.25")))
        self.assertEqual(p4.BPS,(14,25,40))
    def test_05_change_only_source_clock_no_strategy_constants(self):
        unchanged=(core.BEGIN_MS,core.END_MS,core.DAYS,core.FOLD_MS,core.BPS if hasattr(core,"BPS") else core.p4.BPS)
        with x.use_frozen_second_regime():
            self.assertEqual(core.DAYS[0],"2025-11-01")
            self.assertEqual(core.DAYS[-1],"2026-01-03")
            self.assertEqual((core.ZIPS,core.BARS_PER_SYMBOL),(768,30720))
            self.assertEqual(core.p4.BPS,(14,25,40))
            self.assertEqual(set(core.ARMS),{core.ARM_BASE,core.ARM_CORE})
            self.assertLess(core.WARMUP_END,core.FOLD_MS)
            self.assertLess(core.FOLD_MS,core.LAST_ENTRY)
        self.assertEqual((core.BEGIN_MS,core.END_MS,core.DAYS,core.FOLD_MS,core.p4.BPS),unchanged)
    def test_06_clock_scope_restore_after_error(self):
        previous={key:getattr(core,key) for key in x.CAL_FIELDS}
        with self.assertRaisesRegex(RuntimeError,"synthetic"):
            with x.use_frozen_second_regime():
                raise RuntimeError("synthetic")
        self.assertEqual({key:getattr(core,key) for key in x.CAL_FIELDS},previous)
    def test_07_earlier_second_period_not_original_C109_window(self):
        self.assertLess(x.SOURCE_END,core.BEGIN)
    def test_08_old_41_paper_original_witness_shas_frozen(self):
        import c107_original_p4_false_signal_forensics as c107
        z=c107.frozen()
        self.assertEqual((len(z["C105"]["trades"]),len(z["C106"]["trades"])),(25,16))
    def test_09_original_C109_baseline_vs_core_no_hidden_third_arm(self):
        self.assertEqual(len(core.ARMS),2)
        self.assertTrue(core.ARM_BASE.startswith("B0_"))
        self.assertTrue(core.ARM_CORE.startswith("B1_"))
    def test_10_no_live_transport_in_second_calendar_wrapper(self):
        src=(Path(__file__).parent/"c110_blind_unchanged_c109_second_regime.py").read_text()
        self.assertNotIn("place_order(",src)
        self.assertIn("can_approve_live",src)
if __name__=="__main__":unittest.main()
