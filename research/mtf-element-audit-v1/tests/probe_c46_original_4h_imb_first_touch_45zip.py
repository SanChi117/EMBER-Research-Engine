#!/usr/bin/env python3
"""C46 original 45 Binance USD-M signed ZIP source first 4H 3-candle IMB touch.

No POI author golden, entry, VC, STOP/TP or fills. Reuses C08 lineage.
"""
import json,sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ("tests","d05","tools"):
    sys.path.insert(0,str(ROOT/name))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c46_original_4h_classic_imb_first_contact import (
    inspect_original_4h_imb_source)
PIN=ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
CUT=OCT_START+DAY+3*THREE

def run(out=None):
    markets=[]
    for sym in sorted(SYMS):
        old={tf:tuple(load_original(sym,tf,part,at)[0]
             for part,at in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htfs=extended_32day_prefix(old["15m"],old["1d"],END)
        sources=tuple(native_3m(sym,part)[0] for part in PERIODS)
        full=reconcile_native_3m(sources,htfs,as_of_ms=END)
        physical=reconcile_native_3m(sources,htfs,as_of_ms=CUT)
        bounded=inspect_original_4h_imb_source(full,as_of_ms=CUT)
        short=inspect_original_4h_imb_source(physical,as_of_ms=CUT)
        assert bounded==short,"C46_FUTURE_PREFIX_NATIVE3M_LEAK"
        result=inspect_original_4h_imb_source(full,as_of_ms=END)
        assert result.original_native3m_closed==15360
        assert full.native_15m_ohlcv_equalities==3072
        assert result.orders==result.trades==()
        assert result.author_poi_goldens==0 and result.readiness=="NOT_TRADE_READY"
        assert result.first_original3m_contact_count+result.untouched_candidate_count==result.candidate_count
        for ob in result.observations:
            c=ob.candidate
            assert c.fully_known_ms%14400000==0
            assert c.source_status=="C46_NATIVE_4H_CLASSIC_IMB_GEOMETRY_ONLY"
            assert not c.author_poi_certified
            assert ob.has_complete_original3m_prefix_after_known
            assert not ob.academic_poi_test_certified and not ob.academic_volume_confirmation_certified
            assert ob.orders==ob.trades==() and ob.readiness=="NOT_TRADE_READY"
            if ob.first_contact_closed_known_ms is not None:
                assert ob.first_contact_closed_known_ms>c.fully_known_ms
                assert ob.first_contact_bar_start_ms>=c.fully_known_ms
                assert ob.first_contact_original3m_id
            else:
                assert ob.first_contact_original3m_id is None
        markets.append({"symbol":sym,"source_only_4h_classic_imb_first_contact":asdict(result),
            "original_native15m_decimal_equalities":full.native_15m_ohlcv_equalities,
            "original_4h_prefix_physically_cut_equal":True,
            "author_poi_goldens":0,"orders":0,"trades":0,"readiness":"NOT_TRADE_READY"})
        print("C46_ORIGINAL_SOURCE",sym,"4H classic IMB",result.candidate_count,
            "first contact",result.first_original3m_contact_count,flush=True)
    doc={
        "schema":"EMBER_C46_ORIGINAL_USDM_4H_SOURCE_CLASSIC_IMB_FIRST_3M_CONTACT_V1",
        "original_binance_USDM_zip":45,
        "original_native3m_closed":sum(x["source_only_4h_classic_imb_first_contact"]["original_native3m_closed"]
             for x in markets),
        "native15m_decimal_equalities":sum(x["original_native15m_decimal_equalities"] for x in markets),
        "source_candidate_4h_IMB_count":sum(x["source_only_4h_classic_imb_first_contact"]["candidate_count"] for x in markets),
        "first_observed_source_3m_contact_count":sum(x["source_only_4h_classic_imb_first_contact"]["first_original3m_contact_count"] for x in markets),
        "source_no_contact_count":sum(x["source_only_4h_classic_imb_first_contact"]["untouched_candidate_count"] for x in markets),
        "original_market_count":len(markets),
        "author_course_4h_poi_goldens":0,"author_first_test_goldens":0,
        "orders":0,"trades":0,"readiness":"NOT_TRADE_READY",
        "limitations":"Original 4H 3-candle wick gap is source-derived classic IMB geometry only. Course typed POI needs context/first valid test/VC/StrongHL and FTA; first native3m wick intersection is NOT author-labeled test. No OOS, orders, fills, PnL.",
        "markets":markets}
    assert doc["original_native3m_closed"]==76800
    assert doc["native15m_decimal_equalities"]==15360
    assert doc["source_candidate_4h_IMB_count"]==(doc["first_observed_source_3m_contact_count"]+
                                                   doc["source_no_contact_count"])
    if out:
        p=Path(out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(doc,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
    if PIN.exists():
        assert json.loads(PIN.read_text(encoding="utf8"))==json.loads(json.dumps(doc,sort_keys=True)), "C46_ORIGINAL_SOURCE_JSON_DRIFT"
    print(json.dumps({"candidate":doc["source_candidate_4h_IMB_count"],
            "first_observed":doc["first_observed_source_3m_contact_count"],
            "untouched":doc["source_no_contact_count"],"trade":0},sort_keys=True),flush=True)
    return doc

if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
