"""Z04, Z29-Z36, Z38: audit instrumentation, not backtest replacement."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from statistics import fmean
from typing import Mapping, Sequence

from .signals import pearson
from .types import finite, positive


@dataclass(frozen=True)
class TraceRow:
    decision_at: int
    symbol: str
    side: str
    entry: float | None
    stop: float | None
    target: float | None
    source: str

    def __post_init__(self) -> None:
        if not self.symbol or self.side not in ("long", "short", "none") or not self.source:
            raise ValueError("invalid trace")
        for value in (self.entry,self.stop,self.target):
            if value is not None:
                positive(value)


def diff_traces(original: Sequence[TraceRow], challenger: Sequence[TraceRow],
                *, price_abs_tolerance: float=1e-8) -> list[dict[str, object]]:
    """Z04/Z33/Z38. Full key union: never silently match unlike signals."""
    if price_abs_tolerance < 0:
        raise ValueError("tolerance")
    def index(rows: Sequence[TraceRow]) -> dict[tuple[int,str],TraceRow]:
        result: dict[tuple[int,str],TraceRow]={}
        for r in rows:
            key=(r.decision_at,r.symbol)
            if key in result:
                raise ValueError("duplicate decision timestamp+symbol")
            result[key]=r
        return result
    a,b=index(original),index(challenger)
    disagreements=[]
    for key in sorted(set(a)|set(b)):
        left,right=a.get(key),b.get(key)
        if left is None or right is None:
            disagreements.append({"key":key,"difference":"MISSING_FROM_ORIGINAL" if left is None else "MISSING_FROM_CHALLENGER"})
            continue
        for field in ("side","entry","stop","target"):
            x,y=getattr(left,field),getattr(right,field)
            different = (x is None) != (y is None) if x is None or y is None else (x != y if field=="side" else abs(x-y)>price_abs_tolerance)
            if different:
                disagreements.append({"key":key,"difference":field,"original":x,"challenger":y})
    return disagreements


@dataclass(frozen=True)
class ObservedTrade:
    trade_id: str
    symbol: str
    strategy: str
    net_pnl_usdt: float
    exit_at: int
    setup: str = "unknown"

    def __post_init__(self) -> None:
        if not self.trade_id or not self.symbol or not self.strategy:
            raise ValueError("trade identifiers")
        finite(self.net_pnl_usdt)


def paired_ablation(baseline: Sequence[ObservedTrade], variant: Sequence[ObservedTrade]) -> dict[str,object]:
    """Z29. Same-ID matched comparisons; added/dropped trades separate.

    A large change of the trade set cannot be called an isolated filter effect.
    """
    def index(rows: Sequence[ObservedTrade])->dict[str,ObservedTrade]:
        d:dict[str,ObservedTrade]={}
        for row in rows:
            if row.trade_id in d:
                raise ValueError("duplicate trade id")
            d[row.trade_id]=row
        return d
    a,b=index(baseline),index(variant)
    common=sorted(set(a)&set(b))
    return {
        "matched":len(common),
        "removed":sorted(set(a)-set(b)),
        "added":sorted(set(b)-set(a)),
        "matched_delta_pnl":sum(b[k].net_pnl_usdt-a[k].net_pnl_usdt for k in common),
        "total_delta_pnl":sum(t.net_pnl_usdt for t in variant)-sum(t.net_pnl_usdt for t in baseline),
    }


def information_coefficient(predictions: Sequence[float], outcomes: Sequence[float]) -> float | None:
    """Z30. Ex-post Pearson IC; caller must supply timestamp-aligned OOS labels."""
    return pearson(predictions,outcomes)


def bonferroni_pvalue(raw_pvalue: float, trial_count: int) -> float:
    """Z30. Explicit multiple-tests correction, not 'deflated Sharpe'."""
    finite(raw_pvalue)
    if not 0 <= raw_pvalue <= 1 or trial_count < 1:
        raise ValueError("p-value/trial count")
    return min(1.0,raw_pvalue*trial_count)


def pnl_attribution(trades: Sequence[ObservedTrade]) -> dict[str,object]:
    """Z31. Concentration + leave-one-symbol-out PnL; no inferential claims."""
    if len({t.trade_id for t in trades})!=len(trades):
        raise ValueError("duplicate trade ids")
    total=sum(t.net_pnl_usdt for t in trades)
    per_symbol: dict[str,float]=defaultdict(float)
    per_setup: dict[str,float]=defaultdict(float)
    for t in trades:
        per_symbol[t.symbol]+=t.net_pnl_usdt
        per_setup[t.setup]+=t.net_pnl_usdt
    gains=sum(max(0,t.net_pnl_usdt) for t in trades)
    top3=sum(sorted((max(0,t.net_pnl_usdt) for t in trades),reverse=True)[:3])
    return {"total":total,"by_symbol":dict(per_symbol),"by_setup":dict(per_setup),
            "without_symbol":{s:total-v for s,v in per_symbol.items()},
            "top3_share_of_gross_wins":top3/gains if gains else None}


@dataclass(frozen=True)
class FeatureAvailability:
    name: str
    observed_at: int
    available_at: int
    source: str
    negative_shift_bars: int = 0
    warmup_required: int = 0
    warmup_available: int = 0


def leakage_violations(features: Sequence[FeatureAvailability], decision_at: int) -> list[str]:
    """Z32. Explicit metadata gate; does not parse arbitrary Python/Pine source."""
    errors=[]
    for f in features:
        if not f.name or not f.source:
            errors.append("INVALID_FEATURE_ID")
        if f.observed_at > decision_at or f.available_at > decision_at or f.available_at < f.observed_at:
            errors.append(f"{f.name}:FUTURE_OR_UNAVAILABLE")
        if f.negative_shift_bars < 0:
            errors.append(f"{f.name}:NEGATIVE_SHIFT")
        if f.warmup_required > f.warmup_available:
            errors.append(f"{f.name}:INSUFFICIENT_WARMUP")
    return errors


def capacity_limit_quantity(quote_volume_usdt: float, price: float, fraction: float) -> float:
    """Z34. Maximum theoretical bar participation, NOT an expected fill."""
    positive(price)
    finite(quote_volume_usdt,fraction)
    if quote_volume_usdt < 0 or not 0 < fraction <= 1:
        raise ValueError("fraction/quote volume")
    return quote_volume_usdt*fraction/price


def session_pnl(trades: Sequence[ObservedTrade]) -> dict[int,dict[str,float]]:
    """Z35. UTC exit-hour bucket. Research report only, not selected 'best hours'."""
    bins:dict[int,list[float]]=defaultdict(list)
    for t in trades:
        hour=datetime.fromtimestamp(t.exit_at,tz=timezone.utc).hour
        bins[hour].append(t.net_pnl_usdt)
    return {h:{"trades":float(len(v)),"net_pnl_usdt":sum(v)} for h,v in sorted(bins.items())}


@dataclass(frozen=True)
class Holding:
    strategy: str
    symbol: str
    start: int
    end: int

    def __post_init__(self) -> None:
        if not self.strategy or not self.symbol or self.end <= self.start:
            raise ValueError("invalid holding interval")


def exposure_report(holdings: Sequence[Holding], start: int, end: int) -> dict[str,object]:
    """Z36. Union of occupied intervals; overlapping trades do not double count."""
    if start >= end:
        raise ValueError("bad observation window")
    intervals=[]
    for p in holdings:
        a,b=max(start,p.start),min(end,p.end)
        if a < b:
            intervals.append((a,b))
    occupied=0
    current:tuple[int,int]|None=None
    for a,b in sorted(intervals):
        if current is None:
            current=(a,b)
        elif a<=current[1]:
            current=(current[0],max(current[1],b))
        else:
            occupied+=current[1]-current[0]
            current=(a,b)
    if current:
        occupied+=current[1]-current[0]
    return {"time_in_market_fraction":occupied/(end-start),
            "trade_count":len(intervals),"occupied_seconds":occupied}
