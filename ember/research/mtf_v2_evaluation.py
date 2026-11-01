"""Conservative MTF research proxy and same-price-source V1 benchmark.

NOT execution-grade: no mark price/funding, spreads by time, queue, margin,
liquidation, portfolio cash ledger or overlapping risk accounting.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Sequence

from ember.research.initiative_transition import detect as detect_v1
from ember.research.initiative_transition import simulate as simulate_v1
from ember.research.mtf_v2_bars import H4, M15, FlowBar, aggregate
from ember.research.mtf_v2_signals import Entry


@dataclass(frozen=True)
class Outcome:
    symbol: str
    side: str
    model: str
    decision_at: int
    entry_at: int | None
    entry: float | None
    exit_at: int | None
    exit_price: float | None
    reason: str
    gross_pct: float | None
    base_pct: float | None
    stress_pct: float | None

    def as_dict(self) -> dict:
        return asdict(self)


def simulate(
    entries: Sequence[Entry], bars: Sequence[FlowBar],
    *, max_bars: int = 192, base_cost: float = .002, stress_cost: float = .0035,
) -> list[Outcome]:
    """Next 15m OPEN; pessimistic SL first if intra-bar order unknown."""
    index = {bar.ts: i for i, bar in enumerate(bars)}
    results: list[Outcome] = []
    for d in entries:
        i = index.get(d.eligible_entry_at)
        if i is None or i + max_bars > len(bars):
            results.append(Outcome(d.symbol,d.side,d.model,d.eligible_entry_at,None,None,None,None,"INCOMPLETE",None,None,None))
            continue
        opened = bars[i].open
        sign = 1 if d.side == "long" else -1
        risk = sign * (opened - d.stop)
        room = sign * (d.target - opened)
        if risk <= 0 or room <= 0 or room / risk < 1.25:
            results.append(Outcome(d.symbol,d.side,d.model,d.eligible_entry_at,bars[i].ts,opened,None,None,"GAP_INVALIDATED",None,None,None))
            continue
        exit_price = exit_at = None
        reason = "INCOMPLETE"
        for j in range(i,i + max_bars):
            bar = bars[j]
            if j > i and sign * (bar.open - d.stop) <= 0:
                exit_price, exit_at, reason = bar.open, bar.ts, "GAP_STOP"
                break
            stop = bar.low <= d.stop if sign == 1 else bar.high >= d.stop
            target = bar.high >= d.target if sign == 1 else bar.low <= d.target
            if stop:
                exit_price, exit_at, reason = d.stop, bar.ts + M15, "BOTH_STOP_FIRST" if target else "STOP"
                break
            if target:
                exit_price, exit_at, reason = d.target, bar.ts + M15, "STRUCTURE"
                break
            if j == i + max_bars - 1:
                exit_price, exit_at, reason = bar.close, bar.ts + M15, "TIME"
        assert exit_price is not None and exit_at is not None
        gross = sign * (exit_price - opened) / opened * 100
        results.append(Outcome(
            d.symbol,d.side,d.model,d.eligible_entry_at,bars[i].ts,opened,
            exit_at,exit_price,reason,gross,
            gross - base_cost * 100, gross - stress_cost * 100,
        ))
    return results


def v1_same_data(symbol: str, bars: Sequence[FlowBar]) -> list[Outcome]:
    """Old 4H V1 on the exact same 15m-origin price dataset, no independent OOS."""
    four = [bar.as_v1() for bar in aggregate(bars, H4)]
    candidates, _ = detect_v1(symbol, four)
    results = simulate_v1(candidates, four)
    return [
        Outcome(
            symbol, d.side, "V1_4H_ONLY", d.decision_at,
            x.entry_at, x.entry, x.exit_at, x.exit,
            x.exit_reason, x.gross_pct, x.base_pct, x.stress_pct,
        )
        for d, x in zip(candidates, results)
    ]


def summarize(results: Sequence[Outcome]) -> dict:
    resolved = [x for x in results if x.stress_pct is not None]
    n = len(resolved)
    ordered = sorted(x.stress_pct for x in resolved)
    return {
        "n_signals": len(results),
        "n_resolved": n,
        "n_censored": len(results)-n,
        "wins_after_stress": sum(x.stress_pct > 0 for x in resolved),
        "win_rate_after_stress": sum(x.stress_pct > 0 for x in resolved)/n if n else None,
        "mean_gross_pct_notional": sum(x.gross_pct for x in resolved)/n if n else None,
        "mean_base_pct_notional": sum(x.base_pct for x in resolved)/n if n else None,
        "mean_stress_pct_notional": sum(x.stress_pct for x in resolved)/n if n else None,
        "median_stress_pct_notional": ordered[n // 2] if n else None,
        "worst_stress_pct_notional": ordered[0] if n else None,
        "exits": dict(sorted(Counter(x.reason for x in results).items())),
        "notional_sum_stress_pct_points_NOT_PORTFOLIO_RETURN": sum(x.stress_pct for x in resolved),
    }
