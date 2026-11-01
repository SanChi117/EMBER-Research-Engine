"""Mechanism-first original source audit. Zero money math or backtest profitability.

P07 + P10: original Python entry classes and independently observed intermediate
formation states, checked at 100% of frozen Binance USDT-M 1h signal events.
P06: original FreqHub class + REAL TA-Lib indicator library, but minimal
Freqtrade adapter (not full Freqtrade framework parity). Never silently promote.

Output: source-runnable structured geometry cards. SL/TP proposals are explicitly
named ADAPTATION_HYPOTHESIS, never misrepresented as source orders.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import math
import sys
import tempfile
import types
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from run_trace import CSV, SOURCES, clone_and_check, fmt, import_source, prepare

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def number(x, decimals=6):
    if x is None or not math.isfinite(float(x)):
        return None
    return round(float(x), decimals)


def candle_at(frame, i):
    return {"open":number(frame.open.iat[i]),"high":number(frame.high.iat[i]),
            "low":number(frame.low.iat[i]),"close":number(frame.close.iat[i])}


def pivot_target(frame, i, direction, entry):
    """A PRE-EXISTING and CONFIRMED (2 left, 2 right) opposing swing point.

    No pivots at t-1 or t; a two-bar right confirmation is necessary.
    Scan last <=240 completed historical candles. Choose closest valid
    opposing pivot; it need not be unique or a reliable destination.
    """
    if entry is None or i < 5:
        return None
    candidates = []
    for j in range(max(2,i-240),i-1):
        neighborhood=frame.iloc[j-2:j+3]
        if len(neighborhood)!=5:
            continue
        px=float(frame.high.iat[j] if direction==1 else frame.low.iat[j])
        if direction==1:
            if px>entry and px==float(neighborhood.high.max()):
                candidates.append((px,j))
        else:
            if px<entry and px==float(neighborhood.low.min()):
                candidates.append((px,j))
    if not candidates:
        return None
    price,index=min(candidates,key=lambda x:abs(x[0]-entry))
    return {"level":number(price), "pivot_close_utc":fmt(int(frame.close_time.iat[index])),
            "known_by_signal_utc":fmt(int(frame.close_time.iat[index+2])),
            "kind":"PRIOR_CONFIRMED_2L2R_PIVOT_ADAPTATION_NOT_SOURCE"}


def source_utc(frame,i):
    return fmt(int(frame.close_time.iat[i]))


def p07_instrumented(frame):
    """Independent, transition-by-transition replay of PINNED state machine.

    No future candles read to compute any single event; monitor both long and short
    state exactly as author: first breakout -> close-only retest -> re-break;
    re-break and retest are checked BEFORE timeout, which can overrun max age.
    """
    rows=[]
    long=None
    short=None
    for i in range(len(frame)):
        close=float(frame.close.iat[i])
        up=float(frame.bo_high.iat[i]) if pd.notna(frame.bo_high.iat[i]) else math.nan
        down=float(frame.bo_low.iat[i]) if pd.notna(frame.bo_low.iat[i]) else math.nan
        if math.isnan(up):
            continue
        if long is None:
            if close>up:
                long={"level":up,"breakout_i":i,"retest_i":None,"retest_count":0}
        else:
            aged=i-long["breakout_i"]
            lev=long["level"]
            if close>lev*1.0001 and long["retest_i"] is not None:
                rows.append({**long,"i":i,"side":1,"age":aged})
                long=None
            elif abs(close-lev)/lev<=0.005:
                long["retest_count"]+=1
                if long["retest_i"] is None:
                    long["retest_i"]=i
            elif aged>5:
                long=None
        if short is None:
            if close<down:
                short={"level":down,"breakout_i":i,"retest_i":None,"retest_count":0}
        else:
            aged=i-short["breakout_i"]
            lev=short["level"]
            if close<lev*.9999 and short["retest_i"] is not None:
                # Author precedence: long event survives a simultaneous short event.
                if not any(x["i"]==i and x["side"]==1 for x in rows[-1:]):
                    rows.append({**short,"i":i,"side":-1,"age":aged})
                short=None
            elif abs(close-lev)/lev<=.005:
                short["retest_count"]+=1
                if short["retest_i"] is None:
                    short["retest_i"]=i
            elif aged>5:
                short=None
    return rows


def p07(repo,df):
    sys.path.insert(0,str(repo/"src"))
    from perplab.strategy.library.pullback_retest import PullbackRetest

    cards=[]
    per_symbol={}
    ages=Counter()
    for sym in SYMBOLS:
        raw=prepare(df,sym,"1h")
        raw["symbol"]=sym
        obj=PullbackRetest()
        frame=obj.indicators(raw)
        original=obj.entry_signal_vectorized(frame)
        replay=p07_instrumented(frame)
        events=[(x["i"],int(x["side"])) for x in replay]
        original_events=[(i,int(v)) for i,v in enumerate(original) if int(v)!=0]
        assert events==original_events, (sym,"native_event_mismatch",events[:10],original_events[:10])
        per_symbol[sym]=len(events)
        for x in replay:
            i=x["i"]; bi=x["breakout_i"];ri=x["retest_i"];side=x["side"]
            age=x["age"];lev=x["level"]
            assert ri is not None and bi<ri<i
            age_class="TIMEOUT_OVERRUN" if age>5 else "IN_TIME"
            ages[age_class]+=1
            # Ex-ante when the SIGNAL candle closes, no future price is needed.
            j=min(i+1,len(frame)-1)
            eprice=float(frame.open.iat[j]) if j>i else None
            rets=frame.iloc[bi+1:i+1]
            low=float(rets.low.min())
            high=float(rets.high.max())
            stop=low if side==1 else high
            # Source is close-only; wick could breach breakout level and retest still passes.
            wick_breach=low<lev if side==1 else high>lev
            # Touching breakout by wick is not enforced in source.
            retest_wick_touch=(float(frame.low.iat[ri])<=lev if side==1 else float(frame.high.iat[ri])>=lev)
            stop_ok=eprice is not None and (stop<eprice if side==1 else stop>eprice)
            target=pivot_target(frame,i,side,eprice)
            target_ok=target is not None
            cards.append({
                "mechanism":"P07","symbol":sym,"side":"LONG" if side==1 else "SHORT",
                "signal_close_utc":source_utc(frame,i),
                "breakout_close_utc":source_utc(frame,bi),
                "first_retest_close_utc":source_utc(frame,ri),
                "signal_close":number(frame.close.iat[i]),
                "next_open_observed_not_advance_guaranteed":number(eprice),
                "breakout_level_prior20":number(lev),
                "bars_breakout_to_signal":age,
                "first_retest_close":number(frame.close.iat[ri]),
                "retest_count":x["retest_count"],
                "wick_crossed_broken_level_in_formation":bool(wick_breach),
                "first_retest_wick_actually_touched_level":bool(retest_wick_touch),
                "entry_native_rule":"REBREAK_AFTER_RETEST_CLOSE_ONLY",
                "sl_source":None,"sl_source_status":"MISSING",
                "sl_adaptation_retest_extreme":number(stop) if stop_ok else None,
                "sl_adaptation_valid_side":bool(stop_ok),
                "tp_source":None,"tp_source_status":"MISSING",
                "tp_adaptation_prior_confirmed_pivot":target if target_ok else None,
                "has_both_adaptation_levels":bool(stop_ok and target_ok),
                "age_status":age_class,
                "local_extremes_since_breakout":{"high":number(high),"low":number(low)},
                "source_receipt":SOURCES["P07"][3],
            })
    cards.sort(key=lambda r:(r["signal_close_utc"],r["symbol"]))
    assert len(cards)==134, ("P07 expected 134",len(cards))
    return {
        "status":"ORIGINAL_134_134_SIGNAL_PARITY_WITH_INDEPENDENT_STATE_TRANSITIONS",
        "total":len(cards), "by_symbol":per_symbol,
        "age_beyond_max5":ages["TIMEOUT_OVERRUN"],
        "wick_breached_level":sum(x["wick_crossed_broken_level_in_formation"] for x in cards),
        "first_retest_no_wick_touch":sum(not x["first_retest_wick_actually_touched_level"] for x in cards),
        "hypothesis_sl_available":sum(x["sl_adaptation_valid_side"] for x in cards),
        "hypothesis_tp_prior_pivot_available":sum(x["tp_adaptation_prior_confirmed_pivot"] is not None for x in cards),
        "both_adaptation_levels":sum(x["has_both_adaptation_levels"] for x in cards),
        "first20":cards[:20],
    }


def p10(repo,df):
    sys.path.insert(0,str(repo/"src"))
    from crypto_trade.backtest_models import Signal
    stub=types.ModuleType("crypto_trade.strategies")
    stub.__path__=[str(repo/"src"/"crypto_trade"/"strategies")]
    stub.NO_SIGNAL=Signal(direction=0,weight=0)
    sys.modules["crypto_trade.strategies"]=stub
    from crypto_trade.strategies.indicator.bb_squeeze import BbSqueezeStrategy

    cards=[]
    per_symbol={}
    for sym in SYMBOLS:
        frame=prepare(df,sym,"1h")
        frame["symbol"]=sym
        obj=BbSqueezeStrategy()
        obj.compute_features(frame)
        native=[int(obj.get_signal(sym,int(t)).direction) for t in frame.open_time]
        # Independent feature construction for explicit source rule verification.
        ma=frame.close.rolling(20,min_periods=20).mean()
        std=frame.close.rolling(20,min_periods=20).std(ddof=0)
        top=ma+2*std;bot=ma-2*std
        bw=((top-bot)/ma).fillna(0)
        prev=bw.shift(1)
        vavg=frame.volume.rolling(10,min_periods=10).mean()
        independently=[]
        for i in range(len(frame)):
            pv=float(prev.iat[i]) if pd.notna(prev.iat[i]) else math.nan
            val=0
            if (math.isfinite(pv) and pv<.02 and float(bw.iat[i])>.02 and
                float(frame.volume.iat[i])>1.5*float(vavg.iat[i])):
                val=(1 if frame.close.iat[i]>ma.iat[i] else
                     -1 if frame.close.iat[i]<ma.iat[i] else 0)
            independently.append(val)
        assert native==independently,(sym,"native_vs_independent_bb_mismatch")
        per_symbol[sym]=sum(x!=0 for x in native)
        for i,signal in enumerate(native):
            if not signal:
                continue
            # These are indicators/measured features, never profit or order returns.
            entry=float(frame.open.iat[i+1]) if i+1<len(frame) else None
            before=frame.iloc[max(0,i-10):i]
            stop=(float(before.low.min()) if signal==1 else float(before.high.max())) if len(before)>=10 else None
            stop_ok=stop is not None and entry is not None and (stop<entry if signal==1 else stop>entry)
            tp=pivot_target(frame,i,signal,entry)
            prior10_bw=bw.iloc[max(0,i-10):i]
            prior10_narrow=int((prior10_bw<.02).sum())
            cards.append({
                "mechanism":"P10","symbol":sym,"side":"LONG" if signal==1 else "SHORT",
                "signal_close_utc":source_utc(frame,i),
                "signal_close":number(frame.close.iat[i]),
                "next_open_observed_not_advance_guaranteed":number(entry),
                "prev_bandwidth_pct":number(float(prev.iat[i])*100,4),
                "now_bandwidth_pct":number(float(bw.iat[i])*100,4),
                "narrow_bars_in_prior10":prior10_narrow,
                "volume_to_10bar_mean":number(frame.volume.iat[i]/vavg.iat[i],4),
                "signal_close_above_upper_bb":bool(frame.close.iat[i]>top.iat[i]),
                "signal_close_below_lower_bb":bool(frame.close.iat[i]<bot.iat[i]),
                "signal_requires_upper_lower_bb_break":False,
                "source_trigger":"BANDWIDTH_CROSSES_2PCT_FROM_BELOW_AND_VOL_GT1_5_AVG_AND_CLOSE_SIDE_OF_MIDDLE",
                "source_same_candle_close_entry_flag":"NON_CAUSAL_FILL_UNDER_FULL_CLOSE_SIGNAL",
                "sl_source_status":"MECHANICAL_2PCT_BACKTEST_NOT_STRUCTURAL",
                "sl_source_level_if_same_close":number(frame.close.iat[i]*(.98 if signal==1 else 1.02)),
                "sl_adaptation_previous10_range":number(stop) if stop_ok else None,
                "sl_adaptation_valid_side":bool(stop_ok),
                "tp_source_status":"MECHANICAL_3PCT_BACKTEST_NOT_STRUCTURAL",
                "tp_source_level_if_same_close":number(frame.close.iat[i]*(1.03 if signal==1 else .97)),
                "tp_adaptation_prior_confirmed_pivot":tp,
                "has_both_adaptation_levels":bool(stop_ok and tp is not None),
                "source_receipt":SOURCES["P10"][3],
            })
    cards.sort(key=lambda r:(r["signal_close_utc"],r["symbol"]))
    assert len(cards)==54,("P10 expected 54",len(cards))
    return {
        "status":"ORIGINAL_54_54_SIGNALS_INDEPENDENT_FEATURE_PARITY_ON_1H_NONDEFAULT_TIMEFRAME",
        "total":len(cards),"by_symbol":per_symbol,
        "actually_closed_outside_bb":sum((c["signal_close_above_upper_bb"] or c["signal_close_below_lower_bb"]) for c in cards),
        "not_outside_bb":sum(not(c["signal_close_above_upper_bb"] or c["signal_close_below_lower_bb"]) for c in cards),
        "only_1_narrow_bar_previous10":sum(c["narrow_bars_in_prior10"]==1 for c in cards),
        "narrow_bars_previous10_mean":number(sum(c["narrow_bars_in_prior10"] for c in cards)/len(cards),4),
        "hypothesis_sl_available":sum(c["sl_adaptation_valid_side"] for c in cards),
        "hypothesis_tp_prior_pivot_available":sum(c["tp_adaptation_prior_confirmed_pivot"] is not None for c in cards),
        "both_adaptation_levels":sum(c["has_both_adaptation_levels"] for c in cards),
        "first20":cards[:20],
    }


def p06(repo,df):
    # Authored Freqtrade strategy code is loaded and exercised unchanged.
    # talib.abstract is REAL native TA-Lib; Freqtrade class/adapters are SHIMS.
    # Never label results as fully native Freqtrade backtesting/parity.
    import talib.abstract as talib_real
    assert "site-packages" in (talib_real.__file__ or "")
    fake_ft=types.ModuleType("freqtrade")
    fake_strategy=types.ModuleType("freqtrade.strategy")
    fake_persistence=types.ModuleType("freqtrade.persistence")
    class Parameter:
        def __init__(self,*args,default=None,**kwargs):
            self.value=default
    class Trade:
        @staticmethod
        def get_trades_proxy(**kwargs):
            return []
    fake_strategy.IntParameter=Parameter
    fake_strategy.DecimalParameter=Parameter
    fake_strategy.BoolParameter=Parameter
    fake_strategy.CategoricalParameter=Parameter
    fake_strategy.IStrategy=type("IStrategy",(),{})
    fake_persistence.Trade=Trade
    sys.modules.update({"freqtrade":fake_ft,"freqtrade.strategy":fake_strategy,"freqtrade.persistence":fake_persistence})
    source=import_source("ftr_real_talib_native_source",repo/SOURCES["P06"][2])
    original=source.FailureToReturnStrategy()
    cards=[]
    gates=Counter()
    partial=[]
    by_symbol={}
    for sym in SYMBOLS:
        raw=prepare(df,sym,"1h")
        frame=raw.copy()
        frame["date"]=pd.to_datetime(frame.open_time,unit="ms",utc=True)
        indicators=original.populate_indicators(frame,{"pair":sym})
        entries=original.populate_entry_trend(indicators.copy(),{"pair":sym})
        long_flags=entries.get("enter_long",pd.Series(0,index=entries.index)).fillna(0).astype(int)
        short_flags=entries.get("enter_short",pd.Series(0,index=entries.index)).fillna(0).astype(int)
        actual=0
        for i in range(len(entries)):
            r=entries.iloc[i]
            level=number(r.impulse_level)
            trend=bool(r.close>r.ema_slow and r.ema_fast>r.ema_slow)
            vol=bool(r.volume>r.volume_sma*original.volume_factor.value and r.volume>0)
            liquid=bool(r.liquid_session)
            volatility=bool(r.atr_ratio>=original.min_atr_ratio.value)
            pullback=bool(r.pullback_recent)
            reengulf=bool(r.reengulf)
            cflag=int(long_flags.iat[i])
            gates["trending_bar"]+=int(trend)
            gates["impulse_bar"]+=int(bool(r.impulse))
            gates["pullback_zone_bar"]+=int(bool(r.pullback_zone))
            gates["pullback_recent_bar"]+=int(pullback)
            gates["reengulf_bar"]+=int(reengulf)
            gates["pullback_and_reengulf"]+=int(pullback and reengulf)
            gates["full_enter_long"]+=cflag
            gates["enter_short_tag_but_can_short_false"]+=int(short_flags.iat[i])
            if cflag:
                actual+=1
                trigger=float(r.close)
                entry=float(raw.open.iat[i+1]) if i+1<len(raw) else None
                lowwin=float(raw.low.iloc[max(0,i-6):i+1].min())
                structural_sl=lowwin if entry is not None and lowwin<entry else None
                tp=pivot_target(raw,i,1,entry)
                card={
                    "mechanism":"P06","symbol":sym,"side":"LONG",
                    "signal_close_utc":source_utc(raw,i),
                    "breakout_level_prior40":level,
                    "signal_close":number(trigger),
                    "next_open_observed_not_advance_guaranteed":number(entry),
                    "atr14_real_talib":number(r.atr),
                    "ema50_real_talib":number(r.ema_fast),
                    "ema200_real_talib":number(r.ema_slow),
                    "volume_to_sma20":number(r.volume/r.volume_sma,4),
                    "original_flags":{"trend":trend,"volume":vol,"volatility":volatility,
                                      "session":liquid,"pullback_recent":pullback,"reengulf":reengulf},
                    "source_sl":"HARD_8PCT_PLUS_TRAILING_FROM_FT",
                    "source_tp":"TIME_DECAY_ROI_4PCT_3PCT_1PCT_AND_EMA_EXIT",
                    "sl_adaptation_pullback_window_extreme":number(structural_sl),
                    "tp_adaptation_prior_confirmed_pivot":tp,
                    "has_both_adaptation_levels":bool(structural_sl is not None and tp is not None),
                    "source_receipt":SOURCES["P06"][3],
                    "parity_warning":"REAL_TALIB_ORIGINAL_CLASS_BUT_FREQTRADE_FRAMEWORK_SHIM"
                }
                cards.append(card)
            elif pullback and reengulf and len(partial)<12:
                blockers=[x for x,v in (("trend",trend),("volume",vol),("volatility",volatility),("session",liquid)) if not v]
                partial.append({"symbol":sym,"signal_close_utc":source_utc(raw,i),
                                "level":level,"why_not_enter":blockers})
        by_symbol[sym]=actual
    cards.sort(key=lambda r:(r["signal_close_utc"],r["symbol"]))
    assert sum(by_symbol.values())==len(cards)
    return {
        "status":"ORIGINAL_CLASS_REAL_TALIB_FREQTRADE_SHIM_NO_FRAMEWORK_PARITY",
        "total":len(cards),"by_symbol":by_symbol,"gates":dict(gates),
        "near_miss_examples":partial,"first20":cards[:20],
        "restriction":"Only LONG is deployable in original: can_short=False, short labels ignored by executor",
        "source_does_not_require_true_engulfing_candle":True,
    }


def main():
    df=pd.read_csv(CSV)
    assert hashlib.sha256(CSV.read_bytes()).hexdigest()=="b885da6dc7e80ea81c7bfb97ec1fb3da615e31824af48625f81cdd376d9a7ee7"
    df["symbol"]=df.symbol.astype(str)
    report={"data_sha256":hashlib.sha256(CSV.read_bytes()).hexdigest(),
            "period":"2026-08-30_to_2026-11-01_UTC_1H_CLOSED_CANDLES_3_SYMBOLS",
            "no_money_economics":True,
            "p07":{},"p10":{},"p06":{}}
    with tempfile.TemporaryDirectory(prefix="ember_mechanism_originals_") as tmp:
        p07repo=clone_and_check(Path(tmp),"P07")
        p10repo=clone_and_check(Path(tmp),"P10")
        report["p07"]=p07(p07repo,df)
        report["p10"]=p10(p10repo,df)
        if "--skip-p06" in sys.argv:
            report["p06"]={"status":"DEPENDENCY_UNAVAILABLE_PY310_TALIB_SOURCE_WHEEL_TIMEOUT",
                           "first20":[],"native_framework_verified":False}
        else:
            p06repo=clone_and_check(Path(tmp),"P06")
            report["p06"]=p06(p06repo,df)
    target=Path(__file__).resolve().parent/"MECHANISM_CARDS_LOCAL.json"
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print("EMBER_MECHANISM_AUDIT="+json.dumps(report,ensure_ascii=False,allow_nan=False))


if __name__=="__main__":
    main()
