#!/usr/bin/env python3
"""C43 all 45 SHA-pinned original Binance USD-M archives, every source FTA.

4 native3m BOS × 3 post-raid reactions × 3 C39 source FTA family priority ×
3 C42 prior-touch gates; original 1H candidate *each independently* validated
against source original3m OHLC before BOS candle START. Only after break candle
CLOSE may any retrospective re-rank be known. 0 trades / NOT_TRADE_READY.
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
from c43_adapted_per_candidate_fta_rerank import scan_original_per_candidate_fta_rerank
from c42_adapted_source_fta_eligibility import ELIGIBILITY_POLICIES
from c38_adapted_post_raid_reaction import REACTION_VARIANTS
from c39_adapted_preknown_fta_source import FTA_VARIANTS
from c36_adapted_pivot_hypotheses import VARIANTS

PARENT=ROOT/"evidence/c41/C41_ORIGINAL_36_SOURCE_JOIN_MATRIX.json"
C42=ROOT/"evidence/c42/C42_ORIGINAL_SOURCE_FTA_ELIGIBILITY_45ZIP.json"
PIN=ROOT/"evidence/c43/C43_ORIGINAL_ALL_PREKNOWN_CANDIDATE_FTA_RERANK_45ZIP.json"
C41_GIT="ac3bb2b2babafdb28af71c4cbaa2b53fce03b06c"
C42_GIT="bddf315c58a906fe58546512bc416c24bd1ce95f"
CUT=OCT_START+DAY+3*THREE

def run(out=None):
    frozen41=json.loads(PARENT.read_text(encoding="utf8"))
    frozen42=json.loads(C42.read_text(encoding="utf8"))
    old41={m["symbol"]:m for m in frozen41["markets"]}
    old42={m["symbol"]:m for m in frozen42["markets"]}
    markets=[]
    for sym in sorted(SYMS):
        native={tf:tuple(load_original(sym,tf,period,start)[0]
            for period,start in zip(DATES,STARTS))
            for tf in ("15m","1d")}
        htfs=extended_32day_prefix(native["15m"],native["1d"],END)
        three=tuple(native_3m(sym,period)[0] for period in PERIODS)
        full=reconcile_native_3m(three,htfs,as_of_ms=END)
        prefix=reconcile_native_3m(three,htfs,as_of_ms=CUT)
        before=scan_original_per_candidate_fta_rerank(full,as_of_ms=CUT)
        physical=scan_original_per_candidate_fta_rerank(prefix,as_of_ms=CUT)
        assert before==physical,"C43_PHYSICALLY_CUT_SOURCE_FUTURE_SUFFIX_LEAK"
        result=scan_original_per_candidate_fta_rerank(full,as_of_ms=END)
        assert result.source_original3m_closed==15360
        assert full.native_15m_ohlcv_equalities==3072
        assert result.original_c41_routes==len(result.routes)==36
        assert result.orders==result.trades==() and result.author_fta_goldens==0
        assert result.readiness=="NOT_TRADE_READY"
        by41={(x["bos"],x["reaction"],x["fta"]):x for x in old41[sym]["routes"]}
        by42={(x["bos"],x["reaction"],x["fta"]):x for x in old42[sym]["source_routes"]}
        assert len(by41)==len(by42)==36
        observed=[]
        for route in result.routes:
            key=(route.bos,route.reaction,route.fta)
            prior41=by41[key]
            prior42=by42[key]
            assert route.parent_contexts==prior41["parent_BOS_source_contexts"]==prior42["parent_correlated_source_contexts"]
            assert route.selected_by_policy[ELIGIBILITY_POLICIES[0]]==prior42["eligible_counts_by_explicit_adapted_policy"][ELIGIBILITY_POLICIES[0]]
            assert route.replacements_by_policy[ELIGIBILITY_POLICIES[0]]==0
            records=[]
            for index,context in enumerate(route.contexts):
                o=prior41["original_source_contexts"][index]
                previous=prior42["source_context_eligibility_observations"][index]
                assert context.original_bos_3m_row_id==o["original_bos_native3m_row_id"]==previous["original_bos_native3m_row_id"]
                assert context.bos_bar_start_ms==o["bos_bar_start_ms"]==previous["bos_bar_start_ms"]
                assert context.bos_bar_closed_known_ms==o["bos_bar_closed_known_ms"]==previous["bos_bar_closed_known_ms"]
                assert context.original_raid_fractal_center_ms==o["original_raid_fractal_center_ms"]
                assert context.source_reaction_confirmed==o["source_reaction_confirmed"]
                assert context.source_preknown_candidate_count>=context.distinct_source_candidate_count
                assert context.distinct_source_candidate_count>=0
                assert tuple(x.eligibility_policy_id for x in context.decisions)==ELIGIBILITY_POLICIES
                original=context.original_c39_candidate
                if original is None:
                    assert o["potential_1h_obstacle_kind"] is None
                else:
                    s=original.source
                    t=original.touch
                    assert s.kind==o["potential_1h_obstacle_kind"]
                    assert s.source_known_ms==o["potential_1h_obstacle_source_known_ms"]
                    assert t.classification==o["source_prior_touch_classification"]
                    assert t.first_touch_original3m_row_id==o["first_prior_touch_original_native3m_row_id"]
                    assert t.first_full_sweep_or_traversal_ms==o["first_prior_full_sweep_or_traversal_ms"]
                for i,decision in enumerate(context.decisions):
                    policy=ELIGIBILITY_POLICIES[i]
                    assert decision.known_at_ms==context.bos_bar_closed_known_ms
                    assert decision.original_selected_gate_eligible==previous["decisions"][i]["eligible"]
                    assert not decision.order_allowed and not decision.author_fta_approved
                    if decision.selected_candidate is not None:
                        chosen=decision.selected_candidate
                        assert decision.selected_candidate_rank is not None
                        assert chosen.source.source_known_ms<=context.bos_bar_start_ms
                        assert chosen.touch.original_bos_native3m_row_id==context.original_bos_3m_row_id
                        assert chosen.touch.classification!="NO_PREKNOWN_FTA_CANDIDATE"
                        assert not chosen.source.author_priority_attested
                        assert not chosen.source.mitigation_or_freshness_attested
                        if i==2:
                            assert chosen.touch.classification=="NO_PRIOR_SOURCE_TOUCH"
                        if i==1:
                            assert chosen.touch.classification!="PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL"
                    else:
                        assert decision.selected_candidate_rank is None
                    if decision.original_selected_gate_eligible:
                        assert decision.selected_candidate==original
                        assert decision.selected_candidate_rank==0
                    if decision.substituted_after_original_gate_rejection:
                        assert not decision.original_selected_gate_eligible
                        assert decision.selected_candidate is not None
                        assert decision.selected_candidate_rank>0
                assert context.orders==context.trades==() and context.readiness=="NOT_TRADE_READY"
                records.append(asdict(context))
            observed.append({
                "bos":route.bos,"reaction":route.reaction,"fta":route.fta,
                "parent_correlated_contexts":route.parent_contexts,
                "selected_counts_by_policy":route.selected_by_policy,
                "alternate_substitutions_by_policy":route.replacements_by_policy,
                "source_contexts":records,
                "author_fta_certified":False,"orders":0,"trades":0,
                "readiness":"NOT_TRADE_READY"})
        markets.append({"symbol":sym,"original_closed_native3m":result.source_original3m_closed,
            "native15m_exact_decimal":full.native_15m_ohlcv_equalities,
            "physically_cut_source_prefix_equal":True,
            "routes":observed,"orders":0,"trades":0,"readiness":"NOT_TRADE_READY"})
        print(sym,"36×3 ADAPTED FTA reranks, native3m",result.source_original3m_closed,flush=True)
    summaries={}
    for p in ELIGIBILITY_POLICIES:
        selected=sum(rt["selected_counts_by_policy"][p] for m in markets for rt in m["routes"])
        replaced=sum(rt["alternate_substitutions_by_policy"][p] for m in markets for rt in m["routes"])
        old=sum(rt["selected_counts_by_policy"][p] - rt["alternate_substitutions_by_policy"][p]
                for m in markets for rt in m["routes"])
        summaries[p]={"selected_after_per_candidate_rerank":selected,
             "selected_original_c39_candidate":old,
             "reselected_distinct_alternate_source":replaced}
    total=sum(rt["parent_correlated_contexts"] for m in markets for rt in m["routes"])
    assert total==17316
    assert summaries[ELIGIBILITY_POLICIES[0]]["reselected_distinct_alternate_source"]==0
    assert all(summaries[p]["selected_after_per_candidate_rerank"]>=
               frozen42["policy_counts_across_correlated_routes"][p]
               for p in ELIGIBILITY_POLICIES)
    assert (summaries[ELIGIBILITY_POLICIES[0]]["selected_after_per_candidate_rerank"]>=
            summaries[ELIGIBILITY_POLICIES[1]]["selected_after_per_candidate_rerank"]>=
            summaries[ELIGIBILITY_POLICIES[2]]["selected_after_per_candidate_rerank"])
    result={
       "schema":"EMBER_C43_ADAPTED_SOURCE_PER_CANDIDATE_FTA_RERANK_45ZIP_V1",
       "parent_C41_git_blob":C41_GIT,"parent_C42_git_blob":C42_GIT,
       "original_usdm_binance_zip":45,
       "original_native3m_closed":sum(m["original_closed_native3m"] for m in markets),
       "native15m_exact_decimal":sum(m["native15m_exact_decimal"] for m in markets),
       "source_route_count":36,"adapted_policy_count":3,
       "parent_correlated_contexts":total,
       "policy_source_rerank_summary":summaries,
       "source_rank_decision_availability":"AT_3M_BOS_BAR_CLOSE_RETROSPECTIVE_C39",
       "original3m_wick_touch_availability":"ONLY_AFTER_ORIGINAL_1H_SOURCE_KNOWN_AND_BEFORE_BOS_BAR_START",
       "source_author_goldens":0,"orders":0,"trades":0,
       "readiness":"NOT_TRADE_READY",
       "limitations":"Reselected source obstacle is NOT an academic FTA, a target, a fill, or strategy performance. Source 3m OHLC does not prove intrabar order. History begins Sep 2026; original C39 ranking depends on closed BOS candle and is not available at BOS bar start. Repeated 36 routes are correlated.",
       "markets":markets}
    assert result["original_native3m_closed"]==76800
    assert result["native15m_exact_decimal"]==15360
    if out:
        file=Path(out);file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if PIN.exists():
        assert json.loads(PIN.read_text(encoding="utf8"))==json.loads(json.dumps(result,sort_keys=True)),"C43_FROZEN_FULL_JSON_DRIFT"
    print(json.dumps({"reranks":summaries,"parent_contexts":total,"trades":0},sort_keys=True),flush=True)
    return result

if __name__=="__main__":
    run(sys.argv[1] if len(sys.argv)>1 else None)
