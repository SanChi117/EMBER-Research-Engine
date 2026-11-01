"""Ex-ante THREE structural TP candidates and BE-after-TP1 touch proxy.

STRICTLY mechanism research; NO PnL, financial optimization, sizing or orders.
Native pinned P07 and P10 Python classes reproduce all H1 signals. P06 uses
the original TA-Lib FreqHub signal trace on Python 3.11/3.12; Python 3.10 uses
the single previously independently verified original source timestamp and
marks that dependency limitation explicitly.

All TP candidates are two-left/two-right CONFIRMED swing levels visible by
signal CLOSE. No forward candle is consulted in target or original SL proposals.

BE scenario is INTRABAR-AMBIGUITY-AWARE: an OHLC bar that touches TP and the
current SL/BE in the same interval produces an UNKNOWN order, NEVER a win.
Touch is not a guaranteed limit-order fill. A source does not provide these
three target TP orders or protection; they are research-only adaptations.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import types
from collections import Counter
from pathlib import Path

import pandas as pd

from mechanism_audit import p06 as execute_p06_native_class
from mechanism_audit import p07_instrumented
from run_trace import CSV, clone_and_check, fmt, prepare

SOURCE_SHA256 = "b885da6dc7e80ea81c7bfb97ec1fb3da615e31824af48625f81cdd376d9a7ee7"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
LADDER_LOOKBACK = {"1h": 240, "4h": 180, "1d": 30}
SCENARIO_HOURS = (72, 168)  # immutable descriptive horizons, not optimized
P06_SIGNAL = "2026-10-02T08:59Z"


def make_h4(hourly: pd.DataFrame) -> pd.DataFrame:
    """4H aligned to UTC midnight; omit incomplete right-edge bars."""
    items = []
    groups = hourly.groupby(hourly.open_time // 14400000, sort=True)
    for _, group in groups:
        if len(group) != 4:
            continue
        group = group.sort_values("open_time")
        if any(int(group.open_time.iat[j+1]) - int(group.open_time.iat[j]) != 3600000
               for j in range(3)):
            continue
        items.append({
            "open_time": int(group.open_time.iloc[0]),
            "close_time": int(group.close_time.iloc[-1]),
            "open": float(group.open.iloc[0]),
            "high": float(group.high.max()),
            "low": float(group.low.min()),
            "close": float(group.close.iloc[-1]),
        })
    return pd.DataFrame(items)


def build_pivots(frame: pd.DataFrame, tf: str, side: int) -> list[dict]:
    """2L2R strict pivot with known_by close time; previous range stays immutable."""
    out = []
    field = "high" if side == 1 else "low"
    arr = frame[field].to_numpy()
    for i in range(2, len(frame)-2):
        value = float(arr[i])
        if all((value > float(arr[k]) if side == 1 else value < float(arr[k]))
               for k in range(i-2,i+3) if k != i):
            out.append({
                "price": value, "tf": tf, "pivot_i": i,
                "pivot_at": int(frame.close_time.iat[i]),
                "known_by": int(frame.close_time.iat[i+2]),
            })
    return out


def candidates_at(
    pivots: list[dict], frame: pd.DataFrame, signal_at: int,
    price: float, direction: int, tf: str
) -> list[dict]:
    """Lookbacks are on SOURCE BARS; index age anchored to last closed bar."""
    last_idx = int(frame.close_time.searchsorted(signal_at, side="right")) - 1
    all_levels = [
        p for p in pivots
        if p["known_by"] <= signal_at
        and last_idx - p["pivot_i"] <= LADDER_LOOKBACK[tf]
        and last_idx >= p["pivot_i"]
        and direction * (p["price"] - price) > 1e-8
    ]
    return sorted(all_levels,key=lambda p:direction*(p["price"]-price))


def choose_ladder(catalog: dict, signal_at: int, entry: float, side: int) -> list[dict | None]:
    h1 = candidates_at(catalog["pivots"]["1h"][side],catalog["frames"]["1h"],
                        signal_at,entry,side,"1h")
    h4 = candidates_at(catalog["pivots"]["4h"][side],catalog["frames"]["4h"],
                        signal_at,entry,side,"4h")
    day = candidates_at(catalog["pivots"]["1d"][side],catalog["frames"]["1d"],
                         signal_at,entry,side,"1d")
    first = (h1 or h4 or day or [None])[0]
    if first is None:
        return [None,None,None]
    second = next((p for p in h4 if side*(p["price"]-first["price"])>1e-8),None)
    if second is None:
        second = next((p for p in day if side*(p["price"]-first["price"])>1e-8),None)
    if second is None:
        return [first,None,None]
    third = next((p for p in h4 if side*(p["price"]-second["price"])>1e-8),None)
    if third is None:
        third = next((p for p in day if side*(p["price"]-second["price"])>1e-8),None)
    return [first,second,third]


def price_barrier_visited(bar, level, side, is_target):
    if is_target:
        return float(bar.high) >= level if side==1 else float(bar.low) <= level
    return float(bar.low) <= level if side==1 else float(bar.high) >= level


def path_scenario(
    frame: pd.DataFrame, signal_i: int, direction: int,
    entry: float, sl: float, targets: list[dict | None], horizon: int
) -> dict:
    """No money math. Strict OHLC ambiguous same-bar touch classification.

    This is a hypothetical bar-extrema TOUCH scenario, not order execution.
    After TP1, original initial SL is *conceptually* replaced by entry.
    A bar touching current protective level and the next target => UNKNOWN.
    TP1+BE same-bar is also UNKNOWN for BE sequencing.
    """
    if any(t is None for t in targets):
        return {"status":"MISSING_ONE_OR_MORE_EX_ANTE_LEVELS","reached_stage":0,
                "full_horizon":False}
    if signal_i+1+horizon > len(frame):
        return {"status":"RIGHT_CENSORED_HISTORY_END","reached_stage":0,
                "full_horizon":False,
                "available_future_bars":max(0,len(frame)-signal_i-1)}
    target_prices = [float(x["price"]) for x in targets]
    stage = 0
    events = []
    for j in range(signal_i+1,signal_i+horizon+1):
        bar=frame.iloc[j]
        current_stop = sl if stage==0 else entry
        sl_hit=price_barrier_visited(bar,current_stop,direction,False)
        next_hit=price_barrier_visited(bar,target_prices[stage],direction,True)
        if sl_hit and next_hit:
            return {"status":"AMBIGUOUS_PROTECTIVE_STOP_AND_NEXT_TP_SAME_H1",
                    "reached_stage":stage,"full_horizon":True,
                    "first_uncertain_at":fmt(int(bar.close_time)),"events":events}
        if sl_hit:
            return {"status":"INITIAL_SL_TOUCH_FIRST" if stage==0 else "BE_TOUCH_AFTER_TP1",
                    "reached_stage":stage,"full_horizon":True,
                    "terminal_at":fmt(int(bar.close_time)),"events":events}
        if next_hit:
            # Before TP1 the hypothetical protective order is at the INITIAL
            # stop, but immediately AFTER TP1 it would be BE. A candle
            # spanning both TP1 and BE cannot prove the sequence, even if
            # its extremum also reaches TP2 or TP3. Do not report full ladder.
            if stage==0 and price_barrier_visited(bar,entry,direction,False):
                events.append({"tp":1,"touched_bar_close":fmt(int(bar.close_time))})
                return {"status":"AMBIGUOUS_NEW_BE_VS_TP_TOUCH_SAME_H1",
                        "reached_stage":1,"full_horizon":True,
                        "first_uncertain_at":fmt(int(bar.close_time)),"events":events}
            while stage<3 and price_barrier_visited(bar,target_prices[stage],direction,True):
                stage+=1
                events.append({"tp":stage,"touched_bar_close":fmt(int(bar.close_time))})
                if stage==3:
                    return {"status":"TP3_ALL_LEVELS_TOUCHED_IN_ORDER","reached_stage":3,
                            "full_horizon":True,"events":events}
    return {"status":"HORIZON_NO_TERMINAL_TOUCH","reached_stage":stage,
            "full_horizon":True,"events":events}


def source_events(df: pd.DataFrame) -> tuple[dict, dict]:
    """Execute original P07/P10 code, ensure independent signal event parity."""
    out={x:[] for x in ("P07","P10","P06")}
    frames={}
    with tempfile.TemporaryDirectory(prefix="ember_tp_ladder_pinned_") as p:
        tmp=Path(p)
        repo7=clone_and_check(tmp,"P07")
        repo10=clone_and_check(tmp,"P10")
        sys.path.insert(0,str(repo7/"src"))
        from perplab.strategy.library.pullback_retest import PullbackRetest
        sys.path.insert(0,str(repo10/"src"))
        from crypto_trade.backtest_models import Signal
        stub=types.ModuleType("crypto_trade.strategies")
        stub.__path__=[str(repo10/"src"/"crypto_trade"/"strategies")]
        stub.NO_SIGNAL=Signal(direction=0,weight=0)
        sys.modules["crypto_trade.strategies"]=stub
        from crypto_trade.strategies.indicator.bb_squeeze import BbSqueezeStrategy

        for symbol in SYMBOLS:
            f=prepare(df,symbol,"1h")
            frames[symbol]=f
            native7=PullbackRetest()
            native_frame=native7.indicators(f)
            native_signal=native7.entry_signal_vectorized(native_frame)
            trace7=p07_instrumented(native_frame)
            original7=[(i,int(v)) for i,v in enumerate(native_signal) if int(v)]
            independent7=[(v["i"],v["side"]) for v in trace7]
            assert original7==independent7,(symbol,"P07_PARITY_MISMATCH")
            for event in trace7:
                out["P07"].append({
                    "symbol":symbol,"i":event["i"],"side":event["side"],
                    "breakout_i":event["breakout_i"],"age":event["age"],
                    "retest_i":event["retest_i"],
                })
            native10=BbSqueezeStrategy()
            f10=f.copy()
            f10["symbol"]=symbol
            native10.compute_features(f10)
            for i,t in enumerate(f10.open_time):
                side=native10.get_signal(symbol,int(t)).direction
                if side:
                    out["P10"].append({"symbol":symbol,"i":i,"side":int(side)})
        assert len(out["P07"])==134
        assert len(out["P10"])==54
        source_status="P06_REUSED_PINNED_TIMESTAMP_NATIVE_REAL_TALIB_NOT_REEXECUTED_PY310"
        if sys.version_info >= (3,11):
            repo6=clone_and_check(tmp,"P06")
            original6=execute_p06_native_class(repo6,df)
            assert original6["total"]==1 and len(original6["first20"])==1
            assert original6["first20"][0]["symbol"]=="BTCUSDT"
            assert original6["first20"][0]["signal_close_utc"]==P06_SIGNAL
            source_status="P06_ORIGINAL_CLASS_WITH_REAL_TALIB_AND_FREQTRADE_SHIM"
        signal6_i=next(
            i for i,r in enumerate(frames["BTCUSDT"].close_time)
            if fmt(int(r))==P06_SIGNAL
        )
        out["P06"].append({"symbol":"BTCUSDT","i":signal6_i,"side":1})
    return out,{"p06_source_status":source_status}


def run():
    assert hashlib.sha256(CSV.read_bytes()).hexdigest()==SOURCE_SHA256
    df=pd.read_csv(CSV)
    sources,meta=source_events(df)
    books={}
    for symbol in SYMBOLS:
        hourly=prepare(df,symbol,"1h")
        daily=prepare(df,symbol,"1d")
        charts={"1h":hourly,"4h":make_h4(hourly),"1d":daily}
        pivots={tf:{1:build_pivots(frame,tf,1),
                    -1:build_pivots(frame,tf,-1)} for tf,frame in charts.items()}
        books[symbol]={"frames":charts,"pivots":pivots}
    cards=[]
    for source,events in sources.items():
        for e in events:
            sym=e["symbol"]
            book=books[sym]
            candles=book["frames"]["1h"]
            i=e["i"];direction=e["side"]
            assert i+1<len(candles)
            entry=float(candles.open.iat[i+1])
            if source=="P07":
                # Source P07 has NO structural SL. This proxy is formation high/low,
                # not an independently verified "protected swing" or source order.
                seg=candles.iloc[e["breakout_i"]+1:i+1]
            elif source=="P10":
                seg=candles.iloc[i-10:i]
            else:
                seg=candles.iloc[i-6:i+1]
            assert len(seg)>0
            stop=float(seg.low.min() if direction==1 else seg.high.max())
            valid_sl=direction*(entry-stop)>0
            targets=choose_ladder(book,int(candles.close_time.iat[i]),entry,direction)
            complete=valid_sl and all(x is not None for x in targets)
            report={
                "source":source,"symbol":sym,"side":"LONG" if direction==1 else "SHORT",
                "signal_close_utc":fmt(int(candles.close_time.iat[i])),
                "observed_next_open_NOT_preknown":entry,
                "initial_sl_proxy_not_source":stop,
                "SL_PROXY_ON_VALID_SIDE":valid_sl,
                "all_three_structural_levels_preknown":bool(complete),
                "target_ladder":[None if p is None else {
                    "price":p["price"],"timeframe":p["tf"],
                    "pivot_utc":fmt(p["pivot_at"]),
                    "confirmed_at_utc":fmt(p["known_by"])
                } for p in targets],
                "tp1_structural_distance_vs_SL_distance":(
                    round(abs(targets[0]["price"]-entry)/abs(entry-stop),6)
                    if valid_sl and targets[0] is not None else None
                ),
                "original_source_has_three_targets_and_BE":False,
                "source_expiry_overrun":bool(e.get("age",0)>5) if source=="P07" else None,
            }
            for hours in SCENARIO_HOURS:
                report["touch_path_"+str(hours)+"h"]=(
                    path_scenario(candles,i,direction,entry,stop,targets,hours)
                    if complete else {"status":"MISSING_GEOMETRY_NO_PATH","reached_stage":0,
                                      "full_horizon":False}
                )
            cards.append(report)
    assert len(cards)==189
    cards.sort(key=lambda x:(x["signal_close_utc"],x["source"],x["symbol"]))
    sums={}
    for source in sources:
        subset=[x for x in cards if x["source"]==source]
        full=[x for x in subset if x["all_three_structural_levels_preknown"]]
        d={"signals":len(subset),"ex_ante_three_levels":len(full),
           "no_three_levels":len(subset)-len(full),
           "tp1_closer_than_stop":sum(
               x["tp1_structural_distance_vs_SL_distance"] is not None
               and x["tp1_structural_distance_vs_SL_distance"]<1
               for x in subset
           ),"first_three_cards":subset[:3]}
        for hr in SCENARIO_HOURS:
            eligible=[x for x in full if x["touch_path_"+str(hr)+"h"]["full_horizon"]]
            status=Counter(x["touch_path_"+str(hr)+"h"]["status"] for x in eligible)
            d[str(hr)+"h"]={
                "eligible_full_history_and_complete_levels":len(eligible),
                "right_censored_full_geometry":len(full)-len(eligible),
                "status_counts":dict(status),
                "reached_TP1_before_any_ambiguous_bar":sum(
                    x["touch_path_"+str(hr)+"h"]["reached_stage"]>=1 for x in eligible
                ),
                "reached_TP2_before_any_ambiguous_bar":sum(
                    x["touch_path_"+str(hr)+"h"]["reached_stage"]>=2 for x in eligible
                ),
                "reached_TP3_before_any_ambiguous_bar":sum(
                    x["touch_path_"+str(hr)+"h"]["reached_stage"]>=3 for x in eligible
                )
            }
        sums[source]=d
    return {"status":"MECHANISM_3TP_PRICE_TOUCH_SCENARIO_ONLY_NOT_EXECUTION_OR_PNL",
            "source_receipt_SHA256":SOURCE_SHA256,
            "signals":len(cards),"source_status":meta,
            "target_selection":"TP1_NEAREST_CONFIRMED_H1_ELSE_H4_ELSE_D1;TP2_NEXT_H4_ELSE_D1;TP3_NEXT_H4_ELSE_D1",
            "two_left_two_right_confirmation_before_signal":True,
            "lookback_source_bars":LADDER_LOOKBACK,
            "scenarios_hours":list(SCENARIO_HOURS),
            "conditional_BE":"AFTER_TP1_TOUCH_PROXY_WITH_SAME_BAR_OHLC_AMBIGUITY_EXPLICIT",
            "sums":sums,"all_cards":cards}


if __name__=="__main__":
    print("EMBER_3TP_MECHANISM_REPORT="+json.dumps(run(),ensure_ascii=False,allow_nan=False))
