#!/usr/bin/env python3
"""C37 full original 45 USD-M ZIP independent adapted 3m event scanner.

Actual events independently discovered for each variant on strict native3m,
not selected at frozen C21-latest break timestamps.
No author BOS, no executed paper orders or claimed win-rate.
"""
from dataclasses import asdict,replace
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
for name in ("tests","d05","tools"):
    sys.path.insert(0,str(ROOT/name))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c37_native_adapted_bos_event_scanner import scan_original_3m_adapted
from c36_adapted_pivot_hypotheses import VARIANTS,FROZEN_C33_SHA
from c36_adapted_slot_registry import ACADEMIC_CORE_ID

FROZEN=ROOT/"evidence/c33/C33_ORIGINAL_COMPETING_BOS_PIVOTS_SOURCE.json"
PINNED=ROOT/"evidence/c37/C37_ORIGINAL_FOUR_ADAPTED_NATIVE3M_BOS_EVENTS.json"
EXPECTED_C21={"BCHUSDT":99,"BTCUSDT":104,"ETHUSDT":129,
              "SOLUSDT":103,"XRPUSDT":104}
CUT=OCT_START+DAY+3*THREE

def _context(e):
    return (e.raid_fractal_kind,e.raid_fractal_center_ms,
            e.raid_first_breach_ms,e.raid_confirmed_ms)

def _count_splits(events):
    from c36_adapted_pivot_hypotheses import chronological_partition
    out={"DEVELOPMENT":0,"VALIDATION":0,"HOLDOUT":0}
    for x in events:
        out[chronological_partition(x.break_bar_start_ms)]+=1
    return out

def _compare_against_latest(base,variant):
    m={_context(e):e for e in base}
    n={_context(e):e for e in variant}
    if len(m)!=len(base) or len(n)!=len(variant):
        raise ValueError("C37_DUPLICATE_PARENT_RAID_EVENT")
    common=m.keys()&n.keys()
    return {
        "same_raid_parent_count":len(common),
        "only_frozen_C21_latest_parent":len(m.keys()-n.keys()),
        "only_adapted_variant_parent":len(n.keys()-m.keys()),
        "same_raid_same_closed_3m_break_bar":sum(
            m[k].break_original_native3m_row_id==n[k].break_original_native3m_row_id
            for k in common),
        "same_raid_earlier_adapted_close":sum(
            n[k].break_bar_closed_known_ms<m[k].break_bar_closed_known_ms for k in common),
        "same_raid_later_adapted_close":sum(
            n[k].break_bar_closed_known_ms>m[k].break_bar_closed_known_ms for k in common)
    }

def run(out=None):
    prior=json.loads(FROZEN.read_text(encoding="utf8"))
    expected={x["symbol"]:x["original_c21_parent_edges"] for x in prior["markets"]}
    assert expected==EXPECTED_C21
    markets=[]
    for symbol in sorted(SYMS):
        frames={tf:tuple(load_original(symbol,tf,p,start)[0]
              for p,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htfs=extended_32day_prefix(frames["15m"],frames["1d"],END)
        raw=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        full=reconcile_native_3m(raw,htfs,as_of_ms=END)
        prefix=reconcile_native_3m(raw,htfs,as_of_ms=CUT)
        a=scan_original_3m_adapted(full,as_of_ms=CUT)
        b=scan_original_3m_adapted(prefix,as_of_ms=CUT)
        assert a==b,"C37_ASOF_SUFFIX_LEAK_IN_NATIVE_SOURCE"
        r=scan_original_3m_adapted(full,as_of_ms=END)
        assert r.academic_core_sha256==ACADEMIC_CORE_ID
        assert r.frozen_academic_source_git_blob==FROZEN_C33_SHA
        assert r.source_closed_original3m_bars==15360
        assert len(r.routes)==4
        assert r.latest_replays_frozen_C21
        assert r.original_C21_research_event_count==expected[symbol]
        assert len(r.routes[0].events)==expected[symbol]
        assert r.author_bos_approved==r.paper_signals==0
        assert r.orders==r.trades==()
        rm={}
        baseroute=r.routes[0].events
        for route in r.routes:
            ev=route.events
            original_bars={e.break_original_native3m_row_id for e in ev}
            contexts={_context(e) for e in ev}
            assert len(contexts)==len(ev),"C37_REPEATED_RAID_IN_ROUTE"
            assert all(e.break_bar_closed_known_ms==e.break_bar_start_ms+THREE
                   and e.swing_confirmed_ms<=e.break_bar_start_ms
                   and e.raid_confirmed_ms<=e.break_bar_start_ms
                   and not e.author_bos_approved and not e.paper_trade_allowed
                   and not e.orders and not e.trades for e in ev)
            rm[route.hypothesis_id]={
               "raid_context_event_count":len(ev),
               "unique_original3m_break_bars":len(original_bars),
               "additional_contexts_sharing_price_bar":len(ev)-len(original_bars),
               "chronological_splits":_count_splits(ev),
               "vs_latest_C21":_compare_against_latest(baseroute,ev),
               "native_3m_research_events":[asdict(e) for e in ev],
               "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"
            }
        market={
          "symbol":symbol,"original3m_rows":r.source_closed_original3m_bars,
          "original15m_decimal_equalities":full.native_15m_ohlcv_equalities,
          "original1h_closed":r.source_1h_closed_bars,
          "confirmed_1h_wick_raid_contexts":r.source_confirmed_wick_raids,
          "C21_latest_research_event_count":r.original_C21_research_event_count,
          "physically_truncated_asof_source_equal":True,
          "adapted_routes":rm,"author_selected_bos_goldens":0,
          "trade_approved":0,"orders":0,"trades":0,
          "readiness":"NOT_TRADE_READY"}
        markets.append(market)
        print(symbol,"latest",len(baseroute),"alternatives",{
             v:rm[v]["raid_context_event_count"] for v in VARIANTS[1:]},flush=True)
    total={
      v:{"raid_context_event_count":sum(m["adapted_routes"][v]["raid_context_event_count"]
                   for m in markets),
         "unique_original3m_break_bars":sum(m["adapted_routes"][v]["unique_original3m_break_bars"]
                   for m in markets),
         "additional_raid_contexts_reusing_original3m_bar":sum(
                 m["adapted_routes"][v]["additional_contexts_sharing_price_bar"] for m in markets),
         "chronological_splits":{p:sum(m["adapted_routes"][v]["chronological_splits"][p]
                   for m in markets) for p in ("DEVELOPMENT","VALIDATION","HOLDOUT")},
         "vs_latest_C21":{k:sum(m["adapted_routes"][v]["vs_latest_C21"][k]
                for m in markets) for k in markets[0]["adapted_routes"][v]["vs_latest_C21"]}
         } for v in VARIANTS}
    assert total["LATEST_CONFIRMED_V1"]["raid_context_event_count"]==539
    assert total["LATEST_CONFIRMED_V1"]["unique_original3m_break_bars"]==390
    assert total["LATEST_CONFIRMED_V1"]["additional_raid_contexts_reusing_original3m_bar"]==149
    assert all(s["raid_context_event_count"]>=s["unique_original3m_break_bars"]
              for s in total.values())
    document={
        "schema":"EMBER_C37_INDEPENDENT_ORIGINAL_45ZIP_ADAPTED_3M_BOS_EVENTS_V1",
        "source_original_frozen_C33_git_blob":FROZEN_C33_SHA,
        "source_native3m_usdm_ZIP_files":45,
        "source_closed_original3m_total":sum(m["original3m_rows"] for m in markets),
        "native15m_exact_decimal_equalities":sum(m["original15m_decimal_equalities"] for m in markets),
        "academic_core_id":ACADEMIC_CORE_ID,
        "different_BOS_event_timestamps_not_just_C21_level_substitutions":True,
        "author_selected_bos_goldens":0,
        "paper_signals":0,"orders":0,"trades":0,
        "market_wick_intrabar_execution_observable":False,
        "adapted_competition_not_independent_per_trade":True,
        "performance_untouched_holdout":False,
        "comparison_totals":total,"markets":markets,
        "readiness":"NOT_TRADE_READY"
    }
    assert document["source_closed_original3m_total"]==76800
    assert document["native15m_exact_decimal_equalities"]==15360
    if out:
        f=Path(out);f.parent.mkdir(parents=True,exist_ok=True)
        f.write_text(json.dumps(document,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if PINNED.exists():
        assert json.loads(PINNED.read_text(encoding="utf8"))==document,"C37_FROZEN_FULL_45ZIP_EVENT_JSON_DRIFT"
    print(json.dumps({"totals":total,"status":"NOT_TRADE_READY"},sort_keys=True),flush=True)
    return document

if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
