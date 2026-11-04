"""MSR-06: 15m threshold crossing and 4H box edge controls. NO TRADES.

All events are reproduced directly from the unchanged MSR01 source fixtures.
Model output is never used as blinded expert truth.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from replay import STEP_MS, read_csv, replay, Settings, iso
from frozen_bos_counterfactual_v05 import compare_symbol

def utc_ms(s):
    t=datetime.fromisoformat(s.replace('Z','+00:00'))
    if t.utcoffset() is None or t.utcoffset().total_seconds()!=0:
        raise ValueError('UTC expected')
    return int(t.timestamp()*1000)

def qualifies(close, side, reference, atr):
    return side*(close-reference)>= Settings().min_bos_atr*atr

def strict_crossing(bars, start, stop, side, reference, atr):
    prev=bars[start].c
    for t in range(start+STEP_MS,stop+STEP_MS,STEP_MS):
        current=bars[t].c
        if not qualifies(prev,side,reference,atr) and qualifies(current,side,reference,atr):
            return t
        prev=current
    return None

def episodes(rows,hours):
    by=defaultdict(list)
    for r in rows:by[(r['symbol'],r['side'])].append(utc_ms(r['sweep_at']))
    count=0
    for times in by.values():
        previous=None
        for t in sorted(times):
            if previous is None or t-previous>hours*3600000:count+=1
            previous=t
    return count

def audit(paths):
    all_rows=[]; receipts=[]; sources=Counter()
    for path in sorted(paths):
        bars,sha=read_csv(path)
        original=replay(bars).events
        sources.update(e['event'] for e in original)
        ledger=compare_symbol(bars,original)
        boxes={e['candidate_id']:e for e in original if e['event']=='ACCUMULATION_LOCKED'}
        by={x.known_at:x for x in bars}
        last=bars[-1].known_at
        for r in ledger:
            t=utc_ms(r['sweep_at']);d=int(r['side']);atr=float(r['atr1h_at_box'])
            box=boxes[r['candidate_id']]
            old=float(r['sweep_anchor']);frozen=float(r['box_anchor'])
            edge=float(box['level_high'] if d==1 else box['level_low'])
            close_sweep=by[t].c
            old_hit=r['original_bos_at'];frozen_hit=r['frozen_bos_at']
            def fresh(tstamp,ref):
                if not tstamp:return None
                hit=utc_ms(tstamp)
                if hit<=t or hit>last:raise ValueError('Invalid BOS time')
                if not qualifies(by[hit].c,d,ref,atr):raise ValueError('Invalid BOS price')
                return not qualifies(by[hit-STEP_MS].c,d,ref,atr)
            old_is_fresh=fresh(old_hit,old)
            frozen_is_fresh=fresh(frozen_hit,frozen)
            hit=strict_crossing(by,t,min(t+24*STEP_MS,last),d,edge,atr)
            all_rows.append({
                'symbol':r['symbol'],'candidate_id':r['candidate_id'],
                'sweep_at':r['sweep_at'],'side':d,'atr1h':atr,
                'accumulation_low':box['level_low'],'accumulation_high':box['level_high'],
                'original_pivot':old,'frozen_pivot':frozen,
                'original_inside_box':float(box['level_low'])<=old<=float(box['level_high']),
                'frozen_inside_box':float(box['level_low'])<=frozen<=float(box['level_high']),
                'original_qualified_on_sweep':qualifies(close_sweep,d,old,atr),
                'original_qualified_before_sweep':qualifies(by[t-STEP_MS].c,d,old,atr),
                'frozen_qualified_on_sweep':qualifies(close_sweep,d,frozen,atr),
                'original_bos_at':old_hit,'original_is_new_crossing':old_is_fresh,
                'frozen_bos_at':frozen_hit,'frozen_is_new_crossing':frozen_is_fresh,
                'box_edge_break_at':iso(hit) if hit is not None else '',
                'complete_observation':r['window_complete'],
            })
        receipts.append({'symbol':bars[0].symbol,'bars':len(bars),'csv_sha256':sha})
    if len(receipts)!=19 or sum(r['bars'] for r in receipts)!=28500:
        raise ValueError('Source coverage incomplete')
    if len(all_rows)!=639 or sources['STRUCTURE_BREAK_CONFIRMED']!=234:
        raise ValueError('MSR-01 parity mismatch')
    summary={
        'status':'AS_OF_RECOGNITION_GEOMETRY_ONLY_NO_SEMANTIC_TRUTH_NO_TRADES',
        'source_receipts':receipts,'source_event_counts':dict(sources),
        'sweeps':len(all_rows),
        'original_bos':sum(x['original_bos_at']!='' and x['original_bos_at'] is not None for x in all_rows),
        'frozen_bos':sum(bool(x['frozen_bos_at']) for x in all_rows),
        'original_new_crossing':sum(x['original_is_new_crossing'] is True for x in all_rows),
        'original_stale_confirmation':sum(x['original_is_new_crossing'] is False for x in all_rows),
        'frozen_new_crossing':sum(x['frozen_is_new_crossing'] is True for x in all_rows),
        'frozen_stale_confirmation':sum(x['frozen_is_new_crossing'] is False for x in all_rows),
        'old_inside_box':sum(x['original_inside_box'] for x in all_rows),
        'frozen_inside_box':sum(x['frozen_inside_box'] for x in all_rows),
        'original_qualified_at_sweep':sum(x['original_qualified_on_sweep'] for x in all_rows),
        'original_qualified_before_sweep':sum(x['original_qualified_before_sweep'] for x in all_rows),
        'frozen_qualified_at_sweep':sum(x['frozen_qualified_on_sweep'] for x in all_rows),
        'range_edge_new_crossing':sum(bool(x['box_edge_break_at']) for x in all_rows),
        'episode_sensitivity_same_symbol_side':{str(h):episodes(all_rows,h) for h in [1,2,4,6,8,12,24]},
        'limitations':['Not a semantic BOS truth','Overlapping episodes and cross-symbol co-movement',
                       'Only 16 days of one period','Expert blind labels not collected','No PnL']
    }
    return all_rows,summary

def run(paths,out):
    rows,summary=audit(paths);out.mkdir(parents=True,exist_ok=True)
    with (out/'scope_checks_639.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('source_receipts','source_event_counts')},ensure_ascii=False,indent=2))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--csv',type=Path,nargs='+',required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    run(a.csv,a.out)
