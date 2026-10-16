"""B1/C09: real-price geometric 1H pivot/raid -> 5m BOS diagnostics.

Uses unchanged course-v05 functions, data read from verified 5m source
and CLOSED 1h aggregates from exactly twelve original 5m candles.
v05 has a provisional 24h raid freshness and 2+2 pivots: engineering
assumptions not yet chart-attested as author's exact rules. No StrongHL,
academic VC, Daily Bias, entry quote or execution claimed.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"mtf-course-v05"/"src"))
from course_primitives_v05 import (
    Bar,confirmed_pivots,confirmed_hourly_raids,bos_after_raid,validate_bars
)
from f03_5m_original_source import Verified5m,PERIOD,DAY

class PriceRouteRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class PriceRaidBosWitness:
    raid_id: str
    raid_1h_known_at_ms: int
    bos_id: str
    bos_5m_known_at_ms: int
    breached_5m_close_bar_start: int
    original_5m_member_id: str
    status: str="GEOMETRIC_V05_CANDIDATE_NOT_AUTHOR_STRONGHL_OR_READY"

@dataclass(frozen=True)
class PriceGeometryReview:
    as_of_ms: int
    five_minute_closed_count: int
    hourly_closed_count: int
    hourly_pivot_candidates: int
    hourly_raid_candidates: int
    five_minute_pivot_candidates: int
    five_minute_bos_candidates: int
    bos_witnesses: tuple[PriceRaidBosWitness,...]
    completeness: str="ONE_DAY_PREFIX_ONLY_EARLIER_CONTEXT_UNATTESTED"
    academic_semantics: str="V05_GEOMETRY_ONLY_24H_FRESHNESS_UNAPPROVED"
    stronghl_status: str="NO_INDEPENDENT_STRONG_HL_VC_CERTIFICATE"
    readiness: str="NOT_TRADE_READY"

def inspect_source_raid_bos_5m(proof:Verified5m,as_of_ms:int)->PriceGeometryReview:
    if not isinstance(proof,Verified5m) or not isinstance(proof.rows,tuple) or len(proof.rows)!=288:
        raise PriceRouteRejected("NOT_A_FULL_ORIGINAL_5M_SOURCE_PROOF")
    if type(as_of_ms) is not int or as_of_ms<proof.day_start_ms or as_of_ms>proof.day_start_ms+DAY or as_of_ms%PERIOD:
        raise PriceRouteRejected("AS_OF_NOT_CLOSED_WITHIN_5M_ARCHIVE")
    for i,r in enumerate(proof.rows):
        b=r.bar
        if (not isinstance(b,Bar) or b.tf!="5m"
            or b.start!=proof.day_start_ms+i*PERIOD or b.end!=b.start+PERIOD
            or not r.raw_id):
            raise PriceRouteRejected("NONCONTIGUOUS_OR_UNIDENTIFIED_5M_PROVENANCE")
    # Precalibrated 5m archive contains future suffix; NEVER let it enter
    # any pivot/raid/BOS candidate at an earlier decision time.
    closed=[x.bar for x in proof.rows if x.bar.end<=as_of_ms]
    n=len(closed)
    if not n:
        return PriceGeometryReview(as_of_ms,0,0,0,0,0,0,())
    hourly=[]
    for i in range(n//12):
        segment=closed[i*12:(i+1)*12]
        h=Bar(segment[0].start,segment[-1].end,segment[0].o,
              max(b.h for b in segment),min(b.l for b in segment),
              segment[-1].c,"1h")
        if h.start%3600000:
            raise PriceRouteRejected("NOT_UTC_CLOSED_HOURLY")
        hourly.append(h)
    p1=confirmed_pivots(hourly)
    raid=confirmed_hourly_raids(hourly,p1)
    p5=confirmed_pivots(closed)
    bos=bos_after_raid(closed,p5,raid)
    raid_idx={r.id:r for r in raid}
    witnesses=[]
    for event in bos:
        r=raid_idx.get(event.raid_id)
        if r is None or event.known<=r.known or event.tf!="5m":
            raise PriceRouteRejected("INVALID_PARENT_RAID_FOR_BOS")
        index=(event.origin-proof.day_start_ms)//PERIOD
        if index<0 or index>=n or closed[index].end!=event.known:
            raise PriceRouteRejected("BOS_NOT_SOURCE_BOUND_AT_CLOSE")
        witnesses.append(PriceRaidBosWitness(r.id,r.known,event.id,event.known,
                     event.origin,proof.rows[index].raw_id))
    return PriceGeometryReview(as_of_ms,n,len(hourly),len(p1),len(raid),
                               len(p5),len(bos),tuple(witnesses))
