"""C82 cross-referenced review packets: source-only and fail-closed.

C81 source-only queue is immutable; a generated evidence request is NOT
owner authentication, positive/negative golden or trading permission.
Source event timing is checked before drafting a reviewer request.
"""
from dataclasses import dataclass
import hashlib
from c81_source_authenticated_review_queue import QueueItem,C81Rejected

class C82Rejected(ValueError):pass

@dataclass(frozen=True)
class ReviewPacket:
    source_key:str
    priority:int
    source_group:str
    source_proof_sha256:str
    media_required:tuple
    chronology_status:str
    owner_auth_status:str="NOT_AUTHENTICATED"
    positive_golden:bool=False
    negative_golden:bool=False
    author_first_valid_poi_test:bool=False
    author_15m_trigger:bool=False
    author_15m_vc:bool=False
    author_5m_vc:bool=False
    entry_allowed:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def prepare(item, *, pinned_source_sha256):
    if type(item) is not QueueItem:
        raise C82Rejected("EXACT_C81_ITEM_REQUIRED")
    if type(pinned_source_sha256) is not str or len(pinned_source_sha256)!=64 or any(ch not in "0123456789abcdef" for ch in pinned_source_sha256):
        raise C82Rejected("SOURCE_SHA_INVALID")
    if pinned_source_sha256!=hashlib.sha256(b"C81_SOURCE_REVIEW_QUEUE_V1").hexdigest():
        raise C82Rejected("UNPINNED_SOURCE_NAMESPACE")
    if item.source_key != item.symbol+"/"+str(item.index) or item.priority not in (0,1,2,3):
        raise C82Rejected("SOURCE_CASE_KEY_OR_PRIORITY")
    if (item.author_source_authenticated or item.author_verified or item.entry_allowed or item.owner_document_anchor is not None or
        item.claimed_author_label is not None or item.reviewer_attestations or item.orders or item.fills or item.trades or item.readiness!="NOT_TRADE_READY"):
        raise C82Rejected("SPOOFED_C81_AUTHOR_RECORD")
    if item.priority==0:
        if any(type(x) is not int for x in (item.poi_created_ms,item.first_original_3m_close_ms,item.source15m_known_ms,item.first5m_known_ms)) or not (item.poi_created_ms < item.first_original_3m_close_ms < item.source15m_known_ms < item.first5m_known_ms):
            raise C82Rejected("FUTURE_OR_UNPROVEN_SOURCE_ORDER")
        if item.visits_before_source15m is None or type(item.visits_before_source15m)!=int or item.visits_before_source15m<1:
            raise C82Rejected("SOURCE_EPISODES_UNVERIFIED")
        media=("AUTHOR_POI_FIRST_VALID_TEST_POSITIVE_AND_NEGATIVE",
               "AUTHOR_15M_TRIGGER_VS_DIRECT_15M_VC_POSITIVE_AND_NEGATIVE",
               "AUTHOR_5M_VC_AFTER_15M_TRIGGER_POSITIVE_AND_NEGATIVE",
               "ORIGINAL_TIMESTAMPED_BINANCE_CRYPTO_SOURCE")
        status="SOURCE_SEQUENCE_ONLY_3M_TO_15M_TO_5M"
    elif item.priority==1:
        if item.first_original_3m_close_ms is None or item.source15m_known_ms is not None or item.first5m_known_ms is not None:
            raise C82Rejected("SOURCE_TOUCH_ONLY_MISMATCH")
        media=("AUTHOR_VALID_FIRST_POI_TEST_POSITIVE_AND_NEGATIVE",
               "AUTHOR_NO_15M_TRIGGER_OR_VC_COUNTEREXAMPLE",
               "ORIGINAL_TIMESTAMPED_BINANCE_CRYPTO_SOURCE")
        status="SOURCE_TOUCH_ONLY_NO_CONFIRMED_15M"
    elif item.priority==2:
        if item.source15m_known_ms is not None or item.first5m_known_ms is not None:
            raise C82Rejected("UNSELECTED_BRANCH_HAS_15M")
        media=("AUTHOR_OPPOSITE_OR_AMBIGUOUS_PARENT_REJECTION",
               "ORIGINAL_1H_SOURCE_SIDE_AND_TIMESTAMP")
        status="UNSELECTED_ROUTE_A_PARENT"
    else:
        if item.source15m_known_ms is not None or item.first5m_known_ms is not None:
            raise C82Rejected("NO_PARENT_WITH_CHILD")
        media=("AUTHOR_NO_NEW_1H_POI_CASE",
               "ORIGINAL_4H_PARENT_AND_1H_SOURCE")
        status="NO_NEW_SELECTED_1H_POI"
    return ReviewPacket(item.source_key,item.priority,item.source_group,pinned_source_sha256,media,status)

def review_all(queue,*,pinned_source_sha256):
    if type(queue) is not tuple or len(queue)!=153:
        raise C82Rejected("EXACT_153_SOURCE_ITEMS_REQUIRED")
    result=tuple(prepare(q,pinned_source_sha256=pinned_source_sha256) for q in queue)
    if len({x.source_key for x in result})!=153:
        raise C82Rejected("DUPLICATE_SOURCE_ID")
    if any(x.entry_allowed or x.positive_golden or x.negative_golden or x.author_first_valid_poi_test or x.author_15m_trigger or x.author_15m_vc or x.author_5m_vc or x.orders or x.fills or x.trades for x in result):
        raise C82Rejected("FORGED_OWNER_APPROVAL")
    return result
