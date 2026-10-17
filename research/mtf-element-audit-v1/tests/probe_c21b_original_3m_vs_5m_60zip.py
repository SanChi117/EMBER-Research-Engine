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

def main(output=None):
    rows=replay()
    totals={k:sum(x[k] for x in rows) for k in FIELDS}
    result={
      "schema":"EMBER_C21B_NATIVE_3M_5M_ORIGINAL_60_SOURCE_PARENT_DIFFERENCES_V1",
      "period_utc":["2026-09-01","2026-10-02"],
      "original_C08_15m_1d_zip":30,"original_C20_5m_zip":15,
      "original_C21_3m_zip":15,"original_total_zip":60,
      "original_native3m_bars":sum(x["original3m_closed"] for x in rows),
      "original_native5m_bars":sum(x["original5m_closed"] for x in rows),
      "source_native15m_parities_3m":sum(x["exact_native15m_3m_equalities"] for x in rows),
      "source_native15m_parities_5m":sum(x["exact_native15m_5m_equalities"] for x in rows),
      "hourly_source_equivalent":sum(x["closed_1h_hours"] for x in rows),
      "observations":rows,"totals":totals,
      "author_labelled_3m_bos":0,"author_labelled_5m_bos":0,
      "author_approved_trades":0,"readiness":"NOT_TRADE_READY",
      "scope_notice":"Research strict-three-candle 3m and 5m first closed price crossings after next full 1h wick fractal confirmation; per-parent edges not independent trades, no author selection of swing or session or FTA/SL."
    }
    assert len(rows)==5 and result["original_native3m_bars"]==76800
    assert result["original_native5m_bars"]==46080
    assert result["source_native15m_parities_3m"]==15360
    assert result["source_native15m_parities_5m"]==15360
    assert result["hourly_source_equivalent"]==3840
    assert result["totals"]["native5m_cand_edges"]==512
    assert result["totals"]["same_parent_with_both"]+result["totals"]["only_3m_parent"]==result["totals"]["native3m_cand_edges"]
    assert result["totals"]["same_parent_with_both"]+result["totals"]["only_5m_parent"]==512
    pin=ROOT/"evidence"/"c21"/"C21B_ORIGINAL_3M_VS_5M_REPLAY_RECEIPT.json"
    if pin.is_file():
        recorded=json.loads(pin.read_text(encoding="utf8"))
        assert recorded==result,"C21B_PINNED_SOURCE_PARITY_OR_PARENT_DRIFT"
    if output:Path(output).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result,sort_keys=True,indent=2),flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
