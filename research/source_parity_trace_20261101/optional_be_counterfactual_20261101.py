"""Separate OPTIONAL BE-vs-no-BE counterfactual on experimental early entry.

No real orders/fills/costs. Uses H1 OHLC only and marks ALL intrabar conflicts
as ambiguous. NO PnL: this cannot decide if the BE policy creates more profit.
This experiment deliberately DOES NOT make BE mandatory in any strategy.
"""
from __future__ import annotations

import json
from collections import Counter

from six_source_early_acceptance_20261101 import audit, source


def second_confirmed_target(f,i,first,side):
    pivots=[]
    for j in range(max(2,i-240),i-1):
        p=f[j]["high"] if side==1 else f[j]["low"]
        if side*(p-first)<=0:continue
        if all((p>f[k]["high"] if side==1 else p<f[k]["low"])
               for k in range(j-2,j+3) if k!=j):
            pivots.append((abs(p-first),p,j))
    if not pivots:return None
    _,p,j=min(pivots)
    return {"price":p,"pivot_at_i":j,"confirmed_at_i":j+2}


def touched(fbar,price,side,is_target):
    return (fbar["high"]>=price if side==1 else fbar["low"]<=price) if is_target else (
        fbar["low"]<=price if side==1 else fbar["high"]>=price)


def follow_from_tp1(f,first_tp_i,signal_i,side,entry,original_sl,tp2,be):
    for idx in range(first_tp_i,signal_i+1+72):
        bar=f[idx]
        # On the TP1 candle BEFORE the price has definitely hit TP1 we
        # cannot infer that BE was already armed, nor the high/low chronology.
        stop=entry if be else original_sl
        hit_stop=touched(bar,stop,side,False)
        hit_tp=touched(bar,tp2,side,True)
        if idx==first_tp_i and be and hit_stop:
            return "AMBIGUOUS_TP1_AND_NEW_BE_SAME_H1"
        if hit_stop and hit_tp:
            return "AMBIGUOUS_NEXT_TARGET_AND_STOP_SAME_H1"
        if hit_stop:
            return "BE_FIRST" if be else "INITIAL_SL_FIRST_AFTER_TP1"
        if hit_tp:
            return "TP2_FIRST"
    return "NEITHER_IN_REMAINING_72H"


def check():
    cards=audit()["all_experimental_entries"]
    raw=source()
    summaries=[]
    for x in cards:
        if x["72h_next_open_touch_sequence"]!="TP1_FIRST":
            continue
        side=1 if x["side"]=="LONG" else -1
        f=raw[x["symbol"]]["1h"]
        i=x["signal_i"]
        entry=x["entry_next_open_observed"]
        sl=x["stop_retest_wick_ATR_proxy"]
        tp1=x["tp1_previous_confirmed_pivot"]
        assert tp1 is not None
        tp2info=second_confirmed_target(f,i,tp1,side)
        if tp2info is None:
            summaries.append({"symbol":x["symbol"],"entry_i":i,
                              "status":"TP1_FIRST_NO_EX_ANTE_TP2"})
            continue
        tp2=tp2info["price"]
        first_tp_i=None
        for j in range(i+1,i+73):
            bar=f[j]
            a=touched(bar,tp1,side,True)
            b=touched(bar,sl,side,False)
            if b and a:
                raise AssertionError("Original first_tp sequence marked conflict as TP1_FIRST")
            if b:
                raise AssertionError("Original first_tp sequence marked prior SL as TP1_FIRST")
            if a:
                first_tp_i=j
                break
        assert first_tp_i is not None
        with_be=follow_from_tp1(f,first_tp_i,i,side,entry,sl,tp2,be=True)
        no_be=follow_from_tp1(f,first_tp_i,i,side,entry,sl,tp2,be=False)
        summaries.append({
            "symbol":x["symbol"],"entry_i":i,
            "status":"VALID_EX_ANTE_TP2",
            "tp2":tp2,"with_price_BE_scenario":with_be,
            "without_price_BE_scenario":no_be,
            "same_TP1_and_BE_H1_ambiguity":with_be.startswith("AMBIGUOUS_TP1"),
        })
    assert len(summaries)==75
    valid=[x for x in summaries if x["status"]=="VALID_EX_ANTE_TP2"]
    with_counts=Counter(x["with_price_BE_scenario"] for x in valid)
    without_counts=Counter(x["without_price_BE_scenario"] for x in valid)
    conservative_lost=sum(
        x["with_price_BE_scenario"]=="BE_FIRST" and
        x["without_price_BE_scenario"]=="TP2_FIRST" for x in valid)
    result={
        "status":"OPTIONAL_BE_COUNTERFACTUAL_OHLC_TOUCH_ONLY_NOT_PROFITABILITY",
        "all_early_entries":len(cards),"clear_TP1_first":75,
        "TP1_first_with_preknown_further_H1_TP2":len(valid),
        "TP1_first_without_preknown_H1_TP2":75-len(valid),
        "BE_scenario_touch_outcomes":dict(with_counts),
        "no_BE_scenario_touch_outcomes":dict(without_counts),
        "unambiguous_BE_would_prevent_later_TP2_touch":conservative_lost,
        "important":"BE is a separate optional management variant. It cannot be imposed on every signal, and no PnL comparison can be concluded from touches.",
        "records":summaries,
    }
    return result


if __name__=="__main__":
    print("EMBER_OPTIONAL_BE_RESULT="+json.dumps(check(),ensure_ascii=False,allow_nan=False))
