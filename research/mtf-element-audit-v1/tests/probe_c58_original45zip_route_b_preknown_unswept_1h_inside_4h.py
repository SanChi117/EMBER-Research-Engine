#!/usr/bin/env python3
"""C58 source ONLY: 1H BSL SSL fractal preknown unswept INSIDE an
original Binance 4H technical gap at its first original native3m touch.

Original 45 checked USD-M ZIP, physical prefix == full as-of; 4H source
exact matches immutable C46. Course IDM or Strong HL author goldens ZERO.
"""
import sys,json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for f in ("d05","tools","tests"):sys.path.insert(0,str(ROOT/f))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c46_original_4h_classic_imb_first_contact import inspect_original_4h_imb_source
from c58_route_b_preknown_original1h_liquidity_inside_4h_source import scan_c58_source_only,STATUS
FROZEN=ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
PIN=ROOT/"evidence/c58/C58_ORIGINAL_45ZIP_PREKNOWN_UNSWEPT_1H_FRACTAL_INSIDE_4H_FIRST_CONTACT.json"
CUT=OCT_START+DAY+3*THREE
def run(output=None):
    baseline=json.loads(FROZEN.read_text(encoding="utf-8"))
    assert baseline["schema"]=="EMBER_C46_ORIGINAL_USDM_4H_SOURCE_CLASSIC_IMB_FIRST_3M_CONTACT_V1"
    assert baseline["original_binance_USDM_zip"]==45
    assert baseline["original_native3m_closed"]==76800
    assert baseline["source_candidate_4h_IMB_count"]==153
    assert baseline["first_observed_source_3m_contact_count"]==132
    locked={m["symbol"]:m for m in baseline["markets"]}
    assert set(locked)==set(SYMS)
    markets=[];totals=Counter();level_counts=Counter()
    for symbol in sorted(SYMS):
        files={tf:tuple(load_original(symbol,tf,p,t)[0] for p,t in zip(DATES,STARTS))
                for tf in ("15m","1d")}
        htfs=extended_32day_prefix(files["15m"],files["1d"],END)
        orig=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        full=reconcile_native_3m(orig,htfs,as_of_ms=END)
        assert full.native_15m_ohlcv_equalities==3072
        c46=inspect_original_4h_imb_source(full,as_of_ms=END)
        assert json.loads(json.dumps(asdict(c46),sort_keys=True))==locked[symbol]["source_only_4h_classic_imb_first_contact"],"C58_ORIGINAL_C46_SOURCE_DRIFT"
        review=scan_c58_source_only(full,as_of_ms=END)
        physical=reconcile_native_3m(orig,htfs,as_of_ms=CUT)
        c58_short=scan_c58_source_only(physical,as_of_ms=CUT)
        c58_full_prefix=scan_c58_source_only(full,as_of_ms=CUT)
        assert c58_short==c58_full_prefix,"C58_ORIGINAL_3M_PHYSICAL_PREFIX_CHANGED_SOURCE_EVENTS"
        counts=Counter(x.source_state for x in review.reviewed_parents)
        n=sum(counts.values())
        assert n==c46.candidate_count
        assert counts[STATUS[0]]==c46.untouched_candidate_count
        assert sum(counts[x] for x in STATUS[1:])==c46.first_original3m_contact_count
        for e in review.reviewed_parents:
            assert e.readiness=="NOT_TRADE_READY"
            assert not (e.academic_idm_approved or e.author_typed_poi_verified
                         or e.author_stronghl_verified or e.orders or e.trades)
            if e.first_contact_original3m_id is None:
                assert not e.preknown_inside_1h_liquidity
            for v in e.preknown_inside_1h_liquidity:
                assert e.four_hour_gap_fully_known_ms<=v.pivot_fully_known_ms<=e.first_contact_bar_start_ms
                assert not v.author_idm_certified and not v.strong_high_low_author_certified
                assert not v.orders and not v.trades
                assert v.first_original3m_strict_breach_id is None if v.unswept_until_contact_bar_start else v.first_original3m_strict_breach_id is not None
                level_counts["unbroken" if v.unswept_until_contact_bar_start else "already_strict_breached"]+=1
                level_counts[v.kind]+=1
        assert review.author_idm_goldens==review.paper_signals==0 and review.orders==review.trades==()
        totals.update(counts)
        markets.append({
            "symbol":symbol,
            "original_native3m_closed":review.source_original3m_closed,
            "native15m_decimal_equalities":full.native_15m_ohlcv_equalities,
            "original_1h_closed":review.source_original1h_closed,
            "source_4h_gap_candidates":review.original_4h_source_candidate_count,
            "source_statuses":dict(sorted(counts.items())),
            "source_original_3m_physically_truncated_prefix_matches_asof":True,
            "source_observations":[asdict(z) for z in review.reviewed_parents],
            "course_author_idm":0,"orders":0,"trades":0,"readiness":"NOT_TRADE_READY"})
        print("C58",symbol,dict(sorted(counts.items())),flush=True)
    assert sum(x["original_native3m_closed"] for x in markets)==76800
    assert sum(x["native15m_decimal_equalities"] for x in markets)==15360
    assert sum(x["original_1h_closed"] for x in markets)==3840
    assert sum(x["source_4h_gap_candidates"] for x in markets)==153
    assert totals[STATUS[0]]==21
    assert sum(totals.values())==153
    assert sum(level_counts[x] for x in ("unbroken","already_strict_breached"))==sum(
       len(q["preknown_inside_1h_liquidity"]) for market in markets for q in market["source_observations"])
    doc={
      "schema":"EMBER_C58_ORIGINAL45ZIP_CRYPTO_1H_PREKNOWN_INSIDE_4H_TECHNICAL_IMB_FIRST_3M_CONTACT_SOURCE_V1",
      "crypto_only":True,
      "source_period_utc":["2026-09-01","2026-10-02"],
      "original_BINANCE_USDM_ZIP":{"15m":15,"1d":15,"3m":15,"total":45},
      "original_native3m_closed":76800,
      "original_native15m_decimal_equalities":15360,
      "original_1h_closed":3840,
      "source_4h_technical_IMB":153,
      "first_original3m_contact":132,
      "all_1h_levels_interior_not_ahead_assumption":True,
      "historically_strict_wick_breached_not_eligible_unswept":True,
      "no_pivot_ranking_or_first_favorable_selection":True,
      "source_statuses":dict(sorted(totals.items())),
      "candidate_links":dict(sorted(level_counts.items())),
      "previous_frozen_C46_source_git_blob":"dc03c181912ffbb800bc191fbc16ec0d05c335e0",
      "author_verified_typed_4h_Poi":0,
      "author_verified_strong_high_low":0,
      "author_verified_idm":0,
      "paper_signals":0,"orders":0,"trades":0,"fills":0,"PnL":None,
      "readiness":"NOT_TRADE_READY",
      "limitations":"Numerical original preknown 1H BSL/SSL fractal INSIDE a 4H TECHNICAL wick gap is NOT an author's IDM. The course 'ahead' semantics, POI tested state, Strong HL, structural order and RR are not derived; no trades or performance.",
      "markets":markets}
    if output:
        o=Path(output);o.parent.mkdir(exist_ok=True,parents=True)
        o.write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    if PIN.exists():
        assert PIN.read_bytes()==(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8"),"C58_ORIGINAL_SOURCE_PIN_DRIFT"
    print("C58_ALL_ORIGINAL45ZIP",json.dumps(doc["source_statuses"],sort_keys=True),flush=True)
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
