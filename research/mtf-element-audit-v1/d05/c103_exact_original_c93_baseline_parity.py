"""C103 INDEPENDENT forensic proof: research BASELINE == unchanged C93 source.

Temporary in-process symbol allowlist expansion ONLY to run exact original
discover() over the already frozen five new symbols. No original repo edit.
If not equivalent fail closed, so do not label transfer BASELINE exact C93.
"""
import hashlib,json
from pathlib import Path
import c93_native3m_raid_bos_route_c_research as orig
import c102_c103_native3m_new_symbol_transfer as adapted

ORIGINAL_C93_SHA="a241d8de2691bca6247afbfe5e92b0a6e7df25b10f8a4c71f340b815e515bda0"
ORIGINAL_WITNESS_SHA="e5df71e5f58c968c0d4e06cf61e56db6d3e80d1060d2cac2bf7f91b057909d92"
ROOT=Path(__file__).resolve().parents[1]
WITNESS=ROOT/"evidence/c102/C102_C103_NEW5_SYMBOL_NATIVE3M_32DAY_ORIGINAL_TRANSFER.json"
ORIGINAL_C93=ROOT/"d05/c93_native3m_raid_bos_route_c_research.py"
FIELDS=("symbol","side","route","source_tf","entry_ms","exit_ms","entry","stop",
        "target","fta","fta_confirmed_ms","derived_rr","net_r",
        "exit_reason","raid_closed_ms","raid_fractal_known_ms",
        "raid_fractal_level","bos_level","bos_confirmed_ms","bos_close_ms")

class ParityError(ValueError):pass

def signature(t):
    if not all(k in t for k in FIELDS):
        raise ParityError("BASELINE_MISSING_UNTOUCHED_FIELDS")
    return tuple((k,t[k]) for k in FIELDS)

def compare(original,experimental):
    x=sorted((signature(t) for t in original),key=repr)
    y=sorted((signature(t) for t in experimental),key=repr)
    if x!=y:
        return {"matches":False,"original_n":len(x),"experimental_n":len(y),
           "original_only":len(set(x)-set(y)),
           "experimental_only":len(set(y)-set(x)),
           "original_example":list(set(x)-set(y))[:1],
           "experimental_example":list(set(y)-set(x))[:1]}
    return {"matches":True,"original_n":len(x),"experimental_n":len(y),
        "original_only":0,"experimental_only":0}

def execute():
    if hashlib.sha256(ORIGINAL_C93.read_bytes()).hexdigest()!=ORIGINAL_C93_SHA:
        raise ParityError("FROZEN_ORIGINAL_C93_CODE_CHANGED")
    frozen=WITNESS.read_bytes()
    if hashlib.sha256(frozen).hexdigest()!=ORIGINAL_WITNESS_SHA:
        raise ParityError("C102_WITNESS_SHA_CHANGED")
    z=json.loads(frozen)
    sources,proof=adapted.download_original()
    lookup={(x["symbol"],x["date"]):x for x in z["source_manifest"]}
    if len(lookup)!=160 or len(proof)!=160:
        raise ParityError("MISSING_FROZEN_SOURCE_PROOFS")
    for receipt in proof:
        prior=lookup.get((receipt["symbol"],receipt["date"]))
        if prior!=receipt:
            raise ParityError("ORIGINAL_ZIP_CSV_SHA_MISMATCH")
    outcomes={}
    old=orig.SOURCES
    try:
        # Only the symbol whitelist is extended while invoking original
        # function; core C93 code / trade rules are exactly unchanged.
        orig.SOURCES=frozenset(old|set(adapted.SYMBOLS))
        for s in adapted.SYMBOLS:
            src=sources[s]
            baseline_orig=orig.discover(src,s)["trades"]
            baseline_exp=adapted.select_sequential(
                adapted.candidate_events(src,s)[0],"BASELINE")
            lo=adapted.BEGIN_MS+adapted.WARMUP_DAYS*adapted.DAY_MS
            hi=adapted.END_MS-adapted.EMBARGO_HOURS*3600000
            orig_eval=[t for t in baseline_orig if lo<=t["entry_ms"]<hi
                       and t["exit_ms"]<=adapted.END_MS]
            outcomes[s]=compare(orig_eval,baseline_exp)
    finally:
        orig.SOURCES=old
    return {"source_sha":ORIGINAL_WITNESS_SHA,
       "original_c93_sha":ORIGINAL_C93_SHA,
       "by_symbol":outcomes,
       "all_equal":all(x["matches"] for x in outcomes.values()),
       "total_original":sum(x["original_n"] for x in outcomes.values()),
       "total_transfer":sum(x["experimental_n"] for x in outcomes.values()),
       "no_strategy_change":True,"orders":0}

if __name__=="__main__":
    result=execute()
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,default=str))
    if not result["all_equal"]:
        raise SystemExit("ORIGINAL_C93_VS_C102_BASELINE_PARITY_REJECTED")
