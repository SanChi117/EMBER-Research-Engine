"""C81 immutable original-crypto Route A review queue; zero author labels.

The 153 source contexts are price-evidence only. A queue item never
constitutes an author goldens, entry, score, or claimed profitable setup.
Owner references need independent media examination and negative cases.
"""
from dataclasses import dataclass
from collections import Counter
import hashlib,json

C73_SHA="c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b"
C72_GIT_BLOB="19b7e0357600b70b3f26467339a417e0f99a1302"
AUTHOR_LABELS=tuple()
SYMS={"BCHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT"}
NO="NOT_NEW_1H_POI_SOURCE_BRANCH"
UN="NEW_1H_POI_SOURCE_NO_ORIGINAL3M_FIRST_TOUCH"
FIRST="NEW_1H_POI_FIRST_ANY_RAW3M_TOUCH_NO_UNAMBIGUOUS_15M_CHAIN"
ONE="NEW_1H_POI_FIRST_15M_PATTERN_SINGLE_SOURCE_VISIT_NOT_OWNER_VALID"
MULTI="NEW_1H_POI_FIRST_15M_PATTERN_REVISITED_SOURCE_POI_NOT_OWNER_VALID"
ALLOWED={"FIRST_ANY_1H_SOURCE_OPPOSITE_SIDE",
 "FIRST_ANY_1H_TRIGGER_AND_VC_AMBIGUOUS","FIRST_ANY_1H_TWO_SIDES_AMBIGUOUS"}
FIVE={"FIRST_5M_IMB_ALIGNED_NOT_AUTHOR_VC":"ALIGNED",
      "FIRST_5M_SNR_ALIGNED_NOT_AUTHOR_VC":"ALIGNED",
      "FIRST_5M_SOURCE_OPPOSITE_SIDE":"OPPOSITE",
      "FIRST_5M_SOURCE_MULTIPLE_KINDS_AMBIGUOUS":"AMBIGUOUS"}
LABELS=("VALID_FIRST_1H_POI_TEST","15M_TRIGGER","DIRECT_15M_VC","5M_VC","STRONGHL")
class C81Rejected(ValueError):pass
@dataclass(frozen=True)
class QueueItem:
    source_key:str
    symbol:str
    index:int
    side:str
    priority:int
    source_group:str
    poi_kind:str
    poi_created_ms:int|None
    poi_low:str|None
    poi_high:str|None
    first_original_3m_id:str|None
    first_original_3m_close_ms:int|None
    source15m_kind:str
    source15m_known_ms:int|None
    first5m_kind:str
    first5m_known_ms:int|None
    visits_before_source15m:int|None
    parent_fork:str
    owner_document_anchor:str|None=None
    claimed_author_label:str|None=None
    author_source_authenticated:bool=False
    reviewer_attestations:tuple=()
    author_verified:bool=False
    entry_allowed:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def build(c73,c72):
    """Build only from exact archived source bytes, never from self-report."""
    if type(c73) is not bytes or type(c72) is not bytes:
        raise C81Rejected("ORIGINAL_BYTES_REQUIRED")
    if hashlib.sha256(c73).hexdigest()!=C73_SHA:
        raise C81Rejected("FROZEN_C73_SHA_MISMATCH")
    if hashlib.sha1(b"blob "+str(len(c72)).encode()+b"\0"+c72).hexdigest()!=C72_GIT_BLOB:
        raise C81Rejected("FROZEN_C72_GIT_BLOB_MISMATCH")
    a,b=json.loads(c73),json.loads(c72)
    if a.get("readiness")!="NOT_TRADE_READY" or b.get("readiness")!="NOT_TRADE_READY":
        raise C81Rejected("UNTRUSTED_SOURCE_READINESS")
    look={}
    for m in b["markets"]:
        for x in m["original_parent_source_cases"]:
            key=m["symbol"],x["original_c46_4h_parent_index"]
            if key in look:raise C81Rejected("DUPLICATE_C72_KEY")
            look[key]=x
    if len(look)!=153:raise C81Rejected("C72_NOT_153")
    items=[];seen=set()
    for m in a["markets"]:
        sym=m["symbol"]
        if sym not in SYMS:raise C81Rejected("BAD_SYMBOL")
        for p in m["original_parent_source_cases"]:
            i=p["original_c46_4h_parent_index"]
            key=(sym,i)
            if key in seen or key not in look:raise C81Rejected("INVALID_SOURCE_JOIN")
            seen.add(key);q=look[key]
            if q["side"]!=p["side"] or q["c67_route_a_source_fork_state"]!=p["c67_route_a_source_fork_state"]:
                raise C81Rejected("C73_C72_SIDE_FORK")
            if p["source_first_5m_after_candidate_state"]!=q["state"] or p["c72_post_15m_first_any_5m_source_state"]!=q["state"]:
                raise C81Rejected("C72_FIRST_SOURCE_STATE_CHANGED")
            if any(p[k] is not False for k in ("author_entry","author_15m_trigger","author_15m_vc","author_5m_vc","route_b_idm_used","route_c_raid_bos_used")):
                raise C81Rejected("AUTHOR_OR_ROUTE_PROMOTION")
            if p["orders"] or p["trades"] or p["fills"] or q["orders"] or q["trades"] or q["fills"]:
                raise C81Rejected("FORGED_EXECUTION")
            state=p["state"]; fork=p["c67_route_a_source_fork_state"]
            t=p["original_first_source3m_touch_closed_ms"]
            at=p["first_source15m_event_fully_known_ms"]
            five=q["first_any_5m_event_known_ms"]
            if state==NO:
                group="NO_SELECTED_NEW_1H_POI";priority=3
                if t is not None or at is not None or five is not None:raise C81Rejected("NO_PARENT_HAS_EVENT")
            elif state==UN:
                group="UNSELECTED_OPPOSITE_OR_AMBIGUOUS";priority=2
                if fork not in ALLOWED or t is not None or at is not None or five is not None:
                    raise C81Rejected("UNSELECTED_ROUTE_PROMOTION")
            elif state==FIRST:
                group="SELECTED_PHYSICAL_3M_TOUCH_ONLY";priority=1
                if not fork.startswith("NEW_1H_VC_FIRST_SOURCE_TEST_") or t is None or at is not None or five is not None:
                    raise C81Rejected("FIRST_TOUCH_ROUTE_PROMOTION")
            elif state in (ONE,MULTI):
                group="SELECTED_15M_5M_SOURCE_REVIEW";priority=0
                if not fork.startswith("NEW_1H_VC_FIRST_SOURCE_TEST_") or any(type(z) is not int for z in (t,at,five)) or not t<at<five:
                    raise C81Rejected("SOURCE_CAUSAL_CLOCK_OR_ROUTE_INVALID")
                if q["state"] not in FIVE:
                    raise C81Rejected("INVALID_5M_SOURCE")
                ep=p["episodes_before_first_15m_pattern"]
                if type(ep) is not int or (state==ONE and ep!=1) or (state==MULTI and ep<2):
                    raise C81Rejected("SOURCE_VISITS_INCORRECT")
            else:raise C81Rejected("UNKNOWN_STATE")
            items.append(QueueItem(
                source_key=sym+"/"+str(i),symbol=sym,index=i,side=p["side"],
                priority=priority,source_group=group,
                poi_kind=p["source_1h_poi_kind"] or "NO_NEW_1H_POI",
                poi_created_ms=p["source_1h_poi_created_at_ms"],
                poi_low=p["source_1h_poi_bottom"],poi_high=p["source_1h_poi_top"],
                first_original_3m_id=p["original_first_source3m_touch_id"],
                first_original_3m_close_ms=t,
                source15m_kind=p["c71_first_any_15m_source_state"],
                source15m_known_ms=at,
                first5m_kind=q["state"],first5m_known_ms=five,
                visits_before_source15m=p["episodes_before_first_15m_pattern"],
                parent_fork=fork))
    if len(seen)!=len(items)!=153:
        raise C81Rejected("INCOMPLETE_SOURCE")
    result=tuple(sorted(items,key=lambda x:(x.priority,x.symbol,x.index)))
    totals=Counter(x.source_group for x in result)
    if totals!={"NO_SELECTED_NEW_1H_POI":47,
               "UNSELECTED_OPPOSITE_OR_AMBIGUOUS":71,
               "SELECTED_PHYSICAL_3M_TOUCH_ONLY":23,
               "SELECTED_15M_5M_SOURCE_REVIEW":12}:
        raise C81Rejected("FROZEN_COUNTS_DRIFT")
    return result

def validate_queue(queue):
    if type(queue) is not tuple or len(queue)!=153 or any(type(x) is not QueueItem for x in queue):
        raise C81Rejected("EXACT_SOURCE_QUEUE_REQUIRED")
    keys=set()
    for n,x in enumerate(queue):
        if x.source_key in keys or x.source_key!=x.symbol+"/"+str(x.index):
            raise C81Rejected("CASE_ID_COLLISION")
        keys.add(x.source_key)
        if x.priority not in (0,1,2,3) or (n and (queue[n-1].priority,queue[n-1].symbol,queue[n-1].index)>(x.priority,x.symbol,x.index)):
            raise C81Rejected("ORDER_OR_PRIORITY_DRIFT")
        if x.owner_document_anchor is not None or x.claimed_author_label is not None or x.author_source_authenticated or x.reviewer_attestations or x.author_verified or x.entry_allowed or x.orders or x.fills or x.trades or x.readiness!="NOT_TRADE_READY":
            raise C81Rejected("IMPERSONATED_GOLDEN_OR_TRADE")
    return {"total":len(queue),
            "priority_counts":dict(sorted(Counter(x.priority for x in queue).items())),
            "source_groups":dict(sorted(Counter(x.source_group for x in queue).items())),
            "owner_review_verified":0,"proven_positive_goldens":0,"proven_negative_goldens":0,
            "orders":0,"fills":0,"trades":0,"readiness":"NOT_TRADE_READY"}

def submit_for_review(source_item, *, document_sha256, source_anchor, reviewer_declared):
    """Return QUARANTINE ONLY. Arbitrary source/reviewer hashes prove nothing."""
    if type(source_item) is not QueueItem or source_item.author_verified or source_item.entry_allowed:
        raise C81Rejected("FORGED_PARENT")
    if type(document_sha256) is not str or len(document_sha256)!=64 or any(c not in "0123456789abcdef" for c in document_sha256):
        raise C81Rejected("BAD_UNVERIFIED_MEDIA_HASH")
    if type(source_anchor) is not str or not 1<=len(source_anchor)<=240:
        raise C81Rejected("BAD_SOURCE_ANCHOR")
    if type(reviewer_declared) is not str or not 1<=len(reviewer_declared)<=180:
        raise C81Rejected("BAD_REVIEWER_DECLARATION")
    return {"case":source_item.source_key,
            "review_status":"QUARANTINED_EXTERNAL_OWNER_MEDIA_UNAUTHENTICATED",
            "source_media_sha256_claim":document_sha256,
            "source_anchor_claim":source_anchor,
            "author_verified":False,
            "independent_reviewer_verification_complete":False,
            "entry_allowed":False,"orders":[],"fills":[],"trades":[],
            "readiness":"NOT_TRADE_READY"}
