#!/usr/bin/env python3
"""C59 course semantic auditor over THREE previously independently reproduced,
immutable complete original-crypto sources C46, C47 and C58. No fabricated
course screenshot/author goldens, no FX, and NO crypto orders.

Join each of 153 source 4H IMBs by exact index AND original 3m source row IDs.
Classify first subsequent technical 1H IMB vs price interval of parent 4H
IMB and encode the original academy's explicit "4H IMB => don't consider
1H IMB inside as a trigger". Status is descriptive only; an outside IMB
is NOT automatically a valid trigger, author StrongHL or valid POI test.
"""
import json,sys,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c59_academic_stronghl_first_test_semantic_gate import SOURCE_STATUSES,source_parent_contract
from c45_recovered_course_text_contract import recovered_text_claims

BASE=ROOT/"evidence"
P46=BASE/"c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
P47=BASE/"c47/C47_ORIGINAL_4H_FIRST_CONTACT_TO_LATER_1H_IMB_45ZIP.json"
P58=BASE/"c58/C58_ORIGINAL_45ZIP_PREKNOWN_UNSWEPT_1H_FRACTAL_INSIDE_4H_FIRST_CONTACT.json"
PIN=BASE/"c59/C59_FROZEN_3_ORIGINAL_CRYPTO_SOURCES_4H1H_NESTING_AND_STRONGHL_TEXT_AUDIT.json"
BLOBS={
 "c46":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
 "c47":"b2727f081d8a73f522a97a54b4582507ee969244",
 "c58":"06f2ff7decd2aa9660381947d3cf43f6b722cd8e"
}

def load():
    for p in (P46,P47,P58):
        if not p.is_file():
            raise ValueError("C59_FROZEN_SOURCE_NOT_PRESENT")
    a,b,c=(json.loads(p.read_bytes()) for p in (P46,P47,P58))
    assert a["schema"]=="EMBER_C46_ORIGINAL_USDM_4H_SOURCE_CLASSIC_IMB_FIRST_3M_CONTACT_V1"
    assert b["schema"]=="EMBER_C47_SOURCE_C46_4H_FIRST_3M_TOUCH_TO_POST_CONTACT_SAME_SIDE_1H_IMB_V1"
    assert c["schema"]=="EMBER_C58_ORIGINAL45ZIP_CRYPTO_1H_PREKNOWN_INSIDE_4H_TECHNICAL_IMB_FIRST_3M_CONTACT_SOURCE_V1"
    assert a["source_candidate_4h_IMB_count"]==153 and a["first_observed_source_3m_contact_count"]==132
    assert b["original_C46_source_4h_candidate_count"]==153 and b["original_C46_first3m_contact_count"]==132
    assert b["same_side_later_closed_1h_source_candidate_parent_count"]==130
    assert c["source_4h_technical_IMB"]==153 and c["first_original3m_contact"]==132
    assert c["source_statuses"]["PREKNOWN_UNSWEPT_1H_FRACTAL_INSIDE_4H_GAP"]==29
    assert a["author_course_4h_poi_goldens"]==a["author_first_test_goldens"]==0
    assert b["academic_author_chart_goldens"]==b["academic_author_4h_poi_verified"]==0
    assert c["author_verified_idm"]==c["author_verified_strong_high_low"]==0
    return a,b,c

def run(output=None):
    a,b,c=load()
    claims=recovered_text_claims()
    assert {"STRONG-01","POI-03","ROUTE-A-01","ROUTE-A-06"}.issubset(claims)
    m46={z["symbol"]:z for z in a["markets"]}
    m47={z["symbol"]:z for z in b["markets"]}
    m58={z["symbol"]:z for z in c["markets"]}
    assert set(m46)==set(m47)==set(m58)=={"BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"}
    totals=Counter();markets=[];source_child_count=0
    for symbol in sorted(m46):
        p=m46[symbol]["source_only_4h_classic_imb_first_contact"]["observations"]
        h=m47[symbol]["full_original_source_result"]["observations"]
        l=m58[symbol]["source_observations"]
        assert len(p)==len(h)==len(l)
        rows=[];count=Counter()
        for idx,(ob,child,liq) in enumerate(zip(p,h,l)):
            if liq["symbol"]!=symbol:
                raise ValueError("C59_FROZEN_SOURCE_SYMBOL_TAMPERED")
            got=source_parent_contract(ob,child,liq)
            count[got["status"]]+=1
            src=ob["candidate"]
            rows.append({
                "4h_source_parent_index":idx,
                "original_4h_first_native3m_ids":src["three_original_source_first_native3m_ids"],
                "original_4h_known_ms":src["fully_known_ms"],
                "original_4h_side":src["side"],
                "original_4h_price_bounds":[src["bottom"],src["top"]],
                **got
            })
            assert not (got["course_author_strongHL"] or
                        got["course_author_first_valid_test"] or
                        got["course_author_routeA_trigger"] or
                        got["course_author_routeB_IDM"] or got["orders"] or got["trades"])
        assert sum(count.values())==len(p)
        assert count[SOURCE_STATUSES[0]]==len(p)-m46[symbol]["source_only_4h_classic_imb_first_contact"]["first_original3m_contact_count"]
        assert count[SOURCE_STATUSES[1]]==m47[symbol]["full_original_source_result"]["unmatched_after_first_contact_count"]
        source_child_count+=sum(count[k] for k in SOURCE_STATUSES[2:])
        totals.update(count)
        markets.append({
          "symbol":symbol,
          "original_source_4h_imb_parents":len(p),
          "original_source_full_parent_row_ids_cross_checked":True,
          "source_status_counts":{z:count[z] for z in SOURCE_STATUSES},
          "source_audit_per_parent":rows,
          "readiness":"NOT_TRADE_READY","author_goldens":0,"orders":0,"trades":0})
        print("C59",symbol,dict(sorted(count.items())),flush=True)
    assert sum(totals.values())==153
    assert totals[SOURCE_STATUSES[0]]==21
    assert totals[SOURCE_STATUSES[1]]==2
    assert source_child_count==130
    doc={
      "schema":"EMBER_C59_COURSE_TEXT_STRONGHL_FIRST_VALID_TEST_AND_ORIGINAL_C46_C47_C58_NESTED_1H_4H_IMB_RESEARCH_ONLY_V1",
      "scope":"CRYPTO_ONLY_BINANCE_USDM_SOURCE_REPLAY_NOT_ORDERS",
      "three_original_45ZIP_source_evidence_git_blobs":BLOBS,
      "evidence_source":{"c46_sha256":hashlib.sha256(P46.read_bytes()).hexdigest(),
                         "c47_sha256":hashlib.sha256(P47.read_bytes()).hexdigest(),
                         "c58_sha256":hashlib.sha256(P58.read_bytes()).hexdigest()},
      "original_c46_4h_source_candidate_total":153,
      "original_c46_first_3m_source_contact":132,
      "original_c47_after_first_contact_later1h_source":130,
      "original_c58_preknown_unswept1h_inside_original4h":29,
      "academic_course_rules_provenance":[
        "Strong High & Low.txt: contact with liquidity/inefficiency followed by VC POI or BOS movement",
        "Fair Value Gap  Imbalance.txt: true POI testing is FIRST test, repeated contacts are not pristine",
        "2. Entry by IMB & SNR.txt: when 4H is IMB do not treat nested inside 1H IMB as trigger"],
      "source_status_totals":{z:totals[z] for z in SOURCE_STATUSES},
      "academic_author_typed_POI_verified":0,
      "academic_author_first_valid_poi_test_verified":0,
      "academic_author_StrongHL_goldens":0,
      "academic_author_1h_IMB_as_trigger_goldens":0,
      "academic_author_VC_goldens":0,
      "academic_route_B_IDM_author_goldens":0,
      "orders":0,"trades":0,"fills":0,"PnL":None,
      "readiness":"NOT_TRADE_READY",
      "strict_note":"This is a source geometry veto and text-logic gate, NOT author-approved labels. The module refuses nested 1H IMB as trigger under 4H IMB, does not promote outside/overlap to entry, and bare pivot is never StrongHL.",
      "markets":markets}
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if PIN.exists():
        assert PIN.read_bytes()==(
          json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
        ).encode("utf-8"),"C59_IMMUTABLE_FROZEN_SOURCE_VETO_DRIFT"
    print("C59_SOURCE_3_ORIGINAL45ZIP_FROZEN_LINEAGES",json.dumps(doc["source_status_totals"],sort_keys=True),flush=True)
    return doc

if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
