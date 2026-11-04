"""Independent as-of 1H/4H swing comparison for MSR-01 15m BOS events.
Research-only diagnostic: passing a HTF pivot is NOT a definition of true BOS.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from replay import STEP_MS, iso, read_csv, replay


def last_confirmed_swings(bars, factor):
    """Map each 15m close timestamp to last five-bar 2-left/2-right HTF pivot."""
    formed = []
    history = []
    high = low = None
    snapshots = {}
    for bar in bars:
        formed.append(bar)
        if len(formed) == factor:
            if formed[0].t % (factor * STEP_MS):
                raise ValueError('unaligned HTF data')
            q = {
                'high': max(b.h for b in formed),
                'low': min(b.l for b in formed),
            }
            history.append(q)
            formed = []
            if len(history) >= 5:
                a, p, center, n, current = history[-5:]
                if (center['high'] > max(a['high'], p['high'])
                        and center['high'] >= max(n['high'], current['high'])):
                    high = center['high']
                if (center['low'] < min(a['low'], p['low'])
                        and center['low'] <= min(n['low'], current['low'])):
                    low = center['low']
        snapshots[iso(bar.known_at)] = (high, low)
    return snapshots


def audit(paths):
    totals = Counter()
    by_symbol = []
    for source in sorted(paths):
        bars, sha = read_csv(source)
        sym = bars[0].symbol
        events = replay(bars).events
        h1 = last_confirmed_swings(bars, 4)
        h4 = last_confirmed_swings(bars, 16)
        close_by_time = {iso(bar.known_at): bar.c for bar in bars}
        count = Counter()
        for e in events:
            if e['event'] != 'STRUCTURE_BREAK_CONFIRMED':
                continue
            count['bos'] += 1
            t, side = e['known_at'], e['side']
            close = close_by_time[t]
            ref1 = h1[t][0 if side == 1 else 1]
            ref4 = h4[t][0 if side == 1 else 1]
            passed1 = ref1 is not None and (close > ref1 if side == 1 else close < ref1)
            passed4 = ref4 is not None and (close > ref4 if side == 1 else close < ref4)
            if passed1:
                count['passed_last_confirmed_1h_pivot'] += 1
            if passed4:
                count['passed_last_confirmed_4h_pivot'] += 1
            if ref4 is None:
                count['no_confirmed_4h_pivot'] += 1
            if passed1 and passed4:
                count['passed_both_1h_4h'] += 1
        a = {e['candidate_id']: e for e in events
             if e['event'] == 'ACCUMULATION_LOCKED'}
        for e in events:
            if e['event'] == 'STRUCTURE_BREAK_CONFIRMED':
                p = a.get(e['candidate_id'])
                if p and p['level_low'] <= e['reference'] <= p['level_high']:
                    count['broken_15m_pivot_inside_locked_range'] += 1
        totals.update(count)
        by_symbol.append({'symbol': sym, 'source_csv_sha256': sha, **dict(count)})
    return {
        'status': 'CAUSAL_HTF_GEOMETRY_PROXY_NOT_EXPERT_TRUTH',
        'total': dict(totals),
        'by_symbol': by_symbol,
        'definition': '2+2 confirmed pivots from fully closed 1H/4H candles. '
                      'Compare 15m BOS close to most recently known matching HTF pivot.',
        'caveat': 'Not all locally meaningful CHoCH signals must break a higher-timeframe swing.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', nargs='+', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    a = parser.parse_args()
    out = audit(a.csv)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(out['total'], ensure_ascii=False))


if __name__ == '__main__':
    main()
