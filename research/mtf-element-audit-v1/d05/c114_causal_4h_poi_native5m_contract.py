#!/usr/bin/env python3
"""C114-A: as-of causal market geometry contracts. PAPER ONLY. No prices fetched.

Never resample 3m into 5m: ORIGINAL native5m must arrive with checked source.
Not a strategy or claim of economic alpha. Not a C109 extension.
"""
from dataclasses import dataclass
from decimal import Decimal as D
from bisect import bisect_right

MINUTE=60000
M3=3*MINUTE
M5=5*MINUTE
H4=4*60*MINUTE
D1=24*60*MINUTE
SIX_H=6*60*MINUTE

class SourceError(ValueError):pass

@dataclass(frozen=True)
class Candle:
    start_ms:int
    known_ms:int
    o:D
    h:D
    l:D
    c:D
    source_tf_ms:int
    def __post_init__(self):
        if self.source_tf_ms not in (M3,M5,H4,D1):raise SourceError("UNKNOWN_ORIGINAL_TIMEFRAME")
        if self.known_ms-self.start_ms!=self.source_tf_ms:raise SourceError("MALFORMED_CLOSE_TIMESTAMP")
        if self.start_ms%self.source_tf_ms:raise SourceError("NOT_UTC_NATIVE_ALIGNMENT")
        if min(self.o,self.h,self.l,self.c)<=0 or self.h<max(self.o,self.c) or self.l>min(self.o,self.c):raise SourceError("MALFORMED_OHLC")

@dataclass(frozen=True)
class Pivot:
    kind:str
    pivot_ms:int
    confirmed_ms:int
    price:D

@dataclass(frozen=True)
class POI:
    side:str
    lower:D
    upper:D
    created_ms:int
    parent_id:str
    def __post_init__(self):
        if self.side not in ("LONG","SHORT") or not 0<self.lower<self.upper:raise SourceError("INVALID_4H_PARENT")

def strict_native(rows,tf,begin_ms,end_ms):
    """Prove uninterrupted exchange-native clock; no synthetic timezone shifts."""
    if not rows or begin_ms>=end_ms or begin_ms%tf or end_ms%tf:raise SourceError("BAD_SOURCE_INTERVAL")
    if len(rows)!=(end_ms-begin_ms)//tf:raise SourceError("INCOMPLETE_NATIVE_SOURCE")
    if rows[0].start_ms!=begin_ms or rows[-1].known_ms!=end_ms:raise SourceError("BOUNDARY_MISMATCH")
    for i,r in enumerate(rows):
        if r.source_tf_ms!=tf or r.start_ms!=begin_ms+i*tf:raise SourceError("CLOCK_GAP_DUPLICATE_OR_WRONG_TF")
    return True

def strict_cross_native(original3,original5,begin_ms,end_ms):
    if original3 is original5:raise SourceError("SAME_SOURCE_OBJECT")
    strict_native(original3,M3,begin_ms,end_ms)
    strict_native(original5,M5,begin_ms,end_ms)
    if len(original3)*3!=len(original5)*5:raise SourceError("MISMATCH_NATIVE_3M_5M")
    # OHLC aggregated independently to shared 15m boundary: identical prices,
    # not a forbidden 3m -> 5m substitution.
    for offset in range(0,len(original3),5):
        k=offset//5
        a=original3[offset:offset+5]
        b=original5[3*k:3*k+3]
        if (a[0].o!=b[0].o or a[-1].c!=b[-1].c or
            max(x.h for x in a)!=max(x.h for x in b) or
            min(x.l for x in a)!=min(x.l for x in b)):
            raise SourceError("CROSS_NATIVE_15M_OHLC_DISAGREEMENT")
    return True

def closed_pivots(candles,asof,side_bars=2):
    if side_bars!=2:raise SourceError("PIVOT_SCHEMA_CHANGED")
    visible=[c for c in candles if c.known_ms<=asof]
    out=[]
    for i in range(side_bars,len(visible)-side_bars):
        z=visible[i-side_bars:i+side_bars+1]
        x=z[side_bars]
        if x.h>max(t.h for j,t in enumerate(z) if j!=side_bars):
            out.append(Pivot("H",x.start_ms,z[-1].known_ms,x.h))
        if x.l<min(t.l for j,t in enumerate(z) if j!=side_bars):
            out.append(Pivot("L",x.start_ms,z[-1].known_ms,x.l))
    return tuple(out)

def bearish_structure_before_touch(pivots,touch_ms):
    lows=[p for p in pivots if p.kind=="L" and p.confirmed_ms<=touch_ms]
    highs=[p for p in pivots if p.kind=="H" and p.confirmed_ms<=touch_ms]
    if len(lows)<2 or len(highs)<2:return None
    if not (lows[-1].price<lows[-2].price and highs[-1].price<highs[-2].price):
        return None
    return highs[-1]

def bullish_structure_before_touch(pivots,touch_ms):
    lows=[p for p in pivots if p.kind=="L" and p.confirmed_ms<=touch_ms]
    highs=[p for p in pivots if p.kind=="H" and p.confirmed_ms<=touch_ms]
    if len(lows)<2 or len(highs)<2:return None
    if not (lows[-1].price>lows[-2].price and highs[-1].price>highs[-2].price):
        return None
    return lows[-1]

def choch_after_touch(poi,touch_ms,native5,pivots,landmark_ms):
    """Frozen pre-touch structure, only post-touch fully closed actual native5m."""
    if poi.created_ms>touch_ms or landmark_ms!=touch_ms+SIX_H:
        raise SourceError("BAD_4H_FIRST_TOUCH_OR_LANDMARK")
    if poi.side=="LONG":
        ref=bearish_structure_before_touch(pivots,touch_ms)
    else:
        ref=bullish_structure_before_touch(pivots,touch_ms)
    if ref is None:return None,"NO_PRETOUCH_STRUCTURAL_SOURCE"
    for c in native5:
        if c.source_tf_ms!=M5:raise SourceError("FALSE_NATIVE5")
        if c.known_ms<=touch_ms or c.known_ms>landmark_ms:continue
        if ref.confirmed_ms>touch_ms:raise SourceError("PIVOT_LOOKAHEAD")
        if poi.side=="LONG" and c.c>ref.price and c.c>c.o:
            return c.known_ms,"CONFIRMED_CHoCH"
        if poi.side=="SHORT" and c.c<ref.price and c.c<c.o:
            return c.known_ms,"CONFIRMED_CHoCH"
    return None,"NO_CHoCH_BY_LANDMARK"

def landmark_3m_open(native3,landmark_ms):
    if landmark_ms%M3:raise SourceError("LANDMARK_NOT_NATIVE3_ALIGNED")
    starts=[c.start_ms for c in native3]
    i=bisect_right(starts,landmark_ms)-1
    if i<0 or starts[i]!=landmark_ms:raise SourceError("NO_NEXT_3M_OPEN_AT_LANDMARK")
    if native3[i].source_tf_ms!=M3:raise SourceError("FALSE_NATIVE3")
    return native3[i].o

def h4_fvg(last_three):
    if len(last_three)!=3:raise SourceError("THREE_CLOSED_4H_REQUIRED")
    a,b,c=last_three
    if any(z.source_tf_ms!=H4 for z in last_three) or a.known_ms!=b.start_ms or b.known_ms!=c.start_ms:
        raise SourceError("BAD_4H_FORMATION_CLOCK")
    if a.h<c.l:
        return POI("LONG",a.h,c.l,c.known_ms,"LONG:"+str(c.known_ms)+":"+str(a.h)+":"+str(c.l))
    if a.l>c.h:
        return POI("SHORT",c.h,a.l,c.known_ms,"SHORT:"+str(c.known_ms)+":"+str(c.h)+":"+str(a.l))
    return None

def first_touch_asof(poi,original3,asof):
    if asof<poi.created_ms:raise SourceError("PRE_CREATION_LOOKAHEAD")
    for c in original3:
        if c.source_tf_ms!=M3:raise SourceError("FALSE_NATIVE3")
        if c.start_ms<poi.created_ms or c.known_ms>asof:continue
        if c.start_ms>=poi.created_ms+48*60*MINUTE:return None
        if c.h>=poi.lower and c.l<=poi.upper:
            return c.known_ms
    return None

def premium_discount(known_pivots,asof,price):
    """Do not fabricate a current dealing range without *known* opposing extremes."""
    visible=[p for p in known_pivots if p.confirmed_ms<=asof]
    highs=[p for p in visible if p.kind=="H"]
    lows=[p for p in visible if p.kind=="L"]
    if not highs or not lows:return "NO_RANGE",None
    hi,lo=highs[-1],lows[-1]
    if hi.price<=lo.price:return "NO_RANGE",None
    mid=(hi.price+lo.price)/2
    return ("DISCOUNT" if price<mid else "PREMIUM" if price>mid else "EQUILIBRIUM"),(lo.price,hi.price)
