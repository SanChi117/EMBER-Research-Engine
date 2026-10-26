"""C80 fail-closed owner-authenticated crypto case intake; PAPER ONLY.

The source courses provide method rules but no timestamped, author-labelled
Binance positive/negative candle goldens. User-supplied strings, hashes,
labels, URLs, and the assistant's own conjectures are NOT attestations.
This contract only checks provenance and chronology against frozen C73/C72
price-source evidence. It can never mark a case AUTHOR_VERIFIED or trade.

Source: original academy Entry by IMB & SNR, POI, Rejection Block.
All kinds are *claims under review*, not assertions of true author labels.
"""
from dataclasses import dataclass
from collections import Counter
import re

C73_SHA="c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b"
C72_BLOB="19b7e0357600b70b3f26467339a417e0f99a1302"
COURSE_A="1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ"
POI_COURSE="1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R"
LABELS={"1H_POI_VALID_FIRST_TEST","15M_TRIGGER","DIRECT_15M_VC",
        "POST_TRIGGER_5M_VC","STRONGHL"}
FIELDS={"symbol","context_index","source_side","claim","polarity",
        "c73_sha256","c72_blob_sha1","poi_created_ms",
        "original3m_touch_id","original3m_touch_closed_ms",
        "source15m_event_closed_ms","source5m_event_closed_ms",
        "course_route_a_id","course_poi_id","source_document_url",
        "source_document_sha256","author_label_anchor","source_scope",
        "source_reviewer_attestation"}
SHA=re.compile(r"^[0-9a-f]{64}$")
SYMS={"BCHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT"}

# This registry is intentionally empty; a genuine future attestation would
# require independently reviewed source media with confirmed positive AND
# negative cases and code revision. Never populate it from caller input.
PINNED_AUTHOR_CASE_ATTESTATIONS=frozenset()

class C80Rejected(ValueError):pass

@dataclass(frozen=True)
class IntakeResult:
    symbol:str
    index:int
    claim:str
    polarity:str
    status:str="UNVERIFIED_OWNER_LABEL"
    source_price_linked:bool=True
    actual_author_authentication:bool=False
    author_valid_first_test:bool=False
    author_15m_trigger:bool=False
    author_15m_vc:bool=False
    author_5m_vc:bool=False
    entry_allowed:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _t(v):
    return v is None or (type(v) is int and v>0)
def _root(v,name):
    if not (type(v) is str and SHA.fullmatch(v)):
        raise C80Rejected("BAD_"+name)

def review(candidate, source73, source72):
    """Reject fabricated source candle/timestamp/parent or route promotion.

    Authenticity of owner labels is NOT inferred from consistency of OHLCV.
    """
    if type(candidate) is not dict or set(candidate)!=FIELDS:
        raise C80Rejected("EXACT_OWNER_CASE_SCHEMA_REQUIRED")
    if type(source73) is not dict or type(source72) is not dict:
        raise C80Rejected("SOURCE_CASES_REQUIRED")
    p=candidate
    if p["symbol"] not in SYMS or type(p["context_index"]) is not int or p["context_index"]<0:
        raise C80Rejected("BAD_CRYPTO_KEY")
    if p["source_side"] not in ("LONG","SHORT") or p["claim"] not in LABELS or p["polarity"] not in ("POSITIVE","NEGATIVE"):
        raise C80Rejected("INVALID_OWNER_CLAIM")
    if p["source_scope"]!="BINANCE_USDM_ORIGINAL_FROZEN":
        raise C80Rejected("BAD_ORIGINAL_PRICE_SCOPE")
    if p["course_route_a_id"]!=COURSE_A or p["course_poi_id"]!=POI_COURSE:
        raise C80Rejected("WRONG_COURSE_OWNER_REFERENCE")
    if p["c73_sha256"]!=C73_SHA or p["c72_blob_sha1"]!=C72_BLOB:
        raise C80Rejected("FROZEN_PRICE_SHA_DRIFT")
    if p["source_document_url"] is not None:
        if not (type(p["source_document_url"]) is str and p["source_document_url"].startswith("https://") and len(p["source_document_url"])<=500):
            raise C80Rejected("INVALID_AUTHOR_URL")
    if p["source_document_sha256"] is not None:_root(p["source_document_sha256"],"DOC_SHA")
    if p["source_reviewer_attestation"] is not None:
        _root(p["source_reviewer_attestation"],"ATTESTATION")
    if p["author_label_anchor"] is not None:
        if type(p["author_label_anchor"]) is not str or not 1<=len(p["author_label_anchor"])<=250:
            raise C80Rejected("INVALID_LABEL_ANCHOR")
    for k in ("poi_created_ms","original3m_touch_closed_ms","source15m_event_closed_ms","source5m_event_closed_ms"):
        if not _t(p[k]):raise C80Rejected("BAD_TIME_"+k)
    if p["original3m_touch_id"] is not None:
        if type(p["original3m_touch_id"]) is not str or not 1<=len(p["original3m_touch_id"])<=200:
            raise C80Rejected("INVALID_RAW3M_ID")
    for r in (source73,source72):
        if r.get("symbol")!=p["symbol"] or r.get("side")!=p["source_side"] or r.get("original_c46_4h_parent_index")!=p["context_index"]:
            raise C80Rejected("C73_C72_CASE_JOIN_MISMATCH")
        if r.get("readiness")!="NOT_TRADE_READY" or any(r.get(k)!=[] for k in ("orders","fills","trades")):
            raise C80Rejected("SOURCE_ALREADY_PROMOTED")
    for k in ("author_15m_trigger","author_5m_vc","route_b_idm_used","route_c_raid_bos_used"):
        if source73.get(k) is not False or source72.get(k) is not False:
            raise C80Rejected("FORGED_AUTHOR_ROUTE")
    if source73.get("author_1h_poi_valid_first_test") is not False:
        raise C80Rejected("FORGED_OWNER_POI")
    for pk,sk in (
        ("poi_created_ms","source_1h_poi_created_at_ms"),
        ("original3m_touch_closed_ms","original_first_source3m_touch_closed_ms"),
        ("original3m_touch_id","original_first_source3m_touch_id"),
        ("source15m_event_closed_ms","first_source15m_event_fully_known_ms")):
        if p[pk]!=source73.get(sk):
            raise C80Rejected("FROZEN_CASE_SOURCE_MISMATCH_"+pk)
    if p["source5m_event_closed_ms"]!=source72.get("first_any_5m_event_known_ms"):
        raise C80Rejected("FROZEN_5M_SOURCE_MISMATCH")
    if source73.get("c72_post_15m_first_any_5m_source_state")!=source72.get("state"):
        raise C80Rejected("C72_ROUTE_MISMATCH")
    c,t,f=p["poi_created_ms"],p["original3m_touch_closed_ms"],p["source15m_event_closed_ms"]
    five=p["source5m_event_closed_ms"]
    if c is not None and t is not None and t<=c:
        raise C80Rejected("RAW_TOUCH_PRECEDES_CREATION")
    if f is not None and (t is None or f<=t):
        raise C80Rejected("15M_NO_FIRST_TOUCH_OR_LOOKAHEAD")
    if five is not None and (f is None or five<=f):
        raise C80Rejected("5M_BEFORE_15M")
    if p["polarity"]=="POSITIVE":
        target={"1H_POI_VALID_FIRST_TEST":t,
                "15M_TRIGGER":f,"DIRECT_15M_VC":f,
                "POST_TRIGGER_5M_VC":five,"STRONGHL":five}[p["claim"]]
        if target is None:raise C80Rejected("POSITIVE_WITHOUT_ORIGINAL_SOURCE_EVENT")
        if p["claim"] in ("15M_TRIGGER","DIRECT_15M_VC","POST_TRIGGER_5M_VC") and source73.get("state","").startswith("NEW_1H_POI_SOURCE_NO_"):
            raise C80Rejected("NONSELECTED_POI_SOURCE_AS_POSITIVE")
    # The schema can record reference hints but cannot AUTHENTICATE.
    # An outside review must pin a hash to source, time, exact author marking
    # and negative counterexamples before any future promotion, and source
    # consistency alone never authorizes a trading engine.
    return IntakeResult(p["symbol"],p["context_index"],p["claim"],p["polarity"])

def audit_batch(rows):
    if type(rows) is not tuple or any(type(r) is not IntakeResult for r in rows):
        raise C80Rejected("REVIEWED_INTAKE_RESULTS_ONLY")
    seen=set()
    for r in rows:
        key=r.symbol,r.index,r.claim
        if key in seen:raise C80Rejected("DUPLICATE_OR_OPPOSITE_AUTHOR_LABEL_CLAIM")
        seen.add(key)
        if r.status!="UNVERIFIED_OWNER_LABEL" or r.actual_author_authentication or r.entry_allowed or r.readiness!="NOT_TRADE_READY" or any((r.orders,r.fills,r.trades,r.author_valid_first_test,r.author_15m_trigger,r.author_15m_vc,r.author_5m_vc)):
            raise C80Rejected("FORGED_GOLDEN_PROMOTION")
    return {"intake_claims":len(rows),
            "claimed_polarity_counts":dict(sorted(Counter(r.polarity for r in rows).items())),
            "author_authenticated":0,"orders":0,"fills":0,"trades":0,
            "readiness":"NOT_TRADE_READY"}
