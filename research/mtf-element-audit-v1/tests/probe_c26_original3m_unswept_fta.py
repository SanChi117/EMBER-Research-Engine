#!/usr/bin/env python3
"""C26 original 45 USD-M Futures ZIP forensic replay; PAPER ONLY, no orders."""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for folder in ("d05","tools","tests"):
    sys.path.insert(0,str(ROOT/folder))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c25_session_freshness_target_source import inspect_c25
from c26_unswept_1h_fta_source import inspect_c26

COUNTS=("original_parent_edges","research_single_cases",
    "nearest_target_already_crossed","nearest_target_equality_unresolved",
    "nearest_target_intact","nearest_target_not_preknown",
    "alternatives_intact_found","with_preknown_intervening_1h_obstacle",
    "same_bar_tick_order_unresolved")

def replay():
    frozen24=json.loads((ROOT/"evidence"/"c24"/"C24_ORIGINAL_3M_FAIL_CLOSED_ADMISSION.json").read_text())
    frozen25=json.loads((ROOT/"evidence"/"c25"/"C25_ORIGINAL_SESSIONS_TARGET_SOURCE.json").read_text())
    c24={x["symbol"]:x for x in frozen24["original_source_market_results"]}
    c25={x["symbol"]:x for x in frozen25["markets"]}
    findings=[]
    for symbol in sorted(SYMS):
        candles={tf:tuple(load_original(symbol,tf,p,start)[0]
                          for p,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(candles["15m"],candles["1d"],END)
        original=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        source=reconcile_native_3m(original,htf,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        truncated=reconcile_native_3m(original,htf,as_of_ms=cut)
        assert inspect_c26(source,as_of_ms=cut)==inspect_c26(truncated,as_of_ms=cut), "C26_PHYSICALLY_TRUNCATED_PREFIX_DRIFT"
        previous=inspect_c25(source,as_of_ms=END)
        result=inspect_c26(source,as_of_ms=END)
        assert previous.research_single_parent_cases==c24[symbol]["single_research_without_author_labels"]
        assert result.research_single_cases==c25[symbol]["research_single_parent_cases"]
        assert result.original_parent_edges==c25[symbol]["original_parent_edges"]
        assert previous.previous_day_timezone_disagreements==c25[symbol]["previous_day_timezone_disagreements"]
        assert source.native_15m_ohlcv_equalities==3072
        assert result.readiness=="NOT_TRADE_READY" and result.author_approved_trades==0
        assert all("UNKNOWN_AUTHOR_BOS_GOLDENS" in c.reasons and
                   "UNKNOWN_AUTHOR_SESSION_DST" in c.reasons and
                   "UNKNOWN_AUTHOR_SL_BUFFER" in c.reasons and
                   not c.author_approved for c in result.cases)
        witnesses=[]
        for c in result.cases:
            witnesses.append({
                "source_original3m_row_id":c.break_original_row_id,
                "raid_ms":c.raid_ms,"break_start_ms":c.break_start_ms,
                "side":c.side,"research_entry_close":c.research_entry_close,
                "research_raid_extreme":c.research_raid_extreme,
                "minimum_unbuffered_stop_span":c.unbuffered_stop_span,
                "historical_first_target_price":c.nearest_historical_target,
                "historical_target_center_ms":c.nearest_target_center_ms,
                "historical_target_known_ms":c.nearest_target_known_ms,
                "historical_target_asof_history":asdict(c.nearest_target_history)
                    if c.nearest_target_history else None,
                "separate_alternative_intact_hypothesis":c.alternative_intact_target,
                "alternative_center_ms":c.alternative_intact_center_ms,
                "preknown_obstacles":[asdict(v) for v in c.obstacles_before_nearest_target],
                "same_break_3m_bar_tick_order_unknown":c.target_fta_same_3m_bar_order_unknown,
                "research_only_reasons":list(c.reasons),
                "author_approved":False,"readiness":"NOT_TRADE_READY"
            })
        report={"symbol":symbol,
                "original_native3m_bars":len(source.original_3m_closed),
                "native15m_decimal_equalities":source.native_15m_ohlcv_equalities,
                "physically_truncated_prefix_equivalent":True}
        report.update({k:getattr(result,k) for k in COUNTS})
        report["cases"]=witnesses
        findings.append(report)
        print(symbol,"single",result.research_single_cases,
              "historical crossed",result.nearest_target_already_crossed,
              "intact",result.nearest_target_intact,flush=True)
    return findings

def main(output=None):
    markets=replay()
    totals={k:sum(x[k] for x in markets) for k in COUNTS}
    result={
        "schema":"EMBER_C26_UNSWEPT_1H_FTA_ORIGINAL_SOURCE_V1",
        "source":"original Binance USD-M Futures 3m/15m/1d, 2026-09-01 through 2026-10-02 UTC",
        "original_zip_count":45,
        "original_native3m_bars":sum(x["original_native3m_bars"] for x in markets),
        "native15m_decimal_equalities":sum(x["native15m_decimal_equalities"] for x in markets),
        "source_c24_receipt_git_blob":"163a0a41a9e5b51320e8f4baaad85cfd0be7c0a9",
        "source_c25_receipt_git_blob":"fe9b23672f97cdf1e50d603e7d214ecdef7a00ad",
        "causal_cutoff":"closed original 3m rows with known_ms <= break_start_ms; exclude BOS bar",
        "target_semantics":"historical closest opposite 1H fractal is checked for strict earlier wick/body crossings; equality is NOT a cross; alternative is not substituted for approved TP",
        "obstacle_semantics":"known 1H fractal between research entry close and historical nearest target; no author FTA definition or RR threshold",
        "totals":totals,
        "markets":markets,
        "author_bos_goldens":0,"author_timezone_attested":False,
        "author_fta_threshold_attested":False,"author_sl_buffer_attested":False,
        "approved_trades":0,"readiness":"NOT_TRADE_READY",
        "limits":"No intrabar tick order, author timezone/DST, precise author pivot, FTA threshold, stop buffer, or empirical profitability. PAPER ONLY."
    }
    assert result["original_native3m_bars"]==76800
    assert result["native15m_decimal_equalities"]==15360
    assert totals["original_parent_edges"]==539
    assert totals["research_single_cases"]==165
    assert (totals["nearest_target_already_crossed"]+
            totals["nearest_target_equality_unresolved"]+
            totals["nearest_target_intact"]+
            totals["nearest_target_not_preknown"])==165
    pin=ROOT/"evidence"/"c26"/"C26_UNSWEPT_1H_FTA_ORIGINAL_SOURCE.json"
    if pin.exists():
        assert json.loads(pin.read_text(encoding="utf8"))==result,"C26_FULL_JSON_GIT_PINNED_DRIFT"
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"totals":totals,"original_zip_count":45,
         "readiness":result["readiness"],"author_bos_goldens":0},
         sort_keys=True),flush=True)
    return result
if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
