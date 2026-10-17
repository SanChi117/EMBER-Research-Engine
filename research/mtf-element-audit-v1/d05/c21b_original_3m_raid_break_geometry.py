"""C21B original 3m source-derived 1H wick raid -> later 3m close break.

Author original: 1H fractal raid and 3m BOS are distinct requirements;
a strict 3-bar 3m swing + first *closed* cross are explicitly research
operationalizations, NOT author annotated BOS or executable entry.
The following closed 1H confirmation is required (no future). PAPER ONLY.
"""
from dataclasses import dataclass
from decimal import Decimal
import re
from c21_native3m_source_bridge import C21Native3mResult,Original3mRow,THREE,SEPT_START,END
from c20b_hourly_fractal_source_observer import (
    HourSource,observe_fractals_and_first_breach)

HOUR=3600000
@dataclass(frozen=True)
class ThreeSwing:
    kind:str
    level:Decimal
    center_ms:int
    known_ms:int
    native3m_ids:tuple[str,str,str]

@dataclass(frozen=True)
class ThreeBreak:
    pivot_kind:str
    pivot_center_ms:int
    raid_start_ms:int
    raid_confirmed_ms:int
    raid_extreme:Decimal
    raid_level:Decimal
    side:str
    swing:ThreeSwing
    break_start_ms:int
    break_known_ms:int
    break_close:Decimal
    source_original_3m_row_id:str
    status:str="RESEARCH_3M_STRICT_PIVOT_CLOSE_BREAK_NOT_AUTHOR_BOS"

@dataclass(frozen=True)
class ThreeObservation:
    symbol:str
    as_of_ms:int
    source_native3m_rows:int
    source_hourly_closed:int
    closed_fractal_levels:int
    confirmed_first_wick_raids:int
    total_3m_strict_swings:int
    potential_breaks:tuple[ThreeBreak,...]
    readiness:str="NOT_TRADE_READY"
    author_bos_approved:int=0
    trades:int=0
    assumption:str="WAIT_NEXT_FULL_1H_THEN_FIRST_CLOSED_3M_CROSS_BEYOND_LAST_PREKNOWN_STRICT_SWING"

def _source(line,asof):
    if not isinstance(line,C21Native3mResult):
        raise ValueError("NOT_AN_ORIGINAL_C21A_3M_SOURCE")
    if (line.readiness!="NOT_TRADE_READY" or line.author_status!="AUTHOR_GOLDEN_SOURCE_UNAVAILABLE"
        or line.author_bos_approved or line.trade_approved or
        line.native_15m_ohlcv_equalities!=3072 or line.native_1d_equalities!=32
        or len(line.original_zip_shas)!=3 or
        any(not isinstance(x,str) or not re.fullmatch("[0-9a-f]{64}",x)
            for x in line.original_zip_shas)):
        raise ValueError("INVALID_C21A_PRICE_PROOF_OR_FORGED_READY")
    if (type(asof) is not int or asof<SEPT_START or asof>line.as_of_ms or
        asof>END or asof%THREE or
        line.as_of_ms!=SEPT_START+len(line.original_3m_closed)*THREE or
        len(line.original_3m_closed)>15360):
        raise ValueError("FUTURE_UNCLOSED_3M_OR_GAPPED_ASOF")
    for i,r in enumerate(line.original_3m_closed):
        at=SEPT_START+i*THREE
        sha=line.original_zip_shas[0 if i<14400 else 1 if i<14880 else 2]
        if (not isinstance(r,Original3mRow) or r.symbol!=line.symbol
            or r.start_ms!=at or r.known_ms!=at+THREE
            or r.zip_sha!=sha or r.raw_id!=sha+":"+str(at)
            or not all(isinstance(x,Decimal) and x.is_finite()
                       for x in (r.open,r.high,r.low,r.close,r.volume))
            or not (0<r.low<=min(r.open,r.close)<=max(r.open,r.close)<=r.high
                    and r.volume>=0)):
            raise ValueError("ALTERED_ORIGINAL_NATIVE3M_BAR")
    return line.original_3m_closed[:(asof-SEPT_START)//THREE]

def _hours(bars):
    out=[]
    for i in range(0,len(bars)//20*20,20):
        sub=bars[i:i+20]
        out.append(HourSource(sub[0].start_ms,sub[-1].known_ms,
            sub[0].open,max(x.high for x in sub),min(x.low for x in sub),
            sub[-1].close,tuple(x.raw_id for x in sub)))
    return tuple(out)

def _swings(bars):
    out=[]
    for i in range(1,len(bars)-1):
        a,b,c=bars[i-1:i+2]
        if b.high>a.high and b.high>c.high:
            out.append(ThreeSwing("HIGH",b.high,b.start_ms,c.known_ms,
                        (a.raw_id,b.raw_id,c.raw_id)))
        if b.low<a.low and b.low<c.low:
            out.append(ThreeSwing("LOW",b.low,b.start_ms,c.known_ms,
                        (a.raw_id,b.raw_id,c.raw_id)))
    return tuple(out)
