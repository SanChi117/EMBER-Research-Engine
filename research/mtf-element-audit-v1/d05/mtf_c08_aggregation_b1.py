"""B1/C07: 1H/4H/1D CLOSED UTC candles from original 15m child series.

A technical, source-segment resampler. Not the course's Daily Bias, POI,
Order Flow, VC, liquidity, StrongHL, or an approved trading route.
Input archive authenticity MUST be verified separately by original C08 SHA
and remote ZIP+CHECKSUM (see dedicated HTTPS integration test).
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from math import isfinite
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/"mtf-course-v05"/"src"))
from course_primitives_v05 import Bar,TF_MS,validate_bars

DAY=TF_MS["1d"]
CHILD=TF_MS["15m"]
TF_SLOTS={"1h":4,"4h":16,"1d":96}

class MTFSourceRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class Source15m:
    bar: Bar
    volume: Decimal
    member_id: str

@dataclass(frozen=True)
class DerivedClosedBar:
    bar: Bar
    volume: Decimal
    source_member_ids: tuple[str,...]
    known_at_ms: int
    source_resolution: str="SOURCE_15M_BINANCE_FUTURES_UNATTESTED_IN_THIS_FUNCTION"
    course_label: str="AGGREGATE_ONLY_NOT_DAILY_BIAS_OR_VC"
    readiness: str="NOT_TRADE_READY"

@dataclass(frozen=True)
class MTFClosedHierarchy:
    as_of_ms: int
    source_count: int
    bars_1h: tuple[DerivedClosedBar,...]
    bars_4h: tuple[DerivedClosedBar,...]
    bars_1d: tuple[DerivedClosedBar,...]
    pending_1h_slots: int
    pending_4h_slots: int
    pending_1d_slots: int
    status: str="SOURCE_SEGMENT_RESAMPLING_NOT_COURSE_DIRECTION_SIGNOFF"
    readiness: str="NOT_TRADE_READY"

def _aggregate(block: list[Source15m],tf: str) -> DerivedClosedBar:
    first,last=block[0].bar,block[-1].bar
    o=first.o
    h=max(x.bar.h for x in block)
    l=min(x.bar.l for x in block)
    c=last.c
    total=sum((x.volume for x in block),Decimal("0"))
    res=Bar(first.start,last.end,o,h,l,c,tf)
    return DerivedClosedBar(res,total,tuple(x.member_id for x in block),last.end)

def derive_closed_mtf_from_15m(sources: list[Source15m],
                               as_of_ms: int) -> MTFClosedHierarchy:
    """Refuses gaps, missing start-of-day and unfinished HTF candles.

    This scan certifies closed OHLC aggregation in a *supplied segment*
    only. It cannot establish multi-month 1D bias from a one-day fixture.
    """
    if type(as_of_ms) is not int or as_of_ms<0 or as_of_ms%CHILD:
        raise MTFSourceRejected("AS_OF_NOT_15M_CLOSE_BOUNDARY")
    if not isinstance(sources,list) or not sources or any(not isinstance(s,Source15m) for s in sources):
        raise MTFSourceRejected("INVALID_15M_SOURCES")
    closed=[s for s in sources if s.bar.end<=as_of_ms]
    if not closed:
        raise MTFSourceRejected("NO_CLOSED_15M_PREFIX")
    for source in closed:
        b=source.bar
        if not isinstance(b,Bar) or b.tf!="15m" or b.start%CHILD or b.end!=b.start+CHILD:
            raise MTFSourceRejected("NOT_ALIGNED_15M_SOURCE")
        if not isinstance(source.member_id,str) or not source.member_id or (
            not isinstance(source.volume,Decimal) or
            not source.volume.is_finite() or source.volume<0):
            raise MTFSourceRejected("BAD_VOLUME_OR_SOURCE_PROVENANCE")
    if len({s.member_id for s in closed})!=len(closed):
        raise MTFSourceRejected("REUSED_SOURCE_ROW_ID")
    try:
        validate_bars([x.bar for x in closed],"15m")
    except (ValueError,TypeError) as e:
        raise MTFSourceRejected("SOURCE_15M_GAP_OR_MIXED_TF") from e
    if closed[0].bar.start%DAY!=0:
        raise MTFSourceRejected("UNKNOWN_DAY_START_HISTORY")
    if closed[-1].bar.end!=as_of_ms:
        raise MTFSourceRejected("MISSING_BAR_BEFORE_AS_OF")
    completed={}
    remains={}
    for tf,count in TF_SLOTS.items():
        out=[]
        time_step=TF_MS[tf]
        for index in range(0,len(closed)//count):
            group=closed[index*count:(index+1)*count]
            if group[0].bar.start%time_step:
                raise MTFSourceRejected("HIGHER_TF_UTC_ALIGNMENT_ERROR")
            if group[-1].bar.end!=group[0].bar.start+time_step:
                raise MTFSourceRejected("UNFINISHED_HTF_SOURCE_GROUP")
            out.append(_aggregate(group,tf))
        completed[tf]=tuple(out)
        remains[tf]=len(closed)%count
    return MTFClosedHierarchy(as_of_ms,len(closed),completed["1h"],completed["4h"],completed["1d"],
                              remains["1h"],remains["4h"],remains["1d"])
