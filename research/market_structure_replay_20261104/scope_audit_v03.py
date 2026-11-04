"""MSR-03: AS-OF scope of local MSR-01 structure breaks. RESEARCH ONLY; no orders.

This is a *sidecar*: original replay recognition stays untouched.
The HTF reference is frozen at the SWEEP time, not selected using future bars.
"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
from collections import Counter

from replay import read_csv, replay, iso
from htf_pivot_compare_v02 import last_confirmed_swings


def scope_rows(bars, events):
    h1=last_confirmed_swings(bars, 4)
    h4=last_confirmed_swings(bars, 16)
    close={iso(b.known_at): b.c for b in bars}
    sweeps={e['candidate_id']:e for e in events if e['event']=='SWEEP_RETURN'}
    boxes={e['candidate_id']:e for e in events if e['event']=='ACCUMULATION_LOCKED'}
    result=[]
    for e in events:
        if e['event']!='STRUCTURE_BREAK_CONFIRMED':
            continue
        identifier=e['candidate_id']
        if identifier not in sweeps or identifier not in boxes:
            raise ValueError('orphan BOS')
        sweep=sweeps[identifier]
        box=boxes[identifier]
        t, s=sweep['known_at'], e['known_at']
        if not t<s:
            raise ValueError('noncausal sweep/BOS order')
        d=int(e['side'])
        if d not in (-1,1):
            raise ValueError('bad direction')
        p=close[s]
        row={'symbol':e['symbol'], 'candidate_id':identifier,
             'sweep_at':t,'bos_at':s,'side':d,'bos_close':p,
             '15m_pivot':float(e['reference']),
             '15m_pivot_known_at':e['pivot_known_at'],
             'box_known_at':box['known_at'],
             'pivot_known_after_box_lock':e['pivot_known_at']>box['known_at'],
             'pivot_confirmed_on_sweep_bar':e['pivot_known_at']==t,
             'pivot_inside_locked_range':float(box['level_low'])<=float(e['reference'])<=float(box['level_high'])}
        if e['pivot_known_at']>t:
            raise ValueError('pivot from future used by sweep')
        for tf,snaps in [('1h',h1),('4h',h4)]:
            before=snaps[t][0 if d==1 else 1]
            after=snaps[s][0 if d==1 else 1]
            row[tf+'_pivot_at_sweep']=before
            row[tf+'_pivot_at_bos']=after
            row[tf+'_passed_frozen_pivot']=(p>before if d==1 else p<before) if before is not None else None
            row[tf+'_passed_at_bos_pivot']=(p>after if d==1 else p<after) if after is not None else None
            row[tf+'_reference_changed']=before!=after
        a,b=row['1h_passed_frozen_pivot'],row['4h_passed_frozen_pivot']
        row['scope']=('UNKNOWN_HTF_PIVOT' if a is None or b is None else
                      'BOTH_1H_4H' if a and b else
                      'ONE_HOUR_ONLY' if a else
                      'FOUR_HOUR_ONLY' if b else
                      'LOCAL_15M_ONLY')
        result.append(row)
    return result


def inspect_blind(blind_dir:Path):
    """Count visible 4H history without opening the separately sealed labels."""
    import re
    cases=sorted((blind_dir/'cases').glob('*.html'))
    if len(cases)!=180:
        raise ValueError('expected 180 blind HTML cases')
    result=[]
    for p in cases:
        html=p.read_text(encoding='utf-8')
        svgs=re.findall(r'<svg\b.*?</svg>',html,flags=re.DOTALL)
        if len(svgs)!=3:raise ValueError('bad chart '+p.name)
        n=[len(re.findall(r'<rect\b',svg))-1 for svg in svgs]
        result.append({'case_id':p.stem,'15m_visible':n[0],
                       '1h_visible':n[1],'4h_visible':n[2],
                       'h4_review':'CONTEXT_INSUFFICIENT' if n[2]<20 else 'CONTEXT_VISIBLE'})
    return result


def run(paths, blind_dir, out):
    out.mkdir(parents=True,exist_ok=True)
    rows=[];series=[]
    for path in sorted(paths):
        bars,sha=read_csv(path)
        original=replay(bars).events
        sidecar=scope_rows(bars,original)
        rows.extend(sidecar)
        series.append({'symbol':bars[0].symbol,'sha256_source_csv':sha,
                       '15m_bars':len(bars),'original_bos':len(sidecar)})
    if len(series)!=19 or sum(x['15m_bars'] for x in series)!=28500:
        raise ValueError('incorrect real-19 source coverage')
    blind=inspect_blind(blind_dir)
    counts=Counter(x['scope'] for x in rows)
    unique={(x['symbol'],x['bos_at'],x['side']) for x in rows}
    summary={
        'status':'CAUSAL_SCOPE_DIAGNOSTIC_ONLY_NO_EXPERT_TRUTH_NO_PNL',
        'total_bos':len(rows),'unique_symbol_time_side':len(unique),
        'duplicate_same_bar_side':len(rows)-len(unique),
        'scope_counts':dict(counts),
        '1h_frozen_pass':sum(x['1h_passed_frozen_pivot'] is True for x in rows),
        '4h_frozen_pass':sum(x['4h_passed_frozen_pivot'] is True for x in rows),
        '1h_at_bos_pass':sum(x['1h_passed_at_bos_pivot'] is True for x in rows),
        '4h_at_bos_pass':sum(x['4h_passed_at_bos_pivot'] is True for x in rows),
        '4h_frozen_missing':sum(x['4h_passed_frozen_pivot'] is None for x in rows),
        '1h_changed_after_sweep':sum(x['1h_reference_changed'] for x in rows),
        '4h_changed_after_sweep':sum(x['4h_reference_changed'] for x in rows),
        'inside_box':sum(x['pivot_inside_locked_range'] for x in rows),
        'pivot_known_after_box_lock':sum(x['pivot_known_after_box_lock'] for x in rows),
        'pivot_confirmed_on_sweep_bar':sum(x['pivot_confirmed_on_sweep_bar'] for x in rows),
        'blind_cases':len(blind),
        'blind_h4_short_lt5':sum(x['4h_visible']<5 for x in blind),
        'blind_h4_short_lt20':sum(x['4h_visible']<20 for x in blind),
        'blind_h4_short_lt36':sum(x['4h_visible']<36 for x in blind),
        'sources':series,
        'notice':'HTF swing scope is a mechanical proxy, NOT independently verified BOS.'
    }
    with (out/'scope_ledger.jsonl').open('w',encoding='utf-8') as f:
        for x in rows:f.write(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n')
    with (out/'blind_context_readiness.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(blind[0]));w.writeheader();w.writerows(blind)
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='sources'},ensure_ascii=False,indent=2))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--csv',nargs='+',required=True,type=Path)
    p.add_argument('--blind-dir',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    run(a.csv,a.blind_dir,a.out)
