#!/usr/bin/env python3
"""C32 45 original Futures ZIP original dual-route SOURCE ONLY, NO orders."""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for d in ("d05","tools","tests"):sys.path.insert(0,str(ROOT/d))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c32_dual_bos_route_source import inspect_c32
from c31_bos_entry_semantic_disagreement import inspect_c31_bos

FIELDS=("strict_c21_parent_edges","c31_research_single_cases",
        "prior_wick_reach_before_3m_bos_close",
        "prior_wick_reach_before_3m_bos_bar",
        "cross_bar_also_exceeded_raid_extreme",
        "first_cross_bar_did_not_close_beyond_pivot",
        "closed_3m_bos_observed","author_market_cross_approved",
        "author_limit_retest_approved","orders_created","trades_created")
def main(output=None):
    frozen=json.loads((ROOT/"evidence/c31/C31_ORIGINAL_BOS_CROSS_VS_CLOSE_SOURCE.json").read_text(encoding="utf8"))
    c31_lookup={x["symbol"]:x for x in frozen["markets"]}
    markets=[]
    for symbol in sorted(SYMS):
        archive={tf:tuple(load_original(symbol,tf,p,start)[0]
                          for p,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(archive["15m"],archive["1d"],END)
        raw=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        source=reconcile_native_3m(raw,htf,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        trunc=reconcile_native_3m(raw,htf,as_of_ms=cut)
        assert inspect_c32(source,as_of_ms=cut)==inspect_c32(trunc,as_of_ms=cut),"C32_SOURCE_PHYSICAL_PREFIX_ASOF_DRIFT"
        r=inspect_c32(source,as_of_ms=END)
        p=inspect_c31_bos(source,as_of_ms=END)
        f=c31_lookup[symbol]
        assert r.strict_c21_parent_edges==p.strict_closed_3m_research_edges==f["strict_closed_3m_research_edges"]
        assert r.c31_research_single_cases==p.research_single_case_count==f["research_single_case_count"]
        assert r.prior_wick_reach_before_3m_bos_close==p.edges_with_prior_strict_wick_cross
        assert len(source.original_3m_closed)==15360 and source.native_15m_ohlcv_equalities==3072
        assert r.author_market_cross_approved==r.author_limit_retest_approved==r.orders_created==r.trades_created==0
        assert r.readiness=="NOT_TRADE_READY"
        cases=[]
        for c in r.cases:
            assert not c.author_route_approved and c.chosen_route=="NONE_UNTIL_AUTHOR_SOURCE_ATTESTED"
            assert c.readiness=="NOT_TRADE_READY" and not c.orders and not c.trades
            assert c.market_cross.market_order_allowed is False
            assert c.market_cross.actual_tick_cross_ms is None
            assert c.market_cross.simulated_fill_price is None
            assert c.market_cross.first_source_wick_reach_known_ms<=c.close_then_limit.selected_close_known_ms
            assert c.close_then_limit.limit_order_allowed is False
            assert c.close_then_limit.author_limit_price is None
            assert c.close_then_limit.author_limit_expiry is None
            assert c.close_then_limit.inferred_retest_fill is None
            assert c.close_then_limit.selected_close_known_ms==c.close_then_limit.earliest_possible_order_after_ms
            cases.append(asdict(c))
        market={
          "symbol":symbol,"original_native3m_rows":len(source.original_3m_closed),
          "native15m_original_decimal_equalities":source.native_15m_ohlcv_equalities,
          "physically_truncated_source_equal":True,
          "author_approved_bos":0
        }
        market.update({k:getattr(r,k) for k in FIELDS})
        market["dual_route_research_only_observations"]=cases
        markets.append(market)
        print(symbol,"539-subset source edges",r.strict_c21_parent_edges,
              "prior price wick reaches",r.prior_wick_reach_before_3m_bos_bar,
              "first-price-reach-no-close",r.first_cross_bar_did_not_close_beyond_pivot,
              "orders",r.orders_created,flush=True)
    totals={k:sum(m[k] for m in markets) for k in FIELDS}
    receipt={
      "schema":"EMBER_C32_DUAL_BOS_ROUTE_OHLC_NOT_AN_EXECUTION_V1",
      "original_binance_usdm_zip_count":45,
      "original_native3m_closed":sum(x["original_native3m_rows"] for x in markets),
      "native15m_exact_decimal_equalities":sum(x["native15m_original_decimal_equalities"] for x in markets),
      "frozen_original_c31_git_blob":"38276d6d8a77942101a041d3605d72f69a7845d1",
      "direct_author_bos_lesson":"https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view",
      "original_author_2023_not_accessible":"https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21",
      "scope":"First original 3m OHLC wick reach of C21-selected research swing versus first confirmed original 3m BOS close; never infer true tick order, market/limit fills, author BOS swing, stop or target. All observations use source as-of.",
      "source_restrictions":{
        "market":"No tick feed, bid/ask, author selected pivot or risk target; first source candle high/low is not executable time nor price",
        "close_then_limit":"C21 strict 3m close is observed; original instructor limit level, retracement, expiry and fill all unknown",
        "same_bar_stop_and_entry":"OHLC cannot determine which was first; never resolve in favor of a trade",
        "author_status":"NOT_TRADE_READY",
        "orders_created":0,"trades_created":0
      },
      "totals":totals,"markets":markets,
      "author_market_trade_approved":0,"author_limit_trade_approved":0,
      "approved_orders":0,"approved_trades":0,
      "readiness":"NOT_TRADE_READY"
    }
    assert receipt["original_binance_usdm_zip_count"]==45
    assert receipt["original_native3m_closed"]==76800
    assert receipt["native15m_exact_decimal_equalities"]==15360
    assert totals["strict_c21_parent_edges"]==539 and totals["c31_research_single_cases"]==165
    assert totals["prior_wick_reach_before_3m_bos_bar"]==122
    assert totals["prior_wick_reach_before_3m_bos_close"]==122
    assert totals["closed_3m_bos_observed"]==539
    assert totals["author_market_cross_approved"]==totals["author_limit_retest_approved"]==0
    assert totals["orders_created"]==totals["trades_created"]==0
    pin=ROOT/"evidence/c32/C32_ORIGINAL_DUAL_BOS_ROUTE_SOURCE.json"
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(receipt,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if pin.exists():
        assert json.loads(pin.read_text(encoding="utf8"))==json.loads(json.dumps(receipt,sort_keys=True,ensure_ascii=False)),"C32_ORIGINAL_PINNED_FULL_JSON_DRIFT"
    print(json.dumps({"totals":totals,"readiness":"NOT_TRADE_READY"},sort_keys=True),flush=True)
    return receipt
if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
