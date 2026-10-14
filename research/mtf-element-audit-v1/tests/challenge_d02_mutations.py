#!/usr/bin/env python3
"""Independent forced invalid-child perturbations and future-invariance tests."""
import json, pathlib,sys,argparse
from dataclasses import replace
from decimal import Decimal as D
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from strict_bar_closed import ClosedBar,TF_MS
from strict_tf_d02 import snapshot_htf,D02Rejected
T=int(datetime(2026,4,6,tzinfo=timezone.utc).timestamp()*1000);P=TF_MS['15m']

def seedbars():
    return [ClosedBar('BTCUSDT','15m',T+i*P,T+(i+1)*P,D(100+i),D(103+i),D(99+i),D(101+i),D(i+5)) for i in range(16)]

def run():
    errors=[];rejections=0;stable=0
    for i in range(20):
        good=seedbars()
        def revise(key):
            c=list(good)
            if key=='gap': del c[i%15]
            elif key=='duplicate':c.insert(i%15+1,c[i%15])
            elif key=='shift':c[i%15]=replace(c[i%15],open_at_ms=c[i%15].open_at_ms+1)
            elif key=='wrong_close':c[i%15]=replace(c[i%15],close_exclusive_ms=c[i%15].close_exclusive_ms-1)
            elif key=='symbol':c[i%15]=replace(c[i%15],symbol='ETHUSDT')
            elif key=='negative_volume':c[i%15]=replace(c[i%15],volume=D('-1'))
            return c
        for key in ['gap','duplicate','shift','wrong_close','symbol','negative_volume']:
            try:snapshot_htf(revise(key),'1h',as_of_utc=T+16*P,expected_source_start_utc=T);errors.append(key)
            except D02Rejected:rejections+=1
        before=snapshot_htf(good,'1h',as_of_utc=T+4*P)
        after=list(good)
        for j in range(4,16):after[j]=replace(after[j],high=D(1_000_000+i),volume=D(1_000_000+i))
        if snapshot_htf(after,'1h',as_of_utc=T+4*P)!=before:errors.append('future_look_'+str(i))
        else:stable+=1
    return {'cycle':'C05','rejection_attempts':120,'rejections':rejections,'future_mutation_attempts':20,
        'future_invariance_passes':stable,'unexpected_acceptances':errors,'result':'PASS' if rejections==120 and stable==20 and not errors else 'FAIL'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    d=run();pathlib.Path(a.out).write_text(json.dumps(d,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(d);sys.exit(0 if d['result']=='PASS' else 2)
