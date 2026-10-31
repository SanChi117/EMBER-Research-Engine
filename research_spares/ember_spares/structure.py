"""Z11, Z13-Z18, Z19 and Z28: causal OHLC features and state machines.

These algorithms are independent reference implementations, not copies of a
third-party strategy and not guaranteed to be identical to external engines.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import sqrt
from statistics import fmean
from typing import Sequence

from .types import Candle, finite, positive


@dataclass(frozen=True)
class Zone:
    zone_id: str
    side: str  # demand or supply
    low: float
    high: float
    born_at: int
    phase: str = "ACTIVE"  # ACTIVE/TESTED/BROKEN/FLIPPED
    touches: int = 0
    inside: bool = False
    last_updated_at: int = 0

    def __post_init__(self) -> None:
        positive(self.low, self.high)
        if self.low >= self.high or self.side not in ("demand", "supply") or self.phase not in ("ACTIVE", "TESTED", "BROKEN", "FLIPPED"):
            raise ValueError("bad zone")
        if not self.zone_id or self.touches < 0:
            raise ValueError("bad zone state")


def advance_zone(zone: Zone, candle: Candle) -> Zone:
    """Z11. Zone invalidation is a CLOSED-candle close, not a wick.

    Once BROKEN, a subsequent price overlap labels a FLIPPED *candidate*;
    an actual support/resistance flip still needs separate confirmation.
    """
    if candle.available_at <= zone.born_at:
        return zone
    if candle.available_at <= zone.last_updated_at:
        raise ValueError("duplicate or out-of-order zone update")
    overlapping = candle.low <= zone.high and candle.high >= zone.low
    if zone.phase == "FLIPPED":
        return zone
    if zone.phase == "BROKEN":
        return replace(zone, phase="FLIPPED", last_updated_at=candle.available_at) if overlapping else replace(zone, last_updated_at=candle.available_at)
    broke = (zone.side == "demand" and candle.close < zone.low) or (zone.side == "supply" and candle.close > zone.high)
    if broke:
        return replace(zone, phase="BROKEN", inside=False, last_updated_at=candle.available_at)
    touched = zone.touches + (1 if overlapping and not zone.inside else 0)
    return replace(zone, touches=touched, inside=overlapping, phase="TESTED" if touched else "ACTIVE", last_updated_at=candle.available_at)


@dataclass(frozen=True)
class Rule:
    """Safe declarative candle condition; no eval/exec, no arbitrary lookahead."""
    field: str
    operator: str
    value: float
    offset: int = 0  # 0=current closed candle; 1=previous, etc.

    def __post_init__(self) -> None:
        if self.field not in ("open", "high", "low", "close", "volume") or self.operator not in (">", ">=", "<", "<=", "==") or self.offset < 0:
            raise ValueError("invalid rule")
        finite(self.value)


def evaluate_rules(candles: Sequence[Candle], rules: Sequence[Rule], decision_at: int) -> bool:
    """Z13. All conditions must be fully observable when evaluated."""
    if not rules:
        raise ValueError("empty rule set")
    available = [c for c in candles if c.available_at <= decision_at]
    if len(available) <= max(r.offset for r in rules):
        return False
    for r in rules:
        lhs = getattr(available[-1-r.offset], r.field)
        ok = {">": lambda: lhs > r.value, ">=": lambda: lhs >= r.value,
              "<": lambda: lhs < r.value, "<=": lambda: lhs <= r.value,
              "==": lambda: lhs == r.value}[r.operator]()
        if not ok:
            return False
    return True


@dataclass(frozen=True)
class CompressionState:
    phase: str = "IDLE"  # IDLE/COMPRESSED/BREAKOUT/FAILED/RESTART
    boundary_low: float = 0.0
    boundary_high: float = 0.0
    direction: str = "none"


def advance_compression(state: CompressionState, candle: Candle, *,
                        is_compressed: bool = False, compressed_range: tuple[float, float] | None = None) -> CompressionState:
    """Z14. Caller provides a historical-only compression classification.

    The state stores the frozen compression boundaries; a bar closing back
    inside after breakout becomes FAILED; a new close beyond boundary RESTART.
    """
    if is_compressed and state.phase in ("IDLE", "FAILED"):
        if compressed_range is None:
            raise ValueError("missing historical compression range")
        lo, hi = compressed_range
        positive(lo, hi)
        if lo >= hi:
            raise ValueError("range")
        return CompressionState("COMPRESSED", lo, hi, "none")
    if state.phase == "COMPRESSED":
        if candle.close > state.boundary_high:
            return replace(state, phase="BREAKOUT", direction="long")
        if candle.close < state.boundary_low:
            return replace(state, phase="BREAKOUT", direction="short")
    if state.phase == "BREAKOUT":
        failed = (state.direction == "long" and candle.close < state.boundary_high) or (state.direction == "short" and candle.close > state.boundary_low)
        if failed:
            return replace(state, phase="FAILED")
    if state.phase == "FAILED":
        if (state.direction == "long" and candle.close > state.boundary_high) or (state.direction == "short" and candle.close < state.boundary_low):
            return replace(state, phase="RESTART")
    return state


@dataclass(frozen=True)
class ConfirmedPivot:
    index: int
    confirmed_at: int
    price: float
    kind: str


def confirmed_pivots(candles: Sequence[Candle], left: int = 2, right: int = 2, *, decision_at: int | None = None) -> list[ConfirmedPivot]:
    """Z15. A pivot at bar i becomes known only at bar i+right close."""
    if left < 1 or right < 1:
        raise ValueError("pivot spans")
    available = [c for c in candles if decision_at is None or c.available_at <= decision_at]
    output: list[ConfirmedPivot] = []
    for i in range(left, len(available)-right):
        c = available[i]
        highs = [available[j].high for j in range(i-left, i+right+1) if j != i]
        lows = [available[j].low for j in range(i-left, i+right+1) if j != i]
        if all(c.high > h for h in highs):
            output.append(ConfirmedPivot(i, available[i+right].available_at, c.high, "high"))
        if all(c.low < l for l in lows):
            output.append(ConfirmedPivot(i, available[i+right].available_at, c.low, "low"))
    return output


def double_top(candles: Sequence[Candle], tolerance: float = 0.01, min_valley_depth: float = 0.005,
               left: int = 2, right: int = 2) -> tuple[ConfirmedPivot, ConfirmedPivot] | None:
    """Z15. Historical, *confirmed* similar highs with a valley between.

    This detects an established pattern, not a tradable short entry; neckline
    break and exit risk must be specified in the individual strategy.
    """
    if not (0 <= tolerance < 1 and 0 <= min_valley_depth < 1):
        raise ValueError("parameters")
    highs = [p for p in confirmed_pivots(candles, left, right) if p.kind == "high"]
    if len(highs) < 2:
        return None
    a, b = highs[-2:]
    valley = min(c.low for c in candles[a.index + 1:b.index]) if b.index > a.index + 1 else float("inf")
    approx_peak = (a.price + b.price) / 2
    if abs(a.price - b.price) / approx_peak <= tolerance and (approx_peak - valley) / approx_peak >= min_valley_depth:
        return a, b
    return None


@dataclass(frozen=True)
class FvgChannel:
    bull_mid: float | None
    bear_mid: float | None
    bull_count: int
    bear_count: int


def fvg_channel(candles: Sequence[Candle], lookback: int = 30, minimum_gap: float = 0.0) -> FvgChannel:
    """Z16. Mean of prior 3-candle FVG midpoints, not the LuxAlgo algorithm.

    No forward mitigation or future zone assignment is assumed.
    """
    if lookback < 3 or minimum_gap < 0:
        raise ValueError("invalid fvg params")
    segment = candles[-lookback:]
    bull: list[float] = []
    bear: list[float] = []
    for i in range(2, len(segment)):
        left, right = segment[i-2], segment[i]
        if right.low - left.high > minimum_gap:
            bull.append((left.high + right.low) / 2)
        if left.low - right.high > minimum_gap:
            bear.append((right.high + left.low) / 2)
    return FvgChannel(fmean(bull) if bull else None, fmean(bear) if bear else None, len(bull), len(bear))


def failed_breakout(previous: Candle, current: Candle, level: float, side: str) -> bool:
    """Z17. Confirmed false break on the next CLOSED candle."""
    positive(level)
    if current.available_at <= previous.available_at:
        raise ValueError("reversed time")
    if side == "long":
        return previous.close > level and current.close < level
    if side == "short":
        return previous.close < level and current.close > level
    raise ValueError("side")


@dataclass(frozen=True)
class HysteresisRegime:
    state: str = "range"
    pending: str = "range"
    count: int = 0


def advance_regime(prior: HysteresisRegime, trend_strength: float, *,
                   enter_threshold: float = 0.8, exit_threshold: float = 0.4, persistence: int = 3) -> HysteresisRegime:
    """Z18. Absolute trend-strength hysteresis with minimum successive bars."""
    finite(trend_strength, enter_threshold, exit_threshold)
    if not (0 <= exit_threshold < enter_threshold) or persistence < 1:
        raise ValueError("hysteresis parameters")
    candidate = prior.state
    if prior.state == "range" and abs(trend_strength) >= enter_threshold:
        candidate = "up" if trend_strength > 0 else "down"
    elif prior.state in ("up", "down"):
        if abs(trend_strength) <= exit_threshold:
            candidate = "range"
        elif abs(trend_strength) >= enter_threshold and (trend_strength > 0) != (prior.state == "up"):
            candidate = "up" if trend_strength > 0 else "down"
    if candidate == prior.state:
        return HysteresisRegime(prior.state, prior.state, 0)
    count = prior.count + 1 if prior.pending == candidate else 1
    return HysteresisRegime(candidate, candidate, 0) if count >= persistence else HysteresisRegime(prior.state, candidate, count)


def weighted_ma(values: Sequence[float], window: int) -> list[float | None]:
    if window < 1:
        raise ValueError("window")
    out: list[float | None] = [None] * len(values)
    denom = window * (window + 1) / 2
    for i in range(window - 1, len(values)):
        out[i] = sum((j+1) * x for j, x in enumerate(values[i-window+1:i+1])) / denom
    return out


def hull_ma(values: Sequence[float], window: int) -> list[float | None]:
    """Z19. Standard HMA via WMA(2*WMA(n/2)-WMA(n),sqrt(n))."""
    if window < 2:
        raise ValueError("HMA period >= 2")
    half = weighted_ma(values, max(1, window // 2))
    full = weighted_ma(values, window)
    difference = [2*h-f if h is not None and f is not None else None for h, f in zip(half, full)]
    # Preserve the original indices while skipping no missing warm-up values.
    weight = max(1, round(sqrt(window)))
    out: list[float | None] = [None] * len(values)
    denom = weight * (weight + 1) / 2
    for i in range(weight - 1, len(values)):
        sample = difference[i-weight+1:i+1]
        if all(x is not None for x in sample):
            out[i] = sum((j+1) * x for j, x in enumerate(sample)) / denom
    return out


def supertrend(candles: Sequence[Candle], period: int = 10, multiplier: float = 3.0) -> list[tuple[float | None, int]]:
    """Z19. Wilder ATR and trailing bands; direction is computed on closed bars."""
    if period < 1 or multiplier <= 0:
        raise ValueError("parameters")
    n = len(candles)
    if not n:
        return []
    tr = []
    for i, c in enumerate(candles):
        tr.append(max(c.high-c.low, abs(c.high-candles[i-1].close), abs(c.low-candles[i-1].close)) if i else c.high-c.low)
    atr: list[float | None] = [None]*n
    if n >= period:
        atr[period-1] = sum(tr[:period])/period
        for i in range(period, n):
            atr[i] = (atr[i-1]*(period-1) + tr[i])/period  # type: ignore[operator]
    result: list[tuple[float | None, int]] = [(None, 0)]*n
    upper: float | None = None
    lower: float | None = None
    direction = 1
    for i in range(n):
        if atr[i] is None:
            continue
        mid = (candles[i].high + candles[i].low)/2
        candidate_upper = mid + multiplier*atr[i]
        candidate_lower = mid - multiplier*atr[i]
        if upper is None or lower is None:
            upper, lower = candidate_upper, candidate_lower
        else:
            prev_close = candles[i-1].close
            upper = candidate_upper if candidate_upper < upper or prev_close > upper else upper
            lower = candidate_lower if candidate_lower > lower or prev_close < lower else lower
            if candles[i].close > upper:
                direction = 1
            elif candles[i].close < lower:
                direction = -1
        result[i] = ((lower if direction == 1 else upper), direction)
    return result


@dataclass(frozen=True)
class FibonacciPlan:
    side: str
    entry1: float
    entry2: float
    stop: float
    distance_to_stop1: float


def fibonacci_retracement(impulse_low: float, impulse_high: float, side: str,
                         deep_ratio: float = 0.79, second_ratio: float = 0.88,
                         atr: float = 0.0, buffer_atr: float = 1.0) -> FibonacciPlan:
    """Z28. A two-level retracement *geometry*, not a fill/TP decision."""
    positive(impulse_low, impulse_high)
    finite(atr, buffer_atr)
    if impulse_low >= impulse_high or side not in ("long", "short") or not (0 < deep_ratio < second_ratio < 1) or atr < 0 or buffer_atr < 0:
        raise ValueError("invalid impulse geometry")
    amplitude = impulse_high - impulse_low
    if side == "long":
        e1, e2, stop = (impulse_high-deep_ratio*amplitude, impulse_high-second_ratio*amplitude,
                        impulse_low-buffer_atr*atr)
        distance = e1-stop
    else:
        e1, e2, stop = (impulse_low+deep_ratio*amplitude, impulse_low+second_ratio*amplitude,
                        impulse_high+buffer_atr*atr)
        distance = stop-e1
    if distance <= 0 or stop <= 0:
        raise ValueError("invalid stop geometry")
    return FibonacciPlan(side, e1, e2, stop, distance)
