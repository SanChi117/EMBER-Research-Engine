"""D05 C03: complete-source provenance and fail-closed semantic assertions; not trade tests."""
from __future__ import annotations
import json, pathlib, re, unittest
from collections import Counter
BASE=pathlib.Path(__file__).resolve().parent
def read(name):
    return json.loads((BASE/name).read_text(encoding="utf8"))
class FullImageSourceReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=read("C02_SOURCE_IMAGE_INVENTORY.json")
        cls.after=read("C03_58_IMAGE_REVIEW.json")
        cls.new=cls.after["items"]
        cls.old={x["id"]:x for x in cls.before["items"] if x["is_image"] and x["inspection_status"]=="NOT_VISUALLY_INSPECTED"}
    def test_all_58_no_missing_or_duplicate(self):
        self.assertEqual(len(self.new),58)
        self.assertEqual(len({x["source_id"] for x in self.new}),58)
        self.assertEqual(set(x["source_id"] for x in self.new),set(self.old))
    def test_all_sha_are_64_hex(self):
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}",x["sha256"]) for x in self.new))
    def test_source_metadata_no_mismatch(self):
        for x in self.new:
            old=self.old[x["source_id"]]
            self.assertEqual(x["source_file"],old["name"])
            self.assertEqual(x["bytes"],old["size_bytes"])
            self.assertEqual(x["course_folder"],old["section"])
            self.assertIn(x["source_id"],x["drive_uri"])
    def test_counts_exact_from_records(self):
        counts=dict(Counter(x["classification"] for x in self.new))
        self.assertEqual(counts,self.after["class_counts"])
        self.assertEqual(sum(counts.values()),58)
    def test_all_72_complete_but_zero_approved(self):
        self.assertEqual(self.after["previous_reviewed_images"],14)
        self.assertEqual(self.after["new_reviewed_images"],58)
        self.assertEqual(self.after["all_reviewed_images"],72)
        self.assertEqual(self.after["unreviewed_images"],0)
        self.assertEqual(self.after["approved_academic_futures_cases"],0)
        self.assertTrue(all(x["independently_approved"] is False for x in self.new))
    def test_new_numeric_charts_are_forex_only(self):
        found=[x for x in self.new if x["classification"]=="FOREX_PRICE_SCALED_NEEDS_REPLAY"]
        self.assertEqual(len(found),3)
        self.assertEqual({x["tf"] for x in found},{"1w","1d","1h"})
        self.assertTrue(all(x["symbol"]=="EURUSD" and x["venue"]=="OANDA" for x in found))
    def test_unattributed_price_chart_cannot_trade(self):
        found=[x for x in self.new if x["classification"]=="PRICE_AXIS_MARKET_TF_UNKNOWN"]
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]["source_file"],"Untitled (10).png")
        self.assertIsNone(found[0]["tf"])
        self.assertIsNone(found[0]["symbol"])
    def test_other_images_have_no_fake_market_identity(self):
        for x in self.new:
            if x["classification"]!="FOREX_PRICE_SCALED_NEEDS_REPLAY":
                self.assertIsNone(x["venue"])
                self.assertIsNone(x["symbol"])
                self.assertIsNone(x["tf"])
    def test_d01d04_semantics_remain_unaffected(self):
        self.assertEqual(self.after["status"],"SOURCE_ASSETS_REVIEWED_NO_ACADEMIC_SIGNOFF")
        self.assertTrue(all(x["semantic_status"]=="NEEDS_INDEPENDENT_SOURCE_REPLAY" for x in self.new))
    def test_prohibits_undeclared_numeric_futures_label(self):
        self.assertFalse(any(x["classification"]=="BINANCE_FUTURES_GOLDEN_APPROVED" for x in self.new))
        self.assertEqual(self.after["numeric_forex_total"],6)
    def test_mutation_source_omission_detected(self):
        ids={x["source_id"] for x in self.new[:-1]}
        self.assertNotEqual(ids,set(self.old))
    def test_mutation_forged_sha_detected(self):
        x=dict(self.new[0],sha256="x"*64)
        self.assertIsNone(re.fullmatch(r"[0-9a-f]{64}",x["sha256"]))
    def test_mutation_false_approval_detected(self):
        altered=[{**x,**({"independently_approved":True} if i==0 else {})} for i,x in enumerate(self.new)]
        self.assertFalse(all(x["independently_approved"] is False for x in altered))
if __name__=="__main__":
    unittest.main(verbosity=2)
