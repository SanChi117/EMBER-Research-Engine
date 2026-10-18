#!/usr/bin/env python3
"""C30 SOURCE causal known-prior liquidity/IMB wick events, not author RB/SNR."""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for d in ("d05","tools","tests"):sys.path.insert(0,str(ROOT/d))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c30_causal_wick_liquidity_imb import inspect_c30
from c29_rb_snr_source_guards import inspect_c29

FIELDS=("original_parent_edges","research_single_cases","original_closed_1h",
        "source_known_fractals","source_classic_1h_imb","opposite_1h_pairs",
        "pairs_with_known_liquidity_wick","pairs_with_first_liquidity_wick",
        "pairs_with_known_imb_wick","pairs_with_first_imb_wick",
        "pairs_with_any_wick_interaction","case_preknown_pair_links",
        "cases_with_any_source_wick_link","cases_with_first_liquidity_wick_link",
        "cases_with_first_imb_wick_link")

def main(output=None):
    pinned29=json.loads((ROOT/"evidence/c29/C29_ORIGINAL_PAIR_GATES_NOT_RB_SNR.json").read_text(encoding="utf8"))
    old={r["symbol"]:r for r in pinned29["markets"]}
    markets=[]
    for symbol in sorted(SYMS):
        frames={tf:tuple(load_original(symbol,tf,p,start)[0]
                        for p,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(frames["15m"],frames["1d"],END)
        archives=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        source=reconcile_native_3m(archives,htf,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        trunc=reconcile_native_3m(archives,htf,as_of_ms=cut)
        assert inspect_c30(source,as_of_ms=cut)==inspect_c30(trunc,as_of_ms=cut),"C30_SOURCE_PHYSICAL_PREFIX_CAUSAL_DRIFT"
        older=inspect_c29(source,as_of_ms=END)
        now=inspect_c30(source,as_of_ms=END)
        assert now.original_parent_edges==older.original_parent_edges==old[symbol]["original_parent_edges"]
        assert now.research_single_cases==older.research_single_cases==old[symbol]["research_single_cases"]
        assert now.original_closed_1h==768 and now.opposite_1h_pairs==old[symbol]["source_opposite_pairs"]
        assert source.native_15m_ohlcv_equalities==3072
        assert now.readiness=="NOT_TRADE_READY" and now.approved_trades==0
        cases=[]
        for c in now.cases:
            assert c.author_rb_approved==c.author_snr_approved==c.first_fta_approved==0
            assert c.readiness=="NOT_TRADE_READY"
            assert c.preknown_opposing_pair_relations>=c.source_preknown_pairs_with_any_wick_interaction
            assert c.preknown_pairs_with_prior_liquidity_wick>=c.preknown_pairs_with_first_liquidity_wick
            assert c.preknown_pairs_with_prior_imb_wick>=c.preknown_pairs_with_first_imb_wick
            assert all(p.known_ms<=c.research_break_start_ms and
                       p.readiness=="NOT_TRADE_READY" for p in c.latest_three_unranked_pairs)
            cases.append({
                "original_source_research_break_row_id":c.original_research_break_row_id,
                "research_break_start_ms":c.research_break_start_ms,
                "preknown_opposite_1h_pair_relations":c.preknown_opposing_pair_relations,
                "pairs_with_strict_pivot_wick":c.preknown_pairs_with_prior_liquidity_wick,
                "pairs_with_first_strict_pivot_wick":c.preknown_pairs_with_first_liquidity_wick,
                "pairs_with_imb_wick":c.preknown_pairs_with_prior_imb_wick,
                "pairs_with_first_imb_wick":c.preknown_pairs_with_first_imb_wick,
                "pairs_with_any_wick":c.source_preknown_pairs_with_any_wick_interaction,
                "full_case_source_sha256":c.source_case_evidence_sha256,
                "latest_two_unranked_source_pairs":[asdict(x) for x in c.latest_three_unranked_pairs],
                "author_rb_approved":0,"author_snr_approved":0,"first_fta_approved":0,
                "readiness":"NOT_TRADE_READY"})
        market={"symbol":symbol,
            "native3m_original_bar_count":len(source.original_3m_closed),
            "native15m_exact_decimal_equalities":source.native_15m_ohlcv_equalities,
            "physical_prefix_equal":True}
        market.update({k:getattr(now,k) for k in FIELDS})
        market["cases"]=cases
        markets.append(market)
        print(symbol,"first-liquidity-pair witnesses",now.pairs_with_first_liquidity_wick,
             "first-imb-pair witnesses",now.pairs_with_first_imb_wick,flush=True)
    totals={k:sum(m[k] for m in markets) for k in FIELDS}
    out={
      "schema":"EMBER_C30_SOURCE_KNOWN_PIVOT_AND_IMB_WICK_CAUSAL_V1",
      "original_binance_usdm_zip_count":45,
      "native3m_original_rows":sum(m["native3m_original_bar_count"] for m in markets),
      "native15m_exact_decimal_equalities":sum(m["native15m_exact_decimal_equalities"] for m in markets),
      "frozen_c29_original_source_blob":"abd68cb7cb86087c83423d16e9bbdd2cb344224c",
      "original_liquidity_source":"https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view",
      "original_imb_source":"https://drive.google.com/file/d/1ajvG1554qQ-5AnIV8HVmoDflkNRrU-LN/view",
      "original_rb_source":"https://drive.google.com/file/d/1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT/view",
      "original_snr_source":"https://drive.google.com/file/d/1OOyS7C8T8H4FdD47dXsnx7y3u33lNG7m/view",
      "source_only_scope":"Previously confirmed 1+1 1H pivot strict wick vs body cross, and before-formed 1H classic IMB wick-only contact from correct side, each with first vs already breached/touched state; linked to C29 two-color pair source. No author zone approval.",
      "source_limitation":"First strict crossing is observable on CLOSED native1H OHLC, does not reconstruct tick ordering. Candle break CLOSE known only at its close; no entry/TP/SL or first FTA recommendation. Wick-only on an opposite candle pair does not prove authored Rejection Block or Support and Resistance, whose labels and zone bounds remain absent.",
      "totals":totals,"markets":markets,
      "author_positive_rb_goldens":0,"author_positive_snr_goldens":0,
      "author_selected_first_fta":0,"author_selected_bos":0,
      "author_approved_trades":0,"readiness":"NOT_TRADE_READY"
    }
    assert out["original_binance_usdm_zip_count"]==45
    assert out["native3m_original_rows"]==76800
    assert out["native15m_exact_decimal_equalities"]==15360
    assert totals["original_closed_1h"]==3840
    assert totals["original_parent_edges"]==539 and totals["research_single_cases"]==165
    assert totals["opposite_1h_pairs"]==1989
    assert out["author_approved_trades"]==0 and out["readiness"]=="NOT_TRADE_READY"
    pin=ROOT/"evidence/c30/C30_ORIGINAL_PRIOR_WICK_IMB_CAUSAL_SOURCE.json"
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if pin.exists():
        frozen=json.loads(pin.read_text(encoding="utf8"))
        # Python asdict() preserves nested tuple containers; JSON has ONLY arrays.
        # Compare the actual JSON wire schema to avoid false tuple-vs-list drift.
        canonical=json.loads(json.dumps(out,sort_keys=True,ensure_ascii=False))
        if frozen!=canonical:
            def first_diff(a,b,path="root"):
                if type(a)!=type(b):return (path,"TYPE",type(a).__name__,type(b).__name__)
                if isinstance(a,dict):
                    for k in sorted(set(a)|set(b)):
                        if k not in a or k not in b:return (path+"."+k,"KEY_MISSING",k in a,k in b)
                        if a[k]!=b[k]:
                            return first_diff(a[k],b[k],path+"."+k)
                if isinstance(a,list):
                    if len(a)!=len(b):return (path,"LEN",len(a),len(b))
                    for i,(x,y) in enumerate(zip(a,b)):
                        if x!=y:return first_diff(x,y,path+"["+str(i)+"]")
                return (path,"VALUE",str(a)[:180],str(b)[:180])
            diff=first_diff(frozen,canonical)
            print("C30_PINNED_JSON_REPLAY_FIRST_DIFFERENCE",json.dumps(diff,ensure_ascii=False),flush=True)
            raise AssertionError("C30_PINNED_FULL_SOURCE_JSON_DRIFT")
    print(json.dumps({"totals":totals,"approved_trades":0,"readiness":"NOT_TRADE_READY"},sort_keys=True),flush=True)
    return out
if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
