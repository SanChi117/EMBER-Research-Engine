"""D05/C14: exact qualitative author-text labels are NOT market goldens.

Source material is text + diagrams about reactions at levels. It has NO
independently timestamp-aligned Binance USD-M 5m/1h candle labels. This gate
checks the source *meaning* and original figure references, never turning
source-shaped examples into StrongHL, VC, backtest or trade approval.

StrongHL original: contact liquidity OR inefficiency; later VC POI OR BOS;
POI formation on same/lower TF. SNR reversal pair order conflict unresolved.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,re

HERE=Path(__file__).resolve().parent
SOURCE=HERE/"C14_AUTHOR_STRONGHL_QUALITATIVE_CASES.json"
C04=HERE/"C04_LEVEL_REACTION_SOURCE_CASES.json"
C03=HERE/"C03_58_IMAGE_REVIEW.json"

class QualitativeRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class SourceConceptVerdict:
    case_id: str
    source_only_result: str
    source_figure_id: str|None
    author_futures_golden_label: str="NOT_AVAILABLE_IN_ORIGINAL_SOURCE"
    price_origin: str="NO_TIME_OR_RAW_BINANCE_CANDLE_IN_CONCEPT_CASE"
    author_stronghl_approved: bool=False
    trade_ready: bool=False

@dataclass(frozen=True)
class QualitativeSourceSummary:
    cases: tuple[SourceConceptVerdict,...]
    source_concept_consistent: int
    source_derived_negative_controls: int
    unresolved_source_conflicts: int
    not_author_annotated_market_events: int
    original_images_reviewed: int
    labelled_futures_market_cases: int=0
    trade_ready: bool=False
    verdict: str="TEXT_SCHEMATICS_ONLY_NOT_BINANCE_AUTHOR_GOLDENS"

SOURCE_ONLY={"AUTHOR_TEXT_OR_SCHEMATIC_ONLY"}
ALLOWED_OUTCOMES={
 "AUTHOR_TEXT_CONSISTENT_ONLY",
 "MISSING_MOVEMENT_CONFIRMATION",
 "MISSING_LIQUIDITY_OR_INEFFICIENCY_CONTACT",
 "NO_SOURCE_APPROVED_VC_GEOMETRY",
 "UNSUPPORTED_UPPER_TF_CONFIRMATION_IN_SOURCE",
 "CONTEXT_NOT_STRONG_SOURCE_ILLUSTRATION",
 "UNRESOLVED_AUTHOR_TEXT_IMAGE_CONFLICT",
 "LATER_TEST_CANNOT_BE_LABELLED_FIRST",
 "POSSIBLE_RESPONSE_NOT_GUARANTEED",
}
PRIMARY_SOURCE_KEYS={"StrongHL","IMB","POI","SNR"}

def evaluate_qualitative_stronghl(case:dict,fixture:dict,c04:dict)->SourceConceptVerdict:
    if not isinstance(case,dict) or not isinstance(fixture,dict) or not isinstance(c04,dict):
        raise QualitativeRejected("BAD_SOURCE_CASE")
    if (case.get("source_kind") not in SOURCE_ONLY or
        case.get("author_bars_independently_aligned") is not False or
        case.get("binance_futures_raw_prices") is not False or
        case.get("author_stronghl_approved") is not False):
        raise QualitativeRejected("FAKE_MARKET_OR_AUTHOR_ATTESTATION")
    case_id=case.get("case_id")
    if not isinstance(case_id,str) or not re.fullmatch(r"SHL-[A-Z0-9-]+",case_id):
        raise QualitativeRejected("BAD_CASE_ID")
    if case.get("source_uri") not in set(fixture.get("primary_sources",{}).values()):
        raise QualitativeRejected("UNREGISTERED_PRIMARY_SOURCE")
    figure=case.get("figure_ref")
    if figure is not None:
        matched=[x for x in c04["figures"] if x["id"]==figure]
        if len(matched)!=1 or not re.fullmatch(r"[0-9a-f]{64}",matched[0]["sha256"]):
            raise QualitativeRejected("IMAGE_NOT_IN_FROZEN_SOURCE_CASES")
    contact=case.get("contact")
    confirmation=case.get("confirmation")
    tf=case.get("confirm_tf")
    subject=case.get("subject")
    klass=case.get("classification")
    if (subject=="StrongHL" and case["source_uri"]!=fixture["primary_sources"]["StrongHL"]) or (subject=="SNR" and case["source_uri"]!=fixture["primary_sources"]["SNR"]) or (subject in ("POI_FIRST_TEST","POI_REACTION") and case["source_uri"]!=fixture["primary_sources"]["IMB"]):
        raise QualitativeRejected("MISMATCHED_CONCEPT_TEXT_SOURCE")
    if subject=="StrongHL":
        if contact=="NONE":
            result="MISSING_LIQUIDITY_OR_INEFFICIENCY_CONTACT"
        elif contact not in ("LIQUIDITY_CONTACT","INEFFICIENCY_CONTACT"):
            raise QualitativeRejected("UNSUPPORTED_CONTACT_KIND")
        elif confirmation=="NONE":
            result="MISSING_MOVEMENT_CONFIRMATION"
        elif confirmation=="RAW_EXCHANGE_VOLUME_SPIKE":
            result="NO_SOURCE_APPROVED_VC_GEOMETRY"
        elif confirmation not in ("VC_IMB","VC_SNR","VC_RB","BOS"):
            raise QualitativeRejected("UNSUPPORTED_AUTHOR_CONFIRMATION")
        elif tf=="HIGHER":
            result="UNSUPPORTED_UPPER_TF_CONFIRMATION_IN_SOURCE"
        elif tf=="SAME_OR_LOWER":
            result="AUTHOR_TEXT_CONSISTENT_ONLY"
        else:
            raise QualitativeRejected("UNKNOWN_TF_RELATION")
    elif subject=="SNR":
        if case_id=="SHL-MB-WEAK-NOT-STRONG":
            if klass!="SOURCE_ILLUSTRATION" or figure!="POI-IMAGE-4-MB":
                raise QualitativeRejected("WEAK_MB_NOT_SOURCE_SUPPORTED")
            result="CONTEXT_NOT_STRONG_SOURCE_ILLUSTRATION"
        else:
            if figure!="POI-IMAGE-2-SNR-SHORT":
                raise QualitativeRejected("SNR_NOT_SUPPORTED_BY_CONFLICT_IMAGE")
            conflicts=c04.get("source_conflicts",[])
            if not any(x.get("code")=="SNR_RESISTANCE_CANDLE_ORDER_CONFLICT"
                       and x.get("resolution")=="UNRESOLVED_DO_NOT_HARDCODE_CANDLE_ORDER_AS_STRONG_SNR"
                       for x in conflicts):
                raise QualitativeRejected("SNR_CONFLICT_NOT_DOCUMENTED")
            result="UNRESOLVED_AUTHOR_TEXT_IMAGE_CONFLICT"
    elif subject=="POI_FIRST_TEST":
        result="LATER_TEST_CANNOT_BE_LABELLED_FIRST"
    elif subject=="POI_REACTION":
        result="POSSIBLE_RESPONSE_NOT_GUARANTEED"
    else:
        raise QualitativeRejected("UNRECOGNIZED_COURSE_CONCEPT")
    # MB illustration is a specific original *weak* contrast, not StrongHL.
    if case_id=="SHL-MB-WEAK-NOT-STRONG" and figure=="POI-IMAGE-4-MB":
        result="CONTEXT_NOT_STRONG_SOURCE_ILLUSTRATION"
    if result not in ALLOWED_OUTCOMES or case.get("expected")!=result:
        raise QualitativeRejected("SOURCE_CONCEPT_EXPECTATION_MISMATCH")
    if result in ("AUTHOR_TEXT_CONSISTENT_ONLY","POSSIBLE_RESPONSE_NOT_GUARANTEED"):
        if klass!="CONCEPT_POSITIVE":
            raise QualitativeRejected("POSITIVE_TEXT_CASE_MISCLASSIFIED")
    elif result=="UNRESOLVED_AUTHOR_TEXT_IMAGE_CONFLICT":
        if klass!="TEXT_CONFLICT":
            raise QualitativeRejected("CONFLICT_MUST_REMAIN_BLOCKED")
    elif result=="CONTEXT_NOT_STRONG_SOURCE_ILLUSTRATION":
        if klass!="SOURCE_ILLUSTRATION":
            raise QualitativeRejected("WEAK_MB_INCORRECTLY_CLASSIFIED")
    elif klass!="TEXT_DERIVED_NEGATIVE":
        raise QualitativeRejected("TEXT_NEGATIVE_NOT_AUTHOR_PRICE_LABEL")
    return SourceConceptVerdict(case_id,result,figure)

def audit_qualitative_source_cases(source:dict,c04:dict,c03:dict)->QualitativeSourceSummary:
    if (not isinstance(source,dict) or
        source.get("schema")!="EMBER_D05_C14_ACADEMIC_STRONGHL_QUALITATIVE_LABELS_V1" or
        set(source.get("primary_sources",{}))!=PRIMARY_SOURCE_KEYS or
        source.get("academic_futures_golden_labels")!=0 or
        source.get("automatic_entry_permissions")!=0):
        raise QualitativeRejected("NOT_AN_UNAPPROVED_SOURCE_SCHEMATIC_DATASET")
    if (c04.get("acceptance",{}).get("academic_market_patterns_independently_approved")!=0
        or c04.get("source_role")!="ACADEMIC_REACTION_ILLUSTRATION"
        or c04.get("acceptance",{}).get("uses_absolute_market_timestamps") is not False):
        raise QualitativeRejected("CHANGED_OR_FALSE_ORIGINAL_C04_SCOPE")
    if (c03.get("all_reviewed_images")!=72 or c03.get("unreviewed_images")!=0
        or c03.get("approved_academic_futures_cases")!=0
        or c03.get("numeric_forex_total")!=6):
        raise QualitativeRejected("CHANGED_OR_FALSE_ORIGINAL_C03_SCOPE")
    cases=source.get("cases")
    if not isinstance(cases,list) or len(cases)!=13:
        raise QualitativeRejected("INCOMPLETE_SOURCE_CASE_REGISTRY")
    if len({x.get("case_id") for x in cases if isinstance(x,dict)})!=len(cases):
        raise QualitativeRejected("DUPLICATE_SOURCE_CASE_ID")
    results=tuple(evaluate_qualitative_stronghl(c,source,c04) for c in cases)
    positive=sum(r.source_only_result in ("AUTHOR_TEXT_CONSISTENT_ONLY",
                                          "POSSIBLE_RESPONSE_NOT_GUARANTEED")
                 for r in results)
    unresolved=sum(r.source_only_result=="UNRESOLVED_AUTHOR_TEXT_IMAGE_CONFLICT" for r in results)
    return QualitativeSourceSummary(results,positive,len(results)-positive-unresolved,
                                    unresolved,len(results),c03["all_reviewed_images"])

def check_frozen_source_illustrations()->QualitativeSourceSummary:
    return audit_qualitative_source_cases(
        json.loads(SOURCE.read_text(encoding="utf8")),
        json.loads(C04.read_text(encoding="utf8")),
        json.loads(C03.read_text(encoding="utf8")))
