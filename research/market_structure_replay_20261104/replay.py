"""EMBER Market Structure Replay v0.1 — offline, research-only, causal.

No trading, exchange IO, future labels, or automated parameter search.
CSV input: symbol,time,open,high,low,close,volume (15m UTC open times).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STEP_MS = 15 * 60_000
UTC = timezone.utc


@dataclass(frozen=True)
class Settings:
    accumulation_hours: int = 12
    range_atr_limit: float = 5.0
    range_drift_fraction: float = 0.40
    min_sweep_atr: float = 0.10
    max_sweep_atr: float = 1.25
    sweep_expiry_bars: int = 32
    structure_expiry_bars: int = 24
    min_bos_atr: float = 0.15
    min_fvg_atr: float = 0.15
    max_active: int = 64


@dataclass(frozen=True)
class Bar:
    symbol: str
    t: int  # UTC open time in ms; known only at t + STEP_MS
    o: float
    h: float
    l: float
    c: float
    v: float

    @property
    def known_at(self) -> int:
        return self.t + STEP_MS


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=UTC).isoformat().replace('+00:00', 'Z')


def _time_ms(raw: str) -> int:
    raw = raw.strip()
    if raw.isdigit():
        n = int(raw)
        return n * 1000 if n < 1_000_000_000_000 else n
    dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timestamp must contain explicit UTC timezone')
    return int(dt.astimezone(UTC).timestamp() * 1000)


def read_csv(path: Path) -> tuple[list[Bar], str]:
    """Fail closed on unsorted, duplicated, missing, partial, or invalid 15m candles."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    bars: list[Bar] = []
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        required = {'symbol', 'time', 'open', 'high', 'low', 'close', 'volume'}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError('missing CSV columns: ' + ','.join(sorted(required)))
        for row_number, r in enumerate(reader, 2):
            try:
                b = Bar(r['symbol'].strip().upper(), _time_ms(r['time']),
                        float(r['open']), float(r['high']), float(r['low']),
                        float(r['close']), float(r['volume']))
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f'bad row {row_number}: {exc}') from exc
            if (not b.symbol or b.t % STEP_MS != 0 or
                not all(map(math.isfinite, (b.o, b.h, b.l, b.c, b.v))) or
                min(b.o, b.h, b.l, b.c) <= 0 or b.v < 0 or
                b.h < max(b.o, b.c) or b.l > min(b.o, b.c)):
                raise ValueError(f'invalid OHLCV row {row_number}')
            if bars and (bars[-1].symbol != b.symbol or b.t - bars[-1].t != STEP_MS):
                raise ValueError(f'gap, duplicate, unsorted bar or mixed symbol at row {row_number}')
            bars.append(b)
    if not bars:
        raise ValueError('empty CSV')
    return bars, digest


class ClosedTF:
    """Only publish an HTF bar after its final 15m constituent is known."""
    def __init__(self, size: int):
        self.size = size
        self.key: int | None = None
        self.parts: list[Bar] = []

    def add(self, bar: Bar) -> dict[str, float | int] | None:
        key = bar.t // (self.size * STEP_MS)
        if self.key is not None and key != self.key and self.parts:
            raise ValueError('partial higher-timeframe candle: fail closed')
        self.key = key
        self.parts.append(bar)
        if len(self.parts) != self.size:
            return None
        if self.parts[0].t != key * self.size * STEP_MS:
            raise ValueError('HTF candle began mid-period')
        item: dict[str, float | int] = {
            'opened': self.parts[0].t, 'known_at': bar.known_at,
            'o': self.parts[0].o, 'h': max(x.h for x in self.parts),
            'l': min(x.l for x in self.parts), 'c': bar.c,
            'v': sum(x.v for x in self.parts),
        }
        self.parts = []
        self.key = None
        return item


@dataclass
class Candidate:
    id: str
    born: int
    low: float
    high: float
    atr_h1: float
    phase: str = 'WAIT_SWEEP'
    side: int = 0
    sweep_at: int = 0
    extreme: float = 0.0
    reference: float = 0.0
    pivot_known_at: int = 0
    fvg_found: bool = False


class StructureReplay:
    """State machine per frozen range; emits evidence, never orders."""
    def __init__(self, symbol: str, settings: Settings = Settings()):
        self.symbol = symbol
        self.cfg = settings
        self.tf1 = ClosedTF(4)
        self.tf4 = ClosedTF(16)
        self.h1: deque[dict[str, float | int]] = deque(maxlen=64)
        self.h4: deque[dict[str, float | int]] = deque(maxlen=64)
        self.history: deque[Bar] = deque(maxlen=128)
        self.events: list[dict[str, Any]] = []
        self.active: list[Candidate] = []
        self.latest_pivot_high: tuple[float, int] | None = None
        self.latest_pivot_low: tuple[float, int] | None = None
        self.prev: Bar | None = None
        self.index = 0
        self.serial = 0

    def _event(self, bar: Bar, kind: str, candidate: str, **fields: Any) -> None:
        self.events.append({'symbol': self.symbol, 'known_at': iso(bar.known_at),
                            'event': kind, 'candidate_id': candidate, **fields})

    @staticmethod
    def _atr(hist: deque[dict[str, float | int]], length: int = 14) -> float | None:
        if len(hist) <= length:
            return None
        items = list(hist)
        total = 0.0
        for i in range(len(items) - length, len(items)):
            q, prev = items[i], items[i - 1]
            total += max(float(q['h']) - float(q['l']),
                         abs(float(q['h']) - float(prev['c'])),
                         abs(float(q['l']) - float(prev['c'])))
        return total / length

    def _confirmed_swings(self, b: Bar) -> None:
        # Center is two bars ago; only emit pivot at close of current bar.
        z = list(self.history)
        if len(z) < 5:
            return
        a, p, mid, n, current = z[-5:]
        if mid.h > max(a.h, p.h) and mid.h >= max(n.h, current.h):
            self.latest_pivot_high = (mid.h, current.known_at)
            self._event(b, 'PIVOT_HIGH_CONFIRMED', '-', pivot_price=mid.h,
                        pivot_bar_open=iso(mid.t))
        if mid.l < min(a.l, p.l) and mid.l <= min(n.l, current.l):
            self.latest_pivot_low = (mid.l, current.known_at)
            self._event(b, 'PIVOT_LOW_CONFIRMED', '-', pivot_price=mid.l,
                        pivot_bar_open=iso(mid.t))

    def _make_ranges(self, b: Bar) -> None:
        length = self.cfg.accumulation_hours
        atr = self._atr(self.h1)
        if atr is None or atr <= 0 or len(self.h1) < length:
            return
        window = list(self.h1)[-length:]
        low = min(float(x['l']) for x in window)
        high = max(float(x['h']) for x in window)
        width = high - low
        drift = abs(float(window[-1]['c']) - float(window[0]['o']))
        if width <= 0 or width > self.cfg.range_atr_limit * atr:
            return
        if drift > self.cfg.range_drift_fraction * width:
            return
        for other in self.active:
            if other.phase == 'WAIT_SWEEP':
                overlap = max(0.0, min(high, other.high) - max(low, other.low))
                if overlap / max(width, other.high - other.low) >= 0.8:
                    return
        self.serial += 1
        candidate = Candidate(f'{self.symbol}:{b.known_at}:{self.serial}',
                              b.known_at, low, high, atr)
        self.active.append(candidate)
        self._event(b, 'ACCUMULATION_LOCKED', candidate.id,
                    level_low=low, level_high=high, atr1h=atr)

    def update(self, b: Bar) -> None:
        if b.symbol != self.symbol:
            raise ValueError('cross-symbol contamination')
        if self.prev is not None and b.t - self.prev.t != STEP_MS:
            raise ValueError('bar continuity violated during replay')
        self.index += 1
        self.prev = b
        self.history.append(b)
        self._confirmed_swings(b)
        closed_1h = self.tf1.add(b)
        closed_4h = self.tf4.add(b)
        if closed_1h:
            self.h1.append(closed_1h)
        if closed_4h:
            self.h4.append(closed_4h)
        for p in list(self.active):
            if p.phase == 'WAIT_SWEEP':
                if b.known_at - p.born > self.cfg.sweep_expiry_bars * STEP_MS:
                    self._event(b, 'EXPIRED_NO_SWEEP', p.id)
                    self.active.remove(p)
                    continue
                long_exc = p.low - b.l
                short_exc = b.h - p.high
                long_ok = (self.cfg.min_sweep_atr * p.atr_h1 <= long_exc
                           <= self.cfg.max_sweep_atr * p.atr_h1 and b.c > p.low)
                short_ok = (self.cfg.min_sweep_atr * p.atr_h1 <= short_exc
                            <= self.cfg.max_sweep_atr * p.atr_h1 and b.c < p.high)
                if long_ok == short_ok:
                    continue  # no sweep or ambiguous both sides; no hindsight choice
                d = 1 if long_ok else -1
                pivot = self.latest_pivot_high if d == 1 else self.latest_pivot_low
                if not pivot or pivot[1] > b.known_at:
                    self._event(b, 'REJECT_SWEEP_NO_CONFIRMED_PIVOT', p.id, side=d)
                    self.active.remove(p)
                    continue
                p.side = d
                p.phase = 'WAIT_STRUCTURE'
                p.sweep_at = b.known_at
                p.extreme = b.l if d == 1 else b.h
                p.reference, p.pivot_known_at = pivot
                self._event(b, 'SWEEP_RETURN', p.id, side=d,
                            pivot_known_at=iso(p.pivot_known_at),
                            reference=p.reference, extreme=p.extreme)
                continue
            if b.known_at - p.sweep_at > self.cfg.structure_expiry_bars * STEP_MS:
                self._event(b, 'EXPIRED_NO_STRUCTURE', p.id)
                self.active.remove(p)
                continue
            # Sweep candle cannot confirm itself; past-closed pivot must preexist.
            if b.known_at <= p.sweep_at:
                continue
            d = p.side
            gap = (b.l - self.history[-3].h if d == 1 else
                   self.history[-3].l - b.h) if len(self.history) >= 3 else -1.0
            if gap >= self.cfg.min_fvg_atr * p.atr_h1 and not p.fvg_found:
                p.fvg_found = True
                self._event(b, 'FVG_AFTER_SWEEP', p.id, side=d, fvg_size=gap)
            crossed = b.c > p.reference if d == 1 else b.c < p.reference
            if crossed and abs(b.c - p.reference) >= self.cfg.min_bos_atr * p.atr_h1:
                self._event(b, 'STRUCTURE_BREAK_CONFIRMED', p.id, side=d,
                            reference=p.reference, pivot_known_at=iso(p.pivot_known_at),
                            has_prior_fvg=p.fvg_found)
                self.active.remove(p)
        if closed_1h:
            self._make_ranges(b)
        if len(self.active) > self.cfg.max_active:
            overflow = len(self.active) - self.cfg.max_active
            for p in self.active[:overflow]:
                self._event(b, 'EXPIRED_CAPACITY', p.id)
            del self.active[:overflow]


def replay(bars: list[Bar], settings: Settings = Settings()) -> StructureReplay:
    if not bars:
        raise ValueError('empty history')
    machine = StructureReplay(bars[0].symbol, settings)
    for b in bars:
        machine.update(b)
    return machine


def future_outcomes(bars: list[Bar], events: list[dict[str, Any]],
                    horizons: tuple[int, ...] = (16, 32, 64)) -> list[dict[str, Any]]:
    """Post-hoc diagnostics ONLY. No outcomes ever feed the recognizer."""
    by_close = {iso(b.known_at): i for i, b in enumerate(bars)}
    out = []
    for event in events:
        if event['event'] != 'STRUCTURE_BREAK_CONFIRMED':
            continue
        idx = by_close[event['known_at']]
        entry = bars[idx].c
        direction = int(event['side'])
        for h in horizons:
            # Require full future window; NEVER assign fake terminal results.
            if idx + h >= len(bars):
                continue
            xs = bars[idx + 1: idx + h + 1]
            favorable = max(x.h - entry for x in xs) if direction == 1 else max(entry - x.l for x in xs)
            adverse = max(entry - x.l for x in xs) if direction == 1 else max(x.h - entry for x in xs)
            out.append({'symbol': event['symbol'], 'candidate_id': event['candidate_id'],
                        'event_known_at': event['known_at'], 'horizon_bars_15m': h,
                        'favorable_pct': round(100 * favorable / entry, 6),
                        'adverse_pct': round(100 * adverse / entry, 6),
                        'close_change_signed_pct': round(
                            100 * direction * (bars[idx+h].c - entry) / entry, 6)})
    return out


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description='Offline causal market structure audit, no trades')
    parser.add_argument('--csv', type=Path, nargs='+', required=True, help='15m UTC OHLCV CSV files')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--allow-future-diagnostics', action='store_true',
                        help='Export labeled future outcomes SEPARATELY from signals')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    cfg = Settings()
    config_sha = hashlib.sha256(json.dumps(cfg.__dict__, sort_keys=True).encode()).hexdigest()
    audit = []
    all_events: list[dict[str, Any]] = []
    all_outcomes: list[dict[str, Any]] = []
    for path in args.csv:
        bars, sha = read_csv(path)
        machine = replay(bars, cfg)
        summary = {'symbol': bars[0].symbol, 'source_csv': str(path),
                   'csv_sha256': sha, 'bars': len(bars),
                   'first_open': iso(bars[0].t), 'last_close': iso(bars[-1].known_at),
                   'config_sha256': config_sha, 'events': dict(Counter(
                       e['event'] for e in machine.events)), 'unfinished_candidates': len(machine.active)}
        audit.append(summary)
        all_events.extend(machine.events)
        if args.allow_future_diagnostics:
            all_outcomes.extend(future_outcomes(bars, machine.events))
    # JSONL keeps event-specific fields and timestamps without losing evidence.
    with (args.out / 'events.jsonl').open('w', encoding='utf-8') as f:
        for e in all_events:
            f.write(json.dumps(e, ensure_ascii=False, sort_keys=True) + '\n')
    (args.out / 'source_audit.json').write_text(
        json.dumps({'mode': 'RESEARCH_ONLY_NO_ORDERS', 'source_receipts': audit},
                   ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.allow_future_diagnostics:
        _write_csv(args.out / 'future_outcomes_POSTHOC.csv', all_outcomes,
                   ['symbol', 'candidate_id', 'event_known_at', 'horizon_bars_15m',
                    'favorable_pct', 'adverse_pct', 'close_change_signed_pct'])
    print(json.dumps({'sources': len(audit), 'events': len(all_events),
                      'outcome_rows': len(all_outcomes), 'out': str(args.out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()