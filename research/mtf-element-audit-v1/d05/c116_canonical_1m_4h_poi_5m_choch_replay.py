#!/usr/bin/env python3
"""C116 official native1m canonical source -> deterministic 3m+5m price-only study.

C114 economic code and windows frozen; original 3m/5m ZIPs NOT used.
All results HISTORICAL PAPER only and economically blind but source-exposed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path

import c114_independent_poi_native5m_choch_research as economic
import c116_original_1m_source_and_exact_resampler as source

class C116Error(ValueError):pass
PRECOMMIT="cycles/B1_C116_PRECOMMIT_SINGLE_ORIGINAL_1M_CANONICAL_SOURCE_RU.md"

def canonical_original_1m(window):
    _,begin,end=window
    symbols=economic.SYMBOLS
    days=economic.dates(begin,end)
    todo=[(sym,day) for sym in symbols for day in days]
    def task(k):
        sym,day=k
        xs,receipt=source.daily(sym,day)
        if len(xs)!=1440 or receipt["source_interval"]!="ORIGINAL_NATIVE_1M":
            raise C116Error("REQUIRES_ORIGINAL_1440_PER_DAY")
        d3,d5=source.resample(xs)
        if len(d3)!=480 or len(d5)!=288:
            raise C116Error("DERIVED_CLOCK_FAILURE")
        return sym,day,d3,d5,receipt
    with ThreadPoolExecutor(max_workers=12) as ex:
        fetched=list(ex.map(task,todo))
    markets3={s:[] for s in symbols}
    markets5={s:[] for s in symbols}
    original_receipts=[]
    for sym,day,a,b,raw in fetched:
        if (markets3[sym] and markets3[sym][-1].known_ms!=a[0].start_ms or
            markets5[sym] and markets5[sym][-1].close_ms!=b[0].open_ms):
            raise C116Error("MISSING_CANONICAL_ORIGINAL_DAY")
        markets3[sym].extend(a)
        markets5[sym].extend(b)
        original_receipts.append(raw)
    if (len(original_receipts)!=672 or
        len({(r["symbol"],r["date"]) for r in original_receipts})!=672):
        raise C116Error("MISSING_OR_DUPLICATE_672_1M_ZIP")
    start=int(begin.timestamp()*1000)
    stop=int(end.timestamp()*1000)
    parities={}
    for s in symbols:
        a,b=tuple(markets3[s]),tuple(markets5[s])
        if not(len(a)==26880 and len(b)==16128 and
               a[0].start_ms==b[0].open_ms==start and
               a[-1].known_ms==b[-1].close_ms==stop):
            raise C116Error("FULL_CANONICAL_56D_SOURCE_NOT_PRESENT")
        parities[s]=source.verify_joint_15m(a,b)
    # Same original 1m SHA receipt is referenced in TWO derived families.
    # All labels explicitly say derived; no independent original3m/5m claim.
    pseudo3=[]
    pseudo5=[]
    for q in original_receipts:
        common={"symbol":q["symbol"],"date":q["date"],
                "source_original_native_1m_zip_sha256":q["zip_sha256"],
                "source_original_native_1m_csv_sha256":q["csv_sha256"],
                "source_original_native_1m_url":q["url"],
                "independent_original_3m_or_5m_archive_used":False}
        pseudo3.append({**common,"timeframe":"DERIVED_3M_FROM_ORIGINAL_1M",
                        "bars":480,"source":"SINGLE_ORIGINAL_NATIVE_1M"})
        pseudo5.append({**common,"timeframe":"DERIVED_5M_FROM_ORIGINAL_1M",
                        "bars":288,"source":"SINGLE_ORIGINAL_NATIVE_1M"})
    return ({s:tuple(markets3[s]) for s in symbols},
            {s:tuple(markets5[s]) for s in symbols},
            pseudo3,pseudo5,parities)

def run():
    economic.frozen()
    callback=economic.download
    try:
        economic.download=canonical_original_1m
        obj=economic.run()
    finally:
        economic.download=callback
    obj["schema"]="EMBER_C116_CANONICAL_ORIGINAL_NATIVE1M_DERIVED3M5M_STRUCTURAL_REACTION_TEST"
    obj["precommit"]=PRECOMMIT
    obj["inherited_c114_economic_precommit"]=economic.PRECOMMIT
    obj["source_count_original_native1m_zip"]=1344
    obj["source_raw_native1m_bars"]=1935360
    obj["source_3m_kind"]="DERIVED_FROM_ORIGINAL_NATIVE_1M"
    obj["source_5m_kind"]="DERIVED_FROM_ORIGINAL_NATIVE_1M"
    obj["source_3m_5m_independent_original_archives"]=False
    obj["original_3m_zip_total"]=0
    obj["original_5m_zip_total"]=0
    obj["derived_3m_bars_total"]=obj.pop("original_3m_bar_total")
    obj["derived_5m_bars_total"]=obj.pop("original_5m_bar_total")
    obj["source_original_native1m_minutes_replay"]=True
    obj["revisits_source_exposed_C114_C115_windows"]=True
    obj["true_prospective_oos"]=False
    obj["economic_parameters_changed"]=False
    obj["live_approved"]=False
    obj["paper_only"]=True
    for w in obj["windows"].values():
        w["canonical_native1m_zip_receipts"]=list({
           (r["symbol"],r["date"]):
                {"symbol":r["symbol"],"date":r["date"],
                 "original_native1m_zip_sha256":r["source_original_native_1m_zip_sha256"],
                 "original_native1m_csv_sha256":r["source_original_native_1m_csv_sha256"],
                 "original_native1m_url":r["source_original_native_1m_url"],
                 "provider_checksum_verified":True}
           for r in w["source_receipts_3m"]}.values())
        w["derived_3m_daily_receipt_count"]=w.pop("source_3m_zips")
        w["derived_5m_daily_receipt_count"]=w.pop("source_5m_zips")
        w["derived_3m_bars"]=w.pop("original3m_bars")
        w["derived_5m_bars"]=w.pop("original5m_bars")
        w["derived_3m_provenance"]=w.pop("source_receipts_3m")
        w["derived_5m_provenance"]=w.pop("source_receipts_5m")
        w["intra_canonical_1m_3m5m_parity"]=w.pop("source_15m_cross_archive_parity")
        for p in w["per_symbol"].values():
            p["derived_3m_bars"]=p.pop("source_bars_native3m")
            p["derived_5m_bars"]=p.pop("source_bars_native5m")
            for e in p["events"]:
                if e["trade"] is not None:
                    e["trade"]["source_tf"]="DERIVED_3M_FROM_ORIGINAL_NATIVE_1M"
                    e["trade"]["route"]="C116_4H_FVG_TOUCH_NATIVE1M_DERIVED5M_CHOCH"
                    e["trade"]["source_original_native1m"]=True
                e["source_tf_5m"]="DERIVED_FROM_ORIGINAL_NATIVE_1M"
    return obj

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    x=run()
    if (x["source_count_original_native1m_zip"]!=1344 or
        x["source_raw_native1m_bars"]!=1935360 or
        x["derived_3m_bars_total"]!=645120 or
        x["derived_5m_bars_total"]!=387072):
        raise C116Error("CANONICAL_PROVIDER_COUNT_DRIFT")
    dest=a.output_dir;dest.mkdir(parents=True,exist_ok=True)
    receipts={}
    for name,w in x["windows"].items():
        fn=f"C116_{name}_ORIGINAL_1M_CANONICAL_AND_MATCHED_EVENTS.json"
        blob=(json.dumps(w,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
        (dest/fn).write_bytes(blob)
        receipts[name]={"filename":fn,"sha256":sha256(blob).hexdigest(),
                        "bytes":len(blob),"source_original_native1m_zip_count":len(w["canonical_native1m_zip_receipts"]),
                        "cohort":w["cohort"],"scores":w["scores"],
                        "admission":w["admission"],"bootstrap":w["bootstrap"],
                        "portfolio":w["portfolio"],
                        "intra_canonical_parity":w["intra_canonical_1m_3m5m_parity"]}
    manifest={k:v for k,v in x.items() if k!="windows"}
    manifest["window_receipts"]=receipts
    blob=(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    (dest/"C116_SUMMARY.json").write_bytes(blob)
    print(json.dumps({"summary_sha256":sha256(blob).hexdigest(),
                      "original_1m_zip_count":1344,
                      "historical_two_window_screen_pass":manifest["historical_screen_pass_both_windows"],
                      "witnesses":receipts,"live_approved":False},ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
