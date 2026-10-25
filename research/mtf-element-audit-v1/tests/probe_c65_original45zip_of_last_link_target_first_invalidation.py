#!/usr/bin/env python3
"""C65 full authentic cryptocurrency source: C46/60/62/63/64 exact lineage
to independent previously confirmed 1H structural-link proxy + native1d
prior-day HTF target + first ANY after target opposing source POI or
CLOSED 1H structure-link breach. No actual author OF, StrongHL or orders.
All 45 original Binance USDT-M SHA/CHECKSUM ZIP independently downloaded.
"""
import sys,json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for x in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/x))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,TF_MS
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
from c62_academic_snr_rb_imb_liquidity_source_separation import observe_hourly_source_poi_split
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    convert_c62_closed_source_events,source_first_any_after_contact)
from c64_original3m_source_protected_extreme_invalidation import (
    inspect_original_source_protected_extreme)
from c65_of_last_link_target_invalidation_source import (
    source_of_last_link_target_invalidation,STATES,WINDOW)
OLD={
"c46":ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json",
"c60":ROOT/"evidence/c60/C60_ORIGINAL45ZIP_4H_IMB_FIRST_AND_RETURN_SOURCE_NATIVE3M_EPISODES.json",
"c62":ROOT/"evidence/c62/C62_ORIGINAL_45ZIP_1H_SNR_RB_MB_IMB_LIQUIDITY_COMPLETE_SOURCE.json",
"c63":ROOT/"evidence/c63/C63_ORIGINAL45ZIP_FIRST_ANY_CLOSED1H_SOURCE_AFTER_4H_FIRST_NATIVE3M_CONTACT.json",
"c64":ROOT/"evidence/c64/C64_ORIGINAL45ZIP_STRICT_SOURCE_EXTREME_PRECONFIRM_POST_WICK_CLOSE_INVALIDATION.json"
}
PIN=ROOT/"evidence/c65/C65_ORIGINAL45ZIP_LAST_STRUCTURAL_OF_LINK_FIRST_TARGET_INVALIDATION_SOURCE.json"
SOURCE_BLOBS={
"C46":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
"C60":"899373e4a1dc1999d1485ac8c1f790d39071aebd",
"C62":"8428bf7d6cd3bc26f617cfc32a34c91a27c813b2",
"C63":"fdc77c7ec942f03b4efae83b935d994c8435a24f",
"C64":"f70b0493a0c4964c618c09c75fee900dd65f5c05"}
def canonical(x):return json.loads(json.dumps(x,sort_keys=True))
def run(output=None):
    old={key:json.loads(path.read_bytes()) for key,path in OLD.items()}
    assert old["c46"]["source_candidate_4h_IMB_count"]==153
    assert old["c62"]["source_derived_closed_1h_bars"]==3840
    assert old["c64"]["original_4h_technical_source_parents"]==153
    per={
      k:{x["symbol"]:x for x in old[k]["markets"]}
      for k in old}
    assert all(set(k)==set(SYMS) for k in per.values())
    totals=Counter();markets=[]
    for symbol in sorted(SYMS):
        original={tf:tuple(load_original(symbol,tf,p,t)[0]
          for p,t in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(original["15m"],original["1d"],END)
        archives=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        source=reconcile_native_3m(archives,htf,as_of_ms=END)
        assert len(source.original_3m_closed)==15360
        assert source.native_15m_ohlcv_equalities==3072
        assert len(htf.native_1d_closed)==32 and len(htf.derived_1h_closed)==768
        parents=inspect_original_4h_imb_source(source,as_of_ms=END)
        assert canonical(asdict(parents))==per["c46"][symbol]["source_only_4h_classic_imb_first_contact"],"C65_C46_SOURCE_DRIFT"
        c62=observe_hourly_source_poi_split(htf.derived_1h_closed,as_of_ms=END)
        assert canonical([asdict(x) for x in c62["technical_1h_snr_rb_separate_cases"]])==per["c62"][symbol]["source_cases"],"C65_C62_BLOCK_SOURCE_DRIFT"
        assert canonical([asdict(x) for x in c62["technical_original_1h_imb_gaps"]])==per["c62"][symbol]["source_gaps"],"C65_C62_GAP_SOURCE_DRIFT"
        events=convert_c62_closed_source_events(c62,htf.derived_1h_closed,as_of_ms=END)
        c60=per["c60"][symbol]["complete_original_source_visit_lifecycle"]
        c63=per["c63"][symbol]["source_parent_rows"]
        c64=per["c64"][symbol]["parent_source_protected_extreme_cases"]
        assert len(parents.observations)==len(c60)==len(c63)==len(c64)
        counts=Counter();cases=[]
        for i,(parent,p60,p63,p64) in enumerate(zip(parents.observations,c60,c63,c64)):
            assert parent.candidate.fully_known_ms==p60["zone_known_ms"]
            assert parent.candidate.side==p60["technical_4h_zone_side"]
            assert parent.first_contact_original3m_id==p60["first_contact_original3m_id"]
            prior=source_first_any_after_contact(
                symbol=symbol,side=parent.candidate.side,
                zone_known_ms=parent.candidate.fully_known_ms,
                first_original3m_id=parent.first_contact_original3m_id,
                first_contact_known_ms=parent.first_contact_closed_known_ms,
                events=events,as_of_ms=END)
            assert canonical(asdict(prior))=={k:v for k,v in p63.items()
              if k not in ("original_4h_parent_index","parent_original_three_3m_source_IDs")},"C65_C63_FIRST_ANY_ORIGINAL_DRIFT"
            if parent.first_contact_closed_known_ms is None:
                physically_closed=source.original_3m_closed
            else:
                start=(parent.first_contact_closed_known_ms-THREE-source.original_3m_closed[0].start_ms)//THREE
                assert start>=0
                physically_closed=source.original_3m_closed[start:]
            q=inspect_original_source_protected_extreme(
                prior,physically_closed,htf.derived_1h_closed,as_of_ms=END)
            assert canonical(asdict(q))=={k:v for k,v in p64.items()
              if k not in ("original_4h_parent_index","first_any_source_event_status")},"C65_C64_ORIGINAL_PRICE_SOURCE_DRIFT"
            x=source_of_last_link_target_invalidation(
                q,htf.derived_1h_closed,htf.native_1d_closed,
                c62["technical_1h_snr_rb_separate_cases"],events,as_of_ms=END)
            assert x.state in STATES
            assert not(x.author_last_of_link_verified or x.author_htf_target_verified or
              x.author_opposite_poi_verified or x.author_of_invalidation_verified or
              x.author_stronghl_verified or x.orders or x.trades)
            if x.source_first_any_invalidation_known_ms is not None:
                assert x.source_htf_target_first_wick_reached_ms is not None
                assert x.source_first_any_invalidation_known_ms>x.source_htf_target_first_wick_reached_ms
                assert x.source_original1d_htf_target_known_ms<=q.source_event_known_ms
            if x.source_last_link_price is not None:
                counts["source_link_price_available"]+=1
            if x.source_original1d_htf_target_known_ms is not None:
                counts["prior_closed_original1d_target_available"]+=1
            if x.source_htf_target_first_wick_reached_ms is not None:
                counts["original1h_source_target_wick_reached"]+=1
            counts[x.state]+=1
            cases.append({"original_4h_parent_index":i,
                "C64_source_extreme_status":q.source_status,
                **asdict(x)})
        assert sum(counts[k] for k in STATES)==len(cases)
        assert counts[STATES[0]]>=per["c64"][symbol]["source_status_totals"]["NO_ORIGINAL_4H_FIRST_CONTACT"]
        totals.update(counts)
        markets.append({"symbol":symbol,"original_native3m_closed":15360,
          "original_native1d_closed":32,
          "native15m_exact_decimal_parity":3072,"closed_source1h":768,
          "original_4h_parents":len(cases),
          "source_last_link_and_htf_target_status_totals":{s:counts[s] for s in STATES},
          "technical_source_auxiliary_counts":{k:v for k,v in sorted(counts.items()) if k not in STATES},
          "all_153_original_C46_C60_C62_C63_C64_source_parents_frozen":True,
          "original_parent_source_chains":cases,
          "author_goldens":0,"orders":0,"fills":0,"trades":0,
          "readiness":"NOT_TRADE_READY"})
        print("C65",symbol,dict(sorted(counts.items())),flush=True)
    assert sum(x["original_4h_parents"] for x in markets)==153
    assert sum(x["original_native3m_closed"] for x in markets)==76800
    assert sum(x["original_native1d_closed"] for x in markets)==160
    assert sum(x["native15m_exact_decimal_parity"] for x in markets)==15360
    assert sum(x["closed_source1h"] for x in markets)==3840
    assert sum(tot[s] for s in STATES)==153
    assert tot["NO_C64_CONFIRMED_SOURCE_ANCHOR"]>=83
    doc={
      "schema":"EMBER_C65_ORIGINAL_BINANCE45ZIP_SOURCE_OF_LAST_LINK_HTF_TARGET_DUAL_INVALIDATION_V1",
      "market":"BINANCE_USDM_FUTURES_CRYPTO_RESEARCH_ONLY",
      "period_utc":["2026-09-01","2026-10-02"],
      "fresh_signed_original_zip_counts":{"native3m":15,"native15m":15,"native1d":15,"total":45},
      "original_native3m_closed":76800,
      "original_native1d_closed":160,
      "original_native15m_decimal_equalities":15360,
      "derived_closed_original1h":3840,
      "original_4h_C46_candidates":153,
      "source_lookahead_prevented":True,
      "source_48h_observation_window":True,
      "original_4h_full_source_status_totals":{s:tot[s] for s in STATES},
      "source_extra_counts":{k:v for k,v in sorted(tot.items()) if k not in STATES},
      "original_git_source_unchanged":SOURCE_BLOBS,
      "strict_text_source_rules":[
        "Order Flow requires STRUCTURE + liquidity AND IMB source interaction",
        "1H preknown strict UNSWEPT swing source is NOT academic StrongHL",
        "Previous fully closed native 1D high/low is technical HTF target source, not author-selected liquidity target",
        "Only post-target 1H CLOSE beyond last source structural link OR same timeframe OPPOSITE source POI can become an OF reversal proxy",
        "First ANY of two invalidation methods, same close is ambiguous, not first favorable",
        "A source wick across a local extreme alone is NEVER author OF invalidation"
      ],
      "author_last_1h_of_structural_link":0,
      "author_htf_target":0,
      "author_actual_OF_invalidation":0,
      "author_StrongHL":0,
      "author_order_status":0,
      "orders":0,"fills":0,"trades":0,"PnL":None,
      "readiness":"NOT_TRADE_READY",
      "markets":markets}
    if output:
        dst=Path(output);dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if PIN.exists():
        assert PIN.read_bytes()==(json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf-8"),"C65_FULL_SOURCE_PINNED_BYTES_CHANGED"
    print("C65_TOTALS",json.dumps(doc["original_4h_full_source_status_totals"],sort_keys=True),flush=True)
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
