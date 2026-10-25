#!/usr/bin/env python3
"""C64 original SHA checked 45 ZIP: immutable C46/C62/C63 chronology -> native3m
source contact anchor, first preconfirmation breach, post-confirmation wick,
post-confirmation 3m close, and separately later 1h close.

No author Strong High/Low or OF invalidation. Original wick/source extreme
is a technical proxy. Source status cannot open any position.
"""
import sys,json,hashlib
from pathlib import Path
from dataclasses import asdict
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
for x in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/x))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY,TF_MS
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
from c62_academic_snr_rb_imb_liquidity_source_separation import observe_hourly_source_poi_split
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    convert_c62_closed_source_events,source_first_any_after_contact)
from c64_original3m_source_protected_extreme_invalidation import (
    inspect_original_source_protected_extreme,STATUS)
F46=ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
F60=ROOT/"evidence/c60/C60_ORIGINAL45ZIP_4H_IMB_FIRST_AND_RETURN_SOURCE_NATIVE3M_EPISODES.json"
F62=ROOT/"evidence/c62/C62_ORIGINAL_45ZIP_1H_SNR_RB_MB_IMB_LIQUIDITY_COMPLETE_SOURCE.json"
F63=ROOT/"evidence/c63/C63_ORIGINAL45ZIP_FIRST_ANY_CLOSED1H_SOURCE_AFTER_4H_FIRST_NATIVE3M_CONTACT.json"
PIN=ROOT/"evidence/c64/C64_ORIGINAL45ZIP_STRICT_SOURCE_EXTREME_PRECONFIRM_POST_WICK_CLOSE_INVALIDATION.json"
def _canon(x):return json.loads(json.dumps(x,sort_keys=True))
def run(output=None):
    d46=json.loads(F46.read_bytes());d60=json.loads(F60.read_bytes())
    d62=json.loads(F62.read_bytes());d63=json.loads(F63.read_bytes())
    assert d46["source_candidate_4h_IMB_count"]==d60["technical_4h_imb_candidate_total"]==d63["4h_source_parent_candidates"]==153
    assert d62["source_derived_closed_1h_bars"]==3840
    old46={x["symbol"]:x for x in d46["markets"]}
    old60={x["symbol"]:x for x in d60["markets"]}
    old62={x["symbol"]:x for x in d62["markets"]}
    old63={x["symbol"]:x for x in d63["markets"]}
    assert set(old46)==set(old60)==set(old62)==set(old63)==set(SYMS)
    markets=[];tot=Counter()
    for symbol in sorted(SYMS):
        original={tf:tuple(load_original(symbol,tf,p,t)[0]
                  for p,t in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(original["15m"],original["1d"],END)
        archives=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        source=reconcile_native_3m(archives,htf,as_of_ms=END)
        assert len(source.original_3m_closed)==15360
        assert source.native_15m_ohlcv_equalities==3072
        parents=inspect_original_4h_imb_source(source,as_of_ms=END)
        assert _canon(asdict(parents))==old46[symbol]["source_only_4h_classic_imb_first_contact"]
        c62=observe_hourly_source_poi_split(htf.derived_1h_closed,as_of_ms=END)
        assert _canon([asdict(x) for x in c62["technical_1h_snr_rb_separate_cases"]])==old62[symbol]["source_cases"]
        assert _canon([asdict(x) for x in c62["technical_original_1h_imb_gaps"]])==old62[symbol]["source_gaps"]
        events=convert_c62_closed_source_events(c62,htf.derived_1h_closed,as_of_ms=END)
        sixty=old60[symbol]["complete_original_source_visit_lifecycle"]
        last=old63[symbol]["source_parent_rows"]
        assert len(sixty)==len(last)==len(parents.observations)
        counts=Counter();out=[]
        for i,(parent,v,row) in enumerate(zip(parents.observations,sixty,last)):
            assert v["zone_known_ms"]==parent.candidate.fully_known_ms
            assert v["technical_4h_zone_side"]==parent.candidate.side
            assert v["first_contact_original3m_id"]==parent.first_contact_original3m_id
            chain=source_first_any_after_contact(
                symbol=symbol,side=parent.candidate.side,
                zone_known_ms=parent.candidate.fully_known_ms,
                first_original3m_id=parent.first_contact_original3m_id,
                first_contact_known_ms=parent.first_contact_closed_known_ms,
                events=events,as_of_ms=END)
            assert _canon(asdict(chain))=={k:v for k,v in row.items() if k not in (
                "original_4h_parent_index","parent_original_three_3m_source_IDs")},"C64_C63_FROZEN_FIRST_ANY_CHAIN_DRIFT"
            assert row["original_4h_parent_index"]==i
            if parent.first_contact_closed_known_ms is None:
                physical=source.original_3m_closed
            else:
                idx=(parent.first_contact_closed_known_ms-THREE-
                    source.original_3m_closed[0].start_ms)//THREE
                assert idx>=0
                physical=source.original_3m_closed[idx:]
                assert physical[0].raw_id==parent.first_contact_original3m_id
            q=inspect_original_source_protected_extreme(
                chain,physical,htf.derived_1h_closed,as_of_ms=END)
            assert q.source_status in STATUS
            assert q.symbol==symbol and q.original_4h_parent_side==parent.candidate.side
            assert not (q.author_labeled_stronghl or q.author_labeled_OF_invalidation
                        or q.author_labeled_stop_loss or q.author_selected_poi or
                        q.orders or q.fills or q.trades)
            counts[q.source_status]+=1
            if q.source_extreme_frozen_at_ms is not None:
                counts["source_candidate_extreme_with_price"]+=1
                assert q.source_extreme_frozen_at_ms==chain.first_any_source_event_known_ms
                assert q.original_native3m_extreme_witness_id is not None
            if q.source_preactivation_breach_first3m_id is not None:
                counts["preactivation_wick_breach"]+=1
                assert q.source_status=="SOURCE_ANCHOR_BREACHED_BEFORE_EVENT_CONFIRMATION"
            if q.first_postevent_wick_breach_id is not None:
                counts["postevent_3m_wick_breach"]+=1
            if q.first_postevent_3m_close_beyond_id is not None:
                counts["postevent_3m_close_beyond"]+=1
                assert q.first_postevent_wick_breach_id is not None
            if q.first_postevent_1h_close_beyond_id is not None:
                counts["postevent_1h_close_beyond"]+=1
                assert q.first_postevent_wick_breach_id is not None
            if q.full_24h_postevent_source_observed:
                counts["full_postevent_24h_window"]+=1
            out.append({"original_4h_parent_index":i,
                        "first_any_source_event_status":chain.status,
                        **asdict(q)})
        assert sum(counts[x] for x in STATUS)==len(parents.observations)
        assert counts["NO_ORIGINAL_4H_FIRST_CONTACT"]==old46[symbol]["source_only_4h_classic_imb_first_contact"]["untouched_candidate_count"]
        total=tot.update(counts)
        markets.append({
           "symbol":symbol,"original_native3m_closed":15360,
           "original_native1d_closed":32,"native15m_decimal_parity":3072,
           "source_derived1h_closed":768,"original_4h_parent_count":len(out),
           "source_status_totals":{k:counts[k] for k in STATUS},
           "source_breach_totals":{k:v for k,v in sorted(counts.items()) if k not in STATUS},
           "original_4h_c46_and_1h_c62_and_firstany_c63_source_frozen_match":True,
           "parent_source_protected_extreme_cases":out,
           "author_goldens":0,"orders":0,"fills":0,"trades":0,
           "readiness":"NOT_TRADE_READY"})
        print("C64",symbol,dict(sorted(counts.items())),flush=True)
    assert sum(x["original_native3m_closed"] for x in markets)==76800
    assert sum(x["original_native1d_closed"] for x in markets)==160
    assert sum(x["native15m_decimal_parity"] for x in markets)==15360
    assert sum(x["source_derived1h_closed"] for x in markets)==3840
    assert sum(x["original_4h_parent_count"] for x in markets)==153
    assert sum(tot[k] for k in STATUS)==153
    assert tot["NO_ORIGINAL_4H_FIRST_CONTACT"]==21
    d={
       "schema":"EMBER_C64_ORIGINAL45ZIP_3M_CONTACT_TECHNICAL_ANCHOR_PRECONFIRM_AND_WICK_VS_BODY_1H_INVALIDATION_V1",
       "scope":"CRYPTO_ONLY_BINANCE_USDM_ORIGINAL_SOURCE_NO_AUTHOR_GOLDENS_NO_ORDERS",
       "period_utc":["2026-09-01","2026-10-02"],
       "source_signed_original_zip_counts":{"native3m":15,"native15m":15,"native1d":15,"total":45},
       "original_native3m_closed":76800,"original_native1d_closed":160,
       "original_native15m_decimal_parities":15360,
       "source_derived_closed1h":3840,
       "original_4h_technical_source_parents":153,
       "source_status_totals":{k:tot[k] for k in STATUS},
       "source_breach_totals":{k:v for k,v in sorted(tot.items()) if k not in STATUS},
       "fixed_original_postevent_observation_hours":24,
       "anchor_rule":"source-only min(original 3m low) or max(original 3m high) from original first 3m contact bar up to first event's pattern start (exclusive), frozen only on full event close; not author Strong High/Low, not SL",
       "preactivation_rule":"if pattern being formed sweeps the candidate extreme before full event closes, candidate rejected for source protection and not tracked as viable after confirmation",
       "postevent_rule":"independently record first native3m wick-through, first native3m fully closed close-through and first derived fully closed1h close-through in fixed 24h window; wick alone NEVER implies owner Order Flow invalidation",
       "missing_author_goldens":True,
       "author_selected_poi":0,"author_verified_stronghl":0,
       "author_of_invalidation":0,"author_sl":0,"orders":0,
       "fills":0,"trades":0,"PnL":None,"readiness":"NOT_TRADE_READY",
       "original_immutable_sources":{
          "C46":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
          "C60":"899373e4a1dc1999d1485ac8c1f790d39071aebd",
          "C62":"8428bf7d6cd3bc26f617cfc32a34c91a27c813b2",
          "C63":"fdc77c7ec942f03b4efae83b935d994c8435a24f"},
       "markets":markets}
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(d,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if PIN.exists():
        assert PIN.read_bytes()==(json.dumps(d,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf-8"),"C64_IMMUTABLE_SOURCE_DRIFT"
    print("C64_SOURCE_TOTALS",json.dumps(d["source_status_totals"],sort_keys=True),
          json.dumps(d["source_breach_totals"],sort_keys=True),flush=True)
    return d
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
