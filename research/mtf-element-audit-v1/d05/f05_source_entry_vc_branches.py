"""D05/F05 — source-derived Entry by IMB/SNR branch contracts (PAPER ONLY).

Author source:
 https://drive.google.com/file/d/1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ/view
 StrongHL:
 https://drive.google.com/file/d/1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t/view

These types express COURSE RELATIONSHIPS, NOT automatic chart-recognized
events. Self-declared event evidence cannot certify academic VC, StrongHL,
entries, or valid risk. Every result remains NOT_TRADE_READY.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

STEPS={
 "4H_POI_TEST":("4h",("IMB","SNR","RB","LIQUIDITY")),
 "4H_LIQUIDITY_RAID":("4h",("BSL","SSL")),
 "1H_TRIGGER":("1h",("BSL","SSL","IMB")),
 "1H_VC_NEW_POI":("1h",("IMB","SNR","RB")),
 "1H_POI_TEST":("1h",("IMB","SNR","RB")),
 "15M_TRIGGER":("15m",("BSL","SSL","IMB")),
 "15M_VC_ENTRY":("15m",("IMB","SNR")),
 "15M_VC_NEW_POI":("15m",("IMB","SNR")),
 "5M_VC_ENTRY":("5m",("IMB","SNR")),
}
TFMS={"1d":86400000,"4h":14400000,"1h":3600000,"15m":900000,"5m":300000}
RESULTS={
 "4H_TEST_1H_TRIGGER_15M_VC":("4H_POI_TEST","1H_TRIGGER","15M_VC_ENTRY"),
 "4H_TEST_1H_VC_POI_TEST_15M_VC":("4H_POI_TEST","1H_VC_NEW_POI","1H_POI_TEST","15M_VC_ENTRY"),
 "4H_TEST_1H_VC_POI_TEST_15M_TRIGGER_5M_VC":(
    "4H_POI_TEST","1H_VC_NEW_POI","1H_POI_TEST","15M_TRIGGER","5M_VC_ENTRY"),
 "4H_RAID_1H_VC_POI_TEST_15M_VC":(
    "4H_LIQUIDITY_RAID","1H_VC_NEW_POI","1H_POI_TEST","15M_VC_ENTRY"),
 "4H_RAID_1H_VC_POI_TEST_15M_TRIGGER_5M_VC":(
    "4H_LIQUIDITY_RAID","1H_VC_NEW_POI","1H_POI_TEST","15M_TRIGGER","5M_VC_ENTRY"),
}
SUPPORTED_MARKET="BINANCE_USDM_FUTURES"

class EntryCourseRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class ClaimedStage:
    role: str
    kind: str
    tf: str
    source_id: str
    symbol: str
    known_at_ms: int
    parent_source_id: Optional[str]=None
    market: str=SUPPORTED_MARKET
    course_verified: bool=False
    price_geometry_verified: bool=False

@dataclass(frozen=True)
class EntryBranchReview:
    route: str
    observed_stage_ids: tuple[str,...]
    required_remaining_roles: tuple[str,...]
    entry_vc_tf: str
    entry_vc_types: tuple[str,...]=("IMB","SNR")
    strong_hl_certificate: str="MISSING_INDEPENDENT_CONTACT_PLUS_VC_OR_BOS"
    fta_timeframe: str="4h"
    academic_semantics: str="CLAIMED_STAGES_NOT_AUTHOR_PRICE_LABELS"
    status: str="COURSE_BRANCH_TOPOLOGY_ONLY"
    readiness: str="NOT_TRADE_READY"

def inspect_source_entry_branch(route:str,stages:list[ClaimedStage],as_of_ms:int)->EntryBranchReview:
    if route not in RESULTS:
        raise EntryCourseRejected("UNKNOWN_AUTHOR_BRANCH")
    if type(as_of_ms) is not int or as_of_ms<0:
        raise EntryCourseRejected("BAD_AS_OF")
    if not isinstance(stages,list) or any(not isinstance(s,ClaimedStage) for s in stages):
        raise EntryCourseRejected("INVALID_COURSE_STAGE")
    expected=RESULTS[route]
    if len(stages)>len(expected) or tuple(s.role for s in stages)!=expected[:len(stages)]:
        raise EntryCourseRejected("UNEXPECTED_PARENT_TRIGGER_VC_SEQUENCE")
    if any(not s.source_id or not isinstance(s.source_id,str) for s in stages):
        raise EntryCourseRejected("MISSING_SOURCE_EVENT_ID")
    if len({s.source_id for s in stages})!=len(stages):
        raise EntryCourseRejected("REPEATED_SOURCE_EVENT")
    if stages and (not stages[0].symbol or any(s.symbol!=stages[0].symbol for s in stages)):
        raise EntryCourseRejected("CROSS_SYMBOL_CONTEXT")
    previous=-1
    for index,s in enumerate(stages):
        tf,kinds=STEPS[s.role]
        if s.tf!=tf or s.kind not in kinds:
            raise EntryCourseRejected("UNAUTHORIZED_VC_OR_WRONG_TIMEFRAME")
        if s.market!=SUPPORTED_MARKET:
            raise EntryCourseRejected("INVALID_MARKET")
        if type(s.known_at_ms) is not int or s.known_at_ms%TFMS[tf]!=0:
            raise EntryCourseRejected("UNCLOSED_STAGE_EVIDENCE")
        if s.known_at_ms>as_of_ms or s.known_at_ms<previous:
            raise EntryCourseRejected("FUTURE_OR_NONMONOTONIC_STAGE")
        if s.course_verified or s.price_geometry_verified:
            raise EntryCourseRejected("SELF_DECLARED_ACADEMIC_OR_PRICE_ATTESTATION")
        if index>0 and s.parent_source_id!=stages[index-1].source_id:
            raise EntryCourseRejected("UNLINKED_PARENT_STAGE")
        if index==0 and s.parent_source_id is not None:
            raise EntryCourseRejected("ROOT_CANNOT_HAVE_UNPROVED_PARENT")
        previous=s.known_at_ms
    if stages:
        parent=stages[0]
        if parent.role=="4H_POI_TEST":
            for s in stages:
                if s.role=="1H_TRIGGER" and s.kind=="IMB" and parent.kind=="IMB":
                    raise EntryCourseRejected("1H_IMB_TRIGGER_INSIDE_4H_IMB_FORBIDDEN")
                if s.role=="15M_TRIGGER" and s.kind=="IMB":
                    # The original lesson allows IMB triggers only with
                    # a source-grounded RB/SNR support zone; here the only
                    # available supporting 1h context is the newly formed
                    # and subsequently tested 1h POI.
                    support=next((e.kind for e in stages if e.role=="1H_VC_NEW_POI"),None)
                    if support not in ("RB","SNR"):
                        raise EntryCourseRejected("15M_IMB_TRIGGER_REQUIRES_UNPROVED_RB_SNR")
        for s in stages:
            if s.role=="1H_TRIGGER" and s.kind=="IMB" and parent.kind not in ("RB","SNR"):
                raise EntryCourseRejected("IMB_TRIGGER_REQUIRES_RB_OR_SNR_SUPPORT")
            if s.role=="15M_TRIGGER" and s.kind=="IMB":
                support=next((e.kind for e in stages if e.role=="1H_VC_NEW_POI"),None)
                if support not in ("RB","SNR"):
                    raise EntryCourseRejected("15M_IMB_TRIGGER_REQUIRES_UNPROVED_RB_SNR")
    missing=expected[len(stages):]
    return EntryBranchReview(route,tuple(s.source_id for s in stages),missing,
                             "5m" if expected[-1]=="5M_VC_ENTRY" else "15m")

def inspect_idm_bypass_claim(*, high_tf_vc_claimed:bool, strong_hl_claimed:bool,
                             trigger_tf:str,entry_tf:str)->str:
    """IDM is a *different entry mechanics*: no extra LTF VC is universally required.

    Returns type of unresolved proof, NEVER an executable order.
    """
    if (trigger_tf,entry_tf) not in (("4h","1h"),("1h","15m")):
        raise EntryCourseRejected("UNSUPPORTED_AUTHOR_IDM_HIERARCHY")
    if not high_tf_vc_claimed or not strong_hl_claimed:
        return "IDM_SOURCE_VC_OR_STRONGHL_EVIDENCE_MISSING"
    return "IDM_BYPASS_ALLOWED_BY_SOURCE_NOT_AUTHOR_CERTIFIED_NO_ORDER"
