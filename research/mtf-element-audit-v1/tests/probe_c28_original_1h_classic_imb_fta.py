#!/usr/bin/env python3
"""C28 original 45 USD-M ZIP forensic 1H IMB FTA inventory (not author trades)."""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in ("d05","tools","tests"):sys.path.insert(0,str(ROOT/p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c28_source_fta_inventory import inspect_c28
from c27_target_families_source import inspect_c27

FIELDS=("original_parent_edges","research_single_cases","source_hours",
        "full_source_1h_classic_imb","case_preknown_imb_edges",
        "case_overlap_imb_edges","cases_with_overlap",
        "cases_with_previously_untouched_overlap",
        "case_overlap_previously_touched_edges",
        "case_overlap_prior_full_traversals")

def replay():
    original27=json.loads((ROOT/"evidence"/"c27"/"C27_ORIGINAL_1H_EQ_SESSION_SOURCE.json").read_text(encoding="utf8"))
    legacy={x["symbol"]:x for x in original27["markets"]}
    findings=[]
    for sym in sorted(SYMS):
        data={tf:tuple(load_original(sym,tf,p,start)[0]
                   for p,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(data["15m"],data["1d"],END)
        archives=tuple(native_3m(sym,p)[0] for p in PERIODS)
        source=reconcile_native_3m(archives,htf,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        truncated=reconcile_native_3m(archives,htf,as_of_ms=cut)
        assert inspect_c28(source,as_of_ms=cut)==inspect_c28(truncated,as_of_ms=cut), "C28_ORIGINAL_SOURCE_PHYSICAL_PREFIX_DRIFT"
        prior=inspect_c27(source,as_of_ms=END)
        current=inspect_c28(source,as_of_ms=END)
        assert current.research_single_cases==prior.research_single_cases==legacy[sym]["research_single_cases"]
        assert current.original_parent_edges==prior.original_parent_edges==legacy[sym]["original_parent_edges"]
        assert current.source_hours==768
        assert source.native_15m_ohlcv_equalities==3072
        assert current.author_approved_trades==0 and current.readiness=="NOT_TRADE_READY"
        all_cases=[]
        for c in current.cases:
            assert c.break_known_ms>c.break_start_ms
            assert c.overlaps_entry_to_original_target==c.overlaps_never_touched_before_break+c.overlaps_first_touched_before_break
            assert c.overlaps_fully_traversed_before_break<=c.overlaps_first_touched_before_break
            assert not c.author_approved and c.readiness=="NOT_TRADE_READY"
            assert c.candidate_ranking_status=="AUTHOR_FTA_PRIORITY_UNKNOWN"
            all_cases.append({
                "original_source_break_row_id":c.original_break_row_id,
                "raid_ms":c.raid_ms,"break_start_ms":c.break_start_ms,
                "break_close_known_ms":c.break_known_ms,
                "side":c.side,
                "retrospective_break_close_NOT_KNOWN_AT_BREAK_START":c.retrospective_break_close,
                "c26_historical_geometric_single_fractal_target":c.c26_historical_nearest_target,
                "c26_historical_target_crossed_state":c.c26_nearest_target_cross_state,
                "source_preknown_1h_imb":c.total_preknown_1h_classic_imb,
                "source_gap_interval_overlaps":c.overlaps_entry_to_original_target,
                "overlaps_untouched_before_break":c.overlaps_never_touched_before_break,
                "overlaps_previously_touched":c.overlaps_first_touched_before_break,
                "overlaps_previously_fully_traversed":c.overlaps_fully_traversed_before_break,
                "nearest_three_technical_overlap_source_samples":[asdict(v) for v in c.nearest_three_overlap_samples],
                "all_technical_overlap_witnesses_SHA256":c.all_overlap_witnesses_sha256,
                "not_author_fta_reason":c.candidate_ranking_status,
                "other_families_not_approvable":c.other_families_status,
                "author_approved":False,"readiness":"NOT_TRADE_READY"})
        line={"symbol":sym,
              "original_source_3m_bars":len(source.original_3m_closed),
              "native15m_exact_decimal_equalities":source.native_15m_ohlcv_equalities,
              "source_physical_prefix_equivalent":True}
        line.update({k:getattr(current,k) for k in FIELDS})
        line["cases"]=all_cases
        findings.append(line)
        print(sym,"C28 singleton",current.research_single_cases,
              "preknown IMB",current.case_preknown_imb_edges,
              "interval overlaps",current.case_overlap_imb_edges,flush=True)
    return findings

def main(output=None):
    markets=replay()
    totals={k:sum(row[k] for row in markets) for k in FIELDS}
    result={
        "schema":"EMBER_C28_ORIGINAL_1H_CLASSIC_IMB_FTA_SOURCE_V1",
        "prior_receipt_c26_blob":"11edbf5ddf8e89e513fc3893e807903bbf8933eb",
        "prior_receipt_c27_blob":"d434ae830858fecf5e45cf7ef8ff7db1e627d489",
        "original_archive_count":45,
        "original_source_3m_bars":sum(r["original_source_3m_bars"] for r in markets),
        "original_native15m_decimal_equalities":sum(r["native15m_exact_decimal_equalities"] for r in markets),
        "source_IMB_course":"https://drive.google.com/file/d/1ajvG1554qQ-5AnIV8HVmoDflkNRrU-LN/view",
        "source_RB_course":"https://drive.google.com/file/d/1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT/view",
        "source_SNR_course":"https://drive.google.com/file/d/1OOyS7C8T8H4FdD47dXsnx7y3u33lNG7m/view",
        "source_FTA_context":"https://drive.google.com/file/d/14KFoZCWoJEue_WmlOyXg0sBZoXsozP2M/view",
        "source_1h_fvg_geometry":"1H classic 3 closed candle strict first-high<third-low or first-low>third-high. Known only at third 1H close, native 20x3m rows.",
        "pre_break_price_history":"Original CLOSED native3m candles only, known_ms <= breaking 3m BAR START, excludes break candle; strict first wick touch and full wick traversal are observational not fill.",
        "retrospective_range_limitation":"C26 break CLOSE is only known at break BAR CLOSE, so range between that research close and C26 historic target is retrospective and must never be used to claim an entry-time observable interval or live gating.",
        "all_overlap_digest":"Each case retains SHA256 over all sorted technical IMB overlap events and first-touch histories; 3 samples deliberately shown and nonexhaustive.",
        "unverified":"No instructor FTA selection/ranking, RB/SNR author interactions or bounds, age policy, FTA RR threshold, session timezone, selected BOS pivot, SL buffer, or tick entry/fill. This is NOT an author TP, FTA filter or market backtest.",
        "totals":totals,
        "markets":markets,
        "author_rb_snr_selected_fta":0,"author_selected_tp":0,
        "author_bos_approved":0,"approved_trades":0,"readiness":"NOT_TRADE_READY"
    }
    assert result["original_archive_count"]==45
    assert result["original_source_3m_bars"]==76800
    assert result["original_native15m_decimal_equalities"]==15360
    assert totals["research_single_cases"]==165 and totals["original_parent_edges"]==539
    assert all(x["source_hours"]==768 for x in markets)
    assert result["approved_trades"]==0 and result["readiness"]=="NOT_TRADE_READY"
    pin=ROOT/"evidence"/"c28"/"C28_ORIGINAL_1H_CLASSIC_IMB_FTA_SOURCE.json"
    if pin.exists():
        assert json.loads(pin.read_text(encoding="utf8"))==result,"C28_FULL_JSON_IMMUTABLE_RECEIPT_DRIFT"
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"schema":result["schema"],"totals":totals,
        "approved_trades":0,"readiness":"NOT_TRADE_READY"},sort_keys=True),flush=True)
    return result

if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
