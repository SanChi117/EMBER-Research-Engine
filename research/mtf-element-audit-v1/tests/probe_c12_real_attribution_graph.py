#!/usr/bin/env python3
"""B1/C12 independent real F06 5m source ↔ causal attribution graph witness.

Verifies all ten original Binance ZIP/CSV hashes against F06 receipts, then
measures graph ambiguity. The C11 receipt is a separate pinned baseline.
No user orders, no academic StrongHL or VC signoff.
"""
from __future__ import annotations
import json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from f03_5m_original_source import download_source_5m,DAY
from c12_attribution_ambiguity_gate import inspect_ambiguity_from_original_source

F06=ROOT/"evidence"/"f06"/"F06_FIVE_SYMBOL_TWO_DAY_5M_SOURCE_RECEIPTS.json"
C11=ROOT/"evidence"/"c11"/"C11_F06_SOURCE_PRICE_CANDIDATE_DIAGNOSTICS.json"
ORIGIN={"2026-10-01":1790812800000,"2026-10-02":1790899200000}

def main(outfile=None):
    f06=json.loads(F06.read_text(encoding="utf8"))
    c11=json.loads(C11.read_text(encoding="utf8"))
    assert f06["schema"]=="EMBER_B1_C10_TWO_CONSECUTIVE_DAYS_FIVE_SYMBOL_ORIGINAL_5M_RECEIPTS_V1"
    assert c11["schema"]=="EMBER_B1_C11_ORIGINAL_F06_RAID_5M_IMB_POI_RESEARCH_RECEIPT_V1"
    assert f06["readiness"]=="NOT_TRADE_READY" and f06["academy_entry_approved"]==0 and c11["academic_VC_approved"]==0
    assert len(f06["source_days"])==10
    observed=[]
    for symbol in f06["symbols"]:
        original=[]
        for date in f06["dates"]:
            one=next((r for r in f06["source_days"] if r["symbol"]==symbol and r["date"]==date),None)
            assert one is not None
            url=f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/5m/{symbol}-5m-{date}.zip"
            proof=download_source_5m(url)
            assert proof.archive_url==url and proof.symbol==symbol and proof.day_start_ms==ORIGIN[date]
            assert proof.zip_sha256==one["original_5m_zip_sha256"]
            assert proof.raw_csv_sha256==one["original_5m_csv_sha256"]
            original.append(proof)
        a=inspect_ambiguity_from_original_source(original[0],original[1],ORIGIN["2026-10-02"]+DAY)
        prior=next(r for r in c11["rows"] if r["symbol"]==symbol)
        assert a.total_raid_imb_edges==prior["raid_5m_imb_temporal_pairs"]
        assert a.total_known_raid_candidates==prior["source_1h_raid_candidates"]
        assert a.edges_touching_zone_later==prior["with_later_poi_price_touch"]
        assert a.edges_without_later_zone_touch==prior["without_later_price_touch"]
        assert a.author_vc_approvals==a.author_stronghl_approvals==0
        assert a.readiness=="NOT_TRADE_READY"
        observed.append({
            "symbol":symbol,
            "closed_native_5m_candles":len(original[0].rows)+len(original[1].rows),
            "raid_candidates":a.total_known_raid_candidates,
            "candidate_edges_not_events":a.total_raid_imb_edges,
            "raids_with_edges":a.raid_nodes_with_edges,
            "distinct_imb_nodes":a.unique_imb_nodes_with_edges,
            "raids_with_multiple_imbs":a.raids_with_multiple_imbs,
            "imb_nodes_with_multiple_raid_parents":a.imbs_with_multiple_raids,
            "pairs_with_later_zone_touch":a.edges_touching_zone_later,
            "pairs_without_touch":a.edges_without_later_zone_touch,
            "author_attribution":"NOT_RESOLVED_BY_ACADEMIC_SOURCE",
            "ready":False
        })
    result={
        "cycle":"B1_C12_F06_REAL_CAUSAL_AMBIGUITY_DIAGNOSTIC",
        "source_market":"BINANCE_USDM_FUTURES",
        "dates":f06["dates"],
        "symbols":f06["symbols"],
        "source_5m_archives":10,
        "source_5m_candles":sum(x["closed_native_5m_candles"] for x in observed),
        "geometric_edges":sum(x["candidate_edges_not_events"] for x in observed),
        "original_C11_reference_edges":c11["raid_imb_temporal_candidate_PAIRS_NOT_INDEPENDENT_EVENTS"],
        "distinct_imb_nodes":sum(x["distinct_imb_nodes"] for x in observed),
        "raids_with_multiple_imbs":sum(x["raids_with_multiple_imbs"] for x in observed),
        "imbs_with_multiple_raid_parents":sum(x["imb_nodes_with_multiple_raid_parents"] for x in observed),
        "total_distinct_raids_with_edges":sum(x["raids_with_edges"] for x in observed),
        "pairs_touching_zone_later":sum(x["pairs_with_later_zone_touch"] for x in observed),
        "per_symbol":observed,
        "author_approved_vc":0,"author_approved_stronghl":0,"trade_ready":False,
        "audit_status":"UNRESOLVED_ATTRIBUTION_NOT_ACADEMIC_ENTRY",
        "evidence_limit":"Only two UTC days and 5 instruments. Course does not specify first/nearest or fixed-TTL parent attribution, graph counts are geometric only."
    }
    assert result["source_5m_candles"]==2880 and result["geometric_edges"]==177
    assert result["pairs_touching_zone_later"]==168 and result["source_5m_archives"]==10
    pinned=json.loads((ROOT/"evidence"/"c12"/"C12_CAUSAL_AMBIGUITY_F06_DIAGNOSTIC.json").read_text(encoding="utf8"))
    assert pinned["schema"]=="EMBER_B1_C12_F06_TWO_DAY_RAID_IMB_ATTRIBUTION_DIAGNOSTICS_V1"
    assert pinned["f06_raw_zip_and_csv_receipt_git_blob"]=="a5bf2105d1c611517a8d127d5e1f8cb622720162"
    assert pinned["c11_immutably_pinned_candidate_receipt_git_blob"]=="513c950c311efc12fab95ce64f4ac47f0f6003f3"
    for pkey,rkey in (
        ("independently_rechecked_5m_archives","source_5m_archives"),
        ("independently_rechecked_5m_rows","source_5m_candles"),
        ("geometric_raid_imb_edges_not_trade_signals","geometric_edges"),
        ("unique_geometric_imb_nodes","distinct_imb_nodes"),
        ("unique_raid_nodes_with_edges","total_distinct_raids_with_edges"),
        ("raid_nodes_with_multiple_imbs","raids_with_multiple_imbs"),
        ("imbs_with_multiple_raid_parents","imbs_with_multiple_raid_parents"),
        ("later_poi_zone_price_touch_edges","pairs_touching_zone_later")):
        assert pinned[pkey]==result[rkey],(pkey,rkey)
    assert pinned["status"]==result["audit_status"]
    assert pinned["unique_approved_stronghl"]==pinned["approved_vc"]==pinned["ready_trades"]==0
    assert len(pinned["per_symbol"])==len(result["per_symbol"])==5
    for saved,actual in zip(pinned["per_symbol"],result["per_symbol"]):
        assert saved["symbol"]==actual["symbol"]
        for keya,keyb in (
            ("original_5m_candles","closed_native_5m_candles"),
            ("v05_hourly_raid_candidates","raid_candidates"),
            ("geometric_raid_to_imb_edges","candidate_edges_not_events"),
            ("distinct_5m_imb_nodes","distinct_imb_nodes"),
            ("hourly_raids_with_any_matching_imb","raids_with_edges"),
            ("hourly_raids_with_multiple_imb_candidates","raids_with_multiple_imbs"),
            ("imbs_with_multiple_raid_parents","imb_nodes_with_multiple_raid_parents"),
            ("pairs_with_later_price_touch","pairs_with_later_zone_touch"),
            ("pairs_without_later_price_touch","pairs_without_touch")):
            assert saved[keya]==actual[keyb],(saved["symbol"],keya)
    print(json.dumps(result,sort_keys=True,indent=2))
    if outfile:Path(outfile).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
