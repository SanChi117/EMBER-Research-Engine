"""C58: stable 1H parent identity and fail-closed 3m/5m observation state.

C56 establishes technical native-3m/native-5m closed-break observations for
one exact 1H raid. C58 does not create another detector. It gives that parent
a deterministic identity and distinguishes an actually observed single-TF
event from an unobservable TF caused by incomplete source coverage.

A missing C56 event is a confirmed detector absence only when that native TF
source is complete through the same as-of. Timing disagreement is NOT a
market-direction contradiction. Everything remains ADAPTED, source-only,
PAPER ONLY and NOT_TRADE_READY; no entry, order, fill or author approval.
"""
from dataclasses import dataclass
import hashlib

from c56_crypto_native5m_1h_raid_bos_cross_tf import (
    BARRIERS,
    C56CrossTimeframeParent,
    MISSING,
    REG,
    TYPES,
)

HOUR = 3_600_000
TF_MS = {"3m": 180_000, "5m": 300_000}
SYMBOLS = ("BCHUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT")
BOTH = "BOTH_CHILD_BREAKS_OBSERVED"
ONLY_3M = "ONLY_3M_CHILD_BREAK_OBSERVED_5M_ABSENT_IN_COMPLETE_SOURCE"
ONLY_5M = "ONLY_5M_CHILD_BREAK_OBSERVED_3M_ABSENT_IN_COMPLETE_SOURCE"
UNKNOWN_3M = "UNKNOWN_3M_SOURCE_NOT_COMPLETE_AT_AS_OF"
UNKNOWN_5M = "UNKNOWN_5M_SOURCE_NOT_COMPLETE_AT_AS_OF"
STATE_TYPES = (BOTH, ONLY_3M, ONLY_5M, UNKNOWN_3M, UNKNOWN_5M)


@dataclass(frozen=True)
class NativeSourceCoverage:
    """Knowledge boundary of one original native stream, not live availability."""

    timeframe: str
    complete: bool
    closed_through_ms: int
    original_native_rows: int


@dataclass(frozen=True)
class C58RouteCParentState:
    parent_id: str
    parent: C56CrossTimeframeParent
    as_of_ms: int
    coverage_3m: NativeSourceCoverage
    coverage_5m: NativeSourceCoverage
    observation_state: str
    timing_interpretation: str
    semantic_label: str = "ADAPTED_ROUTE_C_PARENT_CHILD_OBSERVATION"
    author_object_identity_approved: bool = False
    author_bos_approved: bool = False
    orders: tuple = ()
    fills: tuple = ()
    trades: tuple = ()
    readiness: str = "NOT_TRADE_READY"


def _integer(value, label):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"C58_BAD_{label}_TYPE")
    return value


def parent_identity(parent):
    """Stable identity of the exact 1H object; child bars cannot rename it."""
    if not isinstance(parent, C56CrossTimeframeParent):
        raise ValueError("C58_UNTRUSTED_C56_PARENT")
    fields = (
        parent.symbol,
        parent.raid_type,
        parent.first_1h_pivot_center_ms,
        parent.first_1h_breach_ms,
        parent.raid_closed_known_ms,
    )
    canonical = "\0".join(str(value) for value in fields)
    digest = hashlib.sha256(("EMBER_C58_1H_PARENT_V1\0" + canonical).encode()).hexdigest()
    return "c58-1h-" + digest


def _validate_raw(raw_id, known_ms, timeframe):
    step = TF_MS[timeframe]
    if not isinstance(raw_id, str) or not REG.fullmatch(raw_id):
        raise ValueError(f"C58_BAD_ORIGINAL_{timeframe}_RAW_ID")
    if int(raw_id.rsplit(":", 1)[1]) != known_ms - step:
        raise ValueError(f"C58_{timeframe}_RAW_ID_NOT_NATIVE_BAR_OPEN")
    if known_ms % step:
        raise ValueError(f"C58_{timeframe}_CLOSE_NOT_ON_NATIVE_GRID")


def validate_c56_parent(parent, as_of_ms):
    if not isinstance(parent, C56CrossTimeframeParent):
        raise ValueError("C58_UNTRUSTED_C56_PARENT")
    _integer(as_of_ms, "AS_OF")
    if parent.symbol not in SYMBOLS or parent.raid_type not in ("BSL", "SSL"):
        raise ValueError("C58_UNSUPPORTED_MARKET_OR_LIQUIDITY_KIND")
    center = _integer(parent.first_1h_pivot_center_ms, "PARENT_CENTER")
    breach = _integer(parent.first_1h_breach_ms, "PARENT_BREACH")
    confirmed = _integer(parent.raid_closed_known_ms, "PARENT_CONFIRMED")
    if (center % HOUR or breach % HOUR or confirmed % HOUR or
            center + 2 * HOUR > breach or confirmed != breach + 2 * HOUR or
            confirmed > as_of_ms):
        raise ValueError("C58_INVALID_OR_FUTURE_1H_PARENT_CAUSALITY")
    if (parent.author_bos_approved or parent.author_fill_approved or
            parent.orders or parent.trades or parent.readiness != "NOT_TRADE_READY" or
            parent.blockers != BARRIERS):
        raise ValueError("C58_AUTHOR_OR_TRADE_PROMOTION_FORBIDDEN")
    present3 = parent.original_3m_bos_raw_id is not None
    present5 = parent.original_5m_bos_raw_id is not None
    if present3 != (parent.original_3m_bos_known_ms is not None):
        raise ValueError("C58_PARTIAL_3M_EVENT")
    if present5 != (parent.original_5m_bos_known_ms is not None):
        raise ValueError("C58_PARTIAL_5M_EVENT")
    if not present3 and not present5:
        raise ValueError("C58_PARENT_WITHOUT_ANY_CHILD_EVENT")
    known3 = known5 = None
    if present3:
        known3 = _integer(parent.original_3m_bos_known_ms, "3M_KNOWN")
        _validate_raw(parent.original_3m_bos_raw_id, known3, "3m")
        if known3 <= confirmed or known3 > as_of_ms:
            raise ValueError("C58_FUTURE_OR_PRE_PARENT_3M_EVENT")
    if present5:
        known5 = _integer(parent.original_5m_bos_known_ms, "5M_KNOWN")
        _validate_raw(parent.original_5m_bos_raw_id, known5, "5m")
        if known5 <= confirmed or known5 > as_of_ms:
            raise ValueError("C58_FUTURE_OR_PRE_PARENT_5M_EVENT")
    if present3 and present5:
        if (parent.original_3m_bos_raw_id.split(":", 1)[0] ==
                parent.original_5m_bos_raw_id.split(":", 1)[0]):
            raise ValueError("C58_BORROWED_CROSS_TF_RAW_ID")
        expected = (TYPES[0] if known3 < known5 else
                    TYPES[1] if known3 > known5 else TYPES[2])
    elif present3:
        expected = MISSING[0]
    else:
        expected = MISSING[1]
    if parent.source_status != expected:
        raise ValueError("C58_C56_STATUS_EVENT_MISMATCH")
    return present3, present5


def _coverage(coverage, timeframe, as_of_ms):
    if not isinstance(coverage, NativeSourceCoverage) or coverage.timeframe != timeframe:
        raise ValueError(f"C58_WRONG_{timeframe}_COVERAGE")
    _integer(coverage.closed_through_ms, f"{timeframe}_COVERAGE")
    rows = _integer(coverage.original_native_rows, f"{timeframe}_ROWS")
    if rows <= 0 or not isinstance(coverage.complete, bool):
        raise ValueError(f"C58_INVALID_{timeframe}_COVERAGE")
    through = coverage.closed_through_ms
    if through % TF_MS[timeframe] or through > as_of_ms:
        raise ValueError(f"C58_FUTURE_OR_UNALIGNED_{timeframe}_COVERAGE")
    return coverage.complete and through == as_of_ms


def identify_route_c_parent_state(parent, *, as_of_ms, coverage_3m, coverage_5m):
    present3, present5 = validate_c56_parent(parent, as_of_ms)
    complete3 = _coverage(coverage_3m, "3m", as_of_ms)
    complete5 = _coverage(coverage_5m, "5m", as_of_ms)
    if present3 and present5:
        state = BOTH
        timing = ("SAME_CLOSED_KNOWLEDGE_TIME_DISTINCT_NATIVE_EVENTS"
                  if parent.source_status == TYPES[2] else
                  "DIFFERENT_CLOSED_KNOWLEDGE_TIMES_NOT_CONTRADICTION")
    elif present3:
        state = ONLY_3M if complete5 else UNKNOWN_5M
        timing = ("SINGLE_3M_EVENT_NO_5M_AGREEMENT_CLAIM" if complete5 else
                  "MISSING_5M_NOT_OBSERVABLE_AT_AS_OF")
    else:
        state = ONLY_5M if complete3 else UNKNOWN_3M
        timing = ("SINGLE_5M_EVENT_NO_3M_AGREEMENT_CLAIM" if complete3 else
                  "MISSING_3M_NOT_OBSERVABLE_AT_AS_OF")
    return C58RouteCParentState(
        parent_identity(parent), parent, as_of_ms, coverage_3m, coverage_5m,
        state, timing,
    )


def build_parent_state_registry(states):
    """One exact 1H object once: prevent duplicate contexts becoming samples."""
    registry = {}
    for state in states:
        if not isinstance(state, C58RouteCParentState):
            raise ValueError("C58_UNTRUSTED_REGISTRY_ITEM")
        if state.parent_id != parent_identity(state.parent):
            raise ValueError("C58_FORGED_PARENT_ID")
        expected = identify_route_c_parent_state(
            state.parent, as_of_ms=state.as_of_ms,
            coverage_3m=state.coverage_3m, coverage_5m=state.coverage_5m,
        )
        if state != expected:
            raise ValueError("C58_FORGED_STATE_FIELDS")
        if state.parent_id in registry:
            raise ValueError("C58_DUPLICATE_1H_PARENT_IDENTITY")
        registry[state.parent_id] = state
    return tuple(registry[key] for key in sorted(registry))
