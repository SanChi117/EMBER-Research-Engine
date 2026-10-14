#!/usr/bin/env python3
"""Append-only (by process policy) SHA256-chained auditable action journal.

A hash chain detects after-the-fact edits; it is NOT independently tamper-proof
until the current tip is externally anchored (e.g. git commit).
"""
import argparse, datetime, hashlib, json, pathlib, sys
BASE=pathlib.Path(__file__).resolve().parents[1]
JOURNAL=BASE/'ЖУРНАЛ_ДЕЙСТВИЙ.jsonl'
GENESIS='0'*64

def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def hashfile(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def verify():
 prev=GENESIS; n=0; ids=set()
 if not JOURNAL.exists():return 0,prev
 for line in JOURNAL.read_text(encoding='utf8').splitlines():
  o=json.loads(line)
  if o['prev_sha256']!=prev:raise ValueError('Broken previous hash at event '+str(n+1))
  hh=o.pop('record_sha256')
  if hashlib.sha256(canonical(o)).hexdigest()!=hh:raise ValueError('Tampered event at '+str(n+1))
  if o['seq']!=n+1:raise ValueError('Sequence gap')
  if o['action_id'] in ids:raise ValueError('Duplicate action ID')
  ids.add(o['action_id']);n+=1;prev=hh
 return n,prev

def record(args):
 n,prev=verify()
 ev=[]
 for item in args.evidence:
  p=BASE/item
  if not p.is_file():raise FileNotFoundError('Evidence not generated: '+str(p))
  ev.append({'path':item,'sha256':hashfile(p),'bytes':p.stat().st_size})
 if args.verdict=='DONE' and not ev:raise ValueError('Cannot mark DONE without evidence')
 if args.verdict=='DONE' and any(x['bytes']==0 for x in ev):raise ValueError('Cannot mark DONE with empty evidence')
 if args.verdict=='DONE' and args.cycle_result not in ('NOT_APPLICABLE','PASSED','FAILED','BLOCKED'):
  raise ValueError('Need declared cycle_result')
 o={'seq':n+1,'action_id':args.action_id,'cycle':args.cycle,
    'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'planned':args.planned,'actually_executed':args.executed,
    'observed_result':args.result,'verdict':args.verdict,
    'cycle_result':args.cycle_result,'countercheck':args.countercheck,'invalidates_action_id':args.invalidates_action_id,
    'evidence':ev,'prev_sha256':prev}
 o['record_sha256']=hashlib.sha256(canonical(o)).hexdigest()
 with JOURNAL.open('a',encoding='utf8') as f:
  f.write(json.dumps(o,ensure_ascii=False,sort_keys=True)+'\n');f.flush()
  import os;os.fsync(f.fileno())
 print('LOGGED',o['action_id'],'SEQ',o['seq'],'HASH',o['record_sha256'])

if __name__=='__main__':
 p=argparse.ArgumentParser();ss=p.add_subparsers(dest='cmd',required=True)
 a=ss.add_parser('record')
 for n in ('action_id','cycle','planned','executed','result','verdict','countercheck'):a.add_argument('--'+n.replace('_','-'),required=True,dest=n)
 a.add_argument('--cycle-result',choices=['NOT_APPLICABLE','PASSED','FAILED','BLOCKED'],required=True,dest='cycle_result')
 a.add_argument('--evidence',action='append',default=[])
 a.add_argument('--invalidates-action-id',default=None,dest='invalidates_action_id')
 ss.add_parser('verify')
 arg=p.parse_args()
 if arg.cmd=='record':record(arg)
 else:
  x,y=verify();print('INTEGRITY_PASS' if x else 'EMPTY_JOURNAL','entries',x,'tip_sha256',y)
