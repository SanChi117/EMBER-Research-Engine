"""EMBER MTF entry formation v2: REAL D1 -> H4 -> H1 event chronology.

Unlike prior H1 range experiments, THIS code generates fresh breakout
candidates from CLOSED H4 ranges. H1 is only the subsequent retest/hold
confirmation. D1 provides an as-of snapshot for situational explanation,
not a compulsory filter. 15m is not claimed until real continuous 15m
source history is frozen. 5m/1m/1s have NO role in setup creation.

This is independently labeled ADAPTATION_HYPOTHESIS, not native six-way
original fusion, not an executed trading strategy or PnL backtest.
No fixed TP / BE / leverage / order size is assigned. A proposed H4
boundary-invalidation level is a diagnostic, NOT verified structural SL.

STATE machine:
  H4_RANGE_KNOWN -> CLOSED_H4_BREAK -> H1_RETEST_HOLD (candidate)
                                    -> H1_FAILED_ACCEPT (watch only)
                                    -> EXPIRED_WITHOUT_RETEST (no trade)

All event timestamps are CLOSED bars; entry confirmation timestamp is
at the H1 close; 'future' price/TP never influences a condition.
"""
from __future__ import annotations

import json
from collections import Counter
from statistics import median

from six_source_early_acceptance_20261101 import source, atr

H4_MS=4*3600000
H1_MS=3600000
D1_MS=24*3600000
RANGE_H4_BARS=12
H4_MIN_CONTEXT=50
H1_RETEST_LIFETIME=12


def complete_h4(f):
    """UTC boundary; no partial H4 bars; preserve last constituent H1 index."""
    buckets={}
    for i,b in enumerate(f):
        key=b["t"]//H4_MS
        buckets.setdefault(key,[]).append((i,b))
    out=[]
    for key,items in sorted(buckets.items()):
        t=key*H4_MS
        if (len(items)!=4 or items[0][1]["t"]!=t
                or any(z[1]["t"]!=t+k*H1_MS
                       for k,z in enumerate(items))):
            continue
        out.append({
            "t":t,"end":items[-1][1]["end"],
            "open":items[0][1]["open"],
            "high":max(z[1]["high"] for z in items),
            "low":min(z[1]["low"] for z in items),
            "close":items[-1][1]["close"],
            "volume":sum(z[1]["volume"] for z in items),
            "last_h1_index":items[-1][0],
        })
    assert all(out[k+1]["t"]-out[k]["t"]==H4_MS
               for k in range(len(out)-1))
    return out


def last_closed_day_index(d,at_ms):
    """Binary search on D1 CLOSE time, no daily peeking."""
    lo,hi=0,len(d)
    while lo<hi:
        mid=(lo+hi)//2
        if d[mid]["end"]<=at_ms:
            lo=mid+1
        else:
            hi=mid
    return lo-1


def ema_until(d,end,n):
    if end<0:return None
    k=2/(n+1)
    value=d[0]["close"]
    for i in range(1,end+1):
        value=k*d[i]["close"]+(1-k)*value
    return value


def d1_context(d,known_at):
    idx=last_closed_day_index(d,known_at)
    if idx<49:
        return {"status":"D1_INSUFFICIENT_CLOSED_HISTORY",
                "last_closed_d1_index":idx}
    e20=ema_until(d,idx,20)
    e50=ema_until(d,idx,50)
    last=d[idx]["close"]
    if last>e20>e50:
        regime="UP_BIASED"
    elif last<e20<e50:
        regime="DOWN_BIASED"
    else:
        regime="MIXED_OR_TRANSITION"
    n=d[max(0,idx-29):idx+1]
    low=min(x["low"] for x in n)
    high=max(x["high"] for x in n)
    pos=(last-low)/(high-low) if high>low else None
    return {
        "status":"D1_AS_OF_SNAPSHOT",
        "last_closed_d1_end":d[idx]["end"],
        "last_closed_d1_index":idx,
        "regime_proxy":regime,
        "EMA20":e20,"EMA50":e50,
        "D1_30_closed_high":high,"D1_30_closed_low":low,
        "position_in_D1_30d_range":pos,
        "warning":"Only descriptive proxy of market regime; not actual P01/P04/P05 source parity.",
    }


def h4_break_events(h4):
    """All CLOSED H4 range breaks. Event eligibility from immediately
    preceding 12 COMPLETE H4 candles, no current-bar range contamination.
    """
    out=[]
    for i in range(H4_MIN_CONTEXT,len(h4)):
        x=h4[i]
        prev=h4[i-RANGE_H4_BARS:i]
        ceiling=max(z["high"] for z in prev)
        floor=min(z["low"] for z in prev)
        last_close=h4[i-1]["close"]
        a=atr(h4,i)
        assert a and a>0
        side=1 if x["close"]>ceiling else -1 if x["close"]<floor else 0
        if not side:continue
        level=ceiling if side==1 else floor
        # Breakout from range is first ACCEPTANCE episode, not any bar
        # continuing to print new highs while previously beyond level.
        if side*(last_close-level)>0:continue
        breakout_strength=side*(x["close"]-level)/a
        out.append({
            "h4_break_i":i,"break_close_ms":x["end"],
            "breakout_h1_index":x["last_h1_index"],
            "side":side,"level":level,
            "h4_ATR14_at_break":a,
            "break_extension_ATR":breakout_strength,
            "h4_bar_high":x["high"],"h4_bar_low":x["low"],
            "source_prior_12_closed_h4_start_ms":prev[0]["t"],
            "source_prior_12_closed_h4_end_ms":prev[-1]["end"],
        })
    return out


def location_snapshot(h4,index,side,level,a):
    """Source-derived H4 location info existing AT breakout.
    Geometric not statistical: includes prior H4 range location, age.
    """
    assert index>=RANGE_H4_BARS
    recent=h4[index-RANGE_H4_BARS:index]
    prior_high=max(x["high"] for x in recent)
    prior_low=min(x["low"] for x in recent)
    top=(level-prior_low)/(prior_high-prior_low) if (
        prior_high>prior_low) else None
    # H4 invalidation zone (a hypothetical boundary, NOT protected swing)
    return {
        "range_H4_high_before_break":prior_high,
        "range_H4_low_before_break":prior_low,
        "relative_boundary_position_in_range":top,
        "range_width_in_H4_ATR":(prior_high-prior_low)/a,
        "boundary_type":"UPPER_BREAK" if side==1 else "LOWER_BREAK",
        "invalidation_H4_boundary_proxy":level-side*.25*a,
    }


def candidate_state_from_breaks(f,h4,breaks,d,symbol):
    """A single active H4 breakout state; H1 retest is only the trigger.
    If a breakout is not retested within next 12 H1 candles: NO ENTRY.
    """
    lookup={q["breakout_h1_index"]:q for q in breaks}
    output=[]
    active=None
    for i,bar in enumerate(f):
        # 1) Process old state and optionally close it at this fully known H1.
        if active is not None:
            state=active
            b=state["break"]
            side=b["side"]
            age=i-b["breakout_h1_index"]
            level=b["level"]
            a=b["h4_ATR14_at_break"]
            if age>H1_RETEST_LIFETIME:
                state["outcome"]="EXPIRED_NO_H1_RETEST_HOLD"
                state["terminal_signal_i"]=i
                output.append(state)
                active=None
            else:
                # Cannot use any H1 candle whose close precedes the H4
                # breakout close: the H4 boundary is not formed yet.
                assert bar["end"]>b["break_close_ms"]
                # Earliest and latest prices of H1 retest candle:
                probe=bar["low"] if side==1 else bar["high"]
                touch=side*(probe-level)<=.10*a
                not_broken=side*(probe-level)>=-.25*a
                held=side*(bar["close"]-level)>0
                positive_body=side*(bar["close"]-bar["open"])>=0
                back_inside=side*(bar["close"]-level)<0
                if touch and not_broken and held and positive_body:
                    state["outcome"]="H1_RETEST_HOLD_ENTRY_CANDIDATE"
                    state["terminal_signal_i"]=i
                    state["confirmation_H1_close_ms"]=bar["end"]
                    state["confirmation_H1_close_price"]=bar["close"]
                    state["confirmation_H1_retest_extreme"]=probe
                    state["age_H1_bars"]=age
                    state["signal_in_4H_hour_index"]=(
                        bar["t"]%H4_MS)//H1_MS
                    state["position_in_h4_entry_context"]="H1_TRIGGER_AFTER_CLOSED_H4_BREAK"
                    state["d1_at_confirmation"]=d1_context(d,bar["end"])
                    state["why_entry"]=(
                        "4H_RANGE_BREAK_KNOWN -> H1_WICK_TESTED_SAME_H4_LEVEL"
                        " -> H1_CLOSE_HELD_BEYOND_LEVEL"
                    )
                    state["if_valid"]={
                        "continuation":"H4 breakout accepted, then H1 retrace and hold",
                        "invalidation":"H1 close re-enters behind H4 broken level or protected structure fails",
                        "optional_future_confirmation":"15m reaction can refine execution ONLY after real 15m candles audited",
                    }
                    state["alternative_scenarios"]=[
                        "H1_OR_H4_REJECTION_THEN_RECLAIM_BACK_IN_RANGE_WATCH_ONLY",
                        "NO_RETEST_AND_FURTHER_EXPANSION_NO_CHASE",
                        "REVERSAL_WHEN_D1_CONTEXT_OPPOSES_BREAKOUT_WATCH_ONLY",
                    ]
                    output.append(state)
                    active=None
                elif back_inside or side*(probe-level)<-.25*a:
                    state["outcome"]="H4_BREAK_FAILED_ACCEPTANCE_NO_ENTRY"
                    state["terminal_signal_i"]=i
                    state["invalidation_H1_close_ms"]=bar["end"]
                    state["why_reject"]=(
                        "H1_CLOSE_REENTERED_BROKEN_H4_RANGE" if back_inside
                        else "H1_WICK_PENETRATED_H4_BOUNDARY_BUFFER"
                    )
                    output.append(state)
                    active=None
        # 2) Only NEW H4 closed bars can initiate a state, not random H1.
        if i in lookup:
            b=lookup[i]
            # A pending structure is not silently overwritten.
            if active is not None:
                output.append({
                    "symbol":symbol,"outcome":"H4_BREAK_IGNORED_EXISTING_PENDING",
                    "break":b,"context_at_break":d1_context(d,bar["end"]),
                })
                continue
            loc=location_snapshot(h4,b["h4_break_i"],b["side"],
                                  b["level"],b["h4_ATR14_at_break"])
            active={
                "symbol":symbol,
                "break":b,
                "structure_location":loc,
                "d1_at_break":d1_context(d,bar["end"]),
                "entry_rule":"H1_RETEST_HOLD_AFTER_4H_CLOSE",
                "do_not_use_5m_for_generation":True,
                "sl_note":"H4_ATR boundary invalidation hypothesis only; no protected-swing SL proof",
                "tp_note":"TP selection deferred per user instruction",
                "original_source_status":"ADAPTATION_HYPOTHESIS_NOT_ORIGINAL_STRATEGY",
            }
            assert b["break_close_ms"]==bar["end"]
    if active is not None:
        active["outcome"]="RIGHT_CENSORED_PENDING_BREAK"
        output.append(active)
    return output


def run():
    raw=source()
    output=[]
    diagnostics={}
    for symbol in ("BTCUSDT","ETHUSDT","SOLUSDT"):
        f=raw[symbol]["1h"]
        d=raw[symbol]["1d"]
        h4=complete_h4(f)
        events=h4_break_events(h4)
        items=candidate_state_from_breaks(f,h4,events,d,symbol)
        output.extend(items)
        diagnostics[symbol]={
            "H1_closed_bars":len(f),
            "H4_full_bars":len(h4),
            "D1_closed_bars_in_store":len(d),
            "h4_breakouts":len(events),
            "mtf_entries":sum(x["outcome"]=="H1_RETEST_HOLD_ENTRY_CANDIDATE"
                              for x in items),
            "rejections":sum(x["outcome"]=="H4_BREAK_FAILED_ACCEPTANCE_NO_ENTRY"
                             for x in items),
            "no_retest":sum(x["outcome"]=="EXPIRED_NO_H1_RETEST_HOLD"
                            for x in items),
        }
    counts=Counter(x["outcome"] for x in output)
    entries=[x for x in output if x["outcome"]==
             "H1_RETEST_HOLD_ENTRY_CANDIDATE"]
    assert all(x["break"]["break_close_ms"]<
               x["confirmation_H1_close_ms"] for x in entries)
    assert all(x["d1_at_confirmation"]["last_closed_d1_end"]<=
               x["confirmation_H1_close_ms"] for x in entries
               if x["d1_at_confirmation"]["status"]=="D1_AS_OF_SNAPSHOT")
    assert all(x["break"]["source_prior_12_closed_h4_end_ms"]<
               x["break"]["break_close_ms"] for x in entries)
    return {
        "scope":"MTF_V2_D1_CONTEXT_H4_FORMATION_H1_RETEST_NO_15M_DATA",
        "source":"genuine frozen Binance USDT-M BTCUSDT ETHUSDT SOLUSDT",
        "new_entry_event_generator":"CLOSED_H4_12_BAR_RANGE_FIRST_BREACH",
        "historical_period":"Same 1499 consecutive H1 futures bars per symbol; D1 older context",
        "event_type_counts":dict(counts),
        "symbol_counts":diagnostics,
        "entry_candidates_count":len(entries),
        "entry_side_counts":dict(Counter(x["break"]["side"] for x in entries)),
        "entry_retest_age_H1_median":median(
            x["age_H1_bars"] for x in entries) if entries else None,
        "D1_regime_at_entry_counts":dict(Counter(
            x["d1_at_confirmation"].get("regime_proxy","INSUFFICIENT")
            for x in entries)),
        "entry_location_examples":entries[:5],
        "all_H4_originated_events":output,
        "cautions":"Research only: no 5m-derived signals; 15m requires fresh full-period data. Break and wick-buffer are hypotheses, not verified protected-SL / exit geometry. No costs, fill parity, independent positive edge, or OOS claim.",
    }


if __name__=="__main__":
    print("EMBER_MTF_ENTRY_V2="+json.dumps(
        run(),ensure_ascii=False,allow_nan=False,separators=(",",":")))
