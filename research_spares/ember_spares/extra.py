"""Additional executable, isolated components for Z15, Z19, Z25, Z27, Z30.

Independent algorithms: not claimed identical to any author's private strategy.
Inputs must be point-in-time and already closed. No order placement.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from hashlib import sha256
from math import exp, isfinite, log, sqrt
from statistics import fmean
from typing import Mapping, Sequence

from .signals import ModelContract, verify_model_contract
from .structure import ConfirmedPivot, confirmed_pivots
from .types import Candle, finite, positive


@dataclass(frozen=True)
class PricePattern:
    name: str
    side: str
    formation_confirmed_at: int
    triggered_at: int
    trigger_level: float
    reference_level: float


def _recognize(p: Sequence[ConfirmedPivot], highs: bool, count: int, tolerance: float) -> tuple[ConfirmedPivot,...] | None:
    selected = [x for x in p if (x.kind == 'high') == highs]
    if len(selected) < count:
        return None
    chosen = tuple(selected[-count:])
    peak = fmean(x.price for x in chosen)
    if not all(abs(x.price - peak)/peak <= tolerance for x in chosen):
        return None
    return chosen


def detect_patterns(candles: Sequence[Candle], *, decision_at: int, tolerance: float = .012,
                    min_depth: float = .008, left: int = 2, right: int = 2) -> list[PricePattern]:
    """Point-in-time, deterministic detectors: 2/3 tops/bottoms, H&S and triangles.

    A signal appears only when the *last closed candle* confirms a break after
    the final pivot was itself confirmed by right-hand bars. No retroactive
    trigger is assigned to the pivot candle. No guaranteed pattern edge.
    """
    if not (0 < tolerance < .2 and 0 < min_depth < .2):
        raise ValueError('invalid pattern tolerances')
    available = [c for c in candles if c.available_at <= decision_at]
    if len(available) < max(12, 2 * (left+right) + 5):
        return []
    if any(b.open_time <= a.open_time for a, b in zip(available, available[1:])):
        raise ValueError('candles must be sorted, no duplicates')
    pivots = confirmed_pivots(available, left, right, decision_at=decision_at)
    end = available[-1]
    prev = available[-2]
    patterns: list[PricePattern] = []

    def add(name: str, side: str, price: float, level: float, confirmed_at: int) -> None:
        if confirmed_at >= end.available_at:
            return
        broken = (prev.close >= level and end.close < level) if side == 'short' else (prev.close <= level and end.close > level)
        if broken:
            patterns.append(PricePattern(name, side, confirmed_at, end.available_at, level, price))

    for n in (2,3):
        top = _recognize(pivots, True, n, tolerance)
        if top and top[-1].index > top[0].index+1:
            baseline = min(c.low for c in available[top[0].index+1:top[-1].index])
            if (fmean(x.price for x in top) - baseline)/fmean(x.price for x in top) >= min_depth:
                add('double_top' if n == 2 else 'triple_top', 'short', fmean(x.price for x in top), baseline, top[-1].confirmed_at)
        bottom = _recognize(pivots, False, n, tolerance)
        if bottom and bottom[-1].index > bottom[0].index+1:
            baseline = max(c.high for c in available[bottom[0].index+1:bottom[-1].index])
            if (baseline - fmean(x.price for x in bottom))/baseline >= min_depth:
                add('double_bottom' if n == 2 else 'triple_bottom', 'long', fmean(x.price for x in bottom), baseline, bottom[-1].confirmed_at)

    highs = [p for p in pivots if p.kind == 'high']
    lows = [p for p in pivots if p.kind == 'low']
    if len(highs) >= 3:
        a, h, b = highs[-3:]
        if h.price > max(a.price,b.price)*(1+min_depth) and abs(a.price-b.price)/fmean([a.price,b.price]) < tolerance:
            neckline = min(c.low for c in available[a.index+1:b.index])
            add('head_shoulders', 'short', h.price, neckline, b.confirmed_at)
    if len(lows) >= 3:
        a, h, b = lows[-3:]
        if h.price < min(a.price,b.price)*(1-min_depth) and abs(a.price-b.price)/fmean([a.price,b.price]) < tolerance:
            neckline = max(c.high for c in available[a.index+1:b.index])
            add('inverse_head_shoulders', 'long', h.price, neckline, b.confirmed_at)
    if len(highs) >= 2 and len(lows) >= 2:
        h1,h2=highs[-2:]
        l1,l2=lows[-2:]
        confirmed=max(h2.confirmed_at,l2.confirmed_at)
        high_same=abs(h2.price-h1.price)/h1.price<=tolerance
        low_same=abs(l2.price-l1.price)/l1.price<=tolerance
        if high_same and l2.price > l1.price:
            add('ascending_triangle','long',fmean([h1.price,h2.price]),max(h1.price,h2.price),confirmed)
        if low_same and h2.price < h1.price:
            add('descending_triangle','short',fmean([l1.price,l2.price]),min(l1.price,l2.price),confirmed)
    return patterns


def efficiency_weighted_ema(values: Sequence[float], period: int = 9) -> list[float | None]:
    """CMO-modulated variable average used as the basis for OTT variants."""
    if period < 2:
        raise ValueError('period >=2')
    if not all(isfinite(x) for x in values):
        raise ValueError('nonfinite input')
    out: list[float | None]=[None]*len(values)
    if len(values) < period+1:
        return out
    alpha=2/(period+1)
    for i in range(period,len(values)):
        differences=[values[j]-values[j-1] for j in range(i-period+1,i+1)]
        up=sum(max(x,0) for x in differences)
        down=sum(-min(x,0) for x in differences)
        scale=abs(up-down)/(up+down) if up+down else 0
        previous=values[i-1] if out[i-1] is None else out[i-1]
        out[i]=alpha*scale*values[i]+(1-alpha*scale)*previous
    return out


def ott_line(values: Sequence[float], *, period: int = 9, percent: float = 1.4) -> list[float | None]:
    """Independent CMO/VAR + trailing-band OTT family implementation.

    The exact historical `FOttStrategy.py` source's state transition and VAR
    formula must still be compared before attributing results to that strategy.
    This function is a callable indicator, not that author's trade signal.
    """
    if not 0 < percent < 100:
        raise ValueError('invalid OTT percent')
    base=efficiency_weighted_ema(values,period)
    result: list[float | None]=[]
    prev_long: float | None=None
    prev_short: float | None=None
    side=1
    for i,value in enumerate(base):
        if value is None:
            result.append(None);continue
        move=value*percent/100
        current_long=value-move
        current_short=value+move
        if prev_long is not None and i>0 and base[i-1] is not None and base[i-1]>prev_long:
            current_long=max(current_long,prev_long)
        if prev_short is not None and i>0 and base[i-1] is not None and base[i-1]<prev_short:
            current_short=min(current_short,prev_short)
        if prev_short is not None and value>prev_short:
            side=1
        elif prev_long is not None and value<prev_long:
            side=-1
        raw=current_long if side==1 else current_short
        result.append(raw*(1+percent/200 if side==1 else 1-percent/200))
        prev_long,prev_short=current_long,current_short
    return result


@dataclass(frozen=True)
class LinearModel:
    """Deterministic auditable logistic-model artifact, not LightGBM."""
    version: int
    weights: dict[str,float]
    intercept: float


def predict_verified_linear(contract: ModelContract, artifact: bytes, features: Mapping[str,float], *, at: int) -> float:
    """Load signed/hashed JSON only. Never run pickle or executable model bytes.

    External trained LightGBM boosters must use the user's pinned engine, not
    this fallback. Production inference is deliberately not claimed.
    """
    if not verify_model_contract(contract,artifact,features,at):
        raise ValueError('model hash, feature schema, or cutoff violation')
    obj=json.loads(artifact.decode('utf-8'))
    if type(obj) is not dict or obj.get('version') != 1 or not isinstance(obj.get('weights'),dict):
        raise ValueError('not a supported JSON linear model')
    if set(obj['weights'])!=set(contract.feature_names):
        raise ValueError('incorrect model weights')
    weights=obj['weights']
    if not all(isinstance(x,(int,float)) and isfinite(x) for x in weights.values()):
        raise ValueError('invalid coefficients')
    intercept=obj.get('intercept')
    if not isinstance(intercept,(int,float)) or not isfinite(intercept):
        raise ValueError('invalid intercept')
    score=float(intercept)+sum(weights[name]*features[name] for name in contract.feature_names)
    return 1.0/(1.0+exp(-max(-700,min(700,score))))


def check_train_holdout(train_end: int, holdout_start: int, embargo_seconds: int) -> None:
    """Fail closed on chronological overlap of train and untouched holdout."""
    if embargo_seconds<0 or train_end + embargo_seconds >= holdout_start:
        raise ValueError('TRAIN_HOLDOUT_OVERLAP')
