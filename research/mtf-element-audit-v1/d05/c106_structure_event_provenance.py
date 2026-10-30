"""C106 independent closed-candle market-structure event-time research contract.

Concept-level synthesis informed by user-provided LuxAlgo SMC source,
SHA256 1802a78cc696206651c1700e92bd03ed4d873374943f4c7ec75be94b7d5b5cf0.
NO copied Pine implementation, NO orders or trading policy changes, PAPER ONLY.
"""
from dataclasses import dataclass
from decimal import Decimal as D

class TemporalStructureError(ValueError):pass
H4=4*3600000
H1=3600000
M15=15*60000
VALID_TF=(M15,H1,H4)

@dataclass(frozen=True)
class Candle:
    start_ms:int
    close_ms:int
    o:D
    h:D
    l:D
    c:D

@dataclass(frozen=True)
class StructureEvent:
    tf_ms:int
    kind:str
    side:str
    level:D
    pivot_bar_closed_ms:int
    confirmed_at_ms:int
    available_at_ms:int

@dataclass(frozen=True)
class GapEvent:
    tf_ms:int
    side:str
    low:D
    high:D
    available_at_ms:int

@dataclass(frozen=True)
class BreakEvent:
    tf_ms:int
    side:str
    kind:str
    level:D
    crossed_at_ms:int
    source_confirmed_at_ms:int

def checked(bars,tf,asof):
    if tf not in VALID_TF or type(asof) is not int or asof<0:
        raise TemporalStructureError("UNREGISTERED_TIMEFRAME_OR_CLOCK")
    if type(bars) is not tuple or not bars:
        raise TemporalStructureError("CLOSED_TYPED_CANDLES_REQUIRED")
    for i,x in enumerate(bars):
        if type(x) is not Candle or not all(type(v) is D and v.is_finite() for v in (x.o,x.h,x.l,x.c)):
            raise TemporalStructureError("ONLY_FINITE_TYPED_CANDLES")
        if x.start_ms%tf or x.close_ms!=x.start_ms+tf or x.close_ms>asof:
            raise TemporalStructureError("PARTIAL_UNCLOSED_OR_FUTURE_BAR")
        if not (D(0)<x.l<=min(x.o,x.c)<=max(x.o,x.c)<=x.h):
            raise TemporalStructureError("INVALID_ORIGINAL_OHLC")
        if i and bars[i-1].close_ms!=x.start_ms:
            raise TemporalStructureError("CANDLE_CLOCK_GAP")
    return bars

def confirmed_swings(bars,tf,asof,left=2,right=2):
    checked(bars,tf,asof)
    if (type(left) is not int or type(right) is not int or left<1 or right<1 or
        left>8 or right>8):
        raise TemporalStructureError("UNREGISTERED_SWING_CONFIRMATION")
    out=[]
    for i in range(left,len(bars)-right):
        z=bars[i];l=bars[i-left:i];r=bars[i+1:i+right+1]
        available=r[-1].close_ms
        if available>asof:continue
        if all(z.h>x.h for x in l) and all(z.h>=x.h for x in r):
            out.append(StructureEvent(tf,"HIGH","BEARISH",z.h,
                z.close_ms,available,available))
        if all(z.l<x.l for x in l) and all(z.l<=x.l for x in r):
            out.append(StructureEvent(tf,"LOW","BULLISH",z.l,
                z.close_ms,available,available))
    return tuple(out)

def gap_from_three(closed,tf,asof):
    checked(closed,tf,asof)
    if len(closed)!=3:raise TemporalStructureError("THREE_FULLY_CLOSED_REQUIRED")
    a,_,z=closed
    if z.l>a.h:
        return GapEvent(tf,"LONG",a.h,z.l,z.close_ms)
    if z.h<a.l:
        return GapEvent(tf,"SHORT",z.h,a.l,z.close_ms)
    return None

def classify_completed_break(level,previous,current,prior_trend,asof):
    """One completed close crossing one already available confirmed pivot.
    Independent event semantics, NOT a copied LuxAlgo stateful implementation.
    """
    if type(level) is not StructureEvent or prior_trend not in (-1,0,1):
        raise TemporalStructureError("CONFIRMED_PIVOT_AND_TREND_REQUIRED")
    checked((previous,current),level.tf_ms,asof)
    if level.available_at_ms>current.start_ms:
        raise TemporalStructureError("LEVEL_NOT_KNOWN_BEFORE_BREAK_BAR")
    if level.confirmed_at_ms<level.pivot_bar_closed_ms or level.available_at_ms<level.confirmed_at_ms:
        raise TemporalStructureError("BACKDATED_OR_FUTURE_PIVOT")
    if level.kind=="HIGH":
        direction=1
        crossed=previous.c<=level.level and current.c>level.level
        side="BULLISH"
    elif level.kind=="LOW":
        direction=-1
        crossed=previous.c>=level.level and current.c<level.level
        side="BEARISH"
    else:
        raise TemporalStructureError("UNKNOWN_PIVOT_TYPE")
    if not crossed:return None
    return BreakEvent(level.tf_ms,side,("CHoCH" if prior_trend==-direction else "BOS"),
                      level.level,current.close_ms,level.confirmed_at_ms)

def check_parent_hierarchy(trade):
    """Only an assertion on C105 witness; never alters its signals or stops."""
    if type(trade) is not dict:
        raise TemporalStructureError("C105_TRADE_REQUIRED")
    if not (trade.get("parent_tf")=="4H" and
        trade.get("stop_source_tf")=="4H" and
        trade.get("target_source_tf")=="4H" and
        trade.get("pad_source")=="ATR_FULLY_CLOSED_4H" and
        trade.get("stop_source")=="4H_FVG_FAR_EDGE" and
        trade.get("target_source")=="4H_UNCONSUMED_CONFIRMED_PIVOT"):
        raise TemporalStructureError("NON_4H_EXIT_PARENT")
    clock=("zone_created_ms","first_4h_poi_touch_ms",
           "one_hour_rejection_close_ms","fifteen_minute_vc_close_ms","entry_ms")
    if any(type(trade.get(k)) is not int for k in clock):
        raise TemporalStructureError("PARENT_CAUSAL_CLOCK_MISSING")
    values=[trade[k] for k in clock]
    if not (values[0]<values[1]<values[2]<values[3]==values[4]):
        raise TemporalStructureError("PARENT_CAUSAL_ORDER_BROKEN")
    if type(trade.get("fta_confirmed_ms")) is not int or trade["fta_confirmed_ms"]>trade["entry_ms"]:
        raise TemporalStructureError("FUTURE_OR_UNKNOWN_4H_FTA")
    return True
