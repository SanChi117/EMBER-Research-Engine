#!/usr/bin/env python3
import argparse, json, pathlib, sys, hashlib, random
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from strict_event_lineage_d03 import CausalEvent, EventLedger, D03Rejected

def source(uid='S',symbol='BTCUSDT'):
 return CausalEvent(uid,'SOURCE',symbol,'BINANCE','USDM_FUTURES','4h',1000,2000,2000,(),('bar_sha:'+uid,))
def make_graph():
 g=EventLedger();g.add(source());g.add(CausalEvent('P','POI','BTCUSDT','BINANCE','USDM_FUTURES','4h',1000,2000,2100,('S',),('feature:P',)))
 g.add(CausalEvent('T','TRIGGER','BTCUSDT','BINANCE','USDM_FUTURES','1h',1000,2000,2200,('P',),('feature:T',)))
 return g

def mutation(i):
 g=make_graph();scenario=i%9
 e=dict(uid='C'+str(i),kind='VC',symbol='BTCUSDT',venue='BINANCE',market='USDM_FUTURES',timeframe='15m',origin_open_ms=1000,origin_close_ms=2000,known_at_ms=2300,parent_uids=('T',),evidence_uids=('source:mutation',))
 if scenario==0:e['known_at_ms']=1999
 if scenario==1:e['symbol']='ETHUSDT'
 if scenario==2:e['venue']='BYBIT'
 if scenario==3:e['market']='SPOT'
 if scenario==4:e['parent_uids']=('NOT_REGISTERED',)
 if scenario==5:e['origin_close_ms']=2500
 if scenario==6:e['decision_at_ms']=2100
 if scenario==7:
  g.add(CausalEvent('X','INVALIDATION','BTCUSDT','BINANCE','USDM_FUTURES','4h',1000,2000,2250,('P',),('source:cancel',)))
 if scenario==8:e['parent_uids']=()
 try:g.add(CausalEvent(**e));return 'ACCEPTED_INVALID'
 except D03Rejected as ex:return ex.code

def main():
 res=[mutation(i) for i in range(180)]
 expected={'UNKNOWN_UNCLOSED_EVENT','CROSS_INSTRUMENT_PARENT','UNKNOWN_PARENT','DECISION_BEFORE_KNOWN',
           'PARENT_ANCESTRY_INVALIDATED','ORPHAN_DERIVED_EVENT'}
 assert len(res)==180 and 'ACCEPTED_INVALID' not in res and set(res)==expected,set(res)
 future_checks=[]
 for i in range(20):
  g=make_graph();asof=2250+i
  before=g.snapshot(asof);before_digest=hashlib.sha256(repr(before).encode()).hexdigest()
  # Later unrelated/cancelled events may alter future views, never the past.
  g.add(CausalEvent('X'+str(i),'INVALIDATION','BTCUSDT','BINANCE','USDM_FUTURES','4h',1000,2000,2400+i,('P',),('source:invalidate',)))
  assert before==g.snapshot(asof)
  assert hashlib.sha256(repr(g.snapshot(asof)).encode()).hexdigest()==before_digest
  future_checks.append(True)
 return dict(component='D03',total=180,rejected=180,by_code={k:res.count(k) for k in sorted(set(res))},
             future_suffix_tests=len(future_checks),future_suffix_unchanged=all(future_checks),
             result='PASS_FORMAL_ISOLATED',no_strategy_claim=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args()
 result=main();pathlib.Path(args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(result)
