"""B1/C11: geometric 1H raid contact -> later 5m IMB confirmation -> 5m POI test.

The ORIGINAL course StrongHL description requires liquidity / inefficiency
contact AND subsequent POI or BOS confirmation. This is a NARROW positive
geometric witness (1h liquidity raid then 5m classic 3-candle IMB), not an
author-approved StrongHL, volume measurement or route-to-entry.

In particular: all source bundles are caller objects until the online
F06-pinned independent replay validates their ZIP and raw CSV SHA.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"mtf-course-v05"/"src"))
from course_primitives_v05 import (
    Bar, confirmed_pivots, confirmed_hourly_raids, confirmed_imb,
)
from f03_5m_original_source import Verified5m,PERIOD
from c10_two_day_original_5m_context import review_two_day_5m

class StrongCandidateRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class ContactImbPriceWitness:
    source_symbol: str
    contact_1h_raid_uid: str
    side: str
    contact_extreme: float
    contact_known_ms: int
    contact_source_5m_id: str
    confirmation_5m_imb_uid: str
    confirmation_known_ms: int
    confirmation_source_5m_id: str
    poi_low: float
    poi_high: float
    first_later_poi_test_known_ms: int|None
    first_later_poi_test_source_id: str|None
    price_status: str="WICK_RAID_THEN_3BAR_IMB_GEOMETRY_ONLY"
    academic_status: str="STRONGHL_AND_VC_NOT_AUTHOR_CERTIFIED"
    readiness: str="NOT_TRADE_READY"

@dataclass(frozen=True)
class ContactImbReview:
    symbol: str
    as_of_ms: int
    closed_5m_count: int
    closed_1h_count: int
    raid_contact_candidates: int
    post_raid_5m_imb_candidates: int
    paired_source_price_witnesses: tuple[ContactImbPriceWitness,...]
    confirmation_definition: str="3_CANDLE_WICK_GAP_NOT_EXCHANGE_VOLUME_SPIKE"
    completeness: str="2_DAY_COURSE_CONTEXT_NOT_FULL_PREHISTORY"
    academic_status: str="NO_AUTHOR_GOLDEN_STRONGHL_OR_VC_APPROVAL"
    readiness: str="NOT_TRADE_READY"

def inspect_contact_then_5m_imb(first:Verified5m,second:Verified5m,
                                as_of_ms:int)->ContactImbReview:
    try:
        old=review_two_day_5m(first,second,as_of_ms)
    except (ValueError,TypeError,AttributeError) as ex:
        raise StrongCandidateRejected("INVALID_TWO_DAY_SOURCE_PREFIX") from ex
    closed=[r for p in (first,second) for r in p.rows if r.bar.end<=as_of_ms]
    bars=[r.bar for r in closed]
    by_open={r.bar.start:r for r in closed}
    hourly=[]
    for i in range(len(bars)//12):
        b=bars[i*12:i*12+12]
        hourly.append(Bar(b[0].start,b[-1].end,b[0].o,
                          max(x.h for x in b),min(x.l for x in b),b[-1].c,"1h"))
    raids=confirmed_hourly_raids(hourly,confirmed_pivots(hourly))
    imbs=confirmed_imb(bars)
    paired=[]
    nconfirm=0
    for raid in raids:
        # Exactly one raw 5m bar at the raided 1h wick extreme, with
        # deterministic first-in-1h selection in case of equal extremes.
        within=[r for r in closed if raid.origin<=r.bar.start<raid.known]
        matches=[r for r in within if (
            r.bar.l==raid.extreme if raid.side=="LONG"
            else r.bar.h==raid.extreme)]
        if len(within)!=12 or not matches:
            raise StrongCandidateRejected("PARENT_RAID_HAS_NO_ORIGINAL_5M_WICK")
        contact=matches[0]
        for imb in imbs:
            if imb.side!=raid.side or imb.origin<raid.known or imb.known>as_of_ms:
                continue
            # Re-breaching the raided extreme before this proposed IMB
            # destroys the *geometric witness* for this raid. This is an
            # intentionally strict research check, not an author-certified
            # universal StrongHL invalidation rule.
            between=(r.bar for r in closed if raid.known<=r.bar.start<imb.known)
            if any((b.h>raid.extreme if raid.side=="SHORT" else b.l<raid.extreme)
                   for b in between):
                continue
            nconfirm+=1
            idx=(imb.known-first.day_start_ms)//PERIOD-1
            if idx<0 or idx>=len(closed) or closed[idx].bar.end!=imb.known:
                raise StrongCandidateRejected("IMB_NOT_BOUND_TO_THIRD_CLOSED_5M_SOURCE")
            final=closed[idx]
            # First test MUST be after the three-bar gap is known. It is
            # merely price overlap, NOT a author-validated POI lifecycle.
            touch=next((r for r in closed if r.bar.start>=imb.known
                        and r.bar.h>=imb.lo and r.bar.l<=imb.hi),None)
            paired.append(ContactImbPriceWitness(
                old.symbol,raid.id,raid.side,raid.extreme,raid.known,contact.raw_id,
                imb.id,imb.known,final.raw_id,imb.lo,imb.hi,
                touch.bar.end if touch else None,touch.raw_id if touch else None))
    return ContactImbReview(old.symbol,as_of_ms,len(bars),len(hourly),
                            len(raids),nconfirm,tuple(paired))
