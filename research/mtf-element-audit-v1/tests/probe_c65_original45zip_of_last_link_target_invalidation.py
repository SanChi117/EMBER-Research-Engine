#!/usr/bin/env python3
"""C65 original SHA-checked Binance USD-M 45 ZIP, CLOSED source OF chain.

Re-derive ALL C46 4H parents, C62 1H SNR/RB/IMB, C63 first ANY
reactions, C64 native3m source anchors, verify full immutably frozen family,
and THEN ask if both source liquidity and IMB work, distinct pre-known
source pivot, and prior CLOSED native1d HTF target exist before scanning
after target for first ANY source OF invalidation proxy.

Never label academic Strong High/Low, Order Flow, target, POI, BOS or trades.
"""
import sys,json
from pathlib import Path
from collections import Counter
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
for x in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/x))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import (
    extended_32day_prefix,END,OCT_START,DAY,TF_MS)
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
from c62_academic_snr_rb_imb_liquidity_source_separation import observe_hourly_source_poi_split
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    convert_c62_closed_source_events,source_first_any_after_contact)
from c64_original3m_source_protected_extreme_invalidation import (
    inspect_original_source_protected_extreme)
from c65_of_last_link_target_invalidation_source import (
    source_of_last_link_target_invalidation,STATES)
def load(n):
    root={
      "C46":"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json",
      "C60":"evidence/c60/C60_ORIGINAL45ZIP_4H_IMB_FIRST_AND_RETURN_SOURCE_NATIVE3M_EPISODES.json",
      "C62":"evidence/c62/C62_ORIGINAL_45ZIP_1H_SNR_RB_MB_IMB_LIQUIDITY_COMPLETE_SOURCE.json",
      "C63":"evidence/c63/C63_ORIGINAL45ZIP_FIRST_ANY_CLOSED1H_SOURCE_AFTER_4H_FIRST_NATIVE3M_CONTACT.json",
      "C64":"evidence/c64/C64_ORIGINAL45ZIP_STRICT_SOURCE_EXTREME_PRECONFIRM_POST_WICK_CLOSE_INVALIDATION.json"
    }
    return json.loads((ROOT/root[n]).read_bytes())
PIN=ROOT/"evidence/c65/C65_ORIGINAL45ZIP_OF_SOURCE_LAST_LINK_HTF_TARGET_FIRST_ANY_INVALIDATION.json"
BLOBS={
    "C46":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
    "C60":"899373e4a1dc1999d1485ac8c1f790d39071aebd",
    "C62":"8428bf7d6cd3bc26f617cfc32a34c91a27c813b2",
    "C63":"fdc77c7ec942f03b4efae83b935d994c8435a24f",
    "C64":"f70b0493a0c4964c618c09c75fee900dd65f5c05"}
def canonical(x):return json.loads(json.dumps(x,sort_keys=True))
def run(output=None):
    d={k:load(k) for k in BLOBS}
    c46={x["symbol"]:x for x in d["C46"]["markets"]}
    c60={x["symbol"]:x for x in d["C60"]["markets"]}
    c62={x["symbol"]:x for x in d["C62"]["markets"]}
    c63={x["symbol"]:x for x in d["C63"]["markets"]}
    c64={x["symbol"]:x for x in d["C64"]["markets"]}
    assert all(set(q)==set(SYMS) for q in (c46,c60,c62,c63,c64))
    assert d["C46"]["source_candidate_4h_IMB_count"]==d["C64"]["original_4h_technical_source_parents"]==153
    markets=[];allcounts=Counter()
    CUT=OCT_START+DAY+TF_MS["1h"]
    cutoff_checked=0
    for symbol in sorted(SYMS):
        orig={tf:tuple(load_original(symbol,tf,period,t)[0]
          for period,t in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(orig["15m"],orig["1d"],END)
        native=reconcile_native_3m(tuple(native_3m(symbol,period)[0] for period in PERIODS),
                                    htf,as_of_ms=END)
        assert len(native.original_3m_closed)==15360
        assert native.native_15m_ohlcv_equalities==3072
        assert len(htf.derived_1h_closed)==768 and len(htf.native_1d_closed)==32
        c46_replay=inspect_original_4h_imb_source(native,as_of_ms=END)
        assert canonical(asdict(c46_replay))==c46[symbol]["source_only_4h_classic_imb_first_contact"],"C65_C46_CRYPTO_SOURCE_DRIFT"
        c62_replay=observe_hourly_source_poi_split(htf.derived_1h_closed,as_of_ms=END)
        assert canonical([asdict(x) for x in c62_replay["technical_1h_snr_rb_separate_cases"]])==c62[symbol]["source_cases"],"C65_C62_SOURCE_BLOCKS_DRIFT"
        assert canonical([asdict(x) for x in c62_replay["technical_original_1h_imb_gaps"]])==c62[symbol]["source_gaps"],"C65_C62_GAPS_DRIFT"
        events=convert_c62_closed_source_events(c62_replay,htf.derived_1h_closed,as_of_ms=END)
        parent60=c60[symbol]["complete_original_source_visit_lifecycle"]
        parents63=c63[symbol]["source_parent_rows"]
        parents64=c64[symbol]["parent_source_protected_extreme_cases"]
        assert len(parent60)==len(parents63)==len(parents64)==len(c46_replay.observations)
        local=Counter();obs=[]
        for i,(p,v,a63,a64) in enumerate(zip(c46_replay.observations,parent60,parents63,parents64)):
            assert p.candidate.fully_known_ms==v["zone_known_ms"]
            assert p.first_contact_original3m_id==v["first_contact_original3m_id"]
            chain=source_first_any_after_contact(symbol=symbol,
              side=p.candidate.side,zone_known_ms=p.candidate.fully_known_ms,
              first_original3m_id=p.first_contact_original3m_id,
              first_contact_known_ms=p.first_contact_closed_known_ms,
              events=events,as_of_ms=END)
            assert canonical(asdict(chain))=={
                k:val for k,val in a63.items() if k not in (
                  "original_4h_parent_index","parent_original_three_3m_source_IDs")
            },"C65_C63_FIRST_ANY_PARENT_DRIFT"
            if p.first_contact_closed_known_ms is None:
                physical=native.original_3m_closed
            else:
                j=(p.first_contact_closed_known_ms-THREE-
                   native.original_3m_closed[0].start_ms)//THREE
                physical=native.original_3m_closed[j:]
                assert physical[0].raw_id==p.first_contact_original3m_id
            a=inspect_original_source_protected_extreme(
                chain,physical,htf.derived_1h_closed,as_of_ms=END)
            assert canonical(asdict(a))=={
               k:val for k,val in a64.items() if k not in (
               "original_4h_parent_index","first_any_source_event_status")
            },"C65_C64_ORIGINAL_3M_SOURCE_ANCHOR_DRIFT"
            review=source_of_last_link_target_invalidation(
                a,htf.derived_1h_closed,htf.native_1d_closed,
                c62_replay["technical_1h_snr_rb_separate_cases"],
                events,as_of_ms=END)
            assert review.state in STATES
            assert not any((review.author_last_of_link_verified,
                 review.author_htf_target_verified,review.author_opposite_poi_verified,
                 review.author_of_invalidation_verified,review.author_stronghl_verified,
                 review.orders,review.trades))
            local[review.state]+=1
            if review.source_htf_target_first_wick_reached_ms is not None:
                local["source_htf_target_reached"]+=1
            if review.source_last_link_price is not None:
                local["source_preknown_last_fractal_link_price_present"]+=1
            if review.source_first_any_invalidation_known_ms is not None:
                local["source_first_any_invalidation_proxy_found"]+=1
            if not review.full_source_48h_window and review.source_window_end_ms is not None:
                local["source_48h_right_censored"]+=1
            # A controlled physical cutoff cannot see future source event
            # and cannot silently include a future daily high/low.
            if (a.source_status=="SOURCE_ANCHOR_KNOWN_AT_REACTION_CLOSE"
                and a.source_event_known_ms<=CUT and cutoff_checked<5):
                allhours=htf.derived_1h_closed
                hprefix=tuple(x for x in allhours if x.known_at_ms<=CUT)
                dayprefix=tuple(x for x in htf.native_1d_closed if x.known_at_ms<=CUT)
                eventprefix=tuple(x for x in events if x.fully_known_ms<=CUT)
                prefix_a=source_of_last_link_target_invalidation(
                   a,allhours,dayprefix,c62_replay["technical_1h_snr_rb_separate_cases"],
                   eventprefix,as_of_ms=CUT)
                prefix_b=source_of_last_link_target_invalidation(
                   a,hprefix,dayprefix,c62_replay["technical_1h_snr_rb_separate_cases"],
                   eventprefix,as_of_ms=CUT)
                assert prefix_a==prefix_b,"C65_PHYSICAL_ORIGINAL1H_CUTOFF_FUTURE_LEAK"
                cutoff_checked+=1
            obs.append({"original_4h_parent_index":i,
                 "original_source_parent_first_any_status":chain.status,
                 "original_source_c64_anchor_status":a.source_status,
                 **asdict(review)})
        assert sum(local[x] for x in STATES)==len(obs)
        allcounts.update(local)
        markets.append({"symbol":symbol,"original_native3m_closed":15360,
             "original_native1d_closed":32,"original_native15m_decimal_parities":3072,
             "original_derived_closed1h":768,"original_4h_parent_count":len(obs),
             "source_status_counts":{st:local[st] for st in STATES},
             "source_observation_counts":{k:v for k,v in sorted(local.items()) if k not in STATES},
             "independent_parent_c46_c60_c62_c63_c64_raw_source_identical":True,
             "source_each_original_parent":obs,
             "author_stronghl_goldens":0,"author_OF_invalidation_goldens":0,
             "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"})
        print("C65",symbol,"source_states",{k:local[k] for k in STATES if local[k]},flush=True)
    assert sum(x["original_4h_parent_count"] for x in markets)==153
    assert sum(x["original_native3m_closed"] for x in markets)==76800
    assert sum(x["original_native1d_closed"] for x in markets)==160
    assert sum(x["original_native15m_decimal_parities"] for x in markets)==15360
    assert sum(x["original_derived_closed1h"] for x in markets)==3840
    assert allcounts["NO_C64_CONFIRMED_SOURCE_ANCHOR"]==83
    assert sum(allcounts[st] for st in STATES)==153
    data={
       "schema":"EMBER_C65_ORIGINAL45ZIP_CLOSED_SOURCE_OF_LAST_LINK_PREKNOWN_LIQUIDITY_IMB_HTF_TARGET_FIRST_ANY_INVALIDATION_V1",
       "scope":"CRYPTO_ONLY_FIVE_USDM_FUTURES_SOURCE_RESEARCH_NOT_TRADE_READY",
       "period_utc":["2026-09-01","2026-10-02"],
       "original_sha_checked_zip_archives":{"native3m":15,"native15m":15,"native1d":15,"total":45},
       "original_native3m_closed":76800,"original_native1d_closed":160,
       "exact_original_native15m_decimal_parities":15360,
       "derived_closed1h":3840,"4h_frozen_source_parents":153,
       "original_c64_frozen_source_candidates_after_confirmation":70,
       "source_of_states":{st:allcounts[st] for st in STATES},
       "source_of_observations":{k:v for k,v in sorted(allcounts.items()) if k not in STATES},
       "source_asof_physical_replay_crosschecks":cutoff_checked,
       "original_immutable_provenance_git_blobs":BLOBS,
       "liquidity_requirement":"previous source1h strict pivot raid SNR/RB case known before source link, same direction; bare strict fractal does not count worked liquidity",
       "imb_requirement":"previous source1h wick-only FVG work SNR/RB case, not merely created source FVG",
       "structural_link_requirement":"different earlier confirmed unswept strict 1h pivot, not C64 ad hoc min/max; still ADAPTED source proxy, not author last OF link",
       "target_requirement":"prior fully closed original1d high for LONG or low for SHORT, strictly ahead of source link close; market must actually wick target before invalidation scan",
       "invalidation_requirement":"FIRST ANY after target from closed1h price beyond distinct source last pivot vs opposite source 1h SNR/RB/classic IMB formed wholly after target; equal time both and future events never cherry picked",
       "no_author_labeled_binance_crypto_examples":True,
       "author_OF_links":0,"author_OF_invalidation":0,"author_StrongHL":0,
       "author_SL_TP_FTA":0,"orders":0,"fills":0,"trades":0,"PnL":None,
       "readiness":"NOT_TRADE_READY",
       "markets":markets
    }
    if output:
        target=Path(output);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    if PIN.exists():
        assert PIN.read_bytes()==(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8"),"C65_IMMUTABLE_COMPLETE_SOURCE_DRIFT"
    print("C65_ORIGINAL45ZIP_COMPLETE",json.dumps(data["source_of_states"],sort_keys=True),flush=True)
    return data
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
