"""C51 30 negative tests: recovered chart images exist; none is author raw candle golden."""
import json,tempfile,unittest
from pathlib import Path
from c51_academic_visual_source_golden_gate import (
    INVENTORY,FOLDERS,BARRIERS,audited_inventory,
    observe_visual_candidate,reject_unverified_golden_promotion)
POI="1TkRlW9atcwqTjT6eS7xMOqqNzud_0qJh"
BOS="1DjAUNwDiNmr3a_ySSreSdtfBzVCWZPaZ"
UNSEEN="1_f_EEaMnRuTmBCx7fcrryM0w2OSpvU7k"
class C51OriginalOwnerCourseVisualInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.images,cls.seen=audited_inventory()
        cls.raw=json.loads(INVENTORY.read_text(encoding="utf8"))
    def bad(self,edit,pattern):
        obj=json.loads(json.dumps(self.raw))
        edit(obj)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bad.json"
            p.write_text(json.dumps(obj),encoding="utf8")
            with self.assertRaisesRegex(ValueError,pattern):audited_inventory(p)
    def test_seven_academic_direct_folders_accessed(self):
        self.assertEqual(len(FOLDERS),7)
    def test_exactly_49_found_png_images(self):
        self.assertEqual(len(self.images),49)
    def test_all_original_owner_drive_ids_unique(self):
        self.assertEqual(len(set(self.images)),49)
    def test_six_actual_images_visually_inspected(self):
        self.assertEqual(len(self.seen),6)
    def test_26_poi_images_grounded(self):
        self.assertEqual(sum(f=="POI" for f,_ in self.images.values()),26)
    def test_11_entry_model_images_grounded(self):
        self.assertEqual(sum(f=="ENTRY_MODEL_LOGIC" for f,_ in self.images.values()),11)
    def test_three_idm_entry_images_grounded(self):
        self.assertEqual(sum(f=="IDM_ENTRY" for f,_ in self.images.values()),3)
    def test_bos_entry_1_image_grounded(self):
        self.assertEqual(sum(f=="BOS_ENTRY" for f,_ in self.images.values()),1)
    def test_two_stronghl_images_grounded(self):
        self.assertEqual(sum(f=="STRONG_HIGH_LOW" for f,_ in self.images.values()),2)
    def test_two_idm_element_images_grounded(self):
        self.assertEqual(sum(f=="IDM_ELEMENT" for f,_ in self.images.values()),2)
    def test_four_liquidity_context_images_grounded(self):
        self.assertEqual(sum(f=="SESSION_LIQUIDITY_CONTEXT" for f,_ in self.images.values()),4)
    def test_real_bos_png_detected_not_author_golden(self):
        x=observe_visual_candidate(BOS)
        self.assertTrue(x.source_image_available and x.candidate.inspected)
        self.assertFalse(x.author_positive_golden or x.author_negative_golden)
    def test_real_poi_diagram_detected_not_trade_ready(self):
        x=observe_visual_candidate(POI)
        self.assertEqual((x.orders,x.trades,x.readiness),((),(),"NOT_TRADE_READY"))
    def test_uninspected_image_marked_explicitly(self):
        x=observe_visual_candidate(UNSEEN)
        self.assertFalse(x.candidate.inspected)
        self.assertIn("NOT_INDEPENDENTLY_VISUALLY_INSPECTED",x.candidate.visually_observed_type)
    def test_no_images_in_registry_are_author_goldens(self):
        for ident in self.images:
            x=observe_visual_candidate(ident)
            self.assertFalse(x.author_positive_golden or x.author_negative_golden)
            self.assertFalse(x.candidate.trade_ready)
            self.assertIsNone(x.matched_raw_candle_id)
    def test_each_source_keeps_all_six_goldens_blockers(self):
        self.assertEqual(len(BARRIERS),6)
        self.assertEqual(observe_visual_candidate(POI).blockers,BARRIERS)
    def test_unknown_image_source_cannot_promote(self):
        with self.assertRaisesRegex(ValueError,"IMAGE_NOT_IN_VERIFIED_OWNER"):
            observe_visual_candidate("NOT-A-REAL-COURSE-PNG-IMAGE")
    def test_metadata_cannot_claim_author_positive_label(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_BE_ATTESTED"):
            reject_unverified_golden_promotion(POI,proposed_author_label="AUTHOR_LONG")
    def test_metadata_cannot_claim_author_negative_label(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_BE_ATTESTED"):
            reject_unverified_golden_promotion(BOS,proposed_author_label="INVALID_TRADE")
    def test_metadata_cannot_claim_original_2023_candle(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_BE_ATTESTED"):
            reject_unverified_golden_promotion(POI,proposed_author_label=None,
                proposed_original_chart_year=2023)
    def test_metadata_cannot_claim_forged_raw_candle_id(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_BE_ATTESTED"):
            reject_unverified_golden_promotion(POI,proposed_author_label=None,
                proposed_raw_candle_id="example:1672531200000")
    def test_source_only_no_claim_returns_unapproved_gate(self):
        z=reject_unverified_golden_promotion(POI,proposed_author_label=None)
        self.assertFalse(z.author_positive_golden or z.author_negative_golden)
        self.assertEqual(z.readiness,"NOT_TRADE_READY")
    def test_inventory_forged_author_approved_count_refused(self):
        self.bad(lambda x:x.update(confirmed_author_candle_goldens=1),"UNTRUSTED_VISUAL_AUTHOR")
    def test_inventory_forged_trade_refused(self):
        self.bad(lambda x:x.update(trades=1),"UNTRUSTED_VISUAL_AUTHOR")
    def test_inventory_claim_entire_course_found_refused(self):
        self.bad(lambda x:x.update(coverage="ALL_COURSE_IMAGERY_FOUND"),"UNTRUSTED_VISUAL_AUTHOR")
    def test_49_count_drift_refused(self):
        self.bad(lambda x:x.update(unique_direct_image_png_count=48),"UNTRUSTED_VISUAL_AUTHOR")
    def test_forged_public_image_binary_copy_refused(self):
        self.bad(lambda x:x.update(image_binary_copied_to_public_repository=True),"UNTRUSTED_VISUAL_AUTHOR")
    def test_duplicate_source_image_id_refused(self):
        self.bad(lambda x:x["folder_inventories"][1]["files"].__setitem__(
            0,dict(x["folder_inventories"][0]["files"][0])),"INVALID_OR_DUPLICATED")
    def test_unsupported_nonpng_mime_refused(self):
        self.bad(lambda x:x["folder_inventories"][0]["files"][0].update(mime_type="text/plain"),"INVALID_OR_DUPLICATED")
    def test_invented_gdrive_file_url_refused(self):
        self.bad(lambda x:x["folder_inventories"][0]["files"][0].update(drive_url="https://evil.example/file"),"INVALID_OR_DUPLICATED")
    def test_missing_real_course_folder_refused(self):
        self.bad(lambda x:x["folder_inventories"].pop(),"IMAGE_COUNT_OR_FOLDER")
    def test_wrong_course_folder_id_refused(self):
        self.bad(lambda x:x["folder_inventories"][0].update(folder_id="WRONG"),"UNTRUSTED_IMAGE_SOURCE_FOLDER")
    def test_sample_falsely_author_verified_rejected(self):
        self.bad(lambda x:x["inspected_samples"][0].update(
            author_annotated_raw_candle_golden_verified=True),"FORGED_VISUAL_INSPECTION")
    def test_fabricated_seventh_inspected_sample_refused(self):
        self.bad(lambda x:x["inspected_samples"].append(dict(x["inspected_samples"][0])),
            "FORGED_VISUAL_INSPECTION")
    def test_deleted_inspected_sample_rejected(self):
        self.bad(lambda x:x["inspected_samples"].pop(),"INSPECTED_SOURCE_SAMPLE_DRIFT")
    def test_untested_course_target_is_not_zero_screenshot_claim(self):
        self.assertEqual(self.raw["coverage"],"SEVEN_GROUNDED_FOLDERS_ONLY_NOT_PROOF_ENTIRE_COURSE_ARCHIVED")
        self.assertEqual(self.raw["confirmed_original_market_source_chart_bindings"],0)
if __name__=="__main__":unittest.main()
