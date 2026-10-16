"""B1/C18: closed native-15m witness graph beneath 1D/4H IMB levels.

Observes causal first lower-TF contact with an already-formed higher-TF
geometric zone, then every *later* closed 1H/15m classic IMB candidate.
These are time-order co-observations, NOT academic VC, StrongHL, BOS or trades.
No nearest child/parent winner and no arbitrary expiry.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
import re
from c16_c08_monthly_daily_htf_lineage import (
    ExtendedHTFReview, NativeKline, DerivedClosedTF, TF_MS, _combine)
from c17_htf_imb_reaction_diagnostics import (
    diagnose_htf_imb, HTFImbalanceCandidate, AUTHOR_UNKNOWN, DIAGNOSTIC_ONLY, C17Rejected)

HEX64=re.compile(r"^[0-9a-f]{64}$")

class C18Rejected(ValueError):
    def __init__(self,code:str):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class ChildGapWitness:
    id:str
    symbol:str
    tf:str
    side:str
    origin_start_ms:int
    known_at_ms:int
    zone_low:Decimal
    zone_high:Decimal
    source_native_15m_rows:tuple[str,...]
    source_zip_shas:tuple[str,...]

@dataclass(frozen=True)
class HTFContactWitness:
    parent_id:str
    parent_tf:str
    parent_side:str
    level_known_at_ms:int
    first_closed_15m_contact_start_ms:Optional[int]
    first_closed_15m_contact_known_at_ms:Optional[int]
    first_closed_15m_source_row_id:Optional[str]
    subsequent_15m_contacts:int
    state:str
    author_status:str=AUTHOR_UNKNOWN

@dataclass(frozen=True)
class CandidateAssociation:
    parent_id:str
    child_id:str
    contact_known_at_ms:int
    child_known_at_ms:int
    temporal_relation:str="THREE_CHILD_SOURCE_BARS_AFTER_FIRST_15M_CONTACT"
    certification:str="OBSERVED_TEMPORAL_COOCCURRENCE_NOT_AUTHOR_PARENT_VC"

@dataclass(frozen=True)
class LowerTFWitnessGraph:
    symbol:str
    as_of_ms:int
    parents:tuple[HTFContactWitness,...]
    children_1h:tuple[ChildGapWitness,...]
    children_15m:tuple[ChildGapWitness,...]
    edges:tuple[CandidateAssociation,...]
    author_status:str=AUTHOR_UNKNOWN
    readiness:str=DIAGNOSTIC_ONLY
    source_scope:str="C16_ORIGINAL_15M_NATIVE_AND_VERIFIED_NATIVE_1D_C17_IMB_GEOMETRY"
    attribution:str="NO_AUTOMATIC_PARENT_OR_VC_SELECTION"

def _verify_review(review:ExtendedHTFReview)->None:
    if not isinstance(review,ExtendedHTFReview):
        raise C18Rejected("NOT_AN_EXTENDED_C16_REVIEW")
    if review.readiness!=DIAGNOSTIC_ONLY or review.author_status!="NO_AUTHOR_LABELLED_1D_4H_POI":
        raise C18Rejected("FORGED_C16_AUTHOR_STATUS")
    if review.crosschecked_native_1d!=len(review.native_1d_closed):
        raise C18Rejected("FALSE_C16_NATIVE_DAILY_MATCH_COUNT")
    if not review.native_15m_closed:
        raise C18Rejected("MISSING_NATIVE_15M_SOURCE_PREFIX")
    series=review.native_15m_closed
    for i,b in enumerate(series):
        if not isinstance(b,NativeKline) or b.symbol!=review.symbol or b.tf!="15m":
            raise C18Rejected("CROSS_SYMBOL_OR_NON_NATIVE_15M")
        if (b.start_ms%TF_MS["15m"] or b.known_at_ms!=b.start_ms+TF_MS["15m"] or
            b.known_at_ms>review.as_of_ms or
            (i and b.start_ms!=series[i-1].known_at_ms)):
            raise C18Rejected("INCOMPLETE_FUTURE_OR_DISORDERED_NATIVE_15M")
        if (not HEX64.fullmatch(b.origin_zip_sha256) or
            b.origin_raw_row_id!=b.origin_zip_sha256+":"+str(b.start_ms)):
            raise C18Rejected("INVALID_NATIVE_15M_SOURCE_SHA")
        if (not all(isinstance(v,Decimal) and v.is_finite() for v in
                (b.open,b.high,b.low,b.close,b.volume)) or
            not (0<b.low<=min(b.open,b.close)<=max(b.open,b.close)<=b.high and b.volume>=0)):
            raise C18Rejected("MUTATED_OR_NONFINITE_NATIVE_15M_PRICE")
    def rebuild(tf:str):
        n=TF_MS[tf]//TF_MS["15m"]
        return tuple(_combine(series[i:i+n],tf) for i in range(0,len(series)//n*n,n))
    if rebuild("1h")!=review.derived_1h_closed:
        raise C18Rejected("DERIVED_1H_SOURCE_GEOMETRY_MISMATCH")
    if rebuild("4h")!=review.derived_4h_closed:
        raise C18Rejected("DERIVED_4H_SOURCE_GEOMETRY_MISMATCH")
    calculated_daily=rebuild("1d")
    if len(calculated_daily)!=len(review.native_1d_closed):
        raise C18Rejected("NATIVE_1D_PREFIX_INCOMPLETE")
    for n,d in zip(review.native_1d_closed,calculated_daily):
        if not isinstance(n,NativeKline) or n.symbol!=review.symbol or n.tf!="1d":
            raise C18Rejected("WRONG_ORIGINAL_DAILY_SOURCE")
        if (n.start_ms,n.known_at_ms,n.open,n.high,n.low,n.close,n.volume)!=(
            d.start_ms,d.known_at_ms,d.open,d.high,d.low,d.close,d.volume):
            raise C18Rejected("NATIVE_DAILY_VS_15M_PARITY_MISMATCH")
        if not HEX64.fullmatch(n.origin_zip_sha256) or n.origin_raw_row_id!=n.origin_zip_sha256+":"+str(n.start_ms):
            raise C18Rejected("NATIVE_DAILY_SOURCE_SHA_MISMATCH")

def _gaps(bars,tf:str,symbol:str)->tuple[ChildGapWitness,...]:
    out=[]
    for i in range(2,len(bars)):
        a,c=bars[i-2],bars[i]
        if c.low>a.high:
            side,lo,hi="LONG",a.high,c.low
        elif c.high<a.low:
            side,lo,hi="SHORT",c.high,a.low
        else:
            continue
        three=bars[i-2:i+1]
        if tf=="15m":
            ids=tuple(x.origin_raw_row_id for x in three)
            shas=tuple(dict.fromkeys(x.origin_zip_sha256 for x in three))
        else:
            ids=tuple(row for x in three for row in x.source_native_15m_rows)
            shas=tuple(dict.fromkeys(s for x in three for s in x.source_native_15m_zip_shas))
        out.append(ChildGapWitness(
            f"{symbol}:{tf}:CLASSIC_IMB:{side}:{c.start_ms}",
            symbol,tf,side,a.start_ms,c.known_at_ms,lo,hi,ids,shas))
    return tuple(out)

def _parent_id(x:HTFImbalanceCandidate)->str:
    return f"{x.symbol}:{x.tf}:HTF_IMB:{x.side}:{x.origin_start_ms}:{x.known_at_ms}"

def build_lower_tf_witness_graph(review:ExtendedHTFReview,*,as_of_ms:int)->LowerTFWitnessGraph:
    """C16 raw provenance MUST be established upstream by an independent source replay.

    Every 1H/15m child is a potential co-occurrence only. All candidate
    parents retained; an isolated apparent match never implies author VC.
    """
    if type(as_of_ms) is not int or as_of_ms%TF_MS["15m"] or as_of_ms<0 or as_of_ms>review.as_of_ms:
        raise C18Rejected("FUTURE_OR_UNCLOSED_ASOF")
    _verify_review(review)
    try:
        higher=diagnose_htf_imb(review,as_of_ms=as_of_ms)
    except C17Rejected as e:
        raise C18Rejected("INVALID_C17_PARENT_CANDIDATES") from e
    native15=tuple(b for b in review.native_15m_closed if b.known_at_ms<=as_of_ms)
    hour=tuple(b for b in review.derived_1h_closed if b.known_at_ms<=as_of_ms)
    gaps15=_gaps(native15,"15m",review.symbol)
    gaps1h=_gaps(hour,"1h",review.symbol)
    children=gaps15+gaps1h
    parents=[]
    edges=[]
    for level in higher.candidates_1d+higher.candidates_4h:
        parent_id=_parent_id(level)
        # A contact with a still-forming HTF level is NOT observed.
        contact=tuple(b for b in native15 if
                      b.start_ms>=level.known_at_ms and
                      b.low<=level.zone_high and b.high>=level.zone_low)
        first=contact[0] if contact else None
        parents.append(HTFContactWitness(
            parent_id,level.tf,level.side,level.known_at_ms,
            first.start_ms if first else None,
            first.known_at_ms if first else None,
            first.origin_raw_row_id if first else None,
            max(0,len(contact)-1),
            "FIRST_NATIVE_15M_CONTACT_OBSERVED" if first else "NO_NATIVE_15M_CONTACT"))
        if first:
            # All three bars composing the child gap must start AFTER the
            # contact candle CLOSED, not merely the child third bar.
            for child in children:
                if child.origin_start_ms>=first.known_at_ms:
                    edges.append(CandidateAssociation(parent_id,child.id,
                                                      first.known_at_ms,child.known_at_ms))
    return LowerTFWitnessGraph(review.symbol,as_of_ms,tuple(parents),
                               gaps1h,gaps15,tuple(edges))
