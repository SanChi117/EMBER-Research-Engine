"""C20B2: lower-timeframe 5m swing-close following a confirmed 1h wick.

The 5m break is only a research geometric witness, NOT independently
author-labelled BOS. No nearest-parent rule, TTL, session substitution,
quote, position sizing, fill, or live orders.
"""
from dataclasses import dataclass
from decimal import Decimal
from c20_original_32day_native5m_lineage import C20NativeSourceLineage,FIVE,SEPT_START
from c20b_hourly_fractal_source_observer import (
    closed_hourly,observe_fractals_and_first_breach,HourFractal,
    FirstWickObservation)

@dataclass(frozen=True)
class FiveMinuteSwing:
    kind:str
    level:Decimal
    origin_ms:int
    known_ms:int
    source_ids:tuple[str,str,str]

@dataclass(frozen=True)
class CloseBreakWitness:
    raid_pivot:HourFractal
    raid:FirstWickObservation
    swing:FiveMinuteSwing
    side:str
    start_ms:int
    known_ms:int
    close:Decimal
    source_row_id:str
    status:str="RESEARCH_ONLY_CLOSED_5M_STRUCTURE_BREAK_NOT_AUTHOR_BOS"

@dataclass(frozen=True)
class CrossTimeframeObservation:
    symbol:str
    as_of_ms:int
    native5m_bars:int
    closed1h_bars:int
    hourly_fractal_count:int
    hourly_first_clean_wick_count:int
    five_minute_swing_count:int
    potential_bos_witnesses:tuple[CloseBreakWitness,...]
    author_status:str="AUTHOR_GOLDEN_SOURCE_UNAVAILABLE"
    readiness:str="NOT_TRADE_READY"
    author_approved_bos:int=0
    author_approved_trades:int=0
    missing_context:str="NO_AUTHOR_FUTURES_GOLDEN_OR_SESSION_FRESHNESS_FTA_CERTIFICATION"
    research_assumption:str="5M_FIRST_CLOSED_CROSS_BEYOND_LATEST_PREKNOWN_STRICT_3BAR_SWING"

def _swings(native):
    swings=[]
    for i in range(1,len(native)-1):
        a,b,c=native[i-1:i+2]
        for kind,valid,level in (
            ("HIGH",b.high>a.high and b.high>c.high,b.high),
            ("LOW",b.low<a.low and b.low<c.low,b.low)):
            if valid:
                swings.append(FiveMinuteSwing(kind,level,b.start_ms,c.known_at_ms,
                           (a.origin_raw_row_id,b.origin_raw_row_id,c.origin_raw_row_id)))
    return tuple(swings)

def cross_timeframe_raid_break(line:C20NativeSourceLineage,*,as_of_ms:int)->CrossTimeframeObservation:
    hours=closed_hourly(line,as_of_ms)
    count=(as_of_ms-SEPT_START)//FIVE
    rows=line.original_5m_closed[:count]
    p,raids=observe_fractals_and_first_breach(hours)
    swings=_swings(rows)
    events=[]
    for raid in raids:
        if raid.confirmed_at_ms is None:continue
        kind="LOW" if raid.fractal.kind=="BSL" else "HIGH"
        side="SHORT" if kind=="LOW" else "LONG"
        eligible=[s for s in swings if s.kind==kind and
             s.origin_ms>=raid.first_breach_ms and
             s.known_ms>=raid.first_breach_close_ms and
             (s.level<raid.fractal.level if side=="SHORT" else s.level>raid.fractal.level)]
        if not eligible:continue
        index=0;last=None
        start=(raid.confirmed_at_ms-SEPT_START)//FIVE
        for i in range(start,len(rows)):
            candle=rows[i]
            # A later 5m sweep beyond the 1h raid wick extreme invalidates
            # the temporal geometric witness instead of being ignored.
            if ((side=="SHORT" and candle.high>raid.extreme) or
                (side=="LONG" and candle.low<raid.extreme)):
                break
            while index<len(eligible) and eligible[index].known_ms<=candle.start_ms:
                last=eligible[index]
                index+=1
            if last is None:continue
            prev=rows[i-1].close
            crossed=(candle.close<last.level and prev>=last.level if side=="SHORT"
                     else candle.close>last.level and prev<=last.level)
            if not crossed:continue
            events.append(CloseBreakWitness(raid.fractal,raid,last,side,
                          candle.start_ms,candle.known_at_ms,candle.close,
                          candle.origin_raw_row_id))
            break
    return CrossTimeframeObservation(
        line.symbol,as_of_ms,len(rows),len(hours),len(p),
        sum(r.confirmed_at_ms is not None for r in raids),len(swings),tuple(events))
