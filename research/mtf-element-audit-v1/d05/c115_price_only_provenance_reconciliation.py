#!/usr/bin/env python3
"""C115 price-source-only policy, C114 economic engine byte-unchanged.

The C114 strict volume-source-block remains immutable in original branch.
This is NOT a new/ex-post optimized signal. PAPER research, NOT pristine blind.
"""
import argparse
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path

import c114_independent_poi_native5m_choch_research as frozen

SOURCE_PRECOMMIT = "cycles/B1_C115_PRECOMMIT_PRICE_ONLY_SOURCE_RECONCILIATION_RU.md"
class C115Error(ValueError):pass

def independent_ohlc_price_parity(original3m,original5m):
    if not original3m or not original5m or len(original3m)//5!=len(original5m)//3:
        raise C115Error("SOURCE_NATIVE_3M5M_COUNT_MISMATCH")
    count=0
    maxrel=D(0)
    maxabs=D(0)
    over_bp=0
    for j in range(len(original3m)//5):
        a=original3m[5*j:5*j+5]
        b=original5m[3*j:3*j+3]
        p3=(a[0].start_ms,a[-1].known_ms,a[0].open,
            max(x.high for x in a),min(x.low for x in a),a[-1].close)
        p5=(b[0].open_ms,b[-1].close_ms,b[0].o,
            max(x.h for x in b),min(x.l for x in b),b[-1].c)
        if p3!=p5:
            raise C115Error("EXACT_ORIGINAL_3M_5M_15M_PRICE_DISAGREEMENT_"+str(j)+
                            "_3M="+str(p3)+"_5M="+str(p5))
        q3=sum((x.volume for x in a),D(0))
        q5=sum((x.volume for x in b),D(0))
        if q3!=q5:
            count+=1
            diff=abs(q3-q5)
            maxabs=max(maxabs,diff)
            relative=diff/max(q3,q5) if max(q3,q5)>0 else D(0)
            maxrel=max(maxrel,relative)
            if relative>D("0.0001"):over_bp+=1
    return {"aligned15m":len(original3m)//5,
            "strict_ohlc_price_clock_parity":True,
            "volume_nonidentical_buckets":count,
            "volume_buckets_drift_gt_1bp":over_bp,
            "max_absolute_15m_volume_drift":str(maxabs),
            "max_relative_15m_volume_drift":str(maxrel),
            "volume_is_diagnostic_only":True,
            "same_original_archives_as_C114":True,
            "use_in_entry_or_exit":False}

def run():
    frozen.frozen()
    old=frozen.independent_15m_parity
    try:
        frozen.independent_15m_parity=independent_ohlc_price_parity
        z=frozen.run()
    finally:
        frozen.independent_15m_parity=old
    z["schema"]="EMBER_C115_PRICE_ONLY_SOURCE_QUALIFICATION_OF_FROZEN_C114_HYPOTHESIS"
    z["precommit"]=SOURCE_PRECOMMIT
    z["inherited_economic_precommit"]=frozen.PRECOMMIT
    z["C114_1bp_volume_source_trial_status"]="SOURCE_BLOCKED_A177_NO_ECONOMIC_OUTCOME"
    z["economic_parameters_changed"]=False
    z["price_ohlc_15m_strict"]=True
    z["volume_trading_factor"]=False
    z["source_format_amendment_after_archive_volume_exposure"]=True
    z["true_prospective_oos"]=False
    z["pristine_blind_economic_oos"]=False
    z["live_approved"]=False
    return z

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    z=run()
    if (z["original_3m_zip_total"]!=1344 or z["original_5m_zip_total"]!=1344 or
        z["original_3m_bar_total"]!=645120 or z["original_5m_bar_total"]!=387072):
        raise C115Error("INCOMPLETE_PRECOMMITTED_SOURCE")
    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    receipts={}
    for name,x in z["windows"].items():
        filename=f"C115_{name}_ORIGINAL_NATIVE3M5M_MATCHED_T_CONTROL.json"
        raw=(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
        (out/filename).write_bytes(raw)
        receipts[name]={"filename":filename,"sha256":sha256(raw).hexdigest(),
                        "bytes":len(raw),"scores":x["scores"],"cohort":x["cohort"],
                        "bootstrap":x["bootstrap"],"admission":x["admission"],
                        "source_parity":x["source_15m_cross_archive_parity"],
                        "portfolio":x["portfolio"]}
    summary={k:v for k,v in z.items() if k!="windows"}
    summary["window_receipts"]=receipts
    raw=(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    (out/"C115_SUMMARY.json").write_bytes(raw)
    print(json.dumps({"manifest_sha256":sha256(raw).hexdigest(),
                      "source_zips":2688,"witnesses":receipts,
                      "economic_pass":summary["historical_screen_pass_both_windows"],
                      "LIVE":False},ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
