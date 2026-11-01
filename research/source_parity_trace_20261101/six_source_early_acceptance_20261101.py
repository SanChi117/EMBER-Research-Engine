"""EMBER six-source SYNTHESIS EXPLORATION, not a validated merged strategy.

Goal: compare genuinely newly generated 'early acceptance' events against
unchanged P07 source events, with no lookahead, using frozen genuine
Binance USD-M closed BTC/ETH/SOL H1 candles. Aux engines P01/P04/P05/P06/P10
provide descriptive labels ONLY, not mutually required conditions.

P01: daily EMA trend proxy (no original portfolio sizing and normalisation).
P04: 720h TSMOM sign proxy (no original vol-target sizing).
P05: 60d daily momentum proxy (no original ATR order implementation).
P06: breakout impulse BODY/ATR proxy (NOT FreqHub source-class signal).
P07: source-exact breakout/retest/rebreak signals; early acceptance is EXPERIMENTAL.
P10: source-equivalent bandwidth/volume H1 signals (native default 15m).

No claim of original six-way source parity, native combined strategy, orders, PnL,
or positive expectation. Outcomes are OHLC TOUCH ORDER with ambiguity flagged.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import pstdev, median

DATA=Path(__file__).resolve().parent/"binance_usdtm_closed_20261101.csv"
SHA="b885da6dc7e80ea81c7bfb97ec1fb3da615e31824af48625f81cdd376d9a7ee7"
SYMS=("BTCUSDT","ETHUSDT","SOLUSDT")
HORIZON=72
LOOKBACK_PIVOT=240


def source():
    assert hashlib.sha256(DATA.read_bytes()).hexdigest()==SHA
    raw={s:{"1h":[],"1d":[]} for s in SYMS}
    with DATA.open(newline="") as f:
        for row in csv.DictReader(f):
            s,tf=row["symbol"],row["interval"]
            if s in raw and tf in ("1h","1d"):
                raw[s][tf].append({k:float(row[k]) for k in
                                   ("open","high","low","close","volume")} |
                                  {"t":int(row["open_time"]),
                                   "end":int(row["close_time"])})
    assert all(len(raw[s]["1h"])==1499 for s in SYMS)
    assert all(len(raw[s]["1d"])==999 for s in SYMS)
    return raw


def atr(bars,i,n=14):
    if i<n:return None
    return sum(max(bars[k]["high"]-bars[k]["low"],
                   abs(bars[k]["high"]-bars[k-1]["close"]),
                   abs(bars[k]["low"]-bars[k-1]["close"]))
               for k in range(i-n+1,i+1))/n


def original_p07(f,sym):
    """Source-code order P07, including late signals if retest precedes timeout."""
    events=[];long=None;short=None
    for i in range(20,len(f)):
        b=f[i];hi=max(x["high"] for x in f[i-20:i])
        lo=min(x["low"] for x in f[i-20:i])
        direction=0
        if long is None:
            if b["close"]>hi:
                long={"level":hi,"from":i,"age":0,"retested":False}
        else:
            long["age"]+=1
            if b["close"]>long["level"]*1.0001 and long["retested"]:
                direction=1
                events.append({"symbol":sym,"i":i,"side":1,
                               "breakout_i":long["from"],"age":long["age"]})
                long=None
            elif abs(b["close"]-long["level"])/long["level"]<=.005:
                long["retested"]=True
            elif long["age"]>5:
                long=None
        if short is None:
            if b["close"]<lo:
                short={"level":lo,"from":i,"age":0,"retested":False}
        else:
            short["age"]+=1
            if b["close"]<short["level"]*.9999 and short["retested"]:
                if not direction:
                    events.append({"symbol":sym,"i":i,"side":-1,
                                   "breakout_i":short["from"],"age":short["age"]})
                short=None
            elif abs(b["close"]-short["level"])/short["level"]<=.005:
                short["retested"]=True
            elif short["age"]>5:
                short=None
    return events


def bb(f,i):
    vals=[x["close"] for x in f[i-19:i+1]]
    avg=sum(vals)/20
    return avg,4*pstdev(vals)/avg


def original_p10_h1(f,sym):
    out=[]
    for i in range(20,len(f)):
        mid,bw=bb(f,i)
        _,prev=bb(f,i-1)
        volume=sum(x["volume"] for x in f[i-9:i+1])/10
        side=1 if f[i]["close"]>mid else -1 if f[i]["close"]<mid else 0
        if prev<.02 and bw>.02 and f[i]["volume"]>1.5*volume and side:
            out.append({"symbol":sym,"i":i,"side":side})
    return out


def confirmed_target(f,known_i,entry,side):
    """2 left+2 right strict swing, confirmed by known signal bar."""
    choices=[]
    for j in range(max(2,known_i-LOOKBACK_PIVOT),known_i-1):
        price=f[j]["high"] if side==1 else f[j]["low"]
        if side*(price-entry)<=0:continue
        if all((price>f[k]["high"] if side==1 else price<f[k]["low"])
               for k in range(j-2,j+3) if k!=j):
            choices.append((abs(price-entry),price,j))
    if not choices:return None
    distance,price,j=min(choices)
    return {"price":price,"pivot_i":j,"confirmed_i":j+2,
            "distance":distance}


def outcome(f,i,side,stop,tp,horizon=HORIZON):
    if i+1+horizon>len(f):
        return "RIGHT_CENSORED"
    entry=f[i+1]["open"]
    if not (side*(entry-stop)>0 and side*(tp-entry)>0):
        return "INVALID_GEOMETRY"
    for k in range(i+1,i+horizon+1):
        x=f[k]
        hit_stop=x["low"]<=stop if side==1 else x["high"]>=stop
        hit_tp=x["high"]>=tp if side==1 else x["low"]<=tp
        if hit_stop and hit_tp:return "AMBIGUOUS_SAME_H1"
        if hit_stop:return "INITIAL_SL_FIRST"
        if hit_tp:return "TP1_FIRST"
    return "NO_TOUCH_IN_72H"


def ema_state(d,last_idx,days):
    p=2/(days+1)
    ema=d[0]["close"]
    for k in range(1,last_idx+1):
        ema=p*d[k]["close"]+(1-p)*ema
    return ema


def context(raw,sym,f,i,side,p10,breakout_i):
    """ALL extra source families are PROXY TAGS, not six native trading engines."""
    b=f[i]
    day=raw[sym]["1d"]
    # Last fully closed daily candle only; do NOT use still-forming D1.
    day_i=-1
    for k in range(len(day)):
        if day[k]["end"]<=b["end"]:day_i=k
        else:break
    p01=None;p05=None;p04=None
    if day_i>=200:
        d=day
        # Daily trend context only. Source P01 also requires risk normalization
        # and portfolio mechanics absent from this label.
        votes=[math.copysign(1,ema_state(d,day_i,a)-ema_state(d,day_i,b))
               for a,b in ((16,48),(32,96),(64,192))]
        p01=(sum(votes)*side)>0
    if day_i>=60:
        p05=(day[day_i]["close"]>day[day_i-60]["close"]) if side==1 else (
             day[day_i]["close"]<day[day_i-60]["close"])
        # P05 is source LONG-only; SHORT is a declared analytical analog.
    if i>=720:
        p04=side*(f[i]["close"]-f[i-720]["close"])>0
    prior6=any(x["side"]==side and 0<=i-x["i"]<=6 for x in p10)
    A=atr(f,breakout_i)
    pr40=f[max(0,breakout_i-40):breakout_i]
    level40=max(x["high"] for x in pr40) if side==1 else min(x["low"] for x in pr40)
    br=f[breakout_i]
    impulse=(A is not None and
             abs(br["close"]-br["open"])>0.9*A and
             side*(br["close"]-level40)>1.2*A)
    return {"P01_daily_ema_proxy_agrees":p01,
            "P04_720h_momentum_proxy_agrees":p04,
            "P05_60d_momentum_proxy_agrees":p05,
            "P06_ATR_impulse_proxy_at_breakout":impulse,
            "P10_H1_squeeze_same_side_last_6h":prior6}


def new_acceptance(raw,sym,original,p10):
    """NEW ENTRY: break of prior20 H1; on future retest wick, close HOLDS
    broken level and candle closes in breakout direction; ENTER next H1 OPEN.

    Unlike original P07 this is EARLIER than final rebreak in some events.
    It is an EXPERIMENTAL entry based on P07 formation geometry, NOT source P07.
    """
    f=raw[sym]["1h"];pending={1:None,-1:None};events=[]
    for i in range(40,len(f)-HORIZON-1):
        x=f[i];last=f[i-20:i]
        hi=max(q["high"] for q in last)
        lo=min(q["low"] for q in last)
        A=atr(f,i)
        assert A is not None
        for side in (1,-1):
            state=pending[side]
            if state is None:continue
            age=i-state["at"];lvl=state["level"]
            if age>5:
                pending[side]=None
                continue
            hit=(x["low"]<=lvl*1.001 and x["low"]>=lvl*.995) if side==1 else (
                 x["high"]>=lvl*.999 and x["high"]<=lvl*1.005)
            hold=(x["close"]>lvl) if side==1 else (x["close"]<lvl)
            close_in_direction=(x["close"]>=x["open"]) if side==1 else (
                                x["close"]<=x["open"])
            if hit and hold and close_in_direction:
                # Stop is structural WICK PROXY + ATR buffer, not a verified
                # protected pivot: trade could fail even when this level holds.
                stop=(x["low"]-.1*A) if side==1 else (x["high"]+.1*A)
                entry=f[i+1]["open"]
                tp=confirmed_target(f,i,entry,side)
                original_after=next((e for e in original
                                     if e["breakout_i"]==state["at"]
                                     and e["side"]==side
                                     and e["i"]>=i and e["i"]<=i+6),None)
                cause=context(raw,sym,f,i,side,p10,state["at"])
                card={
                    "symbol":sym,"signal_i":i,"signal_close_ms":x["end"],
                    "side":"LONG" if side==1 else "SHORT",
                    "breakout_i":state["at"],"retest_age_bars":age,
                    "entry_next_open_observed":entry,
                    "stop_retest_wick_ATR_proxy":stop,
                    "tp1_previous_confirmed_pivot":tp["price"] if tp else None,
                    "tp1_pivot_confirmed_i":tp["confirmed_i"] if tp else None,
                    "source_P07_matching_rebreak_i":original_after["i"] if original_after else None,
                    "earliness_vs_P07_bars":original_after["i"]-i if original_after else None,
                    "source_family_tags":cause,
                }
                if tp:
                    card["ratio_first_target_distance_to_stop"] = (
                        abs(tp["price"]-entry)/abs(entry-stop)
                        if abs(entry-stop)>0 else None
                    )
                    card["72h_next_open_touch_sequence"]=outcome(
                        f,i,side,stop,tp["price"])
                else:
                    card["ratio_first_target_distance_to_stop"]=None
                    card["72h_next_open_touch_sequence"]="NO_EX_ANTE_H1_TP1"
                events.append(card)
                pending[side]=None
            elif ((x["close"]<lvl*.995) if side==1 else (
                  x["close"]>lvl*1.005)):
                pending[side]=None
        if pending[1] is None and x["close"]>hi:
            pending[1]={"at":i,"level":hi}
        if pending[-1] is None and x["close"]<lo:
            pending[-1]={"at":i,"level":lo}
    return events


def audit():
    raw=source()
    records=[];originals={};aux={}
    for sym in SYMS:
        f=raw[sym]["1h"]
        originals[sym]=original_p07(f,sym)
        aux[sym]=original_p10_h1(f,sym)
        records.extend(new_acceptance(raw,sym,originals[sym],aux[sym]))
    assert sum(len(x) for x in originals.values())==134
    assert sum(len(x) for x in aux.values())==54
    assert [len(originals[s]) for s in SYMS]==[53,39,42]
    assert [len(aux[s]) for s in SYMS]==[18,21,15]
    counts=Counter(x["72h_next_open_touch_sequence"] for x in records)
    paired=[x for x in records if x["earliness_vs_P07_bars"] is not None]
    early=[x for x in paired if x["earliness_vs_P07_bars"]>0]
    valid=[x for x in records if x["tp1_previous_confirmed_pivot"] is not None]
    # Descriptive group comparisons, not optimized filters.
    labels={}
    for key in ("P01_daily_ema_proxy_agrees","P04_720h_momentum_proxy_agrees",
                "P05_60d_momentum_proxy_agrees",
                "P06_ATR_impulse_proxy_at_breakout",
                "P10_H1_squeeze_same_side_last_6h"):
        yes=[x for x in valid if x["source_family_tags"][key] is True]
        no=[x for x in valid if x["source_family_tags"][key] is False]
        missing=[x for x in valid if x["source_family_tags"][key] is None]
        labels[key]={
            "yes":len(yes),"yes_tp1_first":sum(
                x["72h_next_open_touch_sequence"]=="TP1_FIRST" for x in yes),
            "no":len(no),"no_tp1_first":sum(
                x["72h_next_open_touch_sequence"]=="TP1_FIRST" for x in no),
            "not_available":len(missing),
        }
    geor=[x["ratio_first_target_distance_to_stop"] for x in valid
          if x["ratio_first_target_distance_to_stop"] is not None]
    evidence={
        "status":"SIX_SOURCE_INSPIRED_SYNTHESIS_HYPOTHESIS_NOT_ORIGINAL_AND_NOT_PROFITABLE",
        "dataset_SHA256":SHA,
        "original_P07_signal_count":134,
        "original_P10_H1_signal_count":54,
        "novel_EARLY_ACCEPT_signal_count":len(records),
        "by_symbol":{s:sum(x["symbol"]==s for x in records) for s in SYMS},
        "source_P07_same_breakout_with_later_rebreak":len(paired),
        "new_entry_earlier_than_P07":len(early),
        "source_P07_comparable_events_same_bar":sum(
            x["earliness_vs_P07_bars"]==0 for x in paired),
        "earliness_median_H1_bars_for_earlier":median(
            [x["earliness_vs_P07_bars"] for x in early]) if early else None,
        "72h_price_touch_outcomes":dict(counts),
        "TP1_first_lower_bound_over_all_records":(
            counts["TP1_FIRST"]/len(records) if records else None),
        "median_TP1_to_initial_SL_distance_ratio_on_valid_geometry":(
            median(geor) if geor else None),
        "P01_P04_P05_P06_P10_auxiliary_labels":labels,
        "rules":"Early entry is EXPERIMENTAL, structural stop is a wick+ATR HYPOTHESIS, H1 same-bar touch order is UNKNOWN and LIMIT fills unproven; this is a short 3-symbol single period exploratory in-sample test, not trade expectancy or source-native six-way parity.",
        "all_experimental_entries":records,
    }
    assert len(records)==120,(len(records),counts)
    assert dict(counts)=={"INITIAL_SL_FIRST":29,"AMBIGUOUS_SAME_H1":9,
                          "NO_EX_ANTE_H1_TP1":7,"TP1_FIRST":75},counts
    assert len(paired)==76 and len(early)==32,(len(paired),len(early))
    return evidence


if __name__=="__main__":
    print("EMBER_EARLY_FUSION_AUDIT="+json.dumps(audit(),ensure_ascii=False,allow_nan=False))
