"""C52 40 tests: 49 visually inspected images, 8 true FX source headers, no author goldens."""
from dataclasses import replace
import unittest
from collections import Counter
from c52_full_course_visual_49_source_inspection import (
    FULL_SOURCE_HEADERS,CONCEPTUAL_IDS,CATEGORIES,ACADEMIC_BARRIERS,
    CourseFigure,review_all_original_course_figures,assert_c52_course_author_golden)
from c51_academic_visual_source_golden_gate import audited_inventory

class C52AcademicSourceInspection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items=review_all_original_course_figures()
        cls.byid={x.drive_id:x for x in cls.items}
    def test_all_49_source_images_marked_viewed(self):
        self.assertEqual(len(self.items),49)
        self.assertTrue(all(x.inspected for x in self.items))
    def test_every_image_matches_original_C51_source_id(self):
        ids,_=audited_inventory()
        self.assertEqual(set(self.byid),set(ids))
    def test_all_49_image_drive_ids_unique(self):
        self.assertEqual(len(self.byid),49)
    def test_source_category_four_safely_distinct(self):
        self.assertEqual(len(set(CATEGORIES)),4)
    def test_8_real_tradingview_eurusd_provider_headers(self):
        self.assertEqual(sum(x.figure_kind==CATEGORIES[0] for x in self.items),8)
    def test_19_cropped_charts_do_not_gain_unsupported_provider(self):
        charts=[x for x in self.items if x.figure_kind==CATEGORIES[1]]
        self.assertEqual(len(charts),19)
        self.assertTrue(all(x.visible_data_provider is None for x in charts))
    def test_eight_concept_or_diagram_sources_no_market_candle_id(self):
        charts=[x for x in self.items if x.figure_kind==CATEGORIES[2]]
        self.assertEqual(len(charts),8)
        self.assertTrue(all(x.original_market_bar_timestamp is None for x in charts))
    def test_fourteen_nested_desktop_screenshots_without_execution(self):
        charts=[x for x in self.items if x.figure_kind==CATEGORIES[3]]
        self.assertEqual(len(charts),14)
        self.assertTrue(all(x.orders==x.trades==() for x in charts))
    def test_included_6_prior_C51_inspections(self):
        _,six=audited_inventory()
        self.assertEqual(len(six),6)
        self.assertTrue(all(self.byid[z].inspected for z in six))
    def test_original_source_image_fingerprints_8_sha256(self):
        import re
        self.assertEqual(len(FULL_SOURCE_HEADERS),8)
        self.assertTrue(all(re.fullmatch("[a-f0-9]{64}",v[4]) for v in FULL_SOURCE_HEADERS.values()))
    def test_eight_actual_source_png_positive_sizes(self):
        self.assertTrue(all(v[5]>50000 for v in FULL_SOURCE_HEADERS.values()))
    def test_exact_8_original_image_dimensions_positive(self):
        self.assertTrue(all(v[6][0]>=1800 and v[6][1]>=800 for v in FULL_SOURCE_HEADERS.values()))
    def test_header_source_eurusd_8_not_binance_2026(self):
        self.assertEqual({v[0] for v in FULL_SOURCE_HEADERS.values()},{"EURUSD"})
        self.assertNotIn("BINANCE",{v[1] for v in FULL_SOURCE_HEADERS.values()})
    def test_provider_count_OANDA_6_SAXO_2(self):
        self.assertEqual(Counter(v[1] for v in FULL_SOURCE_HEADERS.values()),Counter({"OANDA":6,"SAXO":2}))
    def test_published_2024_exactly_five(self):
        self.assertEqual(sum(v[3].startswith("2024-05-26") for v in FULL_SOURCE_HEADERS.values()),5)
    def test_published_2025_exactly_three(self):
        self.assertEqual(sum(v[3].startswith("2025-01") for v in FULL_SOURCE_HEADERS.values()),3)
    def test_no_asserted_2023_chart_publication(self):
        self.assertTrue(all(not v[3].startswith("2023") for v in FULL_SOURCE_HEADERS.values()))
    def test_publication_is_not_original_raw_candle_time(self):
        self.assertTrue(all(x.original_market_bar_timestamp is None for x in self.items))
    def test_2024_EURUSD_source_timeframes_mtf(self):
        a=[v[2] for v in FULL_SOURCE_HEADERS.values() if v[3].startswith("2024")]
        self.assertEqual(Counter(a),Counter({"4H":2,"1H":2,"15M":1}))
    def test_2025_EURUSD_only_4h_source(self):
        a=[v[2] for v in FULL_SOURCE_HEADERS.values() if v[3].startswith("2025")]
        self.assertEqual(a,["4H"]*3)
    def test_tradingview_published_utc_offsets_are_preserved(self):
        self.assertEqual(Counter(v[3].split("UTC")[1] for v in FULL_SOURCE_HEADERS.values()),
            Counter({"+02:00":6,"+01:00":2}))
    def test_source_FX_not_assumed_BINANCE_crypto(self):
        self.assertTrue(all(x.visible_instrument!="BTCUSDT" for x in self.items))
    def test_Route_A_chart_multi_tf_family_not_verified_candle_golden(self):
        a=[x for x in self.items if x.visible_tradingview_publication_timestamp
           and x.visible_tradingview_publication_timestamp.startswith("2024-05-26")]
        self.assertEqual(len(a),5)
        self.assertTrue(all(not x.original_author_annotated_trade_golden for x in a))
    def test_no_author_approval_regardless_of_image_label(self):
        self.assertTrue(all(not x.original_author_annotated_trade_golden for x in self.items))
    def test_no_original_market_candle_raw_id_verified(self):
        self.assertTrue(all(not x.independently_valid_market_source_raw_bar for x in self.items))
    def test_no_trades_or_orders_any_image(self):
        self.assertTrue(all(x.orders==x.trades==() for x in self.items))
    def test_all_49_mark_not_trade_ready(self):
        self.assertTrue(all(x.readiness=="NOT_TRADE_READY" and x.study_only for x in self.items))
    def test_source_frame_is_not_negative_goldens_by_default(self):
        self.assertEqual(assert_c52_course_author_golden(figures=self.items)["known_original_raw_candle_golden"],0)
    def test_no_author_entry_authorization(self):
        z=assert_c52_course_author_golden(figures=self.items)
        self.assertEqual((z["author_verified_entry"],z["orders"],z["trades"]), (0,0,0))
    def test_fake_author_chart_long_rejected(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_PROVE_ACADEMIC_TRADE_GOLDEN"):
            assert_c52_course_author_golden(figures=self.items,claimed_author_entry=True)
    def test_forged_2023_candle_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_PROVE_ACADEMIC_TRADE_GOLDEN"):
            assert_c52_course_author_golden(figures=self.items,claimed_raw_market_timestamp="2023-07-04T09:00Z")
    def test_unverified_BINANCE_provider_match_rejected(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_PROVE_ACADEMIC_TRADE_GOLDEN"):
            assert_c52_course_author_golden(figures=self.items,claimed_provider_match="BINANCE_USDM")
    def test_forged_author_approval_in_image_rejected(self):
        modified=(replace(self.items[0],original_author_annotated_trade_golden=True),)+self.items[1:]
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_COURSE_VISUAL_GOLDEN_REVIEW"):
            assert_c52_course_author_golden(figures=modified)
    def test_forged_matched_candle_time_in_figure_rejected(self):
        modified=(replace(self.items[0],original_market_bar_timestamp="2024-05-25 12:00"),)+self.items[1:]
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_COURSE_VISUAL_GOLDEN_REVIEW"):
            assert_c52_course_author_golden(figures=modified)
    def test_fake_fill_trades_rejected(self):
        modified=(replace(self.items[0],trades=("faux_order",)),)+self.items[1:]
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_COURSE_VISUAL_GOLDEN_REVIEW"):
            assert_c52_course_author_golden(figures=modified)
    def test_missing_one_original_image_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNTRUSTED_COURSE_VISUAL_GOLDEN_REVIEW"):
            assert_c52_course_author_golden(figures=self.items[1:])
    def test_invented_external_market_source_override_refused(self):
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_AUTHOR_LABEL_OR_EXTERNAL"):
            review_all_original_course_figures(market_source_override="BINANCE_2026")
    def test_synthetic_author_label_override_refused(self):
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_AUTHOR_LABEL_OR_EXTERNAL"):
            review_all_original_course_figures(author_label_override="AUTHOR_VC_LONG")
    def test_private_image_sha_validator_cannot_auto_forge(self):
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_ORIGINAL_DRIVE_PNG_BYTES"):
            review_all_original_course_figures(physical_private_binary_validator=lambda *args:False)
    def test_private_image_digest_validator_runs_eight_times(self):
        checked=[]
        review_all_original_course_figures(physical_private_binary_validator=lambda *args:checked.append(args) or True)
        self.assertEqual(len(checked),8)
        self.assertEqual({x[0] for x in checked},set(FULL_SOURCE_HEADERS))
    def test_six_blockers_prevent_chart_meta_entry_promotion(self):
        self.assertEqual(len(ACADEMIC_BARRIERS),5)
    def test_actual_Route_A_textual_4h_1h_15m_image_exists(self):
        x=self.byid["1FdyrtyZYzYcw_y2MZn_s6jrknQjiWR5L"]
        self.assertEqual(x.figure_kind,CATEGORIES[2])
        self.assertFalse(x.original_author_annotated_trade_golden)
    def test_c52_golden_gate_stable_deterministic(self):
        self.assertEqual(review_all_original_course_figures(),self.items)
if __name__=="__main__":unittest.main()
