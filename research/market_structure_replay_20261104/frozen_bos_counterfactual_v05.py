"""MSR-05: causal as-of comparison of BOS at lock-frozen vs sweep-selected pivots.

This is an observational, non-trading diagnostic. The reference is determined at
accumulation lock from confirmed pivots. Original MSR-01 events remain untouched.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from replay import Settings, iso, read_csv, replay


def compare_symbol(bars, events):
    close_index = {iso(b.known_at): i for i, b in enumerate(bars)}
    confirmed = {1: None, -1: None}
    locks, sweeps, original = {}, {}, {}
    for e in events:
        typ, cid = e['event'], e['candidate_id']
        if typ == 'PIVOT_HIGH_CONFIRMED':
            confirmed[1] = (float(e['pivot_price']), e['known_at'])
        elif typ == 'PIVOT_LOW_CONFIRMED':
            confirmed[-1] = (float(e['pivot_price']), e['known_at'])
        elif typ == 'ACCUMULATION_LOCKED':
            if cid in locks: raise ValueError('duplicate lock')
            locks[cid] = {'lock_at': e['known_at'], 'atr': float(e['atr1h']), 'pivots': confirmed.copy()}
        elif typ == 'SWEEP_RETURN':
            side = int(e['side'])
            if cid not in locks or cid in sweeps or side not in (-1, 1):
                raise ValueError('bad sweep')
            current = confirmed[side]
            if current is None or current != (float(e['reference']), e['pivot_known_at']):
                raise ValueError('sweep reference does not match causal as-of pivot')
            if not locks[cid]['lock_at'] < e['known_at']:
                raise ValueError('sweep precedes accumulation')
            sweeps[cid] = {'sweep_at': e['known_at'], 'side': side,
                           'old_reference': current, 'frozen_reference': locks[cid]['pivots'][side]}
        elif typ == 'STRUCTURE_BREAK_CONFIRMED':
            if cid in original or cid not in sweeps:
                raise ValueError('orphan or duplicate BOS')
            if not sweeps[cid]['sweep_at'] < e['known_at']:
                raise ValueError('sweep precedes BOS or timestamp out of order')
            original[cid] = e

    settings = Settings()
    rows = []
    for cid, sweep in sweeps.items():
        start = close_index.get(sweep['sweep_at'])
        if start is None: raise ValueError('sweep not present in OHLC')
        d, old, frozen = sweep['side'], sweep['old_reference'], sweep['frozen_reference']
        atr = locks[cid]['atr']
        if not atr > 0: raise ValueError('bad ATR at lock')
        last = min(start + settings.structure_expiry_bars, len(bars) - 1)

        def first(ref):
            if ref is None: return None
            level = ref[0]
            for i in range(start + 1, last + 1):
                price = bars[i].c
                if d * (price - level) >= settings.min_bos_atr * atr:
                    return i
            return None

        old_idx, frozen_idx = first(old), first(frozen)
        previous = original.get(cid)
        previous_time = previous['known_at'] if previous else None
        old_time = iso(bars[old_idx].known_at) if old_idx is not None else None
        frozen_time = iso(bars[frozen_idx].known_at) if frozen_idx is not None else None
        if old_time != previous_time:
            raise ValueError(f'original MSR-01 BOS parity mismatch: {cid}: {old_time}, {previous_time}')
        old_bos_close = bars[old_idx].c if old_idx is not None else None
        frozen_cross_on_old = None if frozen is None or old_idx is None else (
            d * (old_bos_close - frozen[0]) >= settings.min_bos_atr * atr)
        rows.append({
            'symbol': bars[0].symbol, 'candidate_id': cid, 'side': d,
            'lock_at': locks[cid]['lock_at'], 'sweep_at': sweep['sweep_at'],
            'box_anchor': frozen[0] if frozen else None,
            'box_anchor_known_at': frozen[1] if frozen else None,
            'sweep_anchor': old[0], 'sweep_anchor_known_at': old[1],
            'anchor_reselected': frozen != old,
            'anchor_price_changed': frozen is not None and frozen[0] != old[0],
            'atr1h_at_box': atr,
            'original_bos_at': previous_time,
            'original_bos_close': old_bos_close,
            'frozen_bos_at': frozen_time,
            'frozen_bos_close': bars[frozen_idx].c if frozen_idx is not None else None,
            'frozen_crossed_at_original_bos': frozen_cross_on_old,
            'original_signal': previous is not None,
            'frozen_signal': None if frozen is None else frozen_idx is not None,
            'window_complete': start + settings.structure_expiry_bars < len(bars),
            'observed_future_bars': last - start,
            'first_hit_delta_bars': (frozen_idx-old_idx) if frozen_idx is not None and old_idx is not None else None,
            'status': 'NO_ANCHOR_AT_LOCK' if frozen is None else
                      'BOTH' if old_idx is not None and frozen_idx is not None else
                      'ONLY_ORIGINAL' if old_idx is not None else
                      'ONLY_FROZEN' if frozen_idx is not None else
                      'NO_HIT_FULL_WINDOW' if start + settings.structure_expiry_bars < len(bars) else
                      'CENSORED_NO_HIT'
        })
    return rows


def summarize(rows):
    events = Counter(r['status'] for r in rows)
    bos = [r for r in rows if r['original_signal']]
    return {
        'status':'CAUSAL_FROZEN_ANCHOR_COUNTERFACTUAL_NOT_EXPERT_TRUTH_NO_TRADES',
        'sweeps':len(rows),
        'original_bos':len(bos),
        'frozen_bos':sum(r['frozen_signal'] is True for r in rows),
        'frozen_missing':sum(r['frozen_signal'] is None for r in rows),
        'status_counts':dict(events),
        'original_bos_crossed_frozen_at_original_time':sum(r['frozen_crossed_at_original_bos'] is True for r in bos),
        'original_bos_did_not_cross_frozen_at_original_time':sum(r['frozen_crossed_at_original_bos'] is False for r in bos),
        'original_bos_unknown_frozen_anchor':sum(r['frozen_crossed_at_original_bos'] is None for r in bos),
        'changed_price_in_original_bos':sum(r['anchor_price_changed'] for r in bos),
        'unique_original_symbol_time_side':len({(r['symbol'],r['original_bos_at'],r['side']) for r in bos}),
        'unique_frozen_symbol_time_side':len({(r['symbol'],r['frozen_bos_at'],r['side']) for r in rows if r['frozen_signal'] is True}),
        'censored_sweeps':sum(not r['window_complete'] for r in rows),
        'complete_sweeps':sum(r['window_complete'] for r in rows),
    }


def run(paths,out):
    rows=[]; receipts=[]; c=Counter()
    for p in sorted(paths):
        bars, sha = read_csv(p)
        events = replay(bars).events
        c.update(e['event'] for e in events)
        rows.extend(compare_symbol(bars,events))
        receipts.append({'symbol':bars[0].symbol,'sha256':sha,'bars':len(bars)})
    if len(receipts)!=19 or sum(x['bars'] for x in receipts)!=28500:
        raise ValueError('source count differs from frozen 19-symbol archive')
    s=summarize(rows)
    if s['sweeps'] != c['SWEEP_RETURN'] or s['original_bos'] != c['STRUCTURE_BREAK_CONFIRMED']:
        raise ValueError('original event count mismatch')
    out.mkdir(parents=True,exist_ok=True)
    with (out/'sweep_counterfactual_ledger.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    s['source_receipts']=receipts
    s['original_event_counts']=dict(c)
    (out/'summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return s


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--csv',nargs='+',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    a=parser.parse_args()
    print(json.dumps(run(a.csv,a.out),ensure_ascii=False,indent=2))
