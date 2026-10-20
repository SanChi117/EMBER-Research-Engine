#!/usr/bin/env python3
"""C39 original 45 ZIP replay of 4 independently timed BOS × 3 potential 1H FTA.

Academic 1H fractal and three-hour classic IMB raw sources reused as
distinct FTA obstacle families. Only select levels already known before
the original 3m BOS candle starts. Price is retrospective BOS bar close
known after its own closure; candidates are not order targets.
"""
import json,sys
from dataclasses import asdict
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
for s in ("tests","d05","tools"):sys.path.insert(0,str(ROOT/s))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c39_adapted_preknown_fta_source import scan_original_preknown_fta,FTA_VARIANTS
from c36_adapted_pivot_hypotheses import VARIANTS,chronological_partition
from c36_adapted_slot_registry import ACADEMIC_CORE_ID

C37_PATH=ROOT/"evidence/c37/C37_ORIGINAL_FOUR_ADAPTED_NATIVE3M_BOS_EVENTS.json"
C39_PIN=ROOT/"evidence/c39/C39_ORIGINAL_FOUR_BOS_BY_THREE_POTENTIAL_FTA.json"
C37_BLOB="e4b702e8c6cdc34f1c2475df73ef44ae1631fe56"
CUTOFF=OCT_START+DAY+3*THREE

def run(output=None):
    original=json.loads(C37_PATH.read_text(encoding="utf8"))
    markets_prev={m["symbol"]:m for m in original["markets"]}
    markets=[]
    for symbol in sorted(SYMS):
        frames={tf:tuple(load_original(symbol,tf,p,start)[0]
                 for p,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htfs=extended_32day_prefix(frames["15m"],frames["1d"],END)
        source_files=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        full=reconcile_native_3m(source_files,htfs,as_of_ms=END)
        prefix=reconcile_native_3m(source_files,htfs,as_of_ms=CUTOFF)
        assert scan_original_preknown_fta(full,as_of_ms=CUTOFF)==scan_original_preknown_fta(prefix,as_of_ms=CUTOFF),"C39_FUTURE_SUFFIX_LOOKAHEAD"
        obs=scan_original_preknown_fta(full,as_of_ms=END)
        assert obs.academic_core_id==ACADEMIC_CORE_ID
        assert obs.source_original_native3m_rows==15360
        assert full.native_15m_ohlcv_equalities==3072
        assert obs.fta_hypotheses==FTA_VARIANTS and obs.bos_hypotheses==VARIANTS
        assert len(obs.routes)==12 and obs.author_fta_goldens==obs.author_approved_targets==0
        assert obs.orders==obs.trades==() and obs.readiness=="NOT_TRADE_READY"
        per=[]
        for route in obs.routes:
            ref=markets_prev[symbol]["adapted_routes"][route.bos_hypothesis_id]
            assert route.research_BOS_raid_contexts==ref["raid_context_event_count"]
            assert route.with_potential_source_obstacle+route.without_source_obstacle==route.research_BOS_raid_contexts
            assert len(route.observations)==route.research_BOS_raid_contexts
            selected=[]
            unique_break_rows=set()
            slices={"DEVELOPMENT":0,"VALIDATION":0,"HOLDOUT":0}
            for event in route.observations:
                assert event.hypothesis_id==route.fta_hypothesis_id
                assert event.bos_hypothesis_id==route.bos_hypothesis_id
                assert event.author_selected_FTA is False and event.paper_signal_allowed is False
                assert event.orders==event.trades==event.target_orders==()
                assert event.readiness=="NOT_TRADE_READY"
                unique_break_rows.add(event.original_bos_3m_break_row_id)
                if event.selected_potential_obstacle:
                    candidate=event.selected_potential_obstacle
                    assert candidate.source_known_ms<=event.research_break_3m_close_known_ms-THREE
                    assert Decimal(candidate.distance_from_retrospective_break_close)>0
                    assert not candidate.author_priority_attested and not candidate.mitigation_or_freshness_attested
                    slices[chronological_partition(event.research_break_3m_close_known_ms-THREE)]+=1
                selected.append(asdict(event))
            per.append({
                "bos_hypothesis_id":route.bos_hypothesis_id,
                "fta_hypothesis_id":route.fta_hypothesis_id,
                "source_BOS_raid_contexts":route.research_BOS_raid_contexts,
                "unique_source_BOS_break_bars":len(unique_break_rows),
                "contexts_with_potential_obstacle":route.with_potential_source_obstacle,
                "contexts_without_potential_obstacle":route.without_source_obstacle,
                "selection_partition":slices,
                "original_source_observations":selected,
                "author_fta_targets":0,
                "paper_signals":0,"orders":0,"trades":0,"readiness":"NOT_TRADE_READY"
            })
        markets.append({
            "symbol":symbol,
            "original_closed3m":obs.source_original_native3m_rows,
            "original15m_Decimal_parity":full.native_15m_ohlcv_equalities,
            "prefix_physically_equal":True,
            "bos_by_potential_fta_routes":per,
            "author_fta_goldens":0,
            "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"
        })
        print(symbol,"12 FTA combinations",[(r["bos_hypothesis_id"].split("_")[0],
            r["fta_hypothesis_id"].split("_")[0],r["contexts_with_potential_obstacle"])
            for r in per],flush=True)
    summaries={}
    for bos in VARIANTS:
        for fta in FTA_VARIANTS:
            rows=[z for m in markets for z in m["bos_by_potential_fta_routes"]
                 if z["bos_hypothesis_id"]==bos and z["fta_hypothesis_id"]==fta]
            assert len(rows)==5
            summaries[bos+"::"+fta]={
                "source_bos_contexts":sum(z["source_BOS_raid_contexts"] for z in rows),
                "with_potential_source_fta":sum(z["contexts_with_potential_obstacle"] for z in rows),
                "without_potential_source_fta":sum(z["contexts_without_potential_obstacle"] for z in rows),
                "selection_partition":{period:sum(z["selection_partition"][period] for z in rows)
                  for period in ("DEVELOPMENT","VALIDATION","HOLDOUT")}
            }
            x=summaries[bos+"::"+fta]
            assert x["source_bos_contexts"]==x["with_potential_source_fta"]+x["without_potential_source_fta"]
    result={
        "schema":"EMBER_C39_ORIGINAL_FOUR_BOS_BY_THREE_PREKNOWN_1H_POTENTIAL_FTA_45ZIP_V1",
        "prior_C37_source_git_blob":C37_BLOB,
        "replayed_original_usdm_zip_count":45,
        "closed_original_native3m_bars":sum(m["original_closed3m"] for m in markets),
        "native15m_original_decimal_equalities":sum(m["original15m_Decimal_parity"] for m in markets),
        "bos_variants":list(VARIANTS),"potential_fta_variants":list(FTA_VARIANTS),
        "route_count":12,
        "source_rule":"Prior 1H fractal/IMB fully known by original 3m BOS BAR START; candidate strictly ahead of retrospective BOS close, no prior touch/freshness/author FTA attested.",
        "price_source_scope":"Retrospective break candle CLOSE only, known at break BAR CLOSE; not an executable order entry.",
        "independent_source_obstacles_not_trades":True,
        "original_author_selected_fta_goldens":0,"author_target_approvals":0,
        "paper_signals":0,"orders":0,"trades":0,
        "readiness":"NOT_TRADE_READY",
        "summary_by_route":summaries,
        "markets":markets
    }
    assert result["closed_original_native3m_bars"]==76800
    assert result["native15m_original_decimal_equalities"]==15360
    assert result["route_count"]==12
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if C39_PIN.exists():
        assert json.loads(C39_PIN.read_text(encoding="utf8"))==json.loads(json.dumps(result,sort_keys=True)),"C39_FROZEN_FULL_JSON_DRIFT"
    print(json.dumps({"source_summaries":summaries,"status":result["readiness"]},
        sort_keys=True),flush=True)
    return result

if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
