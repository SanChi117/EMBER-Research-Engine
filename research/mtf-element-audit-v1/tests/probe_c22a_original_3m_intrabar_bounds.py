#!/usr/bin/env python3
"""Source-original 45 USD-M ZIP C22A wick-touch versus closed 3m bounds.

All source ZIP+paired checksums are re-downloaded from Binance, verified
against frozen C08 native 15m OHLCV before deriving tick-inaccessible
intra-3m price-reach lower/upper candle bounds. Never assume actual fills.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for folder in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):
    sys.path.insert(0,str(folder))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c22a_intrabar_vs_closed_3m_provenance import examine_crossing_bounds

FIELDS=("candidate_parent_edges","first_reach_prior_to_closed_break",
        "earlier_reach_without_close","earlier_reach_already_closed_beyond_level",
        "break_bar_open_already_beyond_level","candle_time_unknown_order")

def main(destination=None):
    observations=[]
    baseline=json.loads((ROOT/"evidence"/"c21"/"C21B_ORIGINAL_3M_VS_5M_REPLAY_RECEIPT.json").read_text())
    by_symbol={row["symbol"]:row["native3m_cand_edges"] for row in baseline["observations"]}
    for symbol in sorted(SYMS):
        n={}
        for tf in ("15m","1d"):
            n[tf]=tuple(load_original(symbol,tf,p,t)[0] for p,t in zip(DATES,STARTS))
        c08=extended_32day_prefix(n["15m"],n["1d"],END)
        source=tuple(native_3m(symbol,p)[0] for p in PERIODS)
        full=reconcile_native_3m(source,c08,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        prefix=reconcile_native_3m(source,c08,as_of_ms=cut)
        audit=examine_crossing_bounds(full,as_of_ms=END)
        historical=examine_crossing_bounds(full,as_of_ms=cut)
        independently_cut=examine_crossing_bounds(prefix,as_of_ms=cut)
        assert historical==independently_cut
        assert len(full.original_3m_closed)==15360
        assert audit.candidate_parent_edges==by_symbol[symbol]
        assert audit.author_approved_bos==audit.author_approved_trades==0
        assert audit.readiness=="NOT_TRADE_READY"
        for x in audit.observations:
            assert x.raid_confirmed_ms<=x.structural_swing_known_ms or x.raid_confirmed_ms>x.structural_swing_known_ms
            assert max(x.raid_confirmed_ms,x.structural_swing_known_ms)<=x.first_reachable_cross_start_ms
            assert x.first_reachable_cross_known_ms<=x.close_break_known_ms<=END
            assert x.first_reachable_cross_start_ms<=x.close_break_start_ms
            assert x.first_reachable_cross_native3m_id.endswith(":"+str(x.first_reachable_cross_start_ms))
            assert x.tick_timestamp=="UNOBSERVABLE_WITH_3M_OHLC"
            assert x.market_fill=="UNPROVEN_WITH_OHLC"
        stats={"symbol":symbol,
          "original_native3m_closed":len(full.original_3m_closed),
          "original_native15m_decimal_equalities":full.native_15m_ohlcv_equalities,
          "early_prefix_cut_2026_10_02_0009":historical.candidate_parent_edges,
          "independent_early_prefix_stability":True,
          "five_example_witness_bounds":[{
             "raid_fractal_ms":z.parent_fractal_ms,
             "side":z.side,
             "swing_known_ms":z.structural_swing_known_ms,
             "original3m_first_price_reach_row_id":z.first_reachable_cross_native3m_id,
             "original3m_bos_close_row_id":z.close_break_native3m_id,
             "earlier_reach_bars":z.earlier_reach_bars,
             "author_approval":False
          } for z in audit.observations[:5]]}
        stats.update({k:getattr(audit,k) for k in FIELDS})
        observations.append(stats)
        print(symbol,":",stats["candidate_parent_edges"],"3m price break edges;",
              stats["first_reach_prior_to_closed_break"],
              "with pre-close tick-time ambiguity",flush=True)
    sums={k:sum(x[k] for x in observations) for k in FIELDS}
    result={
      "schema":"EMBER_C22A_ORIGINAL3M_OHLC_BOS_CROSS_VS_CLOSE_BOUNDS_V1",
      "original_3m_zip":15,"original_C08_15m_1d_zip":30,
      "original_total_zip":45,"original_native3m":76800,
      "original_native15m_decimal_parity":15360,
      "source_C21B_receipt_git_blob":"a9a121cb41477b105dd13a1228b5d0577ac3abda",
      "observations":observations,"totals":sums,
      "author_tick_level_labels":0,"author_selected_3m_structural_bos_goldens":0,
      "author_approved_trades":0,"readiness":"NOT_TRADE_READY",
      "meaning":"OHLC wick reach bounds vs closed confirmation of C21B research-selected 3m swing. The exact intrabar crossing timestamp, order, fill and author BOS remain unobservable."
    }
    assert result["totals"]["candidate_parent_edges"]==539
    assert result["totals"]["candle_time_unknown_order"]==539
    assert (result["totals"]["earlier_reach_without_close"]+
            result["totals"]["earlier_reach_already_closed_beyond_level"]==
            result["totals"]["first_reach_prior_to_closed_break"])
    pin=ROOT/"evidence"/"c22"/"C22A_ORIGINAL_3M_CROSS_CLOSE_BOUNDS.json"
    if pin.exists():
        assert json.loads(pin.read_text(encoding="utf8"))==result,"C22A_SOURCE_OHLC_BOUNDS_CHANGED"
    if destination:Path(destination).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result,sort_keys=True,indent=2),flush=True)
if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
