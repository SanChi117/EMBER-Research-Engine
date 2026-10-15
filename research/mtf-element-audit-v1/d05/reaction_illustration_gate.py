"""Read-only D05 course illustration trace-checker — NEVER an executable trade strategy.

The subject is _relationships around a price level_. Absolute candles, time,
exchange and performance are not implied by conceptual textbook figures.
This module only checks a source-linked qualitative description against written
course invariants. Real signal approval remains separate and requires D01-D04,
actual Futures series, as-of structure and independent visual verification.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

SOURCE_STATUS = "SOURCE_REACTION_SEQUENCE_CONSISTENT_NOT_MARKET_ATTESTED"
REVIEW_STATUS = "SOURCE_ILLUSTRATION_NEEDS_HUMAN_REVIEW"
SOURCE_ERROR = "SOURCE_INVARIANT_CONTRADICTION"
IMAGE_SHA = re.compile(r"[0-9a-f]{64}\Z")
ALLOWED_KINDS = {"AUTHOR_TEXT_SEQUENCE","SOURCE_ILLUSTRATION","TEXT_DERIVED_NEGATIVE_CONTRAST"}

class D05ReactionRejected(ValueError):
    pass

def evaluate_sequence(family: str, events: list[str]) -> str:
    """Qualitative source invariants only. No OHLCV, timestamps, trades or PnL."""
    if not isinstance(events,list) or not events or len(set(events))!=len(events):
        raise D05ReactionRejected("INVALID_ILLUSTRATIVE_EVENT_SEQUENCE")
    if not all(isinstance(e,str) and e for e in events):
        raise D05ReactionRejected("INVALID_EVENT_TOKEN")
    def in_order(*tokens):
        return all(t in events for t in tokens) and [events.index(t) for t in tokens] == sorted(events.index(t) for t in tokens)
    if family=="SNR":
        if in_order("SNR_PAIR_PRESENT","NO_LIQUIDITY_RAID_AND_NO_FVG_TEST","RETURN_TO_POI"):
            return "MITIGATION_BLOCK_NOT_STRONG_VC"
        if in_order("CANDLE_PAIR_BUY_SELL","SSL_RAID_OR_NEGATIVE_FVG_TEST",
                    "BULLISH_FULL_CLOSE_ABOVE_PAIR_LEVEL","FIRST_SNR_TEST",
                    "LONG_REACTION_MAY_OCCUR"):
            return "TEXT_CONSISTENT_SEQUENCE_NOT_SIGNAL"
        return "NEEDS_SOURCE_SEQUENCE"
    if family=="IMB":
        if "WICKS_OVERLAP_FIRST_AND_THIRD" in events:
            return "NOT_IMB_THREE_CANDLE_GAP"
        if in_order("THREE_CANDLES","WICK_GAP_BETWEEN_FIRST_AND_THIRD",
                    "ZONE_RETURNS_AND_REACTION_POSSIBLE"):
            return "IMB_CANDIDATE_GEOMETRY_ONLY"
        return "NEEDS_SOURCE_GEOMETRY"
    if family=="POI":
        if "SECOND_RETURN_TO_SAME_POI" in events:
            return "NOT_FIRST_TEST_DO_NOT_MISLABEL" if in_order(
                "POI_FORMED","FIRST_RETURN_TO_POI","SECOND_RETURN_TO_SAME_POI"
            ) else "NEEDS_SOURCE_SEQUENCE"
        if in_order("POI_FORMED","FIRST_RETURN_TO_POI","RESPONSE_POSSIBLE"):
            return "FIRST_TEST_HAS_COURSE_PRIORITY_NOT_GUARANTEE"
        if in_order("POI_WITHOUT_VERIFIED_SSL_BSL_OR_FVG","PRICE_RETURNS_TO_POI","REACTION_MAY_OCCUR"):
            return "STRONG_POI_EVIDENCE_MISSING"
        if in_order("POI_WITH_SSL_BSL_OR_FVG_CONTEXT","PRICE_RETURNS_TO_POI","REACTION_MAY_OCCUR"):
            return "CONTEXTUAL_POI_ILLUSTRATION_ONLY"
        return "NEEDS_SOURCE_SEQUENCE"
    raise D05ReactionRejected("UNSUPPORTED_COURSE_FAMILY")

def validate_source_cases(doc: Mapping, c02: Mapping) -> dict:
    if doc.get("source_role")!="ACADEMIC_REACTION_ILLUSTRATION":
        raise D05ReactionRejected("WRONG_EVIDENCE_ROLE")
    if doc.get("replay_requirement")!="NOT_REQUIRED_FOR_SOURCE_MECHANISM_DESCRIPTION":
        raise D05ReactionRejected("IMPOSED_NUMERIC_REQUIREMENT_ON_SCHEMATIC")
    if doc.get("separate_automatic_trading_requirement")!="REQUIRES_FUTURES_REPLAY_AND_SOURCE_ALIGNED_ALGORITHM":
        raise D05ReactionRejected("FUTURES_EXECUTION_GATE_BYPASSED")
    a=doc.get("acceptance",{})
    if (a.get("academic_market_patterns_independently_approved")!=0 or
        a.get("automatic_trade_plans_allowed")!=0 or a.get("uses_absolute_market_timestamps") is not False):
        raise D05ReactionRejected("UNPROVEN_TRADE_OR_TIMELINE_PROMOTION")
    inventory={x["id"]:x for x in c02["items"] if x.get("is_image")}
    figs=doc.get("figures",[])
    if not isinstance(figs,list) or not figs:
        raise D05ReactionRejected("MISSING_SOURCE_FIGURES")
    if len({f.get("id") for f in figs})!=len(figs):
        raise D05ReactionRejected("DUPLICATE_FIGURE")
    for fig in figs:
        original=inventory.get(fig.get("drive_id"))
        if original is None or fig.get("sha256")!=original.get("sha256") or not IMAGE_SHA.fullmatch(str(fig.get("sha256",""))):
            raise D05ReactionRejected("FIGURE_NOT_SHA_LINKED_TO_SOURCE")
    by_figure={f["id"]:f for f in figs}
    sources=doc.get("primary_text_sources",{})
    if set(sources)!={"SNR","POI","IMB"} or not all(str(v).startswith("https://drive.google.com/file/d/") for v in sources.values()):
        raise D05ReactionRejected("MISSING_OR_WRONG_LESSON")
    cases=doc.get("cases",[])
    if not isinstance(cases,list) or len({c.get("case_id") for c in cases})!=len(cases):
        raise D05ReactionRejected("DUPLICATE_CASES")
    if len(cases)!=a.get("mechanism_examples_illustrated"):
        raise D05ReactionRejected("CASE_COUNT_MISMATCH")
    for case in cases:
        if case.get("family") not in sources or case.get("kind") not in ALLOWED_KINDS:
            raise D05ReactionRejected("INVALID_FAMILY_OR_CASE_SOURCE_ROLE")
        if case.get("image_id") not in by_figure:
            raise D05ReactionRejected("UNLINKED_AUTHOR_ILLUSTRATION")
        if case.get("kind")=="TEXT_DERIVED_NEGATIVE_CONTRAST" and case.get("positive") is not False:
            raise D05ReactionRejected("NEGATIVE_NOT_MARKED_AS_DERIVED")
        observed=evaluate_sequence(case["family"],case.get("events"))
        if observed!=case.get("claim"):
            raise D05ReactionRejected("SOURCE_SEQUENCE_VERSUS_CLAIM_MISMATCH:"+case["case_id"])
        if not case.get("limits") or not all(isinstance(v,str) and v for v in case["limits"]):
            raise D05ReactionRejected("NO_SCOPE_LIMIT")
    conflicts=doc.get("source_conflicts",[])
    if not conflicts or any(x.get("resolution")!="UNRESOLVED_DO_NOT_HARDCODE_CANDLE_ORDER_AS_STRONG_SNR" for x in conflicts):
        raise D05ReactionRejected("SNR_AMBIGUITY_HIDDEN_OR_FALSELY_RESOLVED")
    if not doc.get("errata"):
        raise D05ReactionRejected("MISSING_PREVIOUS_MB_MISLABEL_CORRECTION")
    return {
        "source_illustrations":len(figs),
        "source_level_cases":len(cases),
        "negative_derived":sum(x["kind"]=="TEXT_DERIVED_NEGATIVE_CONTRAST" for x in cases),
        "unresolved_source_conflicts":len(conflicts),
        "academic_market_approvals":0,
        "ready_trade_plans":0,
        "verdict":SOURCE_STATUS,
        "boundary":REVIEW_STATUS
    }
