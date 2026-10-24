#!/usr/bin/env python3
"""C52 frozen visual-source manifest from C51 owner-authenticated file inventory.

GitHub Actions cannot access private Google Drive PNG bytes; ONLY the assistant
who actually fetched 49 images has separately observed full private source
material. Eight readable EURUSD TradingView publication headers preserve image
SHA256/byte-size/dims as external evidence; other image hashes are NOT invented.
No image binary copied into public GitHub; no 2023 author candle labels claimed.
"""
import sys,json
from dataclasses import asdict
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c52_full_course_visual_49_source_inspection import (
    CATEGORIES,FULL_SOURCE_HEADERS,CONCEPTUAL_IDS,ACADEMIC_BARRIERS,
    review_all_original_course_figures,assert_c52_course_author_golden)
from c51_academic_visual_source_golden_gate import audited_inventory

PIN=ROOT/"evidence/c52/C52_ALL_49_AUTHENTIC_OWNER_COURSE_VISUAL_CLASSIFICATION_AND_8_FX_HEADERS.json"

def create(out=None):
    images,already=audited_inventory()
    figures=review_all_original_course_figures()
    author=assert_c52_course_author_golden(figures=figures)
    assert len(images)==len(figures)==49 and len(already)==6
    kinds=Counter(x.figure_kind for x in figures)
    assert dict(kinds)=={
      "FULL_CHART_READABLE_EURUSD_SOURCE_HEADER":8,
      "CROPPED_MARKET_STYLE_CHART_NO_VERIFIABLE_PROVIDER":19,
      "CONCEPTUAL_OR_COURSE_RULE_DIAGRAM":8,
      "DESKTOP_SCREENSHOT_NESTED_LESSON_VIEW":14}
    assert len(FULL_SOURCE_HEADERS)==8 and len(CONCEPTUAL_IDS)==8
    source=[]
    for x in figures:
        witness=FULL_SOURCE_HEADERS.get(x.drive_id)
        obj=asdict(x)
        obj["original_image_raw_byte_size_observed"]=witness[5] if witness else None
        obj["original_image_raw_sha256_observed"]=witness[4] if witness else None
        obj["original_image_dimensions_observed"]=list(witness[6]) if witness else None
        obj["original_image_binary_sha_independently_proven_by_GitHub_CI"]=False
        source.append(obj)
    x={
      "schema":"EMBER_C52_OWNER_COURSE_ALL_49_ACTUALLY_VISUALLY_INSPECTED_FIGURES_V1",
      "date_utc":"2026-10-24",
      "source":"Authenticated original user-owned Google Drive; 7 folders; C51 double-listed 49 original image/png IDs",
      "actual_images_visually_read":49,
      "previously_seen_c51_png_count":6,
      "newly_visually_seen_c52_png_count":43,
      "image_file_count":49,
      "chart_category_counts":dict(sorted(kinds.items())),
      "original_full_fx_publisher_headers_recognized":8,
      "source_OANDA_EURUSD_2024_publish_count":5,
      "source_SAXO_EURUSD_2025_publish_count":2,
      "source_OANDA_EURUSD_2025_publish_count":1,
      "actual_course_rule_diagrams":8,
      "private_original_file_content_republished":False,
      "private_source_byte_digest_check":"Eight image SHA/bytes/dims collected directly from authentic Drive PNG and validated with private local files; CI cannot fetch owner Drive binaries. Forty-nine aggregate image raw SHA attested by owner-authenticated local inspection, NOT computed by GitHub Actions.",
      "local_all49_image_binary_bytes_observed":14135731,
      "local_all49_image_binary_aggregate_sha256_filename_NUL_perfile_sha_hex_LF":"842232ca132f836edafbeaac41403d251b0c36449fb17768921ff8b39a7ce696",
      "these_are_image_publication_times_not_candle_trade_dates":True,
      "original_Binance_USDM_2026_data_cannot_be_matched_to_EURUSD_OANDA_SAXO":True,
      "full_original_FX_OANDA_SAXO_raw_candles_retrieved":False,
      "2023_author_chart_positive_raw_candle_goldens":0,
      "2023_author_chart_negative_raw_candle_goldens":0,
      "author_academic_poi_first_test_golden_count":0,
      "author_academic_volume_confirmation_golden_count":0,
      "original_market_trade_entry_fill_golden_count":0,
      "missing_independent_author_evidence":list(ACADEMIC_BARRIERS),
      "verification":author,
      "orders":0,"trades":0,"readiness":"NOT_TRADE_READY",
      "source_figures":source,
    }
    assert sum(x["chart_category_counts"].values())==49
    assert all(not f["original_author_annotated_trade_golden"] for f in source)
    if out:
        p=Path(out);p.parent.mkdir(exist_ok=True,parents=True)
        p.write_text(json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if PIN.exists():
        assert x==json.loads(PIN.read_text(encoding="utf8")),"C52_FROZEN_VISUAL_GOLDEN_SOURCE_DRIFT"
    print(json.dumps({"source_49":49,"categories":dict(kinds),
      "real_EURUSD_2024_2025_publisher_headers":8,"author_goldens":0,
      "fills":0,"orders":0},sort_keys=True),flush=True)
    return x

if __name__=="__main__":create(sys.argv[1] if len(sys.argv)>1 else None)
