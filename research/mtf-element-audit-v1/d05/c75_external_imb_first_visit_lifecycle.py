"""C75: external 3-candle FVG geometry as a *non-trading* adapted hypothesis.

Author Route A (IMB & SNR) is unchanged. Compatible outside references
describe a wick-to-wick three-bar FVG, but do not establish author Volume
Confirmation, correct parent POI or any statistical trading advantage.
Inputs are typed C21 original3m / C72 original5m / C16 original15m
source records; archive verification must occur in their upstream readers.
This module does not upgrade provenance from a plausible SHA string.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21_native3m_source_bridge import Original3mRow
from c72_original_native5m_source_vc_after15m_gate import Original5m
from c16_c08_monthly_daily_htf_lineage import NativeKline

PERIOD = {"3m": 180000, "5m": 300000, "15m": 900000}
BAR_CLASS = {"3m": Original3mRow, "5m": Original5m, "15m": NativeKline}
SYMBOLS = frozenset(("BCHUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"))
EVIDENCE = "ADAPTED_HYPOTHESIS"
AUTHOR_STATUS = "NOT_VERIFIED"


class C75Rejected(ValueError):
    pass


@dataclass(frozen=True)
class AdaptedFVG:
    symbol: str
    tf: str
    side: str
    lower: Decimal
    upper: Decimal
    first_bar_id: str
    third_bar_id: str
    known_ms: int
    source_sha: str
    evidence_class: str = EVIDENCE
    author_imb_vc: bool = False
    author_15m_trigger: bool = False
    author_entry: bool = False
    readiness: str = "NOT_TRADE_READY"


@dataclass(frozen=True)
class AdaptedFVGVisit:
    symbol: str
    tf: str
    fvg_known_ms: int
    first_touch_id: str | None
    first_touch_closed_ms: int | None
    separate_visits: int
    first_repeat_id: str | None
    first_close_through_id: str | None
    state: str
    evidence_class: str = EVIDENCE
    owner_first_valid_test: bool = False
    owner_15m_trigger: bool = False
    owner_15m_vc: bool = False
    owner_5m_vc: bool = False
    author_entry: bool = False
    orders: tuple = ()
    fills: tuple = ()
    trades: tuple = ()
    readiness: str = "NOT_TRADE_READY"


def _validate(rows, tf, as_of_ms):
    if (tf not in PERIOD or type(as_of_ms) is not int or as_of_ms <= 0
            or type(rows) is not tuple or not rows):
        raise C75Rejected("SOURCE_TF_ASOF_OR_TUPLE")
    step = PERIOD[tf]
    if type(rows[0]) is not BAR_CLASS[tf]:
        raise C75Rejected("NATIVE_TYPE_OR_CROSS_SYMBOL")
    symbol = rows[0].symbol
    if symbol not in SYMBOLS:
        raise C75Rejected("CRYPTO_SYMBOL")
    prev = None
    for bar in rows:
        if type(bar) is not BAR_CLASS[tf] or bar.symbol != symbol:
            raise C75Rejected("NATIVE_TYPE_OR_CROSS_SYMBOL")
        at = bar.start_ms
        known = bar.known_at_ms if tf == "15m" else bar.known_ms
        sha = bar.origin_zip_sha256 if tf == "15m" else bar.zip_sha
        row_id = bar.origin_raw_row_id if tf == "15m" else bar.raw_id
        if (tf == "15m" and bar.tf != "15m"
                or type(at) is not int or at <= 0 or at % step
                or type(known) is not int or known != at + step
                or known > as_of_ms or prev is not None and at != prev
                or type(sha) is not str or len(sha) != 64
                or any(z not in "0123456789abcdef" for z in sha)
                or row_id != sha + ":" + str(at)):
            raise C75Rejected("SOURCE_ID_CLOCK_GAP_FUTURE_OR_PROVENANCE")
        vals = (bar.open, bar.high, bar.low, bar.close, bar.volume)
        if (not all(type(v) is Decimal and v.is_finite() for v in vals)
                or not (0 < bar.low <= min(bar.open, bar.close)
                        <= max(bar.open, bar.close) <= bar.high)
                or bar.volume < 0):
            raise C75Rejected("NONFINITE_OR_IMPOSSIBLE_OHLCV")
        prev = known
    return symbol


def scan_native_fvg(rows, *, tf, as_of_ms):
    """Scan only three fully closed consecutive source candles; no lookahead."""
    symbol = _validate(rows, tf, as_of_ms)
    if len(rows) < 3:
        return ()
    out = []
    for i in range(2, len(rows)):
        first, third = rows[i - 2], rows[i]
        if third.low > first.high:
            side, lower, upper = "LONG", first.high, third.low
        elif third.high < first.low:
            side, lower, upper = "SHORT", third.high, first.low
        else:
            continue
        known = third.known_at_ms if tf == "15m" else third.known_ms
        sha = third.origin_zip_sha256 if tf == "15m" else third.zip_sha
        rid1 = first.origin_raw_row_id if tf == "15m" else first.raw_id
        rid3 = third.origin_raw_row_id if tf == "15m" else third.raw_id
        out.append(AdaptedFVG(symbol, tf, side, lower, upper,
                              rid1, rid3, known, sha))
    return tuple(out)


def inspect_fvg_visits(zone, rows, *, as_of_ms):
    """Continuous overlapping bars = one visit; later separately re-entered
    bar counts after >=1 fully OUTSIDE bar, following frozen C73 semantics.

    A candle closing beyond the far boundary invalidates the *candidate*.
    Same-bar wick/close path is unknown and never simulated as an entry.
    """
    if type(zone) is not AdaptedFVG or zone.evidence_class != EVIDENCE:
        raise C75Rejected("UNTRUSTED_ZONE_OR_AUTHOR_FLAG")
    symbol = _validate(rows, zone.tf, as_of_ms)
    if zone.symbol != symbol or zone not in scan_native_fvg(
            rows, tf=zone.tf, as_of_ms=as_of_ms):
        raise C75Rejected("ZONE_NOT_RECOMPUTED_FROM_SOURCE")
    first = repeat = invalid = None
    first_closed = None
    count = 0
    in_episode = False
    for bar in rows:
        closed = bar.known_at_ms if zone.tf == "15m" else bar.known_ms
        if closed <= zone.known_ms:
            continue
        rid = bar.origin_raw_row_id if zone.tf == "15m" else bar.raw_id
        overlaps = bar.high >= zone.lower and bar.low <= zone.upper
        if overlaps and not in_episode:
            count += 1
            if first is None:
                first, first_closed = rid, closed
            elif repeat is None:
                repeat = rid
        in_episode = overlaps
        # No intrabar assumption: only fully closed invalidation is known.
        if (zone.side == "LONG" and bar.close < zone.lower
                or zone.side == "SHORT" and bar.close > zone.upper):
            invalid = rid
            break
    state = ("CLOSED_THROUGH_FVG_NOT_AUTHOR" if invalid is not None else
             "NO_TEST_RIGHT_CENSORED" if count == 0 else
             "FIRST_VISIT_SOURCE_ONLY" if count == 1 else
             "REPEATED_VISIT_SOURCE_ONLY")
    return AdaptedFVGVisit(symbol, zone.tf, zone.known_ms, first,
                           first_closed, count, repeat, invalid, state)


def classify_c73_fork(frozen_case):
    """Read-only label on immutable C73 source case; NEVER decides Trigger/VC.

    The caller MUST use readback of pinned C73 bytes; it is not a proof
    verifier for arbitrary dictionary objects.
    """
    if type(frozen_case) is not dict or frozen_case.get("readiness") != "NOT_TRADE_READY":
        raise C75Rejected("FORGED_C73_CASE")
    if any(frozen_case.get(k) is not False for k in (
            "author_15m_trigger", "author_15m_vc", "author_1h_poi_valid_first_test",
            "author_5m_vc", "author_entry", "author_stronghl",
            "author_structural_sl", "route_b_idm_used", "route_c_raid_bos_used")):
        raise C75Rejected("C73_AUTHOR_FLAG_OR_ROUTE_CROSSOVER")
    if any(frozen_case.get(k) != [] for k in ("orders", "fills", "trades")):
        raise C75Rejected("C73_UNVERIFIED_TRADES")
    state = frozen_case.get("state")
    known = {
        "NEW_1H_POI_FIRST_15M_PATTERN_SINGLE_SOURCE_VISIT_NOT_OWNER_VALID":
            ("SOURCE_FIRST_VISIT", 1),
        "NEW_1H_POI_FIRST_15M_PATTERN_REVISITED_SOURCE_POI_NOT_OWNER_VALID":
            ("SOURCE_REVISIT", 2)
    }
    if state in known:
        label, n = known[state]
        episodes = frozen_case.get("episodes_before_first_15m_pattern")
        if type(episodes) is not int or episodes < n or (n == 1 and episodes != 1):
            raise C75Rejected("C73_VISIT_STATE_SPOOF")
        return label, "15M_TRIGGER_VS_VC_UNRESOLVED", EVIDENCE
    if state not in (
            "NOT_NEW_1H_POI_SOURCE_BRANCH",
            "NEW_1H_POI_SOURCE_NO_ORIGINAL3M_FIRST_TOUCH",
            "NEW_1H_POI_FIRST_ANY_RAW3M_TOUCH_NO_UNAMBIGUOUS_15M_CHAIN"):
        raise C75Rejected("C73_UNKNOWN_STATE")
    return "SOURCE_INSUFFICIENT", "15M_TRIGGER_VS_VC_UNRESOLVED", EVIDENCE
