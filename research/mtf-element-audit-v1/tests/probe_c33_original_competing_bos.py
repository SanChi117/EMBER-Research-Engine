#!/usr/bin/env python3
"""C33 original 45 SHA Binance Futures ZIP BOS swing-competition research only.

Each C21 selected research swing is one of all strict 3m 1+1 swings that
existed before original BOS candle START. Enumeration is not author choice.
No orders or fills.
"""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for folder in ("d05","tools","tests"):sys.path.insert(0,str(ROOT/folder))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c33_preknown_competing_bos_swings import inspect_c33
from c31_bos_entry_semantic_disagreement import inspect_c31_bos

FIELDS=("original_c21_parent_edges","c31_research_singletons",
        "parents_with_multiple_preknown_swings","parents_with_only_one_preknown_swing",
        "total_competing_preknown_swings","max_preknown_competing_swings",
        "proxy_not_latest_preknown","author_approved_bos",
        "orders_created","trades_created")

def main(output=None):
    old=json.loads((ROOT/"evidence/c32/C32_ORIGINAL_DUAL_BOS_ROUTE_SOURCE.json").read_text(encoding="utf8"))
    prior={r["symbol"]:r for r in old["markets"]}
    markets=[]
    for symbol in sorted(SYMS):
        frames={tf:tuple(load_original(symbol,tf,p,start)[0]
            for p,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htfs=extended_32day_prefix(frames["15m"],frames["1d"],END)
        raw=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        source=reconcile_native_3m(raw,htfs,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        truncated=reconcile_native_3m(raw,htfs,as_of_ms=cut)
        assert inspect_c33(source,as_of_ms=cut)==inspect_c33(truncated,as_of_ms=cut),"C33_ORIGINAL_PHYSICALLY_TRUNCATED_SOURCE_DRIFT"
        now=inspect_c33(source,as_of_ms=END)
        c31=inspect_c31_bos(source,as_of_ms=END)
        assert now.original_c21_parent_edges==c31.strict_closed_3m_research_edges==prior[symbol]["strict_c21_parent_edges"]
        assert now.c31_research_singletons==c31.research_single_case_count==prior[symbol]["c31_research_single_cases"]
        assert now.source3m_rows==15360
        assert source.native_15m_ohlcv_equalities==3072
        assert now.orders_created==now.trades_created==now.author_approved_bos==0
        assert now.readiness=="NOT_TRADE_READY"
        cases=[]
        for z in now.cases:
            assert z.original_break3m_source_row_id and z.competing_preknown_swing_count>=1
            assert z.alternative_preknown_swings==z.competing_preknown_swing_count-1
            assert z.proxy_is_latest_preknown
            assert z.instructor_bos_status=="NEEDS_AUTHOR_1H_3M_POSITIVE_NEGATIVE_GOLDENS"
            assert z.order_allowed is False and z.trades==() and z.readiness=="NOT_TRADE_READY"
            assert sum(q.selected_by_frozen_c21_proxy for q in z.competing_swings)==1
            assert all(q.known_ms<=z.break_3m_bar_start_ms and
                       q.center_ms<z.break_3m_bar_start_ms and
                       q.chosen_by_author is False for q in z.competing_swings)
            cases.append(asdict(z))
        market={
            "symbol":symbol,"original_closed_native3m_bars":len(source.original_3m_closed),
            "original_native15m_exact_decimal":source.native_15m_ohlcv_equalities,
            "physically_truncated_source_equal":True,
            "author_3m_BOS_goldens_found":0,
            "source_case_competing_swings":cases
        }
        market.update({key:getattr(now,key) for key in FIELDS})
        markets.append(market)
        print(symbol,"parents",now.original_c21_parent_edges,
             "ambiguous",now.parents_with_multiple_preknown_swings,
             "unique",now.parents_with_only_one_preknown_swing,
             "source competitor relations",now.total_competing_preknown_swings,flush=True)
    totals={k:sum(m[k] for m in markets) if k!="max_preknown_competing_swings"
            else max(m[k] for m in markets) for k in FIELDS}
    doc={
        "schema":"EMBER_C33_ORIGINAL_NATIVE_3M_PREKNOWN_BOS_PIVOT_COMPETITION_V1",
        "original_binance_usdm_zip_count":45,
        "original_native3m_rows":sum(m["original_closed_native3m_bars"] for m in markets),
        "native15m_exact_decimal_equalities":sum(m["original_native15m_exact_decimal"] for m in markets),
        "frozen_previous_original_c32_git_blob":"c3f4186b50af1e1d5bd85505ef0e8ae5d1d67e74",
        "author_bos_source":"https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view",
        "missing_author_2023_goldens":"https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21",
        "source_only_rule":"All original three-bar strict 1+1 3m swings whose right confirmation closed before C21 technical BOS BAR START, whose center is after raid starts and on directionally correct side. C21 latest is merely frozen retrospective research choice. No source labels allow author-approved pivot.",
        "counterfactual_limitation":"Competing technical preknown pivots are NOT valid instructor BOS models; output does not choose valid local reaction, session, FTA, stop or entry. Early source wick is bar OHLC, not trade/tick fill.",
        "totals":totals,"markets":markets,
        "author_selected_BOS_goldens":0,"market_orders":0,"limit_orders":0,
        "orders_created":0,"trades_created":0,"readiness":"NOT_TRADE_READY"
    }
    assert doc["original_binance_usdm_zip_count"]==45
    assert doc["original_native3m_rows"]==76800
    assert doc["native15m_exact_decimal_equalities"]==15360
    assert totals["original_c21_parent_edges"]==539 and totals["c31_research_singletons"]==165
    assert totals["parents_with_only_one_preknown_swing"]+totals["parents_with_multiple_preknown_swings"]==539
    assert totals["proxy_not_latest_preknown"]==0
    assert totals["orders_created"]==totals["trades_created"]==0
    path=ROOT/"evidence/c33/C33_ORIGINAL_COMPETING_BOS_PIVOTS_SOURCE.json"
    if output:
        q=Path(output);q.parent.mkdir(parents=True,exist_ok=True)
        q.write_text(json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if path.exists():
        assert json.loads(path.read_text(encoding="utf8"))==json.loads(json.dumps(doc,sort_keys=True,ensure_ascii=False)),"C33_FULL_PINNED_ORIGINAL_JSON_DRIFT"
    print(json.dumps({"totals":totals,"readiness":"NOT_TRADE_READY"},sort_keys=True),flush=True)
    return doc

if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
