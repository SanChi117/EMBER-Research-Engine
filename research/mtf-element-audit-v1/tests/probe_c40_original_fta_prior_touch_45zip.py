#!/usr/bin/env python3
"""C40 source-only prior touches for C39 FTA on all original 45 USD-M ZIP.

Every source 1H obstacle is reconstructed and proved from native 3m bars.
Any touch/full gap traversal must CLOSE before independently generated C37
BOS bar START. Zero author freshness labels, orders or trades.
"""
import json,sys
from pathlib import Path
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
for sub in ("tests","d05","tools"):sys.path.insert(0,str(ROOT/sub))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c40_pre_bos_fta_touch_state import inspect_original_fta_prior_touch,STATES
from c36_adapted_pivot_hypotheses import VARIANTS
from c39_adapted_preknown_fta_source import FTA_VARIANTS

PRIOR_PATH=ROOT/"evidence/c39/C39_ORIGINAL_FOUR_BOS_BY_THREE_POTENTIAL_FTA.json"
FROZEN_PATH=ROOT/"evidence/c40/C40_ORIGINAL_PRE_BOS_PRIOR_FTA_TOUCH_STATES.json"
C39_SHA="15dacbe47ba2b6e133d8b97d970a96d6242cd80f"

def run(output=None):
    predecessor=json.loads(PRIOR_PATH.read_text(encoding="utf8"))
    old={m["symbol"]:m for m in predecessor["markets"]}
    result=[]
    for symbol in sorted(SYMS):
        raw={tf:tuple(load_original(symbol,tf,part,at)[0]
            for part,at in zip(DATES,STARTS)) for tf in ("15m","1d")}
        high=extended_32day_prefix(raw["15m"],raw["1d"],END)
        three=tuple(native_3m(symbol,part)[0] for part in PERIODS)
        s=reconcile_native_3m(three,high,as_of_ms=END)
        current=inspect_original_fta_prior_touch(s,as_of_ms=END)
        assert current["source_original3m_rows"]==15360 and current["route_count"]==12
        assert current["readiness"]=="NOT_TRADE_READY"
        assert current["author_fta_freshness_goldens"]==0
        assert current["orders"]==current["trades"]==()
        by_prior={(r["bos_hypothesis_id"],r["fta_hypothesis_id"]):r
                  for r in old[symbol]["bos_by_potential_fta_routes"]}
        entries=[]
        for route in current["routes"]:
            key=(route["bos"],route["fta"])
            prior=by_prior[key]
            states=route["states"]
            assert set(states)==set(STATES)
            assert route["contexts"]==prior["source_BOS_raid_contexts"]
            assert sum(states.values())==route["contexts"]
            assert states["NO_PREKNOWN_FTA_CANDIDATE"]==prior["contexts_without_potential_obstacle"]
            asserts=[]
            for w in route["observations"]:
                if w.first_touch_bar_ms is not None:
                    assert w.first_touch_original3m_row_id is not None
                if w.first_full_sweep_or_traversal_ms is not None:
                    assert w.first_touch_bar_ms is not None
                assert w.author_freshness_certified is False
                assert w.author_target_certified is False
                assert w.order_approval is False
                assert w.orders==w.trades==()
                assert w.readiness=="NOT_TRADE_READY"
                asserts.append(asdict(w))
            entries.append({
              "bos":route["bos"],"fta":route["fta"],
              "research_parent_contexts":route["contexts"],
              "source_prior_interaction_states":states,
              "source_review":asserts,
              "author_fta_approval":False,
              "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"
            })
        assert len(entries)==12
        result.append({"symbol":symbol,
           "original_closed_native3m":current["source_original3m_rows"],
           "native15m_original_parity":s.native_15m_ohlcv_equalities,
           "routes":entries,
           "orders":0,"trades":0,"author_goldens":0,
           "readiness":"NOT_TRADE_READY"})
        print(symbol,"source prior state:",[(r["bos"].split("_")[0],
             r["fta"].split("_")[0],r["source_prior_interaction_states"]) for r in entries],flush=True)
    summary={}
    for b in VARIANTS:
        for f in FTA_VARIANTS:
            m=[q for k in result for q in k["routes"] if q["bos"]==b and q["fta"]==f]
            assert len(m)==5
            summary[b+"::"+f]={state:sum(x["source_prior_interaction_states"][state] for x in m)
                    for state in STATES}
            assert sum(summary[b+"::"+f].values())==sum(x["research_parent_contexts"] for x in m)
    doc={
      "schema":"EMBER_C40_ORIGINAL_1H_FTA_PRIOR_TOUCH_NATIVE3M_45ZIP_V1",
      "prior_C39_frozen_source_blob":C39_SHA,
      "source_original_45_usdm_zip":45,
      "original_closed_native3m":sum(m["original_closed_native3m"] for m in result),
      "native15m_exact_decimal":sum(m["native15m_original_parity"] for m in result),
      "bos":list(VARIANTS),"fta":list(FTA_VARIANTS),
      "route_count":12,
      "prior_source_state_warning":"All wick interactions are native3m bar-OHLC, not fills/ticks. NO_PRIOR_TOUCH_OBSERVED only within inspected source time window. Does not certify academic author unswept FTA or realistic TP.",
      "original_author_freshness_goldens":0,
      "orders":0,"trades":0,"readiness":"NOT_TRADE_READY",
      "summary_by_route":summary,"markets":result}
    assert doc["original_closed_native3m"]==76800
    assert doc["native15m_exact_decimal"]==15360
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if FROZEN_PATH.exists():
        assert json.loads(FROZEN_PATH.read_text(encoding="utf8"))==json.loads(json.dumps(doc,sort_keys=True)), "C40_FROZEN_FULL_SOURCE_JSON_DRIFT"
    print(json.dumps({"states":summary,"trades":0,"readiness":"NOT_TRADE_READY"},sort_keys=True))
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
