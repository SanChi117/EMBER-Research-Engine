"""Backward-time independent H4 history against a *post-selected* pre-entry hypothesis.

No rule changes from Behavior02; the 2.0 prior ATR directional body
indicator was selected on 2025-26 data before reading this 2024-25 H4.
Backward historical holdout is not chronological forward OOS.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean

from behavior01_first_pullback_20261101 import (
    SYMS,LIQ,COMP,load,bar,actual_tf_parity,round_or_none
)
from behavior02_direct_impulse_20261101 import scan_coin_tf

HERE=Path(__file__).resolve().parent
OLD_SHAS={
    "BTCUSDT":"ee32ec200c7ec2176e5a412ac7ed3dae4e4deb78",
    "ETHUSDT":"05ff012160463f069dcae7085af25bd819a68cd5",
    "SOLUSDT":"9d0abc513ad87b10433b681df7854dedcfe9047c",
    "STRKUSDT":"ae4615f4a41594e6b53293cf619d738f19197530",
    "ZKUSDT":"92712b9e8da8ecc21046357652a10bf4cbac7c9a",
    "LDOUSDT":"7a07e838da7b791d9a41ffe1a452f82e31888241",
}


def old_h4(sym):
    p=HERE/(sym+"_4h_OLD_2024_2025.csv")
    raw=p.read_bytes()
    marker=b"blob "+str(len(raw)).encode()+b"\0"+raw
    assert hashlib.sha1(marker).hexdigest()==OLD_SHAS[sym]
    f=list(csv.DictReader(raw.decode("utf-8").splitlines()))
    assert all(x["symbol"]==sym and x["interval"]=="4h" for x in f)
    a=[bar(x) for x in f]
    assert a[-1]["t"]==1750276800000,(sym,a[-1]["t"])
    assert all(a[i+1]["t"]-a[i]["t"]==14400000
               for i in range(len(a)-1)),sym
    return a


def daily_parity(old,day,sym):
    # Each fully covered old day aggregates to the authoritative frozen
    # Binance USD-M D1 OHLCV. Missing first listing partial day excluded.
    dd={x["t"]:x for x in day}
    bars={z["t"]:z for z in old}
    matched=0
    for t,d in dd.items():
        grouped=[bars.get(t+k*14400000) for k in range(6)]
        if any(g is None for g in grouped):continue
        cmp={
            "o":grouped[0]["o"],"c":grouped[-1]["c"],
            "h":max(q["h"] for q in grouped),
            "l":min(q["l"] for q in grouped),
            "vol":sum(q["vol"] for q in grouped),
        }
        for key in ("o","h","l","c"):
            assert abs(cmp[key]-d[key])<1e-7,(sym,t,key)
        assert abs(cmp["vol"]-d["vol"])<=max(.1,1e-7*d["vol"]),(sym,t,"vol")
        matched+=1
    assert matched>300,(sym,matched)
    return matched


def summarise(events):
    S="EXTRA_EXTENSION_BEFORE_HALF_BODY_RETRACE"
    F="HALF_BODY_RETRACE_BEFORE_EXTRA_EXTENSION"
    categories=Counter(z["outcome"]["first_6bar_path_class"] for z in events)
    good=categories[S]
    bad=categories[F]
    prices=[]
    for z in events:
        diag=z["outcome"]["fixed_horizon_diagnostic_returns"]["6"]
        if diag is not None:prices.append(diag["gross_pct"]-.2)
    return {
        "n":len(events),
        "extension_before_half_body_retrace":good,
        "half_body_retrace_first":bad,
        "same_bar_ambiguous":categories["AMBIGUOUS_BOTH_IN_SAME_BAR"],
        "unresolved_or_no_event":len(events)-good-bad-
            categories["AMBIGUOUS_BOTH_IN_SAME_BAR"],
        "resolved_extension_ratio":round_or_none(
            good/(good+bad) if good+bad else None),
        "6_H4_bar_mean_after_hypothetical_0_2pct_friction":round_or_none(
            mean(prices) if prices else None),
        "positive_fixed6_after_friction_count":sum(z>0 for z in prices),
        "n_price_references":len(prices),
    }


def one_cohort(events):
    selected=[z for z in events if z["pre_signal_features"]["impulse_body_atr"]>=2]
    remainder=[z for z in events if z["pre_signal_features"]["impulse_body_atr"]<2]
    assert len(selected)+len(remainder)==len(events)
    return {
        "all":summarise(events),
        "impulse_body_gte_2_prior_ATR":summarise(selected),
        "impulse_body_lt_2_prior_ATR":summarise(remainder),
    }


def run():
    raw,oldmeta=load()
    standard_parity=actual_tf_parity(raw)
    older={}
    p={}
    for symbol in SYMS:
        candles=old_h4(symbol)
        older[symbol]=candles
        p[symbol]=daily_parity(candles,raw[symbol]["1d"],symbol)
    histories={}
    counts={}
    for s in SYMS:
        arr=scan_coin_tf(older[s],raw[s]["1d"],s,"4h")
        histories[s]=arr
        counts[s]={
            "prior_period_total_4h_bars":len(older[s]),
            "prior_period_start_ms":older[s][0]["t"],
            "prior_period_end_ms":older[s][-1]["end"],
            "impulse_events":len(arr),
            "body_size_confirmation_cohort":one_cohort(arr),
        }
    grouped={}
    for name,coins in (("CORE",LIQ),("ALT_COMPARATOR",COMP)):
        older_all=[x for s in coins for x in histories[s]]
        newer_all=[x for s in coins for x in
                   scan_coin_tf(raw[s]["4h"],raw[s]["1d"],s,"4h")]
        grouped[name]={
            "OLD_UNSEEN_2024_2025":one_cohort(older_all),
            "KNOWN_2025_2026":one_cohort(newer_all),
            "CAVEAT":"Older historical backward holdout, after selection on newer period; do not claim prospective out-of-sample",
        }
    return {
        "study":"BEHAVIOR02_H4_BACKWARD_HOLDOUT_BODY_2ATR_NOT_TUNED",
        "status":"HISTORICAL_BACKWARD_CONFIRMATION_NO_FORWARD_OOS",
        "preacquisition_locked_protocol":
            "BEHAVIOR02_LOCKED_BACKWARD_TEST_PREACQUISITION.md",
        "old_frozen_binance_H4_blob_sha":OLD_SHAS,
        "daily_parity_old_H4_grouped_into_actual_D1_bars":p,
        "new_H4_grouped_into_H1_bar_parity":standard_parity,
        "per_symbol":counts,
        "group_comparisons":grouped,
        "all_unseen_older_impulses":{
            s:[{
                "id":x["id"],"time":x["signal_close_ms"],
                "side":x["side"],"body_atr":x["pre_signal_features"][
                    "impulse_body_atr"],
                "class":x["outcome"]["first_6bar_path_class"],
                "6bar_returns":x["outcome"][
                    "fixed_horizon_diagnostic_returns"]["6"],
            } for x in v] for s,v in histories.items()},
        "prohibition":"No further tuning on this or earlier sample. Lack of honest forward OOS, actual executable stop/TP/fees/funding prevents VERIFIED label.",
    }


if __name__=="__main__":
    print("EMBER_BEHAVIOR02_BACKWARD="+json.dumps(
        run(),ensure_ascii=False,allow_nan=False,separators=(",",":")))
