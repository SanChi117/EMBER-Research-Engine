"""C76 read-only original-crypto FVG vs new 1H POI context audit.

C75's adapted FVG is a geometric detector, not academic IMB Trigger or VC.
All prior source C73 records must come from a separately SHA-pinned JSON.
No user-supplied 'author' flags can promote a source candidate to a trade.
"""
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from c75_external_imb_first_visit_lifecycle import (
    AdaptedFVG, C75Rejected, classify_c73_fork,
    EVIDENCE as ADAPTED)

SUPPORTED_KIND = {
    "1H_NEW_VC_RB_SOURCE": "RB_SOURCE_ONLY",
    "1H_NEW_VC_SNR_SOURCE": "SNR_SOURCE_ONLY",
    "1H_NEW_VC_IMB_SOURCE": "IMB_SOURCE_ONLY",
}


class C76Rejected(ValueError):
    pass


@dataclass(frozen=True)
class C76Context:
    symbol: str
    side: str
    parent_kind: str
    parent_first_touch: str
    parent_embedded_15m_fvg: str
    source_first_15m_fvg_at_event: bool
    eligible_nested_count: int
    eligible_overlap_count: int
    author_first_valid_poi_test: bool = False
    author_15m_trigger: bool = False
    author_15m_vc: bool = False
    author_5m_vc: bool = False
    author_stronghl: bool = False
    route_b_idm_approved: bool = False
    route_c_raid_bos_approved: bool = False
    readiness: str = "NOT_TRADE_READY"


def classify_original_parent_fvg(case, original_15m_fvgs):
    """Classify source-only parent geometries with deterministic causal cutoff.

    The source event after first POI visit is explicitly a *different* clock
    from any technical FVG that formed BEFORE the first POI contact.
    A nested 15m FVG in a 1H IMB parent is NOT automatically an eligible
    academic IMB Trigger. Parent RB/SNR type likewise does not prove VC.
    """
    try:
        cohort, _, evidence = classify_c73_fork(case)
    except (C75Rejected, AttributeError, KeyError, TypeError) as exc:
        raise C76Rejected("UNTRUSTED_C73_SOURCE_PARENT") from exc
    if evidence != ADAPTED or type(original_15m_fvgs) is not tuple:
        raise C76Rejected("UNTRUSTED_C75_ORIGINAL_15M_FVG_COHORT")
    symbol = case.get("symbol")
    side = case.get("side")
    if symbol not in ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BCHUSDT") or side not in ("LONG", "SHORT"):
        raise C76Rejected("CROSS_SYMBOL_OR_SIDE")
    if any(type(z) is not AdaptedFVG or z.tf != "15m"
           or z.symbol != symbol or z.evidence_class != ADAPTED
           or z.author_imb_vc or z.author_15m_trigger or z.author_entry
           or z.readiness != "NOT_TRADE_READY"
           for z in original_15m_fvgs):
        raise C76Rejected("FORGED_15M_ADAPTATION_OR_OTHER_ROUTE")
    kind = case.get("source_1h_poi_kind")
    if kind is None:
        if cohort != "SOURCE_INSUFFICIENT":
            raise C76Rejected("MISSING_PARENT_FOR_C73_FIRST_VISIT")
        return C76Context(symbol, side, "NO_SOURCE_NEW_1H_POI",
                          "NO_FIRST_TEST", "NONE", False, 0, 0)
    if kind not in SUPPORTED_KIND:
        raise C76Rejected("UNKNOWN_PARENT_1H_POI_KIND")
    created, touch = case.get("source_1h_poi_created_at_ms"), case.get(
        "original_first_source3m_touch_closed_ms")
    if type(created) is not int or created <= 0:
        raise C76Rejected("FORGED_PARENT_CREATION_TIME")
    try:
        bottom = Decimal(case["source_1h_poi_bottom"])
        top = Decimal(case["source_1h_poi_top"])
    except (InvalidOperation, ValueError, TypeError, KeyError) as e:
        raise C76Rejected("BAD_OR_MISSING_PARENT_BOUNDS") from e
    if not (bottom.is_finite() and top.is_finite() and 0 < bottom < top):
        raise C76Rejected("FORGED_PARENT_BOUNDS")
    event_closed = case.get("first_source15m_event_fully_known_ms")
    aligned = False
    if event_closed is not None:
        if type(event_closed) is not int or event_closed < created:
            raise C76Rejected("FORGED_SOURCE15M_EVENT_TIME")
        aligned = any(f.known_ms == event_closed and f.side == side
                      for f in original_15m_fvgs)
    if touch is None:
        if cohort != "SOURCE_INSUFFICIENT":
            raise C76Rejected("C73_VISIT_WITHOUT_TOUCH")
        return C76Context(symbol, side, SUPPORTED_KIND[kind],
                          "NO_FIRST_TEST", "NOT_TESTED", aligned, 0, 0)
    if type(touch) is not int or touch < created or (
            event_closed is not None and event_closed < touch):
        raise C76Rejected("FUTURE_PARENT_OR_OUT_OF_ORDER_EVENT")
    if cohort not in ("SOURCE_FIRST_VISIT", "SOURCE_REVISIT",
                      "SOURCE_INSUFFICIENT"):
        raise C76Rejected("UNSUPPORTED_C73_COHORT")
    contained = [f for f in original_15m_fvgs
                 if created <= f.known_ms <= touch and f.side == side
                 and bottom <= f.lower and f.upper <= top]
    overlapping = [f for f in original_15m_fvgs
                   if created <= f.known_ms <= touch and f.side == side
                   and f.upper >= bottom and f.lower <= top
                   and not (bottom <= f.lower and f.upper <= top)]
    if contained and kind == "1H_NEW_VC_IMB_SOURCE":
        status = "NESTED_IN_PARENT_IMB_INELIGIBLE_TO_ASSUME_TRIGGER"
    elif contained:
        status = "CONTAINED_FVG_IN_RB_OR_SNR_PARENT_UNVERIFIED"
    elif overlapping:
        status = "PARTIAL_PARENT_OVERLAP_NO_AUTOMATIC_ENTRY"
    else:
        status = "NO_PRETOUCH_SAME_SIDE_PARENT_FVG"
    first = ("SOURCE_REPEAT_VISIT" if cohort == "SOURCE_REVISIT" else
             "SOURCE_FIRST_VISIT" if cohort == "SOURCE_FIRST_VISIT" else
             "SOURCE_TOUCH_NO_UNAMBIGUOUS_15M_CHAIN")
    return C76Context(symbol, side, SUPPORTED_KIND[kind], first,
                      status, aligned, len(contained), len(overlapping))


def summarize_c76_original_contexts(cases, fvg15):
    """All contexts included, no selecting only successful price reactions."""
    if type(cases) is not list:
        raise C76Rejected("SOURCE_CASES_LIST_REQUIRED")
    out = tuple(classify_original_parent_fvg(c, fvg15) for c in cases)
    if any(x.readiness != "NOT_TRADE_READY" or any((
            x.author_first_valid_poi_test, x.author_15m_trigger, x.author_15m_vc,
            x.author_5m_vc, x.author_stronghl, x.route_b_idm_approved,
            x.route_c_raid_bos_approved)) for x in out):
        raise C76Rejected("FORGED_AUTHOR_TRADING_PROMOTION")
    return {
        "original_c73_contexts": len(out),
        "parent_kind_counts": dict(sorted(Counter(x.parent_kind for x in out).items())),
        "parent_fvg_context_counts": dict(sorted(Counter(
            x.parent_embedded_15m_fvg for x in out).items())),
        "first_touch_state_counts": dict(sorted(Counter(
            x.parent_first_touch for x in out).items())),
        "source15m_fvg_same_closed_event_count": sum(
            x.source_first_15m_fvg_at_event for x in out),
        "parent_contained_pretest_source15m_fvg_count": sum(
            x.eligible_nested_count for x in out),
        "parent_overlapping_pretest_source15m_fvg_count": sum(
            x.eligible_overlap_count for x in out),
        "author_approved": 0, "orders": 0, "fills": 0,
        "trades": 0, "readiness": "NOT_TRADE_READY",
    }
