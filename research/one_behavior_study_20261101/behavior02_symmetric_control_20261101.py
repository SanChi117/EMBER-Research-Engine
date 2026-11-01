"""Falsify body-size recognition using symmetric ±1 prior ATR H4 first passages.

Preregistered BEFORE this calculation, but selected after studying other
outcomes on the same historical universe. NEVER claim future OOS or PnL.
All six symbols, old 2024-25 and new 2025-26 Binance USD-M H4 bars.
"""
from __future__ import annotations

import json
from collections import Counter
from statistics import mean

from behavior01_first_pullback_20261101 import (
    SYMS,LIQ,COMP,load,round_or_none
)
from behavior02_direct_impulse_20261101 import scan_coin_tf
from behavior02_backward_confirm_20261101 import old_h4,daily_parity

HORIZON=6


def symmetrical(f,e):
    signal=e["signal_close_ms"]
    i=next(k for k,b in enumerate(f) if b["end"]==signal)
    a=e["prior14_ATR"]
    assert a>0
    side=1 if e["side"]=="LONG" else -1
    future=f[i+1:i+1+HORIZON]
    if not future:
        return {"class":"RIGHT_CENSORED","first_at_bar":None,
                "entry_ref":None}
    entry=future[0]["o"]
    pos=entry+side*a
    neg=entry-side*a
    label="NEITHER_6"
    elapsed=None
    for n,b in enumerate(future,1):
        if side==1:
            good=b["h"]>=pos
            bad=b["l"]<=neg
        else:
            good=b["l"]<=pos
            bad=b["h"]>=neg
        if good and bad:
            label="SAME_BAR_UNKNOWN"
            elapsed=n
            break
        if good:
            label="POS_1ATR_FIRST"
            elapsed=n
            break
        if bad:
            label="NEG_1ATR_FIRST"
            elapsed=n
            break
    if len(future)<HORIZON and label=="NEITHER_6":
        label="RIGHT_CENSORED"
    return {
        "class":label,
        "first_at_bar":elapsed,
        "entry_ref":entry,
        "positive_symmetric_marker":pos,
        "negative_symmetric_marker":neg,
    }


def group_stats(events):
    classes=Counter(z["symmetric"]["class"] for z in events)
    fav=classes["POS_1ATR_FIRST"]
    adverse=classes["NEG_1ATR_FIRST"]
    p=[]
    for z in events:
        h=z["baseline_six_bar_return_after_hypothetical_0_2pct"]
        if h is not None:
            p.append(h)
    return {
        "n":len(events),
        "positive_first":fav,
        "negative_first":adverse,
        "same_bar_unknown":classes["SAME_BAR_UNKNOWN"],
        "neither_or_censored":len(events)-fav-adverse-classes["SAME_BAR_UNKNOWN"],
        "positive_share_among_resolved":round_or_none(
            fav/(fav+adverse) if fav+adverse else None),
        "mean_6bar_after_hypothetical_0_2pct":round_or_none(
            mean(p) if p else None),
        "n_sixbar_returns":len(p),
    }


def run():
    data,meta=load()
    older={}
    parity={}
    for sym in SYMS:
        older[sym]=old_h4(sym)
        parity[sym]=daily_parity(older[sym],data[sym]["1d"],sym)
    cases=[]
    groups={}
    for era,source in (("OLD_2024_2025",older),
                       ("NEW_2025_2026",{
                           s:data[s]["4h"] for s in SYMS
                       })):
        for s in SYMS:
            f=source[s]
            impulses=scan_coin_tf(f,data[s]["1d"],s,"4h")
            for e in impulses:
                px=e["outcome"]["fixed_horizon_diagnostic_returns"]["6"]
                case={
                    "id":e["id"],"era":era,"symbol":s,
                    "cohort":"CORE" if s in LIQ else "ALT_COMPARATOR",
                    "body_size_ge_2prior_ATR":e[
                        "pre_signal_features"]["impulse_body_atr"]>=2.,
                    "body_size_ATR":e["pre_signal_features"][
                        "impulse_body_atr"],
                    "symmetric":symmetrical(f,e),
                    "previous_asymmetric_result":e["outcome"][
                        "first_6bar_path_class"],
                    "baseline_six_bar_return_after_hypothetical_0_2pct":(
                        px["hypothetical_after_friction_pct"]["0.2"]
                        if px is not None else None),
                }
                cases.append(case)
    assert len(cases)==973,len(cases)
    for era in ("OLD_2024_2025","NEW_2025_2026"):
        for name in ("CORE","ALT_COMPARATOR"):
            base=[e for e in cases if e["era"]==era and e["cohort"]==name]
            groups[era+"_"+name]={
                "ALL":group_stats(base),
                "BODY_GTE_2_ATR":group_stats(
                    [z for z in base if z["body_size_ge_2prior_ATR"]]),
                "BODY_LT_2_ATR":group_stats(
                    [z for z in base if not z["body_size_ge_2prior_ATR"]]),
            }
    expected={
        "OLD_2024_2025_CORE":(274,111,163),
        "OLD_2024_2025_ALT_COMPARATOR":(192,60,132),
        "NEW_2025_2026_CORE":(268,120,148),
        "NEW_2025_2026_ALT_COMPARATOR":(239,88,151),
    }
    assert all((
        x["ALL"]["n"],x["BODY_GTE_2_ATR"]["n"],x["BODY_LT_2_ATR"]["n"]
    )==expected[name] for name,x in groups.items()),groups
    return {
        "study":"BEHAVIOR02_SYMMETRIC_1ATR_FIRST_PASSAGE_FALSIFICATION",
        "status":"NOT_VERIFIED_DIRECTIONAL_EDGE",
        "prederegistered_control":"BEHAVIOR02_SYMMETRIC_ATR_FALSIFICATION_PREREG.md",
        "old_H4_D1_match_days":parity,
        "classification":"symmetric +1 ATR vs -1 ATR from observed next-open, six H4 bars, no actual fills/stop/takeprofit",
        "by_era_and_market_group":groups,
        "total_impulse_events_checked":len(cases),
        "complete_case_level_audit":cases,
        "caution":"This is not a risk-adjusted realized futures strategy; ±ATR are diagnostic price thresholds, user has deferred TP/SL design. Data, universe, and body>=2 selected from earlier research, no prospective OOS. Any apparent edge must survive both symmetric geometry and actual costs before positive verdict.",
    }


if __name__=="__main__":
    print("EMBER_BEHAVIOR02_SYMMETRIC="+json.dumps(
        run(),ensure_ascii=False,allow_nan=False,separators=(",",":")))
