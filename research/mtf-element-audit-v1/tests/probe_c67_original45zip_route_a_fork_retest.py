#!/usr/bin/env python3
"""C67 source-only independent original45ZIP owner Route A branch fork.

Each of frozen C46/C60/C62/C63/C66 source rows is checked against freshly
re-downloaded 45 SHA-verified Binance USD-M original crypto ZIP.
1H strict preknown SSL/BSL wick-only raid OR 1H IMB trigger candidate,
with 1H IMB nested in source 4H parent excluded. Distinct 1H RB/SNR/IMB
context-VC new POI requires first AFTER-known 15m wick test before
first ANY technical 15m source event, NEVER author VALID retest or trade.
A 1H IMB qualifying as both trigger and source VC is AMBIGUOUS;
Route B IDM, Route C 3m/5m BOS never mixed.
"""
import sys,json
from pathlib import Path
from dataclasses import asdict
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
for x in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/x))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY,TF_MS
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
from c62_academic_snr_rb_imb_liquidity_source_separation import observe_hourly_source_poi_split
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    convert_c62_closed_source_events,source_first_any_after_contact)
from c66_native15m_route_a_source_event_chain import scan_original15m_source
from c67_route_a_1h_trigger_vs_new_poi_source_fork import (
    route_a_fork_1h_to_15m,FORK_STATES)
OLD={
"c46":ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json",
"c60":ROOT/"evidence/c60/C60_ORIGINAL45ZIP_4H_IMB_FIRST_AND_RETURN_SOURCE_NATIVE3M_EPISODES.json",
"c62":ROOT/"evidence/c62/C62_ORIGINAL_45ZIP_1H_SNR_RB_MB_IMB_LIQUIDITY_COMPLETE_SOURCE.json",
"c63":ROOT/"evidence/c63/C63_ORIGINAL45ZIP_FIRST_ANY_CLOSED1H_SOURCE_AFTER_4H_FIRST_NATIVE3M_CONTACT.json",
"c66":ROOT/"evidence/c66/C66_ORIGINAL45ZIP_4H1H_TO_NATIVE15M_SOURCE_FIRST_ANY_ROUTE_A.json"
}
SOURCE_GIT_BLOBS={
"C46":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
"C60":"899373e4a1dc1999d1485ac8c1f790d39071aebd",
"C62":"8428bf7d6cd3bc26f617cfc32a34c91a27c813b2",
"C63":"fdc77c7ec942f03b4efae83b935d994c8435a24f",
"C66":"c693058cdb28b0e118879d32ddcbbd0d2a66bfc6"}
PIN=ROOT/"evidence/c67/C67_ORIGINAL45ZIP_ROUTE_A_1H_TRIGGER_NEW_POI_15M_FIRST_RETEST_FORK.json"
def normalize(x):return json.loads(json.dumps(x,sort_keys=True))
def run(output=None):
    original_old={k:json.loads(path.read_bytes()) for k,path in OLD.items()}
    assert original_old["c46"]["source_candidate_4h_IMB_count"]==153
    assert original_old["c66"]["original_4h_c46_contexts"]==153
    by={k:{m["symbol"]:m for m in x["markets"]} for k,x in original_old.items()}
    assert all(set(v)==set(SYMS) for v in by.values())
    markets=[];grand=Counter();nested_total=0
    for symbol in sorted(SYMS):
        input_original={tf:tuple(load_original(symbol,tf,period,start)[0]
          for period,start in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(input_original["15m"],input_original["1d"],END)
        source=reconcile_native_3m(tuple(native_3m(symbol,p)[0] for p in PERIODS),htf,as_of_ms=END)
        assert len(source.original_3m_closed)==15360
        assert len(htf.native_15m_closed)==3072
        assert source.native_15m_ohlcv_equalities==3072
        assert len(htf.native_1d_closed)==32 and len(htf.derived_1h_closed)==768
        c46=inspect_original_4h_imb_source(source,as_of_ms=END)
        assert normalize(asdict(c46))==by["c46"][symbol]["source_only_4h_classic_imb_first_contact"],"C67_C46_ORIGINAL_ID_PRICE_DRIFT"
        c62=observe_hourly_source_poi_split(htf.derived_1h_closed,as_of_ms=END)
        assert normalize([asdict(x) for x in c62["technical_1h_snr_rb_separate_cases"]])==by["c62"][symbol]["source_cases"],"C67_C62_ORIGINAL_PAIR_DRIFT"
        assert normalize([asdict(x) for x in c62["technical_original_1h_imb_gaps"]])==by["c62"][symbol]["source_gaps"],"C67_C62_ORIGINAL_1H_GAP_DRIFT"
        h_events=convert_c62_closed_source_events(c62,htf.derived_1h_closed,as_of_ms=END)
        l_events=scan_original15m_source(htf.native_15m_closed,as_of_ms=END)
        assert normalize([asdict(x) for x in l_events])==by["c66"][symbol]["all_native15m_source_events"],"C67_C66_ORIGINAL_15M_EVENT_DRIFT"
        cut=OCT_START+DAY+6*TF_MS["1h"]
        idx=(cut-htf.native_15m_closed[0].start_ms)//TF_MS["15m"]
        assert scan_original15m_source(htf.native_15m_closed,as_of_ms=cut)==scan_original15m_source(
            htf.native_15m_closed[:idx],as_of_ms=cut),"C67_PRELOOK_AHEAD_NATIVE15M"
        c60=by["c60"][symbol]["complete_original_source_visit_lifecycle"]
        c63=by["c63"][symbol]["source_parent_rows"]
        c66=by["c66"][symbol]["all_route_a_source_parent_cases"]
        assert len(c46.observations)==len(c60)==len(c63)==len(c66)
        observed=[];counts=Counter();nested=0
        for i,(parent,p60,p63,p66) in enumerate(zip(c46.observations,c60,c63,c66)):
            assert parent.candidate.side==p60["technical_4h_zone_side"]
            assert parent.candidate.fully_known_ms==p60["zone_known_ms"]
            assert parent.first_contact_original3m_id==p60["first_contact_original3m_id"]
            oldc63=source_first_any_after_contact(
                symbol=symbol,side=parent.candidate.side,
                zone_known_ms=parent.candidate.fully_known_ms,
                first_original3m_id=parent.first_contact_original3m_id,
                first_contact_known_ms=parent.first_contact_closed_known_ms,
                events=h_events,as_of_ms=END)
            assert normalize(asdict(oldc63))=={k:v for k,v in p63.items() if
                k not in ("original_4h_parent_index","parent_original_three_3m_source_IDs")},"C67_C63_FIRST_ANY_ORIGINAL_DRIFT"
            assert p66["original_c46_4h_source_parent_index"]==i
            v=route_a_fork_1h_to_15m(parent,htf.derived_1h_closed,
                         htf.native_15m_closed,h_events,l_events,as_of_ms=END)
            assert v.state in FORK_STATES
            assert v.symbol==symbol and v.original_4h_source_side==parent.candidate.side
            assert not(v.author_4h_poi_first_valid_test or v.author_1h_trigger or
                       v.author_new_1h_vc_poi or v.author_new_1h_poi_first_valid_test or
                       v.author_15m_volume_confirmation or v.author_5m_volume_confirmation or
                       v.author_stronghl or v.route_b_idm_used or v.route_c_raid_bos_used or
                       v.orders or v.fills or v.trades)
            if v.source_first_new_1h_poi_test_native15m_id is not None:
                assert v.source_first_new_1h_poi_test_closed_ms is not None
                assert v.first_source_1h_known_ms<=v.source_first_new_1h_poi_test_closed_ms
            if v.first_15m_after_gate_known_ms is not None:
                assert v.first_15m_after_gate_kind is not None
            nested+=v.nested_1h_imb_4h_trigger_vetoed
            counts[v.state]+=1
            observed.append({"original_c46_parent_index":i,
                "c63_first_any_1h_source_class":oldc63.status,
                "c66_15m_first_any_source_class":p66["route_a_branch_status"],
                **asdict(v)})
        assert sum(counts.values())==len(c46.observations)
        assert counts["NO_4H_SOURCE_FIRST_TOUCH"]==by["c46"][symbol][
             "source_only_4h_classic_imb_first_contact"]["untouched_candidate_count"]
        nested_total+=nested;grand.update(counts)
        markets.append({
            "symbol":symbol,
            "native3m_original_closed":15360,
            "native15m_original_closed":3072,
            "native1d_original_closed":32,
            "derived1h_closed":768,
            "C46_4h_parent_count":len(observed),
            "C66_full_15m_source_event_parity":len(l_events),
            "source_state_counts":{s:counts[s] for s in FORK_STATES},
            "source_1h_imb_nested_in_4h_trigger_veto_occurrences":nested,
            "all_original_parent_source_route_a_fork_cases":observed,
            "author_verified_goldens":0,"orders":0,"fills":0,"trades":0,
            "readiness":"NOT_TRADE_READY"})
        print("C67",symbol,dict(sorted(counts.items())),
              "nested_1h_imb_veto",nested,flush=True)
    assert sum(x["C46_4h_parent_count"] for x in markets)==153
    assert sum(x["native3m_original_closed"] for x in markets)==76800
    assert sum(x["native15m_original_closed"] for x in markets)==15360
    assert sum(x["native1d_original_closed"] for x in markets)==160
    assert sum(x["derived1h_closed"] for x in markets)==3840
    assert sum(grand[s] for s in FORK_STATES)==153
    assert grand["NO_4H_SOURCE_FIRST_TOUCH"]==21
    document={
       "schema":"EMBER_C67_ORIGINAL_BINANCE45ZIP_ROUTE_A_1H_TRIGGER_VS_NEW_POI_FIRST_TEST_NATIVE15M_SOURCE_FORK_V1",
       "market":"CRYPTO_ONLY_BINANCE_USDM_SHA_CHECKED_SOURCE_NO_AUTHOR_TRADE",
       "period_utc":["2026-09-01","2026-10-02"],
       "original_archives":{"native3m":15,"native15m":15,"native1d":15,"total":45},
       "native3m_original_closed":76800,
       "native15m_original_closed":15360,
       "native1d_original_closed":160,
       "derived1h_closed":3840,
       "original_c46_4h_parent_count":153,
       "source_route_a_fork_parent_status_totals":{s:grand[s] for s in FORK_STATES},
       "nested_1h_imb_4h_trigger_veto_source_occurrences":nested_total,
       "all_c46_c60_c62_c63_c66_price_and_SHA_source_IDs_match":True,
       "frozen_old_source_git_blobs":SOURCE_GIT_BLOBS,
       "source_first_1h_trigger_definition":"CLOSED 1H wick-only raid on PREKNOWN UNSWEPT strict1H SSL/BSL OR 3-bar 1H IMB NOT wholly contained in 4H IMB parent; source-only no author trigger",
       "source_first_new_1h_vc_poi_definition":"C62 SNR/RB/IMB source context formed only after 4H source first native3m touch; pair wick or three1h gap envelope is NOT author-selected POI",
       "source_poi_retest_definition":"FIRST following fully closed original native15m wick overlap strictly AFTER source 1H event full close; this is NOT owner first VALID POI test or a trade",
       "source_first_15m_after_new_poi_test_definition":"first ANY source 15m SNR/IMB pattern starting AFTER closed 15m source wick contact; opposing direction and equal-time ties preserved",
       "1h_allowed_imb_also_context_ambiguous":"1H gap eligible nonnested is not automatically trigger rather than new1H VC; same timestamp fork is ambiguous and NOT executable",
       "route_a_4h_poi_first_valid_test_author":0,
       "route_a_owner_1h_raid_or_imb_trigger_confirmed":0,
       "route_a_owner_new_1h_VC_POI_confirmed":0,
       "route_a_owner_first_valid_new1h_POI_test_confirmed":0,
       "route_a_owner_15m_final_VC_confirmed":0,
       "route_a_owner_5m_final_VC_confirmed":0,
       "owner_positive_crypto_candle_goldens":0,
       "route_b_idm_unchanged":True,"route_c_raid_bos_unchanged":True,
       "author_strongHL":0,"author_FTA_SL_TP":0,
       "orders":0,"fills":0,"trades":0,"PnL":None,
       "readiness":"NOT_TRADE_READY",
       "markets":markets}
    data=(json.dumps(document,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode()
    if output:
        target=Path(output);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    if PIN.exists():
        assert PIN.read_bytes()==data,"C67_FROZEN_ORIGINAL45ZIP_REPLAY_DRIFT"
    print("C67_SOURCE_TOTALS",json.dumps(document["source_route_a_fork_parent_status_totals"],sort_keys=True))
    print("C67_NESTED_1H_IMB_VETO",nested_total)
    print("C67_BYTES",len(data))
    return document
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
