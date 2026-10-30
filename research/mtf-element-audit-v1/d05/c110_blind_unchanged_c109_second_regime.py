#!/usr/bin/env python3
"""C110 blind second historical market regime of exactly unchanged C109 core+B0.
ONLY PRECOMMITTED ORIGINAL CALENDAR changes. C109 source SHA pinned.
Original daily 3m ZIP with provider checksums; PAPER ONLY; NOT LIVE-READY.
"""
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
from pathlib import Path
import argparse,hashlib,json
import c109_simple_p4_core_vs_original_research as engine
class C110Rejected(ValueError):pass
CORE_SHA="39bf28a44cec0356b256853514c532b8f37be48f3da3477a365bd19c4add5557"
SOURCE_BEGIN=datetime(2025,11,1,tzinfo=timezone.utc)
SOURCE_END=datetime(2026,1,4,tzinfo=timezone.utc)
SOURCE_FOLD=datetime(2025,12,3,tzinfo=timezone.utc)
NEW_DAYS=tuple((SOURCE_BEGIN+timedelta(days=i)).strftime("%Y-%m-%d") for i in
                range((SOURCE_END-SOURCE_BEGIN).days))
CAL_FIELDS=("BEGIN","END","BEGIN_MS","END_MS","DAYS","WARMUP_END","LAST_ENTRY","FOLD_MS")

def source_code_verified():
    code=(Path(__file__).parent/"c109_simple_p4_core_vs_original_research.py").read_bytes()
    if hashlib.sha256(code).hexdigest()!=CORE_SHA:
        raise C110Rejected("C109_STRATEGY_SOURCE_MODIFIED_OR_RETUNED")
    engine.frozen()
    if (len(NEW_DAYS)!=64 or NEW_DAYS[0]!="2025-11-01" or NEW_DAYS[-1]!="2026-01-03"
        or len(engine.SYMBOLS)!=12):
        raise C110Rejected("CHANGED_2025_DEC_SOURCE_SPEC")
    return True

@contextmanager
def use_frozen_second_regime():
    source_code_verified()
    old={name:getattr(engine,name) for name in CAL_FIELDS}
    try:
        engine.BEGIN=SOURCE_BEGIN
        engine.END=SOURCE_END
        engine.BEGIN_MS=int(SOURCE_BEGIN.timestamp()*1000)
        engine.END_MS=int(SOURCE_END.timestamp()*1000)
        engine.DAYS=NEW_DAYS
        engine.WARMUP_END=engine.BEGIN_MS+7*engine.DAY_MS
        engine.LAST_ENTRY=engine.END_MS-48*engine.p4.H
        engine.FOLD_MS=int(SOURCE_FOLD.timestamp()*1000)
        if (len(engine.DAYS)!=64 or engine.ZIPS!=768 or
            engine.BARS_PER_SYMBOL!=30720 or
            engine.FOLD_MS<=engine.WARMUP_END or
            engine.FOLD_MS>=engine.LAST_ENTRY):
            raise C110Rejected("CLOCK_SCOPE_INVALID")
        yield
    finally:
        for name,val in old.items():
            setattr(engine,name,val)

def run():
    with use_frozen_second_regime():
        market,manifest=engine.provider_3m()
        out=engine.analyze(market,manifest)
    # source-only metadata; all strategy decisions and score returned untouched
    out["schema"]="C110_UNMODIFIED_C109_B0_B1_SECOND_HISTORICAL_MARKET_REGIME"
    out["precommit"]="cycles/B1_C110_PRECOMMIT_BLIND_SECOND_REGIME_UNCHANGED_C109_CORE_RU.md"
    out["c109_original_strategy_sha256"]=CORE_SHA
    out["second_regime_unchanged_strategy"]=True
    out["can_approve_live"]=False
    out["historical_but_not_prospective_future_oos"]=True
    if (out["begin_utc"]!=SOURCE_BEGIN.strftime("%Y-%m-%d") or
        out["end_exclusive_utc"]!=SOURCE_END.strftime("%Y-%m-%d") or
        out["native3m_bars"]!=368640 or out["source_zip_count"]!=768):
        raise C110Rejected("UNEXPECTED_SECOND_REGIME_ORIGINAL_SOURCE")
    if out["orders"] or out["fills"] or out["live_trades"]:
        raise C110Rejected("PAPER_SCOPE_VIOLATED")
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    out=run()
    raw=(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(raw)
    print(json.dumps({
       "zips":out["source_zip_count"],"bars":out["native3m_bars"],
       "scores":{arm:{"n":z["scores"]["25"]["n"],
                       "netR25":z["scores"]["25"]["sum_r"],
                       "pf25":z["scores"]["25"]["pf"],
                       "netR40":z["scores"]["40"]["sum_r"],
                       "pf40":z["scores"]["40"]["pf"],
                       "DD25":z["scores"]["25"]["dd_1pct_risk_pct"],
                       "earlyR25":z["folds"]["early"]["25"]["sum_r"],
                       "lateR25":z["folds"]["late"]["25"]["sum_r"],
                       "admission":z["admission"]}
                 for arm,z in out["arms"].items()},
       "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()},
       ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
