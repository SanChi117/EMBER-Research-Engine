"""EMBER BEHAVIOR02: secondary impulse -> direct expansion before 50% retrace.

EXPLORATORY: selected AFTER viewing behavior01 results on same history.
Not independent OOS, not a validated strategy, no fills/TP/BE decisions.
Preregistered: PREREGISTERED_DIRECT_IMPULSE_CONTINUATION_02.md.
"""
from __future__ import annotations

import bisect
import json
from collections import Counter
from statistics import mean,median

from behavior01_first_pullback_20261101 import (
    LIQ,COMP,SYMS,TFS,MILLISECONDS,load,actual_tf_parity,
    last_n_atr,ema_values,regime_at,round_or_none,
    IMPULSE_TR_ATR,IMPULSE_BODY_FRACTION,IMPULSE_CLOSE_END_FRACTION,
    FUTURE_HORIZONS,FRICTION_PCT
)

EXTENSION_EXTRA_ATR=.5
RETRACEMENT_BODY_FRACTION=.5
ORDER_HORIZON=6


def event_path(f,i,side,a):
    impulse=f[i]
    boundary=(impulse["o"]+impulse["c"])/2
    target=(impulse["h"]+.5*a if side==1 else impulse["l"]-.5*a)
    history=f[i+1:i+1+12]
    reference=f[i+1]["o"] if i+1<len(f) else None
    result="NO_EXTENSION_OR_RETRACE_6"
    first_event_at=None
    for k,z in enumerate(history[:ORDER_HORIZON],1):
        go=(z["h"]>=target if side==1 else z["l"]<=target)
        fall=(z["l"]<=boundary if side==1 else z["h"]>=boundary)
        if go and fall:
            result="AMBIGUOUS_BOTH_IN_SAME_BAR"
            first_event_at=k
            break
        if go:
            result="EXTRA_EXTENSION_BEFORE_HALF_BODY_RETRACE"
            first_event_at=k
            break
        if fall:
            result="HALF_BODY_RETRACE_BEFORE_EXTRA_EXTENSION"
            first_event_at=k
            break
    if len(history)<ORDER_HORIZON and result=="NO_EXTENSION_OR_RETRACE_6":
        result="RIGHT_CENSORED"
    fwd={}
    for h in FUTURE_HORIZONS:
        if len(history)<h or reference is None:
            fwd[str(h)]=None
            continue
        gross=side*(history[h-1]["c"]-reference)/reference*100
        fwd[str(h)]={
            "gross_pct":gross,
            "hypothetical_after_friction_pct":{
                str(k):gross-k for k in FRICTION_PCT},
        }
    mfe=(max((side*((z["h"] if side==1 else z["l"])-reference)
              for z in history),default=0.)/a if reference is not None
         else None)
    mae=(min((side*((z["l"] if side==1 else z["h"])-reference)
              for z in history),default=0.)/a if reference is not None
         else None)
    return {
        "entry_reference_next_open":reference,
        "extension_threshold":target,
        "half_impulse_body_retrace_boundary":boundary,
        "first_6bar_path_class":result,
        "first_event_bar_age":first_event_at,
        "available_bars":len(history),
        "MFE12_ATR":mfe,
        "MAE12_ATR":mae,
        "fixed_horizon_diagnostic_returns":fwd,
    }


def scan_coin_tf(f,d,symbol,tf):
    de=[x["end"] for x in d]
    ema20=ema_values(d,20)
    ema50=ema_values(d,50)
    events=[]
    for i in range(35,len(f)):
        impulse=f[i]
        p=f[i-20:i]
        a=last_n_atr(f,i)
        if not a or a<=0:continue
        size=impulse["h"]-impulse["l"]
        if size<=0:continue
        side=(1 if impulse["c"]>max(z["h"] for z in p) else
              -1 if impulse["c"]<min(z["l"] for z in p) else 0)
        if not side:continue
        body=side*(impulse["c"]-impulse["o"])
        if size<IMPULSE_TR_ATR*a or body/size<IMPULSE_BODY_FRACTION:
            continue
        close_at_tip=(impulse["c"]-impulse["l"])/size if side==1 else (
            impulse["h"]-impulse["c"])/size
        if close_at_tip<IMPULSE_CLOSE_END_FRACTION:continue
        day=regime_at(d,de,ema20,ema50,impulse["end"])
        agree=("AGREES" if ((day=="D1_UP" and side==1)
                           or (day=="D1_DOWN" and side==-1))
               else "OPPOSES" if ((day=="D1_DOWN" and side==1)
                                 or (day=="D1_UP" and side==-1))
               else "MIXED")
        origin=max(z["h"] for z in p) if side==1 else min(z["l"] for z in p)
        vbase=sum(z["vol"] for z in p)/len(p)
        event={
            "id":f"{symbol}:{tf}:{impulse['t']}:{'L' if side==1 else 'S'}",
            "symbol":symbol,
            "universe":"CORE" if symbol in LIQ else "ALT_COMPARATOR",
            "tf":tf,"side":"LONG" if side==1 else "SHORT",
            "impulse_open_ms":impulse["t"],
            "signal_close_ms":impulse["end"],
            "closed_prior20_breakout_boundary":origin,
            "prior14_ATR":a,
            "pre_signal_features":{
                "impulse_true_range_atr":size/a,
                "impulse_body_atr":body/a,
                "close_clearance_over_prior20_level_ATR":
                    side*(impulse["c"]-origin)/a,
                "impulse_volume_multiple_vs_prior20":
                    impulse["vol"]/vbase if vbase else None,
                "prior20_range_ATR":(
                    max(z["h"] for z in p)-min(z["l"] for z in p))/a,
                "prior14_ATR_percent":a/f[i-1]["c"]*100,
                "median_quote_volume_prior20":median(z["qvol"] for z in p),
                "D1_regime_as_of_impulse_close":day,
                "D1_alignment":agree,
            },
            "outcome":event_path(f,i,side,a),
        }
        events.append(event)
    return events


def group_report(events,n_bars,tf):
    cats=Counter(e["outcome"]["first_6bar_path_class"] for e in events)
    months=(n_bars/(24 if tf=="1h" else 6 if tf=="4h" else 1))/30.4375
    def series(h,fee=None):
        res=[]
        for e in events:
            q=e["outcome"]["fixed_horizon_diagnostic_returns"][str(h)]
            if q is None:continue
            res.append(q["gross_pct"] if fee is None
                       else q["hypothetical_after_friction_pct"][str(fee)])
        return res
    d={}
    for h in FUTURE_HORIZONS:
        q=series(h)
        r=series(h,.2)
        d[str(h)]={
            "observations":len(q),
            "gross_mean_pct":round_or_none(mean(q) if q else None),
            "gross_median_pct":round_or_none(median(q) if q else None),
            "after_hypothetical_0_2pct_roundtrip_mean":round_or_none(
                mean(r) if r else None),
            "positive_gross_count":sum(z>0 for z in q),
        }
    resolve=cats["EXTRA_EXTENSION_BEFORE_HALF_BODY_RETRACE"]+(
        cats["HALF_BODY_RETRACE_BEFORE_EXTRA_EXTENSION"])
    return {
        "event_count":len(events),
        "impulses_per_symbol_month":round_or_none(
            len(events)/months if months else None),
        "outcomes":dict(cats),
        "resolved_extension_first_ratio":round_or_none(
            cats["EXTRA_EXTENSION_BEFORE_HALF_BODY_RETRACE"]/resolve
            if resolve else None),
        "resolved_event_count":resolve,
        "fixed_horizon_returns":d,
        "D1_alignment_counts":dict(Counter(
            x["pre_signal_features"]["D1_alignment"] for x in events)),
    }


def run():
    raw,src=load()
    parity=actual_tf_parity(raw)
    events=[]
    details={}
    for s in SYMS:
        details[s]={}
        for tf in TFS:
            arr=scan_coin_tf(raw[s][tf],raw[s]["1d"],s,tf)
            events.extend(arr)
            details[s][tf]=group_report(arr,len(raw[s][tf]),tf)
    total=len(events)
    assert total==894,total  # First behavior-01 preregistered funnel baseline.
    groups={}
    for tf in TFS:
        for name,coins in (("CORE",LIQ),("ALT_COMPARATOR",COMP)):
            e=[x for x in events if x["tf"]==tf and x["symbol"] in coins]
            groups[tf+"_"+name]=group_report(
                e,sum(len(raw[s][tf]) for s in coins),tf)
    regime={}
    for x in ("AGREES","OPPOSES","MIXED"):
        arr=[e for e in events if e["pre_signal_features"]["D1_alignment"]==x]
        regime[x]={
            "n":len(arr),
            "outcomes":dict(Counter(
                e["outcome"]["first_6bar_path_class"] for e in arr)),
        }
    last62=1788098400000
    same={}
    for tf in TFS:
        for name,coins in (("CORE",LIQ),("ALT_COMPARATOR",COMP)):
            arr=[e for e in events if e["symbol"] in coins and e["tf"]==tf
                 and e["signal_close_ms"]>=last62]
            same[tf+"_"+name]={
                "n":len(arr),
                "outcomes":dict(Counter(
                    e["outcome"]["first_6bar_path_class"] for e in arr)),
            }
    return {
        "study":"BEHAVIOR02_SECONDARY_DIRECT_IMPULSE_EXTENSION",
        "status":"EXPLORATORY_POST_SELECTION_NO_OOS_PROFIT_PROOF",
        "root_input_sha":"same pinned source files as Behavior01",
        "source_4h_to_1h_parity_counts":parity,
        "all_symbol_tf_counts":details,
        "per_tf_and_universe":groups,
        "D1_asof_context":regime,
        "same_calendar_last62d":same,
        "n_original_impulse_candidates":total,
        "event_description":"20-bar close breakout + prior range >=1.5ATR + body >=60% + tip close; extra 0.5ATR continuation vs halfway body retrace first within 6 bars",
        "all_impulse_events":events,
        "cautions":"This variant selected after observing Behavior01 on same histories: in-sample; even positive return/extension count cannot prove future profitability. No original source P01/P04/P05/P06/P07/P10 direct entry/exit parity, no actual fees/funding/fills/SL, and overlapping events not statistically independent.",
    }


if __name__=="__main__":
    print("EMBER_BEHAVIOR02_RESULT="+json.dumps(
        run(),ensure_ascii=False,allow_nan=False,separators=(",",":")))
