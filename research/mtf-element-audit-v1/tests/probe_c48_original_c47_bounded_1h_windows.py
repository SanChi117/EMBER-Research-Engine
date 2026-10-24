#!/usr/bin/env python3
"""C48: transform entire frozen original C47 45ZIP source into bounded 1H windows.

Inputs: immutable original 45ZIP-derived 322,066-byte C47 JSON, not
independent predictive data. Outputs: explicit 6/24/72h adapted source
availability and as-of masking. NOT author Volume Confirmation/trades.
"""
import json,sys
from dataclasses import asdict
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for d in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/d))
from c47_post_4h_contact_1h_imb_source_link import (
    C47SourceJoin,FourToOneSourceObservation,OneHourImbSource)
from c48_adapted_post_contact_1h_source_windows import (
    WINDOWS,inspect_c47_source_windows)
SOURCE=ROOT/"evidence/c47/C47_ORIGINAL_4H_FIRST_CONTACT_TO_LATER_1H_IMB_45ZIP.json"
PIN=ROOT/"evidence/c48/C48_ORIGINAL_C47_6_24_72H_SOURCE_WINDOWS.json"

def as_1h(data):
    if data is None:return None
    a=dict(data)
    for k in ("first_raw_native3m_ids","last_raw_native3m_ids","orders","trades"):
        a[k]=tuple(a[k])
    return OneHourImbSource(**a)

def as_ob(data):
    a=dict(data)
    a["original4h_zone_first_raw3m_ids"]=tuple(a["original4h_zone_first_raw3m_ids"])
    a["first_post_contact_1h_imb_source"]=as_1h(a["first_post_contact_1h_imb_source"])
    for k in ("orders","trades"):a[k]=tuple(a[k])
    return FourToOneSourceObservation(**a)

def as_parent(data):
    a=dict(data)
    a["observations"]=tuple(as_ob(x) for x in a["observations"])
    for k in ("orders","trades"):a[k]=tuple(a[k])
    return C47SourceJoin(**a)

def classify(parent,asof):
    result=inspect_c47_source_windows(parent,as_of_ms=asof)
    assert len(result.outcomes)==result.source_parent_context_count
    by_policy={p:Counter() for p,_ in WINDOWS}
    for x in result.outcomes:
        assert len(x.policy_decisions)==len(WINDOWS)
        for d in x.policy_decisions:
            by_policy[d.window_policy][d.state]+=1
            assert not d.author_volume_confirmation_certified
            assert not d.author_poi_test_certified
            assert d.orders==d.trades==()
            assert d.readiness=="NOT_TRADE_READY"
            if d.passes_research_source_window:
                assert d.observed_first_1h_lag_ms is not None
                assert d.selected_first_1h_raw_native3m_id is not None
                assert d.observed_first_1h_lag_ms<=d.window_ms
            if d.selected_first_1h_raw_native3m_id is not None:
                assert d.observed_first_1h_lag_ms is not None
            if d.state in ("PARENT_4H_SOURCE_NOT_YET_KNOWN",
                           "NO_ORIGINAL_3M_CONTACT_KNOWN_AS_OF",
                           "WINDOW_OPEN_NO_1H_SOURCE_KNOWN",
                           "WINDOW_ELAPSED_WITHOUT_1H_SOURCE"):
                assert d.observed_first_1h_lag_ms is None
                assert d.selected_first_1h_raw_native3m_id is None
    assert result.author_poi_test_goldens==result.author_1h_vc_goldens==0
    assert result.trades==result.orders==() and result.readiness=="NOT_TRADE_READY"
    return result,by_policy

def run(out=None):
    raw=SOURCE.read_bytes()
    assert len(raw)==322066
    import hashlib
    assert hashlib.sha256(raw).hexdigest()=="8760ba25e7c8b85e74a66e481e293ca0d9c43fb0e621a38e72bb3ddbbbc2a72d"
    original=json.loads(raw)
    assert original["schema"]=="EMBER_C47_SOURCE_C46_4H_FIRST_3M_TOUCH_TO_POST_CONTACT_SAME_SIDE_1H_IMB_V1"
    assert original["original_binance_USDM_zip"]==45
    assert original["original_native3m_closed"]==76800
    assert original["native15m_decimal_equalities"]==15360
    assert original["original_C46_source_4h_candidate_count"]==153
    assert original["original_C46_first3m_contact_count"]==132
    assert original["same_side_later_closed_1h_source_candidate_parent_count"]==130
    assert original["contacted_parent_without_later_same_side_1h_count"]==2
    results=[]
    totals={p:Counter() for p,_ in WINDOWS}
    for market in original["markets"]:
        par=as_parent(market["full_original_source_result"])
        full,counts=classify(par,par.as_of_ms)
        assert full.source_parent_context_count==par.original_source4h_candidates
        assert full.completed_source_parent_contacts==par.original_source4h_first_contacts
        all6,all24,all72=(sum(counts[p]["LATER_1H_SOURCE_WITHIN_WINDOW"] for p,_ in WINDOWS
                        if p==pid) for pid,_ in WINDOWS)
        assert 0<=all6<=all24<=all72<=par.matched_later_technical1h_imb_count
        for p,v in counts.items():totals[p].update(v)
        results.append({"symbol":par.symbol,"original_C47_source_parent_count":par.original_source4h_candidates,
            "original_C47_first_3m_contact_count":par.original_source4h_first_contacts,
            "original_C47_unbounded_1h_technical_count":par.matched_later_technical1h_imb_count,
            "full_source_window_review":asdict(full),
            "per_policy_state_counts":{p:dict(sorted(v.items())) for p,v in sorted(counts.items())},
            "author_1h_vc_verified":0,"orders":0,"trades":0,
            "readiness":"NOT_TRADE_READY"})
        print("C48_ORIGINAL_SOURCE_ONLY",par.symbol,"unbounded",par.matched_later_technical1h_imb_count,
            "6/24/72 hours",all6,all24,all72,flush=True)
    across={pid:dict(sorted(vals.items())) for pid,vals in sorted(totals.items())}
    passing={pid:counts.get("LATER_1H_SOURCE_WITHIN_WINDOW",0) for pid,counts in across.items()}
    assert sum(x["original_C47_source_parent_count"] for x in results)==153
    assert sum(x["original_C47_first_3m_contact_count"] for x in results)==132
    assert sum(x["original_C47_unbounded_1h_technical_count"] for x in results)==130
    order=[passing[p] for p,_ in WINDOWS]
    assert 0<=order[0]<=order[1]<=order[2]<=130
    doc={"schema":"EMBER_C48_ADAPTED_FINITE_POST_CONTACT_1H_TECHNICAL_SOURCE_WINDOWS_V1",
        "parent_frozen_full_original_C47_source_git_blob":"b2727f081d8a73f522a97a54b4582507ee969244",
        "parent_complete_original_C47_45ZIP_bytes":322066,
        "source_original_USDM_zip_lineage":45,
        "source_native3m_closed":76800,
        "source_native1h_closed":3840,
        "source_native15m_exact_Decimal":15360,
        "original_4h_poi_source_candidates_not_author_labeled":153,
        "original_3m_first_contacts_not_author_labeled":132,
        "unbounded_later_1h_technical_IMB_parents_not_VC":130,
        "source_policies":[{"id":name,"window_hours":h//3600000,"status":"ADAPTED_RESEARCH_SOURCE_ONLY"}
            for name,h in WINDOWS],
        "per_policy_passed_source_counts":passing,
        "per_policy_all_original_source_states":across,
        "original_market_count":len(results),
        "course_author_poi_goldens":0,
        "course_author_1h_vc_goldens":0,
        "order_count":0,
        "trade_count":0,
        "readiness":"NOT_TRADE_READY",
        "limits":"6 24 72 hour post-contact third 1H bar closes are predeclared ADAPTED source-only hypotheses. First post-contact 1H geometry is retrospectively selected in C47; at earlier as-of its ID and known-time remain masked. This is no confirmation of academic POI test, volume, RR, SL/TP, returns, trades or out-of-sample power.",
        "markets":results}
    for pid,_ in WINDOWS:
        assert sum(across[pid].values())==153
    if out:
        p=Path(out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if PIN.exists():
        assert json.loads(PIN.read_text(encoding="utf8"))==json.loads(json.dumps(doc,sort_keys=True)),"C48_ADAPTED_SOURCE_WINDOW_FROZEN_DRIFT"
    print(json.dumps({"unbounded":130,"passed_source_counts":passing,"orders":0,"trades":0},
        sort_keys=True),flush=True)
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
