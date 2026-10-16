#!/usr/bin/env python3
"""B1/C11: 5-symbol, two-day real source 1h raid→5m IMB→first-price-test candidates.

Original Binance USD-M 5m ZIP and CSV checked against immutable F06 receipts.
The independent C08 15m parity was previously verified in F06, unchanged.
This is NOT author-validated StrongHL or terminal VC entry, never an order.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from f03_5m_original_source import download_source_5m,DAY
from c11_contact_imb_source_witness import inspect_contact_then_5m_imb

RECEIPT=ROOT/"evidence"/"f06"/"F06_FIVE_SYMBOL_TWO_DAY_5M_SOURCE_RECEIPTS.json"
DATE_TO_START={"2026-10-01":1790812800000,"2026-10-02":1790899200000}

def main(dest=None):
    proof=json.loads(RECEIPT.read_text(encoding="utf8"))
    assert proof["schema"]=="EMBER_B1_C10_TWO_CONSECUTIVE_DAYS_FIVE_SYMBOL_ORIGINAL_5M_RECEIPTS_V1"
    assert proof["academy_entry_approved"]==0 and proof["readiness"]=="NOT_TRADE_READY"
    rows=[]
    for symbol in proof["symbols"]:
        days=[]
        for date in proof["dates"]:
            expected=next(x for x in proof["source_days"] if x["symbol"]==symbol and x["date"]==date)
            url=f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/5m/{symbol}-5m-{date}.zip"
            five=download_source_5m(url)
            assert five.symbol==symbol and five.day_start_ms==DATE_TO_START[date]
            assert five.zip_sha256==expected["original_5m_zip_sha256"]
            assert five.raw_csv_sha256==expected["original_5m_csv_sha256"]
            assert len(five.rows)==288
            days.append(five)
        first=inspect_contact_then_5m_imb(days[0],days[1],DATE_TO_START["2026-10-02"])
        full=inspect_contact_then_5m_imb(days[0],days[1],DATE_TO_START["2026-10-02"]+DAY)
        assert first.closed_5m_count==288 and full.closed_5m_count==576
        assert first.closed_1h_count==24 and full.closed_1h_count==48
        assert first.readiness=="NOT_TRADE_READY" and full.readiness=="NOT_TRADE_READY"
        assert all(w.confirmation_known_ms> w.contact_known_ms and
                   w.confirmation_known_ms<=full.as_of_ms and
                   w.academic_status=="STRONGHL_AND_VC_NOT_AUTHOR_CERTIFIED"
                   for w in full.paired_source_price_witnesses)
        rows.append({
            "symbol":symbol,
            "closed_5m_bars":full.closed_5m_count,
            "source_1h_raid_candidates":full.raid_contact_candidates,
            "raid_then_5m_imb_time_and_geometry_pairs":full.post_raid_5m_imb_candidates,
            "with_later_5m_poi_price_touch":sum(
                w.first_later_poi_test_known_ms is not None for w in full.paired_source_price_witnesses),
            "without_later_touch":sum(
                w.first_later_poi_test_known_ms is None for w in full.paired_source_price_witnesses),
            "first_price_witness":({
                "contact_raid_uid":full.paired_source_price_witnesses[0].contact_1h_raid_uid,
                "contact_known_ms":full.paired_source_price_witnesses[0].contact_known_ms,
                "contact_5m_source_id":full.paired_source_price_witnesses[0].contact_source_5m_id,
                "imb_uid":full.paired_source_price_witnesses[0].confirmation_5m_imb_uid,
                "imb_known_ms":full.paired_source_price_witnesses[0].confirmation_known_ms,
                "imb_raw_5m_source_id":full.paired_source_price_witnesses[0].confirmation_source_5m_id,
                "later_test_source_id":full.paired_source_price_witnesses[0].first_later_poi_test_source_id,
            } if full.paired_source_price_witnesses else None),
            "source_verified":"PINNED_F06_BINANCE_5M_ZIP_AND_CSV_SHA",
            "stronghl_vc_semantics":"UNAPPROVED_NOT_AUTHOR_VERIFIED",
            "trade_ready":False,
        })
    doc={
        "cycle":"B1_C11_ORIGINAL_F06_CONTACT_IMB_PRICE_WITNESSES",
        "symbols":proof["symbols"],"days":proof["dates"],
        "source_market":"BINANCE_USDM_FUTURES",
        "original_5m_zip_sources":10,
        "verified_raw_closed_5m":sum(x["closed_5m_bars"] for x in rows),
        "source_1h_raid_candidates":sum(x["source_1h_raid_candidates"] for x in rows),
        "price_raid_imb_candidate_pairs":sum(x["raid_then_5m_imb_time_and_geometry_pairs"] for x in rows),
        "price_touch_candidate_pairs":sum(x["with_later_5m_poi_price_touch"] for x in rows),
        "results":rows,
        "academic_approved_stronghl":0,"academic_approved_vc":0,"trade_ready":False,
        "original_f06_and_c08_unchanged":True,
        "limitations":"Temporal 1h raid plus later 5m IMB + possible zone touch; no independent author labels and no confirmed market regimes, FTA, risk, orders"
    }
    assert doc["verified_raw_closed_5m"]==2880 and len(rows)==5
    pinned=json.loads((ROOT/"evidence"/"c11"/"C11_F06_SOURCE_PRICE_CANDIDATE_DIAGNOSTICS.json").read_text(encoding="utf8"))
    assert pinned["schema"]=="EMBER_B1_C11_ORIGINAL_F06_RAID_5M_IMB_POI_RESEARCH_RECEIPT_V1"
    assert pinned["source_receipt_git_blob"]=="a5bf2105d1c611517a8d127d5e1f8cb622720162"
    assert pinned["market"]==doc["source_market"]
    assert pinned["source_bars"]==doc["verified_raw_closed_5m"]
    assert pinned["source_1h_raid_geometric_candidates"]==doc["source_1h_raid_candidates"]
    assert pinned["raid_imb_temporal_candidate_PAIRS_NOT_INDEPENDENT_EVENTS"]==doc["price_raid_imb_candidate_pairs"]
    assert pinned["raid_imb_pairs_with_later_zone_price_contact"]==doc["price_touch_candidate_pairs"]
    assert pinned["unique_author_StrongHL_approved"]==0 and pinned["academic_VC_approved"]==0
    assert pinned["trade_ready"] is False
    for observed,p in zip(rows,pinned["rows"]):
        assert observed["symbol"]==p["symbol"]
        assert observed["source_1h_raid_candidates"]==p["source_1h_raid_candidates"]
        assert observed["raid_then_5m_imb_time_and_geometry_pairs"]==p["raid_5m_imb_temporal_pairs"]
        assert observed["with_later_5m_poi_price_touch"]==p["with_later_poi_price_touch"]
        assert observed["without_later_touch"]==p["without_later_price_touch"]
        assert observed["first_price_witness"]==p["first_price_witness"]
    print(json.dumps(doc,sort_keys=True,indent=2))
    if dest:Path(dest).write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
