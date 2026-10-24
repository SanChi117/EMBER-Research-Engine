#!/usr/bin/env python3
"""C47 entire original 45 Binance USD-M ZIP 4H IMB/contact → later 1H IMB SOURCE.

Every 1H technical witness is AFTER the 3m first-contact bar CLOSE.
Research text labels only; these are NOT academic POI, VC or trade signals.
"""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ("tests","d05","tools"):
    sys.path.insert(0,str(ROOT/name))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c47_post_4h_contact_1h_imb_source_link import scan_original_4h_first_contact_to_later_1h_source
FROZEN_C46=ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
PIN=ROOT/"evidence/c47/C47_ORIGINAL_4H_FIRST_CONTACT_TO_LATER_1H_IMB_45ZIP.json"
CUT=OCT_START+DAY+3*THREE

def run(out=None):
    previous=json.loads(FROZEN_C46.read_text(encoding="utf8"))
    assert previous["schema"]=="EMBER_C46_ORIGINAL_USDM_4H_SOURCE_CLASSIC_IMB_FIRST_3M_CONTACT_V1"
    assert previous["source_candidate_4h_IMB_count"]==153
    assert previous["first_observed_source_3m_contact_count"]==132
    assert previous["source_no_contact_count"]==21
    prev={x["symbol"]:x["source_only_4h_classic_imb_first_contact"]
          for x in previous["markets"]}
    markets=[]
    for symbol in sorted(SYMS):
        original={tf:tuple(load_original(symbol,tf,part,at)[0]
             for part,at in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(original["15m"],original["1d"],END)
        source=tuple(native_3m(symbol,part)[0] for part in PERIODS)
        full=reconcile_native_3m(source,htf,as_of_ms=END)
        physical=reconcile_native_3m(source,htf,as_of_ms=CUT)
        bounded=scan_original_4h_first_contact_to_later_1h_source(full,as_of_ms=CUT)
        actual=scan_original_4h_first_contact_to_later_1h_source(physical,as_of_ms=CUT)
        assert bounded==actual,"C47_FUTURE_SUFFIX_RESULT_LEAK"
        result=scan_original_4h_first_contact_to_later_1h_source(full,as_of_ms=END)
        assert result.original_native3m_closed==15360
        assert result.original_native1h_closed==768
        assert full.native_15m_ohlcv_equalities==3072
        p=prev[symbol]
        assert result.original_source4h_candidates==p["candidate_count"]
        assert result.original_source4h_first_contacts==p["first_original3m_contact_count"]
        assert len(result.observations)==len(p["observations"])
        assert result.matched_later_technical1h_imb_count+result.unmatched_after_first_contact_count==result.original_source4h_first_contacts
        for now,old in zip(result.observations,p["observations"]):
            c=old["candidate"]
            assert now.original4h_zone_side==c["side"]
            assert now.original4h_zone_known_ms==c["fully_known_ms"]
            assert list(now.original4h_zone_first_raw3m_ids)==c["three_original_source_first_native3m_ids"]
            assert now.original4h_first_contact_native3m_id==old["first_contact_original3m_id"]
            assert now.original4h_first_contact_closed_known_ms==old["first_contact_closed_known_ms"]
            assert now.course_typed_poi_approved==now.course_first_valid_test_approved==now.course_volume_confirmation_approved==False
            assert now.author_chart_golden_count==0 and now.orders==now.trades==()
            assert now.readiness=="NOT_TRADE_READY"
            v=now.first_post_contact_1h_imb_source
            if v:
                assert now.original4h_first_contact_closed_known_ms is not None
                assert v.first_hour_start_ms>=now.original4h_first_contact_closed_known_ms
                assert v.fully_known_ms==v.third_hour_start_ms+3600000
                assert v.fully_known_ms<=END
                assert v.side==c["side"]
                assert len(v.first_raw_native3m_ids)==len(v.last_raw_native3m_ids)==3
                assert not v.academic_vc_certified and v.orders==v.trades==()
            elif now.original4h_first_contact_native3m_id is None:
                assert now.post_contact_same_side_1h_candidate_count==0
        assert result.author_vc_goldens==result.author_poi_goldens==0
        assert result.orders==result.trades==()
        assert result.readiness=="NOT_TRADE_READY"
        markets.append({
            "symbol":symbol,"full_original_source_result":asdict(result),
            "original_native15m_decimal_equalities":full.native_15m_ohlcv_equalities,
            "original_native3m_prefix_physically_cut_same":True,
            "original_C46_immutable_parent_witness_exact":True,
            "author_course_poi_vc_goldens":0,"orders":0,"trades":0,
            "readiness":"NOT_TRADE_READY"})
        print("C47_ORIGINAL",symbol,"parent 4H",result.original_source4h_candidates,
            "contact",result.original_source4h_first_contacts,
            "later 1H geometry",result.matched_later_technical1h_imb_count,flush=True)
    doc={
        "schema":"EMBER_C47_SOURCE_C46_4H_FIRST_3M_TOUCH_TO_POST_CONTACT_SAME_SIDE_1H_IMB_V1",
        "original_binance_USDM_zip":45,
        "original_native3m_closed":sum(x["full_original_source_result"]["original_native3m_closed"] for x in markets),
        "original_native1h_closed":sum(x["full_original_source_result"]["original_native1h_closed"] for x in markets),
        "native15m_decimal_equalities":sum(x["original_native15m_decimal_equalities"] for x in markets),
        "original_C46_source_4h_candidate_count":sum(x["full_original_source_result"]["original_source4h_candidates"] for x in markets),
        "original_C46_first3m_contact_count":sum(x["full_original_source_result"]["original_source4h_first_contacts"] for x in markets),
        "same_side_later_closed_1h_source_candidate_parent_count":sum(x["full_original_source_result"]["matched_later_technical1h_imb_count"] for x in markets),
        "contacted_parent_without_later_same_side_1h_count":sum(x["full_original_source_result"]["unmatched_after_first_contact_count"] for x in markets),
        "market_count":len(markets),
        "original_C46_parent_Git_blob":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
        "academic_author_4h_poi_verified":0,
        "academic_author_first_contact_test_verified":0,
        "academic_author_1h_volume_confirmation_verified":0,
        "academic_author_chart_goldens":0,"orders":0,"trades":0,
        "readiness":"NOT_TRADE_READY",
        "limitations":"Post-3m-first-contact 1H IMB is only later source geometry. It is not a verified route-specific 1H volume confirmation or author-labelled 2023 example. Multiple same-side 1H IMBs per parent do not count as independent trades; no SL/TP, fills or profitability.",
        "markets":markets}
    assert doc["original_native3m_closed"]==76800
    assert doc["original_native1h_closed"]==3840
    assert doc["native15m_decimal_equalities"]==15360
    assert doc["original_C46_source_4h_candidate_count"]==153
    assert doc["original_C46_first3m_contact_count"]==132
    assert doc["same_side_later_closed_1h_source_candidate_parent_count"]+doc["contacted_parent_without_later_same_side_1h_count"]==132
    if out:
        p=Path(out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(doc,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
    if PIN.exists():
        assert json.loads(PIN.read_text(encoding="utf8"))==json.loads(json.dumps(doc,sort_keys=True)),"C47_SOURCE_FROZEN_JSON_DRIFT"
    print(json.dumps({k:doc[k] for k in ("original_C46_source_4h_candidate_count","original_C46_first3m_contact_count","same_side_later_closed_1h_source_candidate_parent_count","contacted_parent_without_later_same_side_1h_count")},sort_keys=True),flush=True)
    return doc

if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
