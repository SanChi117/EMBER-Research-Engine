#!/usr/bin/env python3
"""C55 original C37 45ZIP crypto-only adapted 1H Raid→3M BOS source review.

Entire frozen C37 origin is independently accepted; 4 adapted native3m
swing selection hypotheses. 3M source original break bar ID checked and
1H pivot/raid known strictly earlier. 5M not inferred from 3M.
No author BOS, SL/TP, fills, profitability, or trading permission.
"""
import json,sys
from pathlib import Path
from dataclasses import asdict
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"d05"))
from c37_native_adapted_bos_event_scanner import AdaptedClosedBreak
from c36_adapted_pivot_hypotheses import VARIANTS
from c55_crypto_1h_liquidity_raid_3m_bos_route_c_guard import (
 adapted_3m_and_explicit_unassessed_5m,STATES)
SRC=ROOT/"evidence/c37/C37_ORIGINAL_FOUR_ADAPTED_NATIVE3M_BOS_EVENTS.json"
PIN=ROOT/"evidence/c55/C55_ORIGINAL_45ZIP_ROUTE_C_1H_RAID_3M_BOS_4ADAPTED_SOURCE.json"
SYMS={"BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"}

def run(out=None):
    data=json.loads(SRC.read_text(encoding="utf8"))
    assert data["schema"]=="EMBER_C37_INDEPENDENT_ORIGINAL_45ZIP_ADAPTED_3M_BOS_EVENTS_V1"
    assert data["source_native3m_usdm_ZIP_files"]==45
    assert data["source_closed_original3m_total"]==76800
    assert data["native15m_exact_decimal_equalities"]==15360
    assert data["author_selected_bos_goldens"]==data["paper_signals"]==data["orders"]==data["trades"]==0
    assert data["readiness"]=="NOT_TRADE_READY"
    assert set(m["symbol"] for m in data["markets"])==SYMS
    byvariant=Counter();byraid=Counter();by_market=Counter()
    markets=[]
    for market in data["markets"]:
        sym=market["symbol"];hist=[]
        assert market["original3m_rows"]==15360
        assert market["author_selected_bos_goldens"]==market["orders"]==market["trades"]==0
        assert set(market["adapted_routes"])==set(VARIANTS)
        for variant in VARIANTS:
            events=market["adapted_routes"][variant]["native_3m_research_events"]
            assert len(events)==market["adapted_routes"][variant]["raid_context_event_count"]
            for obj in events:
                # dataclass loader does not promote JSON text labels into orders
                e=AdaptedClosedBreak(**obj)
                assert e.symbol==sym and e.hypothesis_id==variant
                three,five=adapted_3m_and_explicit_unassessed_5m(e)
                assert three.source_status==STATES[0] and five.source_status==STATES[1]
                assert three.data_source_timeframe=="3M" and five.data_source_timeframe is None
                assert three.source_original3m_break_bar_id==e.break_original_native3m_row_id
                assert five.source_original3m_break_bar_id is None
                assert not three.academic_BOS_author_verified and not five.academic_BOS_author_verified
                assert not three.orders and not three.trades and not five.orders and not five.trades
                hist.append({
                   "source_variant":variant,
                   "source_1h_liquidity_type":three.raid_type,
                   "source_1h_pivot_center_ms":three.candidate_1h_liquidity_fractal_center_ms,
                   "source_1h_pivot_fully_known_ms":three.candidate_1h_liquidity_fully_known_ms,
                   "source_1h_first_wick_raid_start_ms":three.raid_first_1h_breach_start_ms,
                   "source_1h_wick_raid_confirmed_ms":three.raid_wick_fully_confirmed_ms,
                   "source_3m_swing_bar_id":e.swing_center_native3m_row_id,
                   "source_3m_swing_fully_known_ms":e.swing_confirmed_ms,
                   "source_3m_bos_bar_id":three.source_original3m_break_bar_id,
                   "source_3m_bos_closed_known_ms":three.source_original3m_break_bar_closed_ms,
                   "source_3m_course_route_status":three.source_status,
                   "source_5m_course_route_status":five.source_status,
                   "source_5m_original_market_bar_id":None,
                   "course_author_bos_verified":False,
                   "orders":0,"trades":0})
                byvariant[variant]+=1
                byraid[e.raid_fractal_kind]+=1
                by_market[sym]+=1
        markets.append({"symbol":sym,"source_only_3m_route_C_contexts":len(hist),
          "unique_original_3m_bos_bars_all_adapted_variants":len({x["source_3m_bos_bar_id"] for x in hist}),
          "events":hist})
        print("C55",sym,len(hist),flush=True)
    assert byvariant["LATEST_CONFIRMED_V1"]==539
    assert sum(byvariant.values())==sum(by_market.values())
    assert len(byvariant)==4
    output={
     "schema":"EMBER_C55_ORIGINAL_CRYPTO_45ZIP_1H_LIQUIDITY_RAID_3M_ADAPTED_BOS_ROUTE_C_SOURCE_V1",
     "date_utc":"2026-10-25",
     "owner_scope":"CRYPTO_ONLY",
     "course_figures_role":"LOGIC_EXAMPLES_NOT_MARKET_DATA",
     "original_source_frozen_C37_git_blob":"e4b702e8c6cdc34f1c2475df73ef44ae1631fe56",
     "original_Binance_USDM_zip_lineage":45,
     "original_closed_native3m":76800,
     "exact_native15m":15360,
     "independent_hypothesis_count":4,
     "adapted_source_hypothesis_event_counts":dict(sorted(byvariant.items())),
     "adapted_source_raid_BSL_SSL_counts":dict(sorted(byraid.items())),
     "adapted_source_total_contexts":sum(byvariant.values()),
     "original_5m_Route_C_probed_from_3m":False,
     "original_5m_Route_C_source_status":"NEEDS_DISTINCT_ORIGINAL_NATIVE5M_CAUSAL_REPLAY",
     "author_confirmed_BOS":0,"author_confirmed_1h_liquidity":0,
     "course_author_raid_first_test_verified":0,
     "executed_paper_signals":0,
     "orders":0,"trades":0,"readiness":"NOT_TRADE_READY",
     "markets":markets}
    if out:
        p=Path(out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(output,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
    if PIN.exists():assert output==json.loads(PIN.read_text(encoding="utf8")),"C55_ORIGINAL_SOURCE_DRIFT"
    print(json.dumps({"variants":dict(byvariant),"raids":dict(byraid),
       "source_contexts":sum(byvariant.values()),"orders":0},sort_keys=True),flush=True)
    return output
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
