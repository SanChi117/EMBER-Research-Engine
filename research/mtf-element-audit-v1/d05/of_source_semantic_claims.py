"""D05/F02: Order Flow source requirement graph, NOT an OHLC detector.

Original Order Flow lesson requires liquidity work + imbalances; Strong HL
at same or lower TF supports a link. Target reach does not auto-invalidate.
Structural BOS or opposing same-TF POI can indicate *possible* invalidation.
Caller event labels are NOT independently verified; never set READY.
Source: https://drive.google.com/file/d/1r6sH0XjEoK4Jwq4EVLz8vqPSWVh9qerN/view
"""
from __future__ import annotations
from dataclasses import dataclass
TF={"1d":86400000,"4h":14400000,"1h":3600000,"15m":900000,"5m":300000}
KINDS=frozenset(("LIQUIDITY_WORK","IMBALANCE","STRONG_HL_VC",
                 "HTF_TARGET","STRUCTURE_BOS","OPPOSITE_POI"))
class OFSourceRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class OFClaim:
    kind: str
    side: str
    timeframe: str
    known_at_ms: int
    symbol: str
    source_uid: str
    market: str="BINANCE_USDM_FUTURES"

@dataclass(frozen=True)
class OFReview:
    side: str
    source_timeframe: str
    as_of_ms: int
    evidence_uid_sequence: tuple[str,...]
    composition: str
    link_volume_evidence: str
    target_status: str
    invalidation_status: str
    semantic_status: str="COURSE_EVENT_LABELS_ARE_CALLER_DECLARED_NOT_PRICE_CERTIFIED"
    readiness: str="NOT_TRADE_READY"

def inspect_of_source_claims(side:str,timeframe:str,symbol:str,
                             claims:list[OFClaim],as_of_ms:int)->OFReview:
    """Read-only checks of instructor-stated relationships, never trades."""
    if side not in ("LONG","SHORT") or timeframe not in TF or not isinstance(symbol,str) or not symbol:
        raise OFSourceRejected("INVALID_OF_CONTEXT")
    if type(as_of_ms) is not int or as_of_ms<0:
        raise OFSourceRejected("INVALID_AS_OF")
    if not isinstance(claims,list) or any(not isinstance(e,OFClaim) for e in claims):
        raise OFSourceRejected("INVALID_SOURCE_EVENTS")
    if len({e.source_uid for e in claims})!=len(claims) or any(not e.source_uid for e in claims):
        raise OFSourceRejected("DUPLICATE_OR_MISSING_EVIDENCE_SOURCE")
    last=-1
    for e in claims:
        if e.kind not in KINDS or e.timeframe not in TF:
            raise OFSourceRejected("UNRECOGNIZED_EVENT_KIND_OR_TF")
        if e.symbol!=symbol or e.market!="BINANCE_USDM_FUTURES":
            raise OFSourceRejected("WRONG_MARKET_OR_SYMBOL")
        if type(e.known_at_ms) is not int or e.known_at_ms>as_of_ms or e.known_at_ms<last:
            raise OFSourceRejected("UNSORTED_OR_FUTURE_EVENT")
        if e.known_at_ms%TF[e.timeframe]:
            raise OFSourceRejected("EVENT_KNOWN_BEFORE_OWN_TF_CLOSE")
        if e.kind=="OPPOSITE_POI" and e.timeframe!=timeframe:
            raise OFSourceRejected("OPPOSITE_POI_MUST_BE_SAME_OF_TF")
        if e.kind=="STRONG_HL_VC" and TF[e.timeframe]>TF[timeframe]:
            raise OFSourceRejected("STRONG_HL_VC_ABOVE_SOURCE_OF_TF")
        wanted=("SHORT" if side=="LONG" else "LONG") if e.kind in ("OPPOSITE_POI","STRUCTURE_BOS") else side
        if e.side!=wanted:
            raise OFSourceRejected("WRONG_EVENT_SIDE_FOR_OF_ROLE")
        last=e.known_at_ms
    kinds={e.kind for e in claims}
    composition=("OF_COMPONENTS_PRESENT_NOT_AUTHOR_CERTIFIED"
                 if {"LIQUIDITY_WORK","IMBALANCE"}<=kinds
                 else "OF_COMPONENTS_MISSING_LIQUIDITY_OR_IMBALANCE")
    strong=("STRONG_HL_VC_CLAIM_UNVERIFIED" if "STRONG_HL_VC" in kinds
            else "STRONG_HL_VC_NOT_EVIDENCED")
    target=("HTF_TARGET_CLAIM_NOT_AUTOMATIC_INVALIDATION" if "HTF_TARGET" in kinds
            else "HTF_TARGET_UNOBSERVED")
    invalid=("POSSIBLE_INVALIDATION_BY_STRUCTURE_OR_OPPOSITE_POI_NOT_CERTIFIED"
             if "STRUCTURE_BOS" in kinds or "OPPOSITE_POI" in kinds
             else "NO_INVALIDATION_CLAIM")
    return OFReview(side,timeframe,as_of_ms,tuple(e.source_uid for e in claims),
                    composition,strong,target,invalid)
