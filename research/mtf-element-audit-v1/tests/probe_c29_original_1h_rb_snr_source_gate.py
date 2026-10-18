#!/usr/bin/env python3
"""C29 45-original-ZIP source verification of 1H candle-pair prerequisites ONLY."""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in ("d05","tools","tests"):sys.path.insert(0,str(ROOT/p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c29_rb_snr_source_guards import inspect_c29
from c28_source_fta_inventory import inspect_c28

FIELDS=("original_parent_edges","research_single_cases","source_hours",
        "source_opposite_pairs","source_followed_pairs",
        "source_extreme_envelope_follow_through",
        "case_preknown_pair_relations","cases_with_pair_relation",
        "case_preknown_technical_follow_through_relations",
        "cases_with_technical_follow_through")

def replay():
    frozen=json.loads((ROOT/"evidence"/"c28"/"C28_ORIGINAL_1H_CLASSIC_IMB_FTA_SOURCE.json").read_text(encoding="utf8"))
    prior={x["symbol"]:x for x in frozen["markets"]}
    markets=[]
    for symbol in sorted(SYMS):
        data={tf:tuple(load_original(symbol,tf,p,start)[0]
                       for p,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(data["15m"],data["1d"],END)
        raw=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        src=reconcile_native_3m(raw,htf,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        truncated=reconcile_native_3m(raw,htf,as_of_ms=cut)
        assert inspect_c29(src,as_of_ms=cut)==inspect_c29(truncated,as_of_ms=cut),"C29_PHYSICALLY_TRUNCATED_SOURCE_PREFIX_DRIFT"
        result=inspect_c29(src,as_of_ms=END)
        previous=inspect_c28(src,as_of_ms=END)
        assert result.original_parent_edges==previous.original_parent_edges==prior[symbol]["original_parent_edges"]
        assert result.research_single_cases==previous.research_single_cases==prior[symbol]["research_single_cases"]
        assert result.source_hours==768 and src.native_15m_ohlcv_equalities==3072
        assert result.author_approved_trades==0 and result.readiness=="NOT_TRADE_READY"
        cases=[]
        for case in result.cases:
            assert case.author_rb_confirmed==case.author_snr_confirmed==case.author_mb_as_snr_confirmed==0
            assert case.paired_opposite_closed_1h_count==case.paired_with_later_closed_hour+case.paired_missing_later_closed_hour
            assert case.technical_extreme_envelope_follow_through<=case.paired_with_later_closed_hour
            assert case.readiness=="NOT_TRADE_READY"
            assert all(p.pair_known_ms<=case.research_break_ms and
                (p.next_hour_known_ms is None or p.next_hour_known_ms<=case.research_break_ms)
                and not p.author_approved
                for p in case.unranked_research_sample)
            cases.append({
                "research_break_bar_start_ms":case.research_break_ms,
                "original_break_3m_row_id":case.original_break_row_id,
                "preknown_opposite_candle_pair_relations":case.paired_opposite_closed_1h_count,
                "previously_closed_later_hour_relations":case.paired_with_later_closed_hour,
                "unknown_future_third_hour_relations":case.paired_missing_later_closed_hour,
                "strict_envelope_follow_through_hypotheses":case.technical_extreme_envelope_follow_through,
                "author_rb_confirmed":0,"author_snr_confirmed":0,
                "author_mb_as_snr_confirmed":0,
                "latest_three_source_only_pairs":[asdict(p) for p in case.unranked_research_sample],
                "complete_pair_source_sha256":case.complete_preknown_pairs_sha256,
                "needs_author_labels":case.status,
                "readiness":"NOT_TRADE_READY"
            })
        market={
            "symbol":symbol,
            "native_3m_source_rows":len(src.original_3m_closed),
            "original_native15m_decimal_equalities":src.native_15m_ohlcv_equalities,
            "physically_truncated_replay_equal":True,
        }
        market.update({k:getattr(result,k) for k in FIELDS})
        market["cases"]=cases
        markets.append(market)
        print(symbol,"source 1h color pairs",result.source_opposite_pairs,
              "third full envelope",result.source_extreme_envelope_follow_through,
              "C29 source case relations",result.case_preknown_pair_relations,flush=True)
    return markets

def main(output=None):
    markets=replay()
    totals={k:sum(m[k] for m in markets) for k in FIELDS}
    receipt={
        "schema":"EMBER_C29_1H_COLOR_PAIR_NOT_RB_SNR_OR_FTA_V1",
        "frozen_c28_source_git_blob":"ed3aca9384c8e49d07220f04b7d363df92689317",
        "frozen_c27_source_git_blob":"d434ae830858fecf5e45cf7ef8ff7db1e627d489",
        "original_archive_count":45,
        "original_native3m_source_rows":sum(m["native_3m_source_rows"] for m in markets),
        "native15m_exact_decimal_equalities":sum(m["original_native15m_decimal_equalities"] for m in markets),
        "RB_primary_source":"https://drive.google.com/file/d/1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT/view",
        "SNR_primary_source":"https://drive.google.com/file/d/1OOyS7C8T8H4FdD47dXsnx7y3u33lNG7m/view",
        "FTA_primary_source":"https://drive.google.com/file/d/14KFoZCWoJEue_WmlOyXg0sBZoXsozP2M/view",
        "scope":"Strictly observed opposite-color two closed source 1H candles; optional third fully closed candle strict wick-envelope close-through is explicitly a counterfactual. This is NOT author RB/SNR detection or first test.",
        "causality":"All research case color pairs confirmed at/before C26 break 3m BAR START. Subsequent third 1H candle must also have closed before BAR START to be counted. Future confirmation never backdated.",
        "unresolved":"No author annotated 1H RB/SNR goldens, precise wick raid / IMB overlap source, technical RB wick range, author SNR settled level, strongest protected POI, first-test, FTA priority, bos pivot, session or SL/RR. Mitigation Block is NOT SNR volume confirmation.",
        "totals":totals,"markets":markets,
        "author_positive_rb_examples":0,"author_positive_snr_examples":0,
        "author_selected_first_fta":0,
        "author_trades_approved":0,
        "readiness":"NOT_TRADE_READY",
    }
    assert receipt["original_archive_count"]==45
    assert receipt["original_native3m_source_rows"]==76800
    assert receipt["native15m_exact_decimal_equalities"]==15360
    assert totals["source_hours"]==3840 and totals["research_single_cases"]==165 and totals["original_parent_edges"]==539
    assert receipt["author_trades_approved"]==0
    pinned=ROOT/"evidence"/"c29"/"C29_ORIGINAL_PAIR_GATES_NOT_RB_SNR.json"
    if pinned.exists():
        assert json.loads(pinned.read_text(encoding="utf8"))==receipt,"C29_PINNED_COMPLETE_JSON_DRIFT"
    if output:
        p=Path(output)
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"totals":totals,"original_archive_count":45,
      "readiness":"NOT_TRADE_READY"},sort_keys=True),flush=True)
    return receipt
if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
