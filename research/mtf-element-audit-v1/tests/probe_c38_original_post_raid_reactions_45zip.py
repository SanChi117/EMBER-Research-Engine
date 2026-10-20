#!/usr/bin/env python3
"""C38 all original 45 USD-M ZIP: 4 BOS × 3 independent pre-BOS reaction probes.

Research-only synthetic definitions. All reaction witness source3m candles
must have closed BEFORE each *independently* generated C37 BOS bar START.
No 2023 author positive goldens, no entries, ticks, stops or orders.
"""
import json,sys
from pathlib import Path
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
for name in ("tests","d05","tools"):sys.path.insert(0,str(ROOT/name))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c38_adapted_post_raid_reaction import (
    scan_adapted_reactions,REACTION_VARIANTS)
from c36_adapted_pivot_hypotheses import VARIANTS,chronological_partition
from c36_adapted_slot_registry import ACADEMIC_CORE_ID

C37_PINNED=ROOT/"evidence/c37/C37_ORIGINAL_FOUR_ADAPTED_NATIVE3M_BOS_EVENTS.json"
C38_PINNED=ROOT/"evidence/c38/C38_ORIGINAL_FOUR_BOS_BY_THREE_REACTION_MATRIX.json"
SOURCE_BLOB="e4b702e8c6cdc34f1c2475df73ef44ae1631fe56"
CUTOFF=OCT_START+DAY+3*THREE

def run(out=None):
    previous=json.loads(C37_PINNED.read_text(encoding="utf8"))
    old={m["symbol"]:m for m in previous["markets"]}
    markets=[]
    for symbol in sorted(SYMS):
        frames={tf:tuple(load_original(symbol,tf,p,start)[0]
               for p,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htfs=extended_32day_prefix(frames["15m"],frames["1d"],END)
        raw=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        full=reconcile_native_3m(raw,htfs,as_of_ms=END)
        prefix=reconcile_native_3m(raw,htfs,as_of_ms=CUTOFF)
        before=scan_adapted_reactions(full,as_of_ms=CUTOFF)
        physically=scan_adapted_reactions(prefix,as_of_ms=CUTOFF)
        assert before==physically,"C38_NATIVE_REACTION_SUFFIX_LOOKAHEAD"
        r=scan_adapted_reactions(full,as_of_ms=END)
        assert r.academic_core_id==ACADEMIC_CORE_ID
        assert r.original_closed_3m_bars==15360
        assert r.reaction_hypotheses==REACTION_VARIANTS
        assert r.bos_hypotheses==VARIANTS
        assert len(r.routes)==12
        assert r.author_reaction_goldens==r.author_bos_goldens==0
        assert r.orders==r.trades==()
        market_routes=[]
        for route in r.routes:
            assert route.total_bos_parent_contexts==old[symbol]["adapted_routes"][route.bos_hypothesis_id]["raid_context_event_count"]
            assert route.observed_with_prior_reaction+route.observed_without_prior_reaction==route.total_bos_parent_contexts
            assert len(route.observations)==route.total_bos_parent_contexts
            ids=set()
            partition={"DEVELOPMENT":0,"VALIDATION":0,"HOLDOUT":0}
            for event in route.observations:
                assert event.reaction_hypothesis_id==route.reaction_hypothesis_id
                assert event.bos_hypothesis_id==route.bos_hypothesis_id
                assert not event.author_reaction_verified and not event.author_bos_verified
                assert not event.paper_signal_allowed and not event.orders and not event.trades
                assert event.readiness=="NOT_TRADE_READY"
                if event.condition_satisfied:
                    assert event.first_confirmed_reaction_bar_closed_ms<=event.bos_break_bar_start_ms
                    assert event.first_confirmed_reaction_bar_closed_ms>0
                    assert event.first_confirmed_native3m_row_id!=event.original_bos_break_row_id
                    assert event.first_confirmed_native3m_row_id
                    ids.add(event.first_confirmed_native3m_row_id)
                    partition[chronological_partition(event.bos_break_bar_start_ms)]+=1
                else:
                    assert event.first_confirmed_native3m_row_id is None
                    assert event.first_confirmed_reaction_bar_closed_ms is None
            market_routes.append({
              "bos_hypothesis_id":route.bos_hypothesis_id,
              "reaction_hypothesis_id":route.reaction_hypothesis_id,
              "bos_research_parent_events":route.total_bos_parent_contexts,
              "with_prior_reaction":route.observed_with_prior_reaction,
              "without_prior_reaction":route.observed_without_prior_reaction,
              "unique_original3m_reaction_witness_bars":len(ids),
              "reaction_satisfied_partition":partition,
              "source_research_observations":[asdict(x) for x in route.observations],
              "author_approved_entry":False,
              "paper_signals":0,"orders":0,"trades":0,
              "readiness":"NOT_TRADE_READY"
            })
        markets.append({
           "symbol":symbol,
           "original_closed_native3m":r.original_closed_3m_bars,
           "native15m_decimal_equalities":full.native_15m_ohlcv_equalities,
           "original_asof_prefix_physically_equal":True,
           "bos_reaction_matrix":market_routes,
           "author_reaction_goldens":0,
           "author_bos_goldens":0,"orders":0,"trades":0,
           "readiness":"NOT_TRADE_READY"
        })
        print(symbol,"12 combinations",[
          (z["bos_hypothesis_id"].split("_")[0],
           z["reaction_hypothesis_id"].replace("POST_CONFIRM_","").split("_")[0],
           z["with_prior_reaction"]) for z in market_routes],flush=True)
    totals={}
    for bos in VARIANTS:
        for reaction in REACTION_VARIANTS:
            matching=[r for m in markets for r in m["bos_reaction_matrix"]
                if r["bos_hypothesis_id"]==bos and r["reaction_hypothesis_id"]==reaction]
            assert len(matching)==5
            key=bos+"::"+reaction
            totals[key]={
              "bos_research_parent_events":sum(x["bos_research_parent_events"] for x in matching),
              "with_prior_reaction":sum(x["with_prior_reaction"] for x in matching),
              "without_prior_reaction":sum(x["without_prior_reaction"] for x in matching),
              "unique_witness_source_bars_sum_across_markets":sum(
                   x["unique_original3m_reaction_witness_bars"] for x in matching),
              "reaction_satisfied_partition":{
                 p:sum(x["reaction_satisfied_partition"][p] for x in matching)
                 for p in ("DEVELOPMENT","VALIDATION","HOLDOUT")}
            }
            assert totals[key]["bos_research_parent_events"]==(
                 totals[key]["with_prior_reaction"]+totals[key]["without_prior_reaction"])
    obj={
      "schema":"EMBER_C38_ADAPTED_4_BOS_BY_3_POST_CONFIRM_REACTIONS_ORIGINAL_45ZIP_V1",
      "original_C37_source_git_blob":SOURCE_BLOB,
      "parent_C37_original_research_events":sum(
          m["adapted_routes"]["LATEST_CONFIRMED_V1"]["raid_context_event_count"]
          for m in old.values()),
      "original_USDM_SHA_ZIP_count":45,
      "original_closed_native3m_count":sum(m["original_closed_native3m"] for m in markets),
      "original15m_decimal_parities":sum(m["native15m_decimal_equalities"] for m in markets),
      "hypothesis_count":12,
      "bos_variants":list(VARIANTS),
      "reaction_variants":list(REACTION_VARIANTS),
      "reaction_scope":"ONLY_SOURCE3M_CLOSES_AFTER_FULL_1H_RAID_CONFIRMATION_AND_BEFORE_BOS_BREAK_START",
      "author_reaction_fidelity":"UNKNOWN_NOT_2023_INSTRUCTOR_GOLDENS",
      "independent_price_fill_available":False,
      "source_reactions_not_independent_trades":True,
      "author_approved_reactions":0,
      "author_approved_bos":0,
      "order_submissions":0,"trades":0,
      "readiness":"NOT_TRADE_READY",
      "summary_by_combination":totals,
      "markets":markets}
    assert obj["parent_C37_original_research_events"]==539
    assert obj["original_closed_native3m_count"]==76800
    assert obj["original15m_decimal_parities"]==15360
    if out:
        p=Path(out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if C38_PINNED.exists():
        assert json.loads(C38_PINNED.read_text(encoding="utf8"))==json.loads(json.dumps(obj,sort_keys=True)),"C38_ORIGINAL_SOURCE_FULL_MATRIX_DRIFT"
    print(json.dumps({"reaction_summary":totals,"readiness":"NOT_TRADE_READY"},sort_keys=True),flush=True)
    return obj

if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
