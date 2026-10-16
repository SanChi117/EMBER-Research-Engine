"""C20B1 source observation: closed 1h fractal and first wick-only sweep.

Research geometry only; no author-labelled entry or trade authorisation.
One-hour bars are exact 12x5m Decimal OHLCV aggregates. Any raid is
known only after the following full 1h confirmation bar closes.
"""
from dataclasses import dataclass
from decimal import Decimal
from c20_original_32day_native5m_lineage import C20NativeSourceLineage,FIVE,SEPT_START,END

HOUR=3600000
@dataclass(frozen=True)
class HourSource:
    start_ms:int
    close_ms:int
    open:Decimal
    high:Decimal
    low:Decimal
    close:Decimal
    native_rows:tuple[str,...]

@dataclass(frozen=True)
class HourFractal:
    kind:str
    level:Decimal
    center_ms:int
    known_ms:int
    source_rows:tuple[str,...]

@dataclass(frozen=True)
class FirstWickObservation:
    fractal:HourFractal
    first_breach_ms:int|None
    first_breach_close_ms:int|None
    confirmed_at_ms:int|None
    extreme:Decimal|None
    verdict:str

def closed_hourly(line:C20NativeSourceLineage,as_of_ms:int)->tuple[HourSource,...]:
    if not isinstance(line,C20NativeSourceLineage):
        raise ValueError("REQUIRES_C20A_NATIVE_5M_LINEAGE")
    if (line.readiness!="NOT_TRADE_READY" or
        line.author_source_status!="AUTHOR_GOLDEN_SOURCE_UNAVAILABLE" or
        line.bos_status!="BOS_5M_NOT_YET_AUTHOR_CERTIFIED" or
        line.original_15m_equalities!=3072 or
        line.verified_original_1d_equalities!=32 or
        len(line.source_zip_shas)!=3):
        raise ValueError("FORGED_C20A_SOURCE_APPROVAL")
    if (type(as_of_ms)!=int or as_of_ms%FIVE or as_of_ms<SEPT_START or
        as_of_ms>line.as_of_ms or line.as_of_ms>END):
        raise ValueError("FUTURE_OR_UNCLOSED_FIVE_MINUTE_ASOF")
    rows=line.original_5m_closed
    if (not isinstance(rows,tuple) or not rows or len(rows)>9216 or
        line.as_of_ms!=SEPT_START+len(rows)*FIVE):
        raise ValueError("NOT_A_CONTIGUOUS_NATIVE_FIVE_MINUTE_PREFIX")
    for i,b in enumerate(rows):
        if (b.start_ms!=SEPT_START+i*FIVE or b.known_at_ms!=b.start_ms+FIVE or
            b.origin_raw_row_id!=b.origin_zip_sha256+":"+str(b.start_ms) or
            b.origin_zip_sha256!=line.source_zip_shas[0 if i<8640 else 1 if i<8928 else 2] or
            not all(isinstance(x,Decimal) and x.is_finite() for x in
                    (b.open,b.high,b.low,b.close,b.volume)) or
            not (0<b.low<=min(b.open,b.close)<=max(b.open,b.close)<=b.high)):
            raise ValueError("CORRUPTED_FIVE_MINUTE_SOURCE_ROW")
    current=rows[:(as_of_ms-SEPT_START)//FIVE]
    result=[]
    for i in range(0,len(current)//12*12,12):
        twelve=current[i:i+12]
        result.append(HourSource(twelve[0].start_ms,twelve[-1].known_at_ms,
            twelve[0].open,max(x.high for x in twelve),
            min(x.low for x in twelve),twelve[-1].close,
            tuple(x.origin_raw_row_id for x in twelve)))
    return tuple(result)

def observe_fractals_and_first_breach(hours:tuple[HourSource,...]):
    pivots=[]
    observed=[]
    for i in range(1,len(hours)-1):
        before,center,after=hours[i-1:i+2]
        for kind,formed,level in (
            ("BSL",center.high>before.high and center.high>after.high,center.high),
            ("SSL",center.low<before.low and center.low<after.low,center.low)):
            if not formed:continue
            pivot=HourFractal(kind,level,center.start_ms,after.close_ms,
                              before.native_rows+center.native_rows+after.native_rows)
            pivots.append(pivot)
            first=next((j for j in range(i+2,len(hours)) if
                        (hours[j].high>level if kind=="BSL" else hours[j].low<level)),None)
            if first is None:
                observed.append(FirstWickObservation(pivot,None,None,None,None,"NO_FIRST_BREACH"))
                continue
            raid=hours[first]
            clean=(max(raid.open,raid.close)<=level if kind=="BSL"
                   else min(raid.open,raid.close)>=level)
            if not clean:
                state="FIRST_BREACH_BODY";confirmed=None
            elif first==len(hours)-1:
                state="WICK_NEEDS_FOLLOWING_CLOSED_HOUR";confirmed=None
            else:
                previous,nxt=hours[first-1],hours[first+1]
                fractal=(raid.high>previous.high and raid.high>nxt.high
                         if kind=="BSL" else raid.low<previous.low and raid.low<nxt.low)
                confirmed=nxt.close_ms if fractal else None
                state="WICK_FRACTAL_GEOMETRY" if fractal else "WICK_NONFRACTAL"
            observed.append(FirstWickObservation(
                pivot,raid.start_ms,raid.close_ms,confirmed,
                raid.high if kind=="BSL" else raid.low,state))
    return tuple(pivots),tuple(observed)
