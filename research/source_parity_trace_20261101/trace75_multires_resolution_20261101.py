"""EMBER TRACE75: deterministic fine-grained TP1 -> Entry/TP2 ordering.

Inputs: frozen real Binance USDT-M BTC/ETH/SOL H1, 5m, 1m;
1s series are USD-M PERPETUAL continuous-contract bars, used ONLY if
their 60s aggregation exactly matches the standard futures 1m kline.

This is an audit of price-level touches, NOT fills, not realized PnL.
The original experimental entry/SL/TP1 comes from previously frozen JSON
and remains separate from native P01/P04/P05/P06/P07/P10 strategies.

Never assume the Entry touch early in the signal/entry H1 counts as a
post-TP1 BE touch. The BE level is armed only AFTER the first TP1 crossing.
When both occur within the finest available 1s candle: unresolved.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from six_source_early_acceptance_20261101 import DATA, SHA, source

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / "trace75_tp1_price_paths_20261101.json"
FIVE = tuple(ROOT / f"binance_5m_trace75_batch_{i:02d}_20261101.csv"
             for i in range(10))
ONE = tuple(ROOT / f"binance_1m_trace75_batch_{i:02d}_20261101.csv"
            for i in range(6))
SECOND = tuple(ROOT / f"binance_1s_trace75_batch_{suffix}_20261101.csv"
               for suffix in ("00", "01a", "01b", "02a", "02b"))
ONE_MIN_MS = 60000
FIVE_MIN_MS = 300000


def read_batches(paths, count, spacing):
    out = defaultdict(list)
    for file in paths:
        assert file.is_file(), file
        with file.open(newline="") as f:
            for row in csv.DictReader(f):
                out[row["case_id"]].append({
                    "t": int(row["open_time"]),
                    "o": float(row["open"]), "h": float(row["high"]),
                    "l": float(row["low"]), "c": float(row["close"]),
                    "v": float(row["volume"]),
                    "symbol": row["symbol"],
                })
    for name, bars in out.items():
        assert len(bars) == count, (name, len(bars), count)
        assert all(bars[k+1]["t"]-bars[k]["t"] == spacing
                   for k in range(len(bars)-1)), name
    return out


def aggregated(bars):
    assert bars
    return {
        "o": bars[0]["o"], "h": max(x["h"] for x in bars),
        "l": min(x["l"] for x in bars), "c": bars[-1]["c"],
        "v": sum(x["v"] for x in bars),
    }


def ensure_matching(x, y, name):
    # Multiple sub-bars sum 0.001-rounded quantities; allow 0.05 absolute
    # volume difference, which is explicitly below practical trade volume.
    for k in ("o", "h", "l", "c"):
        assert abs(x[k]-y[k]) <= 1e-5, (
            "OHLC_MISMATCH", name, k, x[k], y[k])
    assert abs(x["v"]-y["v"]) <= max(.05, 1e-7*abs(y["v"])), (
        "VOLUME_MISMATCH", name, x["v"], y["v"])


def actual_h1():
    assert hashlib.sha256(DATA.read_bytes()).hexdigest() == SHA
    raw=source()
    return {
        sym: {x["t"]: {
            "o": x["open"], "h": x["high"], "l": x["low"],
            "c": x["close"], "v": x["volume"]
        } for x in data["1h"]}
        for sym, data in raw.items()
    }


def validate_data(allcases, five, one, second):
    assert len(allcases)==75
    assert len(five)==75
    assert len(one)==44
    assert len(second)==22
    h1=actual_h1()
    check_counts=Counter()
    for card in allcases:
        name=card["tracker_id"]
        sym=card["symbol"]
        bars=five[name]
        assert all(b["symbol"]==sym for b in bars)
        start=int(card["tp1_first_touch_ms"])
        assert bars[0]["t"]==start
        for j in range(25):
            h=bars[j*12:(j+1)*12]
            x=h1[sym][start+j*3600000]
            ensure_matching(aggregated(h), x, ("H1",name,j))
            check_counts["H1_matched"]+=1
        side=1 if card["direction"]=="LONG" else -1
        first5=next((j for j,b in enumerate(bars[:12])
                     if hit_tp1(b,card["tp1"],side)),None)
        assert first5 is not None,name
        five_bar=bars[first5]
        has_be=hit_entry(five_bar,card["entry"],side)
        if has_be:
            assert name in one, ("missing1m",name)
        else:
            assert name not in one, ("unneeded1m",name)
        if name in one:
            minbars=one[name]
            assert minbars[0]["t"]==five_bar["t"]
            assert all(b["symbol"]==sym for b in minbars)
            ensure_matching(aggregated(minbars),five_bar,("5m",name))
            check_counts["5m_matched"]+=1
            first1=next((j for j,b in enumerate(minbars)
                        if hit_tp1(b,card["tp1"],side)),None)
            assert first1 is not None,name
            if hit_entry(minbars[first1],card["entry"],side):
                assert name in second, ("missing1s",name)
            else:
                assert name not in second, ("unneeded1s",name)
            if name in second:
                secondbars=second[name]
                assert secondbars[0]["t"]==minbars[first1]["t"]
                assert all(b["symbol"]==sym for b in secondbars)
                ensure_matching(aggregated(secondbars),minbars[first1],
                                ("1m_1s_continuous_contract",name))
                check_counts["1m_matched"]+=1
    assert check_counts=={"H1_matched":1875,"5m_matched":44,
                         "1m_matched":22},check_counts
    return dict(check_counts)


def hit_tp1(bar,level,side):
    return bar["h"]>=level if side==1 else bar["l"]<=level


def hit_entry(bar,level,side):
    return bar["l"]<=level if side==1 else bar["h"]>=level


def extended(bar,level,side):
    return max(0.0,side*((bar["h"] if side==1 else bar["l"])-level))


def full_timeline(card,five,one,seconds):
    name=card["tracker_id"]
    b5=five[name]
    side=1 if card["direction"]=="LONG" else -1
    k=next(j for j,b in enumerate(b5[:12])
           if hit_tp1(b,card["tp1"],side))
    if name not in one:
        return [(b, "5m") for b in b5]
    minute=one[name]
    expanded=[]
    if name not in seconds:
        expanded=[(b,"1m") for b in minute]
    else:
        mid=next(i for i,b in enumerate(minute)
                 if hit_tp1(b,card["tp1"],side))
        expanded=([(b,"1m") for b in minute[:mid]]
                  +[(b,"1s") for b in seconds[name]]
                  +[(b,"1m") for b in minute[mid+1:]])
    return ([(b,"5m") for b in b5[:k]]
            + expanded
            + [(b,"5m") for b in b5[k+1:]])


def evaluate_one(card,timeline):
    side=1 if card["direction"]=="LONG" else -1
    entry=card["entry"]
    tp1=card["tp1"]
    tp2=card["tp2"]
    atr=card["atr"]
    assert atr>0
    accepted=False
    tp1_at=None
    tp1_resolution=None
    first_be=None
    be_resolution=None
    first_tp2=None
    first_tp2_resolution=None
    ambiguous_tp1_be=False
    ambiguous_tp2_be=False
    max_before_be=0.0
    possible_extra_in_uncertain_bar=0.0
    clean_atr={str(x):False for x in (.25,.5,1,2)}
    # Every part of first TP1 5m bar is included, split into 1m/1s as needed.
    for b,res in timeline:
        has_tp1=hit_tp1(b,tp1,side)
        has_be=hit_entry(b,entry,side)
        has_tp2=(tp2 is not None and hit_tp1(b,tp2,side))
        possible=extended(b,tp1,side)
        if not accepted:
            if not has_tp1:
                continue  # BE not armed yet, even on the Entry H1 open.
            accepted=True
            tp1_at=b["t"]
            tp1_resolution=res
            if has_be:
                ambiguous_tp1_be=True
                possible_extra_in_uncertain_bar=max(
                    possible_extra_in_uncertain_bar, possible)
                # Cannot determine the existence/order of a post-TP1 BE
                # inside this smallest bar; MUST abstain from classifying
                # any later runner event as an actionable outcome.
                break
            # Price must have crossed TP1 before favorable level >TP1;
            # without BE collision in this bar, extension is certifiable.
        elif has_be:
            first_be=b["t"]
            be_resolution=res
            if has_tp2 and first_tp2 is None:
                ambiguous_tp2_be=True
            possible_extra_in_uncertain_bar=max(
                possible_extra_in_uncertain_bar,possible)
            # Do NOT assign this bar's favorable high/low to the
            # active runner before BE without tick-level ordering.
            break
        max_before_be=max(max_before_be, possible)
        if has_tp2 and first_tp2 is None:
            first_tp2=b["t"]
            first_tp2_resolution=res
        for threshold in (.25,.5,1,2):
            if max_before_be>=threshold*atr:
                clean_atr[str(threshold)]=True
    assert accepted,card["tracker_id"]
    classification=("TP1_BE_SAME_SECOND_UNRESOLVED"
                    if ambiguous_tp1_be else
                    "TP2_BE_SAME_BAR_UNRESOLVED"
                    if ambiguous_tp2_be else
                    "BE_AFTER_TP1" if first_be is not None else
                    "NO_BE_IN_25H")
    if tp2 is None:
        tp2_class="NO_PREKNOWN_TP2"
    elif ambiguous_tp1_be:
        tp2_class="UNKNOWN_TP1_BE_SAME_BAR"
    elif first_tp2 is not None:
        tp2_class="TP2_BEFORE_BE"  # iff far target traversed first
    elif ambiguous_tp2_be:
        tp2_class="UNKNOWN_TP2_BE_SAME_BAR"
    elif first_be is not None:
        tp2_class="BE_BEFORE_TP2"
    else:
        tp2_class="NEITHER_TO_25H"
    return {
        "id":card["tracker_id"],"symbol":card["symbol"],
        "direction":card["direction"],
        "signal_utc":card["signal_utc"],
        "entry":entry, "tp1":tp1, "tp2":tp2, "atr":atr,
        "tp1_first_touch_ms":tp1_at,
        "tp1_first_touch_resolution":tp1_resolution,
        "first_post_tp1_BE_ms":first_be,
        "be_time_resolution":be_resolution,
        "first_tp2_before_be_ms":first_tp2,
        "first_tp2_resolution":first_tp2_resolution,
        "event_class":classification,"tp2_vs_BE_class":tp2_class,
        "certified_max_extension_beyond_TP1_before_BE_price":
            max_before_be,
        "certified_max_extension_beyond_TP1_before_BE_ATR":
            max_before_be/atr,
        "possible_extra_extension_in_first_ambiguous_bar_ATR":
            possible_extra_in_uncertain_bar/atr,
        "certified_atr_thresholds_before_BE":clean_atr,
        "P10_volatility_label":card.get("P10_last_6h_label"),
        "original_1H_entry_conflict":card["entry_revisit_same_tp1_h1_ambiguous"],
    }


def run():
    raw=json.loads(ORIGINAL.read_text())
    items=raw["individual_75_price_traces"]
    assert len(items)==75
    five=read_batches(FIVE,300,FIVE_MIN_MS)
    one=read_batches(ONE,5,ONE_MIN_MS)
    sec=read_batches(SECOND,60,1000)
    matched=validate_data(items,five,one,sec)
    paths=[evaluate_one(c,full_timeline(c,five,one,sec))
           for c in items]
    status=Counter(c["event_class"] for c in paths)
    reach=Counter(c["tp2_vs_BE_class"] for c in paths)
    thresholds={str(t):sum(x["certified_atr_thresholds_before_BE"][str(t)]
                           for x in paths)
                for t in (.25,.5,1,2)}
    cert=[c["certified_max_extension_beyond_TP1_before_BE_ATR"]
          for c in paths if c["event_class"]!="TP1_BE_SAME_SECOND_UNRESOLVED"]
    result={
        "title":"TRACE75_5M_1M_1S_20261101",
        "source":"REAL_BINANCE_USDTM_FROZEN_KLINES_PRICE_TOUCH_ONLY",
        "source_H1_sha256":SHA,
        "n_selected_from_experimental_model":75,
        "matched_bars_to_pinned_higher_resolution":matched,
        "5m_samples_per_case":300,
        "1m_collision_cases":len(one),
        "1s_collision_cases":len(sec),
        "volume_note":"1s data Binance USD-M continuous PERPETUAL, accepted only after matching exact 1m OHLCV.",
        "runner_horizon":"25 hours from the first TP1 H1 hour; not necessarily full 24h after the exact TP1 tick",
        "counts":dict(status),
        "tp2_vs_be_counts":dict(reach),
        "certified_extra_ATR_before_be_counts":thresholds,
        "median_certified_extra_ATR_only_determined":(
            median(cert) if cert else None),
        "case_results":paths,
        "assumptions":"Price-level touches only; intra-1s collisions remain unresolved; do not interpret as actual fills, risk-adjusted PnL, causal original 6-way source code, or profitability. User proposed BE only as optional scenario.",
    }
    assert status["TP1_BE_SAME_SECOND_UNRESOLVED"]==8,status
    assert sum(status.values())==75
    assert sum(reach.values())==75
    return result


if __name__=="__main__":
    print("EMBER_TRACE75_FINE_RESULT="+json.dumps(run(),ensure_ascii=False,
                                             allow_nan=False,separators=(",",":")))
