#!/usr/bin/env python3
"""C61 comprehensive course POI+first visit+StrongHL prerequisite audit.

Five Binance USD-M cryptocurrency markets, TWO exact source dimensions:
  A. RE-DOWNLOAD original 45 signed ZIP (30 native 15m/1d + 15 native 3m)
     and verify all C46 full source 4H candidate parent IDs and 15m parity.
  B. Source chronological join original 1D known before 4H formation,
     frozen C46 first touch, C47 post-touch 1H source, C59 nesting veto,
     C60 first/repeated native3m episode, matching 153 parent IDs exactly.

NO source technical gap or pivot is author-selected contextual POI / first
valid test / VC POI/BOS / Strong High Low / IDM / entry. No orders.
"""
import sys,json,hashlib
from collections import Counter
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for f in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/f))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,DAY,SEPT_START
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
from c61_academic_poi_context_first_valid_stronghl_contract import (
    last_closed_original_day_before_zone,join_source_poi_context,REASONS)
C46=ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
C47=ROOT/"evidence/c47/C47_ORIGINAL_4H_FIRST_CONTACT_TO_LATER_1H_IMB_45ZIP.json"
C59=ROOT/"evidence/c59/C59_FROZEN_3_ORIGINAL_CRYPTO_SOURCES_4H1H_NESTING_AND_STRONGHL_TEXT_AUDIT.json"
C60=ROOT/"evidence/c60/C60_ORIGINAL45ZIP_4H_IMB_FIRST_AND_RETURN_SOURCE_NATIVE3M_EPISODES.json"
PIN=ROOT/"evidence/c61/C61_ORIGINAL45ZIP_DAILY_PRIOR_POI_FIRST_VISIT_STRONGHL_SOURCE_AUDIT.json"
SOURCE_BLOBS={
"c46":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
"c47":"b2727f081d8a73f522a97a54b4582507ee969244",
"c59":"46077ffb3495c14c906963156dd4a93c7acf9911",
"c60":"899373e4a1dc1999d1485ac8c1f790d39071aebd"}
def read_frozen():
    a,b,c,d=[json.loads(x.read_bytes()) for x in (C46,C47,C59,C60)]
    assert a["source_candidate_4h_IMB_count"]==153
    assert b["original_C46_source_4h_candidate_count"]==153
    assert c["original_c46_4h_source_candidate_total"]==153
    assert d["technical_4h_imb_candidate_total"]==153
    assert a["first_observed_source_3m_contact_count"]==132
    assert d["original_first_native3m_contact_total"]==132
    assert d["distinct_source_visit_episodes_total"]==4421
    assert a["author_first_test_goldens"]==b["academic_author_4h_poi_verified"]==0
    assert c["academic_author_StrongHL_goldens"]==d["author_first_valid_POI_tests"]==0
    assert d["orders"]==d["trades"]==d["fills"]==0
    return a,b,c,d

def run(output=None):
    frozen=read_frozen()
    lookups=[
      {z["symbol"]:z for z in src["markets"]} for src in frozen
    ]
    assert all(set(v)==set(SYMS) for v in lookups)
    markets=[];total=Counter()
    for symbol in sorted(SYMS):
        original={tf:tuple(load_original(symbol,tf,p,t)[0]
          for p,t in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(original["15m"],original["1d"],END)
        zips=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        native=reconcile_native_3m(zips,htf,as_of_ms=END)
        assert len(native.original_3m_closed)==15360
        assert len(htf.native_1d_closed)==32
        assert native.native_15m_ohlcv_equalities==3072
        p46=inspect_original_4h_imb_source(native,as_of_ms=END)
        old46=lookups[0][symbol]["source_only_4h_classic_imb_first_contact"]
        assert json.loads(json.dumps(asdict(p46),sort_keys=True))==old46,"C61_ORIGINAL_C46_REPLAY_CHANGED"
        old47=lookups[1][symbol]["full_original_source_result"]
        old59=lookups[2][symbol]
        old60=lookups[3][symbol]
        a=old46["observations"]
        b=old47["observations"]
        c=old59["source_audit_per_parent"]
        d=old60["complete_original_source_visit_lifecycle"]
        assert len(a)==len(b)==len(c)==len(d)==p46.candidate_count
        allstates=[];counts=Counter()
        for i,(p,h,g,v) in enumerate(zip(a,b,c,d)):
            day=last_closed_original_day_before_zone(
                htf.native_1d_closed,
                symbol=symbol,
                zone_known_ms=p["candidate"]["fully_known_ms"],as_of_ms=END)
            combined=join_source_poi_context(p,h,g,v,day)
            assert combined["symbol"]==symbol
            assert not any(combined[x] for x in (
                "author_daily_context","author_typed_4h_poi",
                "author_first_valid_test","author_reaction_vc_or_bos",
                "author_strongHL","course_fully_verified","orders","trades"))
            assert tuple(combined["blocking_reasons"])==REASONS
            if combined["original_prior_day_raw_id"] is None:
                counts["no_prior_closed_original_daily_candle"]+=1
            else:
                counts["had_prior_closed_original_daily_candle"]+=1
                assert day.latest_prior_day_known_ms<=combined["source_parent_known_ms"]
                assert day.latest_prior_day_known_ms%DAY==0
            counts[combined["source_visit_status"]]+=1
            counts[combined["c59_routeA_1h_imb_geometry_status"]]+=1
            if combined["later_same_side_1h_technical_imb_known_ms"] is not None:
                counts["post_touch_1h_technical_imb_but_not_author_vc"]+=1
                assert combined["original_first3m_touch_id"] is not None
            allstates.append({"original_parent_index":i,**combined})
        assert sum(counts[x] for x in (
            "NO_OBSERVED_FIRST_SOURCE_CONTACT",
            "REVISITED_TECHNICAL_ZONE",
            "ONE_TECHNICAL_SOURCE_VISIT"))==len(a)
        assert counts["NO_OBSERVED_FIRST_SOURCE_CONTACT"]==old46["untouched_candidate_count"]
        assert counts["REVISITED_TECHNICAL_ZONE"]==old60["source_candidates_with_repeated_return"]
        assert counts["post_touch_1h_technical_imb_but_not_author_vc"]==old47["matched_later_technical1h_imb_count"]
        total.update(counts)
        markets.append({
           "symbol":symbol,"fresh_original_native3m_closed":15360,
           "fresh_original_native1d_closed":32,
           "fresh_original_native15m_decimal_parities":3072,
           "original_4h_source_candidate_count":len(a),
           "original_frozen_lineage_all_parents_equal":True,
           "original_prior_closed_1d_context_not_selected_POI":True,
           "course_author_goldens":0,
           "source_stats":dict(sorted(counts.items())),
           "source_each_parent":[*allstates],
           "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"})
        print("C61",symbol,dict(sorted(counts.items())),flush=True)
    assert sum(m["fresh_original_native3m_closed"] for m in markets)==76800
    assert sum(m["fresh_original_native1d_closed"] for m in markets)==160
    assert sum(m["fresh_original_native15m_decimal_parities"] for m in markets)==15360
    assert sum(m["original_4h_source_candidate_count"] for m in markets)==153
    assert total["NO_OBSERVED_FIRST_SOURCE_CONTACT"]==21
    assert total["REVISITED_TECHNICAL_ZONE"]==127
    assert total["ONE_TECHNICAL_SOURCE_VISIT"]==5
    assert total["post_touch_1h_technical_imb_but_not_author_vc"]==130
    doc={
      "schema":"EMBER_C61_FRESH_45ZIP_ORIGINAL_DAILY_TO_4H_POI_FIRST_VISIT_1H_VC_STRONGHL_FAILCLOSED_SOURCE_V1",
      "scope":"CRYPTO_ONLY_BINANCE_USDM_SOURCE_RESEARCH_NOT_TRADE_READY",
      "period_utc":["2026-09-01","2026-10-02"],
      "original_45_sha_checked_zip_archives":{"native3m":15,"native15m":15,"native1d":15,"total":45},
      "original_native3m_closed":76800,
      "original_native1d_closed":160,
      "original_native15m_decimal_equalities":15360,
      "original_4h_classic_imb_source_parents":153,
      "original_4h_source_first_native3m_contacts":132,
      "original_c47_postcontact_same_side_1h_imb_sources":130,
      "original_c60_distinct_technical_3m_wick_visits":4421,
      "source_stats":dict(sorted(total.items())),
      "previous_immutable_c46_c47_c59_c60_git_blobs":SOURCE_BLOBS,
      "course_owner_text_anchors":[
       "POI.txt: support/resistance; strong POI interacted with BSL/SSL or FVG",
       "Rejection Block.txt: two opposing candles and liquidity raid or IMB work mandatory",
       "Fair Value Gap Imbalance.txt: only FIRST valid POI test is considered pristine",
       "Strong High & Low.txt: contact with liquidity/inefficiency then later VC POI or BOS",
       "Order Flow.txt: trend structure includes genuine liquidity and POI work",
       "2. Entry by IMB & SNR.txt: Daily POI/Liquidity -> 4H VC -> 1H trigger -> 15m VC; nested 1h IMB in 4h IMB not trigger",
       "3. Entry by IDM.txt: direct IDM route can plan limits before POI test; not Route A"],
      "no_author_goldens_reason":"The owner's text and diagrams do not identify timestamped verified Binance USD-M crypto candle/symbol/SL/TP cases; daily high/low is contextual liquidity only and technical 4H wick IMB is not author typed selected POI.",
      "author_selected_1d_or_4h_poi_goldens":0,
      "author_verified_first_valid_poi_tests":0,
      "author_verified_strong_high_low":0,
      "author_1h_trigger_and_volume_confirmation_goldens":0,
      "author_route_B_IDM_goldens":0,
      "author_route_C_BOS_goldens":0,
      "author_execution_goldens":0,
      "orders":0,"trades":0,"fills":0,"PnL":None,
      "readiness":"NOT_TRADE_READY",
      "markets":markets}
    if output:
        path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if PIN.exists():
        assert PIN.read_bytes()==(json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf-8"),"C61_PINNED_CRYPTO_SOURCE_BYTES_CHANGED"
    print("C61_COMPLETE_ORIGINAL45ZIP",json.dumps(doc["source_stats"],sort_keys=True),flush=True)
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
