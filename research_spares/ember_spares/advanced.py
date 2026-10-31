"""Concrete missing functionality for EMBER spares (offline-only research).

All functions are pure deterministic computations on caller-supplied, point-in-time
market evidence. None places orders or converts unknown executions into fills.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from math import erf, exp, isfinite, log, sqrt
from statistics import fmean, stdev
from typing import Any, Mapping, Sequence

from .types import Candle, Evidence, finite, positive
from .accounting import CashEvent, Exposure, IsolatedMargin, MarginTier, Position, maintenance_required, margin_state, replay_cash_events, update_risk, RiskState
from .market import Book, OrderSnapshot, OrderState, transition_order, maker_fill_certainty, QueueEvidence, classify_bracket_bar
from .signals import pearson, pair_spread, z_score, momentum_ranks, oi_quadrant, taker_pressure, fit_ou, ou_z_score
from .structure import Zone, advance_zone, confirmed_pivots, fibonacci_retracement
from .research import TraceRow, diff_traces, ObservedTrade, paired_ablation, pnl_attribution, session_pnl
from .extra import detect_patterns, ott_line, check_train_holdout


class UnavailableEvidence(ValueError):
    """A non-fabricable source is needed for the requested calculation."""


def closed(candles: Sequence[Candle], at: int, min_bars: int = 1) -> list[Candle]:
    """Select bars already received, without silently treating future data as current."""
    if at < 0:
        raise ValueError('invalid decision timestamp')
    out = [c for c in candles if c.available_at <= at]
    if len(out) < min_bars:
        raise UnavailableEvidence('insufficient CLOSED candles available at decision time')
    if any(a.open_time >= b.open_time or a.close_time > b.open_time for a,b in zip(out,out[1:])):
        raise ValueError('unsorted or overlapping candles')
    return out


def historical_signal_frame(candles: Sequence[Candle], funding: Sequence[Evidence], oi: Sequence[Evidence], *,
                            decision_at: int, max_age_seconds: int) -> dict[str,Any]:
    """Z01: as-of evidence, reject source age rather than forward-fill indefinitely."""
    from .market import asof_evidence
    last=closed(candles,decision_at)[-1]
    f=asof_evidence(funding,decision_at,max_age_seconds)
    o=asof_evidence(oi,decision_at,max_age_seconds)
    return {'bar_close_at':last.close_time,'bar_available_at':last.available_at,
            'close':last.close,'funding':None if f is None else f.value,
            'oi':None if o is None else o.value,
            'funding_available_at':None if f is None else f.available_at,
            'oi_available_at':None if o is None else o.available_at,
            'valid_for_oi_funding_signal':f is not None and o is not None}


def liquidation_boundary(position: IsolatedMargin, tiers: Sequence[MarginTier], *, minimum_price: float,
                         maximum_price: float, tolerance: float = 1e-7) -> dict[str,Any]:
    """Z02: solve isolated maintenance equality using supplied tier rules, if bracketed.

    Binance exchange liquidations are more complex and may add bankruptcy
    premiums, fee reserves, funding and changing tiers; caller must supply
    those parameters. Returns a modeled boundary, NEVER an exchange order level.
    """
    from dataclasses import replace
    positive(minimum_price,maximum_price,tolerance)
    if minimum_price >= maximum_price:
        raise ValueError('bad price bracket')
    def gap(price: float) -> float:
        s=margin_state(replace(position,mark_price=price),tiers)
        return float(s['equity'])-float(s['maintenance'])
    low,high=minimum_price,maximum_price
    gl,gh=gap(low),gap(high)
    if gl==0:
        boundary=low
    elif gh==0:
        boundary=high
    elif gl*gh>0:
        return {'found':False,'modeled_mark':None,'note':'no maintenance boundary in supplied bracket'}
    else:
        for _ in range(100):
            mid=(low+high)*.5
            gm=gap(mid)
            if abs(gm)<tolerance or (high-low)<tolerance:
                low=high=mid
                break
            if gm*gl>0:
                low,gl=mid,gm
            else:
                high,gh=mid,gm
        boundary=(low+high)*.5
    return {'found':True,'modeled_mark':boundary,'note':'model only; not Binance exchange liquidation price'}


def orderbook_depth(bids: Sequence[tuple[float,float]], asks: Sequence[tuple[float,float]], *, levels: int = 5) -> dict[str,float]:
    """Z03: depth imbalance/microprice from strictly sorted L2 bids/asks."""
    if levels < 1 or not bids or not asks:
        raise ValueError('nonempty book and levels required')
    if any(p<=0 or q<=0 or not isfinite(p) or not isfinite(q) for p,q in [*bids,*asks]):
        raise ValueError('bad level')
    if any(a[0] <= b[0] for a,b in zip(bids,bids[1:])) or any(a[0] >= b[0] for a,b in zip(asks,asks[1:])):
        raise ValueError('book levels must be descending bids and ascending asks')
    if bids[0][0]>=asks[0][0]:
        raise ValueError('crossed book')
    bid_qty=sum(q for _,q in bids[:levels]);ask_qty=sum(q for _,q in asks[:levels])
    bbo=Book(bids[0][0],asks[0][0],bids[0][1],asks[0][1],0,0)
    from .market import microprice
    return {'depth_imbalance':(bid_qty-ask_qty)/(bid_qty+ask_qty),
            'microprice':microprice(bbo),'mid':(bids[0][0]+asks[0][0])/2,
            'spread':asks[0][0]-bids[0][0]}


def quote_fill(side: str, quantity: float, quote: Book, *, max_fraction_of_top_size: float = 1.) -> dict[str,float|bool]:
    """Z03/Z34: top-of-book marketable quantity upper bound (not a confirmed fill)."""
    positive(quantity,max_fraction_of_top_size)
    if max_fraction_of_top_size>1 or side not in ('buy','sell'):
        raise ValueError('invalid side or depth fraction')
    price = quote.ask if side=='buy' else quote.bid
    available = (quote.ask_quantity if side=='buy' else quote.bid_quantity)*max_fraction_of_top_size
    return {'limit_quantity':min(quantity,available),'reference_price':price,
            'fully_covered_top_book':quantity<=available,'confirmed_fill':False}


def full_trace_parity(original: Sequence[TraceRow], candidate: Sequence[TraceRow], *,
                     tolerance: float = 1e-8) -> dict[str,Any]:
    """Z04/Z33/Z38: deterministic signal parity contract, reject on ANY difference."""
    diffs=diff_traces(original,candidate,price_abs_tolerance=tolerance)
    return {'matches':not diffs,'original_rows':len(original),'candidate_rows':len(candidate),
            'differences':diffs}


def two_leg_cash_ledger(legs: Mapping[str, Sequence[CashEvent]], sides: Mapping[str,str],
                        marks: Mapping[str,float], *, fee_on_close_rate: float = 0.0) -> dict[str, Any]:
    """Z05/Z06: two-leg asynchronous fills with realized+unrealized cash, per-leg mark.

    If one leg has not filled, the imbalance remains explicitly visible.
    """
    if len(legs)!=2 or set(legs)!=set(sides) or set(legs)!=set(marks):
        raise ValueError('exactly two tagged legs and marks required')
    if not (0<=fee_on_close_rate<1):
        raise ValueError('invalid fee')
    details={}; total=0.; signed_notional=0.
    for symbol,events in legs.items():
        positive(marks[symbol]);p=replay_cash_events(symbol,sides[symbol],events)
        sign=1 if p.side=='long' else -1
        notional=sign*p.quantity*marks[symbol]
        unrealized=sign*p.quantity*(marks[symbol]-p.avg_entry)
        close_fee=abs(notional)*fee_on_close_rate
        net=p.realised_pnl+unrealized-p.paid_fees-p.paid_funding-close_fee
        details[symbol]={'quantity':p.quantity,'avg_entry':p.avg_entry,'realised':p.realised_pnl,
                         'unrealised':unrealized,'fees':p.paid_fees,'funding':p.paid_funding,
                         'estimated_exit_fee':close_fee,'net_mark_to_market':net}
        total+=net;signed_notional+=notional
    return {'legs':details,'net_mark_to_market_usdt':total,'signed_notional_usdt':signed_notional,
            'legs_hedged':abs(signed_notional)<1e-9}


def correlated_risk_gate(existing: Sequence[Exposure], new: Exposure, *,
                         max_stop_risk: float, max_gross_notional: float,
                         max_strategy_stop_risk: float, max_symbol_notional: float) -> dict[str,Any]:
    """Z07: conservative risk budget across engines, symbols and portfolio.

    No same-symbol long/short netting; one liquidating hedge can break another.
    """
    positive(max_stop_risk,max_gross_notional,max_strategy_stop_risk,max_symbol_notional)
    all_exposures=[*existing,new]
    checks={
        'stop_risk':sum(e.stop_risk_usdt for e in all_exposures)<=max_stop_risk,
        'gross_notional':sum(e.notional_usdt for e in all_exposures)<=max_gross_notional,
        'strategy_stop_risk':sum(e.stop_risk_usdt for e in all_exposures if e.strategy==new.strategy)<=max_strategy_stop_risk,
        'symbol_notional':sum(e.notional_usdt for e in all_exposures if e.symbol==new.symbol)<=max_symbol_notional,
    }
    return {'allow':all(checks.values()),'checks':checks}


def portfolio_replay(orders: Mapping[str,OrderSnapshot], events: Sequence[tuple[int,str,str,float]]) -> dict[str,OrderSnapshot]:
    """Z10: replay asynchronous per-order event streams in receive-time order."""
    state=dict(orders)
    if any(a[0]>b[0] for a,b in zip(events,events[1:])):
        raise ValueError('event queue not ordered')
    for at,oid,action,qty in events:
        if oid not in state:
            raise ValueError('unknown order id')
        state[oid]=transition_order(state[oid],action,at,qty)
    return state


def progress_zone_history(zone: Zone, candles: Sequence[Candle], *, decision_at: int) -> Zone:
    """Z11: stateful zone re-evaluation using only closed candles."""
    last=zone
    for candle in closed(candles,decision_at):
        if candle.available_at>zone.born_at and candle.available_at>last.last_updated_at:
            last=advance_zone(last,candle)
    return last


def compression_breakout(candles: Sequence[Candle], *, decision_at: int, lookback: int=20,
                         max_range_atr: float=2.0, volume_multiplier: float=1.3) -> dict[str,Any]:
    """Z14: real compression detector + closed-candle breakout, no oracle flags."""
    bars=closed(candles,decision_at,lookback+2)
    if lookback<5 or max_range_atr<=0 or volume_multiplier<=0:
        raise ValueError('invalid compression parameters')
    background=bars[-lookback-1:-1]
    widths=[b.high-b.low for b in background]
    avg_range=fmean(widths)
    range_high=max(b.high for b in background)
    range_low=min(b.low for b in background)
    avg_vol=fmean(b.volume for b in background)
    # A compressed range must be relatively small vs summed bar true range;
    # this is a condition, not a profitable entry signal.
    range_to_tr=(range_high-range_low)/avg_range if avg_range>0 else float('inf')
    squeezed=range_to_tr <= max_range_atr
    last=bars[-1]
    direction='long' if last.close>range_high else 'short' if last.close<range_low else 'none'
    vol_ok=last.volume>=avg_vol*volume_multiplier if avg_vol>0 else False
    return {'compressed':squeezed,'direction':direction if squeezed and vol_ok else 'none',
            'range_high':range_high,'range_low':range_low,'range_to_mean_bar_range':range_to_tr,
            'volume_confirmed':vol_ok,'trigger_time':last.available_at}


def failure_exit(candles: Sequence[Candle], *, decision_at:int, level:float,
                 breakout_side:str, required_confirmation:int=1) -> dict[str,Any]:
    """Z17: invalidation only after n closed acceptance bars on wrong side."""
    positive(level)
    if breakout_side not in ('long','short') or required_confirmation<1:
        raise ValueError('side/count')
    bars=closed(candles,decision_at,required_confirmation+1)
    tail=bars[-required_confirmation:]
    bad=all(b.close<level for b in tail) if breakout_side=='long' else all(b.close>level for b in tail)
    return {'invalidation':bad,'confirmed_at':tail[-1].available_at if bad else None,
            'bars_confirmed':required_confirmation if bad else 0}


def funding_pressure(funding: Sequence[Evidence], *, decision_at:int, lookback:int=30,
                      min_count:int=8) -> dict[str,Any]:
    """Z20: funding settlement z + OU fit on *prior known* events only."""
    if lookback<min_count or min_count<6:
        raise ValueError('insufficient history spec')
    available=sorted((e for e in funding if e.available_at<=decision_at and e.event_time<=decision_at),key=lambda e:(e.event_time,e.available_at))
    if len(available)<min_count+1:
        raise UnavailableEvidence('not enough prior funding settlements')
    past=[e.value for e in available[-lookback-1:-1]]
    obs=available[-1].value
    fit=fit_ou(past)
    return {'current':obs,'z':z_score(past,obs),'ou_z':ou_z_score(fit,obs) if fit else None,
            'half_life_events':fit.half_life_periods if fit else None,'sample_count':len(past),
            'available_at':available[-1].available_at}


def oi_signal(prices: Sequence[Evidence], oi: Sequence[Evidence], taker_ratio:float|None, *,
              decision_at:int, max_age:int=900) -> dict[str,Any]:
    """Z21: align price and OI *publication time*, no borrowing later OI for earlier bar."""
    from .market import asof_evidence
    valid_prices=sorted((p for p in prices if p.available_at<=decision_at),key=lambda p:p.available_at)
    if len(valid_prices)<2:
        raise UnavailableEvidence('need two known price observations')
    curr=valid_prices[-1];prev=valid_prices[-2]
    # Historical comparators become usable only at decision_at. They must
    # describe their respective price bars and be published no later than the
    # current decision. Do NOT pretend they existed at the earlier price close.
    visible=[e for e in oi if e.available_at<=decision_at and e.event_time<=decision_at]
    def match(price):
        choices=[e for e in visible if e.event_time<=price.event_time and price.event_time-e.event_time<=max_age]
        return max(choices,key=lambda e:(e.event_time,e.available_at),default=None)
    oi_now=match(curr)
    oi_prev=match(prev)
    if oi_now is None or oi_prev is None or oi_now is oi_prev:
        raise UnavailableEvidence('need two distinct OI observations aligned to each price bar, known at decision time')
    return {'quadrant':oi_quadrant(prev.value,curr.value,oi_prev.value,oi_now.value,taker_ratio),
            'price_from':prev.value,'price_to':curr.value,'oi_from':oi_prev.value,'oi_to':oi_now.value,
            'oi_available_at':oi_now.available_at}


def taker_series(candles: Sequence[Candle], buy_volumes: Sequence[float], *,
                 decision_at:int, window:int=5) -> dict[str,Any]:
    """Z22: rolling taker ratio, rejects mismatched aggregated bar time."""
    bars=closed(candles,decision_at,window)
    if len(buy_volumes)!=len(candles) or window<1:
        raise ValueError('taker volume must align one-for-one with candle time')
    # Candle indices may not be a prefix when the caller mixed future rows.
    # Select the exact same market timestamps for numerator and denominator.
    visible_indices=[i for i,c in enumerate(candles) if c.available_at<=decision_at]
    buy=[buy_volumes[i] for i in visible_indices[-window:]]
    total=[b.volume for b in bars[-window:]]
    ratio=taker_pressure(buy,total)
    return {'buy_ratio':ratio,'sell_ratio':None if ratio is None else 1-ratio,
            'n':window,'decision_at':decision_at}


def basket_orders(histories: Mapping[str,Sequence[float]], *, lookback:int=14, top:int=3,
                  equity:float=1000., exposure_fraction:float=.6,
                  maximum_symbol_weight:float=.25) -> dict[str,Any]:
    """Z24: point-in-time deterministic basket weights, caps and no leverage."""
    positive(equity)
    if top<1 or not 0<exposure_fraction<=1 or not 0<maximum_symbol_weight<=1:
        raise ValueError('invalid allocation')
    ranked=momentum_ranks(histories,lookback)
    take=ranked[:top]
    weight=min(maximum_symbol_weight,exposure_fraction/len(take))
    return {'entries':[{ 'symbol':r.asset,'weight':weight,'usdt_target':weight*equity,
                         'return_fraction':r.return_fraction} for r in take],
            'unallocated_weight':1-weight*len(take), 'gross_weight':weight*len(take)}


def pair_diagnostics(prices_y:Sequence[float],prices_x:Sequence[float],latest_y:float,latest_x:float,
                     *,required_half_life:float|None=None) -> dict[str,Any]:
    """Z25: estimate hedge + residual AR(1) stationarity screen, not cointegration proof."""
    est=pair_spread(prices_y,prices_x,latest_y,latest_x)
    past=[y-est.alpha-est.beta*x for x,y in zip(prices_x,prices_y)]
    fit=fit_ou(past)
    halflife=fit.half_life_periods if fit else None
    return {'hedge_ratio':est.beta,'intercept':est.alpha,'z':est.residual_z,
            'residual_half_life':halflife,'ar1_stationary':fit is not None,
            'eligible_for_further_tests':fit is not None and (required_half_life is None or halflife<=required_half_life)}


def dislocation_plan(prices:Sequence[float],latest:float,rsi:float, *,
                     sma_threshold:float=-.30,rsi_threshold:float=30.,max_hold_bars:int=48)->dict[str,Any]:
    """Z26: full RSI+SMA dislocation rule and holding horizon, no inherited -99% stop."""
    positive(latest,*prices)
    finite(rsi)
    if not prices or not -1<sma_threshold<0 or not 0<=rsi_threshold<=100 or max_hold_bars<1:
        raise ValueError('bad dislocation rule')
    sma=fmean(prices)
    magnitude=latest/sma-1
    return {'eligible':rsi<=rsi_threshold and magnitude<=sma_threshold,
            'sma':sma,'deviation_fraction':magnitude,'max_hold_bars':max_hold_bars}


def dual_entry_risk(impulse_low:float,impulse_high:float,side:str,atr:float,
                    *,risk_budget_usdt:float, fraction_first:float=.5, deep_ratio:float=.79, second_ratio:float=.88)->dict[str,Any]:
    """Z28: 2 fills with total worst-case stop risk <= requested fixed budget."""
    positive(risk_budget_usdt,atr)
    if not 0<=fraction_first<=1:
        raise ValueError('bad first-order risk fraction')
    p=fibonacci_retracement(impulse_low,impulse_high,side,deep_ratio,second_ratio,atr)
    r1=abs(p.entry1-p.stop);r2=abs(p.entry2-p.stop)
    if r1<=0 or r2<=0:
        raise ValueError('stop behind entry geometry')
    q1=risk_budget_usdt*fraction_first/r1;q2=risk_budget_usdt*(1-fraction_first)/r2
    return {'entry1':p.entry1,'entry2':p.entry2,'stop':p.stop,'quantity1':q1,'quantity2':q2,
            'worst_case_loss_usdt':q1*r1+q2*r2}


def bootstrap_mean_ci(values:Sequence[float], *, block_size:int=5,
                      replicates:int=1000,seed:int=17)->dict[str,float]:
    """Z30: reproducible moving-block bootstrap mean CI for serial dependence.

    Resamples groups, not individual returns; not deflated Sharpe / proof of edge.
    """
    from random import Random
    import math
    if not values or not all(isfinite(x) for x in values) or block_size<1 or replicates<100 or block_size>len(values):
        raise ValueError('bad bootstrap inputs')
    rng=Random(seed);n=len(values)
    means=[]
    for _ in range(replicates):
        sample=[]
        while len(sample)<n:
            i=rng.randrange(n-block_size+1)
            sample.extend(values[i:i+block_size])
        means.append(fmean(sample[:n]))
    means.sort()
    return {'sample_mean':fmean(values),'lower_95':means[int(replicates*.025)],
            'upper_95':means[min(replicates-1,int(replicates*.975))], 'replicates':float(replicates)}


def review_source_for_lookahead(code:str, *, language:str='python')->list[str]:
    """Z32: conservative static heuristic scanner, not a full source verifier."""
    import re
    if language not in ('python','pine'):
        raise ValueError('unsupported source language')
    patterns=(
        (r'\.shift\(\s*-\d+', 'NEGATIVE_SHIFT'),
        (r'np\.gradient\s*\(', 'GRADIENT_REQUIRES_EDGE_AUDIT'),
        (r'argrelextrema\s*\(', 'EXTREMA_REQUIRES_CONFIRMATION'),
        (r'lookahead\s*=\s*barmerge\.lookahead_on', 'PINE_LOOKAHEAD_ON'),
        (r'center\s*=\s*True', 'CENTERED_WINDOW'),
        (r'(?<!\w)future\s*\[', 'FUTURE_FEATURE_REFERENCE'),
    )
    return [tag for pattern,tag in patterns if re.search(pattern,code)]


def volume_impact_envelope(order_quantity:float,price:float,quote_volume:float,spread_fraction:float,
                           *,participation_limit:float=.05, square_root_coefficient:float=.15)->dict[str,Any]:
    """Z34: explicit scenario market-impact *assumption*, not observed execution."""
    positive(order_quantity,price,quote_volume)
    if not 0<=spread_fraction<1 or not 0<participation_limit<=1 or square_root_coefficient<0:
        raise ValueError('invalid impact assumptions')
    fraction=order_quantity*price/quote_volume
    return {'participation':fraction,'capacity_ok':fraction<=participation_limit,
            'scenario_cost_fraction':spread_fraction/2+square_root_coefficient*sqrt(fraction),
            'is_scenario_not_observed':True}


def attribution_by_regime(trades:Sequence[ObservedTrade], regimes:Mapping[str,str])->dict[str,Any]:
    """Z31: segment known trades by fixed signal-time regime labels."""
    if set(t.trade_id for t in trades)!=set(regimes):
        raise ValueError('missing or extra regime labels')
    buckets=defaultdict(list)
    for t in trades:
        buckets[regimes[t.trade_id]].append(t)
    return {name:pnl_attribution(rows) for name,rows in buckets.items()}


def session_preregistered(trades:Sequence[ObservedTrade], allowed_utc_hours:Sequence[int])->dict[str,Any]:
    """Z35: fixed hours provided before testing; never mine best hour ex post."""
    from datetime import datetime,timezone
    hours=set(allowed_utc_hours)
    if not hours or any(not isinstance(h,int) or not 0<=h<24 for h in hours):
        raise ValueError('invalid session preregistration')
    included=[t for t in trades if datetime.fromtimestamp(t.exit_at,tz=timezone.utc).hour in hours]
    excluded=[t for t in trades if t not in included]
    return {'included_trades':len(included),'excluded_trades':len(excluded),
            'included_net_usdt':sum(t.net_pnl_usdt for t in included),
            'excluded_net_usdt':sum(t.net_pnl_usdt for t in excluded)}


def risk_with_addons(fills:Sequence[CashEvent], *, symbol:str, side:str,stop:float,
                     max_stop_loss:float,mark:float,collateral:float,tiers:Sequence[MarginTier])->dict[str,Any]:
    """Z37: actual changing quantity, live stop risk and maintenance from events."""
    positive(stop,max_stop_loss,mark,collateral)
    p=replay_cash_events(symbol,side,fills)
    stoprisk=p.quantity*max(0,p.avg_entry-stop) if side=='long' else p.quantity*max(0,stop-p.avg_entry)
    if p.quantity:
        m=margin_state(IsolatedMargin(side,p.quantity,p.avg_entry,mark,collateral,p.paid_funding),tiers)
    else:
        m={'equity':collateral,'maintenance':0.,'below_maintenance':False,'notional':0.}
    return {'quantity':p.quantity,'average_entry':p.avg_entry,'stop_risk_usdt':stoprisk,
            'risk_budget_ok':stoprisk<=max_stop_loss,'margin':m}
