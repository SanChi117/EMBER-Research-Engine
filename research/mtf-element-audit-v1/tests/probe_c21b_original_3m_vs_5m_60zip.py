#!/usr/bin/env python3
"""C21B independent original Binance USD-M 3m vs 5m first-parent geometry.

Read 30 original C08 15m/1d ZIP, 15 original 3m ZIP and 15 original 5m
ZIP again over HTTPS with original paired .CHECKSUM, verify native exact
Decimal source lineage, then independently compare post-raid price geometry.
PAPER only. Does not classify actual author BOS or trade entry.
"""
from __future__ import annotations
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for folder in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):
    sys.path.insert(0,str(folder))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c20_original_5m_monthly_cross_15m import original_5m
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c20_original_32day_native5m_lineage import reconcile_32day_native5m
from c21b_original_3m_raid_break_geometry import observe_native3m_raid_break
from c20b_five_minute_break_observer import cross_timeframe_raid_break
from c21b_3m_5m_geometry_compare import compare_original_3m_and_5m

FIELDS=("native3m_cand_edges","native5m_cand_edges",
        "same_parent_with_both","only_3m_parent","only_5m_parent",
        "earliest_3m_before_5m","earliest_5m_before_3m",
        "simultaneous_close","distinct_3m_native_break_bars",
        "distinct_5m_native_break_bars","multi_parent_3m_edges",
        "multi_parent_5m_edges")

def replay():
    rows=[]
    for sym in sorted(SYMS):
        originals={}
        for tf in ("15m","1d"):
            originals[tf]=tuple(load_original(sym,tf,d,start)[0]
                                 for d,start in zip(DATES,STARTS))
        c08=extended_32day_prefix(originals["15m"],originals["1d"],END)
        source3=tuple(native_3m(sym,d)[0] for d in PERIODS)
        source5=tuple(original_5m(sym,d)[0] for d in DATES)
        three=reconcile_native_3m(source3,c08,as_of_ms=END)
        five=reconcile_32day_native5m(source5,c08,as_of_ms=END)
        comparison=compare_original_3m_and_5m(three,five,as_of_ms=END)
        cut=OCT_START+DAY+900000
        earlier=compare_original_3m_and_5m(three,five,as_of_ms=cut)
        prefix3=reconcile_native_3m(source3,c08,as_of_ms=cut)
        prefix5=reconcile_32day_native5m(source5,c08,as_of_ms=cut)
        independently_cut=compare_original_3m_and_5m(
            prefix3,prefix5,as_of_ms=cut)
        assert earlier==independently_cut
        assert comparison.native3m_cand_edges>=0
        assert comparison.native5m_cand_edges>=0
        assert (comparison.same_parent_with_both+comparison.only_3m_parent
                ==comparison.native3m_cand_edges)
        assert (comparison.same_parent_with_both+comparison.only_5m_parent
                ==comparison.native5m_cand_edges)
        assert comparison.author_trades==0
        threeobs=observe_native3m_raid_break(three,as_of_ms=END)
        fiveobs=cross_timeframe_raid_break(five,as_of_ms=END)
        assert threeobs.closed_fractal_levels==fiveobs.hourly_fractal_count
        assert threeobs.confirmed_first_wick_raids==fiveobs.hourly_first_clean_wick_count
        assert comparison.readiness=="NOT_TRADE_READY"
        line={"symbol":sym,"original3m_closed":len(three.original_3m_closed),
              "original5m_closed":len(five.original_5m_closed),
              "exact_native15m_3m_equalities":three.native_15m_ohlcv_equalities,
              "exact_native15m_5m_equalities":five.original_15m_equalities,
              "closed_1h_hours":threeobs.source_hourly_closed,
              "1h_first_fractal_wick":threeobs.confirmed_first_wick_raids,
              "earlier_2026_10_02_0015_utc_3m_edges":earlier.native3m_cand_edges,
              "earlier_2026_10_02_0015_utc_5m_edges":earlier.native5m_cand_edges,
              "asof_prefix_reconciled_independently":True}
        line.update({k:getattr(comparison,k) for k in FIELDS})
        rows.append(line)
        print(f"{sym}: original 3m geometric edges={comparison.native3m_cand_edges}; "
              f"original 5m edges={comparison.native5m_cand_edges}; "
              f"shared raid parents={comparison.same_parent_with_both}; "
              f"3m only={comparison.only_3m_parent}; "
              f"5m only={comparison.only_5m_parent}",flush=True)
    return rows
