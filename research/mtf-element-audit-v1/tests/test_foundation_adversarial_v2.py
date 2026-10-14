#!/usr/bin/env python3
"""Falsify D01/D02 acceptance of the *existing* immutable research loader.

No trading code is edited. No PnL is consulted. 'Accepted' is an observation,
not an endorsement. Reference contract is more strict by construction and is
not promoted into production until approved separately.
"""
from __future__ import annotations
import csv,hashlib,importlib.util,json,math,os,tempfile,sys
from datetime import datetime,timezone
from pathlib import Path

ENGINE=Path('/mnt/data/MTF_ROUTE_LAB_V05_LIFECYCLE_REPAIR_20261014/src/mtf_engine.py')
sp=importlib.util.spec_from_file_location('legacy_mtf_engine',ENGINE)
engine=importlib.util.module_from_spec(sp);sys.modules[sp.name]=engine;sp.loader.exec_module(engine)
STEP=900000
START=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
BASE=[{'open_time':str(START+i*STEP),'open':'100','high':'103','low':'99','close':'101','volume':'5'} for i in range(5)]
FIELDS=['open_time','open','high','low','close','volume']

def sample(rows,headers=FIELDS,tf='15m'):
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'test.csv'
  with p.open('w',encoding='utf8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=headers,extrasaction='ignore');w.writeheader();w.writerows(rows)
  try:
   bs,_=engine.load_csv(p,'BTCUSDT',tf)
   return {'accepts':True,'count':len(bs),'last_bar_end':bs[-1].end if bs else None}
  except Exception as e:return {'accepts':False,'error_type':type(e).__name__,'error_msg':str(e)[:160]}

def exact_gate(rows,as_of,tf='15m'):
 """Independent proposed D01 contract, not executable trade engine."""
 step=engine.STEPS[tf];prev=None
 for raw in rows:
  for k in FIELDS:
   if k not in raw or not str(raw[k]).strip():return False,'MISSING_'+k
  try:
   ms=int(raw['open_time']);oh=[float(raw[x]) for x in ('open','high','low','close')];volume=float(raw['volume'])
  except (ValueError,TypeError):return False,'PARSE_ERROR'
  o,h,l,c=oh
  if any(not math.isfinite(z) for z in [*oh,volume]) or h<max(o,l,c) or l>min(o,c,h) or volume<0:return False,'BAD_OHLCV'
  if ms%step:return False,'OFF_GRID'
  if prev is not None and ms-prev!=step:return False,'NON_CONTIGUOUS_OR_UNSORTED'
  if ms+step>as_of:return False,'CANDLE_STILL_OPEN'
  prev=ms
 return True,'COMPLETE_CLOSED_ALIGNED'

def check_agg():
 b=[]
 for i in range(5):b.append(engine.Bar(START+i*STEP,START+(i+1)*STEP,100,105,95,101,1.0,'15m'))
 full=engine.aggregate(b,'1h');partial=engine.aggregate(b[:3],'1h')
 # An as-of 00:45 must never contain a completed 1H candle ending at 01:00.
 future_bars=[x for x in full if x.end>START+3*STEP]
 return {'one_closed_1h_bucket_from_5_quarters':len(full),'zero_1h_from_3_quarters':len(partial),
         'aggregate_api_has_as_of_parameter':'as_of' in engine.aggregate.__code__.co_varnames[:engine.aggregate.__code__.co_argcount],
         'future_bar_in_raw_aggregate_called_with_all_data':len(future_bars),
         'interpretation':'aggregation is correct on complete buckets, but caller MUST pass only as-of data; no own as_of gate'}

def main():
 cases={}
 def evaluate(name,rows,as_of,headers=FIELDS,expected_ok=True):
  observed=sample(rows,headers);ref,reason=exact_gate(rows,as_of)
  cases[name]={'legacy':observed,'proposed_strict':{'accepted':ref,'reason':reason},
    'contract_expectation':expected_ok,'legacy_matches_contract':observed['accepts']==ref}
 # control: all known as of 2026-01-01 01:15 UTC
 evaluate('valid_5_closed',BASE,START+5*STEP,expected_ok=True)
 missing=[dict(x) for x in BASE];missing[2]['volume']=''
 evaluate('empty_volume',missing,START+5*STEP,expected_ok=False)
 missing_col=[{k:v for k,v in x.items() if k!='volume'} for x in BASE]
 evaluate('missing_volume_column',missing_col,START+5*STEP,[k for k in FIELDS if k!='volume'],expected_ok=False)
 off=[dict(x) for x in BASE]
 for x in off:x['open_time']=str(int(x['open_time'])+5*60*1000)
 evaluate('all_timestamps_shifted_5_minutes',off,START+6*STEP,expected_ok=False)
 evaluate('last_candle_unfinished_as_of',BASE,START+4*STEP,expected_ok=False)
 dup=[dict(x) for x in BASE];dup.append(dict(BASE[-1]))
 evaluate('duplicate_timestamp',dup,START+6*STEP,expected_ok=False)
 gap=[dict(x) for x in BASE];gap.pop(2)
 evaluate('gap_15m',gap,START+5*STEP,expected_ok=False)
 bad=[dict(x) for x in BASE];bad[1]['high']='98'
 evaluate('invalid_high',bad,START+5*STEP,expected_ok=False)
 cases_with_real_failures=[k for k,v in cases.items() if not v['legacy_matches_contract']]
 outcome={'component_ids':['D01','D02','D03','D04'],
          'legacy_source_sha256':hashlib.sha256(ENGINE.read_bytes()).hexdigest(),
          'cases':cases,'aggregate_probe':check_agg(),
          'counterexamples_where_legacy_accepts_invalid':cases_with_real_failures,
          'rejected_as_fully_accepted':bool(cases_with_real_failures),
          'result':'D01_EXISTING_LOADER_FAILS_STRICT_CLOSED_CANDLE_CONTRACT',
          'scope':'Synthetic examples, independent gate; needs real bar-source check and semantic signoff'}
 print(json.dumps(outcome,ensure_ascii=False,sort_keys=True,indent=2))
 return 0
if __name__=='__main__':raise SystemExit(main())