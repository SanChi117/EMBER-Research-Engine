#!/usr/bin/env python3
"""Independent 30-C08-archive replay of C18 HTF→15m/1h co-observation graph.

No selected VC/StrongHL parent, no author-approved route or trading order.
"""
from __future__ import annotations
import json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for d in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):
    sys.path.insert(0,str(d))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,OCT_START,DAY,END
from c17_htf_imb_reaction_diagnostics import diagnose_htf_imb,AUTHOR_UNKNOWN
from c18_native_15m_child_witness_graph import build_lower_tf_witness_graph

def summarize(g):
    by_child=Counter(e.child_id for e in g.edges)
    by_parent=Counter(e.parent_id for e in g.edges)
    contacts=sum(p.first_closed_15m_contact_known_at_ms is not None for p in g.parents)
    assert len(set(p.parent_id for p in g.parents))==len(g.parents)
    assert len(set(c.id for c in g.children_15m+g.children_1h))==len(g.children_15m)+len(g.children_1h)
    assert all(e.contact_known_at_ms<e.child_known_at_ms and e.parent_id in
               {p.parent_id for p in g.parents} for e in g.edges)
    return {
      "parents_1d":sum(p.parent_tf=="1d" for p in g.parents),
      "parents_4h":sum(p.parent_tf=="4h" for p in g.parents),
      "parents_with_subsequent_native_15m_contact":contacts,
      "parents_without_native_15m_contact":len(g.parents)-contacts,
      "closed_15m_geometric_children":len(g.children_15m),
      "closed_1h_geometric_children":len(g.children_1h),
      "temporal_cooccurrence_edges":len(g.edges),
      "child_nodes_with_multiple_possible_htf_parents":sum(v>1 for v in by_child.values()),
      "htf_parents_with_multiple_possible_children":sum(v>1 for v in by_parent.values()),
      "unattributed_parent_choices":len(g.parents),
      "author_status":g.author_status,
      "readiness":g.readiness
    }

def main(path=None):
    observations=[]
    cutoff=OCT_START+DAY+3600000
    for symbol in SYMS:
        original={}
        for tf in ("15m","1d"):
            original[tf]=tuple(load_original(symbol,tf,d,s)[0] for d,s in zip(DATES,STARTS))
        source_full=extended_32day_prefix(original["15m"],original["1d"],END)
        source_prior=extended_32day_prefix(original["15m"],original["1d"],cutoff)
        graph=build_lower_tf_witness_graph(source_full,as_of_ms=END)
        past=build_lower_tf_witness_graph(source_prior,as_of_ms=cutoff)
        past_again=build_lower_tf_witness_graph(source_full,as_of_ms=cutoff)
        assert past==past_again, "FUTURE_SUFFIX_CHANGED_C18_HISTORIC_CAUSAL_GRAPH"
        htf=diagnose_htf_imb(source_full,as_of_ms=END)
        assert len(graph.parents)==len(htf.candidates_1d)+len(htf.candidates_4h)
        assert graph.author_status==AUTHOR_UNKNOWN and graph.readiness=="NOT_TRADE_READY"
        assert all(x.certification=="OBSERVED_TEMPORAL_COOCCURRENCE_NOT_AUTHOR_PARENT_VC" for x in graph.edges)
        count=summarize(graph)
        observations.append({"symbol":symbol,"counts":count,
                             "native_15m_bars":len(source_full.native_15m_closed),
                             "original_daily_parity":source_full.crosschecked_native_1d,
                             "prefix_invariance":True,
                             "author_approved_poi":0,"author_approved_vc":0,
                             "author_approved_stronghl":0,"trades":0})
        print(f"{symbol}: native 15m=3072; parents={len(graph.parents)}, coobservations={len(graph.edges)}, multi-parent-children={count['child_nodes_with_multiple_possible_htf_parents']}",flush=True)
    result={
        "cycle":"B1_C18_NATIVE_15M_FIRST_CONTACT_TO_LTF_IMB_COOBSERVATION",
        "market":"BINANCE_USDM_FUTURES","period_utc":["2026-09-01","2026-10-02"],
        "original_C08_archives_reloaded":30,"original_native_15m_bars":15360,
        "native_daily_parities":160,"derived_closed_1h":3840,
        "observations":observations,
        "author_golden_source_status":AUTHOR_UNKNOWN,
        "readiness":"NOT_TRADE_READY","trade_ready":0,
        "limitations":"First native 15m close-zone overlap after formation is diagnostic, not author first POI test. Later 1h/15m classic IMB gaps are coobservations not certified volume confirmation/BOS/entry; no complete original 5m 32-day lineage, no author Futures annotated goldens, no ROI."
    }
    assert len(observations)==5 and sum(x["native_15m_bars"] for x in observations)==15360
    assert sum(x["original_daily_parity"] for x in observations)==160
    assert all(x["prefix_invariance"] and x["counts"]["author_status"]==AUTHOR_UNKNOWN
               and x["counts"]["readiness"]=="NOT_TRADE_READY" for x in observations)
    if path:Path(path).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    return 0
if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
