#!/usr/bin/env python3
"""C19 original 30 native C08 ZIP replay: closed 15m first-fractal wick raid.

Independent exact SHA-certified C16/C18 lineage upstream; no author-labelled
BOS, POI or trades and no invented same-timeframe 3m/5m replay.
"""
from __future__ import annotations
import json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for d in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):sys.path.insert(0,str(d))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,OCT_START,DAY,END
from c19_fractal_wick_raid_source_witness import build_c19_fractal_wick_witness
from c17_htf_imb_reaction_diagnostics import AUTHOR_UNKNOWN

def counts(graph):
    kinds=Counter(x.kind for x in graph.fractal_levels)
    states=Counter(x.verdict for x in graph.first_breaches)
    assert set(x.id for x in graph.fractal_levels)==set(x.pivot_id for x in graph.first_breaches)
    assert sum(states.values())==len(graph.fractal_levels)
    assert all(x.raid_confirmed_at_ms>x.breach_close_known_at_ms>x.pivot_known_at_ms
               for x in graph.first_breaches if x.raid_confirmed_at_ms is not None)
    assert all(x.raid_known_at_ms>x.first_ltf_contact_known_at_ms for x in graph.first_contact_raid_coobservations)
    assert graph.author_status==AUTHOR_UNKNOWN and graph.readiness=="NOT_TRADE_READY"
    assert graph.author_approved_stronghl==graph.author_approved_vc==graph.candidate_bos_3m5m==0
    return {
        "fractal_bsl_closed":kinds["BSL"],
        "fractal_ssl_closed":kinds["SSL"],
        "first_clean_fractal_wick_breaches":states["FIRST_WICK_BREACH_CONFIRMED_FRACTAL_GEOMETRY"],
        "first_breach_body_not_clean":states["FIRST_BREACH_BODY_NOT_CLEAN_RAID"],
        "first_wick_unconfirmed_fractal":states["FIRST_WICK_BREACH_NOT_CONFIRMED_FRACTAL"],
        "first_wick_wait_next_close":states["FIRST_WICK_BREACH_AWAIT_NEXT_BAR"],
        "never_breached_in_prefix":states["NO_FIRST_BREACH_IN_PREFIX"],
        "htf_first_contact_and_clean_fractal_wick_coobservations":len(graph.first_contact_raid_coobservations),
        "distinct_htf_parents_with_exact_fractal_wick_contact":len({x.htf_id for x in graph.first_contact_raid_coobservations}),
        "distinct_raid_pivots_coobserved_at_htf_contact":len({x.pivot_id for x in graph.first_contact_raid_coobservations}),
        "coobservations_with_later_15m_gap_geometry":sum(x.later_15m_gap_geometry_count>0 for x in graph.first_contact_raid_coobservations),
        "coobservations_with_later_1h_gap_geometry":sum(x.later_1h_gap_geometry_count>0 for x in graph.first_contact_raid_coobservations),
        "author_stronghl_approved":0,"author_vc_approved":0,"author_bos_3m5m_approved":0,
        "readiness":"NOT_TRADE_READY"
    }

def main(path=None):
    out=[]
    cutoff=OCT_START+DAY+3600000
    for symbol in SYMS:
        chunks={tf:tuple(load_original(symbol,tf,day,start)[0] for day,start in zip(DATES,STARTS))
                for tf in ("15m","1d")}
        full=extended_32day_prefix(chunks["15m"],chunks["1d"],END)
        short=extended_32day_prefix(chunks["15m"],chunks["1d"],cutoff)
        end=build_c19_fractal_wick_witness(full,as_of_ms=END)
        earlier=build_c19_fractal_wick_witness(short,as_of_ms=cutoff)
        repeated=build_c19_fractal_wick_witness(full,as_of_ms=cutoff)
        assert earlier==repeated,"FUTURE_SOURCE_SUFFIX_CHANGED_PAST_15M_FRACTAL_RAID_CAUSAL_OBSERVATION"
        ct=counts(end)
        out.append({"symbol":symbol,"counts":ct,
                    "verified_native_15m_closed":len(full.native_15m_closed),
                    "matched_native_daily":full.crosschecked_native_1d,
                    "future_suffix_invariant":True,
                    "source_32day_original_native_3m5m":False})
        print(f"{symbol}: native 15m={len(full.native_15m_closed)} closed fractal levels={ct['fractal_bsl_closed']+ct['fractal_ssl_closed']}, first clean fractal-wick breaches={ct['first_clean_fractal_wick_breaches']}, exact HTF contact pairs={ct['htf_first_contact_and_clean_fractal_wick_coobservations']}",flush=True)
    result={
        "cycle":"B1_C19_FRACTAL_FIRST_WICK_RAID_NATIVE_15M_SOURCE_OBSERVATIONS",
        "market":"BINANCE_USDM_FUTURES","period_utc":["2026-09-01","2026-10-02"],
        "original_C08_archive_sources_replayed":30,
        "verified_native_15m_rows":sum(x["verified_native_15m_closed"] for x in out),
        "original_native_1d_equalities":sum(x["matched_native_daily"] for x in out),
        "observations":out,"author_golden_source_status":AUTHOR_UNKNOWN,
        "readiness":"NOT_TRADE_READY","trades":0,
        "limitations":"Strict 3-bar 15m fractal pivots and first wick-only breached pivot confirmed on next closed native 15m bar. HTF zone contact must be exact same native 15m candle. Geometrical coincidence is not a certified author raid, POI, StrongHL or BOS. Original academic BOS model typically 1H raid->3m/5m BOS; 32-day original 3m/5m archives unavailable; no price/pip/session assumptions, no trade/ROI."}
    assert len(out)==5 and result["verified_native_15m_rows"]==15360
    assert result["original_native_1d_equalities"]==160 and result["trades"]==0
    pinned_file=ROOT/"evidence"/"c19"/"C19_ORIGINAL_NATIVE15M_FRACTAL_WICK_RESULT.json"
    if pinned_file.exists():
        pinned=json.loads(pinned_file.read_text(encoding="utf8"))
        assert pinned["schema"]=="EMBER_C19_NATIVE_C08_FRACTAL_FIRST_WICK_GEOMETRY_ONLY"
        assert pinned["observations"]==result["observations"],"PINNED_FRACTAL_WICK_COUNTS_DRIFT"
        assert pinned["original_archive_sources"]==30
        assert pinned["original_native_15m"]==15360 and pinned["original_native_1d_equalities"]==160
        assert pinned["author_golden_source_status"]==AUTHOR_UNKNOWN
        assert pinned["readiness"]=="NOT_TRADE_READY" and pinned["author_approvals"]==pinned["trades"]==0
    if path:Path(path).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    return 0
if __name__=="__main__":raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
