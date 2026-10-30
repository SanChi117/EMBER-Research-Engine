#!/usr/bin/env python3
"""C107 original 640 Binance 3m source research: factual root-cause diagnostics only.
NO NEW TRADE SIGNALS; NO C105/C106 LOGIC CHANGES. PAPER ONLY.
"""
import argparse,hashlib,json
from collections import Counter
from bisect import bisect_left
from decimal import Decimal as D
from pathlib import Path
import c105_parent4h_native3m_source as s105
import c106_parent4h_semantic_transfer as s106
import c105_parent4h_structural_geometry as p4
import c91_continuous_causal_route_a_paper as olda

class C107Error(ValueError):pass
ROOT=Path(__file__).resolve().parent.parent
C105_SHA="5cb01f8022fe5b1de7d19b853cad2ab478cab37fc69204268af911bc159abea4"
C106_SHA="148cd6cd75960730df1bba5c4ca13511e8398e0de2c4f224415a79bf6e33daa8"
EVIDENCE={
 "C105":("c105/C105_4H_PARENT_320_ORIGINAL_NATIVE3M_ZIPS.json",C105_SHA),
 "C106":("c106/C106_P4_UNCHANGED_320_NATIVE3M_ZIP_H4_CAUSAL_AUDIT.json",C106_SHA)
}
def frozen():
    s106.check_frozen()
    out={}
    for tag,(relative,sha) in EVIDENCE.items():
        data=(ROOT/"evidence"/relative).read_bytes()
        if hashlib.sha256(data).hexdigest()!=sha:
            raise C107Error("SOURCE_WITNESS_MUTATED_"+tag)
        out[tag]=json.loads(data)
    if len(out["C105"]["trades"])!=25 or len(out["C106"]["trades"])!=16:
        raise C107Error("C105_C106_41_TRADES_NOT_FROZEN")
    return out

def ceil_closed4(t):
    if type(t) is not int or t<=0:raise C107Error("INVALID_SOURCE_TIMESTAMP")
    return ((t+p4.H4-1)//p4.H4)*p4.H4

def diagnostic(t,rows):
    """Fixed existing trade event; source-only features at pre-entry and post-exit."""
    if not t["parent_tf"]==t["stop_source_tf"]==t["target_source_tf"]=="4H":
        raise C107Error("NOT_FROZEN_4H_PARENT")
    if t["symbol"]!=rows[0].symbol or len(rows)!=15360:
        raise C107Error("BAD_ORIGINAL_COIN_32D_SOURCE")
    fours=p4.aggregate(rows,p4.H4)
    hours=p4.aggregate(rows,p4.H)
    m15=p4.aggregate(rows,p4.M15)
    by4={x.close_ms:i for i,x in enumerate(fours)}
    by1={x.close_ms:x for x in hours}
    by15={x.close_ms:i for i,x in enumerate(m15)}
    born=t["zone_created_ms"];enter=t["entry_ms"];stop_time=t["exit_ms"]
    if born not in by4 or stop_time<=enter or t["fta_confirmed_ms"]>enter:
        raise C107Error("SOURCE_TRADE_CAUSAL_TIMESTAMP_MISMATCH")
    i=by4[born]
    if i<2:raise C107Error("MISSING_4H_MIDDLE_DISPLACEMENT")
    a,middle,last=fours[i-2:i+1]
    # The original FVG gap is as-of the third completed 4H candle.
    original_fvg=olda._fvg((a,middle,last))
    if not original_fvg or original_fvg[0]!=t["side"]:
        raise C107Error("NOT_A_REAL_PREENTRY_4H_FVG")
    if original_fvg[1:]!=(D(t["zone_lower"]),D(t["zone_upper"])):
        raise C107Error("FOUR_H_PARENT_FVG_LEVEL_MISMATCH")
    original_reject=by1.get(t["one_hour_rejection_close_ms"])
    if original_reject is None:raise C107Error("MISSING_CLOSED_HOUR_CONFIRMATION")
    closed15_index=by15.get(t["fifteen_minute_vc_close_ms"])
    if closed15_index is None or closed15_index<3:raise C107Error("MISSING_CLOSED_15M_CONFIRMATION")
    vc_type=olda._vc(m15[closed15_index-3:closed15_index+1],t["side"])
    if vc_type not in ("IMB","SNR"):raise C107Error("UNSUPPORTED_EXISTING_15M_VC")
    zone_mid=(D(t["zone_lower"])+D(t["zone_upper"]))/D(2)
    h1_inside=(original_reject.c<=D(t["zone_upper"]) if t["side"]=="LONG"
               else original_reject.c>=D(t["zone_lower"]))
    # The actual original next-3m entry is later than closed 15m confirmation.
    idx=bisect_left([x.start_ms for x in rows],enter)
    if idx>=len(rows) or rows[idx].open!=D(t["entry"]):
        raise C107Error("FAKE_NEXT_3M_OPEN")
    far_entry=(D(t["entry"])>D(t["zone_upper"]) if t["side"]=="LONG"
                else D(t["entry"])<D(t["zone_lower"]))
    distance= (D(t["entry"])-D(t["zone_upper"]) if t["side"]=="LONG"
               else D(t["zone_lower"])-D(t["entry"]))
    atr=D(t["atr4h"])
    if atr<=0:raise C107Error("ORIGINAL_4H_ATR_INVALID")
    middle_momentum=(middle.c>middle.o if t["side"]=="LONG" else middle.c<middle.o)
    midpoint_depth= ((original_reject.c-zone_mid) if t["side"]=="LONG"
                    else (zone_mid-original_reject.c))
    exittype=t["exit_reason"]
    stopped=exittype in ("STOP_FIRST_SAME_3M","STOP_GAP")
    closed4_at_stop=None;reclaimed=None;invalidated=None;forward_hit_target_after_stop=None
    if stopped:
        close_ms=ceil_closed4(stop_time)
        stop_i=by4.get(close_ms)
        if stop_i is None:raise C107Error("STOP_4H_CANDLE_MISSING")
        close4=fours[stop_i]
        closed4_at_stop=str(close4.c)
        invalidated=(close4.c<D(t["zone_lower"]) if t["side"]=="LONG" else
                     close4.c>D(t["zone_upper"]))
        reclaimed=not invalidated
        # Pure post-stop observation, never a hypothetical PnL or signal.
        maxend=min(enter+p4.MAX_HOLD*p4.THREE,rows[-1].known_ms)
        target=D(t["target"])
        after=[x for x in rows if x.start_ms>=stop_time and x.known_ms<=maxend]
        forward_hit_target_after_stop=any((x.high>=target if t["side"]=="LONG" else
                                           x.low<=target) for x in after)
    return {
       "symbol":t["symbol"],"side":t["side"],"entry_ms":enter,
       "exit_reason":exittype,"exit_ms":stop_time,
       "zone_born":born,"parent_id":t["parent_id"],
       "fvg_middle_direction_agrees":middle_momentum,
       "fvg_middle_body_to_range":round(float(abs(middle.c-middle.o)/(middle.h-middle.l)),8) if middle.h>middle.l else None,
       "fvg_gap_to_atr4h":round(float((D(t["zone_upper"])-D(t["zone_lower"]))/atr),8),
       "h1_reaction_close_inside_parent_fvg":h1_inside,
       "h1_reaction_midpoint_depth_atr4h":round(float(midpoint_depth/atr),8),
       "existing_15m_vc_type":vc_type,
       "entry_beyond_parent_near_edge":far_entry,
       "entry_beyond_parent_near_edge_atr4h":round(float(distance/atr),8),
       "stopped_by_native3m_wick_or_gap":stopped,
       "stop_candle_4h_closed_at_ms":ceil_closed4(stop_time) if stopped else None,
       "stop_candle_4h_close_price":closed4_at_stop,
       "4h_parent_invalidated_on_stop_candle_close":invalidated,
       "4h_parent_still_valid_on_stop_candle_close":reclaimed,
       "original_target_traded_after_stop_within_initial_48h":forward_hit_target_after_stop,
       "stop":t["stop"],"target":t["target"],"entry":t["entry"]
    }

def audit(markets,tags,witnesses):
    names=set(s105.SYMBOLS)|set(s106.SYMBOLS)
    if set(markets)!=names or len(names)!=20 or len(tags)!=640:
        raise C107Error("640_ORIGINAL_20_COIN_PROVIDER_MANIFEST_REQUIRED")
    allx=[]
    for tag in ("C105","C106"):
        for trade in witnesses[tag]["trades"]:
            out=diagnostic(trade,markets[trade["symbol"]])
            out["cohort"]=tag
            allx.append(out)
    if len(allx)!=41:raise C107Error("BROKEN_SOURCE_TRADE_TOTAL")
    by_cohort={}
    for name in ("C105","C106","COMBINED"):
        xs=([x for x in allx if x["cohort"]==name] if name!="COMBINED" else allx)
        stops=[x for x in xs if x["stopped_by_native3m_wick_or_gap"]]
        by_cohort[name]={
          "n":len(xs),"stops":len(stops),"4h_valid_at_stop_bar_close":sum(x["4h_parent_still_valid_on_stop_candle_close"] for x in stops),
          "4h_invalidated_at_stop_bar_close":sum(x["4h_parent_invalidated_on_stop_candle_close"] for x in stops),
          "later_original_target_touched_after_real_stop":sum(x["original_target_traded_after_stop_within_initial_48h"] for x in stops),
          "wrong_direction_middle_4h_fvg":sum(not x["fvg_middle_direction_agrees"] for x in xs),
          "h1_reaction_closed_inside_fvg":sum(x["h1_reaction_close_inside_parent_fvg"] for x in xs),
          "entry_beyond_parent_near_edge":sum(x["entry_beyond_parent_near_edge"] for x in xs),
          "VC_type":dict(sorted(Counter(x["existing_15m_vc_type"] for x in xs).items())),
          "VC_type_stop":dict(sorted(Counter(x["existing_15m_vc_type"] for x in stops).items()))
        }
    return {"schema":"C107_20_COIN_ORIGINAL_640_NATIVE3M_41_C105_C106_FROZEN_TRADES",
      "cohorts":by_cohort,"original_20_crypto_symbols":sorted(names),
      "source_zip_count":len(tags),"source_manifest":tags,
      "source_bars":sum(len(v) for v in markets.values()),
      "all_41_fixed_original_trade_diagnostics":allx,
      "previous_source_witness_sha":{"C105":C105_SHA,"C106":C106_SHA},
      "new_indicators":0,"new_trading_rules":0,"orders":[],"fills":[],"live_trades":[],
      "purpose":"DIAGNOSTIC_NOT_COUNTERFACTUAL_STRATEGY_OPTIMIZATION",
      "status":"PAPER_RESEARCH_CAUSAL_DEFECT_DIAGNOSIS_NOT_LIVE_READY"}

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    witnesses=frozen()
    # Strict provider, no substitution of missing sources; each function verifies SHA/checksum.
    m105,receipt105=s105.original_all()
    m106,receipt106=s106.load_new_sources()
    markets={**m105,**m106}
    result=audit(markets,receipt105+receipt106,witnesses)
    raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(raw)
    print(json.dumps({"cohorts":result["cohorts"],"n_source_zip":result["source_zip_count"],
        "bars":result["source_bars"],"bytes":len(raw),
        "sha256":hashlib.sha256(raw).hexdigest()},ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
