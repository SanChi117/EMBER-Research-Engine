"""B1/C02: read-only POI touch-observation overlay on unchanged course v05 PoiLifecycle.

Observes *when* the first candidate test is known, continuous contact and a
later independent contact candidate; never pretends later contact is the
course-verified second test. A post-first close beyond POI is an evidence
warning, not a newly invented academic invalidation rule.
No trade plan, order placement or exchange integration.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
import sys

RESEARCH=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(RESEARCH/"mtf-course-v05"/"src"))
from course_primitives_v05 import POI, Bar, PoiLifecycle, validate_bars

class PoiObservationRejected(ValueError):
    pass

@dataclass(frozen=True)
class PoiNote:
    poi_id: str
    kind: str
    known_at_ms: int
    observed_tf: str
    bar_start_ms: int
    reason: str

@dataclass(frozen=True)
class PoiDiagnostic:
    poi_id: str
    as_of_ms: int
    notes: tuple[PoiNote,...]
    readiness: str = "NOT_TRADE_READY"
    source_status: str = "COURSE_REACTION_LIFECYCLE_PARTIAL"

def inspect_poi_touch_sequence(poi:POI, bars:list[Bar], as_of_ms:int)->PoiDiagnostic:
    """Prefix-stable source diagnostics; uses v05's original first-touch guard."""
    if not isinstance(poi,POI):
        raise PoiObservationRejected("INVALID_PARENT_POI")
    if type(as_of_ms) is not int or as_of_ms<0:
        raise PoiObservationRejected("INVALID_AS_OF_TIME")
    if not all(isfinite(x) and x>0 for x in (poi.lo,poi.hi)):
        raise PoiObservationRejected("INVALID_POI_GEOMETRY")
    if not isinstance(bars,list) or any(not isinstance(b,Bar) for b in bars):
        raise PoiObservationRejected("BAD_INPUT_BARS")
    closed=[x for x in bars if x.end<=as_of_ms]
    if closed:
        validate_bars(closed,closed[0].tf)
    lifecycle=PoiLifecycle(poi)
    seen=False
    prior_touch=False
    broken_warning=False
    notes=[]
    def add(b:Bar,kind:str,reason:str):
        notes.append(PoiNote(poi.id,kind,b.end,b.tf,b.start,reason))
    for b in closed:
        if b.start<poi.known:
            continue
        if lifecycle.state=="INVALIDATED":
            break
        touched=b.h>=poi.lo and b.l<=poi.hi
        if lifecycle.state=="FRESH":
            result=lifecycle.advance(b)
            if result=="TESTED":
                seen=True
                prior_touch=True
                add(b,"FIRST_TEST_CANDIDATE","v05 PoiLifecycle accepted first post-known zone contact; geometric course recognition not approved")
                continue
            if result=="INVALIDATED":
                add(b,"PRE_FIRST_CLOSE_BREACH_V05","original v05 preliminary invalidation state (not author-complete)")
                break
        elif seen:
            if touched and not prior_touch:
                add(b,"LATER_CONTACT_UNCLASSIFIED","post-exit zone contact; do not silently relabel as confirmed second test or create a trade")
            beyond=(b.c<poi.lo if poi.side=="LONG" else b.c>poi.hi)
            if beyond and not broken_warning:
                broken_warning=True
                add(b,"POST_FIRST_CLOSE_BREACH_NEEDS_RULE","v05 stays TESTED: post-first invalidation and pending-order lifecycle require separate source")
        prior_touch=touched
    return PoiDiagnostic(poi.id,as_of_ms,tuple(notes))
