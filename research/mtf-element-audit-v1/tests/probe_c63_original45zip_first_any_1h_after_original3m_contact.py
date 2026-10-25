#!/usr/bin/env python3
"""C63 fresh 45 signed Binance USD-M ZIP source first-ANY post-first-contact.

No favorable first selection: observed FIRST ANY 1H source technical event
from C62 SNR/RB/classic IMB or previously known 3bar fractal CLOSE break,
regardless of side; ALL events and timestamps preserved in C63 evidence.
Parent original C46 source and frozen C62 full source are independently
replayed, with original native3m/native15m/native1d parity.
Never mark StrongHL, author valid first test, final route A VC, entry,
real or paper orders, FTA/SL/TP/PnL.
"""
import sys,json,hashlib
from pathlib import Path
from dataclasses import asdict
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
for f in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/f))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY,TF_MS
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
from c62_academic_snr_rb_imb_liquidity_source_separation import observe_hourly_source_poi_split
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    source_first_any_after_contact,convert_c62_closed_source_events,STATUS)
C46=ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
C60=ROOT/"evidence/c60/C60_ORIGINAL45ZIP_4H_IMB_FIRST_AND_RETURN_SOURCE_NATIVE3M_EPISODES.json"
C62=ROOT/"evidence/c62/C62_ORIGINAL_45ZIP_1H_SNR_RB_MB_IMB_LIQUIDITY_COMPLETE_SOURCE.json"
PIN=ROOT/"evidence/c63/C63_ORIGINAL45ZIP_FIRST_ANY_CLOSED1H_SOURCE_AFTER_4H_FIRST_NATIVE3M_CONTACT.json"
WINDOW=24*TF_MS["1h"]
def run(output=None):
    old46=json.loads(C46.read_bytes());old60=json.loads(C60.read_bytes());old62=json.loads(C62.read_bytes())
    assert old46["source_candidate_4h_IMB_count"]==old60["technical_4h_imb_candidate_total"]==153
    assert old62["source_derived_closed_1h_bars"]==3840
    p46={x["symbol"]:x for x in old46["markets"]}
    p60={x["symbol"]:x for x in old60["markets"]}
    p62={x["symbol"]:x for x in old62["markets"]}
    assert set(p46)==set(p60)==set(p62)==set(SYMS)
    markets=[];tot=Counter()
    for symbol in sorted(SYMS):
        original={tf:tuple(load_original(symbol,tf,period,begin)[0]
              for period,begin in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(original["15m"],original["1d"],END)
        archives=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        native=reconcile_native_3m(archives,htf,as_of_ms=END)
        assert len(native.original_3m_closed)==15360
        assert native.native_15m_ohlcv_equalities==3072
        source46=inspect_original_4h_imb_source(native,as_of_ms=END)
        assert json.loads(json.dumps(asdict(source46),sort_keys=True))==p46[symbol]["source_only_4h_classic_imb_first_contact"]
        source62=observe_hourly_source_poi_split(htf.derived_1h_closed,as_of_ms=END)
        assert json.loads(json.dumps([asdict(x) for x in source62["technical_1h_snr_rb_separate_cases"]],sort_keys=True))==p62[symbol]["source_cases"],"C63_FROZEN_C62_BLOCK_SOURCE_DRIFT"
        assert json.loads(json.dumps([asdict(x) for x in source62["technical_original_1h_imb_gaps"]],sort_keys=True))==p62[symbol]["source_gaps"],"C63_FROZEN_C62_CLASSIC_GAP_SOURCE_DRIFT"
        full_events=convert_c62_closed_source_events(source62,htf.derived_1h_closed,as_of_ms=END)
        parent60=p60[symbol]["complete_original_source_visit_lifecycle"]
        assert len(parent60)==len(source46.observations)
        counts=Counter();children=[]
        for i,(z,v) in enumerate(zip(source46.observations,parent60)):
            assert z.candidate.fully_known_ms==v["zone_known_ms"]
            assert z.candidate.side==v["technical_4h_zone_side"]
            assert z.first_contact_original3m_id==v["first_contact_original3m_id"]
            result=source_first_any_after_contact(
               symbol=symbol,side=z.candidate.side,
               zone_known_ms=z.candidate.fully_known_ms,
               first_original3m_id=z.first_contact_original3m_id,
               first_contact_known_ms=z.first_contact_closed_known_ms,
               events=full_events,as_of_ms=END)
            assert result.status in STATUS
            assert not (result.has_author_selected_poi or
                result.has_author_first_valid_poi_test or
                result.has_author_vc_or_bos or result.has_author_stronghl or
                result.author_trade_approved or result.orders or result.trades)
            if result.first_any_source_event_known_ms is not None:
                assert all(k.fully_known_ms==result.first_any_source_event_known_ms
                    for k in result.first_any_source_events)
                assert all(k.first_pattern_bar_start_ms>=z.first_contact_closed_known_ms
                    for k in result.first_any_source_events)
                assert result.first_any_source_event_known_ms<=END
                for e in result.first_any_source_events:counts["FIRST_ANY_KIND_"+e.kind]+=1
            if result.status=="NO_4H_SOURCE_FIRST_CONTACT":
                assert z.first_contact_original3m_id is None
            counts[result.status]+=1
            children.append({"original_4h_parent_index":i,
                "parent_original_three_3m_source_IDs":list(z.candidate.three_original_source_first_native3m_ids),
                **asdict(result)})
        assert sum(counts[z] for z in STATUS)==len(children)
        assert counts[STATUS[0]]==p46[symbol]["source_only_4h_classic_imb_first_contact"]["untouched_candidate_count"]
        tot.update(counts)
        # PHYSICAL one-hour native prefix at cutoff is identically sourced.
        CUT=OCT_START+DAY+TF_MS["1h"]
        k=(CUT-htf.derived_1h_closed[0].start_ms)//TF_MS["1h"]
        c1=observe_hourly_source_poi_split(htf.derived_1h_closed,as_of_ms=CUT)
        c2=observe_hourly_source_poi_split(htf.derived_1h_closed[:k],as_of_ms=CUT)
        assert c1==c2,"C63_1H_C62_SOURCE_PREFIX_FUTURE_LEAK"
        e1=convert_c62_closed_source_events(c1,htf.derived_1h_closed,as_of_ms=CUT)
        e2=convert_c62_closed_source_events(c2,htf.derived_1h_closed[:k],as_of_ms=CUT)
        assert e1==e2,"C63_1H_FIRST_ANY_EVENT_PREFIX_FUTURE_LEAK"
        markets.append({
          "symbol":symbol,"original_native3m_closed":15360,
          "original_native1d_closed":32,"original_native15m_decimal_parity":3072,
          "fully_closed_source_1h":len(htf.derived_1h_closed),
          "original_4h_parent_count":len(children),
          "source_1h_events_all_kinds":len(full_events),
          "first_any_status_counts":{s:counts[s] for s in STATUS},
          "first_any_event_kind_counts":{k:v for k,v in sorted(counts.items()) if k.startswith("FIRST_ANY_KIND_")},
          "original_1h_source_asof_prefix_equal_physical":True,
          "source_parent_rows":children,
          "author_goldens":0,"orders":0,"trades":0,
          "readiness":"NOT_TRADE_READY"})
        print("C63",symbol,"eventTotal",len(full_events),{s:counts[s] for s in STATUS},flush=True)
    assert sum(z["original_4h_parent_count"] for z in markets)==153
    assert sum(z["original_native3m_closed"] for z in markets)==76800
    assert sum(z["original_native1d_closed"] for z in markets)==160
    assert sum(z["original_native15m_decimal_parity"] for z in markets)==15360
    assert sum(z["fully_closed_source_1h"] for z in markets)==3840
    assert tot["NO_4H_SOURCE_FIRST_CONTACT"]==21
    assert sum(tot[s] for s in STATUS)==153
    doc={
       "schema":"EMBER_C63_ORIGINAL45ZIP_FIRST_ANY_CLOSED1H_TECHNICAL_AFTER_4H_FIRST_NATIVE3M_WICK_V1",
       "scope":"CRYPTO_ONLY_RESEARCH_SOURCE_NO_ORDERS",
       "period_utc":["2026-09-01","2026-10-02"],
       "source_signed_original_crypto_zip":{"original_native3m":15,
         "original_native15m":15,"original_native1d":15,"total":45},
       "original_native3m_closed":76800,"original_native1d_closed":160,
       "native15m_exact_original_decimal_parity":15360,
       "fully_closed_original_1h":3840,"4h_source_parent_candidates":153,
       "original_first3m_source_contact_parents":132,
       "max_fixed_1h_event_wait_hours":24,
       "rule":"FIRST ANY later wholly post-first-contact confirmed source 1H event, same or opposite or ambiguous. Not first favorable. Right censor when window unavailable.",
       "all_parent_status_counts":{s:tot[s] for s in STATUS},
       "first_any_kind_counts":{k:v for k,v in sorted(tot.items()) if k.startswith("FIRST_ANY_KIND_")},
       "previous_source_git_blobs":{
         "C46":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
         "C60":"899373e4a1dc1999d1485ac8c1f790d39071aebd",
         "C62":"8428bf7d6cd3bc26f617cfc32a34c91a27c813b2"},
       "author_selected_POI":0,"author_first_valid_poi_test":0,
       "author_real_volume_confirmation":0,"author_true_BOS":0,
       "author_strongHL":0,"author_SL_TP":0,"orders":0,"fills":0,
       "trades":0,"PnL":None,"readiness":"NOT_TRADE_READY",
       "limitations":"Source C62 1H SNR/RB/IMB geometries and 1H strict preknown fractal CLOSE breach are technical adapted observations only. Not academic author StrongHL or real 1H volume confirmation/BOS, FTA/SL/TP. No positive author price chart goldens. First ANY source observation must not become trade win rate.",
       "markets":markets}
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if PIN.exists():
        assert PIN.read_bytes()==(
           json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
        ).encode("utf-8"),"C63_IMMUTABLE_FULL_SOURCE_REPLAY_DRIFT"
    print("C63_COUNTS",json.dumps(doc["all_parent_status_counts"],sort_keys=True),flush=True)
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
