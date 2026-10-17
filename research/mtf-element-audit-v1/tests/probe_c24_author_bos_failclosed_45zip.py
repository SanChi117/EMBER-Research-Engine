#!/usr/bin/env python3
"""C24 original Binance Futures 45 source ZIP fail-closed entry adjudication."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):sys.path.insert(0,str(p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c24_bos_research_admission_gate import audit_route_admission

FIELDS=("total_original_research_edges","source_single_pivot_single_parent",
        "multiple_pivot_refused","no_intact_pivot_refused",
        "multiple_parent_refused","single_research_without_author_labels")
def replay():
    out=[]
    for sym in sorted(SYMS):
        original={}
        for tf in ("15m","1d"):
            original[tf]=tuple(load_original(sym,tf,p,t)[0] for p,t in zip(DATES,STARTS))
        source15=extended_32day_prefix(original["15m"],original["1d"],END)
        zips=tuple(native_3m(sym,p)[0] for p in PERIODS)
        full=reconcile_native_3m(zips,source15,as_of_ms=END)
        cut=OCT_START+DAY+3*THREE
        truncated=reconcile_native_3m(zips,source15,as_of_ms=cut)
        full_early=audit_route_admission(full,as_of_ms=cut)
        trunc_early=audit_route_admission(truncated,as_of_ms=cut)
        assert full_early==trunc_early,"C24_NO_LOOKAHEAD"
        result=audit_route_admission(full,as_of_ms=END)
        assert result.approved_trades==result.author_approved_bos==0
        assert result.readiness=="NOT_TRADE_READY"
        assert all(not e.author_approved for e in result.cases)
        record={"symbol":sym,"original_3m_bars":len(full.original_3m_closed),
          "native15m_parity":full.native_15m_ohlcv_equalities,
          "prefix_source_equal":True}
        record.update({k:getattr(result,k) for k in FIELDS})
        out.append(record)
        print(sym,"research singles",result.source_single_pivot_single_parent,
              "multi-pivot rejects",result.multiple_pivot_refused,
              "multi-parent rejects",result.multiple_parent_refused,flush=True)
    return out

def main(target=None):
    rows=replay()
    totals={k:sum(x[k] for x in rows) for k in FIELDS}
    r={"schema":"EMBER_C24_FAIL_CLOSED_RESEARCH_BOS_V1",
       "original_zip":45,"native3m_closed":sum(x["original_3m_bars"] for x in rows),
       "native15m_equalities":sum(x["native15m_parity"] for x in rows),
       "original_source_market_results":rows,"totals":totals,
       "author_approved_bos":0,"author_approved_trades":0,
       "readiness":"NOT_TRADE_READY"}
    assert r["native3m_closed"]==76800 and r["native15m_equalities"]==15360
    assert totals["total_original_research_edges"]==539
    assert totals["multiple_pivot_refused"]+totals["no_intact_pivot_refused"]+totals["multiple_parent_refused"]+totals["single_research_without_author_labels"]==539
    pin=ROOT/"evidence"/"c24"/"C24_ORIGINAL_3M_FAIL_CLOSED_ADMISSION.json"
    if pin.exists():assert json.loads(pin.read_text(encoding="utf8"))==r
    if target:Path(target).write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(r,indent=2,sort_keys=True),flush=True)
if __name__=="__main__":main(sys.argv[1] if len(sys.argv)>1 else None)
