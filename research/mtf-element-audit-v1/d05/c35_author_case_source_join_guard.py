"""C35 author BOS case provenance and date/market/source non-intersection guards.

Original instructor BOS 2023 backtest link is unavailable; course heading
alone cannot establish instrument or a labeled 3m pivot. Previously frozen
C33 native USD-M sample covers 2026-09-01 through 2026-10-03 exclusively.
No author labeled case is certified by this metadata-only module.
PAPER ONLY / NOT_TRADE_READY. No orders, trade signals, fills or TP/SL.
"""
from dataclasses import dataclass
from datetime import datetime,timezone

C33_ORIGINAL_START_MS=1788220800000 # 2026-09-01T00:00:00Z
C33_ORIGINAL_END_MS=1790985600000   # 2026-10-03T00:00:00Z, exclusive
INSTRUCTOR_BACKTEST_REF=(
 "https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21")
INSTRUCTOR_BACKTEST_TITLE_PERIOD_START_MS=1672531200000 # 2023-01-01 UTC
INSTRUCTOR_BACKTEST_TITLE_PERIOD_END_MS=1690848000000   # 2023-08-01 UTC
ALLOWED_STATUS=frozenset(("SOURCE_UNAVAILABLE","CASE_METADATA_ONLY",
                            "EXTERNAL_UNVERIFIED_LABEL"))

@dataclass(frozen=True)
class InstructorCaseClaim:
    original_author_source_url:str
    source_status:str="SOURCE_UNAVAILABLE"
    author_source_sha256:str|None=None
    author_explicit_case_label:str|None=None
    market_symbol:str|None=None
    market_venue:str|None=None
    market_provider:str|None=None
    chart_iana_timezone:str|None=None
    instructor_case_start_ms:int|None=None
    instructor_case_end_ms:int|None=None
    instructor_selected_3m_bos_level:str|None=None
    source_3m_original_bar_sha:str|None=None
    source_1h_original_bar_sha:str|None=None
    instructor_first_fta_level:str|None=None
    instructor_stop_level:str|None=None

@dataclass(frozen=True)
class InstructorCaseGuard:
    source_reference:str
    case_evidence_gaps:tuple[str,...]
    case_within_frozen_c33_period:bool|None
    course_title_period_overlaps_frozen_c33:bool
    joined_to_frozen_c33:bool=False
    has_verified_author_bos_positive:bool=False
    has_verified_author_bos_negative:bool=False
    source_case_label_status:str="NEEDS_AUTHOR_BOS_GOLDENS"
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _strict_epoch_ms(field,value):
    if value is not None and (type(value)!=int or value<=0):
        raise ValueError("C35_INVALID_"+field)

def _strict_str(field,value):
    if value is not None and (type(value)!=str or len(value.strip())==0
                              or len(value)>2048):
        raise ValueError("C35_INVALID_"+field)

def _overlap(a_start,a_end,b_start,b_end):
    return a_start<b_end and b_start<a_end

def review_author_case_claim(p):
    if not isinstance(p,InstructorCaseClaim):
        raise ValueError("C35_UNTRUSTED_AUTHOR_CASE")
    if p.original_author_source_url!=INSTRUCTOR_BACKTEST_REF:
        raise ValueError("C35_NOT_ORIGINAL_INSTRUCTOR_BACKTEST_REF")
    if p.source_status not in ALLOWED_STATUS:
        raise ValueError("C35_UNTRUSTED_SOURCE_STATUS")
    for field in (
        "author_source_sha256","author_explicit_case_label","market_symbol",
        "market_venue","market_provider","chart_iana_timezone",
        "instructor_selected_3m_bos_level","source_3m_original_bar_sha",
        "source_1h_original_bar_sha","instructor_first_fta_level",
        "instructor_stop_level"):
        _strict_str(field,getattr(p,field))
    for field in ("instructor_case_start_ms","instructor_case_end_ms"):
        _strict_epoch_ms(field,getattr(p,field))
    if (p.instructor_case_start_ms is None)!=(p.instructor_case_end_ms is None):
        raise ValueError("C35_PARTIAL_CASE_TIMESTAMP")
    if (p.instructor_case_start_ms is not None and
        p.instructor_case_end_ms<=p.instructor_case_start_ms):
        raise ValueError("C35_CASE_END_NOT_AFTER_START")
    if p.author_source_sha256 is not None and (
        len(p.author_source_sha256)!=64 or
        any(c not in "0123456789abcdef" for c in p.author_source_sha256)):
        raise ValueError("C35_INVALID_AUTHOR_SOURCE_SHA256")
    # A screenshot label is never an authenticated positive merely because
    # a caller sets both source_status and a SHA without showing the source.
    gaps=[]
    for field in (
        "author_source_sha256","author_explicit_case_label","market_symbol",
        "market_venue","market_provider","chart_iana_timezone",
        "instructor_case_start_ms","instructor_case_end_ms",
        "instructor_selected_3m_bos_level","source_3m_original_bar_sha",
        "source_1h_original_bar_sha","instructor_first_fta_level",
        "instructor_stop_level"):
        if getattr(p,field) is None:
            gaps.append("SOURCE_NOT_SHOWN_"+field.upper())
    if p.source_status=="SOURCE_UNAVAILABLE":
        gaps.append("INSTRUCTOR_2023_BACKTEST_SOURCE_UNAVAILABLE")
    if p.source_status!="SOURCE_UNAVAILABLE":
        gaps.append("CLAIM_NOT_INDEPENDENTLY_AUTHENTICATED_AS_AUTHOR")
    time_overlap=None
    if p.instructor_case_start_ms is not None:
        time_overlap=_overlap(p.instructor_case_start_ms,
                             p.instructor_case_end_ms,
                             C33_ORIGINAL_START_MS,C33_ORIGINAL_END_MS)
        if not time_overlap:
            gaps.append("CASE_TIME_NOT_IN_FROZEN_C33_2026_SOURCE_WINDOW")
    title_overlap=_overlap(INSTRUCTOR_BACKTEST_TITLE_PERIOD_START_MS,
                           INSTRUCTOR_BACKTEST_TITLE_PERIOD_END_MS,
                           C33_ORIGINAL_START_MS,C33_ORIGINAL_END_MS)
    if title_overlap:
        raise ValueError("C35_CORRUPTED_2023_2026_PERIOD_CONSTANTS")
    gaps.append("AUTHOR_CASE_SAME_MARKET_AND_PROVIDER_PRICE_PARITY_NOT_ATTESTED")
    return InstructorCaseGuard(p.original_author_source_url,tuple(gaps),
        time_overlap,title_overlap)

def default_missing_original_backtest():
    return review_author_case_claim(InstructorCaseClaim(INSTRUCTOR_BACKTEST_REF))
