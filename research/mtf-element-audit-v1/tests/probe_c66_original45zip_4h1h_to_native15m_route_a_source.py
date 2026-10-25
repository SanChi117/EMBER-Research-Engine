#!/usr/bin/env python3
"""C66 ORIGINAL 45 authenticated Binance USD-M ZIP route-A source study:
4H technical IMB first native3m touch (C46/C60) → first ANY closed1H
technical source context (C62/C63) → 15m original native raw gap or
liquidity/older-IMB worked SNR source ONLY, time 24h fixed.
Always non-tradable: no author 4H POI test, 1H trigger vs VC branch,
actual new 1H POI retest, 15m volume-confirmation, StrongHL or FTA/SL/TP.
No mixing Route B IDM or C raid→BOS.
"""
import sys,json,hashlib
from pathlib import Path
from dataclasses import asdict
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
for name in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/name))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY,TF_MS
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
from c62_academic_snr_rb_imb_liquidity_source_separation import observe_hourly_source_poi_split
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    convert_c62_closed_source_events,source_first_any_after_contact)
from c66_native15m_route_a_source_event_chain import (
    scan_original15m_source,route_a_15m_source_review,KINDS,STATES)
OLD={
 "c46":ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json",
 "c60":ROOT/"evidence/c60/C60_ORIGINAL45ZIP_4H_IMB_FIRST_AND_RETURN_SOURCE_NATIVE3M_EPISODES.json",
 "c62":ROOT/"evidence/c62/C62_ORIGINAL_45ZIP_1H_SNR_RB_MB_IMB_LIQUIDITY_COMPLETE_SOURCE.json",
 "c63":ROOT/"evidence/c63/C63_ORIGINAL45ZIP_FIRST_ANY_CLOSED1H_SOURCE_AFTER_4H_FIRST_NATIVE3M_CONTACT.json",
 "c65":ROOT/"evidence/c65/C65_ORIGINAL45ZIP_OF_SOURCE_LAST_LINK_HTF_TARGET_FIRST_ANY_INVALIDATION.json"}
FROZEN_GIT_BLOBS={
"C46":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
"C60":"899373e4a1dc1999d1485ac8c1f790d39071aebd",
"C62":"8428bf7d6cd3bc26f617cfc32a34c91a27c813b2",
"C63":"fdc77c7ec942f03b4efae83b935d994c8435a24f",
"C65":"791f20fcf0a8d6c4697f02fd7247b45cfd4b6de5"}
PIN=ROOT/"evidence/c66/C66_ORIGINAL45ZIP_4H1H_TO_NATIVE15M_SOURCE_FIRST_ANY_ROUTE_A.json"
def _canon(x):return json.loads(json.dumps(x,sort_keys=True))
def run(output=None):
    old={k:json.loads(x.read_bytes()) for k,x in OLD.items()}
    assert old["c46"]["source_candidate_4h_IMB_count"]==153
    assert old["c62"]["source_derived_closed_1h_bars"]==3840
    assert old["c63"]["4h_source_parent_candidates"]==153
    per={k:{x["symbol"]:x for x in old[k]["markets"]} for k in old}
    assert all(set(x)==set(SYMS) for x in per.values())
    markets=[];tot=Counter();kinds=Counter()
    for symbol in sorted(SYMS):
        original={tf:tuple(load_original(symbol,tf,p,t)[0]
          for p,t in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(original["15m"],original["1d"],END)
        archive=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        native=reconcile_native_3m(archive,htf,as_of_ms=END)
        assert len(native.original_3m_closed)==15360
        assert native.native_15m_ohlcv_equalities==3072
        assert len(htf.native_15m_closed)==3072
        assert len(htf.native_1d_closed)==32
        assert len(htf.derived_1h_closed)==768
        original15=htf.native_15m_closed
        events15=scan_original15m_source(original15,as_of_ms=END)
        # Every emitted 15m event is auditable against exact original
        # native15m bar + SHA from the source, not generated price bars.
        by15={x.start_ms:x for x in original15}
        for ev in events15:
            assert ev.kind in KINDS
            assert by15[ev.pattern_start_ms].origin_raw_row_id==ev.first_original15m_id
            assert by15[ev.known_ms-TF_MS["15m"]].origin_raw_row_id==ev.last_original15m_id
            assert not(ev.author_entry or ev.author_volume_confirmation or ev.orders or ev.trades)
            kinds[ev.kind]+=1
        CUT=OCT_START+DAY+6*TF_MS["1h"]
        idx=(CUT-original15[0].start_ms)//TF_MS["15m"]
        assert 0<idx<len(original15)
        assert scan_original15m_source(original15,as_of_ms=CUT)==scan_original15m_source(
            original15[:idx],as_of_ms=CUT),"C66_FUTURE_LEAK_NATIVE15M_EVENT_PREFIX"
        c46=inspect_original_4h_imb_source(native,as_of_ms=END)
        assert _canon(asdict(c46))==per["c46"][symbol]["source_only_4h_classic_imb_first_contact"],"C66_C46_PRICE_DRIFT"
        c62=observe_hourly_source_poi_split(htf.derived_1h_closed,as_of_ms=END)
        assert _canon([asdict(x) for x in c62["technical_1h_snr_rb_separate_cases"]])==per["c62"][symbol]["source_cases"],"C66_C62_SOURCE_CASE_DRIFT"
        assert _canon([asdict(x) for x in c62["technical_original_1h_imb_gaps"]])==per["c62"][symbol]["source_gaps"],"C66_C62_GAP_DRIFT"
        events1=convert_c62_closed_source_events(c62,htf.derived_1h_closed,as_of_ms=END)
        old60=per["c60"][symbol]["complete_original_source_visit_lifecycle"]
        old63=per["c63"][symbol]["source_parent_rows"]
        assert len(c46.observations)==len(old60)==len(old63)
        cases=[];counts=Counter()
        for i,(p,v,z) in enumerate(zip(c46.observations,old60,old63)):
            assert p.first_contact_original3m_id==v["first_contact_original3m_id"]
            assert p.candidate.fully_known_ms==v["zone_known_ms"]
            assert p.candidate.side==v["technical_4h_zone_side"]
            c63=source_first_any_after_contact(
                symbol=symbol,side=p.candidate.side,
                zone_known_ms=p.candidate.fully_known_ms,
                first_original3m_id=p.first_contact_original3m_id,
                first_contact_known_ms=p.first_contact_closed_known_ms,
                events=events1,as_of_ms=END)
            assert _canon(asdict(c63))=={k:x for k,x in z.items()
                if k not in ("original_4h_parent_index","parent_original_three_3m_source_IDs")}
            c66=route_a_15m_source_review(c63,events15,as_of_ms=END)
            assert c66.route_a_branch_status in STATES
            assert not(c66.route_a_author_4h_poi_test or
                c66.route_a_author_1h_trigger or
                c66.route_a_author_new_1h_vc_poi_test or
                c66.route_a_author_15m_vc or c66.route_b_idm_evaluated or
                c66.route_c_raid_bos_evaluated or c66.author_15m_stronghl or
                c66.orders or c66.fills or c66.trades)
            counts[c66.route_a_branch_status]+=1
            cases.append({"original_c46_4h_source_parent_index":i,
                "C63_original_1h_source_status":c63.status,
                **asdict(c66)})
        assert sum(counts[s] for s in STATES)==len(c46.observations)
        assert counts["NO_4H_FIRST_SOURCE_TOUCH"]==per["c46"][symbol]["source_only_4h_classic_imb_first_contact"]["untouched_candidate_count"]
        tot.update(counts)
        markets.append({"symbol":symbol,"original_native3m_closed":15360,
            "original_native15m_closed":3072,"original_native1d_closed":32,
            "derived_closed1h":768,"original_c46_4h_parent_count":len(cases),
            "all_native15m_source_events":len(events15),
            "source_native15m_type_counts":dict(Counter(x.kind for x in events15)),
            "native15m_physical_prefix_equals_logical_asof":True,
            "all_native15m_original_source_events":[asdict(x) for x in events15],
            "all_route_a_source_parent_cases":cases,
            "original_source_parent_statuses":{s:counts[s] for s in STATES},
            "owner_approved_golden_poi":0,
            "owner_approved_15m_VC":0,"orders":0,"fills":0,"trades":0,
            "readiness":"NOT_TRADE_READY"})
        print("C66",symbol,"15m",len(events15),dict(sorted(counts.items())),flush=True)
    assert sum(x["original_c46_4h_parent_count"] for x in markets)==153
    assert sum(x["original_native3m_closed"] for x in markets)==76800
    assert sum(x["original_native15m_closed"] for x in markets)==15360
    assert sum(x["original_native1d_closed"] for x in markets)==160
    assert sum(x["derived_closed1h"] for x in markets)==3840
    assert sum(tot[s] for s in STATES)==153
    assert tot["NO_4H_FIRST_SOURCE_TOUCH"]==21
    doc={
      "schema":"EMBER_C66_FROZEN_ORIGINAL45ZIP_CRYPTO_4H1H_NATIVE15M_ROUTE_A_SOURCE_ONLY_FIRST_ANY_V1",
      "market":"BINANCE_USDM_FUTURES_SOURCE_ONLY_PAPER",
      "period_utc":["2026-09-01","2026-10-02"],
      "original_sha_checked_zip":{"native3m":15,"native15m":15,"native1d":15,"total":45},
      "original_native3m_closed":76800,"original_native15m_closed":15360,
      "original_native1d_closed":160,"derived_closed1h":3840,
      "original_4h_c46_contexts":153,
      "source_15m_event_type_totals":{k:kinds[k] for k in KINDS},
      "source_4h1h15m_first_any_route_a_counts":{s:tot[s] for s in STATES},
      "original_frozen_source_blobs":FROZEN_GIT_BLOBS,
      "academic_gate":"4H parent original IMB is technical not owner POI; 1H first ANY source event is neither verified 1H trigger nor owner VC new POI; no author first valid POI retest, so 15M IMB/SNR source may NOT be classified as a trade or as academic 15m VC",
      "route_a_trigger_context_not_proven":True,
      "route_a_ltf_15m_source_events_are_NOT_final_entries":True,
      "route_b_idm_untouched":True,"route_c_3m5m_raid_bos_untouched":True,
      "golden_author_price_cases":0,
      "author_final_entry_approved":0,
      "author_vc_15m_confirmed":0,
      "author_StrongHL":0,"author_SL_TP_FTA":0,
      "orders":0,"fills":0,"trades":0,"PnL":None,
      "readiness":"NOT_TRADE_READY",
      "markets":markets}
    if output:
        dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    if PIN.exists():
        assert PIN.read_bytes()==(
            json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
        ).encode("utf-8"),"C66_FROZEN_ORIGINAL45_SOURCE_DRIFT"
    print("C66_SUMMARY",json.dumps(doc["source_4h1h15m_first_any_route_a_counts"],sort_keys=True))
    print("C66_EVENT_TYPES",json.dumps(doc["source_15m_event_type_totals"],sort_keys=True))
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
