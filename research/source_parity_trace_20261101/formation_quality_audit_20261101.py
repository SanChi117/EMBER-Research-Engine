"""EMBER: setup formation quality audit on real frozen Binance futures candles.

Research-only; original six strategies are unmodified. This evaluates
the ORIGINAL experimental EARLY_ACCEPT signal generator's 120 events,
including all failures, rather than only 75 TP1-first winners.

NO filter/parameter selection by observed outcomes. Ex-ante descriptors:
prior level, breakout and retest geometry, source of stop, ex-ante
confirmed pivot target with stale-level diagnosis, realistic first
obstacle distance. Entry at next H1 open is an observed execution
convention, NOT knowable at the signal close.

Eight intra-second collisions are analyzed separately for geometry.
TP1/BE/TP2 management is not a rule of this setup generator.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from six_source_early_acceptance_20261101 import audit, source, atr

ROOT = Path(__file__).resolve().parent
SECONDS = tuple(
    ROOT / f"binance_1s_trace75_batch_{name}_20261101.csv"
    for name in ("00", "01a", "01b", "02a", "02b")
)
TRACE75 = ROOT / "trace75_tp1_price_paths_20261101.json"
FINE = ROOT / "trace75_1m_ambiguous_for_1s_20261101.json"
DIAG_PCT = (0.02, 0.05, 0.1, 0.2, 0.3)
DIAG_R = (0.5, 1.0, 1.5, 2.0)


def confirmed_pivots(f, i, side):
    """Only strict 2L/2R pivots whose right flank is already closed."""
    found=[]
    for j in range(max(2, i-240), i-1):
        val=f[j]["high"] if side==1 else f[j]["low"]
        if all(val>f[z]["high"] if side==1 else val<f[z]["low"]
               for z in range(j-2,j+3) if z!=j):
            found.append((j,val))
    return found


def last_protected_pivot(f,i,side,entry):
    """Candidate for structural SL: confirmed opposite-side H1 swing.
    This is a new adaptation hypothesis, NOT the source strategy stop.
    """
    candidates=confirmed_pivots(f,i,-side)
    options=[(j,p) for j,p in candidates if side*(entry-p)>0]
    return options[-1] if options else None


def formation_card(r,f):
    sym=r["symbol"]
    side=1 if r["side"]=="LONG" else -1
    i=r["signal_i"]
    bi=r["breakout_i"]
    assert 40<=bi<i and i+1<len(f)
    bar=f[i]
    breakout=f[bi]
    entry=f[i+1]["open"]
    signal_close=bar["close"]
    a=atr(f,i)
    assert a and a>0
    # level actually established by PRIOR channel, not the breakout bar
    prior=f[bi-20:bi]
    lvl=(max(z["high"] for z in prior) if side==1
         else min(z["low"] for z in prior))
    retest_ext=bar["low"] if side==1 else bar["high"]
    retest_overshoot=max(0,side*(lvl-retest_ext))
    directional_close=side*(bar["close"]-lvl)
    bar_body=abs(bar["close"]-bar["open"])
    volbase=sum(x["volume"] for x in f[bi-20:bi])/20
    channel_dist=side*(breakout["close"]-lvl)
    # Recompute exact nearest confirmed pivot known AT signal-close.
    pivots=confirmed_pivots(f,i,side)
    forward=[(j,p) for j,p in pivots if side*(p-entry)>0]
    forward.sort(key=lambda x:side*(x[1]-entry))
    first=forward[0] if forward else None
    original=r["tp1_previous_confirmed_pivot"]
    assert (first is None)==(original is None)
    if first:
        assert abs(first[1]-original)<=1e-7,(sym,i,first,original)
    # Previously hit pivot is NOT an intact obstacle: distinguish level
    # source from active level. Check only bars AFTER confirmation before
    # the setup bar (avoid current swing candle and future information).
    swept=None
    swept_at=None
    if first:
        pivot_i,pivot=first
        for k in range(pivot_i+3,i):
            if side*(f[k]["high"]-pivot)>=0 if side==1 else (
                side*(f[k]["low"]-pivot)>=0):
                swept=True
                swept_at=k
                break
        if swept is None:
            swept=False
    risk=abs(entry-r["stop_retest_wick_ATR_proxy"])
    dist=abs(original-entry) if first else None
    close_dist=abs(original-signal_close) if first else None
    structural_sl=last_protected_pivot(f,i,side,entry)
    close_to_entry_bp=abs(entry-signal_close)/signal_close*10000
    first_target_pct=(dist/entry*100 if first else None)
    ratio=dist/risk if first and risk>0 else None
    result={
        "symbol":sym,"signal_i":i,"signal_close_ms":r["signal_close_ms"],
        "direction":r["side"],"breakout_i":bi,"retest_age":r["retest_age_bars"],
        "source_p07_match":r["earliness_vs_P07_bars"],
        "prior20_level":lvl,"entry_next_open":entry,
        "entry_signal_close":signal_close,"gap_to_entry_bp":close_to_entry_bp,
        "breakout_close_distance_ATR":channel_dist/a,
        "breakout_body_ATR":abs(breakout["close"]-breakout["open"])/a,
        "breakout_volume_multiple_vs_prior20":(
            breakout["volume"]/volbase if volbase else None),
        "retest_overshoot_ATR":retest_overshoot/a,
        "retest_close_hold_ATR":directional_close/a,
        "retest_body_ATR":bar_body/a,
        "candidate_original_SL_wick_ATR":r["stop_retest_wick_ATR_proxy"],
        "candidate_confirmed_structural_SL":(
            structural_sl[1] if structural_sl else None),
        "candidate_structural_pivot_confirmed_at":(
            structural_sl[0]+2 if structural_sl else None),
        "SL_uses_actual_protected_structure":False,
        "ATR_at_signal":a,
        "first_ex_ante_pivot_TP1":original,
        "first_pivot_i":first[0] if first else None,
        "first_pivot_confirmed_at":first[0]+2 if first else None,
        "first_pivot_previously_swept":swept,
        "first_pivot_prior_sweep_at":swept_at,
        "first_target_distance_from_entry_pct":first_target_pct,
        "first_target_distance_from_signal_close_pct":(
            close_dist/signal_close*100 if first else None),
        "distance_TP1_to_wick_stop_ratio":ratio,
        "original_result_H1":r["72h_next_open_touch_sequence"],
        "p10_volatility_descriptor":r["source_family_tags"][
            "P10_H1_squeeze_same_side_last_6h"],
        "diagnostic_room_pct":{
            str(n):first_target_pct is not None and first_target_pct>=n
            for n in DIAG_PCT},
        "diagnostic_ratio":{
            str(n):ratio is not None and ratio>=n for n in DIAG_R
        },
    }
    return result


def eight_same_second():
    info={x["tracker_id"]:x for x in json.loads(TRACE75.read_text())[
        "individual_75_price_traces"]}
    candles=defaultdict(list)
    for path in SECONDS:
        with path.open(newline="") as file:
            for row in csv.DictReader(file):
                candles[row["case_id"]].append({
                    "t":int(row["open_time"]),
                    "o":float(row["open"]),
                    "h":float(row["high"]),
                    "l":float(row["low"]),
                    "c":float(row["close"]),
                })
    unresolved=[]
    for q in json.loads(FINE.read_text())["events"]:
        name=q["id"]
        side=1 if q["dir"]=="LONG" else -1
        for bar in candles[name]:
            hit_tp=(bar["h"]>=q["tp1"] if side==1
                    else bar["l"]<=q["tp1"])
            hit_e=(bar["l"]<=q["entry"] if side==1
                   else bar["h"]>=q["entry"])
            if hit_tp:
                if not hit_e:
                    break
                entry_hour_start=(bar["t"]==int(
                    info[name]["signal_close_ms"])+1)
                unresolved.append({
                    "id":name,"symbol":q["symbol"],
                    "second_ms":bar["t"],"open":bar["o"],
                    "high":bar["h"],"low":bar["l"],
                    "close":bar["c"],
                    "entry":q["entry"],"tp1":q["tp1"],
                    "first_second_of_entry_hour":entry_hour_start,
                    "second_open_equals_entry":abs(
                        bar["o"]-q["entry"])<=1e-8,
                    "distance_entry_TP1_pct":abs(
                        q["tp1"]-q["entry"])/q["entry"]*100,
                    "note":"A pre-TP1 Entry touch NEVER arms BE. Same-second OHLC cannot rule out a second post-TP1 touch.",
                })
                break
    assert len(unresolved)==8,len(unresolved)
    assert sum(x["second_open_equals_entry"] for x in unresolved)==3
    assert all(x["distance_entry_TP1_pct"]<.1 for x in unresolved)
    return unresolved


def run():
    base=audit()
    data=source()
    rows=[formation_card(x,data[x["symbol"]]["1h"])
          for x in base["all_experimental_entries"]]
    assert len(rows)==120
    assert Counter(x["original_result_H1"] for x in rows)=={
        "TP1_FIRST":75,"INITIAL_SL_FIRST":29,
        "AMBIGUOUS_SAME_H1":9,"NO_EX_ANTE_H1_TP1":7
    }
    available=[x for x in rows if x["first_ex_ante_pivot_TP1"] is not None]
    metrics={}
    for threshold in DIAG_PCT:
        cases=[x for x in available if x["diagnostic_room_pct"][str(threshold)]]
        metrics[str(threshold)]={
            "n":len(cases),
            "tp1_first":sum(x["original_result_H1"]=="TP1_FIRST" for x in cases),
            "sl_first":sum(x["original_result_H1"]=="INITIAL_SL_FIRST" for x in cases),
            "hour_ambiguous":sum(
                x["original_result_H1"]=="AMBIGUOUS_SAME_H1" for x in cases),
            "median_R":median(x["distance_TP1_to_wick_stop_ratio"]
                              for x in cases) if cases else None
        }
    rmetrics={}
    for threshold in DIAG_R:
        cases=[x for x in available
               if x["diagnostic_ratio"][str(threshold)]]
        rmetrics[str(threshold)]={
            "n":len(cases),
            "tp1_first":sum(x["original_result_H1"]=="TP1_FIRST" for x in cases),
            "sl_first":sum(x["original_result_H1"]=="INITIAL_SL_FIRST" for x in cases),
            "hour_ambiguous":sum(
                x["original_result_H1"]=="AMBIGUOUS_SAME_H1" for x in cases)
        }
    summary={
        "status":"EX_ANTE_SETUP_QUALITY_AUDIT_NOT_STRATEGY_REOPTIMIZATION",
        "base_candidate_events":len(rows),
        "events_with_H1_TP1":len(available),
        "all_75_winner_paths_not_rewritten":75,
        "sources":"Original 6 strategies unchanged; P07-derived early accept IS AN ADAPTATION",
        "signal_time_only_features":True,
        "next_open_gap_observed_not_predictable":True,
        "TP1_pivots_previously_swept_count":sum(
            x["first_pivot_previously_swept"] is True for x in available),
        "structural_protected_SL_pivot_available":sum(
            x["candidate_confirmed_structural_SL"] is not None for x in rows),
        "p07_retest_level_penetration_seen":sum(
            x["retest_overshoot_ATR"]>0 for x in rows),
        "target_distance_pct_median":median(
            x["first_target_distance_from_entry_pct"] for x in available),
        "target_to_proxy_SL_median":median(
            x["distance_TP1_to_wick_stop_ratio"] for x in available),
        "diagnostic_min_target_room_pct":metrics,
        "diagnostic_min_target_SL_ratio":rmetrics,
        "one_second_price_path_8_ambiguous":eight_same_second(),
        "caution":"No optimized thresholds, fees or fills. One-source approximate wick stops not structurally validated; 72h H1 outcomes not native PnL, same-hour touches ambiguous. TP1 must cover real costs and first obstacle.",
        "individual_120_formation_cards":rows
    }
    assert len(summary["one_second_price_path_8_ambiguous"])==8
    return summary


if __name__=="__main__":
    print("EMBER_SETUP_QUALITY="+json.dumps(run(),ensure_ascii=False,
                                       allow_nan=False,separators=(",",":")))
