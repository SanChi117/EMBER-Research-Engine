#!/usr/bin/env python3
"""C50 cross-join two exact independent frozen original45ZIP-derived sources.

Course A academic validity is NOT inferred from technical 4H/1H IMB
geometry or 3m directional close. Frozen original sources C47/C49 are
independently replayable; all seven C50 classifications are source-only.
"""
import sys,json,hashlib
from collections import Counter
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for s in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/s))
from probe_c48_original_c47_bounded_1h_windows import as_parent
from c49_original3m_post_contact_directional_close import (
    C49SourceReview,C49ParentReactionSource,C49DirectionalCloseObservation)
from c50_course_route_a_source_causality_gate import (
    review_course_1h_source_causality,MODES,BLOCKERS,CITED_RULE_IDS)

SRC47=ROOT/"evidence/c47/C47_ORIGINAL_4H_FIRST_CONTACT_TO_LATER_1H_IMB_45ZIP.json"
SRC49=ROOT/"evidence/c49/C49_ORIGINAL_45ZIP_4H_CONTACT_FIRST_LATER_3M_CLOSE.json"
PIN=ROOT/"evidence/c50/C50_ORIGINAL_C47_C49_COURSE_1H_CAUSALITY_GAP_45ZIP.json"

def as_c49(data):
    x=dict(data)
    x["observations"]=tuple(as_context(v) for v in x["observations"])
    for key in ("orders","trades"):x[key]=tuple(x[key])
    return C49SourceReview(**x)

def as_context(data):
    x=dict(data)
    x["window_observations"]=tuple(
        C49DirectionalCloseObservation(**{**z,"orders":tuple(z["orders"]),"trades":tuple(z["trades"])})
        for z in x["window_observations"])
    for k in ("orders","trades"):x[k]=tuple(x[k])
    return C49ParentReactionSource(**x)

def checked_frozen(path,n,sha):
    b=path.read_bytes()
    assert len(b)==n,(path,len(b))
    assert hashlib.sha256(b).hexdigest()==sha,path
    return json.loads(b)

def run(out=None):
    c47=checked_frozen(SRC47,322066,
        "8760ba25e7c8b85e74a66e481e293ca0d9c43fb0e621a38e72bb3ddbbbc2a72d")
    c49=checked_frozen(SRC49,463807,
        "e1315222e3bf492580abb435998bb79235d0db6e787f456cd03cccb2fafd7597")
    assert c47["original_binance_USDM_zip"]==c49["original_USDM_45ZIP_source"]==45
    assert c47["original_native3m_closed"]==c49["original_native3m_closed"]==76800
    assert c47["native15m_decimal_equalities"]==c49["original_native15m_exact"]==15360
    assert c47["original_C46_source_4h_candidate_count"]==c49["original_C46_4H_source_candidates"]==153
    assert c47["original_C46_first3m_contact_count"]==c49["original_C46_native3m_first_contacts"]==132
    a={m["symbol"]:m for m in c47["markets"]}
    b={m["symbol"]:m for m in c49["markets"]}
    assert len(a)==len(b)==5 and a.keys()==b.keys()
    markets=[]
    tally=Counter()
    directional=Counter()
    before=0
    for symbol in sorted(a):
        parent=as_parent(a[symbol]["full_original_source_result"])
        source=as_c49(b[symbol]["source_review"])
        result=review_course_1h_source_causality(parent,source)
        assert result.symbol==symbol
        assert result.as_of_ms==parent.as_of_ms==source.as_of_ms
        assert result.original_4h_candidate_count==len(result.source_contexts)
        assert result.author_verified_poi_count==result.author_verified_1h_vc_count==result.author_verified_entry_count==0
        assert result.trades==result.orders==() and result.readiness=="NOT_TRADE_READY"
        counts=Counter()
        cross=Counter()
        for ctx in result.source_contexts:
            counts[ctx.mode]+=1
            assert ctx.mode in MODES
            assert ctx.course_source_blockers==BLOCKERS
            assert ctx.readiness=="NOT_TRADE_READY"
            assert ctx.orders==ctx.trades==()
            assert not ctx.source_trade_ready
            assert not ctx.course_author_poi_test_verified
            assert not ctx.course_author_1h_volume_confirmation_verified
            if ctx.first_12h_direction is not None:
                assert ctx.first_12h_direction in ("FAVORABLE","ADVERSE")
                cross[ctx.mode+"__"+ctx.first_12h_direction]+=1
            if ctx.mode=="FIRST_DIRECTIONAL_3M_CLOSE_BEFORE_1H_IMB_CLOSE":
                assert ctx.first_12h_direction in ("FAVORABLE","ADVERSE")
                assert ctx.first_12h_directional_close_ms<ctx.first_later_1h_imb_closed_known_ms
                before+=1
        tally.update(counts)
        directional.update(cross)
        markets.append({
            "symbol":symbol,
            "original_source_parent_4h_IMB_candidates":parent.original_source4h_candidates,
            "original_source_first_3m_contacts":parent.original_source4h_first_contacts,
            "original_source_full_3m_closed":parent.original_native3m_closed,
            "classification_counts":dict(sorted(counts.items())),
            "price_close_side_by_classification":dict(sorted(cross.items())),
            "source_context_review":asdict(result),
            "course_author_POI_VC_goldens":0,
            "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"})
        print("C50_SOURCE",symbol,dict(sorted(counts.items())),flush=True)
    assert sum(tally.values())==153
    assert sum(x["original_source_first_3m_contacts"] for x in markets)==132
    assert tally["NO_ORIGINAL_4H_FIRST_3M_CONTACT"]==21
    assert tally["CONTACT_NO_DIRECTIONAL_3M_CLOSE_WITHIN_12H"]==3
    assert tally["DIRECTIONAL_CLOSE_NO_LATER_1H_IMB"]==2
    assert tally["FIRST_1H_IMB_CLOSED_AFTER_24H_OBSERVATION_WINDOW"]==23
    assert tally["FIRST_DIRECTIONAL_3M_CLOSE_BEFORE_1H_IMB_CLOSE"]==104
    assert tally["FIRST_DIRECTIONAL_3M_CLOSE_AT_1H_IMB_CLOSE"]==0
    assert tally["FIRST_1H_IMB_CLOSE_BEFORE_DIRECTIONAL_3M_CLOSE"]==0
    assert directional["FIRST_DIRECTIONAL_3M_CLOSE_BEFORE_1H_IMB_CLOSE__FAVORABLE"]==78
    assert directional["FIRST_DIRECTIONAL_3M_CLOSE_BEFORE_1H_IMB_CLOSE__ADVERSE"]==26
    assert before==104
    document={
        "schema":"EMBER_C50_ORIGINAL_C47_C49_SOURCE_CAUSALITY_AND_COURSE_POI_VC_EVIDENCE_GAP_V1",
        "original_Binance_USDM_ZIP_lineage":45,
        "original_native3m_closed":76800,
        "original_native15m_decimal_equalities":15360,
        "original_parent_source_4h_geometry":153,
        "original_first_native3m_contacts":132,
        "original_C47_full_json_git_blob":"b2727f081d8a73f522a97a54b4582507ee969244",
        "original_C49_full_json_git_blob":"c213c36a2e26caf63d9d65403429d1419a844bd9",
        "recovered_course_text_lessons":9,
        "necessary_course_text_rule_ids":list(CITED_RULE_IDS),
        "missing_author_evidence_per_candidate":list(BLOCKERS),
        "adapted_later_onehour_completion_window_hours":24,
        "adapted_first_directional_closed_3m_window_hours":12,
        "technical_source_event_classification_counts":dict(sorted(tally.items())),
        "direction_side_by_event_classification":dict(sorted(directional.items())),
        "original_market_count":len(markets),
        "author_verified_POI_first_test":0,
        "author_verified_onehour_VC":0,
        "author_verified_market_entry":0,
        "orders":0,"trades":0,"readiness":"NOT_TRADE_READY",
        "interpretation":"Among source-only records with 12h directional 3m close and a 1H IMB fully formed by 24h, the 3m close always happened before completion of the candidate 1H IMB. This disproves using a post-hoc 1H technical IMB as if it were a timely prerequisite confirming that EARLIER 3m exit. It does not disprove existence of separate academic route setups or true 1H volume confirmations not represented in these source objects. 12h/24h are independent ADAPTED research boundaries; no fills, RR, PnL, OOS or author 2023 positive examples.",
        "markets":markets}
    if out:
        target=Path(out);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(document,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    if PIN.exists():
        assert json.loads(PIN.read_text(encoding="utf8"))==json.loads(json.dumps(document,sort_keys=True)),"C50_FROZEN_SOURCE_DRIFT"
    print(json.dumps({"source_contexts":153,"counts":dict(tally),"reproducible_before_1h":104,
         "author_verified_POI_VC":0,"trade":0},sort_keys=True),flush=True)
    return document
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
