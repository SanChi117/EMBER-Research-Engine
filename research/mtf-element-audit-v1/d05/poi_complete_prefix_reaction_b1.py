"""B1/C05: fail-closed, read-only POI contact/reaction prefix observer.

Academic lesson diagrams illustrate *how price reacts to a level*. This module
does not decide whether the level is an academically valid POI. Nor is a
directional price move an academically confirmed Volume Confirmation.
Input must cover EVERY complete child-timeframe candle since parent POI known
as an aligned timestamp. Missing history => UNKNOWN, never "first test".
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"mtf-course-v05"/"src"))
from course_primitives_v05 import Bar, POI, TF_MS, validate_bars

class PrefixRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class PrefixEvent:
    type: str
    at_ms: int
    bar_start_ms: int
    evidence: str

@dataclass(frozen=True)
class PrefixReview:
    poi_id: str
    as_of_ms: int
    first_contact_at_ms: int | None
    contact_count: int
    event_log: tuple[PrefixEvent,...]
    history_contract: str="SUPPLIED_CLOSED_BARS_COMPLETE_AS_DECLARED_NOT_SOURCE_PROVEN"
    academy_level_status: str="LEVEL_AUTHOR_SEMANTICS_UNKNOWN"
    response_status: str="DIRECTIONAL_MOVE_IS_OBSERVATION_NOT_ACADEMIC_VC"
    order_readiness: str="NOT_TRADE_READY"

def inspect_complete_poi_prefix(poi:POI,bars:list[Bar],as_of_ms:int)->PrefixReview:
    """Only label first observed post-known contact if the full prefix is given.

    A contact = candle high/low intersects [poi.lo,poi.hi]. A later *separate*
    contact follows one or more whole noncontact candles. No author-specific
    definition of a "valid second test" is implied.
    A "directional move" is simply a subsequent close outside the POI
    beyond the favorable boundary, NOT an academic trigger, VC or filled trade.
    """
    if not isinstance(poi,POI) or not isinstance(bars,list):
        raise PrefixRejected("INVALID_POI_OR_BARS")
    if type(as_of_ms) is not int or type(poi.known) is not int or as_of_ms<=poi.known:
        raise PrefixRejected("INVALID_AS_OF_OR_POI_KNOWN")
    if not all(type(x) in (float,int) and isfinite(x) and x>0 for x in (poi.lo,poi.hi)):
        raise PrefixRejected("INVALID_ZONE_PRICE")
    if not bars or any(not isinstance(b,Bar) for b in bars):
        raise PrefixRejected("NO_VALID_CANDLES")
    tf=bars[0].tf
    duration=TF_MS[tf]
    if poi.known%duration:
        raise PrefixRejected("UNKNOWN_CONTACT_IN_PARTIAL_KNOWN_CANDLE")
    if as_of_ms%duration:
        raise PrefixRejected("AS_OF_NOT_CLOSED_BAR_BOUNDARY")
    # The future suffix is never inspected or validated as evidence.
    closed=[b for b in bars if b.end<=as_of_ms]
    if not closed:
        raise PrefixRejected("MISSING_CLOSED_PREFIX")
    try:
        validate_bars(closed,tf)
    except (ValueError,TypeError) as e:
        raise PrefixRejected("INCOMPLETE_OR_MIXED_TIMEFRAME_PREFIX") from e
    if closed[0].start!=poi.known or closed[-1].end!=as_of_ms:
        raise PrefixRejected("NOT_ALL_POST_KNOWN_CANDLES_PRESENT")
    if any(b.start<poi.known for b in closed):
        raise PrefixRejected("INCLUDES_PRE_KNOWN_BAR")
    out=[]
    first=None
    last_touch=False
    contact_count=0
    emitted_direction=False
    warned_breach=False
    def note(kind,b,why):
        out.append(PrefixEvent(kind,b.end,b.start,why))
    for b in closed:
        hit=b.h>=poi.lo and b.l<=poi.hi
        if hit and first is None:
            first=b.end
            contact_count+=1
            note("FIRST_CONTACT_OBSERVED_COMPLETE_PREFIX",b,
                 "First interval intersection since parent known; author-valid POI remains unknown")
        elif hit and not last_touch:
            contact_count+=1
            note("LATER_CONTACT_UNCLASSIFIED",b,
                 "Separated by at least one closed noncontact bar; not a source-certified second test")
        # Need a STRICTLY LATER completed candle after first contact: same-bar
        # OHLC has no reliable intrabar chronology.
        if first is not None and b.start>=first and not emitted_direction:
            favorable=b.c>poi.hi if poi.side=="LONG" else b.c<poi.lo
            if favorable:
                emitted_direction=True
                note("LATER_FAVORABLE_CLOSE_OBSERVED_NOT_VC",b,
                     "A later closed candle moved beyond POI favorable bound; not author VC/BOS/entry")
        if first is not None and b.start>=first and not warned_breach:
            beyond=b.c<poi.lo if poi.side=="LONG" else b.c>poi.hi
            if beyond:
                warned_breach=True
                note("CLOSE_BEYOND_OPPOSITE_BOUND_NEEDS_INVALIDATION_RULE",b,
                     "Observed breach, source-specific invalidation and pending-order state unresolved")
        last_touch=hit
    return PrefixReview(poi.id,as_of_ms,first,contact_count,tuple(out))
