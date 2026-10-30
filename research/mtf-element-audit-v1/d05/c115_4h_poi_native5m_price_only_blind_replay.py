#!/usr/bin/env python3
"""C115 new original 2023 OOS C114 economic replication, SOURCE-ONLY amendment.

No modifications of C114 entry, stop, target, risk, matching, or statistics.
Volume disagreements recorded not turned into price-only filters or trades.
"""
import argparse,hashlib,json
from contextlib import contextmanager
from datetime import datetime,timezone
from decimal import Decimal as D
from pathlib import Path

import c114_independent_poi_native5m_choch_research as original

class C115Rejected(ValueError):pass
SOURCE_FILE=Path(original.__file__).resolve()
FROZEN_C114_SHA="36d677166f4091f2ce66084dfb75f2407c72cbf735483cb3ee584a687ba41e6f"
PRECOMMIT="cycles/B1_C115_PRECOMMIT_FROZEN_4H_POI_5M_CHOCH_PRICE_ONLY_SOURCE_RU.md"
WINDOWS=(
    ("WIN_A",datetime(2023,9,1,tzinfo=timezone.utc),
              datetime(2023,10,27,tzinfo=timezone.utc)),
    ("WIN_B",datetime(2023,11,1,tzinfo=timezone.utc),
              datetime(2023,12,27,tzinfo=timezone.utc))
)
EXPECTED_ZIPS=2688
EXPECTED_3M=645120
EXPECTED_5M=387072

def frozen():
    if hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest()!=FROZEN_C114_SHA:
        raise C115Rejected("ORIGINAL_C114_ECONOMIC_ENGINE_TAMPERED")
    if len(WINDOWS)!=2 or any((end-begin).days!=56 for _,begin,end in WINDOWS):
        raise C115Rejected("C115_2023_TWO_FROZEN_56_DAY_WINDOWS_MUTATED")
    if (original.REPS!=2000 or original.BOOT_SEED!=11420261030 or
        original.LANDMARK!=6*original.H or
        original.SYMBOLS!=("BNBUSDT","XLMUSDT","HBARUSDT","INJUSDT",
                          "OPUSDT","ALGOUSDT","CHZUSDT","ICPUSDT",
                          "SEIUSDT","PENDLEUSDT","LINKUSDT","UNIUSDT")):
        raise C115Rejected("C114_CONTROL_AND_HYPOTHESIS_CHANGED")
    assert original.EXPECTED_3M_ZIPS==1344 and original.EXPECTED_5M_ZIPS==1344
    original.frozen()
    return True

def price_only_causal_15m_parity(three,five):
    """Strict close-aligned ORIGINAL 3m/5m candles; volume never a trade gate.

    Every OHLC disagreement blocks source. Every volume discrepancy preserved
    with severity, even though no model formation uses volume.
    """
    if (not three or not five or len(three)%5 or len(five)%3 or
        len(three)//5!=len(five)//3):
        raise C115Rejected("NATIVE_3M5M_CLOCK_LENGTH_MISMATCH")
    bad_v=0
    max_rel=D(0)
    total_v3=D(0)
    total_v5=D(0)
    examples=[]
    total=len(three)//5
    for j in range(total):
        a=three[j*5:j*5+5]
        b=five[j*3:j*3+3]
        # Actual provider 15min OHLC / UTC close signature. No price tolerance.
        three_ohlc=(a[0].start_ms,a[-1].known_ms,a[0].open,
                    max(q.high for q in a),min(q.low for q in a),a[-1].close)
        five_ohlc=(b[0].open_ms,b[-1].close_ms,b[0].o,
                   max(q.h for q in b),min(q.l for q in b),b[-1].c)
        if three_ohlc!=five_ohlc:
            raise C115Rejected("STRICT_15M_OHLC_MISMATCH_" + str(j)+
                               "_3M="+str(three_ohlc)+"_5M="+str(five_ohlc))
        if any(x.known_ms!=y.start_ms for x,y in zip(a,a[1:])):
            raise C115Rejected("NATIVE_3M_INTRA_BUCKET_GAP")
        if any(x.close_ms!=y.open_ms for x,y in zip(b,b[1:])):
            raise C115Rejected("NATIVE_5M_INTRA_BUCKET_GAP")
        v3=sum((q.volume for q in a),D(0))
        v5=sum((q.volume for q in b),D(0))
        if (not v3.is_finite() or not v5.is_finite() or v3<0 or v5<0):
            raise C115Rejected("INVALID_PRICE_ONLY_SOURCE_VOLUME_FIELD")
        total_v3+=v3
        total_v5+=v5
        if v3!=v5:
            bad_v+=1
            pct=abs(v3-v5)/max(v3,v5) if max(v3,v5)>0 else D(0)
            max_rel=max(max_rel,pct)
            if len(examples)<12:
                examples.append({"bucket":j,"start_ms":a[0].start_ms,
                                 "3m_base_volume":str(v3),
                                 "5m_base_volume":str(v5),
                                 "relative_spread":str(pct)})
    return {
        "aligned15m":total,
        "strict_ohlc_price_clock_parity":True,
        "price_tolerance":"EXACT",
        "volume_is_signal":False,"volume_is_source_gate":False,
        "volume_mismatch_15m_bucket_count":bad_v,
        "max_relative_15m_volume_drift":str(max_rel),
        "total_3m_volume_sum":str(total_v3),
        "total_5m_volume_sum":str(total_v5),
        "volume_discrepancy_samples":examples,
    }


def pure_trade_provenance_bridge(three,five,symbol,window):
    """Repair C114 event->trade attribution only; preserve ALL trade economics.

    The original C114 per_symbol emitted trades without symbol/parent_id;
    C114.evaluate portfolio sort expects both and raises KeyError. Attach
    the already stored event identifiers as metadata. Never add/remove events,
    modify trade direction, price, exit time, costs, matching, or TP/SL.
    """
    result=_ORIGINAL_PER_SYMBOL(three,five,symbol,window)
    for event in result["events"]:
        trade=event.get("trade")
        if trade is None:
            continue
        if "symbol" in trade and trade["symbol"]!=event["symbol"]:
            raise C115Rejected("CONFLICTING_TRADE_SYMBOL_PROVENANCE")
        if "parent_id" in trade and trade["parent_id"]!=event["parent_id"]:
            raise C115Rejected("CONFLICTING_4H_PARENT_PROVENANCE")
        trade["symbol"]=event["symbol"]
        trade["parent_id"]=event["parent_id"]
    return result

_ORIGINAL_PER_SYMBOL=original.per_symbol

@contextmanager
def frozen_source_scope():
    frozen()
    old_windows=original.WINDOWS
    old_parity=original.independent_15m_parity
    old_precommit=original.PRECOMMIT
    old_per_symbol=original.per_symbol
    original.WINDOWS=WINDOWS
    original.independent_15m_parity=price_only_causal_15m_parity
    original.PRECOMMIT=PRECOMMIT
    original.per_symbol=pure_trade_provenance_bridge
    try:
        yield
    finally:
        original.WINDOWS=old_windows
        original.independent_15m_parity=old_parity
        original.PRECOMMIT=old_precommit
        original.per_symbol=old_per_symbol

def run():
    with frozen_source_scope():
        answer=original.run()
    answer["schema"]="C115_ORIGINAL_C114_PAPER_FIRST_TOUCH_4H_VS_5M_CHOCH_PRICE_ONLY_SOURCE"
    answer["original_c114_engine_sha256"]=FROZEN_C114_SHA
    answer["original_c114_hypothesis_parameters_unmodified"]=True
    answer["source_gate_strict_price_only"]=True
    answer["precommit"]=PRECOMMIT
    answer["no_live_trades"]=True
    answer["non_economic_event_attribution_bridge"]=True
    if (answer["original_3m_zip_total"]+answer["original_5m_zip_total"]!=EXPECTED_ZIPS or
        answer["original_3m_bar_total"]!=EXPECTED_3M or
        answer["original_5m_bar_total"]!=EXPECTED_5M):
        raise C115Rejected("INCOMPLETE_ORIGINAL_2023_BOTH_WINDOWS")
    return answer

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    folder=args.output_dir
    try:
        result=run()
    except Exception as ex:
        if not isinstance(ex,(C115Rejected,original.C114Error,
                               original.provider3.C104SourceError,
                               original.provider5.C114SourceError)):
            raise
        folder.mkdir(parents=True,exist_ok=True)
        evidence={"schema":"C115_PRICE_ONLY_SOURCE_BLOCK_OR_ENGINEERING_REJECT",
                  "error_class":type(ex).__name__,"reason":str(ex),
                  "frozen_windows":[[name,a.isoformat(),b.isoformat()] for name,a,b in WINDOWS],
                  "source_gate":"EXACT_NATIVE3M_NATIVE5M_OHLC",
                  "no_economic_results":True,"paper_only":True,"live_approved":False}
        (folder/"C115_SOURCE_BLOCKED.json").write_text(
            json.dumps(evidence,sort_keys=True,indent=2)+"\n")
        raise
    folder.mkdir(parents=True,exist_ok=True)
    receipts={}
    for name,payload in result["windows"].items():
        fn=f"C115_{name}_ORIGINAL_3M5M_EVENT_AND_PAIR_LEDGER.json"
        raw=(json.dumps(payload,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode()
        (folder/fn).write_bytes(raw)
        receipts[name]={"filename":fn,"sha256":hashlib.sha256(raw).hexdigest(),
                        "bytes":len(raw),"cohort":payload["cohort"],
                        "admission":payload["admission"],"scores":payload["scores"],
                        "portfolio":payload["portfolio"],"bootstrap":payload["bootstrap"]}
    summary={k:v for k,v in result.items() if k!="windows"}
    summary["window_receipts"]=receipts
    raw=(json.dumps(summary,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode()
    (folder/"C115_SUMMARY.json").write_bytes(raw)
    print(json.dumps({"source_zip_count":EXPECTED_ZIPS,"original_3m_bars":EXPECTED_3M,
        "original_5m_bars":EXPECTED_5M,
        "economic_historical_screen_pass_both":result["historical_screen_pass_both_windows"],
        "evidence":receipts,"summary_sha256":hashlib.sha256(raw).hexdigest(),
        "paper_only":True,"live_approved":False},sort_keys=True,ensure_ascii=False))
if __name__=="__main__":
    main()
