"""B1/C17 read-only higher-timeframe classic IMB price witnesses.

C16 supplies source-validated closed 1D/4H prices; v05 confirmed_imb supplies
the three-candle wick-gap *geometry*. A candidate is NOT an author-labelled
POI/StrongHL/VC or a trade. No choice of parent, nearest gap, market order,
hard-coded author reaction threshold, or unclosed candle is permitted.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from c16_c08_monthly_daily_htf_lineage import (
    ExtendedHTFReview, NativeKline, DerivedClosedTF, TF_MS
)

AUTHOR_UNKNOWN = "AUTHOR_GOLDEN_SOURCE_UNAVAILABLE"
DIAGNOSTIC_ONLY = "NOT_TRADE_READY"
SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")

class C17Rejected(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)

@dataclass(frozen=True)
class PriceContact:
    start_ms: int
    known_at_ms: int
    close_location: str
    ordinal: int

@dataclass(frozen=True)
class HTFImbalanceCandidate:
    symbol: str
    tf: str
    side: str
    zone_low: Decimal
    zone_high: Decimal
    origin_start_ms: int
    known_at_ms: int
    source_bar_starts: tuple[int, int, int]
    source_native_sha256: tuple[str, ...]
    contacts: tuple[PriceContact, ...]
    first_contact_known_at_ms: Optional[int]
    later_contacts: int
    contact_state: str
    price_class: str = "CLASSIC_THREE_CLOSED_BAR_WICK_GAP_GEOMETRY_ONLY"
    author_status: str = AUTHOR_UNKNOWN
    readiness: str = DIAGNOSTIC_ONLY
    parent_attribution: str = "AUTHOR_PARENT_NOT_DEFINED"

@dataclass(frozen=True)
class C17HTFDiagnostic:
    symbol: str
    as_of_ms: int
    candidates_1d: tuple[HTFImbalanceCandidate, ...]
    candidates_4h: tuple[HTFImbalanceCandidate, ...]
    concept_source: str = "FROZEN_COURSE_V05_CONFIRMED_IMB_GEOMETRY"
    provenance_scope: str = "C16_CALLER_MUST_VERIFY_ORIGINAL_C08_ARCHIVES"
    author_status: str = AUTHOR_UNKNOWN
    readiness: str = DIAGNOSTIC_ONLY

def _validate_stream(rows, tf: str, symbol: str, cutoff: int):
    prev_end = None
    for bar in rows:
        if not isinstance(bar, (NativeKline if tf == "1d" else DerivedClosedTF)):
            raise C17Rejected("MIXED_OR_UNSUPPORTED_HTF_SOURCE_TYPE")
        if bar.symbol != symbol or bar.tf != tf or bar.start_ms % TF_MS[tf]:
            raise C17Rejected("WRONG_TF_SYMBOL_OR_ALIGNMENT")
        if bar.known_at_ms != bar.start_ms + TF_MS[tf]:
            raise C17Rejected("UNFINISHED_OR_INVALID_HTF_CANDLE")
        if bar.known_at_ms > cutoff:
            raise C17Rejected("SOURCE_CONTAINS_FUTURE_OR_UNCLOSED_BAR")
        if prev_end is not None and prev_end != bar.start_ms:
            raise C17Rejected("INCOMPLETE_OR_OVERLAPPING_HTF_HISTORY")
        if not all(isinstance(v, Decimal) and v.is_finite() for v in
                   (bar.open, bar.high, bar.low, bar.close, bar.volume)):
            raise C17Rejected("UNTRUSTED_OR_NONFINITE_HTF_PRICE")
        if not (Decimal(0) < bar.low <= min(bar.open,bar.close) <=
                max(bar.open,bar.close) <= bar.high and bar.volume >= 0):
            raise C17Rejected("IMPOSSIBLE_HTF_OHLCV")
        if tf == "1d":
            if (not SHA_PATTERN.fullmatch(bar.origin_zip_sha256) or
                bar.origin_raw_row_id != bar.origin_zip_sha256 + ":" + str(bar.start_ms)):
                raise C17Rejected("INVALID_ORIGIN_NATIVE_DAILY_SHA")
        else:
            if (bar.provenance != "DERIVED_EXACT_DECIMAL_FROM_C08_NATIVE_15M" or
                len(bar.source_native_15m_rows) != 16 or
                not bar.source_native_15m_zip_shas or
                any(not SHA_PATTERN.fullmatch(s) for s in bar.source_native_15m_zip_shas) or
                bar.author_status != "ACADEMIC_HTF_POI_NOT_CERTIFIED"):
                raise C17Rejected("INVALID_4H_15M_LINEAGE")
            if any(not any(row.startswith(s + ":") for s in
                           bar.source_native_15m_zip_shas)
                   for row in bar.source_native_15m_rows):
                raise C17Rejected("FORGED_4H_SOURCE_ROW_SHA")
        prev_end = bar.known_at_ms

def _source_shas(bars, tf: str):
    if tf == "1d":
        return tuple(dict.fromkeys(x.origin_zip_sha256 for x in bars))
    return tuple(dict.fromkeys(s for x in bars for s in x.source_native_15m_zip_shas))

def _detect(rows, tf: str, symbol: str):
    candidates = []
    for i in range(2, len(rows)):
        first, middle, third = rows[i-2], rows[i-1], rows[i]
        if third.low > first.high:
            side, lo, hi = "LONG", first.high, third.low
        elif third.high < first.low:
            side, lo, hi = "SHORT", third.high, first.low
        else:
            continue
        # The gap exists only when the entire third candle has CLOSED.
        formed = third.known_at_ms
        contacts = []
        for b in rows[i+1:]:
            if b.start_ms < formed:
                raise C17Rejected("REACTION_PRECEDES_LEVEL_FORMATION")
            if b.high >= lo and b.low <= hi:
                location = ("ABOVE_ZONE" if b.close > hi else
                            "BELOW_ZONE" if b.close < lo else "INSIDE_ZONE")
                contacts.append(PriceContact(b.start_ms, b.known_at_ms,
                                             location, len(contacts) + 1))
        if not contacts:
            state = "NO_SUBSEQUENT_CONTACT_OBSERVED"
        elif len(contacts) == 1:
            state = "FIRST_CONTACT_OBSERVED_ONLY"
        else:
            state = "REPEATED_CONTACTS_OBSERVED"
        candidates.append(HTFImbalanceCandidate(
            symbol, tf, side, lo, hi, first.start_ms, formed,
            (first.start_ms, middle.start_ms, third.start_ms),
            _source_shas((first,middle,third),tf),
            tuple(contacts), contacts[0].known_at_ms if contacts else None,
            max(0, len(contacts)-1), state))
    return tuple(candidates)

def diagnose_htf_imb(review: ExtendedHTFReview, *, as_of_ms: int) -> C17HTFDiagnostic:
    """Re-evaluate strictly CLOSED source prefix; no retrospective author status.

    The C16 caller must independently establish C08 ZIP+receipt integrity.
    This function never confers that provenance from a caller's assertion.
    """
    if not isinstance(review, ExtendedHTFReview):
        raise C17Rejected("NOT_A_C16_REVIEW")
    if (review.readiness != DIAGNOSTIC_ONLY or
        review.author_status != "NO_AUTHOR_LABELLED_1D_4H_POI" or
        review.crosschecked_native_1d != len(review.native_1d_closed)):
        raise C17Rejected("FORGED_AUTHOR_OR_SOURCE_APPROVAL")
    if (type(as_of_ms) is not int or as_of_ms % TF_MS["15m"] or
        as_of_ms > review.as_of_ms or as_of_ms < 0 or
        type(review.as_of_ms) is not int or review.as_of_ms < 0 or
        review.as_of_ms % TF_MS["15m"]):
        raise C17Rejected("INVALID_OR_FUTURE_ASOF")
    if review.symbol not in ("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"):
        raise C17Rejected("UNSUPPORTED_FUTURES_SYMBOL")
    # C16 may contain later CLOSED bars; cut off before any evaluation.
    daily = tuple(x for x in review.native_1d_closed if x.known_at_ms <= as_of_ms)
    fourh = tuple(x for x in review.derived_4h_closed if x.known_at_ms <= as_of_ms)
    # All source records in a C16 review must themselves be closed as of its own timestamp.
    _validate_stream(review.native_1d_closed, "1d", review.symbol, review.as_of_ms)
    _validate_stream(review.derived_4h_closed, "4h", review.symbol, review.as_of_ms)
    if daily and fourh and daily[0].start_ms != fourh[0].start_ms:
        raise C17Rejected("CROSS_TF_START_BOUNDARY_MISMATCH")
    return C17HTFDiagnostic(review.symbol, as_of_ms,
                           _detect(daily,"1d",review.symbol),
                           _detect(fourh,"4h",review.symbol))
