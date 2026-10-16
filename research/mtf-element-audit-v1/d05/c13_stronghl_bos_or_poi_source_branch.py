"""B1/C13: separate author-text POI-or-BOS confirmation paths without certifying either.

Author Strong High & Low source explicitly allows VC POI OR BOS after liquidity/
inefficiency contact. C11/C12 exposes many-to-many 5m POI/IMB candidates;
C10 has a separate 5m BOS geometric event with an explicit 1h Raid UID.

Combines these *observations*, not independent author chart labels.
Crucially, 'both branches present' is never a reason to mark StrongHL, VC,
entry or SL as approved. Historical original-Futures SHA replay is separate.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re,sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"mtf-course-v05"/"src"))
from c10_two_day_original_5m_context import TwoDayReview,review_two_day_5m
from c12_attribution_ambiguity_gate import AttributionAudit,inspect_ambiguity_from_original_source
from f03_5m_original_source import Verified5m,PERIOD

class BranchRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class ConfirmationBranch:
    raid_source_uid: str
    bos_event_ids: tuple[str,...]
    imb_event_ids: tuple[str,...]
    classification: str
    attribution: str="SOURCE_GEOMETRY_ONLY_NOT_AUTHOR_CAUSAL_LABEL"
    trade_readiness: str="NOT_TRADE_READY"

@dataclass(frozen=True)
class ConfirmationBranchAudit:
    symbol: str
    as_of_ms: int
    known_raid_candidates: int
    raids_with_any_observed_branch: int
    raids_with_bos_branch: int
    raids_with_imb_branch: int
    raids_with_both_branches: int
    bos_only_raids: int
    imb_only_raids: int
    unknown_raids_without_either: int
    bos_event_count: int
    imb_pair_count: int
    distinct_imb_count: int
    parent_bos_links: tuple[ConfirmationBranch,...]
    author_stronghl_approvals: int=0
    author_vc_approvals: int=0
    academic_status: str="UNLABELLED_BOS_OR_POI_PATHS_NOT_STRONGHL_CERTIFICATE"
    readiness: str="NOT_TRADE_READY"

def compare_geometric_confirmation_routes(
    bos:TwoDayReview,poi:AttributionAudit
)->ConfirmationBranchAudit:
    if not isinstance(bos,TwoDayReview) or not isinstance(poi,AttributionAudit):
        raise BranchRejected("INVALID_PRICE_SOURCE_REVIEW_PAIR")
    if (bos.symbol!=poi.symbol or bos.as_of_ms!=poi.as_of_ms
        or bos.closed_5m_count!=poi.as_of_ms*0+bos.closed_1h_count*12
        or poi.closed_1h_count*12>poi.closed_5m_count) if hasattr(poi,"closed_1h_count") else False:
        # AttributionAudit intentionally does not copy entire price prefix;
        # the explicit simple cross-review guards below are authoritative.
        raise BranchRejected("UNSUPPORTED_OR_INCOMPATIBLE_SOURCE_REVIEW")
    if (bos.symbol!=poi.symbol or bos.as_of_ms!=poi.as_of_ms
        or bos.confirmed_1h_raids!=poi.total_known_raid_candidates):
        raise BranchRejected("SOURCE_OR_RAID_COUNTS_DISAGREE")
    if (bos.readiness!="NOT_TRADE_READY" or poi.readiness!="NOT_TRADE_READY"
        or bos.approval!="PRICE_GEOMETRY_V05_NOT_AUTHOR_STRONGHL_VC_POI"
        or poi.author_stronghl_approvals or poi.author_vc_approvals):
        raise BranchRejected("FAKE_ALREADY_CERTIFIED_AUTHOR_EVENT")
    if not isinstance(bos.source_raid_bos,tuple) or not isinstance(poi.nodes,tuple):
        raise BranchRejected("INVALID_SOURCE_EVENT_SETS")
    raid_imb={}
    imbs=set()
    for n in poi.nodes:
        if n.readiness!="NOT_TRADE_READY" or n.author_attribution!="NOT_RESOLVED_BY_ACADEMIC_SOURCE":
            raise BranchRejected("FORGED_AUTHOR_ATTRIBUTION")
        if len(n.connected_uids)!=n.observed_edge_count or len(set(n.connected_uids))!=len(n.connected_uids):
            raise BranchRejected("INCONSISTENT_OR_DUPLICATE_EDGE_NODE")
        if n.node_type=="LIQUIDITY_RAID":
            if n.source_uid in raid_imb:
                raise BranchRejected("DUPLICATE_PARENT_RAID_NODE")
            raid_imb[n.source_uid]=tuple(n.connected_uids)
        elif n.node_type=="5M_CLASSIC_IMB":
            if n.source_uid in imbs:
                raise BranchRejected("DUPLICATE_CHILD_IMB_NODE")
            imbs.add(n.source_uid)
        else:
            raise BranchRejected("UNRECOGNIZED_GRAPH_NODE_TYPE")
    if set(y for links in raid_imb.values() for y in links)!=imbs:
        raise BranchRejected("RAID_IMB_GRAPH_NODE_MISMATCH")
    if sum(len(xs) for xs in raid_imb.values())!=poi.total_raid_imb_edges:
        raise BranchRejected("RAID_IMB_EDGE_COUNT_MISMATCH")
    if len(imbs)!=poi.unique_imb_nodes_with_edges or len(raid_imb)!=poi.raid_nodes_with_edges:
        raise BranchRejected("BIPARTITE_GRAPH_CARDINALITY_MISMATCH")
    raid_bos={}
    bos_ids=set()
    for w in bos.source_raid_bos:
        if (not w.raid_id or not w.bos_id or w.bos_id in bos_ids
            or not w.bos_id.startswith("5m:BOS:")
            or not w.bos_id.endswith(":"+w.raid_id)
            or not w.raid_id.startswith("1h:RAID:")
            or not w.raid_known<w.bos_known<=bos.as_of_ms or w.bos_known%PERIOD
            or not re.fullmatch(r"[0-9a-f]{64}",w.original_day_zip_sha256)
            or not w.original_bar_id.startswith(w.original_day_zip_sha256+":")
            or int(w.original_bar_id.rsplit(":",1)[1])+PERIOD!=w.bos_known):
            raise BranchRejected("INVALID_SOURCE_BOS_PARENT_OR_BAR_PROOF")
        bos_ids.add(w.bos_id)
        raid_bos.setdefault(w.raid_id,set()).add(w.bos_id)
    parents=sorted(set(raid_imb)|set(raid_bos))
    if len(parents)>bos.confirmed_1h_raids:
        raise BranchRejected("MORE_BRANCH_RAIDS_THAN_CONFIRMED_RAID_EVENTS")
    output=[]
    for id in parents:
        bs=tuple(sorted(raid_bos.get(id,())))
        ims=tuple(sorted(raid_imb.get(id,())))
        classification=("BOTH_BOS_AND_IMB_GEOMETRY_NOT_AUTHOR_CERTIFIED" if bs and ims
                        else "BOS_ONLY_GEOMETRY_NOT_AUTHOR_CERTIFIED" if bs
                        else "IMB_ONLY_GEOMETRY_NOT_AUTHOR_CERTIFIED")
        output.append(ConfirmationBranch(id,bs,ims,classification))
    both=sum(bool(x.bos_event_ids) and bool(x.imb_event_ids) for x in output)
    boscount=sum(bool(x.bos_event_ids) for x in output)
    imbcount=sum(bool(x.imb_event_ids) for x in output)
    return ConfirmationBranchAudit(
        bos.symbol,bos.as_of_ms,bos.confirmed_1h_raids,len(parents),
        boscount,imbcount,both,boscount-both,imbcount-both,
        bos.confirmed_1h_raids-len(parents),len(bos_ids),
        poi.total_raid_imb_edges,len(imbs),tuple(output))

def inspect_both_author_branches(
    first:Verified5m,second:Verified5m,as_of_ms:int
)->ConfirmationBranchAudit:
    """Existing source checks are reused, not replaced by self-declared labels."""
    b=review_two_day_5m(first,second,as_of_ms)
    g=inspect_ambiguity_from_original_source(first,second,as_of_ms)
    return compare_geometric_confirmation_routes(b,g)
