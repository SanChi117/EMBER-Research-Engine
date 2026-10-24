#!/usr/bin/env python3
"""C49 original 45 USD-M ZIP first later 3m CLOSE vs 4H 3-bar IMB source.

Outcomes are source observations NOT author Volume Confirmation/trading wins.
"""
import sys,json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for v in ("tests","d05","tools"):sys.path.insert(0,str(ROOT/v))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END,OCT_START,DAY
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS,THREE
from c49_original3m_post_contact_directional_close import (
    inspect_original_source_4h_contact_directional_close,HORIZONS)
PIN=ROOT/"evidence/c49/C49_ORIGINAL_45ZIP_4H_CONTACT_FIRST_LATER_3M_CLOSE.json"
C46=ROOT/"evidence/c46/C46_ORIGINAL_4H_CLASSIC_IMB_FIRST_NATIVE3M_CONTACT_45ZIP.json"
CUT=OCT_START+DAY+3*THREE

def classify_result(review,parent):
    assert review.original_4h_source_candidates==parent["candidate_count"]
    assert review.native3m_first_contact_count==parent["first_original3m_contact_count"]
    assert len(review.observations)==len(parent["observations"])
    states={k:Counter() for k,_ in HORIZONS}
    for o,previous in zip(review.observations,parent["observations"]):
        previous_c=previous["candidate"]
        assert o.original_4h_zone_side==previous_c["side"]
        assert o.original_4h_zone_fully_known_ms==previous_c["fully_known_ms"]
        assert o.source_original3m_first_contact_id==previous["first_contact_original3m_id"]
        assert o.source_original3m_first_contact_closed_ms==previous["first_contact_closed_known_ms"]
        assert o.academic_valid_first_test==o.academic_valid_reaction==False
        assert o.trades==o.orders==() and o.readiness=="NOT_TRADE_READY"
        for decision,(name,window) in zip(o.window_observations,HORIZONS):
            assert decision.horizon_id==name and decision.horizon_ms==window
            states[name][decision.status]+=1
            assert decision.readiness=="NOT_TRADE_READY" and decision.orders==decision.trades==()
            assert decision.author_reaction_certified==decision.author_volume_confirmation_certified==False
            if decision.first_later_event_original3m_id is not None:
                assert o.source_original3m_first_contact_closed_ms is not None
                assert decision.first_later_event_close_known_ms>o.source_original3m_first_contact_closed_ms
                assert decision.first_later_event_close_known_ms<=o.source_original3m_first_contact_closed_ms+window
                assert decision.first_later_event_close_known_ms<=review.as_of_ms
                assert decision.favorable_3m_close!=decision.adverse_3m_close
            else:
                assert decision.first_later_event_close_known_ms is None and decision.first_later_event_close_price is None
                assert not decision.favorable_3m_close and not decision.adverse_3m_close
    assert review.course_reaction_goldens==review.course_volume_confirmation_goldens==0
    assert review.trades==review.orders==() and review.readiness=="NOT_TRADE_READY"
    for name,_ in HORIZONS:assert sum(states[name].values())==review.original_4h_source_candidates
    return states

def run(out=None):
    prev=json.loads(C46.read_text(encoding="utf8"))
    assert prev["source_candidate_4h_IMB_count"]==153
    assert prev["first_observed_source_3m_contact_count"]==132
    expected={z["symbol"]:z["source_only_4h_classic_imb_first_contact"] for z in prev["markets"]}
    markets=[]
    aggregate={name:Counter() for name,_ in HORIZONS}
    for sym in sorted(SYMS):
        old={tf:tuple(load_original(sym,tf,period,begin)[0]
             for period,begin in zip(DATES,STARTS)) for tf in ("15m","1d")}
        htf=extended_32day_prefix(old["15m"],old["1d"],END)
        sources=tuple(native_3m(sym,period)[0] for period in PERIODS)
        whole=reconcile_native_3m(sources,htf,as_of_ms=END)
        cut=reconcile_native_3m(sources,htf,as_of_ms=CUT)
        prefix_a=inspect_original_source_4h_contact_directional_close(whole,as_of_ms=CUT)
        prefix_b=inspect_original_source_4h_contact_directional_close(cut,as_of_ms=CUT)
        assert prefix_a==prefix_b,"C49_FUTURE_3M_SOURCE_SUFFIX_LEAK"
        r=inspect_original_source_4h_contact_directional_close(whole,as_of_ms=END)
        assert whole.native_15m_ohlcv_equalities==3072 and r.original_native3m_closed==15360
        state=classify_result(r,expected[sym])
        for name,counts in state.items():aggregate[name].update(counts)
        markets.append({"symbol":sym,"source_review":asdict(r),
            "original_native15m_exact":whole.native_15m_ohlcv_equalities,
            "original_fully_cut_asof_equals_full_source_prefix":True,
            "author_goldens":0,"orders":0,"trades":0,"readiness":"NOT_TRADE_READY",
            "source_state_counts":{k:dict(sorted(v.items())) for k,v in sorted(state.items())}})
        print("C49_ORIGINAL",sym,"contacts",r.native3m_first_contact_count,
            "source outcomes",[[name,v["FIRST_LATER_FAVORABLE_3M_CLOSE"],v["FIRST_LATER_ADVERSE_3M_CLOSE"]]
             for name,v in state.items()],flush=True)
    counts={name:dict(sorted(v.items())) for name,v in sorted(aggregate.items())}
    assert all(sum(v.values())==153 for v in counts.values())
    doc={"schema":"EMBER_C49_ORIGINAL_45ZIP_FIRST_POST_CONTACT_SOURCE_3M_DIRECTIONAL_CLOSE_V1",
        "original_USDM_45ZIP_source":45,
        "original_native3m_closed":sum(x["source_review"]["original_native3m_closed"] for x in markets),
        "original_native15m_exact":sum(x["original_native15m_exact"] for x in markets),
        "original_C46_4H_source_candidates":sum(x["source_review"]["original_4h_source_candidates"] for x in markets),
        "original_C46_native3m_first_contacts":sum(x["source_review"]["native3m_first_contact_count"] for x in markets),
        "preregistered_horizon_ids":[name for name,_ in HORIZONS],
        "source_horizon_state_counts":counts,
        "market_count":len(markets),
        "academic_author_verified_reactions":0,
        "academic_author_verified_1h_volume_confirmations":0,
        "original_author_chart_trade_goldens":0,
        "orders":0,"trades":0,"readiness":"NOT_TRADE_READY",
        "limits":"First strictly LATER fully closed source3m candle close beyond technical 4H IMB wick gap, not the same first-contact candle; favorable/adverse source observation is NOT an entry, STOP/TP, author reaction, 1H VC, return or profit. Right-censored incomplete 1h/4h/12h horizons are separate from negative source observations. 3m OHLC wicks cannot sequence fills.",
        "markets":markets}
    assert doc["original_native3m_closed"]==76800
    assert doc["original_native15m_exact"]==15360
    assert doc["original_C46_4H_source_candidates"]==153
    assert doc["original_C46_native3m_first_contacts"]==132
    if out:
        f=Path(out);f.parent.mkdir(parents=True,exist_ok=True)
        f.write_text(json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if PIN.exists():
        assert json.loads(PIN.read_text(encoding="utf8"))==json.loads(json.dumps(doc,sort_keys=True)),"C49_FROZEN_FULL_SOURCE_DRIFT"
    print(json.dumps({"counts":counts,"orders":0,"trades":0},sort_keys=True),flush=True)
    return doc
if __name__=="__main__":run(sys.argv[1] if len(sys.argv)>1 else None)
