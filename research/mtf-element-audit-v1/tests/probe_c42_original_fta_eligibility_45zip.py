#!/usr/bin/env python3
"""C42 full original 45 Binance USD-M ZIP, 36 source routes x 3 policies.

No new BOS/FTA/Reaction events or trades. Interpret only C40 prior-touches
of C41 frozen parent, original3m as-of and C39 retrospective ranking.
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
from c42_adapted_source_fta_eligibility import scan_original_source_eligibility,ELIGIBILITY_POLICIES

PARENT=ROOT/"evidence/c41/C41_ORIGINAL_36_SOURCE_JOIN_MATRIX.json"
PINNED=ROOT/"evidence/c42/C42_ORIGINAL_SOURCE_FTA_ELIGIBILITY_45ZIP.json"
PARENT_SHA="ac3bb2b2babafdb28af71c4cbaa2b53fce03b06c"
CUT=OCT_START+DAY+3*THREE

def run(out=None):
    parent=json.loads(PARENT.read_text(encoding="utf8"))
    assert parent["source_route_count"]==36
    old={m["symbol"]:m for m in parent["markets"]}
    markets=[]
    for symbol in sorted(SYMS):
        raw={tf:tuple(load_original(symbol,tf,part,at)[0]
           for part,at in zip(DATES,STARTS)) for tf in ("15m","1d")}
        hours=extended_32day_prefix(raw["15m"],raw["1d"],END)
        orig3=tuple(native_3m(symbol,part)[0] for part in PERIODS)
        full=reconcile_native_3m(orig3,hours,as_of_ms=END)
        cut=reconcile_native_3m(orig3,hours,as_of_ms=CUT)
        early=scan_original_source_eligibility(full,as_of_ms=CUT)
        physical=scan_original_source_eligibility(cut,as_of_ms=CUT)
        assert early==physical,"C42_PHYSICALLY_CUT_SOURCE_SUFFIX_DRIFT"
        now=scan_original_source_eligibility(full,as_of_ms=END)
        assert len(now.routes)==now.parent_route_count==36
        assert now.source_original3m_closed==15360
        assert now.author_fta_goldens==0 and now.orders==now.trades==()
        assert now.readiness=="NOT_TRADE_READY"
        assert full.native_15m_ohlcv_equalities==3072
        old_route={(v["bos"],v["reaction"],v["fta"]):v for v in old[symbol]["routes"]}
        assert len(old_route)==36
        rows=[]
        for route in now.routes:
            key=(route.bos,route.reaction,route.fta)
            reference=old_route[key]
            assert len(reference["original_source_contexts"])==route.parent_contexts
            assert route.parent_contexts==reference["parent_BOS_source_contexts"]
            baseline,strict,untouched=(route.policy_eligible_counts[p] for p in ELIGIBILITY_POLICIES)
            states=reference["prior_state_counts"]
            assert baseline==route.parent_contexts-states["NO_PREKNOWN_FTA_CANDIDATE"]
            assert strict==baseline-states["PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL"]
            assert untouched==states["NO_PRIOR_SOURCE_TOUCH"]
            assert baseline>=strict>=untouched
            reviews=[]
            for current,previous in zip(route.observations,reference["original_source_contexts"]):
                assert current.original_bos_native3m_row_id==previous["original_bos_native3m_row_id"]
                assert current.original_raid_fractal_center_ms==previous["original_raid_fractal_center_ms"]
                assert current.bos_bar_start_ms==previous["bos_bar_start_ms"]
                assert current.bos_bar_closed_known_ms==previous["bos_bar_closed_known_ms"]
                assert current.potential_obstacle_kind==previous["potential_1h_obstacle_kind"]
                assert current.potential_obstacle_known_ms==previous["potential_1h_obstacle_source_known_ms"]
                assert current.observed_prior_touch_state==previous["source_prior_touch_classification"]
                assert current.prior_touch_original3m_row_id==previous["first_prior_touch_original_native3m_row_id"]
                assert current.author_freshness_approved is False
                assert current.orders==current.trades==() and current.readiness=="NOT_TRADE_READY"
                assert tuple(d.hypothesis_id for d in current.decisions)==ELIGIBILITY_POLICIES
                assert all(not d.order_allowed and not d.author_target_approved and
                    not d.author_fta_freshness_approved and
                    d.decision_known_at_ms==current.bos_bar_closed_known_ms
                    for d in current.decisions)
                reviews.append(asdict(current))
            rows.append({
              "bos":route.bos,"reaction":route.reaction,"fta":route.fta,
              "parent_correlated_source_contexts":route.parent_contexts,
              "source_state_counts":states,
              "eligible_counts_by_explicit_adapted_policy":route.policy_eligible_counts,
              "source_context_eligibility_observations":reviews,
              "author_fta_eligibility_approved":False,
              "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"
            })
        assert len(rows)==36
        markets.append({"symbol":symbol,"original_closed_native3m":now.source_original3m_closed,
            "native15m_exact_decimal":full.native_15m_ohlcv_equalities,
            "prefix_physically_cut_equal":True,
            "source_routes":rows,"orders":0,"trades":0,"readiness":"NOT_TRADE_READY"})
        print(symbol,"36 x 3 adapted source eligibility research policy outcomes",flush=True)
    by_policy={p:sum(route["eligible_counts_by_explicit_adapted_policy"][p]
       for market in markets for route in market["source_routes"])
       for p in ELIGIBILITY_POLICIES}
    total=sum(route["parent_correlated_source_contexts"]
              for market in markets for route in market["source_routes"])
    assert total==17316
    assert by_policy[ELIGIBILITY_POLICIES[0]]>=by_policy[ELIGIBILITY_POLICIES[1]]>=by_policy[ELIGIBILITY_POLICIES[2]]
    doc={
       "schema":"EMBER_C42_ADAPTED_SOURCE_FTA_ELIGIBILITY_4BOS_3REACTION_3FTA_45ZIP_V1",
       "parent_C41_git_blob":PARENT_SHA,
       "original_source_usdm_45zip":45,
       "original_closed_native3m":sum(m["original_closed_native3m"] for m in markets),
       "native15m_decimal_equalities":sum(m["native15m_exact_decimal"] for m in markets),
       "parent_correlated_source_contexts":total,
       "route_count":36,"eligibility_policy_count":len(ELIGIBILITY_POLICIES),
       "eligibility_policies":list(ELIGIBILITY_POLICIES),
       "policy_counts_across_correlated_routes":by_policy,
       "author_source_fta_freshness_goldens":0,"orders":0,"trades":0,
       "readiness":"NOT_TRADE_READY",
       "limitations":"No lifetime 1H level freshness before Sep 2026; source 3m OHLC is not intrabar tick/fill. All policies are ADAPTED. C39 selected candidate relies on retrospective BOS CLOSE, so the decision is NOT known by BOS START; no author approved FTA, entry, SL/TP, trade returns, OOS.",
       "markets":markets
    }
    assert doc["original_closed_native3m"]==76800
    assert doc["native15m_decimal_equalities"]==15360
    if out:
        target=Path(out);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if PINNED.exists():
        assert json.loads(PINNED.read_text(encoding="utf8"))==json.loads(json.dumps(doc,sort_keys=True)), "C42_ENTIRE_45ZIP_SOURCE_POLICY_JSON_DRIFT"
    print(json.dumps({"counts":by_policy,"contexts":total,"trades":0,"readiness":"NOT_TRADE_READY"},
        sort_keys=True),flush=True)
    return doc

if __name__=="__main__":
    run(sys.argv[1] if len(sys.argv)>1 else None)
