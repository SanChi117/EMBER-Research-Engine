#!/usr/bin/env python3
"""Original-source C27 1H TP family comparison and strict as-of replay.

No author-selected BOS or actual targets; numeric close/proximity EQ policy UNKNOWN.
Uses exactly same 45 Binance USD-M ZIP and original 3m price as C26.
"""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for directory in ("d05","tools","tests"):
    sys.path.insert(0,str(ROOT/directory))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c27_target_families_source import inspect_c27
from c26_unswept_1h_fta_source import inspect_c26

METRICS=("original_parent_edges","research_single_cases",
    "with_exact_price_pair_on_side","exact_price_pairs_total",
    "with_session_scenario_disagreement","incomplete_session_windows",
    "prior_target_crossed_by_c26")
ROOT_SOURCE="https://data.binance.vision/data/futures/um/"
def replay():
    original26=json.loads((ROOT/"evidence"/"c26"/"C26_UNSWEPT_1H_FTA_ORIGINAL_SOURCE.json").read_text(encoding="utf8"))
    prior={r["symbol"]:r for r in original26["markets"]}
    markets=[]
    for symbol in sorted(SYMS):
        data={tf:tuple(load_original(symbol,tf,p,start)[0]
                       for p,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(data["15m"],data["1d"],END)
        original3m=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        source=reconcile_native_3m(original3m,htf,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        physically_truncated=reconcile_native_3m(original3m,htf,as_of_ms=cut)
        assert inspect_c27(source,as_of_ms=cut)==inspect_c27(physically_truncated,as_of_ms=cut), "C27_PHYSICALLY_TRUNCATED_CAUSAL_PREFIX_DRIFT"
        current=inspect_c27(source,as_of_ms=END)
        previously=inspect_c26(source,as_of_ms=END)
        expected=prior[symbol]
        assert current.original_parent_edges==expected["original_parent_edges"]
        assert current.research_single_cases==expected["research_single_cases"]
        assert current.prior_target_crossed_by_c26==expected["nearest_target_already_crossed"]
        assert previously.readiness==current.readiness=="NOT_TRADE_READY"
        assert current.author_approved_trades==0
        assert source.native_15m_ohlcv_equalities==3072
        witnesses=[]
        for c in current.cases:
            assert len(c.previous_calendar_scenarios)==12
            assert all(not w.status.startswith("ACADEMIC_APPROVED")
                       for w in c.previous_calendar_scenarios)
            assert not c.author_target_approved and c.readiness=="NOT_TRADE_READY"
            assert "AUTHOR_EQ_TOLERANCE_UNKNOWN" in c.unknowns
            witnesses.append({
                "raid_ms":c.raid_ms,"break_start_ms":c.break_start_ms,
                "original_3m_break_row_id":c.source_original3m_break_row_id,
                "side":c.side,"technical_break_close":c.research_entry_close,
                "c26_initial_single_1h_fractal_history_state":c.c26_initial_target_cross_state,
                "exact_1h_eq_price_pair_witnesses":[asdict(p) for p in c.exact_price_pairs_on_research_side],
                "hypothetical_previous_session_calendar_witnesses":[asdict(w) for w in c.previous_calendar_scenarios],
                "timezone_hypotheses_disagree":c.session_scenario_value_disagreement,
                "unresolved_author_rules":list(c.unknowns),
                "author_target_approved":False,"readiness":"NOT_TRADE_READY"})
        row={"symbol":symbol,
             "original_native3m_bars":len(source.original_3m_closed),
             "native15m_exact_decimal_equalities":source.native_15m_ohlcv_equalities,
             "independent_physically_truncated_prefix_equal":True}
        row.update({key:getattr(current,key) for key in METRICS})
        row["cases"]=witnesses
        markets.append(row)
        print(symbol,"C27 cases",current.research_single_cases,
            "exact-equality research witnesses",current.exact_price_pairs_total,
            "timezone-scenario disagreements",current.with_session_scenario_disagreement,flush=True)
    return markets

def main(output=None):
    markets=replay()
    totals={k:sum(r[k] for r in markets) for k in METRICS}
    report={
        "schema":"EMBER_C27_SOURCE_TYPED_1H_TARGET_FAMILIES_V1",
        "original_source":"45 Binance USD-M Futures 3m/15m/1d original SHA-checked ZIP, 2026-09-01 through 2026-10-02 UTC",
        "source_base":ROOT_SOURCE,
        "original_archive_count":45,
        "source_native_3m_bars":sum(r["original_native3m_bars"] for r in markets),
        "source_native_15m_decimal_equalities":sum(r["native15m_exact_decimal_equalities"] for r in markets),
        "frozen_c26_receipt_git_blob":"11edbf5ddf8e89e513fc3893e807903bbf8933eb",
        "academic_entry_bos_url":"https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view",
        "academic_liquidity_url":"https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view",
        "academic_strong_highlow_url":"https://drive.google.com/file/d/1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t/view",
        "strict_numeric_eq_pair_semantics":"EXACT Decimal equality of >=2 confirmed one-hour same-side fractal highs/lows only; narrow source witness, never inferred author tolerance",
        "scenario_semantics":"Previous local calendar day (24 complete 1H) and previous local 09-17 interval (8 complete 1H), each under UTC, Europe/Kyiv and Europe/London. Hypotheses, NOT author timezone or session.",
        "target_fta_semantics":"Family observations do not choose TP, cannot infer author FTA or RR threshold, historical future/tick-order not reconstructed.",
        "totals":totals,"markets":markets,
        "author_labeled_futures_bos_cases":0,
        "author_eq_tolerance_known":False,
        "author_session_timezone_dst_known":False,
        "author_fta_rr_known":False,
        "author_sl_buffer_known":False,
        "approved_trades":0,
        "readiness":"NOT_TRADE_READY"
    }
    assert report["original_archive_count"]==45
    assert report["source_native_3m_bars"]==76800
    assert report["source_native_15m_decimal_equalities"]==15360
    assert totals["research_single_cases"]==165
    assert totals["original_parent_edges"]==539
    assert totals["prior_target_crossed_by_c26"]==137
    assert sum(len(x["cases"]) for x in markets)==165
    pin=ROOT/"evidence"/"c27"/"C27_ORIGINAL_1H_EQ_SESSION_SOURCE.json"
    if pin.exists():
        assert json.loads(pin.read_text(encoding="utf8"))==report,"C27_COMPLETE_PINNED_SOURCE_JSON_DRIFT"
    if output:
        path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"schema":report["schema"],"totals":totals,
        "approved_trades":0,"readiness":"NOT_TRADE_READY"},sort_keys=True),flush=True)
    return report

if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv)>1 else None)
