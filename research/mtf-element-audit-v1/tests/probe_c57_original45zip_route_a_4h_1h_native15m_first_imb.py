#!/usr/bin/env python3
"""C57 full source research: 4H technical classic IMB → original3m first
contact → later C47 1H technical IMB → FIRST ANY native15m classic IMB.

Fresh 45 original Binance USD-M ZIP + CHECKSUM: 30 native15m/1d from
frozen C08 and 15 native3m from C21. Original native15m is not fabricated
from 3m. SHA lineage, 3072 Decimal 15m parity with original3m per symbol,
physical 15m/3m prefixes, all C47 source JSON equality. 6h fixed only for
bounded source observation, with explicit right censorship. No author VC.
"""
import sys,json,hashlib
from collections import Counter
from pathlib import Path
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
for p in ("d05","tools","tests"):sys.path.insert(0,str(ROOT/p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c47_post_4h_contact_1h_imb_source_link import scan_original_4h_first_contact_to_later_1h_source
from c57_route_a_original15m_first_imb_after_1h_source import (
    scan_c57_original_route_a,STATUS,FIFTEEN,SOURCE_SCOPE)
C47=ROOT/"evidence/c47/C47_ORIGINAL_4H_FIRST_CONTACT_TO_LATER_1H_IMB_45ZIP.json"
C46=ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
PIN=ROOT/"evidence/c57/C57_ORIGINAL_45ZIP_4H_FIRST_CONTACT_LATER_1H_THEN_FIRST_ANY_NATIVE15M_IMB.json"
CUT=OCT_START+DAY+FIFTEEN

def run(out=None):
    f47=json.loads(C47.read_text(encoding="utf-8"))
    f46=json.loads(C46.read_text(encoding="utf-8"))
    assert f47["schema"]=="EMBER_C47_SOURCE_C46_4H_FIRST_3M_TOUCH_TO_POST_CONTACT_SAME_SIDE_1H_IMB_V1"
    assert f47["original_binance_USDM_zip"]==45
    assert f47["original_C46_source_4h_candidate_count"]==153
    assert f47["original_C46_first3m_contact_count"]==132
    assert f46["source_candidate_4h_IMB_count"]==153
    assert f46["first_observed_source_3m_contact_count"]==132
    assert f47["same_side_later_closed_1h_source_candidate_parent_count"]==130
    assert f47["author_course_poi_vc_goldens"]==f47["orders"]==f47["trades"]==0
    prev={m["symbol"]:m for m in f47["markets"]}
    assert set(prev)==set(SYMS)
    markets=[];totals=Counter()
    for symbol in sorted(SYMS):
        old={tf:tuple(load_original(symbol,tf,d,start)[0]
                      for d,start in zip(DATES,STARTS))
             for tf in ("15m","1d")}
        htf=extended_32day_prefix(old["15m"],old["1d"],END)
        archives=tuple(native_3m(symbol,d)[0] for d in PERIODS)
        full=reconcile_native_3m(archives,htf,as_of_ms=END)
        assert full.native_15m_ohlcv_equalities==3072
        assert len(htf.native_15m_closed)==3072 and len(full.original_3m_closed)==15360
        c47=scan_original_4h_first_contact_to_later_1h_source(full,as_of_ms=END)
        assert json.loads(json.dumps(asdict(c47),sort_keys=True))==prev[symbol]["full_original_source_result"], "C57_FRESH_ORIGINAL45ZIP_C47_PARENT_JSON_DRIFT"
        review=scan_c57_original_route_a(c47,htf.native_15m_closed,as_of_ms=END)
        physical=reconcile_native_3m(archives,htf,as_of_ms=CUT)
        p47=scan_original_4h_first_contact_to_later_1h_source(physical,as_of_ms=CUT)
        v47=scan_original_4h_first_contact_to_later_1h_source(full,as_of_ms=CUT)
        assert p47==v47, "C57_NATIVE3M_PHYSICAL_PREFIX_LEAK"
        cut15=tuple(z for z in htf.native_15m_closed if z.known_at_ms<=CUT)
        assert len(cut15)==31*96+1
        rp=scan_c57_original_route_a(p47,cut15,as_of_ms=CUT)
        rv=scan_c57_original_route_a(v47,cut15,as_of_ms=CUT)
        assert rp==rv, "C57_NATIVE15M_POST_C47_CAUSAL_SUFFIX_LEAK"
        counts=Counter(x.source_status for x in review.observations)
        assert sum(counts.values())==c47.original_source4h_candidates
        assert counts[STATUS[0]]==c47.original_source4h_candidates-c47.original_source4h_first_contacts
        assert counts[STATUS[1]]==c47.unmatched_after_first_contact_count
        assert sum(counts[z] for z in STATUS[2:])==c47.matched_later_technical1h_imb_count
        assert c47.original_source4h_first_contacts==132 if len(SYMS)==1 else True
        assert review.author_POI_goldens==review.author_15m_VC_goldens==0
        assert not review.orders and not review.trades and review.readiness=="NOT_TRADE_READY"
        assert all(not q.paper_order_approved and not q.orders and not q.trades
                   and not q.course_author_15m_VC_verified and
                   not q.course_author_first_valid_test_verified and
                   not q.course_author_1h_trigger_verified and
                   q.readiness=="NOT_TRADE_READY"
                   for q in review.observations)
        for q in review.observations:
            if q.first_any_15m_imb is not None:
                g=q.first_any_15m_imb
                assert q.subsequent_1h_source_known_ms is not None
                assert g.first_start_ms>=q.subsequent_1h_source_known_ms
                assert g.fully_known_ms<=q.upper_observation_boundary_ms<=END
                assert len(g.original_native15m_ids)==3
            if q.source_status==STATUS[5]:
                assert q.fixed_six_hour_window_fully_observed is False
                assert q.first_any_15m_imb is None
        totals.update(counts)
        markets.append({
            "symbol":symbol,
            "original15m_native_source_rows":len(htf.native_15m_closed),
            "original3m_native_source_rows":len(full.original_3m_closed),
            "original3m_to_original15m_Decimal_OHLCV_parities":full.native_15m_ohlcv_equalities,
            "first_physical_suffix_cut_equals_source_asof":True,
            "source_4h_candidate_count":c47.original_source4h_candidates,
            "first_3m_source_contact_count":c47.original_source4h_first_contacts,
            "later_1h_source_imb_count":c47.matched_later_technical1h_imb_count,
            "status_counts":dict(sorted(counts.items())),
            "complete_original_source_observations":[asdict(x) for x in review.observations],
            "readiness":"NOT_TRADE_READY","author_trade_goldens":0,
            "orders":0,"trades":0})
        print("C57",symbol,dict(sorted(counts.items())),flush=True)
    assert sum(m["original15m_native_source_rows"] for m in markets)==15360
    assert sum(m["original3m_native_source_rows"] for m in markets)==76800
    assert sum(m["original3m_to_original15m_Decimal_OHLCV_parities"] for m in markets)==15360
    assert sum(m["source_4h_candidate_count"] for m in markets)==153
    assert sum(m["first_3m_source_contact_count"] for m in markets)==132
    assert sum(m["later_1h_source_imb_count"] for m in markets)==130
    assert totals[STATUS[0]]==21 and totals[STATUS[1]]==2
    assert sum(totals[x] for x in STATUS[2:])==130
    doc={
      "schema":"EMBER_C57_FRESH_BINANCE_USDM_ORIGINAL45ZIP_4H_SOURCE_FIRST3M_TOUCH_LATER1H_TO_FIRST_ANY_NATIVE15M_IMB_V1",
      "scope":"CRYPTO_ONLY_BINANCE_USDM_SOURCE_RESEARCH",
      "source_archives":{"original15m_and_native1d":30,"original3m":15,"total":45},
      "period_utc":["2026-09-01","2026-10-02"],
      "native_original3m_closed":76800,"native_original15m_closed":15360,
      "independent_original3m_native15m_OHLCV_equalities":15360,
      "fixed_observation_15m_imb_window_hours":6,
      "first_any_not_first_favorable":True,
      "explicit_source_end_right_censorship":True,
      "previous_C46_source_git_blob":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
      "previous_C47_source_git_blob":"b2727f081d8a73f522a97a54b4582507ee969244",
      "course_route_mode_source_only":SOURCE_SCOPE,
      "4h_source_IMB_candidates":153,
      "source_first3m_contacts":132,
      "post_contact_technical1h_candidates":130,
      "statuses":dict(sorted(totals.items())),
      "academic_author_4h_poi_goldens":0,
      "academic_author_1h_trigger_goldens":0,
      "academic_author_15m_vc_goldens":0,
      "author_POI_first_test_goldens":0,
      "executed_paper_signals":0,"orders":0,"trades":0,"fills":0,"PnL":None,
      "readiness":"NOT_TRADE_READY",
      "limitations":"First source-native15m technical wick-gap is NOT course VC, does not prove actual volume confirmation or first valid POI test; bounded 6h is not an author entry rule, and no timing, execution, stop or expected profit can be inferred.",
      "markets":markets}
    if out:
        dst=Path(out);dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if PIN.exists():
        assert PIN.read_bytes()==(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode("utf-8"),"C57_PINNED_SOURCE_BYTE_DRIFT"
    print("C57_FULL_ORIGINAL45ZIP_REPLAY",json.dumps(doc["statuses"],sort_keys=True),flush=True)
    return doc

if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
