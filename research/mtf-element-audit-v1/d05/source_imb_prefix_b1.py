"""B1/C06: source-defined classic 3-candle IMB candidate → POI contact prefix.

Unlike the deliberately lookahead-created fixture of B1/C05, this candidate
is emitted ONLY when the 3rd candle closes, using unchanged v05.confirmed_imb.
An IMB is not automatically an academically approved POI/VC or trade.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"mtf-course-v05"/"src"))
from course_primitives_v05 import Bar,POI,confirmed_imb,validate_bars
from poi_complete_prefix_reaction_b1 import (
    PrefixRejected,PrefixReview,inspect_complete_poi_prefix,
)

class CourseImbRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class CourseImbObservation:
    imbalance_id: str
    known_at_ms: int
    side: str
    zone_lo: float
    zone_hi: float
    contact: PrefixReview | None
    status: str="CLASSIC_WICK_GAP_SOURCE_CANDIDATE_NOT_ACADEMIC_POI_SIGNOFF"
    readiness: str="NOT_TRADE_READY"

def observe_source_defined_imbs(bars:list[Bar],as_of_ms:int)->tuple[CourseImbObservation,...]:
    """Read-only; input is a *declared* continuous interval of closed candles.

    A candidate is known at third candle CLOSE. All subsequent contact/reaction
    readings use bars with start >= known, never that confirmation candle.
    """
    if not isinstance(bars,list) or not bars or any(not isinstance(b,Bar) for b in bars):
        raise CourseImbRejected("INVALID_HISTORY")
    if type(as_of_ms) is not int:
        raise CourseImbRejected("INVALID_AS_OF")
    closed=[b for b in bars if b.end<=as_of_ms]
    if not closed:
        raise CourseImbRejected("NO_CLOSED_CANDLES_AS_OF")
    try:
        validate_bars(closed,closed[0].tf)
    except (ValueError,TypeError) as e:
        raise CourseImbRejected("MIXED_OR_GAPPED_HISTORY") from e
    if closed[-1].end!=as_of_ms:
        raise CourseImbRejected("PREFIX_NOT_COMPLETE_TO_AS_OF")
    candidates=confirmed_imb(closed)
    observed=[]
    for imb in candidates:
        if imb.known>as_of_ms:
            raise CourseImbRejected("FUTURE_IMB")
        interval=POI("source-candidate:"+imb.id,imb.tf,imb.side,imb.lo,imb.hi,imb.known)
        subsequent=[b for b in closed if b.start>=imb.known]
        contact=None
        if subsequent:
            try:
                contact=inspect_complete_poi_prefix(interval,subsequent,as_of_ms)
            except PrefixRejected as e:
                raise CourseImbRejected("SOURCE_IMB_CHILD_PREFIX_REJECTED_"+e.code) from e
        observed.append(CourseImbObservation(imb.id,imb.known,imb.side,
                                              imb.lo,imb.hi,contact))
    return tuple(observed)
