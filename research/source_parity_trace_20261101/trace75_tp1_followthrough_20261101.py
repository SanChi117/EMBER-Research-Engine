"""TRACE75: market-price path AFTER first TP1 touch for early-acceptance experiment.

Research-only diagnostic on frozen genuine Binance USDT-M H1 candles.
NOT 75 orders or guaranteed fills. NO profitability, no capital math, and
no automatic BE rule. Tracks full post-TP1 candles and preserves ambiguity
within the TP1 candle / later bars. Distinguishes extension independent of
BE from a continuation hypothetically possible before an entry revisit.

The 75 are selected from the earlier experimental synthesis (not random/OOS).
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median

from six_source_early_acceptance_20261101 import audit, source, atr
from optional_be_counterfactual_20261101 import second_confirmed_target

HERE=Path(__file__).resolve().parent
HOURS=(1,3,6,12,24,48,72)
ATR_LEVELS=(0.25,0.50,1.00,2.00)


def hit_target(b,price,side):
    return b["high"]>=price if side==1 else b["low"]<=price


def hit_entry(b,price,side):
    return b["low"]<=price if side==1 else b["high"]>=price


def favorable_peak(bars,side):
    return max(x["high"] for x in bars) if side==1 else min(x["low"] for x in bars)


def first_tp_candle(f,card):
    side=1 if card["side"]=="LONG" else -1
    entry=card["entry_next_open_observed"]
    stop=card["stop_retest_wick_ATR_proxy"]
    target=card["tp1_previous_confirmed_pivot"]
    for j in range(card["signal_i"]+1,card["signal_i"]+73):
        bar=f[j]
        sl=hit_entry(bar,stop,side)
        tp=hit_target(bar,target,side)
        if sl and tp:
            raise AssertionError("AMBIGUOUS first touch misclassified as TP1_FIRST")
        if sl:
            raise AssertionError("SL first misclassified as TP1_FIRST")
        if tp:
            return j
    raise AssertionError("TP1_FIRST with no TP1 touch")


def one_trace(f,card):
    assert card["72h_next_open_touch_sequence"]=="TP1_FIRST"
    side=1 if card["side"]=="LONG" else -1
    signal_i=card["signal_i"]
    tp_i=first_tp_candle(f,card)
    tp1=card["tp1_previous_confirmed_pivot"]
    entry=card["entry_next_open_observed"]
    a=atr(f,signal_i)
    assert a is not None and a>0
    initial=f[tp_i]
    # TP1 H1 candle: can see its close but cannot order its high/low.
    tp_bar_extension=max(0.0,side*(favorable_peak([initial],side)-tp1))
    tp_bar_entry=hit_entry(initial,entry,side)
    tp_bar_close_beyond=side*(initial["close"]-tp1)>0
    # Last 72 *following* whole H1 candles (not just 72h after signal).
    after=f[tp_i+1:tp_i+73]
    complete_followup=len(after)==72
    tp2=second_confirmed_target(f,signal_i,tp1,side)
    tp2_price=tp2["price"] if tp2 else None
    milestones={}
    for hours in HOURS:
        if len(after)<hours:
            milestones[str(hours)]=None
            continue
        bs=after[:hours]
        favorable_price=favorable_peak(bs,side)
        extension=max(0.0,side*(favorable_price-tp1))
        milestones[str(hours)]={
            "extension_price":extension,
            "extension_in_ATR":extension/a,
            "extension_vs_initial_entry_to_TP1":extension/abs(tp1-entry),
            "extended_any_amount":extension>0,
            "extended_at_least_quarter_ATR":extension>=.25*a,
            "extended_at_least_half_ATR":extension>=.50*a,
            "extended_at_least_one_ATR":extension>=1*a,
            "extended_at_least_two_ATR":extension>=2*a,
            "at_least_one_H1_close_beyond_TP1":any(
                side*(x["close"]-tp1)>0 for x in bs),
            "revisited_entry_at_any_point":any(
                hit_entry(x,entry,side) for x in bs),
            "tp2_was_touched_after_TP1_hour":(
                any(hit_target(x,tp2_price,side) for x in bs)
                if tp2_price is not None else None),
        }
    # Counterfactual entry re-touch chronology. NEVER call this a filled BE:
    # same-TP1-bar entry touch makes BE state unresolvable from H1.
    if tp_bar_entry:
        runner="AMBIGUOUS_ENTRY_REVISIT_IN_TP1_H1"
    else:
        runner="NO_ENTRY_REVISIT_IN_NEXT_72H"
        for j,bar in enumerate(after,1):
            near=hit_entry(bar,entry,side)
            ext=side*(favorable_peak([bar],side)-tp1)>=.5*a
            if near and ext:
                runner="AMBIGUOUS_HALF_ATR_EXTENSION_VS_ENTRY_SAME_H1"
                break
            if near:
                runner="ENTRY_REVISIT_FIRST_BEFORE_HALF_ATR_EXTENSION"
                break
            if ext:
                runner="HALF_ATR_EXTENSION_BEFORE_ENTRY_REVISIT"
                break
        if not complete_followup and runner=="NO_ENTRY_REVISIT_IN_NEXT_72H":
            runner="RIGHT_CENSORED_BEFORE_72H"
    return {
        "symbol":card["symbol"],
        "direction":card["side"],
        "signal_close_ms":card["signal_close_ms"],
        "signal_i":signal_i,
        "TP1_first_touch_H1_open_ms":initial["t"],
        "TP1_first_touch_index":tp_i,
        "hours_from_signal_to_TP1_touch_bar":tp_i-signal_i-1,
        "entry_observed_next_H1_open":entry,
        "TP1_level_preknown":tp1,
        "initial_SL_wick_ATR_proxy":card["stop_retest_wick_ATR_proxy"],
        "ATR14_at_signal":a,
        "TP1_first_bar_close_beyond":tp_bar_close_beyond,
        "TP1_first_bar_extension_ATR_unordered":tp_bar_extension/a,
        "TP1_first_bar_entry_revisit_ambiguous":tp_bar_entry,
        "TP2_preknown":tp2_price,
        "TP2_first_bar_touched_unordered":(
            hit_target(initial,tp2_price,side) if tp2_price is not None else None),
        "followup_available_H1_bars":len(after),
        "followup_full_72H":complete_followup,
        "runner_BE_counterfactual":runner,
        "post_first_TP1_hour_windows":milestones,
        "P10_last_6h_label":card["source_family_tags"][
            "P10_H1_squeeze_same_side_last_6h"],
    }


def roll_up(traces):
    out={"cases":len(traces),
         "with_full_72h_followup":sum(x["followup_full_72H"] for x in traces),
         "TP1_first_bar_close_beyond":sum(x["TP1_first_bar_close_beyond"] for x in traces),
         "TP1_bar_entry_revisit_ambiguous":sum(
             x["TP1_first_bar_entry_revisit_ambiguous"] for x in traces),
         "TP2_preknown":sum(x["TP2_preknown"] is not None for x in traces),
         "TP2_first_bar_touched_unordered":sum(
             x["TP2_first_bar_touched_unordered"] is True for x in traces),
         "BE_counterfactual_state_counts":dict(
             Counter(x["runner_BE_counterfactual"] for x in traces)),
         "windows":{}}
    for hour in HOURS:
        eligible=[x["post_first_TP1_hour_windows"][str(hour)] for x in traces
                  if x["post_first_TP1_hour_windows"][str(hour)] is not None]
        atr_moves=[x["extension_in_ATR"] for x in eligible]
        out["windows"][str(hour)]={
            "complete":len(eligible),
            "extended_beyond_TP1_on_later_H1":sum(
                x["extended_any_amount"] for x in eligible),
            "extended_ge_quarter_ATR":sum(
                x["extended_at_least_quarter_ATR"] for x in eligible),
            "extended_ge_half_ATR":sum(
                x["extended_at_least_half_ATR"] for x in eligible),
            "extended_ge_one_ATR":sum(
                x["extended_at_least_one_ATR"] for x in eligible),
            "extended_ge_two_ATR":sum(
                x["extended_at_least_two_ATR"] for x in eligible),
            "H1_close_confirmed_beyond_TP1":sum(
                x["at_least_one_H1_close_beyond_TP1"] for x in eligible),
            "revisited_entry_at_least_once":sum(
                x["revisited_entry_at_any_point"] for x in eligible),
            "TP2_touched_after_TP1_hour_of_those_with_preknown_TP2":sum(
                x["tp2_was_touched_after_TP1_hour"] is True for x in eligible),
            "with_ex_ante_TP2":sum(
                x["tp2_was_touched_after_TP1_hour"] is not None for x in eligible),
            "median_max_favorable_extension_in_ATR_after_hour":(
                median(atr_moves) if atr_moves else None),
        }
    return out


def run():
    base=audit()
    raw=source()
    preknown=[x for x in base["all_experimental_entries"]
              if x["72h_next_open_touch_sequence"]=="TP1_FIRST"]
    assert len(preknown)==75
    traces=[one_trace(raw[c["symbol"]]["1h"],c) for c in preknown]
    res=roll_up(traces)
    by_sym={s:roll_up([x for x in traces if x["symbol"]==s]) for s in (
        "BTCUSDT","ETHUSDT","SOLUSDT")}
    by_p10={
        "yes":roll_up([x for x in traces if x["P10_last_6h_label"]]),
        "no":roll_up([x for x in traces if not x["P10_last_6h_label"]]),
    }
    # 100% original selected denominator: all 75 from experiment.
    assert res["cases"]==75
    assert by_p10["yes"]["cases"]+by_p10["no"]["cases"]==75
    return {
        "experiment":"TRACE75_TP1_NEXT_PRICE_PATH_H1_ONLY",
        "original_experiment":"EARLY_ACCEPT_SYNTHESIS_HYPOTHESIS_NOT_SOURCE_6WAY",
        "original_120_scenarios":120,
        "selected_75_TP1_FIRST":75,
        "source_receipt_sha256":"b885da6dc7e80ea81c7bfb97ec1fb3da615e31824af48625f81cdd376d9a7ee7",
        "timeframe":"1h",
        "report_convention":"All continuation statistics EXCLUDE the whole TP1 first-touch H1 candle. First-touch candle extrema and CLOSE are separate and may conceal ordering.",
        "thresholds_ATR":list(ATR_LEVELS),
        "important":"Max favorable excursion after TP1 may happen AFTER return to entry; is NOT a BE runner outcome. Same H1 touch order is unknown; no fill or PnL claim.",
        "aggregate":res,"by_symbol":by_sym,"by_P10_volatility_label":by_p10,
        "individual_75_price_traces":traces
    }


if __name__=="__main__":
    print("EMBER_TRACE75="+json.dumps(run(),ensure_ascii=False,allow_nan=False))
