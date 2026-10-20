"""C36 academic core locked while research adapted modules are replaced."""
import copy
import unittest
from c36_adapted_slot_registry import (
    ACADEMIC_CORE_REFERENCE,ACADEMIC_CORE_ID,FROZEN_C33_SHA,
    VARIANTS,SLOTS,create_research_assembly,slot_manifest)

class ResearchSlotIsolation(unittest.TestCase):
    def test_academic_core_identity_is_stable(self):
        self.assertEqual(len(ACADEMIC_CORE_ID),64)
        self.assertIn("READ_ONLY",ACADEMIC_CORE_REFERENCE["academic_original_evidence"])
    def test_manifest_does_not_say_author_ready(self):
        m=slot_manifest()
        self.assertEqual(m["readiness"],"NOT_TRADE_READY")
        self.assertEqual(m["author_goldens"],0)
        self.assertEqual(m["orders"],0)
        self.assertEqual(m["trades"],0)
    def test_original_45_zip_C33_source_sha_is_locked(self):
        self.assertEqual(slot_manifest()["academic_core"]["snapshot_git_blob_C33"],FROZEN_C33_SHA)
    def test_every_registered_BOS_variant_creates_source_only_assembly(self):
        for v in VARIANTS:
            with self.subTest(v=v):
                x=create_research_assembly({"BOS_PIVOT":v})
                self.assertEqual(x.adapted_selection,(("BOS_PIVOT",v),))
                self.assertFalse(x.technical_backtest_ready)
    def test_latest_registered_is_not_author_bos(self):
        x=create_research_assembly({"BOS_PIVOT":"LATEST_CONFIRMED_V1"})
        self.assertFalse(x.author_method_reproduced)
    def test_first_registered_is_not_author_bos(self):
        x=create_research_assembly({"BOS_PIVOT":"EARLIEST_CONFIRMED_V1"})
        self.assertFalse(x.author_method_reproduced)
    def test_empty_assembly_remains_incomplete(self):
        x=create_research_assembly({})
        self.assertTrue(x.unresolved_slots)
        self.assertEqual(x.adapted_selection,())
    def test_adapted_BOS_cannot_activate_fully_blocked_reaction(self):
        x=create_research_assembly({"BOS_PIVOT":VARIANTS[0]})
        self.assertIn("REACTION",x.unresolved_slots)
    def test_adapted_BOS_cannot_activate_FTA_or_stop(self):
        x=create_research_assembly({"BOS_PIVOT":VARIANTS[0]})
        self.assertIn("FIRST_TROUBLE_AREA",x.unresolved_slots)
        self.assertIn("STOP_TARGET",x.unresolved_slots)
    def test_reject_forged_core_id(self):
        with self.assertRaisesRegex(ValueError,"ACADEMIC_CORE_OR_SOURCE"):
            create_research_assembly({},core_id="fake")
    def test_reject_wrong_source_blob(self):
        with self.assertRaisesRegex(ValueError,"ACADEMIC_CORE_OR_SOURCE"):
            create_research_assembly({},original_c33_git_blob="f"*40)
    def test_reject_core_raid_replacement(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_REPLACE_ACADEMIC_CORE"):
            create_research_assembly({"RAID_1H":"FAST_RAID"})
    def test_reject_entry_order_route_in_adapted_slots(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_REPLACE_ACADEMIC_CORE"):
            create_research_assembly({"ENTRY":"LIVE_MARKET_AT_CROSS"})
    def test_reject_unvalidated_reaction_variant(self):
        with self.assertRaisesRegex(ValueError,"UNREGISTERED_OR_UNTESTED"):
            create_research_assembly({"REACTION":"ANY_REACTION"})
    def test_reject_unvalidated_FTA_route(self):
        with self.assertRaisesRegex(ValueError,"UNREGISTERED_OR_UNTESTED"):
            create_research_assembly({"FIRST_TROUBLE_AREA":"NEAREST_IMB"})
    def test_reject_unvalidated_SL_route(self):
        with self.assertRaisesRegex(ValueError,"UNREGISTERED_OR_UNTESTED"):
            create_research_assembly({"STOP_TARGET":"ATR_3X"})
    def test_reject_unregistered_BOS_variant(self):
        with self.assertRaisesRegex(ValueError,"UNREGISTERED_OR_UNTESTED"):
            create_research_assembly({"BOS_PIVOT":"HIGHEST_BACKTEST_PROFIT"})
    def test_reject_unknown_slot(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_SLOT"):
            create_research_assembly({"REAL_BINANCE_EXECUTION":"ON"})
    def test_reject_forged_non_dict_selection(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_ADAPTED_SELECTION"):
            create_research_assembly([("BOS_PIVOT","LATEST_CONFIRMED_V1")])
    def test_all_orders_and_backtests_explicitly_empty(self):
        for v in VARIANTS:
            x=create_research_assembly({"BOS_PIVOT":v})
            self.assertFalse(x.paper_order_placement_allowed)
            self.assertFalse(x.real_order_placement_allowed)
            self.assertEqual((x.orders,x.trades,x.optimized_parameters,x.backtest_results),((),(),(),()))
            self.assertEqual(x.readiness,"NOT_TRADE_READY")
    def test_manifest_holdout_not_still_pristine(self):
        m=slot_manifest()
        self.assertIn("NOT a pristine performance holdout",m["holdout_caution"])
    def test_registry_is_read_only_to_callers(self):
        snapshot=copy.deepcopy(slot_manifest())
        snapshot["registered_slots"]["BOS_PIVOT"]["variants"].append("FORGED_VARIANT")
        self.assertNotIn("FORGED_VARIANT",slot_manifest()["registered_slots"]["BOS_PIVOT"]["variants"])
    def test_registry_has_no_hidden_pnl_metrics(self):
        m=slot_manifest()
        self.assertEqual(m["optimization_status"],"NOT_STARTED_NO_PROFIT_TARGET_OBJECTIVE")
        self.assertEqual(m["real_execution_status"],"FORBIDDEN")
if __name__=="__main__":unittest.main()
