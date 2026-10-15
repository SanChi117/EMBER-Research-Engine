"""D05 C02 source-asset inventory guards (NOT a market pattern detector)."""
from __future__ import annotations
import json
import pathlib
import unittest
from collections import Counter

BASE=pathlib.Path(__file__).resolve().parent
def load(name):
    return json.loads((BASE/name).read_text(encoding="utf8"))

class SourceAssetInventoryC02(unittest.TestCase):
    def setUp(self):
        self.x=load("C02_SOURCE_IMAGE_INVENTORY.json")
        self.routes=load("C02_TDA_SOURCE_ROUTE_TOPOLOGY.json")
        self.assets={a["id"]:a for a in self.x["items"]}

    def test_8_folders_no_duplicate_ids(self):
        self.assertEqual(len(self.x["folders"]),8)
        self.assertEqual(len(self.assets),len(self.x["items"]))

    def test_manifest_totals_are_derived_not_assumed(self):
        metrics=self.x["metrics"]
        self.assertEqual(len(self.assets),metrics["all_entries"])
        images=[x for x in self.assets.values() if x["is_image"]]
        self.assertEqual(len(images),metrics["image_assets"])
        self.assertEqual(sum(x["entries"] for x in self.x["folders"]),len(self.assets))
        self.assertEqual(metrics["folders"],len(self.x["folders"]))

    def test_reviewed_files_sha_exact_format(self):
        import re
        observed=[x for x in self.assets.values() if x["is_image"] and x["sha256"]]
        self.assertEqual(len(observed),self.x["metrics"]["reviewed_images_with_sha256"])
        self.assertTrue(all(re.fullmatch("[0-9a-f]{64}",x["sha256"]) for x in observed))

    def test_no_unreviewed_source_can_have_sha_claim(self):
        for x in self.assets.values():
            if x["is_image"] and x["inspection_status"]=="NOT_VISUALLY_INSPECTED":
                self.assertIsNone(x["sha256"])

    def test_three_price_axis_examples_are_forex_not_futures(self):
        num=[x for x in self.assets.values() if x["inspection_status"]=="NUMERIC_FOREX_ACADEMIC_REFERENCE"]
        self.assertEqual(len(num),3)
        self.assertEqual(len(num),self.x["metrics"]["numeric_price_axis_forex_only"])
        self.assertTrue(all("EURUSD" in x["summary"] and "4H" in x["summary"] for x in num))
        self.assertEqual(self.x["metrics"]["independent_futures_semantic_cases_approved"],0)

    def test_all_course_screenshots_still_not_golden(self):
        old={x["drive_file_id"]:x for x in load("C01_VISUAL_CANDIDATES.json")["candidates"]}
        self.assertEqual(len(old),6)
        for itemid,x in old.items():
            self.assertEqual(self.assets[itemid]["sha256"],x["sha256"])
            self.assertEqual(self.assets[itemid]["inspection_status"],"PREVIOUS_C01_NONNUMERIC_SCREENSHOT")

    def test_tda_source_sha_matches_asset_record(self):
        image=self.assets[self.routes["source_image_drive_id"]]
        self.assertEqual(image["sha256"],self.routes["source_sha256"])
        self.assertEqual(image["inspection_status"],"COURSE_ROUTE_SCHEMATIC")

    def test_five_routes_are_unique_and_start_with_daily_context(self):
        paths=self.routes["paths"]
        self.assertEqual(len(paths),5)
        self.assertEqual({x["color"] for x in paths},{"ORANGE","GREEN","RED","BLUE","YELLOW"})
        self.assertEqual(len({tuple(p["steps"]) for p in paths}),5)
        self.assertTrue(all(p["steps"][0]=="DAILY_CONTEXT" for p in paths))
        self.assertTrue(all(len(p["steps"])>=4 for p in paths))

    def test_five_minute_vc_is_not_fifteen_minute_proxy(self):
        for p in self.routes["paths"]:
            has5="5M_VC_ENTRY" in p["steps"]
            self.assertEqual(p["entry_tf"],"5m" if has5 else "15m")
            self.assertEqual(p["steps"][-1],"5M_VC_ENTRY" if has5 else "15M_VC_ENTRY")
            if has5:self.assertIn("15M_LIQUIDITY_IMB_TRIGGER",p["steps"])

    def test_tda_paths_never_claim_bos_3m5m(self):
        for p in self.routes["paths"]:
            self.assertFalse(any("BOS" in s or s.startswith("3M_") for s in p["steps"]))
        self.assertFalse(self.routes["approvals"]["code_semantics_verified"])
        self.assertEqual(self.routes["approvals"]["numeric_automated_signals_approved"],0)

    def test_mutation_duplicate_route_is_caught(self):
        paths=self.routes["paths"][:]
        paths[1]={**paths[1],"steps":paths[0]["steps"]}
        self.assertNotEqual(len({tuple(x["steps"]) for x in paths}),5)

    def test_mutation_forex_source_promoted_false(self):
        forged=dict(self.x["metrics"])
        forged["independent_futures_semantic_cases_approved"]=3
        self.assertNotEqual(forged["independent_futures_semantic_cases_approved"],
                            self.x["metrics"]["independent_futures_semantic_cases_approved"])

if __name__=="__main__":
    unittest.main(verbosity=2)
