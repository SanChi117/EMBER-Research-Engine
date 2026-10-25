"""C74 Route A author-golden intake: fail closed; never generates trading signals.

A timestamped crypto author-labelled golden is NOT present in the available
course files. Frozen C73 observations are source measurements, not author labels.
This module intentionally has no path to AUTHOR_VERIFIED / READY.
"""
from dataclasses import dataclass
import re

C73_SHA = "c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b"
SYMBOLS = frozenset(("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BCHUSDT"))
SHA = re.compile(r"^[0-9a-f]{64}$")
FIELDS = frozenset((
    "symbol", "venue", "route", "poi_tf", "poi_kind", "poi_source_id",
    "parent_4h_source_id", "parent_4h_vc_label", "poi_created_ms",
    "first_raw3m_id", "first_raw3m_closed_ms", "source_visit_episodes",
    "repeat_raw3m_id", "first_15m_event_kind", "first_15m_pattern_start_ms",
    "first_15m_event_closed_ms", "first_5m_event_kind", "first_5m_event_closed_ms",
    "author_first_valid_test_label", "author_15m_trigger_label",
    "author_15m_vc_label", "author_5m_vc_label", "stronghl_cause",
    "stronghl_confirmation", "course_route_a_id", "course_poi_id",
    "source_zip_sha256", "source_csv_sha256", "c73_source_sha256",
    "author_attestation_id", "as_of_ms"
))
ROUTE_A_ID = "1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ"
POI_ID = "1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R"
# Intentionally EMPTY until a separate, source-authenticated review is accepted.
PINNED_AUTHOR_CRYPTO_GOLDENS = frozenset()


class C74Rejected(ValueError):
    """A structurally invalid or spoofed author's evidence claim."""


@dataclass(frozen=True)
class C74Decision:
    source_status: str
    author_status: str = "NOT_VERIFIED"
    academic_route_fork: str = "UNRESOLVED"
    author_valid_first_test: bool = False
    author_15m_trigger: bool = False
    author_15m_vc: bool = False
    author_5m_vc: bool = False
    author_stronghl: bool = False
    orders: tuple = ()
    fills: tuple = ()
    trades: tuple = ()
    readiness: str = "NOT_TRADE_READY"


def _exact_int(v, name):
    if type(v) is not int or v <= 0:
        raise C74Rejected("BAD_TIMESTAMP_" + name)
    return v


def _typed_text(v, name):
    if type(v) is not str or not v or len(v) > 256:
        raise C74Rejected("BAD_TEXT_" + name)
    return v


def evaluate_author_academic_golden(p):
    """Validate candidate geometry/provenance but do not certify course events.

    No caller-controlled flag, signature string, source SHA or geometry can
    upgrade author status. Historical original-source price rows are not
    loaded by this static contract, so even SOURCE_ONLY is a *candidate*.
    """
    if type(p) is not dict or set(p) != FIELDS:
        raise C74Rejected("SCHEMA_EXACT_FIELDS_REQUIRED")
    for k in ("symbol", "venue", "route", "poi_tf", "poi_kind",
              "poi_source_id", "parent_4h_source_id", "parent_4h_vc_label",
              "first_raw3m_id", "first_15m_event_kind",
              "first_5m_event_kind", "course_route_a_id", "course_poi_id"):
        _typed_text(p[k], k)
    if p["symbol"] not in SYMBOLS or p["venue"] != "BINANCE_USDM":
        raise C74Rejected("CRYPTO_SOURCE_MISMATCH")
    if p["route"] != "A" or p["poi_tf"] != "1h" or p["poi_kind"] not in ("RB", "SNR", "IMB"):
        raise C74Rejected("ROUTE_OR_TF_OR_POI_MISMATCH")
    if p["parent_4h_vc_label"] != "UNVERIFIED":
        raise C74Rejected("UNVERIFIED_PARENT_MUST_NOT_BE_CERTIFIED")
    if p["course_route_a_id"] != ROUTE_A_ID or p["course_poi_id"] != POI_ID:
        raise C74Rejected("COURSE_PROVENANCE_MISMATCH")
    for k in ("source_zip_sha256", "source_csv_sha256", "c73_source_sha256"):
        if type(p[k]) is not str or not SHA.fullmatch(p[k]):
            raise C74Rejected("BAD_SOURCE_SHA_" + k)
    if p["c73_source_sha256"] != C73_SHA:
        raise C74Rejected("C73_FROZEN_SHA_MISMATCH")
    for k in ("author_first_valid_test_label", "author_15m_trigger_label",
              "author_15m_vc_label", "author_5m_vc_label"):
        if p[k] != "UNVERIFIED":
            raise C74Rejected("AUTHOR_LABEL_WITHOUT_EXTERNAL_GOLDEN_" + k)
    if p["author_attestation_id"] is not None:
        # Not even a plausible-looking author ID is a course/market attestation.
        raise C74Rejected("UNPINNED_AUTHOR_ATTESTATION")
    if p["stronghl_cause"] is not None or p["stronghl_confirmation"] is not None:
        raise C74Rejected("STRONGHL_REQUIRES_AUTHOR_CAUSE_AND_CONFIRMATION")
    a = _exact_int(p["as_of_ms"], "as_of_ms")
    created = _exact_int(p["poi_created_ms"], "poi_created_ms")
    touch = _exact_int(p["first_raw3m_closed_ms"], "first_raw3m_closed_ms")
    if not (created <= touch <= a):
        raise C74Rejected("FIRST_TOUCH_BEFORE_CREATION_OR_FUTURE")
    if type(p["source_visit_episodes"]) is not int or p["source_visit_episodes"] < 1:
        raise C74Rejected("INVALID_SOURCE_VISIT_EPISODES")
    if p["source_visit_episodes"] == 1 and p["repeat_raw3m_id"] is not None:
        raise C74Rejected("FALSE_REPEAT_VISIT")
    if p["source_visit_episodes"] > 1:
        _typed_text(p["repeat_raw3m_id"], "repeat_raw3m_id")
        if p["repeat_raw3m_id"] == p["first_raw3m_id"]:
            raise C74Rejected("SAME_RAW_ID_FALSE_REPEAT")
    kind = p["first_15m_event_kind"]
    if kind not in ("NONE", "RAW_IMB", "RAW_SNR", "AMBIGUOUS", "OPPOSITE"):
        raise C74Rejected("UNRECOGNIZED_15M_SOURCE_EVENT")
    start, close = p["first_15m_pattern_start_ms"], p["first_15m_event_closed_ms"]
    if kind == "NONE":
        if start is not None or close is not None:
            raise C74Rejected("EVENT_TIME_WITH_NO_EVENT")
    else:
        s, c = _exact_int(start, "first_15m_pattern_start_ms"), _exact_int(close, "first_15m_event_closed_ms")
        if not (touch <= s < c <= a):
            raise C74Rejected("FUTURE_OR_PRECONTACT_15M_EVENT")
    k5, t5 = p["first_5m_event_kind"], p["first_5m_event_closed_ms"]
    if k5 not in ("NONE", "RAW_IMB", "RAW_SNR", "AMBIGUOUS", "OPPOSITE"):
        raise C74Rejected("UNRECOGNIZED_5M_SOURCE_EVENT")
    if k5 == "NONE":
        if t5 is not None:
            raise C74Rejected("5M_TIME_WITHOUT_EVENT")
    else:
        if kind == "NONE":
            raise C74Rejected("ORPHAN_5M_EVENT")
        five_close = _exact_int(t5, "first_5m_event_closed_ms")
        if five_close <= close or five_close > a:
            raise C74Rejected("5M_EVENT_BEFORE_15M_KNOWN_OR_FUTURE")
    # Route B IDM and Route C Raid/BOS must use their own proof contracts.
    # Neither a single physical contact nor a repeat is author-valid/invalid.
    state = "SOURCE_ONLY_CANDIDATE" if kind in ("RAW_IMB", "RAW_SNR") else "UNRESOLVED"
    return C74Decision(source_status=state)
