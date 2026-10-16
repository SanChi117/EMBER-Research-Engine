#!/usr/bin/env python3
"""B1/C13: ten original Binance 5m source receipts → v05 BOS OR 5m IMB paths.

Reuses F06 ZIP+CSV SHA and C12 graph benchmarks. Does not invent
author-confirmed StrongHL/VC or favor BOS over POI in trading.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from f03_5m_original_source import download_source_5m,DAY
from c13_stronghl_bos_or_poi_source_branch import inspect_both_author_branches
F06=ROOT/"evidence"/"f06"/"F06_FIVE_SYMBOL_TWO_DAY_5M_SOURCE_RECEIPTS.json"
C12=ROOT/"evidence"/"c12"/"C12_CAUSAL_AMBIGUITY_F06_DIAGNOSTIC.json"
START={"2026-10-01":1790812800000,"2026-10-02":1790899200000}

def main(outfile=None):
    source=json.loads(F06.read_text(encoding="utf8"))
    c12=json.loads(C12.read_text(encoding="utf8"))
    assert source["schema"]=="EMBER_B1_C10_TWO_CONSECUTIVE_DAYS_FIVE_SYMBOL_ORIGINAL_5M_RECEIPTS_V1"
    assert c12["schema"]=="EMBER_B1_C12_F06_TWO_DAY_RAID_IMB_ATTRIBUTION_DIAGNOSTICS_V1"
    assert source["readiness"]=="NOT_TRADE_READY" and c12["ready_trades"]==0
    rows=[]
    for sym in source["symbols"]:
        originals=[]
        for day in source["dates"]:
            expected=next(v for v in source["source_days"] if v["symbol"]==sym and v["date"]==day)
            url=f"https://data.binance.vision/data/futures/um/daily/klines/{sym}/5m/{sym}-5m-{day}.zip"
            obj=download_source_5m(url,40)
            assert obj.symbol==sym and obj.day_start_ms==START[day]
            assert obj.zip_sha256==expected["original_5m_zip_sha256"]
            assert obj.raw_csv_sha256==expected["original_5m_csv_sha256"]
            assert len(obj.rows)==288
            originals.append(obj)
        q=inspect_both_author_branches(*originals,START["2026-10-02"]+DAY)
        prior=next(x for x in c12["per_symbol"] if x["symbol"]==sym)
        assert q.known_raid_candidates==prior["v05_hourly_raid_candidates"]
        assert q.imb_pair_count==prior["geometric_raid_to_imb_edges"]
        assert q.distinct_imb_count==prior["distinct_5m_imb_nodes"]
        assert q.raids_with_imb_branch==prior["hourly_raids_with_any_matching_imb"]
        assert q.author_stronghl_approvals==q.author_vc_approvals==0
        assert q.readiness=="NOT_TRADE_READY"
        assert q.raids_with_any_observed_branch+q.unknown_raids_without_either==q.known_raid_candidates
        assert q.raids_with_any_observed_branch==q.bos_only_raids+q.imb_only_raids+q.raids_with_both_branches
        rows.append({
            "symbol":sym,
            "original_raw_5m_bars":576,
            "v05_1h_raid_candidates":q.known_raid_candidates,
            "original_5m_bos_events":q.bos_event_count,
            "original_raid_imb_pair_edges":q.imb_pair_count,
            "distinct_imb_nodes":q.distinct_imb_count,
            "raids_with_bos_path":q.raids_with_bos_branch,
            "raids_with_poi_imb_path":q.raids_with_imb_branch,
            "raids_with_both_geometric_paths":q.raids_with_both_branches,
            "raids_with_only_bos_geometry":q.bos_only_raids,
            "raids_with_only_imb_geometry":q.imb_only_raids,
            "raids_without_either_geometry":q.unknown_raids_without_either,
            "parent_bos_and_imb_evidence":[{
                "raid_id":x.raid_source_uid,
                "bos_ids":list(x.bos_event_ids),
                "imb_ids":list(x.imb_event_ids),
                "path_class":x.classification
            } for x in q.parent_bos_links],
            "source_provenance":"ORIGINAL_F06_TEN_5M_ZIPS_INDEPENDENT_SHA_CHECK",
            "author_StrongHL_confirmed":False,
            "trade_ready":False
        })
    report={
        "cycle":"B1_C13_ORIGINAL_F06_BOS_OR_POI_STRONGHL_GEOMETRY",
        "source_market":"BINANCE_USDM_FUTURES",
        "source_dates":source["dates"],
        "symbols":source["symbols"],
        "original_5m_zip_archives":10,
        "source_5m_bars":sum(r["original_raw_5m_bars"] for r in rows),
        "raid_candidates":sum(r["v05_1h_raid_candidates"] for r in rows),
        "bos_geometric_event_count":sum(r["original_5m_bos_events"] for r in rows),
        "raid_to_imb_geometric_edges":sum(r["original_raid_imb_pair_edges"] for r in rows),
        "distinct_imb_nodes":sum(r["distinct_imb_nodes"] for r in rows),
        "raids_with_bos_path":sum(r["raids_with_bos_path"] for r in rows),
        "raids_with_imb_path":sum(r["raids_with_poi_imb_path"] for r in rows),
        "raids_with_both_geometric_paths":sum(r["raids_with_both_geometric_paths"] for r in rows),
        "bos_only_raids":sum(r["raids_with_only_bos_geometry"] for r in rows),
        "imb_only_raids":sum(r["raids_with_only_imb_geometry"] for r in rows),
        "raids_without_either":sum(r["raids_without_either_geometry"] for r in rows),
        "results":rows,
        "author_approved_vc":0,"author_approved_stronghl":0,
        "trade_ready":False,
        "course_contract":"StrongHL contact + later confirmation POI OR BOS; these two geometric alternatives are not author-positive labels",
        "frozen_F06_C12_retained":True,
        "research_scope":"2-day 5-symbol USD-M Futures v05 geometry only, no complete 1D/4H POI context, no independent author golden labels"
    }
    assert report["source_5m_bars"]==2880
    assert report["raid_to_imb_geometric_edges"]==177
    assert report["bos_geometric_event_count"]==12
    assert report["raid_candidates"]==25
    pinned=json.loads((ROOT/"evidence"/"c13"/"C13_DUAL_SOURCE_BOS_POI_DIAGNOSTICS.json").read_text(encoding="utf8"))
    assert pinned["schema"]=="EMBER_B1_C13_ORIGINAL_F06_BOS_OR_POI_GEOMETRIC_BRANCH_DIAGNOSTICS_V1"
    assert pinned["original_F06_zip_csv_receipt_blob"]=="a5bf2105d1c611517a8d127d5e1f8cb622720162"
    assert pinned["original_C12_graph_receipt_blob"]=="a18e62776584ad428ad74c254d864c59dd540984"
    pairs=(
       ("original_5m_zip_archives","original_5m_zip_archives"),
       ("native_5m_bars","source_5m_bars"),
       ("raid_candidates","raid_candidates"),
       ("raid_to_5m_imb_geometric_edges","raid_to_imb_geometric_edges"),
       ("distinct_imb_nodes","distinct_imb_nodes"),
       ("bos_5m_events","bos_geometric_event_count"),
       ("raids_with_bos_branch","raids_with_bos_path"),
       ("raids_with_imb_branch","raids_with_imb_path"),
       ("raids_with_both_branches","raids_with_both_geometric_paths"),
       ("raids_with_bos_only","bos_only_raids"),
       ("raids_with_imb_only","imb_only_raids"),
       ("raids_with_neither","raids_without_either"))
    for pkey,rkey in pairs:assert pinned[pkey]==report[rkey],(pkey,rkey)
    assert pinned["author_approved_vc"]==pinned["author_approved_stronghl"]==0
    assert pinned["trade_ready"] is False and report["trade_ready"] is False
    assert len(pinned["per_symbol"])==len(report["results"])==5
    for a,b in zip(pinned["per_symbol"],report["results"]):
        assert a["symbol"]==b["symbol"]
        for pkey,rkey in (
           ("raid_candidates","v05_1h_raid_candidates"),
           ("bos_events","original_5m_bos_events"),
           ("imb_pairs","original_raid_imb_pair_edges"),
           ("distinct_imb_nodes","distinct_imb_nodes"),
           ("bos_path_raids","raids_with_bos_path"),
           ("imb_path_raids","raids_with_poi_imb_path"),
           ("both_path_raids","raids_with_both_geometric_paths"),
           ("bos_only_raids","raids_with_only_bos_geometry"),
           ("imb_only_raids","raids_with_only_imb_geometry"),
           ("neither_path_raids","raids_without_either_geometry")):
            assert a[pkey]==b[rkey],(a["symbol"],pkey)
        assert a["first_parent_combined_branch"]==(b["parent_bos_and_imb_evidence"][0] if b["parent_bos_and_imb_evidence"] else None)
    print(json.dumps(report,sort_keys=True,indent=2))
    if outfile:Path(outfile).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return 0
if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
