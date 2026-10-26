"""C83 audit 12 crypto source packets against original owner lesson *text*.

Read-only original lesson excerpts identify rule meanings. They are not
cryptographic attestation of course images or dated Binance trade goldens.
The C81 queue must be regenerated from frozen C73/C72 source bytes and
byte-compare its serialized records to the pinned C81 153-item witness.
No claim labels, orders or author golden can be emitted here.
"""
from dataclasses import dataclass,asdict
from collections import Counter
import hashlib,json
from c81_source_authenticated_review_queue import build,QueueItem
from c82_independent_owner_media_request import prepare, C82Rejected

COURSE_ROUTE_ID="1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ"
COURSE_RB_ID="1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT"
COURSE_POI_ID="1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R"
COURSE_CITATIONS=(
  ("1H_PARENT",COURSE_ROUTE_ID,"1H POI завжди має бути створена в контексті тесту та реакції від 4H POI"),
  ("1H_FIRST_TEST",COURSE_ROUTE_ID,"Щоб ввійти в позицію у нас обовʼязково має бути **ТЕСТ** цього 1H POI"),
  ("15M_TRIGGER_TO_5M_VC",COURSE_ROUTE_ID,"З 15M Trigger SSL, BSL or IMB"),
  ("NO_TRIGGER_DIRECT_15M_VC",COURSE_ROUTE_ID,"При відсутності 15M Trigger → очікується на 15M VC [IMB, SNR]"),
  ("RB_RAID_OR_IMB",COURSE_RB_ID,"RB обоʼязково має знімати ліквідність, або перекривати POI у вигляді IMB"),
  ("RB_FIRST_REAL_TEST",COURSE_RB_ID,"за істинний тест потрібно сприймати тільки ПЕРШИЙ"),
  ("POI_STRENGTH",COURSE_POI_ID,"Сильна POI - це та, яка працювала з ліквідністю [SSL, BSL] або FVG"),
)
C73_SHA="c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b"
C72_BLOB="19b7e0357600b70b3f26467339a417e0f99a1302"
class C83Rejected(ValueError):pass

@dataclass(frozen=True)
class C83SourceCrosswalk:
    case_key:str
    symbol:str
    side:str
    poi_kind:str
    first_3m_source_close_ms:int
    source15m_known_ms:int
    source5m_known_ms:int
    physical_visit_episodes:int
    source15m_geometry:str
    source5m_geometry:str
    course_rule_anchors:tuple
    next_required_proof:tuple
    exact_course_media_timestamp_attested:bool=False
    author_positive_golden:bool=False
    author_negative_golden:bool=False
    author_eligible_15m_trigger:bool=False
    author_direct_15m_vc:bool=False
    author_valid_first_poi_test:bool=False
    author_5m_vc:bool=False
    entry_allowed:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def source_matched_queue(c73_bytes,c72_bytes,c81_serialized):
    """Derive full 153 and reject any drift in the C81 checkpoint."""
    if type(c73_bytes) is not bytes or type(c72_bytes) is not bytes or type(c81_serialized) is not bytes:
        raise C83Rejected("REQUIRES_SOURCE_BYTES")
    if hashlib.sha256(c73_bytes).hexdigest()!=C73_SHA:
        raise C83Rejected("C73_SHA_DIFFERENT")
    if hashlib.sha1(b"blob "+str(len(c72_bytes)).encode()+b"\0"+c72_bytes).hexdigest()!=C72_BLOB:
        raise C83Rejected("C72_BLOB_DIFFERENT")
    original=build(c73_bytes,c72_bytes)
    try:
        frozen=json.loads(c81_serialized)
    except (ValueError,TypeError) as e:
        raise C83Rejected("C81_JSON_CORRUPT") from e
    if type(frozen) is not list or len(frozen)!=153 or frozen!=[asdict(q) for q in original]:
        raise C83Rejected("C81_ORIGINAL153_SOURCE_DRIFT")
    return original

def make_p0(item):
    if type(item) is not QueueItem or item.priority!=0:
        raise C83Rejected("NOT_P0_SOURCE_CASE")
    pin=hashlib.sha256(b"C81_SOURCE_REVIEW_QUEUE_V1").hexdigest()
    try:
        request=prepare(item,pinned_source_sha256=pin)
    except C82Rejected as e:
        raise C83Rejected("C82_SOURCE_CONTRACT_REJECTED") from e
    if request.owner_auth_status!="NOT_AUTHENTICATED" or request.positive_golden or request.negative_golden:
        raise C83Rejected("UNTRUSTED_AUTHOR_REVIEW")
    if item.poi_kind not in ("1H_NEW_VC_RB_SOURCE","1H_NEW_VC_SNR_SOURCE"):
        raise C83Rejected("NO_SOURCE_PARENT_RB_SNR")
    if item.source15m_kind not in ("FIRST_ANY_NEW1H_POI_15M_IMB_TRIGGER_VS_VC_UNRESOLVED",
                                  "FIRST_ANY_NEW1H_POI_15M_SNR_TRIGGER_VS_VC_UNRESOLVED"):
        raise C83Rejected("NO_15M_SOURCE_GEOMETRY")
    if item.first5m_kind not in ("FIRST_5M_IMB_ALIGNED_NOT_AUTHOR_VC",
                                "FIRST_5M_SNR_ALIGNED_NOT_AUTHOR_VC",
                                "FIRST_5M_SOURCE_OPPOSITE_SIDE",
                                "FIRST_5M_SOURCE_MULTIPLE_KINDS_AMBIGUOUS"):
        raise C83Rejected("UNSUPPORTED_5M_SOURCE")
    if any(type(x) is not int for x in (item.poi_created_ms,item.first_original_3m_close_ms,item.source15m_known_ms,item.first5m_known_ms)):
        raise C83Rejected("SOURCE_CLOCK_INVALID")
    if not (item.poi_created_ms<item.first_original_3m_close_ms<item.source15m_known_ms<item.first5m_known_ms):
        raise C83Rejected("LOOKAHEAD_SOURCE")
    if type(item.visits_before_source15m) is not int or item.visits_before_source15m<1:
        raise C83Rejected("BAD_PHYSICAL_VISITS")
    points=["1H_PARENT","1H_FIRST_TEST","15M_TRIGGER_TO_5M_VC",
            "NO_TRIGGER_DIRECT_15M_VC"]
    if item.poi_kind=="1H_NEW_VC_RB_SOURCE":
        points.extend(["RB_RAID_OR_IMB","RB_FIRST_REAL_TEST"])
    else:points.append("POI_STRENGTH")
    needs=["OWNER_POSITIVE_AND_NEGATIVE_FIRST_VALID_POI_TEST",
           "OWNER_LABEL_15M_TRIGGER_VS_DIRECT_15M_VC",
           "EXACT_5M_VC_WITH_REAL_TRIGGER_AND_TIMESTAMP",
           "AUTHOR_CRYPTO_CHART_TIMESTAMP_AND_SOURCE_MATCH"]
    if item.visits_before_source15m>1:
        needs.append("OWNER_CONFIRM_NO_REVISIT_AS_FIRST_VALID_TEST")
    if item.first5m_kind=="FIRST_5M_SOURCE_OPPOSITE_SIDE":
        needs.append("OWNER_REJECTION_OF_OPPOSITE_5M_SOURCE_GEOMETRY")
    if item.first5m_kind=="FIRST_5M_SOURCE_MULTIPLE_KINDS_AMBIGUOUS":
        needs.append("OWNER_AMBIGUOUS_KIND_COUNTEREXAMPLE")
    return C83SourceCrosswalk(
        item.source_key,item.symbol,item.side,item.poi_kind,
        item.first_original_3m_close_ms,item.source15m_known_ms,
        item.first5m_known_ms,item.visits_before_source15m,
        "IMB" if "_IMB_" in item.source15m_kind else "SNR",
        "SAME_SIDE_GEOMETRY" if "_ALIGNED_" in item.first5m_kind else
          "OPPOSITE_SIDE_GEOMETRY" if "OPPOSITE_SIDE" in item.first5m_kind
          else "MULTIPLE_KINDS_AMBIGUOUS",
        tuple(points),tuple(needs))

def inspect_all(c73_bytes,c72_bytes,c81_serialized):
    queue=source_matched_queue(c73_bytes,c72_bytes,c81_serialized)
    found=tuple(make_p0(q) for q in queue if q.priority==0)
    if len(found)!=12 or len({x.case_key for x in found})!=12:
        raise C83Rejected("EXPECTED_EXACTLY_12_UNIQUE_P0")
    if any(x.readiness!="NOT_TRADE_READY" or any((x.author_positive_golden,x.author_negative_golden,
            x.author_eligible_15m_trigger,x.author_direct_15m_vc,x.author_valid_first_poi_test,
            x.author_5m_vc,x.exact_course_media_timestamp_attested,x.entry_allowed,
            x.orders,x.fills,x.trades)) for x in found):
        raise C83Rejected("AUTHOR_PROMOTION")
    counts=lambda attr:dict(sorted(Counter(getattr(x,attr) for x in found).items()))
    return found,{"schema":"EMBER_C83_OWNER_COURSE_TEXT_CROSSWALK_P0_V1",
        "source_total_contexts":len(queue),"original_p0_count":len(found),
        "poi_kind":counts("poi_kind"),"15m_geometries":counts("source15m_geometry"),
        "5m_geometries":counts("source5m_geometry"),
        "source_15m_chronology_verified":12,
        "author_text_rule_anchors":len(COURSE_CITATIONS),
        "author_crypto_timestamp_labels_verified":0,
        "owner_authenticated_positive_goldens":0,
        "owner_authenticated_negative_goldens":0,
        "entries_allowed":0,"orders":0,"fills":0,"trades":0,"readiness":"NOT_TRADE_READY"}
