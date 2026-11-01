"""EMBER BEHAVIOR-01 · preregistered impulse -> first pullback -> continuation.

DESCRIPTIVE RESEARCH ONLY, NOT AN EXECUTABLE OR PROFITABLE STRATEGY.
The source-native P01/P04/P05/P06/P07/P10 are NOT modified here.
Thresholds are frozen in PREREGISTERED_IMPULSE_FIRST_PULLBACK.md;
do not tune them to this in-sample historical dataset.
All price series are actual Binance USDT-M FUTURES closed candles.
"""
from __future__ import annotations

import bisect
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median

HERE=Path(__file__).resolve().parent
LEGACY=HERE.parent/"source_parity_trace_20261101"/"binance_usdtm_closed_20261101.csv"
LIQ=("BTCUSDT","ETHUSDT","SOLUSDT")
COMP=("STRKUSDT","ZKUSDT","LDOUSDT")
SYMS=LIQ+COMP
TFS=("1h","4h","1d")
MILLISECONDS={"1h":3600000,"4h":14400000,"1d":86400000}
BLOB_SHA={
    str(LEGACY.relative_to(HERE.parents[1])):"39d402392be164be7afee99259c1bf9b64a155e4",
    **{str((HERE/(s+"_4h_3000_binance.csv")).relative_to(HERE.parents[1])):sha
       for s,sha in zip(SYMS,(
           "510a9d3aae653e8766f7288cc7abdf255a21c8ed",
           "688a66f2a9b5577a3365d560fd19352ad83e4592",
           "8f20bed27f745e3a5ec5e92d7ee55c906da11a3e",
           "2a4fc3a9335ce0d8c891ba298cf4c8653f106e74",
           "8370bebfa9bbf28fdba3b5b35ce2f74b1552966f",
           "6dd70c7f6462b3b4b08011c0c2354461e9dad4d0"
       ))},
    **{str((HERE/(s+"_1h_1d_binance.csv")).relative_to(HERE.parents[1])):sha
       for s,sha in zip(COMP,(
           "22ed9fefc2ff567138aa5265bb39fe8cf404b91a",
           "0250b8e73e124fc88543d944e78c45203dd5784d",
           "62e30bd161a205c669edbf2fd7c32261c47a9de0"
       ))}
}
IMPULSE_TR_ATR=1.50
IMPULSE_BODY_FRACTION=.60
IMPULSE_CLOSE_END_FRACTION=.75
PULLBACK_MIN_ATR=.35
PULLBACK_MAX_ATR=1.50
FIRST_PULLBACK_MAX_BARS=6
FUTURE_HORIZONS=(3,6,12)
FRICTION_PCT=(.1,.2,.4)


def blob_read(path):
    data=path.read_bytes()
    name=str(path.relative_to(HERE.parents[1]))
    marker=b"blob "+str(len(data)).encode()+b"\0"+data
    assert hashlib.sha1(marker).hexdigest()==BLOB_SHA[name],name
    return data.decode("utf-8")


def parse_csv(content):
    return list(csv.DictReader(content.splitlines()))


def bar(x):
    return {
        "t":int(x["open_time"]),"end":int(x["close_time"]),
        "o":float(x["open"]),"h":float(x["high"]),"l":float(x["low"]),
        "c":float(x["close"]),"vol":float(x["volume"]),
        "qvol":float(x["quote_volume"]),
    }


def load():
    raw={s:{tf:[] for tf in TFS} for s in SYMS}
    for row in parse_csv(blob_read(LEGACY)):
        raw[row["symbol"]][row["interval"]].append(bar(row))
    for s in SYMS:
        for row in parse_csv(blob_read(HERE/(s+"_4h_3000_binance.csv"))):
            assert row["symbol"]==s and row["interval"]=="4h"
            raw[s]["4h"].append(bar(row))
    for s in COMP:
        for row in parse_csv(blob_read(HERE/(s+"_1h_1d_binance.csv"))):
            assert row["symbol"]==s and row["interval"] in ("1h","1d")
            raw[s][row["interval"]].append(bar(row))
    n={}
    for s in SYMS:
        n[s]={}
        for tf in TFS:
            a=raw[s][tf]
            assert len(a)>=800,(s,tf,len(a))
            gap=MILLISECONDS[tf]
            assert all(a[k+1]["t"]-a[k]["t"]==gap
                       for k in range(len(a)-1)),(s,tf,"gap")
            assert all(b["end"]==b["t"]+gap-1 for b in a),(s,tf)
            assert all(z["l"]<=min(z["o"],z["c"])<=max(z["o"],z["c"])
                       <=z["h"] for z in a),(s,tf)
            n[s][tf]={"count":len(a),"start":a[0]["t"],
                      "end":a[-1]["end"]}
    return raw,n


def actual_tf_parity(raw):
    # Every H4 direct futures kline on overlapping 1h window must
    # exactly reproduce the four standard H1 USDT-M OHLCV bars.
    checked=Counter()
    for s in SYMS:
        h={b["t"]:b for b in raw[s]["1h"]}
        for x in raw[s]["4h"]:
            four=[h.get(x["t"]+j*3600000) for j in range(4)]
            if any(b is None for b in four):continue
            agg={"o":four[0]["o"],"c":four[-1]["c"],
                 "h":max(z["h"] for z in four),
                 "l":min(z["l"] for z in four),
                 "vol":sum(z["vol"] for z in four),
                 "qvol":sum(z["qvol"] for z in four)}
            for k in ("o","h","l","c"):
                assert abs(agg[k]-x[k])<1e-7,(s,x["t"],k,agg[k],x[k])
            assert abs(agg["vol"]-x["vol"])<max(.1,1e-6*x["vol"])
            assert abs(agg["qvol"]-x["qvol"])<max(.2,1e-7*x["qvol"])
            checked[s]+=1
    assert all(checked[s]>=370 for s in SYMS),checked
    return dict(checked)


def last_n_atr(f,i,n=14):
    if i<n+1:return None
    total=0.
    for k in range(i-n,i):
        b=f[k]
        prev=f[k-1]["c"]
        total+=max(b["h"]-b["l"],abs(b["h"]-prev),abs(b["l"]-prev))
    return total/n


def ema_values(f,n):
    factor=2/(n+1)
    out=[]
    for i,b in enumerate(f):
        out.append(b["c"] if i==0 else factor*b["c"]+
                   (1-factor)*out[-1])
    return out


def regime_at(d,ends,ema20,ema50,ms):
    j=bisect.bisect_right(ends,ms)-1
    if j<50:
        return "D1_CONTEXT_NOT_READY"
    close=d[j]["c"]
    if close>ema20[j]>ema50[j]:return "D1_UP"
    if close<ema20[j]<ema50[j]:return "D1_DOWN"
    return "D1_MIXED"


def retest_and_outcome(f,i,side,level,base_atr):
    """First matching CLOSE after impulse. Invalid lookalikes retained."""
    impulse=f[i]
    extreme=impulse["h"] if side==1 else impulse["l"]
    for age in range(1,FIRST_PULLBACK_MAX_BARS+1):
        j=i+age
        if j>=len(f):
            return "RIGHT_CENSORED_BEFORE_PULLBACK",None,None
        x=f[j]
        depth=side*(impulse["c"]-x["c"])/base_atr
        new_extreme=(x["h"]>extreme if side==1 else x["l"]<extreme)
        back_inside=side*(x["c"]-level)<=0
        qualifies=(PULLBACK_MIN_ATR<=depth<=PULLBACK_MAX_ATR
                   and not back_inside)
        if new_extreme and qualifies:
            return "AMBIGUOUS_NEW_EXTREME_SAME_PULLBACK_BAR",j,None
        if new_extreme:
            return "CONTINUATION_NO_FIRST_PULLBACK",j,None
        if back_inside:
            return "BREAKOUT_FAILED_BEFORE_PULLBACK",j,None
        if qualifies:
            return "QUALIFIED_FIRST_PULLBACK",j,{
                "age":age,"depth_atr":depth,
                "wick_penetration_atr":max(0,side*(level-(
                    x["l"] if side==1 else x["h"])))/base_atr,
                "level_clearance_atr":side*(x["c"]-level)/base_atr,
            }
        if depth>PULLBACK_MAX_ATR:
            return "TOO_DEEP_WITHOUT_QUALIFYING_HOLD",j,None
    return "NO_FIRST_PULLBACK_IN_6",i+FIRST_PULLBACK_MAX_BARS,None


def after_signal(f,i,j,side,atr):
    signal=f[j]
    stop=signal["l"] if side==1 else signal["h"]
    impulse_extreme=f[i]["h"] if side==1 else f[i]["l"]
    if j+1>=len(f):
        return {"status":"CENSORED_NO_NEXT_OPEN"}
    entry=f[j+1]["o"]
    if (side*(entry-stop)<=0 or side*(impulse_extreme-entry)<=0):
        invalid_on_open=True
    else:
        invalid_on_open=False
    path=f[j+1:j+1+12]
    outcome="TIME_CENSORED_12"
    event_age=None
    for k,b in enumerate(path,1):
        continuation=(b["h"]>impulse_extreme if side==1 else
                      b["l"]<impulse_extreme)
        invalidation=(b["l"]<stop if side==1 else b["h"]>stop)
        if continuation and invalidation:
            outcome="AMBIGUOUS_SAME_BAR"
            event_age=k
            break
        if continuation:
            outcome="CONTINUATION_BEFORE_INVALIDATION"
            event_age=k
            break
        if invalidation:
            outcome="INVALIDATION_BEFORE_CONTINUATION"
            event_age=k
            break
    if len(path)<12 and outcome=="TIME_CENSORED_12":
        outcome="RIGHT_CENSORED_FUTURE"
    mfe=max((side*((b["h"] if side==1 else b["l"])-entry)
             for b in path),default=0.)/atr
    mae=min((side*((b["l"] if side==1 else b["h"])-entry)
             for b in path),default=0.)/atr
    price_returns={}
    for h in FUTURE_HORIZONS:
        key=str(h)
        if len(path)>=h:
            gross=side*(path[h-1]["c"]-entry)/entry*100
            price_returns[key]={
                "gross_pct":gross,
                "after_hypothetical_friction_pct":{
                    str(c):gross-c for c in FRICTION_PCT},
            }
        else:
            price_returns[key]=None
    return {
        "entry_observed_next_open":entry,
        "original_impulse_extreme":impulse_extreme,
        "pullback_extreme_as_invalidation_reference":stop,
        "entry_gap_beyond_event_geometry":invalid_on_open,
        "status":outcome,
        "event_elapsed_bars":event_age,
        "future_bars_available":len(path),
        "MFE_12_atr":mfe,"MAE_12_atr":mae,
        "fixed_horizon_diagnostic_returns":price_returns,
    }


def detect(f,d,symbol,tf):
    events=[]
    statuses=Counter()
    ends=[x["end"] for x in d]
    e20=ema_values(d,20)
    e50=ema_values(d,50)
    for i in range(35,len(f)):
        z=f[i]
        old=f[i-20:i]
        atr=last_n_atr(f,i)
        if not atr or atr<=0:continue
        height=z["h"]-z["l"]
        if height<=0:continue
        long=(z["c"]>max(x["h"] for x in old))
        short=(z["c"]<min(x["l"] for x in old))
        side=1 if long else -1 if short else 0
        if not side:continue
        directional_body=side*(z["c"]-z["o"])
        if height<IMPULSE_TR_ATR*atr or directional_body/height<IMPULSE_BODY_FRACTION:
            continue
        directional_pos=((z["c"]-z["l"])/height if side==1
                         else (z["h"]-z["c"])/height)
        if directional_pos<IMPULSE_CLOSE_END_FRACTION:
            continue
        level=max(x["h"] for x in old) if side==1 else min(x["l"] for x in old)
        status,j,meta=retest_and_outcome(f,i,side,level,atr)
        statuses[status]+=1
        if status!="QUALIFIED_FIRST_PULLBACK":
            continue
        assert j is not None and meta is not None
        asof=f[j]["end"]
        D=regime_at(d,ends,e20,e50,asof)
        bg="REGIME_ALIGNED" if (
            (D=="D1_UP" and side==1) or (D=="D1_DOWN" and side==-1)
        ) else "REGIME_OPPOSED" if (
            (D=="D1_DOWN" and side==1) or (D=="D1_UP" and side==-1)
        ) else "REGIME_MIXED"
        prev_volume=sum(x["vol"] for x in old)/20
        prior_move=side*(f[i-1]["c"]-f[i-20]["o"])/atr
        detail={
            "id":symbol+"-"+tf+"-"+str(z["t"])+"-"+(
                "L" if side==1 else "S"),
            "symbol":symbol,"group":"CORE" if symbol in LIQ else "ALT_COMPARATOR",
            "tf":tf,"side":"LONG" if side==1 else "SHORT",
            "impulse_i":i,"pullback_i":j,
            "impulse_close_ms":z["end"],
            "signal_close_ms":asof,
            "break_level":level,
            "signal_close":f[j]["c"],
            "base_atr":atr,
            "pre_entry_features":{
                "time_to_first_pullback_bars":meta["age"],
                "pullback_depth_ATR":meta["depth_atr"],
                "wick_beyond_break_level_ATR":meta["wick_penetration_atr"],
                "hold_clearance_ATR":meta["level_clearance_atr"],
                "impulse_body_ATR":directional_body/atr,
                "impulse_true_range_ATR":height/atr,
                "impulse_volume_multiple_prior20":(
                    z["vol"]/prev_volume if prev_volume else None),
                "preimpulse_20bar_directional_move_ATR":prior_move,
                "ATR_percent_preimpulse":100*atr/f[i-1]["c"],
                "quote_volume_median_prev20":median(x["qvol"] for x in old),
                "day_regime_as_of_signal":D,
                "day_regime_alignment":bg,
            },
            "price_path":after_signal(f,i,j,side,atr),
        }
        events.append(detail)
    return events,dict(statuses)


def round_or_none(x):
    return round(x,6) if x is not None else None


def summary_group(events,observed_bars,group_key):
    result={}
    per_month=observed_bars/(24 if group_key=="1h" else 6 if group_key=="4h"
                              else 1)/30.4375
    states=Counter(e["price_path"]["status"] for e in events)
    valid=[e for e in events if e["price_path"]["status"] not in (
        "CENSORED_NO_NEXT_OPEN","RIGHT_CENSORED_FUTURE")]
    valid_struct=[e for e in events if e["price_path"]["status"] in (
        "CONTINUATION_BEFORE_INVALIDATION",
        "INVALIDATION_BEFORE_CONTINUATION")]
    def ret(h,friction=None):
        vals=[]
        for e in valid:
            path=e["price_path"]["fixed_horizon_diagnostic_returns"].get(str(h))
            if path is not None:
                vals.append(path["gross_pct"] if friction is None
                            else path["after_hypothetical_friction_pct"][str(friction)])
        return vals
    result={
        "n":len(events),
        "n_events_per_symbol_month":round_or_none(
            len(events)/per_month) if per_month else None,
        "structural_outcomes":dict(states),
        "resolved_continuation_share":round_or_none(
            states["CONTINUATION_BEFORE_INVALIDATION"]/len(valid_struct)
            if valid_struct else None),
        "resolved_count":len(valid_struct),
        "median_MFE12_ATR":round_or_none(median(
            [e["price_path"]["MFE_12_atr"] for e in valid])
            if valid else None),
        "median_MAE12_ATR":round_or_none(median(
            [e["price_path"]["MAE_12_atr"] for e in valid])
            if valid else None),
        "hypothetical_fixed_horizon":{
            str(h):{
                "n":len(ret(h)),
                "mean_gross_pct":round_or_none(mean(ret(h)) if ret(h) else None),
                "median_gross_pct":round_or_none(median(ret(h)) if ret(h) else None),
                "mean_0.2pct_friction_pct":round_or_none(
                    mean(ret(h,.2)) if ret(h,.2) else None),
                "gross_positive_count":sum(x>0 for x in ret(h)),
            } for h in FUTURE_HORIZONS},
        "D1_direction_class":dict(Counter(
            e["pre_entry_features"]["day_regime_alignment"] for e in events)),
    }
    return result


def run():
    raw,meta=load()
    parity=actual_tf_parity(raw)
    rows=[]
    count={}
    for s in SYMS:
        count[s]={}
        for tf in TFS:
            ev,states=detect(raw[s][tf],raw[s]["1d"],s,tf)
            rows.extend(ev)
            count[s][tf]={
                "impulse_candidate_funnel":states,
                "events":summary_group(ev,len(raw[s][tf]),tf),
            }
    per_tf={}
    for tf in TFS:
        for name,coins in (("CORE",LIQ),("ALT_COMPARATOR",COMP)):
            pool=[e for e in rows if e["tf"]==tf and e["symbol"] in coins]
            observed=sum(len(raw[s][tf]) for s in coins)
            per_tf[tf+"_"+name]=summary_group(pool,observed,tf)
    split={}
    for tf in TFS:
        f=[e for e in rows if e["tf"]==tf]
        split[tf]={
            "years":dict(Counter(str(__import__("datetime").datetime.fromtimestamp(
                e["signal_close_ms"]/1000,__import__("datetime").timezone.utc).year)
                for e in f)),
            "liquid_main":sum(e["group"]=="CORE" for e in f),
            "comparator":sum(e["group"]=="ALT_COMPARATOR" for e in f),
        }
    likeness={}
    for feat in ("day_regime_alignment",):
        likeness[feat]={}
        for cls in ("REGIME_ALIGNED","REGIME_OPPOSED","REGIME_MIXED"):
            v=[e for e in rows if e["pre_entry_features"][feat]==cls]
            st=Counter(e["price_path"]["status"] for e in v)
            likeness[feat][cls]={"count":len(v),"outcomes":dict(st)}
    # Fixed time reference comparison; no cherry picked TF periods.
    threshold=1788098400000
    same_date={}
    for tf in TFS:
        for group,coins in (("CORE",LIQ),("ALT_COMPARATOR",COMP)):
            v=[e for e in rows if e["tf"]==tf and e["symbol"] in coins
               and e["signal_close_ms"]>=threshold]
            same_date[tf+"_"+group]={
                "events":len(v),
                "states":dict(Counter(e["price_path"]["status"] for e in v)),
            }
    return {
        "study":"BEHAVIOR01_PREREGISTERED_FIRST_PULLBACK",
        "status":"DESCRIPTIVE_EVENT_STUDY_NO_VERIFIED_EDGE",
        "raw_source_blob_sha":BLOB_SHA,
        "series":meta,
        "H4_H1_cross_venue_exact_OHLCV_parity":parity,
        "universes":{"CORE":LIQ,"ALT_COMPARATOR":COMP},
        "event_logic":"breakout 20-bar + range >=1.5 prior ATR + body >=60% + extreme close >=75%; first close-based pullback 0.35-1.5ATR in six bars without reentry or new impulse extreme; no fitted filters",
        "per_symbol_tf":count,
        "per_tf_universe_summary":per_tf,
        "same_last_62d_calendar_comparison":same_date,
        "event_calendar_years_by_tf":split,
        "pre_entry_d1_regime_lookalikes":likeness,
        "total_impulses":sum(sum(v["impulse_candidate_funnel"].values())
                              for s in count.values() for v in s.values()),
        "total_qualifying_first_pullbacks":len(rows),
        "all_qualifying_events":rows,
        "cautions":"Descriptive lookalike audit, not source-native P01/P04/P05/P06/P07/P10 strategy parity; fixed-time exit diagnostics are not executed TP, the wick boundary is not a validated stop, 0.1/0.2/0.4% roundtrip friction is hypothetical and excludes funding/slippage/mark-price execution. Historical events overlap; no de-duplication. Different TF periods and small OOS samples limit conclusions. Comparator alt selection is exploratory and may have survivorship bias.",
    }


if __name__=="__main__":
    print("EMBER_BEHAVIOR01_RESULT="+json.dumps(
        run(),ensure_ascii=False,allow_nan=False,separators=(",",":")))
