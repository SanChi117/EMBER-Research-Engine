#!/usr/bin/env python3
"""C69 first original native15m liquidity raid bar or new 1H POI source test.

Source study only. C68 verified source StrongHL remains immutable.

C68 45 original signed crypto ZIP source-only StrongHL prerequisite replay.

All 153 original C46→C60→C62→C63→C66→C67 parent source IDs match frozen
45-ZIP evidence. C68 source contact from genuine original native15m
SHA:timestamp (RAID last bar *proxy* or first NEW 1H POI wick *proxy*),
then first ANY confirmed native15m IMB/SNR or 1H BOS proxy, protected
technical extrema only after event fully closed, pre-confirm wick veto.
ZERO author-certified StrongHL, VC, BOS, SL, trade or performance.
"""
import sys,json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,TF_MS,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
from c62_academic_snr_rb_imb_liquidity_source_separation import observe_hourly_source_poi_split
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    convert_c62_closed_source_events,source_first_any_after_contact)
from c66_native15m_route_a_source_event_chain import scan_original15m_source
from c67_route_a_1h_trigger_vs_new_poi_source_fork import (
    route_a_fork_1h_to_15m,FORK_STATES)
from c68_stronghl_post_contact_vc_bos_source import (
    observe_source_stronghl_after_contact,STATES as OLD68_STATES)
from c69_exact_native15m_first_liquidity_raid_vs_poi_test import (
    first_original_native15m_source_contact,STATES)
OLD={
"c46":ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json",
"c60":ROOT/"evidence/c60/C60_ORIGINAL45ZIP_4H_IMB_FIRST_AND_RETURN_SOURCE_NATIVE3M_EPISODES.json",
"c62":ROOT/"evidence/c62/C62_ORIGINAL_45ZIP_1H_SNR_RB_MB_IMB_LIQUIDITY_COMPLETE_SOURCE.json",
"c63":ROOT/"evidence/c63/C63_ORIGINAL45ZIP_FIRST_ANY_CLOSED1H_SOURCE_AFTER_4H_FIRST_NATIVE3M_CONTACT.json",
"c66":ROOT/"evidence/c66/C66_ORIGINAL45ZIP_4H1H_TO_NATIVE15M_SOURCE_FIRST_ANY_ROUTE_A.json",
"c67":ROOT/"evidence/c67/C67_ORIGINAL45ZIP_ROUTE_A_1H_TRIGGER_NEW_POI_15M_FIRST_RETEST_FORK.json",
"c68":ROOT/"evidence/c68/C68_ORIGINAL45ZIP_STRONGHL_POST_CONTACT_FIRST_ANY_15M_VC_OR_1H_BOS_SOURCE.json"
}
FROZEN_BLOBS={
"C46":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
"C60":"899373e4a1dc1999d1485ac8c1f790d39071aebd",
"C62":"8428bf7d6cd3bc26f617cfc32a34c91a27c813b2",
"C63":"fdc77c7ec942f03b4efae83b935d994c8435a24f",
"C66":"c693058cdb28b0e118879d32ddcbbd0d2a66bfc6",
"C67":"87409101a6fad4897b32e13085c9a0cc13566594",
"C68":"587779a7dd1736099e8270c8823c15822f0e77a0"}
PIN=ROOT/"evidence/c69/C69_ORIGINAL45ZIP_FIRST_NATIVE15M_LIQUIDITY_RAID_OR_NEW1H_POI_SOURCE_TEST.json"
def canon(x):return json.loads(json.dumps(x,sort_keys=True))
def run(output=None):
    old={k:json.loads(v.read_bytes()) for k,v in OLD.items()}
    assert old["c67"]["original_c46_4h_parent_count"]==153
    by={k:{x["symbol"]:x for x in doc["markets"]} for k,doc in old.items()}
    assert all(set(v)==set(SYMS) for v in by.values())
    alltotal=Counter();market=[]
    for symbol in sorted(SYMS):
        src={tf:tuple(load_original(symbol,tf,p,t)[0]
          for p,t in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(src["15m"],src["1d"],END)
        n3=reconcile_native_3m(tuple(native_3m(symbol,p)[0] for p in PERIODS),
                               htf,as_of_ms=END)
        assert len(n3.original_3m_closed)==15360
        assert n3.native_15m_ohlcv_equalities==3072
        assert len(htf.native_15m_closed)==3072 and len(htf.native_1d_closed)==32
        assert len(htf.derived_1h_closed)==768
        c46=inspect_original_4h_imb_source(n3,as_of_ms=END)
        assert canon(asdict(c46))==by["c46"][symbol]["source_only_4h_classic_imb_first_contact"]
        c62=observe_hourly_source_poi_split(htf.derived_1h_closed,as_of_ms=END)
        assert canon([asdict(x) for x in c62["technical_1h_snr_rb_separate_cases"]])==by["c62"][symbol]["source_cases"]
        assert canon([asdict(x) for x in c62["technical_original_1h_imb_gaps"]])==by["c62"][symbol]["source_gaps"]
        events1=convert_c62_closed_source_events(c62,htf.derived_1h_closed,as_of_ms=END)
        events15=scan_original15m_source(htf.native_15m_closed,as_of_ms=END)
        assert canon([asdict(x) for x in events15])==by["c66"][symbol]["all_native15m_original_source_events"]
        c60=by["c60"][symbol]["complete_original_source_visit_lifecycle"]
        c63=by["c63"][symbol]["source_parent_rows"]
        c67=by["c67"][symbol]["all_original_parent_source_route_a_fork_cases"]
        c68=by["c68"][symbol]["original_parent_source_cases"]
        assert len(c46.observations)==len(c60)==len(c63)==len(c67)==len(c68)
        observed=[];status=Counter()
        for i,(parent,p60,p63,p67,p68) in enumerate(zip(c46.observations,c60,c63,c67,c68)):
            assert parent.candidate.fully_known_ms==p60["zone_known_ms"]
            assert parent.candidate.side==p60["technical_4h_zone_side"]
            assert parent.first_contact_original3m_id==p60["first_contact_original3m_id"]
            e63=source_first_any_after_contact(
                symbol=symbol,side=parent.candidate.side,
                zone_known_ms=parent.candidate.fully_known_ms,
                first_original3m_id=parent.first_contact_original3m_id,
                first_contact_known_ms=parent.first_contact_closed_known_ms,
                events=events1,as_of_ms=END)
            assert canon(asdict(e63))=={k:v for k,v in p63.items() if
              k not in ("original_4h_parent_index","parent_original_three_3m_source_IDs")}
            e67=route_a_fork_1h_to_15m(parent,htf.derived_1h_closed,
                htf.native_15m_closed,events1,events15,as_of_ms=END)
            assert canon(asdict(e67))=={k:v for k,v in p67.items() if k not in
              ("original_c46_parent_index","c63_first_any_1h_source_class","c66_15m_first_any_source_class")},"C68_PREVIOUS_C67_BRANCH_SOURCE_DRIFT"
            e68=observe_source_stronghl_after_contact(
                e67,htf.native_15m_closed,events15,events1,as_of_ms=END)
            assert e68.source_status in OLD68_STATES
            assert canon(asdict(e68))=={k:v for k,v in p68.items() if k not in
              ("original_c46_4h_parent_index","c67_route_a_source_fork_state")},"C69_PREVIOUS_C68_SOURCE_DRIFT"
            e69=first_original_native15m_source_contact(
                e67,htf.derived_1h_closed,htf.native_15m_closed,as_of_ms=END)
            assert e69.source_status in STATES
            assert not(e69.author_first_valid_poi_test or
                e69.author_liquidity_raid_confirmed or
                e69.author_stronghl_confirmed or e69.author_sl_level or
                e69.orders or e69.fills or e69.trades)
            if e69.first_exact_original15m_contact_id is not None:
                assert e69.first_exact_original15m_contact_start_ms is not None
                assert e69.first_exact_original15m_contact_closed_ms<=END
            status[e69.source_status]+=1
            observed.append({"original_c46_4h_parent_index":i,
                "c67_route_a_source_fork_state":e67.state,
                "c68_original_stronghl_source_status":e68.source_status,
                **asdict(e69)})
        assert sum(status[s] for s in STATES)==len(c46.observations)
        alltotal.update(status)
        market.append({
          "symbol":symbol,"original_native3m_closed":15360,
          "original_native15m_closed":3072,
          "original_native1d_closed":32,"derived_source_closed1h":768,
          "c46_parent_count":len(observed),
          "source_status_totals":{s:status[s] for s in STATES},
          "original_parent_source_cases":observed,
          "frozen_c46_to_c67_exact_rechecked":True,
          "author_verified_stronghl":0,"orders":0,"fills":0,"trades":0,
          "readiness":"NOT_TRADE_READY"})
        print("C69",symbol,dict(sorted(status.items())),flush=True)
    assert sum(z["c46_parent_count"] for z in market)==153
    assert sum(z["original_native3m_closed"] for z in market)==76800
    assert sum(z["original_native15m_closed"] for z in market)==15360
    assert sum(z["original_native1d_closed"] for z in market)==160
    assert sum(z["derived_source_closed1h"] for z in market)==3840
    assert sum(alltotal[s] for s in STATES)==153
    doc={
      "schema":"EMBER_C69_CRYPTO_ORIGINAL45ZIP_PREKNOWN_SSL_BSL_FIRST_EXACT_NATIVE15M_WICK_RAID_NEW1H_POI_FIRST_SOURCE_TEST_V1",
      "market":"BINANCE_USDM_FUTURES_CRYPTO_RESEARCH_ONLY",
      "period_utc":["2026-09-01","2026-10-02"],
      "original_zip_counts":{"native3m":15,"native15m":15,"native1d":15,"total":45},
      "original_native3m_closed":76800,
      "original_native15m_closed":15360,
      "original_native1d_closed":160,
      "derived_closed1h":3840,
      "source_4h_C46_parent_count":153,
      "source_first_exact_native15m_contact_state_totals":{s:alltotal[s] for s in STATES},
      "original_frozen_git_blobs":FROZEN_BLOBS,
      "owner_stronghl_rule":"Real StrongHL requires liquidity OR inefficiency contact then owner VC POI or BOS, NOT strict native15m first technical contact by itself",
      "c69_source_rule":"Source 1H SSL/BSL raid first exact original native15m wick cross of preknown unswept strict 1H liquidity, verifying OHLCV Decimal parity with containing closed 1H; if 15m closes beyond level and 1H recovers later classify separately; if several levels first crossed in same 15m, ambiguous. New1H source POI first native15m wick test replayed after fully known 1H context, not author valid first test.",
      "owner_of_rule":"Actual OF needs both liquidity AND IMB work, last structural link and HTF target; source StrongHL extrema do not prove OF or future profit",
      "asof_source_bar_lineage_verified":True,
      "source_first_native15m_liquidity_raid_index_measured_in_original_source":True,
      "source_new1h_poi_wick_test_not_owner_first_valid_poi_test":True,
      "route_b_idm_untouched":True,"route_c_raid_bos_untouched":True,
      "owner_crypto_labeled_positive_goldens":0,
      "author_verified_technical_first_raid_is_author_valid":0,"author_verified_first_new1h_poi_valid_test":0,
      "author_verified_VC":0,"author_verified_BOS":0,
      "author_verified_StrongHL":0,"author_verified_OF":0,
      "author_structural_SL_TP_FTA":0,
      "orders":0,"fills":0,"trades":0,"PnL":None,
      "readiness":"NOT_TRADE_READY",
      "markets":market}
    data=(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    if output:
        dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data)
    if PIN.exists():assert PIN.read_bytes()==data,"C69_FROZEN_ORIGINAL45ZIP_SOURCE_CHANGED"
    print("C69_STATUS_TOTALS",json.dumps(doc["source_first_exact_native15m_contact_state_totals"],sort_keys=True))
    print("C69_SOURCE_BYTES",len(data))
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
