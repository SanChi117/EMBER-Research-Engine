#!/usr/bin/env python3
"""C73 after signed ORIGINAL 60 ZIP: count distinct 3m POI visit episodes BEFORE next candidate15m pattern, never upgrade source to author first valid test or decide Trigger/VC.

C72 independently downloaded ORIGINAL Binance native5m ZIP, 3:1 15m parity and first ANY after C71 provisional Route A 15m.

C71 Route A after ORIGINAL source3m contact and full1H closed -> first ANY source15m IMB/SNR vs source1H BOS.

C70 exact FIRST original native3m wick inside independently verified C69 native15m.

C69 first original native15m liquidity raid bar or new 1H POI source test.

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
    first_original_native15m_source_contact,STATES as OLD69_STATES)
from c70_exact_native3m_first_raid_or_poi_source_wick import (
    original3m_first_wick_within_c69,STATES as OLD70_STATES)
from c71_post_contact_closed_15m_vc_1h_bos_semantic_gate import (
    classify_after_original3m_contact,STATES as OLD71_STATES)
from c72_original_native5m_source_vc_after15m_gate import (
    original5m_url,parse_original5m_zip,reconcile_original5m_to_native15m,
    scan_original5m_source_events,first_any_5m_after_provisional15m,STATES as OLD72_STATES)
from c73_new1h_poi_original3m_visit_episodes_route_split import (
    evaluate_new1h_source_poi_first_visit_and_route,STATES)
import urllib.request,urllib.parse
from strict_vision_d04 import _SingleHostRedirect
def checked_new5m(url,limit=25000000):
    # D04 legacy parse_url explicitly restricts historical source tfs to
    # 3m/15m/1d; NEW genuine native5m needs independently pinned host path.
    if not isinstance(url,str) or not url.startswith("https://data.binance.vision/"):
        raise ValueError("C72_FORBIDDEN_NEW5M_HOST")
    original=url[:-9] if url.endswith(".CHECKSUM") else url
    from c72_original_native5m_source_vc_after15m_gate import original5m_url
    a=original.rsplit("/",1)[-1]
    parts=a.split("-5m-")
    if len(parts)!=2 or not parts[1].endswith(".zip"):
        raise ValueError("C72_FORBIDDEN_NEW5M_NAME")
    symbol=parts[0];period=parts[1][:-4]
    if original!=original5m_url(symbol,period):
        raise ValueError("C72_FORBIDDEN_NEW5M_PATH")
    opener=urllib.request.build_opener(_SingleHostRedirect())
    with opener.open(urllib.request.Request(url,headers={
        "User-Agent":"EMBER-C72-original-native5m-source-readonly/1.0"}),timeout=40) as response:
        remote=urllib.parse.urlsplit(response.geturl())
        if remote.scheme!="https" or remote.netloc!="data.binance.vision":
            raise ValueError("C72_CROSS_HOST_REDIRECT")
        data=response.read(limit+1)
    if not 0<len(data)<=limit:raise ValueError("C72_MISSING_OR_OVERSIZE_ORIGINAL_5M")
    return data
OLD={
"c46":ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json",
"c60":ROOT/"evidence/c60/C60_ORIGINAL45ZIP_4H_IMB_FIRST_AND_RETURN_SOURCE_NATIVE3M_EPISODES.json",
"c62":ROOT/"evidence/c62/C62_ORIGINAL_45ZIP_1H_SNR_RB_MB_IMB_LIQUIDITY_COMPLETE_SOURCE.json",
"c63":ROOT/"evidence/c63/C63_ORIGINAL45ZIP_FIRST_ANY_CLOSED1H_SOURCE_AFTER_4H_FIRST_NATIVE3M_CONTACT.json",
"c66":ROOT/"evidence/c66/C66_ORIGINAL45ZIP_4H1H_TO_NATIVE15M_SOURCE_FIRST_ANY_ROUTE_A.json",
"c67":ROOT/"evidence/c67/C67_ORIGINAL45ZIP_ROUTE_A_1H_TRIGGER_NEW_POI_15M_FIRST_RETEST_FORK.json",
"c68":ROOT/"evidence/c68/C68_ORIGINAL45ZIP_STRONGHL_POST_CONTACT_FIRST_ANY_15M_VC_OR_1H_BOS_SOURCE.json",
"c69":ROOT/"evidence/c69/C69_ORIGINAL45ZIP_FIRST_NATIVE15M_LIQUIDITY_RAID_OR_NEW1H_POI_SOURCE_TEST.json",
"c70":ROOT/"evidence/c70/C70_ORIGINAL45ZIP_EXACT_FIRST_NATIVE3M_WICK_WITHIN_C69_15M_SOURCE.json",
"c71":ROOT/"evidence/c71/C71_ORIGINAL45ZIP_3M_CONTACT_THEN_FIRST_ANY_15M_VC_OR_1H_BOS_SOURCE.json",
"c72":ROOT/"evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json"
}
FROZEN_BLOBS={
"C46":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
"C60":"899373e4a1dc1999d1485ac8c1f790d39071aebd",
"C62":"8428bf7d6cd3bc26f617cfc32a34c91a27c813b2",
"C63":"fdc77c7ec942f03b4efae83b935d994c8435a24f",
"C66":"c693058cdb28b0e118879d32ddcbbd0d2a66bfc6",
"C67":"87409101a6fad4897b32e13085c9a0cc13566594",
"C68":"587779a7dd1736099e8270c8823c15822f0e77a0",
"C69":"b22860dfa13e4b19d16e8dd892719a772485e847",
"C70":"e100ca8a70a32484fd311ae2dcf31a311d85865c",
"C71":"ef05ecdcfb31e59dec79d10eb5d3dc40b3c3af97",
"C72":"19b7e0357600b70b3f26467339a417e0f99a1302"}
PIN=ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json"
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
        # The three NEW, genuinely native Binance USD-M 5m ZIP are NOT
        # resampled from original3m or source15m. Independent raw source.
        original5=[];original5_proof=[]
        for period in PERIODS:
            url=original5m_url(symbol,period)
            raw=checked_new5m(url,25000000)
            check=checked_new5m(url+".CHECKSUM",1024)
            a=parse_original5m_zip(symbol,period,raw,check)
            original5.append(a)
            original5_proof.append({"period":period,"url":url,
                "same_host_checksum_sha_verified":True,
                "zip_sha256":a.zip_sha,"raw_csv_sha256":a.csv_sha,
                "native5m_bars":len(a.rows)})
        five=reconcile_original5m_to_native15m(
            tuple(original5),htf.native_15m_closed,as_of_ms=END)
        assert five.native15m_3_to_1_decimal_equalities==3072
        assert len(five.rows)==9216
        events5=scan_original5m_source_events(five)
        c60=by["c60"][symbol]["complete_original_source_visit_lifecycle"]
        c63=by["c63"][symbol]["source_parent_rows"]
        c67=by["c67"][symbol]["all_original_parent_source_route_a_fork_cases"]
        c68=by["c68"][symbol]["original_parent_source_cases"]
        c69=by["c69"][symbol]["original_parent_source_cases"]
        c70=by["c70"][symbol]["original_parent_source_cases"]
        c71=by["c71"][symbol]["original_parent_source_cases"]
        c72=by["c72"][symbol]["original_parent_source_cases"]
        assert len(c46.observations)==len(c60)==len(c63)==len(c67)==len(c68)==len(c69)==len(c70)==len(c71)==len(c72)
        observed=[];status=Counter()
        for i,(parent,p60,p63,p67,p68,p69,p70,p71,p72) in enumerate(zip(c46.observations,c60,c63,c67,c68,c69,c70,c71,c72)):
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
            assert e69.source_status in OLD69_STATES
            assert canon(asdict(e69))=={k:v for k,v in p69.items() if k not in
                ("original_c46_4h_parent_index","c67_route_a_source_fork_state",
                 "c68_original_stronghl_source_status")},"C70_PREVIOUS_C69_SOURCE_FIRST15M_SHA_ID_DRIFT"
            e70=original3m_first_wick_within_c69(
                e67,e69,htf.native_15m_closed,n3.original_3m_closed,as_of_ms=END)
            assert e70.source_status in OLD70_STATES
            assert canon(asdict(e70))=={k:v for k,v in p70.items() if k not in
               ("original_c46_4h_parent_index","c67_route_a_source_fork_state",
                "c68_original_stronghl_source_status","c69_exact_native15m_source_status")},"C71_C70_ORIGINAL_FIRST3M_SOURCE_ID_DRIFT"
            e71=classify_after_original3m_contact(
                e67,e69,e70,htf.native_15m_closed,n3.original_3m_closed,
                htf.derived_1h_closed,events15,events1,as_of_ms=END)
            assert e71.state in OLD71_STATES and e71.readiness=="NOT_TRADE_READY"
            assert canon(asdict(e71))=={k:v for k,v in p71.items() if k not in
               ("original_c46_4h_parent_index","c67_route_a_source_fork_state",
                "c68_original_stronghl_source_status","c69_exact_native15m_source_status",
                "c70_exact_native3m_source_status")},"C72_OLD_C71_SOURCE_SHA_PRICE_DRIFT"
            e72=first_any_5m_after_provisional15m(e71,five,events5)
            assert e72.state in OLD72_STATES and e72.readiness=="NOT_TRADE_READY"
            assert canon(asdict(e72))=={k:v for k,v in p72.items() if k not in
                ("original_c46_4h_parent_index","c67_route_a_source_fork_state",
                 "c70_exact_native3m_source_status",
                 "c71_first_any_15m_or_1h_source_status")},"C73_PRIOR_C72_ORIGINAL60_PRICE_SHA_OR_EVENT_DRIFT"
            e73=evaluate_new1h_source_poi_first_visit_and_route(
                e67,e69,e70,e71,e72,n3.original_3m_closed,
                htf.native_15m_closed,htf.derived_1h_closed,events15,
                events1,five,events5,as_of_ms=END)
            assert e73.state in STATES and e73.readiness=="NOT_TRADE_READY"
            assert not(e73.author_1h_poi_valid_first_test or e73.author_15m_trigger
                or e73.author_15m_vc or e73.author_5m_vc
                or e73.author_stronghl or e73.author_entry
                or e73.author_structural_sl or e73.route_b_idm_used
                or e73.route_c_raid_bos_used or e73.orders
                or e73.fills or e73.trades)
            if e73.episodes_before_first_15m_pattern is not None:
                assert e73.episodes_before_first_15m_pattern>=1
                assert e73.first_source15m_event_pattern_start_ms>=e73.original_first_source3m_touch_closed_ms
            status[e73.state]+=1
            observed.append({"original_c46_4h_parent_index":i,
                "c67_route_a_source_fork_state":e67.state,
                "c70_exact_native3m_source_status":e70.source_status,
                "c71_first_any_15m_or_1h_source_status":e71.state,
                "c72_post_15m_first_any_5m_source_state":e72.state,
                **asdict(e73)})
        assert sum(status[s] for s in STATES)==len(c46.observations)
        alltotal.update(status)
        market.append({
          "symbol":symbol,"original_native3m_closed":15360,
          "original_native15m_closed":3072,
          "original_native1d_closed":32,"derived_source_closed1h":768,
          "c46_parent_count":len(observed),
          "source_status_totals":{s:status[s] for s in STATES},
          "original_native5m_closed":len(five.rows),
          "original_native5m_to_original15m_3_to_1_equalities":five.native15m_3_to_1_decimal_equalities,
          "original5m_archives":original5_proof,
          "native5m_source_imb_snr_geometries_count":len(events5),
          "original_parent_source_cases":observed,
          "frozen_c46_to_c67_exact_rechecked":True,
          "author_verified_stronghl":0,"orders":0,"fills":0,"trades":0,
          "readiness":"NOT_TRADE_READY"})
        print("C73",symbol,dict(sorted(status.items())),flush=True)
    assert sum(z["c46_parent_count"] for z in market)==153
    assert sum(z["original_native3m_closed"] for z in market)==76800
    assert sum(z["original_native15m_closed"] for z in market)==15360
    assert sum(z["original_native1d_closed"] for z in market)==160
    assert sum(z["derived_source_closed1h"] for z in market)==3840
    assert sum(z["original_native5m_closed"] for z in market)==46080
    assert sum(z["original_native5m_to_original15m_3_to_1_equalities"] for z in market)==15360
    assert sum(alltotal[s] for s in STATES)==153
    doc={
      "schema":"EMBER_C73_ORIGINAL_BINANCE_60ZIP_RAW3M_FIRST_NEW1H_POI_VISIT_EPISODES_BEFORE_SOURCE15M_NO_AUTHOR_V1",
      "market":"BINANCE_USDM_FUTURES_CRYPTO_RESEARCH_ONLY",
      "period_utc":["2026-09-01","2026-10-02"],
      "original_zip_counts":{"native3m":15,"native15m":15,"native1d":15,"new_native5m":15,"total":60},
      "original_native3m_closed":76800,
      "original_native5m_closed":46080,
      "native5m_to_native15m_original_decimal_equalities":15360,
      "source_5m_archives_checksum_proof":{x["symbol"]:x["original5m_archives"] for x in market},
      "original_native15m_closed":15360,
      "original_native1d_closed":160,
      "derived_closed1h":3840,
      "source_4h_C46_parent_count":153,
      "original3m_new1h_poi_first_visit_source_state_totals":{s:alltotal[s] for s in STATES},
      "original_frozen_git_blobs":FROZEN_BLOBS,
      "owner_stronghl_rule":"Real StrongHL requires liquidity OR inefficiency contact then owner VC POI or BOS, NOT strict native15m first technical contact by itself",
      "c69_source_rule":"Earlier C69 first native15m preknown liquidity wick and source new POI first native15m wick is fully independently rechecked before 3m refinement.",
      "c70_source_rule":"C70 immutable first native3m source wick and 15m Decimal parity verified exactly by source IDs",
      "c71_source_rule":"Previous frozen C71 original45 ZIP first ANY source 15m/1h after source3m and closed1h fully rechecked",
      "c72_source_rule":"All prior frozen C72 original60 crypto native5m 3:1 SHA OHLCV and first following source5m event independently rechecked.",
      "c73_source_rule":"Count strictly separate native3m POI source contact EPISODES between genuine earliest 1H-new-POI wick and beginning of 15m candidate pattern; one visit = consecutive bars whose wicks overlap zone, subsequent only after FULL original 3m candle completely outside. No retroactive use of 15m confirmation bars, no cherry-picked repeat or author first VALID POI assumption. Real 15m Trigger vs 15m VC, subsequent 5m VC requires author-labelled semantic proof unavailable.",
      "owner_of_rule":"Actual OF needs both liquidity AND IMB work, last structural link and HTF target; source StrongHL extrema do not prove OF or future profit",
      "asof_source_bar_lineage_verified":True,
      "source_first_native15m_liquidity_raid_index_measured_in_original_source":True,
      "source_first_native3m_wick_independently_checked_inside_first15m":True,
      "source_first_1h_raid_may_not_be_used_until_1h_fully_closed":True,
      "source_new1h_poi_wick_test_not_owner_first_valid_poi_test":True,
      "route_b_idm_untouched":True,"route_c_raid_bos_untouched":True,
      "owner_crypto_labeled_positive_goldens":0,
      "author_verified_technical_first_raid_is_author_valid":0,"author_verified_first_new1h_poi_valid_test":0,
      "author_verified_original3m_first_wick_is_owner_valid":0,
      "author_verified_routeA_15m_vc_or_bos":0,
      "author_verified_native5m_volume_confirmation":0,
      "author_verified_original3m_first_valid_1h_poi_test":0,
      "author_verified_routeA_15m_trigger_or_15m_vc_split":0,
      "source5m_same_host_checksum_not_independent_signature":True,
      "author_verified_new1h_poi_first_valid_test":0,
      "author_verified_5m_vc":0,
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
    if PIN.exists():assert PIN.read_bytes()==data,"C73_FROZEN_ORIGINAL60ZIP_SOURCE_CHANGED"
    print("C73_STATUS_TOTALS",json.dumps(doc["original3m_new1h_poi_first_visit_source_state_totals"],sort_keys=True))
    print("C73_SOURCE_BYTES",len(data))
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
