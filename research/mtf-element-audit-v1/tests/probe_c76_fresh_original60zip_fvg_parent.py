#!/usr/bin/env python3
"""C76: FRESH, original-source, complete 60 ZIP replay; source-only adaptation.

Five crypto markets BTC ETH SOL XRP BCH * monthly Sep2026 + Oct1/2 daily:
15 original native3m, 15 original native5m, 15 native15m, 15 native1d.
C08 signed-by-same-host provider checksum + frozen receipts; native3m and
native5m exact OHLCV reconcile into original15m, which reconciles native1d.
C73 fixed 303327-byte source snapshot is cross-linked but C73's *entire*
153-case algorithm is NOT rerun here; pinned source ZIP and all source
lineage are what we independently replay. No orders or profit claims.
"""
import sys, json, hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
for folder in ("tests","d05","tools"):
    sys.path.insert(0,str(ROOT/folder))
from probe_c16_32day_native_htf_sources import load_original,SYMS,DATES,STARTS
from probe_c21_native3m_futures_32day import native_3m
from probe_c73_original60zip_new1h_poi_3m_visits_semantic_split import checked_new5m
from c16_c08_monthly_daily_htf_lineage import extended_32day_prefix,END
from c21_native3m_source_bridge import reconcile_native_3m,PERIODS
from c72_original_native5m_source_vc_after15m_gate import (
    original5m_url,parse_original5m_zip,reconcile_original5m_to_native15m)
from c75_external_imb_first_visit_lifecycle import (
    scan_native_fvg,inspect_fvg_visits)
from c76_original_crypto_fvg_1h_parent_semantic_audit import (
    summarize_c76_original_contexts)
C73_SHA="c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b"
C73=ROOT/"evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json"
C21=ROOT/"evidence/c21/C21A_NATIVE3M_C08_PARITY_RECEIPT.json"

def run(out=None):
    raw=C73.read_bytes()
    assert len(raw)==303327 and hashlib.sha256(raw).hexdigest()==C73_SHA
    frozen=json.loads(raw)
    c21=json.loads(C21.read_bytes())
    c21_by={v["symbol"]:v for v in c21["observations"]}
    parent={v["symbol"]:v for v in frozen["markets"]}
    assert set(parent)==set(SYMS)==set(c21_by)
    summaries=[]
    original_zips=Counter()
    for symbol in sorted(SYMS):
        pieces={}
        archive_receipts=[]
        for tf in ("15m","1d"):
            source=[]
            for date,start in zip(DATES,STARTS):
                a,proof=load_original(symbol,tf,date,start)
                source.append(a)
                archive_receipts.append(proof)
                original_zips[tf]+=1
            pieces[tf]=tuple(source)
        htf=extended_32day_prefix(pieces["15m"],pieces["1d"],END)
        n3_source=[]
        for period in PERIODS:
            a,proof=native_3m(symbol,period)
            target=next(z for z in c21_by[symbol]["new_original_source_zip"]
                        if z["period"]==period)
            assert target==proof,"C76_ORIGINAL3M_FROZEN_RECEIPT_DIFFERENCE"
            n3_source.append(a)
            archive_receipts.append(proof)
            original_zips["3m"]+=1
        native3=reconcile_native_3m(tuple(n3_source),htf,as_of_ms=END)
        original5=[]
        old5=parent[symbol]["original5m_archives"]
        for period in PERIODS:
            url=original5m_url(symbol,period)
            blob=checked_new5m(url,25000000)
            checksum=checked_new5m(url+".CHECKSUM",1024)
            x=parse_original5m_zip(symbol,period,blob,checksum)
            witness=next(z for z in old5 if z["period"]==period)
            assert (witness["zip_sha256"]==x.zip_sha and
                    witness["raw_csv_sha256"]==x.csv_sha and
                    witness["url"]==url),"C76_ORIGINAL5M_C73_SHA_DRIFT"
            original5.append(x)
            archive_receipts.append({"tf":"5m","period":period,
                 "zip_sha256":x.zip_sha,"raw_csv_sha256":x.csv_sha,
                 "native5m_bars":len(x.rows)})
            original_zips["5m"]+=1
        five=reconcile_original5m_to_native15m(
            tuple(original5),htf.native_15m_closed,as_of_ms=END)
        assert len(native3.original_3m_closed)==15360
        assert len(five.rows)==9216
        assert len(htf.native_15m_closed)==3072
        assert len(htf.native_1d_closed)==32
        assert native3.native_15m_ohlcv_equalities==3072
        assert five.native15m_3_to_1_decimal_equalities==3072
        streams={
            "3m":native3.original_3m_closed,
            "5m":five.rows,
            "15m":htf.native_15m_closed
        }
        fvg={tf:scan_native_fvg(rows,tf=tf,as_of_ms=END)
             for tf,rows in streams.items()}
        samples={}
        for tf, rows in streams.items():
            if fvg[tf]:
                first=fvg[tf][0]
                visit=inspect_fvg_visits(first,rows,as_of_ms=END)
                assert visit.readiness=="NOT_TRADE_READY"
                assert not any((visit.owner_first_valid_test,visit.owner_15m_trigger,
                                visit.owner_15m_vc,visit.owner_5m_vc,
                                visit.author_entry,visit.orders,visit.fills,visit.trades))
                samples[tf]={
                    "first_source_fvg_known_ms":first.known_ms,
                    "first_source_fvg_side":first.side,
                    "first_raw_source_first_bar_id":first.first_bar_id,
                    "first_raw_source_third_bar_id":first.third_bar_id,
                    "first_visit":visit.first_touch_id,
                    "separate_visits_until_first_close_through":visit.separate_visits,
                    "lifecycle":visit.state,
                    "candidate_only":True
                }
            else:
                samples[tf]={"no_source_fvg":True}
        cases=parent[symbol]["original_parent_source_cases"]
        context=summarize_c76_original_contexts(cases,fvg["15m"])
        assert context["original_c73_contexts"]==len(cases)
        assert context["author_approved"]==context["trades"]==0
        summaries.append({
            "symbol":symbol,
            "original_archives":archive_receipts,
            "original_counts":{"3m":len(streams["3m"]),
                               "5m":len(streams["5m"]),
                               "15m":len(streams["15m"]),
                               "1d":len(htf.native_1d_closed)},
            "exact_3m_to_native15m":native3.native_15m_ohlcv_equalities,
            "exact_5m_to_native15m":five.native15m_3_to_1_decimal_equalities,
            "adapted_closed_source_fvg_counts":{
                 tf:len(events) for tf,events in fvg.items()},
            "adapted_first_candidate_lifecycle_samples":samples,
            "c73_parent_poi_crosscheck":context,
            "author_verified":0,"orders":0,"fills":0,"trades":0
        })
        print("C76_FRESH_MARKET",symbol,"FVG",
              {tf:len(v) for tf,v in fvg.items()},
              "C73 parents",len(cases),flush=True)
    assert original_zips==Counter({"3m":15,"5m":15,"15m":15,"1d":15})
    assert sum(x["c73_parent_poi_crosscheck"]["original_c73_contexts"]
               for x in summaries)==153
    assert sum(x["exact_3m_to_native15m"] for x in summaries)==15360
    assert sum(x["exact_5m_to_native15m"] for x in summaries)==15360
    assert all(x["orders"]==x["fills"]==x["trades"]==0 for x in summaries)
    result={
      "schema":"EMBER_C76_REAL_ORIGINAL60ZIP_ADAPTED_FVG_1H_PARENT_REPLAY_V1",
      "market":"BINANCE_USDM_FUTURES_CRYPTO_RESEARCH_ONLY",
      "original_source_period_utc":["2026-09-01","2026-10-02"],
      "original_zip_counts":dict(sorted(original_zips.items())),
      "source_C73_frozen_sha256":C73_SHA,
      "source_C73_case_count":153,
      "fresh_full_original_60zip_source_replay":True,
      "fresh_C73_153_parent_algorithm_full_reexecution":False,
      "original_closed_bar_counts":{"native3m":76800,"native5m":46080,
             "native15m":15360,"native1d":160},
      "original_decimal_parity":{"3m_to_15m":15360,"5m_to_15m":15360},
      "markets":summaries,
      "evidence_class":"ADAPTED_HYPOTHESIS",
      "author_15m_trigger_vc_positive_verified":0,
      "author_valid_poi_first_tests_verified":0,
      "author_vc_stronghl_structural_sl_tp_verified":0,
      "source_checksum_independent_third_party_signature":False,
      "orders":0,"fills":0,"trades":0,"pnl":None,
      "readiness":"NOT_TRADE_READY"
    }
    content=json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=True)
    if out:
        dst=Path(out);dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("C76_EVIDENCE_JSON:"+content,flush=True)
    print("C76_FINAL_REPLAY_PASS 60 ORIGINAL ZIP; 153 C73 CONTEXTS; NO TRADES",
          flush=True)
    return result

if __name__=="__main__":
    run(sys.argv[1] if len(sys.argv)>1 else None)
