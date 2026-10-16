"""B1/C12 — ambiguous liquidity-contact-to-IMB attribution audit.

Academic sources say StrongHL needs contact with liquidity/inefficiency AND
a resulting POI/BOS confirmation. They DO NOT define a universally unique
first/nearest/fixed-TTL association between a raid and a later 5m IMB.

C11 enumerates actual geometric candidates. This module exposes both sides
of that bipartite relation, NEVER chooses one IMB/raid automatically and
NEVER produces an academic StrongHL, VC, paper-ready intent or order.

Only the independent network replay can corroborate raw F06 source ZIP+CSV.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from c11_contact_imb_source_witness import (
    ContactImbPriceWitness,ContactImbReview,StrongCandidateRejected,inspect_contact_then_5m_imb
)
from f03_5m_original_source import Verified5m,PERIOD

class AttributionRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class AttributionNode:
    node_type: str
    source_uid: str
    connected_uids: tuple[str,...]
    observed_edge_count: int
    classification: str
    author_attribution: str="NOT_RESOLVED_BY_ACADEMIC_SOURCE"
    readiness: str="NOT_TRADE_READY"

@dataclass(frozen=True)
class AttributionAudit:
    symbol: str
    as_of_ms: int
    total_raid_imb_edges: int
    total_known_raid_candidates: int
    raid_nodes_with_edges: int
    unique_imb_nodes_with_edges: int
    raids_with_multiple_imbs: int
    imbs_with_multiple_raids: int
    edges_touching_zone_later: int
    edges_without_later_zone_touch: int
    nodes: tuple[AttributionNode,...]
    diagnostic: str="BIPARTITE_CANDIDATES_NO_AUTOMATIC_PARENT_ASSIGNMENT"
    author_stronghl_approvals: int=0
    author_vc_approvals: int=0
    readiness: str="NOT_TRADE_READY"

def audit_ambiguous_edges(review:ContactImbReview)->AttributionAudit:
    """Deterministic graph diagnostic, intentionally not a source oracle.

    No external serialized graph is allowed to claim certification; even
    a 1↔1 geometric match has unverified author semantics.
    """
    if not isinstance(review,ContactImbReview) or review.readiness!="NOT_TRADE_READY":
        raise AttributionRejected("UNTRUSTED_OR_READY_CONTACT_REVIEW")
    if (type(review.as_of_ms) is not int or review.as_of_ms%PERIOD
        or review.closed_5m_count<0 or review.closed_1h_count*12>review.closed_5m_count
        or review.raid_contact_candidates<0 or review.post_raid_5m_imb_candidates<0):
        raise AttributionRejected("INVALID_CLOSED_SOURCE_REVIEW")
    witnesses=review.paired_source_price_witnesses
    if (len(witnesses)!=review.post_raid_5m_imb_candidates
        or not isinstance(witnesses,tuple)):
        raise AttributionRejected("C11_EDGE_COUNT_INCONSISTENT")
    raided:dict[str,set[str]]={}
    imbs:dict[str,set[str]]={}
    seen=set()
    same_imb={}
    touched=0
    for w in witnesses:
        if not isinstance(w,ContactImbPriceWitness):
            raise AttributionRejected("NOT_A_C11_PRICE_WITNESS")
        if (w.source_symbol!=review.symbol or w.side not in ("LONG","SHORT")
            or w.academic_status!="STRONGHL_AND_VC_NOT_AUTHOR_CERTIFIED"
            or w.readiness!="NOT_TRADE_READY"):
            raise AttributionRejected("CROSS_SYMBOL_OR_FAKE_STRONGHL")
        if (not w.contact_1h_raid_uid or not w.confirmation_5m_imb_uid
            or not w.contact_source_5m_id or not w.confirmation_source_5m_id
            or w.confirmation_known_ms%PERIOD
            or w.contact_known_ms%3600000
            or not 0<=w.contact_known_ms<w.confirmation_known_ms<=review.as_of_ms):
            raise AttributionRejected("INVALID_CONTACT_TO_IMB_CAUSAL_TIME")
        if (not 0<w.poi_low<w.poi_high
            or not re.fullmatch(r"[0-9a-f]{64}:[0-9]+",w.contact_source_5m_id)
            or not re.fullmatch(r"[0-9a-f]{64}:[0-9]+",w.confirmation_source_5m_id)):
            raise AttributionRejected("UNBOUND_OR_BAD_RAW_SOURCE_REFERENCE")
        try:
            contact_open=int(w.contact_source_5m_id.rsplit(":",1)[1])
            imb_open=int(w.confirmation_source_5m_id.rsplit(":",1)[1])
        except ValueError as e:
            raise AttributionRejected("SOURCE_TIMESTAMP_BAD") from e
        if not (w.contact_known_ms-3600000<=contact_open<w.contact_known_ms
                and imb_open+PERIOD==w.confirmation_known_ms):
            raise AttributionRejected("RAW_SOURCE_CLOSE_MISMATCH")
        touch=w.first_later_poi_test_known_ms
        if (touch is None)!=(w.first_later_poi_test_source_id is None):
            raise AttributionRejected("UNPAIRED_FIRST_ZONE_TOUCH")
        if touch is not None:
            if (type(touch) is not int or touch%PERIOD or
                touch<=w.confirmation_known_ms or touch>review.as_of_ms or
                not re.fullmatch(r"[0-9a-f]{64}:[0-9]+",w.first_later_poi_test_source_id)
                or int(w.first_later_poi_test_source_id.rsplit(":",1)[1])+PERIOD!=touch):
                raise AttributionRejected("RETROSPECTIVE_OR_FUTURE_FIRST_TEST")
            touched+=1
        edge=(w.contact_1h_raid_uid,w.confirmation_5m_imb_uid)
        if edge in seen:
            raise AttributionRejected("DUPLICATE_CAUSAL_EDGE")
        seen.add(edge)
        # Same IMB in multiple candidate parents must have identical raw
        # geometry + first possible touch; conflicting reused IDs are fake.
        imm=(w.side,w.confirmation_source_5m_id,w.confirmation_known_ms,
             w.poi_low,w.poi_high,w.first_later_poi_test_known_ms,
             w.first_later_poi_test_source_id)
        old=same_imb.setdefault(w.confirmation_5m_imb_uid,imm)
        if old!=imm:
            raise AttributionRejected("FORGED_DUPLICATED_IMB_GEOMETRY")
        raided.setdefault(edge[0],set()).add(edge[1])
        imbs.setdefault(edge[1],set()).add(edge[0])
    if len(raided)>review.raid_contact_candidates:
        raise AttributionRejected("MORE_PARENT_RAIDS_THAN_SOURCE_OBSERVATIONS")
    out=[]
    for rid,imb_uids in sorted(raided.items()):
        out.append(AttributionNode(
            "LIQUIDITY_RAID",rid,tuple(sorted(imb_uids)),len(imb_uids),
            "MULTIPLE_GEOMETRIC_IMBS_NO_AUTHOR_CHOICE" if len(imb_uids)>1
            else "SINGLE_GEOMETRIC_MATCH_STILL_UNCERTIFIED"))
    for uid,raid_uids in sorted(imbs.items()):
        out.append(AttributionNode(
            "5M_CLASSIC_IMB",uid,tuple(sorted(raid_uids)),len(raid_uids),
            "MULTIPLE_PARENT_RAIDS_NO_AUTHOR_CHOICE" if len(raid_uids)>1
            else "SINGLE_GEOMETRIC_MATCH_STILL_UNCERTIFIED"))
    return AttributionAudit(review.symbol,review.as_of_ms,len(witnesses),
                            review.raid_contact_candidates,len(raided),len(imbs),
                            sum(len(s)>1 for s in raided.values()),
                            sum(len(s)>1 for s in imbs.values()),
                            touched,len(witnesses)-touched,tuple(out))

def inspect_ambiguity_from_original_source(
    first:Verified5m,second:Verified5m,as_of_ms:int
)->AttributionAudit:
    """Call the existing C11 source+known-at gate, then classify all edges."""
    try:
        review=inspect_contact_then_5m_imb(first,second,as_of_ms)
    except StrongCandidateRejected as e:
        raise AttributionRejected("INVALID_TWO_DAY_SOURCE_PREFIX") from e
    return audit_ambiguous_edges(review)
