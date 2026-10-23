#!/usr/bin/env python3
"""Original 45 USD-M ZIP C44 bounded 1H FTA source-only hypotheses.

All signed source contexts C43 verified against original source and previous
closed 4H/1D context. NOT academic POI, orders, trades or target fills.
"""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ("tests","d05","tools"):
    sys.path.insert(0,str(ROOT/name))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c44_adapted_bounded_source_fta import scan_original_c44_bounded_source,POLICIES

FROZEN=ROOT/"evidence/c44/C44_ORIGINAL_BOUNDED_FTA_SOURCE_45ZIP.json"
C43_BLOB="c1db4afec81cb240f981e6e0ef2211044c75e372"
C43_FULL="92956d189574d2a13a0f8aa3f5aa9f99ddd4cc33dcb128c3fbb2b9b8fc30e791"
CUT=OCT_START+DAY+3*THREE

def run(out=None):
    oldroot=ROOT/"evidence/c43"
    manifest=json.loads((oldroot/"C43_ORIGINAL_45ZIP_MANIFEST.json").read_text())
    assert manifest["complete_aggregate_source_json_sha256"]==C43_FULL
    parts={entry["symbol"]:entry for entry in manifest["market_parts"]}
    markets=[]
    for sym in sorted(SYMS):
        previous=json.loads((oldroot/parts[sym]["name"]).read_text())
        native={tf:tuple(load_original(sym,tf,period,at)[0]
            for period,at in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htfs=extended_32day_prefix(native["15m"],native["1d"],END)
        threes=tuple(native_3m(sym,part)[0] for part in PERIODS)
        full=reconcile_native_3m(threes,htfs,as_of_ms=END)
        physically_cut=reconcile_native_3m(threes,htfs,as_of_ms=CUT)
        early=scan_original_c44_bounded_source(full,as_of_ms=CUT)
        cut=scan_original_c44_bounded_source(physically_cut,as_of_ms=CUT)
        assert early==cut,"C44_PHYSICALLY_CUT_ASOF_SOURCE_DRIFT"
        bounded=scan_original_c44_bounded_source(full,as_of_ms=END)
        assert bounded.source_native3m_closed==15360
        assert full.native_15m_ohlcv_equalities==3072
        assert len(bounded.routes)==len(previous["routes"])==36
        assert bounded.academic_author_fta_goldens==bounded.author_poi_goldens==0
        assert bounded.orders==bounded.trades==() and bounded.readiness=="NOT_TRADE_READY"
        prior={(x["bos"],x["reaction"],x["fta"]):x for x in previous["routes"]}
        results=[]
        for rt in bounded.routes:
            key=(rt.bos,rt.reaction,rt.fta)
            prev=prior[key]
            assert len(rt.contexts)==len(prev["source_contexts"])==prev["parent_correlated_contexts"]
            records=[]
            for now,old in zip(rt.contexts,prev["source_contexts"]):
                assert now.original_bos_3m_row_id==old["original_bos_3m_row_id"]
                assert now.original_raid_center_ms==old["original_raid_fractal_center_ms"]
                assert now.original_bos_start_ms==old["bos_bar_start_ms"]
                assert now.original_bos_closed_ms==old["bos_bar_closed_known_ms"]
                assert now.source_reaction_confirmed==old["source_reaction_confirmed"]
                original=old["decisions"][2]["selected_candidate"]
                new_key=now.original_c43_no_touch_selected_source_key
                if original is None:
                    assert new_key is None
                else:
                    source=original["source"]
                    assert new_key==(
                        source["kind"],source["source_known_ms"],source["source_level"],
                        source["source_first_native3m_row_id"],source["source_last_native3m_row_id"])
                assert len(now.decisions)==len(POLICIES)==4
                for i,d in enumerate(now.decisions):
                    assert d.policy_id==POLICIES[i]
                    assert d.decision_known_at_ms==now.original_bos_closed_ms
                    assert not d.author_fta_verified and not d.author_poi_verified and not d.trade_allowed
                    if d.selected_candidate is not None:
                        selected=d.selected_candidate
                        assert selected.source_known_ms<=now.original_bos_start_ms
                        assert selected.source_age_at_bos_start_ms>=0
                        assert selected.original_prior_touch_state=="NO_PRIOR_SOURCE_TOUCH"
                        assert selected.first_source_raw3m_id and selected.last_source_raw3m_id
                        assert d.selected_candidate_rank is not None
                        maxhours=24 if i==0 else 72
                        maxpct=1 if i==0 else 3
                        assert selected.source_age_at_bos_start_ms<=maxhours*3600000
                        assert float(selected.distance_from_retrospective_bos_close_pct)<=maxpct
                    else:
                        assert d.selected_candidate_rank is None
                records.append(asdict(now))
            results.append({
                "bos":rt.bos,"reaction":rt.reaction,"fta":rt.fta,
                "parent_correlated_source_contexts":len(rt.contexts),
                "bounded_source_selected_counts":rt.selected_count_by_policy,
                "source_contexts":records,
                "author_poi_goldens":0,"orders":0,"trades":0,"readiness":"NOT_TRADE_READY"
            })
        markets.append({"symbol":sym,"original_native3m_closed":bounded.source_native3m_closed,
            "original_native15m_decimal":full.native_15m_ohlcv_equalities,
            "prefix_source_physically_cut_equal":True,"source_routes":results,
            "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"})
        print("C44_ORIGINAL_SOURCE",sym,"36 route comparisons + 4 bounded hypotheses",flush=True)
    source_counts={p:sum(rt["bounded_source_selected_counts"][p]
        for m in markets for rt in m["source_routes"]) for p in POLICIES}
    assert source_counts[POLICIES[0]]<=source_counts[POLICIES[1]]
    assert source_counts[POLICIES[2]]<=source_counts[POLICIES[1]]
    assert source_counts[POLICIES[3]]<=source_counts[POLICIES[1]]
    total=sum(rt["parent_correlated_source_contexts"] for m in markets for rt in m["source_routes"])
    assert total==17316
    doc={"schema":"EMBER_C44_ADAPTED_C43_ALL_PREKNOWN_BOUNDED_SOURCE_ORIGINAL_45ZIP_V1",
         "previous_c43_git_manifest_blob":C43_BLOB,
         "previous_c43_entire_168mb_json_sha256":C43_FULL,
         "original_binance_usdm_source_zip":45,
         "original_native3m_closed":sum(x["original_native3m_closed"] for x in markets),
         "native15m_exact_decimal":sum(x["original_native15m_decimal"] for x in markets),
         "correlated_parent_contexts":total,"route_count":36,
         "policies":list(POLICIES),"correlated_bounded_candidate_counts":source_counts,
         "reference_range_not_academic_poi":True,"research_parameters_not_course_attested":True,
         "author_fta_goldens":0,"author_poi_goldens":0,
         "orders":0,"trades":0,"readiness":"NOT_TRADE_READY",
         "limitations":"Source age 24/72 hours, break-close distance 1/3 pct, prior full 4H/1D ranges are independent ADAPTED research choices, NOT author POI; original native3m OHLC not fill events. 36 route overlays are correlated; original archived 2026-09/10 window reused; no independent unseen performance holdout.",
         "markets":markets}
    assert doc["original_native3m_closed"]==76800
    assert doc["native15m_exact_decimal"]==15360
    if out:
        dest=Path(out);dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if FROZEN.exists():
        assert json.loads(FROZEN.read_text(encoding="utf8"))==json.loads(json.dumps(doc,sort_keys=True)),"C44_FULL_ORIGINAL_45ZIP_SOURCE_JSON_DRIFT"
    print(json.dumps({"correlated_source_counts":source_counts,"parent_contexts":total,"trades":0},sort_keys=True),flush=True)
    return doc

if __name__=="__main__":
    run(sys.argv[1] if len(sys.argv)>1 else None)
