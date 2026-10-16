"""B1/C19 original native-15m fractal/wick breach diagnostics, PAPER ONLY.

Author liquidity lesson: three-candle fractal high/low, wick-only clean raid,
raid itself must be fractal; author StrongHL lesson requires later VC POI or BOS.
Author BOS entry model mostly 1H raid -> 3m/5m BOS: C19 DOES NOT assert BOS.
All price witnesses are original-source 15m geometries; the first bar's breach
is never retrospectively reported as a confirmed fractal until its next bar
CLOSES. No author-labelled Futures cases, no selected parent, no trading.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from c16_c08_monthly_daily_htf_lineage import ExtendedHTFReview, NativeKline, TF_MS
from c18_native_15m_child_witness_graph import (
    build_lower_tf_witness_graph,LowerTFWitnessGraph,C18Rejected)
from c17_htf_imb_reaction_diagnostics import AUTHOR_UNKNOWN, DIAGNOSTIC_ONLY

STEP=TF_MS["15m"]

class C19Rejected(ValueError):
    def __init__(self,code:str):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class FractalLiquidity:
    id:str
    kind:str
    level:Decimal
    center_start_ms:int
    known_at_ms:int
    original_15m_rows:tuple[str,str,str]

@dataclass(frozen=True)
class FirstLevelBreach:
    pivot_id:str
    kind:str
    pivot_known_at_ms:int
    breach_start_ms:Optional[int]
    breach_close_known_at_ms:Optional[int]
    raid_confirmed_at_ms:Optional[int]
    breach_bar_native_row_id:Optional[str]
    next_confirm_native_row_id:Optional[str]
    verdict:str
    # This is a *price observation*, not labelled market raid or author StrongHL.
    author_status:str=AUTHOR_UNKNOWN

@dataclass(frozen=True)
class ContactRaidAssociation:
    htf_id:str
    pivot_id:str
    breach_start_ms:int
    raid_known_at_ms:int
    first_ltf_contact_known_at_ms:int
    later_15m_gap_geometry_count:int
    later_1h_gap_geometry_count:int
    aligned_direction_gap_count:int
    opposite_direction_gap_count:int
    interpretation:str="EXACT_FIRST_HTF_ZONE_CONTACT_AND_FIRST_FRACTAL_WICK_BREACH_COOCCUR_NOT_CAUSALLY_AUTHOR_ATTRIBUTED"

@dataclass(frozen=True)
class C19SourceWitness:
    symbol:str
    as_of_ms:int
    fractal_levels:tuple[FractalLiquidity,...]
    first_breaches:tuple[FirstLevelBreach,...]
    first_contact_raid_coobservations:tuple[ContactRaidAssociation,...]
    candidate_bos_3m5m:int=0
    author_approved_stronghl:int=0
    author_approved_vc:int=0
    author_status:str=AUTHOR_UNKNOWN
    readiness:str=DIAGNOSTIC_ONLY
    provenance:"str"="C08_NATIVE_15M_VERIFIED_BY_C16_C18_AND_C19_PRICE_GEOMETRY"
    limitations:"str"="WICK_FRACTAL_15M_GEOMETRY_NOT_AUTHORIZED_BOS_OR_STRONGHL;NO_32DAY_NATIVE_3M5M"

def observe_fractal_first_breaches(native15:tuple[NativeKline,...],symbol:str)->tuple[tuple[FractalLiquidity,...],tuple[FirstLevelBreach,...]]:
    """Validated original stream is the responsibility of the C18 guard caller.

    Strict >/< pivot excludes equal highs/lows (EQH/EQL require another
    independent source geometry). A pivot is knowable at NEXT candle close.
    First subsequent strict crossing is counted once, even if later wick raids
    occur. Wick body must remain behind the crossed fractal level.
    """
    pivots=[]
    breaches=[]
    for i in range(1,len(native15)-1):
        left,center,right=native15[i-1:i+2]
        for kind,formed in (
            ("BSL",center.high>left.high and center.high>right.high),
            ("SSL",center.low<left.low and center.low<right.low)):
            if not formed:continue
            level=center.high if kind=="BSL" else center.low
            pivot=FractalLiquidity(
                f"{symbol}:15m:FRACTAL:{kind}:{center.start_ms}",
                kind,level,center.start_ms,right.known_at_ms,
                tuple(b.origin_raw_row_id for b in (left,center,right)))
            pivots.append(pivot)
            first=None
            # At time the pivot is confirmed, no one can use its future price.
            for j in range(i+2,len(native15)):
                b=native15[j]
                if ((kind=="BSL" and b.high>level) or
                    (kind=="SSL" and b.low<level)):
                    first=j
                    break
            if first is None:
                breaches.append(FirstLevelBreach(pivot.id,kind,pivot.known_at_ms,
                                                 None,None,None,None,None,
                                                 "NO_FIRST_BREACH_IN_PREFIX"))
                continue
            b=native15[first]
            wick=(b.open<=level and b.close<=level if kind=="BSL"
                  else b.open>=level and b.close>=level)
            # Fractal-reaction requirement: the actual RAID candle must be a
            # strict pivot vs its PREVIOUS and NEXT candle; only next CLOSED
            # confirms the raid (not a same-candle lookahead).
            if not wick:
                state="FIRST_BREACH_BODY_NOT_CLEAN_RAID"
            elif first+1==len(native15):
                state="FIRST_WICK_BREACH_AWAIT_NEXT_BAR"
            else:
                pre,nxt=native15[first-1],native15[first+1]
                confirmed=(b.high>pre.high and b.high>nxt.high if kind=="BSL"
                           else b.low<pre.low and b.low<nxt.low)
                state=("FIRST_WICK_BREACH_CONFIRMED_FRACTAL_GEOMETRY" if confirmed
                       else "FIRST_WICK_BREACH_NOT_CONFIRMED_FRACTAL")
            ok=state=="FIRST_WICK_BREACH_CONFIRMED_FRACTAL_GEOMETRY"
            breaches.append(FirstLevelBreach(
                pivot.id,kind,pivot.known_at_ms,b.start_ms,b.known_at_ms,
                native15[first+1].known_at_ms if ok else None,
                b.origin_raw_row_id,native15[first+1].origin_raw_row_id if ok else None,
                state))
    return tuple(pivots),tuple(breaches)

def build_c19_fractal_wick_witness(review:ExtendedHTFReview,*,as_of_ms:int)->C19SourceWitness:
    if not isinstance(review,ExtendedHTFReview):
        raise C19Rejected("NOT_A_C16_REVIEW")
    if type(as_of_ms) is not int or as_of_ms<0 or as_of_ms%STEP or as_of_ms>review.as_of_ms:
        raise C19Rejected("INVALID_FUTURE_15M_ASOF")
    try:
        g:LowerTFWitnessGraph=build_lower_tf_witness_graph(review,as_of_ms=as_of_ms)
    except C18Rejected as ex:
        raise C19Rejected("INVALID_C18_PRICE_LINEAGE") from ex
    native15=tuple(b for b in review.native_15m_closed if b.known_at_ms<=as_of_ms)
    pivots,breaches=observe_fractal_first_breaches(native15,review.symbol)
    b_by_time={}
    for ev in breaches:
        if ev.raid_confirmed_at_ms is not None:
            b_by_time.setdefault(ev.breach_start_ms,[]).append(ev)
    child15=g.children_15m
    child1h=g.children_1h
    observed=[]
    for p in g.parents:
        if p.first_closed_15m_contact_start_ms is None:continue
        for raid in b_by_time.get(p.first_closed_15m_contact_start_ms,()):
            assert raid.raid_confirmed_at_ms is not None
            after15=tuple(c for c in child15 if c.origin_start_ms>=raid.raid_confirmed_at_ms)
            after1h=tuple(c for c in child1h if c.origin_start_ms>=raid.raid_confirmed_at_ms)
            natural_side="SHORT" if raid.kind=="BSL" else "LONG"
            aligned=sum(c.side==natural_side for c in after15+after1h)
            observed.append(ContactRaidAssociation(
                p.parent_id,raid.pivot_id,raid.breach_start_ms,
                raid.raid_confirmed_at_ms,p.first_closed_15m_contact_known_at_ms,
                len(after15),len(after1h),aligned,
                len(after15)+len(after1h)-aligned))
    return C19SourceWitness(review.symbol,as_of_ms,pivots,breaches,tuple(observed))
