"""EMBER experimental SETUP FORMATION v1: build causal range acceptance plans.

Original P01/P04/P05/P06/P07/P10 sources are not modified or conflated.
The new event generator is the previously frozen 120 EARLY_ACCEPT events;
this is the FIRST independently testable PLAN/REJECT layer.
Source P01/P04/P05/P06/P10 labels remain auxiliary, not mandatory.

Every structural target must be a previously confirmed, NOT subsequently
touched H1/H4 pivot, with complete H4 bar chronology. Never skip a nearby
active opposing level to manufacture R. No TP/BE/runner management here.

No fees calibrated, no profit claim, no future-data filters. Entry plan
uses signal CLOSE, while next-open is kept only for simulated execution.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import median

from six_source_early_acceptance_20261101 import audit, source, atr

OUT = Path(__file__).resolve().parent
FOUR_HOURS_MS = 4 * 60 * 60 * 1000
OBSERVED_PCT_THRESHOLDS = (0.05, 0.10, 0.20)
OBSERVED_R_THRESHOLDS = (0.5, 1.0, 1.5)


def four_hour_complete(f, at_i):
    """Only full, UTC-aligned four-H1 groups closed by signal time."""
    buckets={}
    for bar in f[:at_i+1]:
        key=bar["t"]//FOUR_HOURS_MS
        buckets.setdefault(key,[]).append(bar)
    complete=[]
    for key,bars in sorted(buckets.items()):
        start=key*FOUR_HOURS_MS
        if (len(bars)!=4 or bars[0]["t"]!=start
                or bars[-1]["t"]!=start+3*3600000):
            continue
        complete.append({
            "t":start,"end":bars[-1]["end"],
            "high":max(x["high"] for x in bars),
            "low":min(x["low"] for x in bars),
            "open":bars[0]["open"],"close":bars[-1]["close"],
        })
    assert all(x["end"]<=f[at_i]["end"] for x in complete)
    return complete


def prior_confirmed_levels(f, at_i, side, entry_at_signal):
    """Generate H1/H4 pivot candidates, then filter already swept ones."""
    groups=[("1h",f[:at_i+1])]
    groups.append(("4h",four_hour_complete(f,at_i)))
    result=[]
    for tf,bars in groups:
        for j in range(max(2,len(bars)-(240 if tf=="1h" else 180)),
                       len(bars)-2):
            value=bars[j]["high"] if side==1 else bars[j]["low"]
            if side*(value-entry_at_signal)<=0:
                continue
            if not all(value>bars[k]["high"] if side==1
                       else value<bars[k]["low"]
                       for k in range(j-2,j+3) if k!=j):
                continue
            confirmed_end=bars[j+2]["end"]
            # Verify at the highest raw available resolution H1 that no
            # later wick has touched/consumed the level. This includes
            # today's setup bar, known by its close.
            already_touched=False
            for low in f[:at_i+1]:
                if low["t"]<=confirmed_end:
                    continue
                if ((low["high"]>=value) if side==1 else (
                    low["low"]<=value)):
                    already_touched=True
                    break
            result.append({
                "timeframe":tf,"price":value,
                "confirmed_at_ms":confirmed_end,
                "previously_touched":already_touched,
                "distance_from_signal_price":abs(value-entry_at_signal),
            })
    # Deduplicate same numerical obstacle from 1H and 4H:
    # sort in favor of H4 if identical price; no outcome-based pruning.
    result.sort(key=lambda x:(
        x["distance_from_signal_price"],
        0 if x["timeframe"]=="4h" else 1))
    return result


def formation_plan(card,f):
    side=1 if card["side"]=="LONG" else -1
    i=card["signal_i"]
    bi=card["breakout_i"]
    candle=f[i]
    close=candle["close"]
    a=atr(f,i)
    assert a is not None and a>0
    assert bi<i
    level=(max(b["high"] for b in f[bi-20:bi]) if side==1
           else min(b["low"] for b in f[bi-20:bi]))
    body=side*(candle["close"]-candle["open"])
    retest_low=candle["low"] if side==1 else candle["high"]
    assert side*(candle["close"]-level)>0
    assert body>=0
    assert ((retest_low<=level*1.001 and retest_low>=level*.995)
            if side==1 else (
                retest_low>=level*.999 and retest_low<=level*1.005))
    targets=prior_confirmed_levels(f,i,side,close)
    active=[x for x in targets if not x["previously_touched"]]
    nearest=active[0] if active else None
    # Stop PROXY behind known retest wick with ATR buffer. It is NOT
    # a confirmed strong high/low and cannot be called source-native.
    stop=retest_low-side*.1*a
    valid_stop=side*(close-stop)>0
    risk=abs(close-stop)
    dist=abs(nearest["price"]-close) if nearest else None
    theoretical_r=dist/risk if nearest and valid_stop and risk>0 else None
    target_pct=dist/close*100 if nearest else None
    # Distinguish FORMATION quality from later entry mechanics.
    # Hard checks are objective chronology/geometry only.
    reasons=[]
    if not valid_stop:
        reasons.append("STOP_WRONG_SIDE")
    if nearest is None:
        reasons.append("NO_LIVE_CONFIRMED_H1_H4_DESTINATION")
    if nearest and dist<=0:
        reasons.append("FIRST_LIVE_OBSTACLE_AT_SIGNAL")
    if not reasons:
        status="PLAN_GEOMETRY_EXISTS_NOT_APPROVED_FOR_TRADING"
    else:
        status="NO_TRADE_GEOMETRY_INCOMPLETE"
    # Known only when next bar opens; execution feasibility, not
    # information allowed into signal creation.
    next_open=f[i+1]["open"]
    live_target_behind_next_open=(nearest is not None and
                                   side*(nearest["price"]-next_open)<=0)
    return {
        "symbol":card["symbol"],"signal_i":i,
        "signal_close_utc_ms":card["signal_close_ms"],
        "direction":card["side"],"source_breakout_i":bi,
        "source_family_tags":card["source_family_tags"],
        "entry_plan_at_signal_close":close,
        "entry_observed_next_open":next_open,
        "breakout_level_prior20":level,
        "retest_age_bars":card["retest_age_bars"],
        "retest_overshoot_ATR":max(0,side*(level-retest_low))/a,
        "retest_close_beyond_level_ATR":side*(close-level)/a,
        "stop_retest_extremum_ATR_PROXY":stop,
        "first_active_target":nearest,
        "first_active_target_pct":target_pct,
        "first_active_target_R_to_proxy_stop":theoretical_r,
        "number_active_pivot_levels":len(active),
        "number_historically_swept_pivots":sum(
            x["previously_touched"] for x in targets),
        "nearest_original_TP1":card["tp1_previous_confirmed_pivot"],
        "original_TP1_same_as_active":(
            nearest is not None and
            card["tp1_previous_confirmed_pivot"] is not None
            and abs(nearest["price"]-card[
                "tp1_previous_confirmed_pivot"])<=1e-7),
        "execution_next_open_already_beyond_target":live_target_behind_next_open,
        "diagnostics_target_room_pct":{
            str(x):target_pct is not None and target_pct>=x
            for x in OBSERVED_PCT_THRESHOLDS},
        "diagnostics_R":{
            str(x):theoretical_r is not None and theoretical_r>=x
            for x in OBSERVED_R_THRESHOLDS},
        "original_hourly_outcome_not_recomputed":card[
            "72h_next_open_touch_sequence"],
        "status":status,"reasons":reasons,
        "warning":"New ex-ante target is different from previous first pivot. Previous 75 TP1-first outcomes are NOT transferable to this plan."
    }


def run():
    orig=audit()
    data=source()
    items=[formation_plan(x,data[x["symbol"]]["1h"])
           for x in orig["all_experimental_entries"]]
    assert len(items)==120
    status=Counter(x["status"] for x in items)
    active=[x for x in items if x["first_active_target"] is not None]
    changed=[x for x in active if not x["original_TP1_same_as_active"]]
    details={
        "status":"SETUP_FORMATION_V1_CAUSAL_LEVELS_NO_BACKTEST",
        "base_original_experimental_events":len(items),
        "successfully_geometric_plans":status.get(
            "PLAN_GEOMETRY_EXISTS_NOT_APPROVED_FOR_TRADING",0),
        "rejected_for_missing_active_target":status.get(
            "NO_TRADE_GEOMETRY_INCOMPLETE",0),
        "active_target_available":len(active),
        "active_target_different_from_earlier_legacy_TP1":len(changed),
        "next_open_gapped_beyond_active_target":sum(
            x["execution_next_open_already_beyond_target"]
            for x in active),
        "target_room_at_least_pct":{
            str(p):sum(x["diagnostics_target_room_pct"][str(p)]
                       for x in active)
            for p in OBSERVED_PCT_THRESHOLDS},
        "target_R_at_least":{
            str(r):sum(x["diagnostics_R"][str(r)] for x in active)
            for r in OBSERVED_R_THRESHOLDS},
        "median_target_distance_pct":median(
            x["first_active_target_pct"] for x in active) if active else None,
        "median_stop_proxy_R":median(
            x["first_active_target_R_to_proxy_stop"] for x in active)
            if active else None,
        "excluded":"No TP/BE management, no PnL, no signal quality tuned to outcomes; exit path for new targets NOT simulated; no assertion that FTA swing pivot reflects genuine orderbook liquidity.",
        "all_120_formation_plans":items,
    }
    return details


if __name__=="__main__":
    print("EMBER_SETUP_V1="+json.dumps(
        run(),allow_nan=False,ensure_ascii=False,separators=(",",":")))
