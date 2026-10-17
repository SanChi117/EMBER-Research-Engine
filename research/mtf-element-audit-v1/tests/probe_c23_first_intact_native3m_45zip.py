#!/usr/bin/env python3
"""C23: independently original 45 Futures ZIP prove known-then-first-closed-pivot.

Maintains C21B/C22B evidence frozen. Never infer exact author pivot.
"""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):sys.path.insert(0,str(p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c23_first_intact_pivot_guard import inspect_first_intact_pivots

COUNTS=("original_parent_edges","total_eligible_before_first_break_test",
        "previously_close_broken_levels","previously_wick_breached_levels",
        "still_close_intact_levels","first_close_crossing_levels",
        "first_close_single_candidate_edges","first_close_multiple_candidate_edges",
        "no_first_close_candidate_edges","chosen_latest_proxy_previously_close_broken",
        "first_close_multiple_parent_bar_edges")

def replay():
    pinned=json.loads((ROOT/"evidence"/"c22"/"C22B_ORIGINAL_PIVOT_ALTERNATIVES.json").read_text())
    expected={x["symbol"]:x for x in pinned["observations"]}
    result=[]
    for symbol in sorted(SYMS):
        source={}
        for tf in ("15m","1d"):
            source[tf]=tuple(load_original(symbol,tf,p,t)[0]
                             for p,t in zip(DATES,STARTS))
        reference=extended_32day_prefix(source["15m"],source["1d"],END)
        archives=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        original=reconcile_native_3m(archives,reference,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        truncated=reconcile_native_3m(archives,reference,as_of_ms=cut)
        earlier=inspect_first_intact_pivots(original,as_of_ms=cut)
        independent=inspect_first_intact_pivots(truncated,as_of_ms=cut)
        assert earlier==independent,"C23_NATIVE3M_ORIGINAL_PREFIX_DRIFT"
        observed=inspect_first_intact_pivots(original,as_of_ms=END)
        assert observed.original_parent_edges==expected[symbol]["observed_parent_edges"]
        assert observed.total_eligible_before_first_break_test==expected[symbol]["eligible_pivot_options"]
        assert original.native_15m_ohlcv_equalities==3072
        assert observed.approved_trades==observed.author_selected_pivots==0
        result.append({
          "symbol":symbol,
          "original_source_3m_bars":len(original.original_3m_closed),
          "original_15m_parity":original.native_15m_ohlcv_equalities,
          "source_earlier_prefix_invariant":True,
          **{name:getattr(observed,name) for name in COUNTS},
          "ten_original_research_witnesses":list(observed.examples)})
        print(symbol,"historical eligible",observed.total_eligible_before_first_break_test,
            "retired closed",observed.previously_close_broken_levels,
            "first-close singles",observed.first_close_single_candidate_edges,
            "first-close multiples",observed.first_close_multiple_candidate_edges,flush=True)
    return result

def main(target=None):
    rows=replay()
    totals={name:sum(x[name] for x in rows) for name in COUNTS}
    result={"schema":"EMBER_C23_FIRST_INTACT_NATIVE3M_SOURCE_V1",
       "period_utc":["2026-09-01","2026-10-02"],
       "original_3m_and_15m_1d_zip":45,
       "original_3m_closed":sum(x["original_source_3m_bars"] for x in rows),
       "original_native15m_equalities":sum(x["original_15m_parity"] for x in rows),
       "original_source_results":rows,"totals":totals,
       "author_timestamp_bos_goldens":0,"author_approved_trades":0,
       "readiness":"NOT_TRADE_READY"}

    assert result["original_3m_closed"]==76800
    assert result["original_native15m_equalities"]==15360
    assert totals["original_parent_edges"]==539
    assert totals["total_eligible_before_first_break_test"]==3393
    assert totals["previously_close_broken_levels"]+totals["still_close_intact_levels"]==3393
    assert totals["first_close_single_candidate_edges"]+totals["first_close_multiple_candidate_edges"]+totals["no_first_close_candidate_edges"]==539

    pin=ROOT/"evidence"/"c23"/"C23_ORIGINAL_FIRST_INTACT_PIVOT_RESULT.json"
    if pin.exists():
        assert json.loads(pin.read_text(encoding="utf8"))==result,"C23_ORIGINAL_SOURCE_PINNED_DRIFT"
    if target:
        Path(target).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)
if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv)>1 else None)
