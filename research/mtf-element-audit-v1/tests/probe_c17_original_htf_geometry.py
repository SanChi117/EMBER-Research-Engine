#!/usr/bin/env python3
"""B1/C17 independent original C08 32-day HTF geometry diagnosis.

Uses frozen C08 original receipts and C16 source verifier, 30 independent raw
USD-M ZIP + checksum downloads. Never creates author-labelled patterns/trades.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for d in (ROOT/"d05",ROOT/"tools",ROOT/"tests"):sys.path.insert(0,str(d))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c17_htf_imb_reaction_diagnostics import diagnose_htf_imb,AUTHOR_UNKNOWN

def main(path=None):
    out=[]
    cutoff=OCT_START+DAY+3_600_000
    for symbol in SYMS:
        chunks={}
        for tf in ("15m","1d"):
            chunks[tf]=tuple(load_original(symbol,tf,d,s)[0] for d,s in zip(DATES,STARTS))
        full=extended_32day_prefix(chunks["15m"],chunks["1d"],END)
        prefix=extended_32day_prefix(chunks["15m"],chunks["1d"],cutoff)
        end=diagnose_htf_imb(full,as_of_ms=END)
        prior=diagnose_htf_imb(prefix,as_of_ms=cutoff)
        rerun_prior=diagnose_htf_imb(full,as_of_ms=cutoff)
        assert prior==rerun_prior, "FUTURE_PRICE_CHANGED_PAST_REACTION_DIAGNOSTIC"
        assert end.author_status==prior.author_status==AUTHOR_UNKNOWN
        assert end.readiness==prior.readiness=="NOT_TRADE_READY"
        counts={}
        for tf,candidates in (("1d",end.candidates_1d),("4h",end.candidates_4h)):
            assert all(c.tf==tf and c.author_status==AUTHOR_UNKNOWN
                       and c.readiness=="NOT_TRADE_READY"
                       and c.parent_attribution=="AUTHOR_PARENT_NOT_DEFINED" for c in candidates)
            assert all(c.known_at_ms<=END and
                       all(t.known_at_ms>c.known_at_ms for t in c.contacts)
                       for c in candidates)
            counts[tf]={"gap_candidates":len(candidates),
                        "with_later_contact":sum(bool(c.contacts) for c in candidates),
                        "without_later_contact":sum(not c.contacts for c in candidates),
                        "with_repeat_contact":sum(c.later_contacts>0 for c in candidates)}
            assert counts[tf]["with_later_contact"]+counts[tf]["without_later_contact"]==len(candidates)
        out.append({"symbol":symbol,"counts":counts,
                    "checked_native_1d":full.crosschecked_native_1d,
                    "derived_4h":len(full.derived_4h_closed),
                    "prefix_invariant":True,
                    "author_approved_stronghl":0,"author_approved_poi":0,
                    "author_approved_vc":0,"trades":0})
        print(f"{symbol}: 32 source-checked native 1d, {len(full.derived_4h_closed)} closed 4h, HTF candidate counts {counts}",flush=True)
    result={"cycle":"B1_C17_READ_ONLY_1D_4H_GEOMETRIC_CANDIDATE_DIAGNOSTICS",
            "market":"BINANCE_USDM_FUTURES",
            "period_utc":["2026-09-01","2026-10-02"],
            "original_C08_sources_replayed":30,
            "source_certification":"C08_ORIGINAL_15M_NATIVE_1D_C16_VERIFIER",
            "observations":out,
            "author_golden_source_status":AUTHOR_UNKNOWN,
            "ready_trades":0,"readiness":"NOT_TRADE_READY",
            "limitations":"Only 32 days and three-closed-bar IMB geometry; not author POI/StrongHL/VC, not independently author-labelled Futures signals, not 32-day original 5m, no numerical performance"}
    pinned=json.loads((ROOT/"evidence"/"c17"/"C17_ORIGINAL_C08_1D_4H_CANDIDATE_RESULT.json").read_text(encoding="utf8"))
    assert pinned["schema"]=="EMBER_B1_C17_NATIVE_C08_1D_4H_RESEARCH_GEOMETRY_V1"
    assert pinned["baseline_reused_original_c08_c16_git_blob"]=="bdaa008ce719254507ea95231cdc630bfa85cd67"
    assert pinned["original_native_zip_sources"]==30
    assert pinned["native_15m_closed"]==15360
    assert pinned["derived_4h_closed"]==960
    assert pinned["independent_native_1d_equalities"]==160
    assert pinned["author_golden_source_status"]==AUTHOR_UNKNOWN
    assert pinned["trade_ready"]==pinned["author_approved_poi"]==pinned["author_approved_stronghl"]==pinned["author_approved_vc"]==0
    assert len(pinned["observations"])==len(out)
    for actual,fixed in zip(out,pinned["observations"]):
        assert actual["symbol"]==fixed["symbol"]
        assert actual["checked_native_1d"]==fixed["checked_native_1d"]
        assert actual["derived_4h"]==fixed["derived_closed_4h"]
        for tf in ("1d","4h"):
            assert actual["counts"][tf]==fixed[tf], (actual["symbol"],tf,"PINNED_RESULT_DRIFT")
    assert len(out)==5 and sum(x["checked_native_1d"] for x in out)==160
    assert sum(x["derived_4h"] for x in out)==960
    assert result["ready_trades"]==0
    if path: Path(path).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    return 0
if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else None))
