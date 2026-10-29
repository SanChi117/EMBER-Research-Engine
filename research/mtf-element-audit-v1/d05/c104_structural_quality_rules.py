"""C104 precommitted causal 4H confirmed swing + 12h FTA reachability, PAPER."""
from decimal import Decimal as D
from collections import Counter
from c91_continuous_causal_route_a_paper import OHLC
import c93_native3m_raid_bos_route_c_research as base
import c102_c103_native3m_new_symbol_transfer as old

class C104QualityError(ValueError):pass
FOUR=4*base.H1

def four_hour(hour):
    if type(hour) is not tuple or len(hour)!=768:
        raise C104QualityError("COMPLETE_32_DAY_H1_REQUIRED")
    out=[]
    for i in range(0,len(hour),4):
        w=hour[i:i+4]
        if len(w)!=4 or w[0].start_ms%FOUR or any(a.close_ms!=b.start_ms for a,b in zip(w,w[1:])):
            raise C104QualityError("UNALIGNED_OR_GAP_4H")
        out.append(OHLC(w[0].start_ms,w[-1].close_ms,w[0].o,
            max(z.h for z in w),min(z.l for z in w),w[-1].c,
            sum((z.v for z in w),D(0))))
    return tuple(out)

def context(rows):
    if type(rows) is not tuple or len(rows)!=15360 or any(
        i and rows[i-1].known_ms!=r.start_ms for i,r in enumerate(rows)):
        raise C104QualityError("INVALID_NATIVE_3M_SOURCE")
    hours=base._aggregate3(rows,base.H1)
    fours=four_hour(hours)
    return hours,fours,base._confirmed(fours,FOUR,rows[-1].known_ms)

def asof_quality(t,hours,fours,swings):
    now=t["entry_ms"]
    if now!=t["bos_close_ms"] or now<=t["raid_closed_ms"]:
        raise C104QualityError("BOS_ENTRY_CAUSAL_CLOCK")
    if t["side"] not in ("LONG","SHORT"):
        raise C104QualityError("INVALID_C93_SIDE")
    e=old.dec(t["entry"]);sl=old.dec(t["stop"]);tp=old.dec(t["target"])
    if not((sl<e<tp) if t["side"]=="LONG" else (tp<e<sl)):
        raise C104QualityError("INVALID_STRUCTURAL_ENTRY_SL_FTA")
    if t["fta_confirmed_ms"]>now:
        raise C104QualityError("FUTURE_1H_FTA")
    h=[z for z in hours if z.close_ms<=now]
    f=[z for z in fours if z.close_ms<=now]
    if len(h)<12 or len(f)<6:raise C104QualityError("ASOF_WARMUP_MISSING")
    h=h[-12:];f=f[-6:]
    if any(x.close_ms>now for x in h+f):
        raise C104QualityError("FUTURE_1H_OR_4H_CANDLE")
    lows=[s for s in swings if s.kind=="LOW" and s.confirmed_ms<=now]
    highs=[s for s in swings if s.kind=="HIGH" and s.confirmed_ms<=now]
    middle=(max(x.h for x in f)+min(x.l for x in f))/D(2)
    htf=((len(lows)>=2 and lows[-1].price>lows[-2].price and f[-1].c>middle)
         if t["side"]=="LONG" else
         (len(highs)>=2 and highs[-1].price<highs[-2].price and f[-1].c<middle))
    hist_range=max(x.h for x in h)-min(x.l for x in h)
    reach=hist_range>0 and abs(tp-e)<=hist_range
    return {"pass":bool(htf and reach),
        "four_hour_direction_ok":bool(htf),
        "fta_12h_range_ok":bool(reach),
        "last_closed_1h_ms":h[-1].close_ms,
        "last_closed_4h_ms":f[-1].close_ms,
        "last_confirmed_4h_low_ms":lows[-1].confirmed_ms if lows else None,
        "last_confirmed_4h_high_ms":highs[-1].confirmed_ms if highs else None,
        "four_hour_midpoint":str(middle),
        "target_distance":str(abs(tp-e)),
        "observed_prior_12h_range":str(hist_range),
        "rejections":([] if htf else ["NO_CAUSAL_4H_SWING_SLOPE_DIRECTION"])+
                     ([] if reach else ["NEAREST_1H_FTA_OUTSIDE_PRIOR_12H_RANGE"])}

def select_symbol(events,require_quality=False):
    chosen=[];busy=0
    for t in sorted(events,key=lambda z:(z["entry_ms"],z["symbol"])):
        if require_quality and not t["preentry_quality"]["pass"]:continue
        if t["entry_ms"]<busy:continue
        chosen.append(t);busy=t["exit_ms"]
    return chosen

def cap_direction(trades):
    active={"LONG":[],"SHORT":[]};chosen=[];blocked=[]
    for t in sorted(trades,key=lambda x:(x["entry_ms"],x["symbol"])):
        side=t["side"]
        if side not in active:raise C104QualityError("UNKNOWN_SIDE")
        now=t["entry_ms"]
        active[side]=[x for x in active[side] if x>now]
        if active[side]:
            blocked.append({"symbol":t["symbol"],"entry_ms":now,"side":side,
                "reason":"ONE_CONCURRENT_DIRECTION_ONLY"})
            continue
        chosen.append(t);active[side].append(t["exit_ms"])
    return chosen,blocked
