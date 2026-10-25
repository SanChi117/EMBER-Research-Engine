#!/usr/bin/env python3
"""C77 independent original crypto 45ZIP source replay. No trades."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in ("d05","tests","tools"):sys.path.insert(0,str(ROOT/p))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c62_academic_snr_rb_imb_liquidity_source_separation import observe_hourly_source_poi_split
from c77_original_parent_source_first3m import inspect,summarize
C73=ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json"
C21=ROOT/"evidence/c21/C21A_NATIVE3M_C08_PARITY_RECEIPT.json"
SHA="c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b"
def replay(out=None):
    raw=C73.read_bytes()
    assert len(raw)==303327 and hashlib.sha256(raw).hexdigest()==SHA
    frozen={x["symbol"]:x for x in json.loads(raw)["markets"]}
    receipts={x["symbol"]:x for x in json.loads(C21.read_text())["observations"]}
    assert set(frozen)==set(SYMS)==set(receipts)
    markets=[]
    for sym in sorted(SYMS):
        s={tf:tuple(load_original(sym,tf,d,at)[0] for d,at in zip(DATES,STARTS))
           for tf in ("15m","1d")}
        h=extended_32day_prefix(s["15m"],s["1d"],END)
        archives=[]
        for period in PERIODS:
            a,receipt=native_3m(sym,period)
            assert receipt==next(v for v in receipts[sym]["new_original_source_zip"]
                                 if v["period"]==period)
            archives.append(a)
        n3=reconcile_native_3m(tuple(archives),h,as_of_ms=END)
        assert n3.native_15m_ohlcv_equalities==3072
        c62=observe_hourly_source_poi_split(h.derived_1h_closed,as_of_ms=END)
        assert c62["author_goldens"]==0
        cases=[inspect(case,c62["technical_1h_snr_rb_separate_cases"],
                c62["technical_original_1h_imb_gaps"],n3.original_3m_closed,END)
               for case in frozen[sym]["original_parent_source_cases"]]
        summary=summarize(cases)
        assert summary["contexts"]==frozen[sym]["c46_parent_count"]
        markets.append({"symbol":sym,"review":summary,
          "verified_3m_zip":[a.zip_sha for a in archives],
          "verified_15m_zip":[a.zip_sha256 for a in s["15m"]],
          "verified_1d_zip":[a.zip_sha256 for a in s["1d"]],
          "closed_3m":len(n3.original_3m_closed),
          "author_approved":0,"trades":0})
        print("C77_PARENT_SOURCE",sym,summary,flush=True)
    assert sum(x["review"]["contexts"] for x in markets)==153
    doc={"schema":"EMBER_C77_FRESH_ORIGINAL45ZIP_FIRST3M_PARENT_C62_AUDIT_V1",
       "period_utc":["2026-09-01","2026-10-02"],
       "original_zip_counts":{"3m":15,"15m":15,"1d":15,"total":45},
       "original3m_closed":76800,"native15m_equalities":15360,
       "source_C73_sha256":SHA,"source_contexts":153,
       "evidence_class":"ADAPTED_HYPOTHESIS","markets":markets,
       "author_verified":0,"orders":0,"fills":0,"trades":0,
       "readiness":"NOT_TRADE_READY",
       "limitations":["Not a 5m replay","C62 source rules are proxy semantics only",
            "No author's timestamped positive/negative crypto goldens"]}
    if out:Path(out).write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n")
    print("C77_RESULT_JSON:"+json.dumps(doc,sort_keys=True,separators=(",",":")),flush=True)
    print("C77_45ZIP_SOURCE_PASS",flush=True)
    return doc
if __name__=="__main__":replay(sys.argv[1] if len(sys.argv)>1 else None)
