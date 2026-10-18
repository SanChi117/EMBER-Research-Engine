#!/usr/bin/env python3
"""C31 full 45 original USD-M ZIP: first wick vs 3m close BOS proxy disagreement.

This is a forensic source-only replay, not an author BOS detector or trades.
"""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for d in ("d05","tools","tests"):sys.path.insert(0,str(ROOT/d))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c31_bos_entry_semantic_disagreement import inspect_c31_bos
from c25_session_freshness_target_source import inspect_c25

FIELDS=("strict_closed_3m_research_edges","research_single_case_count",
    "proxy_raid_fractal_bos_order_pass","edges_with_prior_strict_wick_cross",
    "prior_strict_wick_cross_observations",
    "edges_with_prior_wick_without_close_confirmation",
    "edges_with_prior_closed_beyond_selected_swing",
    "break_at_raid_confirmation_hour_count",
    "break_later_than_3h_after_raid_confirmation")

def main(output=None):
    markets=[]
    for symbol in sorted(SYMS):
        frames={tf:tuple(load_original(symbol,tf,p,start)[0]
                       for p,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(frames["15m"],frames["1d"],END)
        original=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        source=reconcile_native_3m(original,htf,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        trunc=reconcile_native_3m(original,htf,as_of_ms=cut)
        assert inspect_c31_bos(source,as_of_ms=cut)==inspect_c31_bos(trunc,as_of_ms=cut),"C31_CAUSAL_PHYSICAL_PREFIX_DRIFT"
        review=inspect_c31_bos(source,as_of_ms=END)
        prior=inspect_c25(source,as_of_ms=END)
        assert review.strict_closed_3m_research_edges==prior.original_parent_edges
        assert review.research_single_case_count==prior.research_single_parent_cases
        assert review.source_original3m_closed==15360
        assert source.native_15m_ohlcv_equalities==3072
        assert review.author_annotated_1h3m_goldens==review.author_approved_trades==0
        assert review.readiness=="NOT_TRADE_READY"
        cases=[]
        for w in review.cases:
            assert w.strictly_bos_side_of_raid_fractal
            assert w.research_break_close_known_ms==w.research_break_start_ms+THREE
            assert w.selected_3m_swing_known_ms<=w.research_break_start_ms
            assert w.raid_confirmed_ms<=w.research_break_start_ms
            assert w.earlier_wick_cross_count>=w.earlier_wick_without_confirmed_bos_count
            assert w.earlier_wick_cross_count>=w.earlier_close_beyond_bos_level_count
            assert w.readiness=="NOT_TRADE_READY"
            assert w.academic_bos_pivot_status=="AUTHOR_SELECTED_BOS_PIVOT_UNKNOWN"
            cases.append(asdict(w))
        market={"symbol":symbol,
            "original_native3m_closed":len(source.original_3m_closed),
            "native15m_decimal_equalities":source.native_15m_ohlcv_equalities,
            "source_physically_truncated_asof_equal":True,
            "author_bos_labeled_examples":0,
            "previous_day_calendar_hypothesis_only":dict(review.previous_calendar_day_hypotheses)}
        market.update({k:getattr(review,k) for k in FIELDS})
        market["research_only_3m_bos_witnesses"]=cases
        markets.append(market)
        print(symbol,"research BOS edges",review.strict_closed_3m_research_edges,
             "prior wick",review.edges_with_prior_strict_wick_cross,
             "prior wick-no-close",review.edges_with_prior_wick_without_close_confirmation,
             "prior close",review.edges_with_prior_closed_beyond_selected_swing,flush=True)
    totals={k:sum(x[k] for x in markets) for k in FIELDS}
    receipt={
        "schema":"EMBER_C31_ORIGINAL_BOS_WICK_VS_CLOSED_PRICE_SOURCE_V1",
        "source_original_zip_count":45,
        "source_original3m_bars":sum(x["original_native3m_closed"] for x in markets),
        "original_native15m_exact_decimal_equalities":sum(x["native15m_decimal_equalities"] for x in markets),
        "original_instructor_lesson":"https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view",
        "instructor_linked_goldens_not_accessible":"https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21",
        "technical_scope":"For EACH research-selected 3m swing compare any prior strict price wick penetration known on CLOSED original 3m candles after raid+selected swing confirmed, versus later first C21 close signal. This is retrospective pivot-index comparison, not author crossing entry/tick fill.",
        "prior_close_caveat":"A prior closed bar beyond retrospectively selected pivot exposes difference with 'first close beyond this selected swing'; original C21 dynamically chooses last eligible swing. It is a research contradiction to investigate, not a proved faulty author signal.",
        "freshness_caveat":"UTC/Kyiv/London previous-calendar-day counts are alternative hypotheses only; author session IANA timezone/DST not verified.",
        "public_external_sources_not_author_goldens":[
           "https://secuora.net/strategy/ict-silver-bullet",
           "https://innercircletrader.net/tutorials/killzone-silver-bullet-overlap/",
           "https://marketshala.com/blog/ict-liquidity-strategy-91-win-rate",
           "https://www.backtestingmax.com/strategy/ict-gold-a-liquidity-sweep-market-structure-shift-fair-value-GykYIUp2xmTxMnmBFO37"],
        "totals":totals,"markets":markets,
        "author_confirmed_3m_BOS":0,
        "author_selected_pivot_goldens":0,
        "author_live_execution_model_approved":0,
        "author_trade_approved":0,
        "readiness":"NOT_TRADE_READY"
    }
    assert receipt["source_original_zip_count"]==45
    assert receipt["source_original3m_bars"]==76800
    assert receipt["original_native15m_exact_decimal_equalities"]==15360
    assert totals["strict_closed_3m_research_edges"]==539
    assert totals["research_single_case_count"]==165
    assert receipt["author_trade_approved"]==0 and receipt["readiness"]=="NOT_TRADE_READY"
    pin=ROOT/"evidence/c31/C31_ORIGINAL_BOS_CROSS_VS_CLOSE_SOURCE.json"
    if pin.exists():
        normalized=json.loads(json.dumps(receipt,sort_keys=True,ensure_ascii=False))
        assert json.loads(pin.read_text(encoding="utf8"))==normalized,"C31_ORIGINAL_PINNED_FULL_JSON_DRIFT"
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(receipt,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"totals":totals,"author_BOS_goldens":0,
                      "readiness":"NOT_TRADE_READY"},sort_keys=True),flush=True)
    return receipt
if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
