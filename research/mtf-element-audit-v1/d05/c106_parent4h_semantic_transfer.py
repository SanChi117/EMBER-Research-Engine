#!/usr/bin/env python3
"""C106B: ORIGINAL UNCHANGED C105 rules, ten new source coins.
Only semantic/temporal assertions for EXISTING POI/1H/15m/SL/FTA, no new detector.
No direct Pine code reuse from user-provided CC BY-NC-SA LuxAlgo indicator.
PAPER-only, not optimized or live-executable.
"""
import argparse
import hashlib
import json
from bisect import bisect_left
from pathlib import Path
from decimal import Decimal as D

import c105_parent4h_native3m_research as base
import c105_parent4h_native3m_source as sources
import c105_parent4h_structural_geometry as geometry
import c93_native3m_raid_bos_route_c_research as structural_pivot

class C106Rejected(ValueError):pass
SYMBOLS=("ALGOUSDT","CHZUSDT","CRVUSDT","EGLDUSDT","ENSUSDT",
         "ICPUSDT","MANAUSDT","PENDLEUSDT","SEIUSDT","TIAUSDT")
PRECOMMIT="B1_C106_PRECOMMIT_EXISTING_P4_SEMANTICS_UNCHANGED_TRANSFER_RU.md"
SOURCE_BASELINE="C105_4H_PARENT_320_ORIGINAL_NATIVE3M_ZIPS.json"
A168_WITNESS_SHA="5cb01f8022fe5b1de7d19b853cad2ab478cab37fc69204268af911bc159abea4"
ORIGINAL_C105_PINS={
 "c105_parent4h_structural_geometry.py":"b86623b8a7bb8f2580c129e70edbc0dfcf0f68bafc90f94e726d999f0e5db7ac",
 "c105_parent4h_native3m_source.py":"3c083718ddf11e337c2eb0d203a7e60b83b8fe900dbe756c39d9265a8ed2e13d",
 "c105_parent4h_native3m_research.py":"f04b58b998bc1a4bbc531202f241eb476395457765c68189eabf0344f5bd370f"
}
PREVIOUS_GROUPS=(
 {"BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"},
 {"ADAUSDT","AVAXUSDT","DOGEUSDT","LINKUSDT","SUIUSDT"},
 {"AAVEUSDT","APTUSDT","ARBUSDT","ATOMUSDT","ETCUSDT","FILUSDT","LTCUSDT","NEARUSDT","TRXUSDT","UNIUSDT"},
 {"BNBUSDT","XLMUSDT","HBARUSDT","INJUSDT","OPUSDT","LDOUSDT","DOTUSDT","GALAUSDT","SANDUSDT","RUNEUSDT"}
)

def check_frozen():
    here=Path(__file__).resolve().parent
    for path,sha in ORIGINAL_C105_PINS.items():
        actual=hashlib.sha256((here/path).read_bytes()).hexdigest()
        if actual!=sha:raise C106Rejected("ORIGINAL_C105_SOURCE_MUTATED_"+path)
    baseline=here.parent/"evidence"/"c105"/SOURCE_BASELINE
    if hashlib.sha256(baseline.read_bytes()).hexdigest()!=A168_WITNESS_SHA:
        raise C106Rejected("ORIGINAL_C105_25_TRADES_WITNESS_MUTATED")
    base.frozen_source_checks()
    if len(set(SYMBOLS))!=10 or any(set(SYMBOLS)&other for other in PREVIOUS_GROUPS):
        raise C106Rejected("UNPREDECLARED_SYMBOL_CROSSOVER")

def load_new_sources(*,fetch=None):
    """Change only research ticker allowlist temporarily; C105 engine is never edited."""
    check_frozen()
    old=sources.SYMBOLS
    try:
        sources.SYMBOLS=SYMBOLS
        if fetch is None:market,manifest=sources.original_all()
        else:market,manifest=sources.original_all(fetch=fetch)
    finally:
        sources.SYMBOLS=old
    return market,manifest

def replay_unchanged(markets,manifest):
    check_frozen()
    if set(markets)!=set(SYMBOLS) or len(manifest)!=320:
        raise C106Rejected("NEW_10_ORIGINAL_320_ZIP_REQUIRED")
    old=sources.SYMBOLS
    try:
        sources.SYMBOLS=SYMBOLS
        results=base.analyze(markets,manifest)
    finally:
        sources.SYMBOLS=old
    return results

def candle_at_closed(series,when):
    return next((x for x in series if x.close_ms==when),None)

def audit_existing_trade(t,original_rows):
    """Independent reconstruction of timestamps and original C105 exit geometry.
    Reads ONLY existing C105 signal event, never creates or filters trading signals.
    """
    sym=t["symbol"]
    if not all(t.get(k)=="4H" for k in ("parent_tf","stop_source_tf","target_source_tf")):
        raise C106Rejected("NOT_4H_PARENT_SL_TP")
    if (t.get("pad_source")!="ATR_FULLY_CLOSED_4H" or
        t.get("target_source")!="4H_UNCONSUMED_CONFIRMED_PIVOT" or
        t.get("stop_source")!="4H_FVG_FAR_EDGE"):
        raise C106Rejected("LOWER_TF_EXIT_LEAK")
    birth=t["zone_created_ms"];touch=t["first_4h_poi_touch_ms"]
    rejection=t["one_hour_rejection_close_ms"];confirm=t["fifteen_minute_vc_close_ms"]
    entry_time=t["entry_ms"]
    if not (birth<touch<rejection<confirm==entry_time):
        raise C106Rejected("ASOF_EVENT_ORDER")
    if not(birth%geometry.H4==0 and rejection%geometry.H==0
           and confirm%geometry.M15==0 and confirm%geometry.THREE==0):
        raise C106Rejected("WRONG_CLOSED_TIMEFRAME_ALIGNMENT")
    if not t["fta_confirmed_ms"]<=entry_time:
        raise C106Rejected("FUTURE_4H_FTA")
    if t["fta_confirmed_ms"]%geometry.H4 or t["fta_pivot_closed_ms"]%geometry.H4:
        raise C106Rejected("NON4H_PIVOT_CLOCK")
    if original_rows[0].symbol!=sym or original_rows[0].start_ms>birth:
        raise C106Rejected("UNRELATED_ORIGINAL_MARKET_SOURCE")
    opens=[x.start_ms for x in original_rows]
    idx=bisect_left(opens,entry_time)
    if idx>=len(original_rows) or original_rows[idx].start_ms!=entry_time:
        raise C106Rejected("MISSING_NATIVE3M_NEXT_OPEN")
    if original_rows[idx].open!=D(t["entry"]):
        raise C106Rejected("FABRICATED_NATIVE3M_FILL")
    fours=geometry.aggregate(original_rows,geometry.H4)
    fifteens=geometry.aggregate(original_rows,geometry.M15)
    hours=geometry.aggregate(original_rows,geometry.H)
    weeks=geometry.aggregate(original_rows,geometry.W1,geometry.WEEK_ANCHOR)
    days=geometry.aggregate(original_rows,geometry.D1)
    f_index=next((i for i,x in enumerate(fours) if x.close_ms==birth),None)
    if f_index is None or f_index<2:
        raise C106Rejected("PARENT_BORN_BEFORE_THIRD_CLOSED_4H")
    zone,why=geometry.zone_from_three(fours[f_index-2:f_index+1],days,weeks)
    if zone is None or why!="OK" or zone.parent_id!=t["parent_id"] or (
       zone.lower!=D(t["zone_lower"]) or zone.upper!=D(t["zone_upper"])):
        raise C106Rejected("ORIGINAL_4H_FVG_PARENT_MISMATCH")
    start=next((k for k,x in enumerate(fifteens) if x.close_ms==birth),None)
    hit=next((x.close_ms for x in fifteens[start+1:] if x.h>=zone.lower and x.l<=zone.upper),None)
    if hit!=touch:
        raise C106Rejected("FIRST_4H_TOUCH_NOT_FIRST")
    hour=candle_at_closed(hours,rejection)
    if hour is None:raise C106Rejected("1H_REACTION_NOT_A_FULL_CLOSED_CANDLE")
    zone.state="WAIT_1H_REJECTION";zone.first_touch_ms=touch
    if not geometry.rejection(zone,hour):
        raise C106Rejected("REJECTION_NOT_VALID_ON_CLOSED_1H")
    # Assert lower confirmation exactly on given fully closed 15m, later than H1
    m_index=next((k for k,x in enumerate(fifteens) if x.close_ms==confirm),None)
    if m_index is None or m_index<3:raise C106Rejected("NO_COMPLETE_15M_CONFIRM")
    zone.state="WAIT_15M_VC";zone.rejection_ms=rejection
    if not geometry.vc(zone,fifteens[m_index-3:m_index+1]):
        raise C106Rejected("15M_VC_NOT_VALID_ON_CLOSE")
    f_now=next((i for i,x in enumerate(fours) if x.close_ms>entry_time),len(fours))
    before=fours[:f_now]
    if not before or before[-1].close_ms>entry_time:
        raise C106Rejected("FUTURE_4H_ATR")
    atr=geometry.four_atr(before)
    if atr!=D(t["atr4h"]):
        raise C106Rejected("H4_ATR_MISMATCH")
    margin=geometry.PAD*atr
    want_sl=(zone.lower-margin) if zone.side=="LONG" else (zone.upper+margin)
    if want_sl!=D(t["stop"]):
        raise C106Rejected("STOP_NOT_FROM_ORIGINAL_4H_ZONE")
    pivots=structural_pivot._confirmed(fours,geometry.H4,entry_time)
    pivot_candidates=[x for x in pivots if
        x.kind==("HIGH" if zone.side=="LONG" else "LOW") and
        x.confirmed_ms==t["fta_confirmed_ms"] and
        x.pivot_closed_ms==t["fta_pivot_closed_ms"] and
        x.price==D(t["fta"])]
    if not pivot_candidates:
        raise C106Rejected("MISSING_2RIGHT_CLOSED_4H_FTA_PIVOT")
    price=D(t["fta"])
    # independent original 3m proof target was not previously traded after pivot confirmation
    first=bisect_left(opens,t["fta_confirmed_ms"])
    if any((x.high>=price if zone.side=="LONG" else x.low<=price)
           for x in original_rows[first:idx]):
        raise C106Rejected("ALREADY_CONSUMED_4H_FTA")
    want_tp=price-margin if zone.side=="LONG" else price+margin
    if want_tp!=D(t["target"]):
        raise C106Rejected("TP_NOT_FROM_4H_FTA")
    rr=abs(want_tp-D(t["entry"]))/abs(want_sl-D(t["entry"]))
    if round(float(rr),6)!=t["derived_rr"]:
        raise C106Rejected("ARTIFICIAL_FIXED_RR")
    return {"symbol":sym,"parent_id":t["parent_id"],
        "source_c105_trade_entry_ms":entry_time,
        "asof_born_4h":birth,"first_15m_touch":touch,"closed_1h_reaction":rejection,
        "closed_15m_vc":confirm,"h4_fta_available":t["fta_confirmed_ms"],
        "h4_sl_recomputed":str(want_sl),"h4_tp_recomputed":str(want_tp),
        "h4_atr_recomputed":str(atr),"derived_rr":t["derived_rr"],
        "all_existing_semantics_match":True}

def run_new():
    market,manifest=load_new_sources()
    result=replay_unchanged(market,manifest)
    diagnostics=[audit_existing_trade(t,market[t["symbol"]]) for t in result["trades"]]
    return {"schema":"C106B_UNCHANGED_C105_P4_NEW10_REAL_NATIVE3M",
        "precommit":PRECOMMIT,
        "source":"ORIGINAL_BINANCE_VISION_SHA_CHECKED",
        "historical_unseen_symbols_only_not_future_prospective_oos":True,
        "symbols":list(SYMBOLS),"native3m_bars":result["native3m_bars"],
        "source_zip_count":result["source_zip_count"],
        "source_manifest":manifest,"per_symbol":result["per_symbol"],
        "trades":result["trades"],"scores":result["scores"],"folds":result["folds"],
        "admission":result["admission"],"semantic_reconstructions":diagnostics,
        "audited_trades_count":len(diagnostics),
        "c105_engine_sha256":ORIGINAL_C105_PINS,
        "previous_c105_source_witness_sha256":A168_WITNESS_SHA,
        "new_trade_rules":0,"new_luxalgo_indicators":0,
        "parent_tf":"4H","fixed_rr_target":False,
        "live_approved":False,"orders":[],"fills":[],"live_trades":[],
        "status":"PAPER_RESEARCH_NOT_TRADE_READY"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run_new()
    raw=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(raw)
    print(json.dumps({"n":len(report["trades"]),"zips":report["source_zip_count"],
      "bars":report["native3m_bars"],"semantic_proven":report["audited_trades_count"],
      "netR25":report["scores"]["25"]["sum_r"],"PF25":report["scores"]["25"]["pf"],
      "PF40":report["scores"]["40"]["pf"],"screen":report["admission"],
      "sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)},ensure_ascii=False))
if __name__=="__main__":main()
