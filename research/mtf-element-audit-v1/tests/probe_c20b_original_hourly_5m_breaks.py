#!/usr/bin/env python3
"""C20B price geometry replay: real 5m native sources and C08 1h equivalents.

No author-labelled currency Futures BOS, no market orders or trade outcomes.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):sys.path.insert(0,str(p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c20_original_5m_monthly_cross_15m import original_5m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c20_original_32day_native5m_lineage import reconcile_32day_native5m
from c20b_hourly_fractal_source_observer import closed_hourly
from c20b_five_minute_break_observer import cross_timeframe_raid_break

def main(path=None):
    obs=[]
    for sym in SYMS:
        prev={}
        for tf in ("15m","1d"):
            prev[tf]=tuple(load_original(sym,tf,d,t)[0] for d,t in zip(DATES,STARTS))
        c08=extended_32day_prefix(prev["15m"],prev["1d"],END)
        five=tuple(original_5m(sym,d)[0] for d in DATES)
        source=reconcile_32day_native5m(five,c08,as_of_ms=END)
        hours=closed_hourly(source,END)
        assert len(hours)==768 and len(c08.derived_1h_closed)==768
        for actual,expected in zip(hours,c08.derived_1h_closed):
            assert (actual.start_ms,actual.close_ms,actual.open,actual.high,
                    actual.low,actual.close)==(expected.start_ms,expected.known_at_ms,
                                               expected.open,expected.high,expected.low,expected.close)
        observed=cross_timeframe_raid_break(source,as_of_ms=END)
        cut=OCT_START+DAY+300000
        former=cross_timeframe_raid_break(source,as_of_ms=cut)
        independently_cut=reconcile_32day_native5m(five,c08,as_of_ms=cut)
        future_stable=cross_timeframe_raid_break(independently_cut,as_of_ms=cut)
        assert former==future_stable
        assert observed.native5m_bars==9216
        assert observed.author_approved_bos==observed.author_approved_trades==0
        assert observed.readiness=="NOT_TRADE_READY"
        assert all(w.raid.confirmed_at_ms<=w.start_ms<w.known_ms<=END and
                   w.swing.known_ms<=w.start_ms and
                   ((w.swing.level<w.raid.fractal.level and w.side=="SHORT") or
                    (w.swing.level>w.raid.fractal.level and w.side=="LONG"))
                   for w in observed.potential_bos_witnesses)
        cases=[{
           "first_1h_fractal_center_ms":w.raid.fractal.center_ms,
           "direction":w.side,
           "confirmed_raid_ms":w.raid.confirmed_at_ms,
           "bos_closed_ms":w.known_ms,
           "bos_original_5m_row_id":w.source_row_id
        } for w in observed.potential_bos_witnesses[:5]]
        obs.append({
          "symbol":sym,
          "native_5m_source_rows":observed.native5m_bars,
          "closed_source_1h":observed.closed1h_bars,
          "closed_original_c08_1h_parities":len(hours),
          "observed_1h_fractal_levels":observed.hourly_fractal_count,
          "observed_1h_first_confirmed_wick_geometry":observed.hourly_first_clean_wick_count,
          "observed_5m_strict_swing_candidates":observed.five_minute_swing_count,
          "observed_5m_price_break_candidates":len(observed.potential_bos_witnesses),
          "first_five_schematic_replay_events":cases,
          "asof_earlier_prefix_2026_10_02_0005_candidates":len(former.potential_bos_witnesses),
          "no_trading_and_no_author_goldens":True
        })
        print(f"{sym}: 1h pivots={observed.hourly_fractal_count} confirmed 1h first wick={observed.hourly_first_clean_wick_count} observed post-raid 5m breaks={len(observed.potential_bos_witnesses)}",flush=True)
    result={
       "cycle":"B1_C20B_NATIVE_SOURCE_1H_FIRST_FRACTAL_WICK_TO_5M_CLOSE_BREAK",
       "original_5m_sources":15,"original_C08_15m_1d_sources":30,
       "rows_5m":sum(x["native_5m_source_rows"] for x in obs),
       "hourly_source_ohlc_parities":sum(x["closed_original_c08_1h_parities"] for x in obs),
       "symbols":[x["symbol"] for x in obs],
       "observations":obs,
       "readiness":"NOT_TRADE_READY",
       "author_golden_source_status":"AUTHOR_GOLDEN_SOURCE_UNAVAILABLE",
       "author_approved_bos":0,"author_approved_trades":0,
       "assumption":"Strict three-bar 5m swing and first close-break after confirmed 1h raid are explicit operational geometry, not independently author-labelled BOS.",
       "missing":"Source does not settle 5m structural pivot priority, sessions/timezones, FTA/SL and original 3m goldens; real crypto-ready trade algorithm unavailable."
    }
    assert result["rows_5m"]==46080
    assert result["hourly_source_ohlc_parities"]==3840
    assert result["author_approved_trades"]==0
    pin=ROOT/"evidence"/"c20"/"C20B_ORIGINAL_1H_5M_AGGREGATES.json"
    if pin.is_file():
        fixed=json.loads(pin.read_text(encoding="utf8"))
        assert fixed["schema"]=="EMBER_C20B_HISTORICAL_AGGREGATE_REPLAY_V1"
        assert fixed["source_5m_bars"]==result["rows_5m"]==46080
        assert fixed["source_hourly_parities"]==result["hourly_source_ohlc_parities"]==3840
        for x,pinned in zip(result["observations"],fixed["per_symbol"]):
            assert [x["symbol"],x["observed_1h_fractal_levels"],
                    x["observed_1h_first_confirmed_wick_geometry"],
                    x["observed_5m_price_break_candidates"]]==pinned
        assert fixed["totals"]["closed_5m_crosses"]==sum(x["observed_5m_price_break_candidates"] for x in obs)==512
        assert fixed["totals"]["first_wick_geometry_1h"]==sum(x["observed_1h_first_confirmed_wick_geometry"] for x in obs)==642
        assert fixed["academic_bos_certified"] is False
        assert fixed["readiness"]=="NOT_TRADE_READY"
    if path:Path(path).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result,sort_keys=True,indent=2),flush=True)
if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
