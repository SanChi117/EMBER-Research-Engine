#!/usr/bin/env python3
"""C41 full original 45 Binance USD-M ZIP 36-route source-only replay.

Independently link frozen C38 reactions, C39 potential FTA, C40 prior
touch by original BOS native3m row ID and original source chronology.
Full JSON, not counts-only. No entries, PnL, fills or author labels.
"""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for sub in ("tests","d05","tools"):
    sys.path.insert(0,str(ROOT/sub))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c41_source_only_bos_reaction_fta_join import scan_original_c41_source_matrix
from c36_adapted_pivot_hypotheses import VARIANTS
from c38_adapted_post_raid_reaction import REACTION_VARIANTS
from c39_adapted_preknown_fta_source import FTA_VARIANTS
from c40_pre_bos_fta_touch_state import STATES

C38_PATH=ROOT/"evidence/c38/C38_ORIGINAL_FOUR_BOS_BY_THREE_REACTION_MATRIX.json"
C39_PATH=ROOT/"evidence/c39/C39_ORIGINAL_FOUR_BOS_BY_THREE_POTENTIAL_FTA.json"
C40_PATH=ROOT/"evidence/c40/C40_ORIGINAL_PRE_BOS_PRIOR_FTA_TOUCH_STATES.json"
C41_FROZEN=ROOT/"evidence/c41/C41_ORIGINAL_36_SOURCE_JOIN_MATRIX.json"
CUTOFF=OCT_START+DAY+3*THREE

def run(output=None):
    orig38=json.loads(C38_PATH.read_text(encoding="utf8"))
    orig39=json.loads(C39_PATH.read_text(encoding="utf8"))
    orig40=json.loads(C40_PATH.read_text(encoding="utf8"))
    prior38={m["symbol"]:m for m in orig38["markets"]}
    prior39={m["symbol"]:m for m in orig39["markets"]}
    prior40={m["symbol"]:m for m in orig40["markets"]}
    markets=[]
    for symbol in sorted(SYMS):
        raw={tf:tuple(load_original(symbol,tf,part,at)[0]
            for part,at in zip(DATES,STARTS)) for tf in ("15m","1d")}
        high=extended_32day_prefix(raw["15m"],raw["1d"],END)
        three=tuple(native_3m(symbol,part)[0] for part in PERIODS)
        full=reconcile_native_3m(three,high,as_of_ms=END)
        prefix=reconcile_native_3m(three,high,as_of_ms=CUTOFF)
        a=scan_original_c41_source_matrix(full,as_of_ms=CUTOFF)
        b=scan_original_c41_source_matrix(prefix,as_of_ms=CUTOFF)
        assert a==b,"C41_PHYSICAL_NATIVE3M_SUFFIX_LOOKAHEAD"
        current=scan_original_c41_source_matrix(full,as_of_ms=END)
        assert current.route_count==36
        assert current.source_original3m_closed==15360
        assert full.native_15m_ohlcv_equalities==3072
        assert current.readiness=="NOT_TRADE_READY"
        assert current.orders==current.trades==()
        rx={(z["bos_hypothesis_id"],z["reaction_hypothesis_id"]):z
             for z in prior38[symbol]["bos_reaction_matrix"]}
        ft={(z["bos_hypothesis_id"],z["fta_hypothesis_id"]):z
             for z in prior39[symbol]["bos_by_potential_fta_routes"]}
        tx={(z["bos"],z["fta"]):z for z in prior40[symbol]["routes"]}
        assert len(rx)==12 and len(ft)==len(tx)==12
        rs=[]
        for route in current.routes:
            old_rx=rx[(route.bos,route.reaction)]
            old_ft=ft[(route.bos,route.fta)]
            old_touch=tx[(route.bos,route.fta)]
            assert route.parent_bos_contexts==old_rx["bos_research_parent_events"]
            assert route.parent_bos_contexts==old_ft["source_BOS_raid_contexts"]
            assert route.parent_bos_contexts==old_touch["research_parent_contexts"]
            assert route.source_confirmed_reactions==old_rx["with_prior_reaction"]
            assert route.with_preknown_obstacle==old_ft["contexts_with_potential_obstacle"]
            counts={s:sum(q.source_prior_touch_classification==s
                           for q in route.observations) for s in STATES}
            assert counts==old_touch["source_prior_interaction_states"],"C41_C40_PRIOR_TOUCH_STATE_DRIFT"
            observed=[]
            for i,w in enumerate(route.observations):
                parent_rx=old_rx["source_research_observations"][i]
                parent_ft=old_ft["original_source_observations"][i]
                parent_tx=old_touch["source_review"][i]
                assert w.original_bos_native3m_row_id==parent_rx["original_bos_break_row_id"]
                assert w.original_bos_native3m_row_id==parent_ft["original_bos_3m_break_row_id"]
                assert w.original_bos_native3m_row_id==parent_tx["original_bos_native3m_row_id"]
                assert w.source_reaction_confirmed==parent_rx["condition_satisfied"]
                assert w.first_reaction_original_native3m_row_id==parent_rx["first_confirmed_native3m_row_id"]
                assert w.source_prior_touch_classification==parent_tx["classification"]
                chosen=parent_ft["selected_potential_obstacle"]
                assert w.potential_1h_obstacle_kind==(chosen["kind"] if chosen else None)
                assert w.potential_1h_obstacle_source_known_ms==(chosen["source_known_ms"] if chosen else None)
                assert w.author_bos_approved is False
                assert w.author_reaction_approved is False
                assert w.author_fta_approved is False
                assert w.paper_signal_allowed is False
                assert w.orders==w.trades==() and w.readiness=="NOT_TRADE_READY"
                observed.append(asdict(w))
            rs.append({
                "bos":route.bos,"reaction":route.reaction,"fta":route.fta,
                "parent_BOS_source_contexts":route.parent_bos_contexts,
                "with_post_confirmation_source_reaction":route.source_confirmed_reactions,
                "with_preknown_potential_source_obstacle":route.with_preknown_obstacle,
                "with_no_prior_source_touch_observed":route.with_no_prior_touch_observed,
                "original_source_contexts":observed,
                "prior_state_counts":counts,
                "author_entry_or_FTA_approved":False,
                "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"
            })
        assert len(rs)==36
        markets.append({"symbol":symbol,
            "original_closed_native3m":current.source_original3m_closed,
            "native15m_decimal_equalities":full.native_15m_ohlcv_equalities,
            "source_suffix_prefix_equals_physical_cut":True,
            "routes":rs,"orders":0,"trades":0,"readiness":"NOT_TRADE_READY"})
        print(symbol,"36 source combinations, original3m rows:",current.source_original3m_closed,flush=True)
    summaries={}
    for bos in VARIANTS:
        for rx_id in REACTION_VARIANTS:
            for ft_id in FTA_VARIANTS:
                seq=[z for m in markets for z in m["routes"]
                     if (z["bos"],z["reaction"],z["fta"])==(bos,rx_id,ft_id)]
                assert len(seq)==5
                key=bos+"::"+rx_id+"::"+ft_id
                summaries[key]={
                    "correlated_BOS_source_contexts":sum(z["parent_BOS_source_contexts"] for z in seq),
                    "source_reaction_confirmed":sum(z["with_post_confirmation_source_reaction"] for z in seq),
                    "with_preknown_source_obstacle":sum(z["with_preknown_potential_source_obstacle"] for z in seq),
                    "no_prior_touch_observed":sum(z["with_no_prior_source_touch_observed"] for z in seq)}
    obj={
      "schema":"EMBER_C41_ADAPTED_SOURCE_ONLY_FOUR_BOS_THREE_REACTIONS_THREE_FTA_45ZIP_V1",
      "original_C38_git_blob":"a69d69de29d4b52a9ee68ccdf0dbcb20222a6440",
      "original_C39_git_blob":"15dacbe47ba2b6e133d8b97d970a96d6242cd80f",
      "original_C40_git_blob":"718ce971dd781b2046c530992b4c9743225ef5b7",
      "source_original_binance_usdm_zip":45,
      "source_original_native3m_bars":sum(m["original_closed_native3m"] for m in markets),
      "source_native15m_decimal_equalities":sum(m["native15m_decimal_equalities"] for m in markets),
      "bos":list(VARIANTS),"reactions":list(REACTION_VARIANTS),"potential_fta":list(FTA_VARIANTS),
      "source_route_count":36,
      "total_correlated_contexts":sum(z["parent_BOS_source_contexts"] for m in markets for z in m["routes"]),
      "academic_author_goldens":0,"orders":0,"trades":0,
      "readiness":"NOT_TRADE_READY",
      "limitations":"All source observations are correlated. C39 FTA uses retrospective BOS close; C40 prior touches are OHLC not intrabar fills; no author FTA, entry, SL/TP or new unexamined holdout.",
      "summary_by_36_source_route":summaries,"markets":markets}
    assert obj["source_original_native3m_bars"]==76800
    assert obj["source_native15m_decimal_equalities"]==15360
    assert len(summaries)==36
    assert obj["total_correlated_contexts"]==9*(539+462+412+511)
    if output:
        target=Path(output);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if C41_FROZEN.exists():
        assert json.loads(C41_FROZEN.read_text(encoding="utf8"))==json.loads(json.dumps(obj,sort_keys=True)), "C41_FULL_36_SOURCE_JSON_DRIFT"
    print(json.dumps({"summary_by_36":summaries,"contexts":obj["total_correlated_contexts"],
                      "trades":0,"readiness":"NOT_TRADE_READY"},sort_keys=True),flush=True)
    return obj

if __name__=="__main__":
    run(sys.argv[1] if len(sys.argv)>1 else None)
