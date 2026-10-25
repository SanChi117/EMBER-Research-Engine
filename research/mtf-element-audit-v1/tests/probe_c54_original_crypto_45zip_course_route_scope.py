"""C54 crypto-only frozen original45ZIP 4H/1H source lineage vs course ROUTE A/B/C logic."""
import sys,json
from pathlib import Path
from collections import Counter
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/"d05"))
from c54_crypto_only_course_logic_source_bridge import CryptoTechnicalParent,overlay_crypto_course_routes,ROUTE_MAP,TARGET
SRC46=root/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
SRC47=root/"evidence/c47/C47_ORIGINAL_4H_FIRST_CONTACT_TO_LATER_1H_IMB_45ZIP.json"
PIN=root/"evidence/c54/C54_CRYPTO_ONLY_ACADEMIC_LOGIC_45ZIP_SOURCE_OVERLAYS.json"

def run(output=None):
    a=json.loads(SRC46.read_text());b=json.loads(SRC47.read_text())
    assert a["original_binance_USDM_zip"]==b["original_binance_USDM_zip"]==45
    assert a["original_native3m_closed"]==b["original_native3m_closed"]==76800
    assert a["native15m_decimal_equalities"]==b["native15m_decimal_equalities"]==15360
    assert a["source_candidate_4h_IMB_count"]==b["original_C46_source_4h_candidate_count"]==153
    assert a["first_observed_source_3m_contact_count"]==b["original_C46_first3m_contact_count"]==132
    assert b["original_C46_parent_Git_blob"]=="dc03c181912ffbb800bc191fbc16ec0d05c335e0"
    x={m["symbol"]:m for m in a["markets"]};y={m["symbol"]:m for m in b["markets"]}
    assert set(x)==set(y)=={"BTCUSDT","ETHUSDT","SOLUSDT","BCHUSDT","XRPUSDT"}
    counts=Counter();routes=Counter();markets=[]
    for sym in sorted(x):
        parent=x[sym]["source_only_4h_classic_imb_first_contact"]
        follow=y[sym]["full_original_source_result"]
        assert parent["as_of_ms"]==follow["as_of_ms"]
        assert parent["academic_core_id"]==follow["academic_core_id"]
        assert len(parent["observations"])==len(follow["observations"])==parent["candidate_count"]
        records=[];market_counts=Counter()
        for old,new in zip(parent["observations"],follow["observations"]):
            p=old["candidate"];later=new["first_post_contact_1h_imb_source"]
            assert p["three_original_source_first_native3m_ids"]==new["original4h_zone_first_raw3m_ids"]
            assert p["side"]==new["original4h_zone_side"]
            assert p["fully_known_ms"]==new["original4h_zone_known_ms"]
            assert old["first_contact_original3m_id"]==new["original4h_first_contact_native3m_id"]
            assert old["first_contact_closed_known_ms"]==new["original4h_first_contact_closed_known_ms"]
            assert not p["author_poi_certified"] and not old["academic_poi_test_certified"]
            assert not later or not later["academic_vc_certified"]
            raw=CryptoTechnicalParent(sym,parent["as_of_ms"],p["side"],
                tuple(p["three_original_source_first_native3m_ids"]),p["fully_known_ms"],
                old["first_contact_original3m_id"],old["first_contact_closed_known_ms"],
                later["first_raw_native3m_ids"][0] if later else None,
                later["fully_known_ms"] if later else None)
            overlays=overlay_crypto_course_routes(raw)
            assert len(overlays)==8 and {q.course_mode for q in overlays}==set(ROUTE_MAP)
            assert all(q.target_market==TARGET and q.readiness=="NOT_TRADE_READY"
                       and not q.academic_PoI_VC_entry_confirmed and not q.orders and not q.trades
                       for q in overlays)
            modes={q.course_mode:q.final_state for q in overlays}
            market_counts.update(modes.values());counts.update(modes.values());routes.update(modes.keys())
            records.append({"parent_original3m_source_id":raw.original_4h_source3m_ids[0],
              "parent_closed_known_ms":raw.original_4h_known_ms,
              "first_native3m_contact_id":raw.first_original3m_touch_id,
              "first_contact_closed_known_ms":raw.first_original3m_touch_known_ms,
              "first_followup_1h_technical_imb_native3m_id":raw.first_later_1h_technical_imb_source3m_id,
              "first_followup_1h_technical_imb_closed_known_ms":raw.first_later_1h_technical_imb_known_ms,
              "course_route_source_states":modes,"author_confirmed":False,
              "orders":0,"trades":0})
        markets.append({"symbol":sym,"parent_adapted_IMB_sources":parent["candidate_count"],
         "first_native3m_contacts":parent["first_original3m_contact_count"],
         "later_same_side_technical_1h_sources":follow["matched_later_technical1h_imb_count"],
         "route_states":dict(sorted(market_counts.items())),"source_contexts":records})
        print("C54",sym,len(records),dict(market_counts),flush=True)
    assert sum(m["parent_adapted_IMB_sources"] for m in markets)==153
    assert sum(m["first_native3m_contacts"] for m in markets)==132
    assert sum(m["later_same_side_technical_1h_sources"] for m in markets)==130
    assert counts=={
      "CONTEXT_TF_NOT_EVIDENCED_FOR_COURSE_ROUTE":765,
      "TECHNICAL_1H_IMB_AFTER_TOUCH_ONLY":390,
      "TECHNICAL_FIRST_TOUCH_WITHOUT_1H_SOURCE":6,
      "TECHNICAL_FIRST_TOUCH_UNKNOWN":63}
    assert len(routes)==8 and all(v==153 for v in routes.values())
    data={"schema":"EMBER_C54_CRYPTO_ONLY_ACADEMY_IMAGE_LOGIC_BRIDGE_V1",
      "date_utc":"2026-10-25","target":"BINANCE_USDM_CRYPTO_PAPER_ONLY",
      "teacher_images_role":"LOGIC_EXAMPLES_NOT_FX_RAW_CANDLES",
      "course_original_golden_FX_raw_candle_matching_required":False,
      "original_BINANCE_USDM_ZIP_lineage":45,
      "original_native3m_closed":76800,"native15m_exact":15360,
      "source_4h_technical_IMBs":153,"first_original3m_contacts":132,
      "later_1h_technical_IMBs":130,"academic_route_model_count":8,
      "route_source_contexts_checked":1224,
      "source_states":dict(sorted(counts.items())),
      "route_variants":dict(sorted(routes.items())),
      "source_C46_git_blob":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
      "source_C47_git_blob":"b2727f081d8a73f522a97a54b4582507ee969244",
      "academic_PoI_verified":0,"academic_VC_verified":0,
      "academic_IDM_BOS_verified":0,"orders":0,"trades":0,
      "readiness":"NOT_TRADE_READY","markets":markets}
    if output:
      p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
      p.write_text(json.dumps(data,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if PIN.exists(): assert data==json.loads(PIN.read_text()),"C54_FROZEN_CRYPTO_SOURCE_DRIFT"
    print("C54_45ZIP_CRYPTO_SOURCE_REJOIN_PASS 153 132 130 1224 8",flush=True)
    return data
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
