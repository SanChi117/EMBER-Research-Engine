#!/usr/bin/env python3
"""C22B source-observed pivot conflict replay on 45 original USD-M ZIP.

Not an author-labelled backtest. No author BOS, sessions or trading signal.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for d in ("d05","tools","tests"):sys.path.insert(0,str(ROOT/d))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c22b_source_inventory import audit_rival_pivots

FIELDS=("observed_parent_edges","multiple_eligible_parent_edges",
        "same_bar_multiple_crossings","eligible_pivot_options",
        "alternate_pivot_options","simultaneous_extra_crossings")

def replay():
    original=json.loads((ROOT/"evidence"/"c21"/"C21B_ORIGINAL_3M_VS_5M_REPLAY_RECEIPT.json").read_text(encoding="utf8"))
    baseline={r["symbol"]:r["native3m_cand_edges"] for r in original["observations"]}
    out=[]
    for sym in sorted(SYMS):
        n={}
        for tf in ("15m","1d"):
            n[tf]=tuple(load_original(sym,tf,p,t)[0] for p,t in zip(DATES,STARTS))
        source15=extended_32day_prefix(n["15m"],n["1d"],END)
        source3=tuple(native_3m(sym,p)[0] for p in PERIODS)
        full=reconcile_native_3m(source3,source15,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        prefix=reconcile_native_3m(source3,source15,as_of_ms=cut)
        a=audit_rival_pivots(full,as_of_ms=END)
        partial=audit_rival_pivots(full,as_of_ms=cut)
        independently=audit_rival_pivots(prefix,as_of_ms=cut)
        assert partial==independently
        assert a["observed_parent_edges"]==baseline[sym]
        assert a["author_approved_trades"]==a["source_author_goldens"]==0
        assert a["readiness"]=="NOT_TRADE_READY"
        assert a["eligible_pivot_options"]==a["observed_parent_edges"]+a["alternate_pivot_options"]
        row={"symbol":sym,"native3m_bars":len(full.original_3m_closed),
             "native15m_price_parity":full.native_15m_ohlcv_equalities,
             "source_prefix_independent":True,
             "first_ten_rival_pivots":a["first_ten_research_cases"]}
        row.update({k:a[k] for k in FIELDS})
        out.append(row)
        print(sym,"edges",a["observed_parent_edges"],
              "multiple_pivots",a["multiple_eligible_parent_edges"],
              "same-bar alternative crossings",a["same_bar_multiple_crossings"],flush=True)
    return out

def main(output=None):
    per_symbol=replay()
    total={k:sum(r[k] for r in per_symbol) for k in FIELDS}
    result={"schema":"EMBER_C22B_ORIGINAL_3M_PIVOT_ALTERNATIVES_V1",
      "period_utc":["2026-09-01","2026-10-02"],"verified_total_source_zip":45,
      "native3m_closed":sum(r["native3m_bars"] for r in per_symbol),
      "native15m_decimal_equalities":sum(r["native15m_price_parity"] for r in per_symbol),
      "observations":per_symbol,"totals":total,
      "author_timestamped_binance_bos_goldens":0,
      "author_approved_trades":0,"readiness":"NOT_TRADE_READY"}

    assert result["native3m_closed"]==76800
    assert result["native15m_decimal_equalities"]==15360
    assert total["observed_parent_edges"]==539
    assert total["eligible_pivot_options"]==539+total["alternate_pivot_options"]
    assert total["multiple_eligible_parent_edges"]>=total["same_bar_multiple_crossings"]
