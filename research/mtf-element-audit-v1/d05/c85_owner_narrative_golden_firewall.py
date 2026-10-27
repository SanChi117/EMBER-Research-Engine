"""C85 original academy narrative / crypto-golden firewall, research only.

Course prose illustrates valid schematic routes, but its diagram URLs and
captions do NOT identify timestamp-labelled Binance source candles. This
module NEVER makes an AUTHOR_VERIFIED crypto case or submits a trade.
"""
from dataclasses import dataclass, asdict
from collections import Counter
from hashlib import sha256
import json
from c83_owner_course_text_crosswalk import source_matched_queue
from c81_source_authenticated_review_queue import QueueItem,validate_queue
from c84_route_a_paper_fsm import original153_projection,summarize

class C85Rejected(ValueError): pass
ENTRY="1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ"
RB="1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT"
POI="1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R"
IDM="19SW5tv2CdeaYeP9jCO6WOCs5bpYSjVrs"
SOURCE_IDS={ENTRY,RB,POI,IDM}
SYMBOLS={"BCHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT"}
CLASSES=("OWNER_TEXT_RULE","OWNER_TEXT_SCHEMATIC","SOURCE_TECHNICAL",
         "ADAPTED_HYPOTHESIS","UNKNOWN","AUTHOR_VERIFIED")
ROUTES={
 "A4H_TRIGGER_15M_VC":("4H_POI_TEST","1H_TRIGGER_BSL","15M_VC_SNR_IMB"),
 "A4H_RAID_1H_RB":("DAILY_POI","4H_SSL_RAID","1H_VC_RB_NEW_POI"),
 "A1H_TRIGGER_5M_VC":("4H_IMB_TEST","1H_IMB_NEW_POI","1H_POI_TEST",
                       "15M_TRIGGER_BSL","5M_VC_IMB_SNR"),
 "A1H_NO_TRIGGER_DIRECT_15M_VC":("4H_SSL_RAID","1H_RB_NEW_POI",
                                 "1H_POI_TEST","15M_DIRECT_VC_IMB"),
}
# These are direct TEXT captions in owner Entry by IMB & SNR. They are
# narrative schematic examples, NOT verified on C81 dated Binance charts.
TEXT_EXAMPLES={
 "A4H_TRIGGER_15M_VC":"4H POI [SNR] → 1H Trigger [BSL] → 15M VC [SNR & IMB - Entry]",
 "A4H_RAID_1H_RB":"4H Raid SSL in Daily POI [RB] → 1H VC [RB]",
 "A1H_TRIGGER_5M_VC":"4H POI [IMB] → 1H VC [IMB - NEW POI] → 15M Trigger [BSL] → 5M VC [IMB & SNR - Entry]",
 "A1H_NO_TRIGGER_DIRECT_15M_VC":"4H POI [SSL Raid] → 1H VC [RB - NEW POI] → 15M VC [IMB - Entry]",
}
COURSE_RULES=(
 ("DAILY_CONTEXT","Daily POI or Liquidity → 4H VC [IMB, SNR, RB]",ENTRY),
 ("4H_VALID_TEST","Щоб ввійти в позицію у нас обовʼязково має бути **ТЕСТ** цього 4H POI",ENTRY),
 ("NO_1H_TRIGGER","При відсутності 1H Trigger → очікується на 1H VC [IMB, SNR, RB]",ENTRY),
 ("1H_CREATED_FROM_4H","1H POI завжди має бути створена в контексті тесту та реакції від 4H POI",ENTRY),
 ("1H_VALID_TEST","Щоб ввійти в позицію у нас обовʼязково має бути **ТЕСТ** цього 1H POI",ENTRY),
 ("15M_TRIGGER","З 15M Trigger SSL, BSL or IMB",ENTRY),
 ("DIRECT_15M_VC","При відсутності 15M Trigger → очікується на 15M VC [IMB, SNR]",ENTRY),
 ("ENTRY_VC_TYPES","для входу в позицію використовується ТІЛЬКИ ***[SNR or IMB]***",ENTRY),
 ("4H_IMB_1H_IMB_NEST","якщо на 4Н IMB, то всередині нього ми не роглядаємо 1H IMB",ENTRY),
 ("RB_TWO_CANDLES","дві свічки BUY+SELL or SELL+BUY",RB),
 ("RB_RAID_OR_IMB","RB обоʼязково має знімати ліквідність, або перекривати POI у вигляді IMB",RB),
 ("RB_WICK_ONLY","Raid або тест імбалансу має бути ***виключно*** тінню свічки",RB),
 ("RB_IMB_BODY_CLOSE","головне, щоб був закріп RB тілом над чи під IMB",RB),
 ("ONLY_FIRST_REAL_TEST","за істинний тест потрібно сприймати тільки ПЕРШИЙ",RB),
 ("POI_LIQUIDITY_OR_FVG","Сильна POI - це та, яка працювала з ліквідністю [SSL, BSL] або FVG",POI),
 ("IDM_ROUTE_SEPARATE","4H VC [POI] → 1H IDM Entry",IDM),
)
REQUIRED=("AUTHENTICATED_COURSE_MEDIA","ORIGINAL_BINANCE_NATIVE_BAR_SOURCE",
          "EXACT_SYMBOL_TICKER_TIMEFRAME","SOURCE_BAR_CLOSE_AND_AVAILABILITY",
          "AUTHOR_LABELLED_POSITIVE_AND_NEGATIVE","INDEPENDENT_HUMAN_MEDIA_REVIEW",
          "NO_LOOKAHEAD_AND_SEQUENCE","NON_GEOMETRIC_TRIGGER_OR_VC_PROOF")

@dataclass(frozen=True)
class Claim:
    """Untrusted submission. All input fields are claims, never credentials."""
    case_key:str
    author_example_id:str
    claim_class:str="OWNER_TEXT_SCHEMATIC"
    native_symbol:str=""
    native_tf:str=""
    native_closed_ms:int=-1
    course_media_digest:str=""
    provider_media_id:str=""
    attestation:str=""
    reviewer:str=""
    positive_label:bool=False
    negative_label:bool=False
    claimed_author_verified:bool=False
    route:str="A"

def reject_untrusted_claim(claim,queue):
    """Classify untrusted source media conservatively, NEVER authenticate."""
    if type(claim) is not Claim or type(queue) is not tuple or len(queue)!=153:
        raise C85Rejected("INVALID_SUBMISSION_OR_QUEUE")
    if claim.route!="A":raise C85Rejected("CROSS_ROUTE_PROOF_REJECTED")
    if claim.claim_class not in CLASSES or claim.claim_class=="AUTHOR_VERIFIED" or claim.claimed_author_verified:
        raise C85Rejected("FORGED_OWNER_CERTIFICATION")
    if claim.author_example_id not in TEXT_EXAMPLES:
        raise C85Rejected("UNKNOWN_COURSE_EXAMPLE")
    x=next((x for x in queue if x.source_key==claim.case_key),None)
    if type(x) is not QueueItem:raise C85Rejected("UNMATCHED_ORIGINAL_CRYPTO_CASE")
    if claim.native_symbol and claim.native_symbol!=x.symbol:
        raise C85Rejected("ORIGINAL_SYMBOL_MISMATCH")
    if claim.native_tf not in ("","3m","5m","15m","1h","4h","1d"):
        raise C85Rejected("UNKNOWN_NATIVE_TIMEFRAME")
    if type(claim.native_closed_ms) is not int or claim.native_closed_ms< -1:
        raise C85Rejected("BAD_CLOSE_TIMESTAMP")
    if claim.native_closed_ms!=-1 and claim.native_tf=="":
        raise C85Rejected("CLOSE_TIMESTAMP_REQUIRES_NATIVE_TF")
    if claim.course_media_digest and (len(claim.course_media_digest)!=64 or
        any(ch not in "0123456789abcdef" for ch in claim.course_media_digest)):
        raise C85Rejected("MALFORMED_MEDIA_DIGEST")
    if claim.positive_label and claim.negative_label:
        raise C85Rejected("CONTRADICTORY_LABELS")
    if any(len(v)>240 for v in (claim.provider_media_id,claim.attestation,claim.reviewer)):
        raise C85Rejected("UNBOUNDED_ATTESTATION")
    # Never infer genuine author attestation from a self-asserted SHA/URL.
    return {"case":x.source_key,"course_example":claim.author_example_id,
            "submission_status":"UNVERIFIED_OWNER_MEDIA_QUARANTINE",
            "course_kind":"OWNER_TEXT_SCHEMATIC_NOT_CRYPTO_GOLDEN",
            "media_hash_is_authentication":False,"positive_golden":False,
            "negative_golden":False,"author_verified":False,
            "entry_allowed":False,"orders":[],"fills":[],"trades":[],
            "missing_proofs":list(REQUIRED),"readiness":"NOT_TRADE_READY"}

def independent_source_report(c73,c72,c81):
    """153 original cases classified without admitting made-up labels."""
    queue=source_matched_queue(c73,c72,c81)
    validate_queue(queue)
    projections=original153_projection(c73,c72,c81)
    if len(projections)!=153:raise C85Rejected("SOURCE_LEN_DRIFT")
    out=[]
    for item,p in zip(queue,projections):
        if item.source_key!=p["case"] or item.priority!=p["priority"]:
            raise C85Rejected("REPLAY_IDENTITY_DRIFT")
        events=[item.poi_created_ms,item.first_original_3m_close_ms,
                item.source15m_known_ms,item.first5m_known_ms]
        if item.priority==0 and not (events[0]<events[1]<events[2]<events[3]):
            raise C85Rejected("P0_NON_CAUSAL")
        out.append({"case":item.source_key,"priority":item.priority,
                    "technical_source_state":p["source_observation"],
                    "author_positive_case":False,"author_negative_case":False,
                    "course_text_example_match":"NOT_PROVEN",
                    "4h_first_valid_test":"UNKNOWN","1h_first_valid_test":"UNKNOWN",
                    "15m_trigger_vs_direct_vc":"UNKNOWN","5m_vc":"UNKNOWN",
                    "missing_proofs":list(REQUIRED),
                    "readiness":"NOT_TRADE_READY"})
    return out

def summary(rows):
    if type(rows) is not list or len(rows)!=153 or len({x["case"] for x in rows})!=153:
        raise C85Rejected("EXPECTED_EXACT_153")
    if any(x["author_positive_case"] or x["author_negative_case"] or
           x["course_text_example_match"]!="NOT_PROVEN" or
           x["readiness"]!="NOT_TRADE_READY" for x in rows):
        raise C85Rejected("SOURCE_PROMOTED_AS_AUTHOR_PROOF")
    return {"schema":"C85_OWNER_NARRATIVE_TO_ORIGINAL153_GOLDEN_FIREWALL",
            "original_crypto_contexts":153,
            "priority":dict(sorted(Counter(str(x["priority"]) for x in rows).items())),
            "owner_text_schematic_example_count":len(TEXT_EXAMPLES),
            "course_rule_text_anchor_count":len(COURSE_RULES),
            "proven_matched_original_crypto_examples":0,
            "owner_authenticated_positive":0,"owner_authenticated_negative":0,
            "entries":0,"orders":0,"fills":0,"trades":0,
            "readiness":"NOT_TRADE_READY"}

def witness(c73,c72,c81):
    result=summary(independent_source_report(c73,c72,c81))
    result["original_lesson_drive_file_ids"]=[ENTRY,RB,POI,IDM]
    result["owner_text_examples"]=[{"id":x,"route":list(ROUTES[x]),
        "quote":TEXT_EXAMPLES[x],"label":"OWNER_TEXT_SCHEMATIC"}
        for x in sorted(TEXT_EXAMPLES)]
    result["original_rule_anchors"]=[{"id":k,"quote":t,"drive_id":v,
        "label":"OWNER_TEXT_RULE"} for k,t,v in COURSE_RULES]
    result["media_attestation"]="NO_AUTHENTICATED_OWNER_BINANCE_TIMESTAMP_LABEL"
    return result

def serialize_witness(c73,c72,c81):
    return (json.dumps(witness(c73,c72,c81),ensure_ascii=False,
                       sort_keys=True,indent=2)+"\n").encode("utf8")
