#!/usr/bin/env python3
"""C60 original USD-M 45 independently signed ZIP: native3m 4H IMB source
FIRST touch vs separated later SOURCE visits, not author valid POI tests.

C08 30 native15m/1d + C21 15 original native3m ZIP, five cryptocurrencies.
Recompute frozen C46 full first touch ID; as-of prefix equals physically cut
native3m stream; no hindsight, orders, trades, author StrongHL.
"""
import sys,json,hashlib
from collections import Counter
from pathlib import Path
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
for n in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/n))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
from c60_original_4h_imb_3m_contact_episode_lifecycle import scan_c60_original_source
PIN_C46=ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
FROZEN_C60=ROOT/"evidence/c60/C60_ORIGINAL45ZIP_4H_IMB_FIRST_AND_RETURN_SOURCE_NATIVE3M_EPISODES.json"
CUT=OCT_START+DAY+3*THREE

def run(out=None):
    c46=json.loads(PIN_C46.read_bytes())
    assert c46["schema"]=="EMBER_C46_ORIGINAL_USDM_4H_SOURCE_CLASSIC_IMB_FIRST_3M_CONTACT_V1"
    assert c46["source_candidate_4h_IMB_count"]==153
    assert c46["first_observed_source_3m_contact_count"]==132
    locked={x["symbol"]:x for x in c46["markets"]}
    assert set(locked)==set(SYMS)
    allm=[];tot=Counter()
    for symbol in sorted(SYMS):
        originals={tf:tuple(load_original(symbol,tf,p,t)[0] for p,t in zip(DATES,STARTS))
            for tf in ("15m","1d")}
        htf=extended_32day_prefix(originals["15m"],originals["1d"],END)
        archives=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        source=reconcile_native_3m(archives,htf,as_of_ms=END)
        assert len(source.original_3m_closed)==15360
        assert source.native_15m_ohlcv_equalities==3072
        expected=locked[symbol]["source_only_4h_classic_imb_first_contact"]
        parent=inspect_original_4h_imb_source(source,as_of_ms=END)
        assert json.loads(json.dumps(asdict(parent),sort_keys=True))==expected,"C60_FROZEN_C46_FULL_SOURCE_DRIFT"
        full=scan_c60_original_source(source,as_of_ms=END)
        physical=reconcile_native_3m(archives,htf,as_of_ms=CUT)
        cut_scan=scan_c60_original_source(physical,as_of_ms=CUT)
        full_asof=scan_c60_original_source(source,as_of_ms=CUT)
        assert cut_scan==full_asof,"C60_POST_CUT_ORIGINAL3M_FUTURE_LEAK"
        assert full.technical_4h_candidate_count==expected["candidate_count"]
        assert full.candidates_with_first_source_contact==expected["first_original3m_contact_count"]
        assert full.author_valid_poi_tests==full.author_stronghl_goldens==0
        assert full.orders==full.trades==() and full.readiness=="NOT_TRADE_READY"
        assert full.total_separate_source_visits>=full.candidates_with_first_source_contact
        assert full.candidates_with_repeated_source_returns<=full.candidates_with_first_source_contact
        count=Counter()
        for v in full.candidate_visits:
            assert not (v.course_author_valid_first_test or v.course_author_StrongHL or
                        v.academic_trade_signal or v.orders or v.trades)
            visits=v.all_closed_3m_visit_episodes
            if not visits:
                count["no_original_source_contact"]+=1
            elif len(visits)==1:
                count["single_observed_visit"]+=1
            else:
                count["two_or_more_distinct_source_visits"]+=1
            if v.last_episode_still_open_at_source_end:
                count["source_right_censored_active_last_visit"]+=1
            for i,t in enumerate(visits):
                assert not (t.author_valid_poi_test_verified or t.orders or t.trades)
                assert t.first_bar_start_ms>=v.zone_known_ms
                assert t.first_bar_known_ms==t.first_bar_start_ms+THREE
                assert t.first_original3m_raw_id.rsplit(":",1)[1]==str(t.first_bar_start_ms)
                assert t.last_bar_known_ms<=END
                assert t.kind==("FIRST_SOURCE_WICK_VISIT" if i==0 else "REPEATED_SOURCE_WICK_RETURN")
                assert t.separated_from_prior_by_fully_closed_outside_3m==bool(i)
            if visits:
                assert v.first_contact_original3m_id==visits[0].first_original3m_raw_id
        assert sum(count[k] for k in (
            "no_original_source_contact","single_observed_visit",
            "two_or_more_distinct_source_visits"))==full.technical_4h_candidate_count
        tot.update(count)
        allm.append({
            "symbol":symbol,
            "original3m_closed":len(source.original_3m_closed),
            "exact_native15m_Decimal_parities":source.native_15m_ohlcv_equalities,
            "original_4h_classic_imb_source_candidates":full.technical_4h_candidate_count,
            "original_3m_first_touch_sources":full.candidates_with_first_source_contact,
            "all_distinct_source_visit_episodes":full.total_separate_source_visits,
            "source_candidates_with_repeated_return":full.candidates_with_repeated_source_returns,
            "source_right_censored_last_visits":full.right_censored_final_episodes,
            "source_status_counts":dict(sorted(count.items())),
            "physical_original3m_prefix_equals_asof":True,
            "complete_original_source_visit_lifecycle":[asdict(q) for q in full.candidate_visits],
            "author_valid_first_test_goldens":0,"orders":0,"trades":0,
            "readiness":"NOT_TRADE_READY"})
        print("C60",symbol,full.total_separate_source_visits,dict(sorted(count.items())),flush=True)
    assert sum(x["original3m_closed"] for x in allm)==76800
    assert sum(x["exact_native15m_Decimal_parities"] for x in allm)==15360
    assert sum(x["original_4h_classic_imb_source_candidates"] for x in allm)==153
    assert sum(x["original_3m_first_touch_sources"] for x in allm)==132
    assert tot["no_original_source_contact"]==21
    doc={
       "schema":"EMBER_C60_ORIGINAL_BINANCE_USDM_45ZIP_4H_CLASSIC_IMB_FIRST_AND_REPEATED_NATIVE3M_SOURCE_VISITS_V1",
       "scope":"CRYPTO_ONLY_SOURCE_RESEARCH",
       "source_zip_counts":{"original_native15m":15,"original_native1d":15,"original_native3m":15,"total":45},
       "source_period_utc":["2026-09-01","2026-10-02"],
       "original_closed_native3m":76800,
       "crosschecked_native15m_exact_Decimal_parities":15360,
       "technical_4h_imb_candidate_total":153,
       "original_first_native3m_contact_total":132,
       "distinct_source_visit_episodes_total":sum(x["all_distinct_source_visit_episodes"] for x in allm),
       "candidate_status_totals":dict(sorted(tot.items())),
       "right_censor_explicit":True,
       "one_contiguous_3m_wick_overlap_episode_per_visit":True,
       "full_closed_3m_noncontact_departure_needed_for_new_return":True,
       "original_C46_source_git_blob":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
       "author_4h_typed_POI_valid":0,
       "author_first_valid_POI_tests":0,"author_StrongHL_goldens":0,
       "author_volume_confirmation":0,"author_entry_signals":0,
       "orders":0,"fills":0,"trades":0,"PnL":None,"readiness":"NOT_TRADE_READY",
       "limitations":"Episodes of original native3m WICK overlaps are technical source geometry, not academic POI first VALID test. Intrabar multi-pass is unknowable from OHLC. Consecutive overlap bars are one encounter; later contacts require closed noncontact evidence. No author goldens, no SL/TP, entry, fills or PnL.",
       "markets":allm}
    if out:
        p=Path(out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if FROZEN_C60.exists():
        assert FROZEN_C60.read_bytes()==(
          json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
        ).encode("utf-8"),"C60_ORIGINAL45ZIP_SOURCE_FILE_DRIFT"
    print("C60_TOTALS",json.dumps(doc["candidate_status_totals"],sort_keys=True),flush=True)
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
