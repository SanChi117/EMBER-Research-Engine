"""Z20-Z27: isolated observable features, NOT profitable or production strategies."""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, log, sqrt
from statistics import fmean, stdev
from typing import Mapping, Sequence

from .types import finite, positive


def _mean_sd(values: Sequence[float]) -> tuple[float, float]:
    if len(values) < 2:
        raise ValueError("at least two samples required")
    if not all(isfinite(x) for x in values):
        raise ValueError("nonfinite history")
    return fmean(values), stdev(values)


def z_score(history: Sequence[float], observation: float) -> float | None:
    """Compute historical-only z. None for constant history (no invented signal)."""
    finite(observation)
    mu, sigma = _mean_sd(history)
    return (observation-mu)/sigma if sigma > 0 else None


@dataclass(frozen=True)
class OUFit:
    persistence: float
    mean: float
    half_life_periods: float
    stationary_sd: float
    sample_size: int


def fit_ou(history: Sequence[float]) -> OUFit | None:
    """Z20. AR(1) OLS on *past funding settlements*.

    OU stationarity 0<b<1 is required. Nonstationary/insufficient windows
    return None rather than making an executable prediction. No fee model.
    """
    if len(history) < 6:
        return None
    if not all(isfinite(x) for x in history):
        raise ValueError("invalid funding history")
    x, y = history[:-1], history[1:]
    mx, my = fmean(x), fmean(y)
    denom = sum((v-mx)**2 for v in x)
    if denom == 0:
        return None
    b = sum((a-mx)*(c-my) for a, c in zip(x, y))/denom
    if not (0 < b < 1):
        return None
    a = my-b*mx
    residuals = [c-(a+b*t) for t,c in zip(x,y)]
    if len(residuals) < 3:
        return None
    sigma = stdev(residuals)/sqrt(1-b*b)
    return OUFit(b, a/(1-b), log(0.5)/log(b), sigma, len(history))


def ou_z_score(params: OUFit, rate: float) -> float | None:
    finite(rate)
    if params.stationary_sd <= 0:
        return None
    return (rate-params.mean)/params.stationary_sd


class OIRegime:
    NEW_LONGS = "NEW_LONGS"
    NEW_SHORTS = "NEW_SHORTS"
    LONG_CLOSING = "LONG_CLOSING"
    SHORT_CLOSING = "SHORT_CLOSING"
    NEUTRAL = "NEUTRAL"


def oi_quadrant(prev_price: float, price: float, prev_oi: float, oi: float,
                taker_buy_ratio: float | None = None) -> str:
    """Z21. Basic price×OI categorisation, NOT proof of motive/position identity."""
    positive(prev_price, price, prev_oi, oi)
    if taker_buy_ratio is not None:
        finite(taker_buy_ratio)
        if not 0 <= taker_buy_ratio <= 1:
            raise ValueError("taker ratio outside [0,1]")
    if price == prev_price or oi == prev_oi:
        return OIRegime.NEUTRAL
    if price > prev_price and oi > prev_oi:
        return OIRegime.NEW_LONGS
    if price < prev_price and oi > prev_oi:
        return OIRegime.NEW_SHORTS
    if price > prev_price and oi < prev_oi:
        return OIRegime.SHORT_CLOSING
    return OIRegime.LONG_CLOSING


def taker_pressure(buy_volume: Sequence[float], total_volume: Sequence[float]) -> float | None:
    """Z22. Volume-weighted fraction of aggressive buys across CLOSED bars."""
    if len(buy_volume) != len(total_volume) or not buy_volume:
        raise ValueError("volume arrays must match and not be empty")
    for buy, total in zip(buy_volume, total_volume):
        finite(buy, total)
        if total < 0 or not (0 <= buy <= total):
            raise ValueError("inconsistent taker volume")
    total = sum(total_volume)
    return sum(buy_volume)/total if total else None


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    if not all(isfinite(x) for x in xs) or not all(isfinite(y) for y in ys):
        raise ValueError("bad inputs")
    mx, my = fmean(xs), fmean(ys)
    xx = sum((a-mx)**2 for a in xs)
    yy = sum((b-my)**2 for b in ys)
    return sum((a-mx)*(b-my) for a,b in zip(xs,ys))/sqrt(xx*yy) if xx > 0 and yy > 0 else None


def lag_correlations(leader_returns: Sequence[float], follower_returns: Sequence[float], max_lag: int) -> dict[int, float | None]:
    """Z23. Historical event study, not a real-time lead-lag trade signal.

    lag=k: follower[t] vs leader[t-k] (k>=0); no future observations
    or smoothing with centred windows. Inputs must share aligned timestamps.
    """
    if len(leader_returns) != len(follower_returns) or max_lag < 0:
        raise ValueError("same-length synchronized returns required")
    return {k: pearson(leader_returns[:-k] if k else leader_returns,
                       follower_returns[k:] if k else follower_returns)
            for k in range(max_lag+1)}


@dataclass(frozen=True)
class AssetRank:
    asset: str
    return_fraction: float
    rank: int


def momentum_ranks(price_histories: Mapping[str, Sequence[float]],
                   lookback: int) -> list[AssetRank]:
    """Z24. Rank historical observed price returns (fixed universe)."""
    if lookback < 1:
        raise ValueError("lookback")
    scored: list[tuple[str,float]] = []
    for asset, prices in price_histories.items():
        if len(prices) <= lookback:
            raise ValueError(f"not enough history: {asset}")
        older, latest = prices[-lookback-1], prices[-1]
        positive(older, latest)
        scored.append((asset,latest/older-1))
    ordered=sorted(scored,key=lambda v:(-v[1],v[0]))
    return [AssetRank(asset,return_fraction,i+1) for i,(asset,return_fraction) in enumerate(ordered)]


@dataclass(frozen=True)
class PairEstimate:
    beta: float
    alpha: float
    residual_z: float | None
    residual_mean: float
    residual_sd: float


def pair_spread(prices_y: Sequence[float], prices_x: Sequence[float],
                latest_y: float, latest_x: float) -> PairEstimate:
    """Z25. OLS spread of two synced historical price streams.

    This is NOT proof of cointegration, stability, or tradable 2-leg fills.
    Latest observation must not be included in training histories.
    """
    if len(prices_y) != len(prices_x) or len(prices_x) < 6:
        raise ValueError("paired history >= 6 required")
    positive(latest_y,latest_x,*prices_y,*prices_x)
    mx,my=fmean(prices_x),fmean(prices_y)
    denom=sum((x-mx)**2 for x in prices_x)
    if denom==0:
        raise ValueError("constant hedge asset")
    beta=sum((x-mx)*(y-my) for x,y in zip(prices_x,prices_y))/denom
    alpha=my-beta*mx
    residuals=[y-(alpha+beta*x) for x,y in zip(prices_x,prices_y)]
    mean,sd=_mean_sd(residuals)
    current=latest_y-(alpha+beta*latest_x)
    return PairEstimate(beta,alpha,(current-mean)/sd if sd else None,mean,sd)


def mean_dislocation(prices: Sequence[float], latest: float, *, threshold: float = -0.30) -> bool:
    """Z26. Latest vs historical SMA, excluding latest from baseline."""
    if not prices or threshold >= 0 or threshold <= -1:
        raise ValueError("bad dislocation input")
    positive(latest,*prices)
    reference=fmean(prices)
    return latest/reference-1 < threshold


@dataclass(frozen=True)
class ModelContract:
    """Z27. Artifact-only offline gate; never loads pickle or executes a model."""
    model_name: str
    artifact_sha256: str
    trained_until: int
    feature_names: tuple[str,...]
    min_probability: float

    def __post_init__(self) -> None:
        if not self.model_name or len(self.artifact_sha256)!=64 or not all(ch in '0123456789abcdef' for ch in self.artifact_sha256.lower()):
            raise ValueError("invalid model metadata")
        if self.trained_until < 0 or not self.feature_names or len(set(self.feature_names))!=len(self.feature_names):
            raise ValueError("invalid schema")
        if not 0 < self.min_probability < 1:
            raise ValueError("threshold")


def verify_model_contract(contract: ModelContract, artifact: bytes, available_features: Mapping[str,float], at: int) -> bool:
    """Do not execute artifact; verify immutable bytes, feature parity and cutoff."""
    from hashlib import sha256
    if at <= contract.trained_until:
        return False
    if sha256(artifact).hexdigest().lower() != contract.artifact_sha256.lower():
        return False
    if set(available_features) != set(contract.feature_names):
        return False
    return all(isfinite(value) for value in available_features.values())
