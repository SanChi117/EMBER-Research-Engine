#!/usr/bin/env python3
"""C55 original crypto native 3m from 45 checksum-checked Binance USD-M ZIP.

Original 30 15m/1d source + original 15 native3m source archives.
Independent physical prefix at 2026-10-02 00:09 UTC compared to same-source
as-of replay, with 1H first wick raid/confirmed causal 3m BOS audit.
TECHNICAL research only, not actual author-labelled BOS/entry.
"""
import sys,json,hashlib
from dataclasses import asdict
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c55_crypto_1h_liquidity_raid_bos_lifecycle import (
    audit_original_1h_liquidity_and_3m_bos,STATES)
BASE=ROOT/"evidence/c21/C21B_ORIGINAL_3M_VS_5M_REPLAY_RECEIPT.json"
PIN=ROOT/"evidence/c55/C55_ORIGINAL_45ZIP_1H_LIQUIDITY_FIRST_RAID_LATER_3M_BOS.json"

def report(output=None):
    reference=json.loads(BASE.read_text(encoding="utf8"))
    bysym={x["symbol"]:x for x in reference["observations"]}
    assert len(bysym)==5 and reference["original_total_zip"]==60
    assert reference["totals"]["native3m_cand_edges"]==539
    markets=[];totals=Counter();source_zip_count=0
    for sym in sorted(SYMS):
        orig={}
        for tf in ("15m","1d"):
            orig[tf]=tuple(load_original(sym,tf,date,start)[0]
                          for date,start in zip(DATES,STARTS))
            source_zip_count+=3
        c08=extended_32day_prefix(orig["15m"],orig["1d"],END)
        source3=tuple(native_3m(sym,d)[0] for d in PERIODS)
        source_zip_count+=3
        original=reconcile_native_3m(source3,c08,as_of_ms=END)
        full=audit_original_1h_liquidity_and_3m_bos(original,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        # A true PHYSICAL prefix replay must match as-of crop of full source.
        physical=reconcile_native_3m(source3,c08,as_of_ms=cut)
        prefix=audit_original_1h_liquidity_and_3m_bos(physical,as_of_ms=cut)
        virtual=audit_original_1h_liquidity_and_3m_bos(original,as_of_ms=cut)
        assert prefix==virtual,"C55_ORIGINAL_3M_PHYSICAL_PREFIX_DISAGREES_WITH_CAUSAL_AS_OF"
        assert full.symbol==sym and full.as_of_ms==END
        assert full.original_closed_native3m_count==15360
        assert full.complete_1h_count==768
        assert full.first_confirmed_wick_raids==bysym[sym]["1h_first_fractal_wick"]
        assert full.adapted_closed_native3m_breaks==bysym[sym]["native3m_cand_edges"]
        assert len(full.lifecycle)==full.preknown_1h_fractal_liquidity_levels
        assert sum(e.source_state==STATES[-1] for e in full.lifecycle)==full.adapted_closed_native3m_breaks
        assert all(e.source_as_of_ms==END and e.readiness=="NOT_TRADE_READY"
                   and not e.orders and not e.trades and not e.academic_bos_verified
                   and not e.academic_entry_verified for e in full.lifecycle)
        counts=Counter(x.source_state for x in full.lifecycle)
        totals.update(counts)
        markets.append({
            "symbol":sym,
            "original_3m_closed":full.original_closed_native3m_count,
            "original_1h_fully_closed":full.complete_1h_count,
            "preknown_1h_liquidity_levels":full.preknown_1h_fractal_liquidity_levels,
            "first_confirmed_wick_raids":full.first_confirmed_wick_raids,
            "original_3m_closed_research_breaks":full.adapted_closed_native3m_breaks,
            "source_state_counts":dict(sorted(counts.items())),
            "physically_cut_native3m_matches_original_source_asof":True,
            "events":[asdict(e) for e in full.lifecycle]})
        print("C55_ORIGINAL",sym,dict(sorted(counts.items())),flush=True)
    assert source_zip_count==45
    assert sum(x["original_3m_closed"] for x in markets)==76800
    assert sum(x["original_1h_fully_closed"] for x in markets)==3840
    assert sum(x["first_confirmed_wick_raids"] for x in markets)==642
    assert sum(x["original_3m_closed_research_breaks"] for x in markets)==539
    assert sum(totals.values())==sum(x["preknown_1h_liquidity_levels"] for x in markets)
    a={
      "schema":"EMBER_C55_ORIGINAL_CRYPTO_1H_FIRST_LIQUIDITY_RAID_TO_ADAPTED_3M_BOS_LIFECYCLE_V1",
      "date_utc":"2026-10-25",
      "source":"BINANCE_USDM_2026_ORIGINAL_45_ZIP_WITH_CHECKSUM",
      "scope":"CRYPTO_ONLY_ACADEMIC_ILLUSTRATIONS_ARE_LOGIC_NOT_PRICE",
      "original_zip_count":source_zip_count,
      "original_closed_native3m":76800,
      "original_complete_1h":3840,
      "first_confirmed_1h_wick_raids":642,
      "adapted_3m_price_breaks":539,
      "source_states":dict(sorted(totals.items())),
      "source_prefix_replay":"PHYSICAL_ORIGINAL_ARCHIVES_CUT_AND_FULL_SOURCE_ASOF_REPRODUCIBLE",
      "original_C21B_60ZIP_parent_comparison_Git_witness":"C21B_ORIGINAL_3M_VS_5M_REPLAY_RECEIPT.json",
      "route":"C_1H_RAID_3M_BOS",
      "route_families_A_B_not_changed":True,
      "source_5m_original_BOS_not_implemented_in_C55":True,
      "academic_1h_liquidity_goldens":0,
      "academic_3m_BOS_goldens":0,
      "academic_entry_goldens":0,
      "fills":0,"orders":0,"trades":0,"PnL":None,"readiness":"NOT_TRADE_READY",
      "markets":markets}
    if output:
        p=Path(output);p.parent.mkdir(exist_ok=True,parents=True)
        p.write_text(json.dumps(a,sort_keys=True,indent=2,ensure_ascii=False,default=str)+"\n",encoding="utf8")
    if PIN.exists():
        assert json.loads(PIN.read_text(encoding="utf8"))==json.loads(json.dumps(a,default=str)),"C55_FROZEN_ORIGINAL_SOURCE_DRIFT"
    print("C55_ALL_ORIGINAL_45ZIP_NATIVE_CRYPTO_539_ADAPTED_3M_EVENTS_PASS",flush=True)
    return a
if __name__=="__main__":report(sys.argv[1] if len(sys.argv)>1 else None)
