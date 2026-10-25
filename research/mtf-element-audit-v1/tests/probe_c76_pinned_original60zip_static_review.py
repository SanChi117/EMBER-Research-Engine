#!/usr/bin/env python3
"""C76 pinned original60ZIP replay: independently check JSON invariants.

This is not a replacement for a fresh 60ZIP replay. Run alongside it.
"""
from collections import Counter
from pathlib import Path
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
C73=ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json"
C76=ROOT/"evidence/c76/C76_FRESH_ORIGINAL60ZIP_ADAPTED_FVG_PARENT_REPLAY.json"
C73_SHA="c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b"
def verify():
    d=json.loads(C76.read_bytes())
    older=C73.read_bytes()
    assert len(older)==303327 and hashlib.sha256(older).hexdigest()==C73_SHA
    assert d["source_C73_frozen_sha256"]==C73_SHA
    assert d["schema"]=="EMBER_C76_REAL_ORIGINAL60ZIP_ADAPTED_FVG_1H_PARENT_REPLAY_V1"
    assert d["original_source_period_utc"]==["2026-09-01","2026-10-02"]
    assert d["original_zip_counts"]=={"3m":15,"5m":15,"15m":15,"1d":15}
    assert d["fresh_full_original_60zip_source_replay"] is True
    assert d["fresh_C73_153_parent_algorithm_full_reexecution"] is False
    assert d["original_closed_bar_counts"]=={"native3m":76800,"native5m":46080,
                                            "native15m":15360,"native1d":160}
    assert d["original_decimal_parity"]=={"3m_to_15m":15360,"5m_to_15m":15360}
    assert d["evidence_class"]=="ADAPTED_HYPOTHESIS"
    syms=("BCHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT")
    assert len(d["markets"])==5
    assert tuple(x["symbol"] for x in d["markets"])==syms
    full=Counter(); po=Counter(); zips=[]
    for x in d["markets"]:
        assert x["original_counts"]=={"3m":15360,"5m":9216,"15m":3072,"1d":32}
        assert x["exact_3m_to_native15m"]==3072
        assert x["exact_5m_to_native15m"]==3072
        assert len(x["original_archives"])==12
        for a in x["original_archives"]:
            s=a.get("zip_sha256",a.get("original_zip_sha256"))
            assert isinstance(s,str) and len(s)==64
            assert all(c in "0123456789abcdef" for c in s)
            zips.append(s)
        c=x["c73_parent_poi_crosscheck"]
        assert c["original_c73_contexts"]==len(json.loads(older)["markets"][
          syms.index(x["symbol"])]["original_parent_source_cases"])
        assert c["author_approved"]==c["orders"]==c["fills"]==c["trades"]==0
        assert x["author_verified"]==x["orders"]==x["fills"]==x["trades"]==0
        for tf,n in x["adapted_closed_source_fvg_counts"].items():
            assert tf in ("3m","5m","15m") and type(n) is int and n>=0
            full[tf]+=n
        for name,n in c["parent_fvg_context_counts"].items():
            po[name]+=n
        assert len(x["adapted_first_candidate_lifecycle_samples"])==3
    assert len(zips)==60
    assert all(k>=0 for k in full.values())
    assert dict(full)=={"3m":18762,"5m":10338,"15m":3048}
    assert dict(po)=={"NONE":47,"NOT_TESTED":71,
          "NO_PRETOUCH_SAME_SIDE_PARENT_FVG":29,
          "CONTAINED_FVG_IN_RB_OR_SNR_PARENT_UNVERIFIED":5,
          "PARTIAL_PARENT_OVERLAP_NO_AUTOMATIC_ENTRY":1}
    assert sum(po.values())==153
    assert d["source_C73_case_count"]==153
    assert (d["author_valid_poi_first_tests_verified"],
            d["author_15m_trigger_vc_positive_verified"],
            d["author_vc_stronghl_structural_sl_tp_verified"],
            d["orders"],d["fills"],d["trades"])==(0,0,0,0,0,0)
    assert d["pnl"] is None and d["readiness"]=="NOT_TRADE_READY"
    print("C76_PINNED_JSON_REVIEW_PASS",hashlib.sha256(C76.read_bytes()).hexdigest(),
          "FVG",dict(sorted(full.items())),"153_SOURCE_CONTEXTS_NO_TRADES")
if __name__=="__main__":verify()
