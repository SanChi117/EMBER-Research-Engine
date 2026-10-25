#!/usr/bin/env python3
"""C77 forensic replay: NEVER repair source case direction or promote author VC.

Keep the strict inspect() fail-closed. Classify each independent mismatch
against genuine original 45 Binance USD-M ZIP and pinned C73 source receipt.
"""
import sys,json,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
for p in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c62_academic_snr_rb_imb_liquidity_source_separation import observe_hourly_source_poi_split
from c77_original_parent_source_first3m import inspect,C77Rejected
P=ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json"
SHA="c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b"
def run(path=None):
    raw=P.read_bytes()
    assert len(raw)==303327 and hashlib.sha256(raw).hexdigest()==SHA
    by={m["symbol"]:m for m in json.loads(raw)["markets"]}
    markets=[];issues=[]
    for sym in sorted(SYMS):
        src={tf:tuple(load_original(sym,tf,d,t)[0] for d,t in zip(DATES,STARTS))
             for tf in ("15m","1d")}
        htf=extended_32day_prefix(src["15m"],src["1d"],END)
        n3=reconcile_native_3m(tuple(native_3m(sym,p)[0] for p in PERIODS),htf,as_of_ms=END)
        catalog=observe_hourly_source_poi_split(htf.derived_1h_closed,as_of_ms=END)
        success=Counter();bad=Counter();count=0
        for c in by[sym]["original_parent_source_cases"]:
            count+=1
            try:
                v=inspect(c,catalog["technical_1h_snr_rb_separate_cases"],
                          catalog["technical_original_1h_imb_gaps"],
                          n3.original_3m_closed,END)
                success[v[0]]+=1
            except C77Rejected as ex:
                message=str(ex)
                code=message.split(" ",1)[0]
                bad[code]+=1
                issues.append({"symbol":sym,"parent_index":c["original_c46_4h_parent_index"],
                   "source_context_side":c["side"],
                   "source_kind":c["source_1h_poi_kind"],
                   "source_created_ms":c["source_1h_poi_created_at_ms"],
                   "reason":message[:500]})
        markets.append({"symbol":sym,"contexts":count,"source_verified_groups":dict(success),
                        "source_rejected_groups":dict(bad)})
        print("C77_FORENSIC",sym,"contexts",count,"verified",sum(success.values()),"reject",dict(bad),flush=True)
    assert sum(m["contexts"] for m in markets)==153
    doc={"schema":"EMBER_C77_FORENSIC_ORIGINAL45ZIP_SOURCE_CONTRADICTIONS_V1",
         "period_utc":["2026-09-01","2026-10-02"],
         "source_C73_sha256":SHA,
         "original_zip_verified":{"native3m":15,"native15m":15,"native1d":15,"total":45},
         "source_contexts":153,"fully_strict_verified_contexts":153-len(issues),
         "source_semantic_conflict_contexts":len(issues),
         "issues":issues,"markets":markets,
         "author_grade_verified":0,"orders":0,"fills":0,"trades":0,
         "readiness":"NOT_TRADE_READY",
         "decision":"CONFLICTS_BLOCK_ROUTE_A_PROMOTION" if issues else "SOURCE_ONLY_NOT_AUTHOR"}
    if path:Path(path).write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n")
    print("C77_FORENSIC_JSON:"+json.dumps(doc,separators=(",",":"),sort_keys=True),flush=True)
    print("C77_REAL45_COMPLETE_FORENSIC_DONE_NOT_TRADE_READY",flush=True)
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
