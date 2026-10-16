"""B1/C10: two consecutive ORIGINAL 5m Futures days, one causal 1h context.

Reuses unchanged author-candidate primitives course-v05, not a source-exact
author certification. Archive authenticity comes from the separate F03/F06
live HTTPS + .CHECKSUM + pinned SHA job, NOT merely this object constructor.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"mtf-course-v05"/"src"))
from course_primitives_v05 import Bar,confirmed_pivots,confirmed_hourly_raids,bos_after_raid
from f03_5m_original_source import Verified5m,parse_5m_source,PERIOD,DAY

class TwoDayRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class TwoDayBos:
    raid_id: str
    raid_known: int
    bos_id: str
    bos_known: int
    original_day_zip_sha256: str
    original_bar_id: str

@dataclass(frozen=True)
class TwoDayReview:
    symbol: str
    as_of_ms: int
    closed_5m_count: int
    closed_1h_count: int
    confirmed_1h_pivots: int
    confirmed_1h_raids: int
    confirmed_5m_pivots: int
    source_raid_bos: tuple[TwoDayBos,...]
    first_day_raid_count: int
    second_day_raid_count: int
    readiness: str="NOT_TRADE_READY"
    approval: str="PRICE_GEOMETRY_V05_NOT_AUTHOR_STRONGHL_VC_POI"
    source_scope: str="TWO_DAYS_SAME_SYMBOL_ONLY_NO_COURSE_TRADE_READY"

def review_two_day_5m(first:Verified5m,second:Verified5m,as_of_ms:int)->TwoDayReview:
    if not isinstance(first,Verified5m) or not isinstance(second,Verified5m):
        raise TwoDayRejected("NOT_VERIFIED_5M_SOURCE_OBJECTS")
    try:
        a,d0,_=parse_5m_source(first.archive_url)
        b,d1,_=parse_5m_source(second.archive_url)
    except Exception as ex:
        raise TwoDayRejected("INVALID_5M_FUTURES_SOURCE_PATH") from ex
    if (a!=b or first.symbol!=a or second.symbol!=a or
        d0!=first.day_start_ms or d1!=second.day_start_ms):
        raise TwoDayRejected("CROSS_MARKET_SYMBOL_OR_SOURCE_DAY")
    if d1!=d0+DAY:
        raise TwoDayRejected("MISSING_OR_OVERLAPPING_UTC_DAY")
    if type(as_of_ms) is not int or as_of_ms%PERIOD or as_of_ms<d0 or as_of_ms>d1+DAY:
        raise TwoDayRejected("AS_OF_NOT_CLOSED_ON_VALID_5M_BOUNDARY")
    combined=[]
    for p in (first,second):
        if (len(p.rows)!=288 or not re.fullmatch("[0-9a-f]{64}",p.zip_sha256)
            or not re.fullmatch("[0-9a-f]{64}",p.raw_csv_sha256)):
            raise TwoDayRejected("INCOMPLETE_OR_MALFORMED_5M_ARCHIVE_PROOF")
        for i,row in enumerate(p.rows):
            bar=row.bar
            if (not isinstance(bar,Bar) or bar.tf!="5m" or
                bar.start!=p.day_start_ms+i*PERIOD or bar.end!=bar.start+PERIOD or
                row.raw_id!=p.zip_sha256+":"+str(bar.start)):
                raise TwoDayRejected("ORIGINAL_5M_ROW_TIME_OR_LINEAGE_MISMATCH")
            combined.append((bar,p.zip_sha256,row.raw_id))
    if first.zip_sha256==second.zip_sha256:
        raise TwoDayRejected("REUSED_ORIGINAL_SOURCE_ARCHIVE_HASH")
    closed=[r for r in combined if r[0].end<=as_of_ms]
    bars=[x[0] for x in closed]
    hours=[]
    for i in range(len(bars)//12):
        group=bars[12*i:12*i+12]
        if group[0].start%3600000 or group[-1].end!=group[0].start+3600000:
            raise TwoDayRejected("INCOMPLETE_1H_FROM_5M_SOURCE")
        hours.append(Bar(group[0].start,group[-1].end,group[0].o,
                         max(r.h for r in group),min(r.l for r in group),
                         group[-1].c,"1h"))
    piv1=confirmed_pivots(hours)
    raids=confirmed_hourly_raids(hours,piv1)
    piv5=confirmed_pivots(bars)
    bos=bos_after_raid(bars,piv5,raids)
    byraid={r.id:r for r in raids}
    bytime={r[0].start:r for r in closed}
    result=[]
    for ev in bos:
        parent=byraid.get(ev.raid_id)
        raw=bytime.get(ev.origin)
        if (parent is None or parent.known>=ev.known or ev.known>as_of_ms
            or raw is None or ev.known!=raw[0].end):
            raise TwoDayRejected("BOS_NOT_CHILD_OF_CLOSED_PARENT_RAID_AND_SOURCE")
        result.append(TwoDayBos(parent.id,parent.known,ev.id,ev.known,raw[1],raw[2]))
    return TwoDayReview(a,as_of_ms,len(bars),len(hours),len(piv1),len(raids),
                        len(piv5),tuple(result),
                        sum(r.known<=d1 for r in raids),
                        sum(r.known>d1 for r in raids))
