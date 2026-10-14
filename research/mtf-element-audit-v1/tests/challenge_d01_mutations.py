"""D01 external mutation test: corrupt valid candles and recompute file SHA.
The validator must reject content errors, not merely rely on checksum mismatch.
"""
from __future__ import annotations
import csv,hashlib,json,pathlib,random,sys,tempfile
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from strict_bar_closed import Provenance,read_closed_bars,D01Rejected
STEP=900000
START=int(datetime(2026,4,1,tzinfo=timezone.utc).timestamp()*1000)
RNG=random.Random(20261014)
FIELDS=('open_time','close_time','open','high','low','close','volume','symbol')

def base():
 return [dict(open_time=str(START+i*STEP),close_time=str(START+(i+1)*STEP-1),open='100.5',high='101.5',low='99.2',close='100.9',volume='15.1',symbol='BTCUSDT') for i in range(12)]

def check():
 variants=['blank_volume','nan','negative_volume','negative_price','future','wrong_close','gap','duplicate','bad_symbol','bad_high','offgrid','order_swap']
 results=[]
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d)/'bars.csv'
  for i in range(180):
   kind=variants[i%len(variants)];rows=base();j=RNG.randrange(1,len(rows)-2)
   if kind=='blank_volume':rows[j]['volume']=''
   if kind=='nan':rows[j]['volume']='NaN'
   if kind=='negative_volume':rows[j]['volume']='-1'
   if kind=='negative_price':rows[j]['open']='-1'
   if kind=='future':rows[j]['open_time']=str(START+20*STEP);rows[j]['close_time']=str(START+21*STEP-1)
   if kind=='wrong_close':rows[j]['close_time']=str(int(rows[j]['close_time'])+1)
   if kind=='gap':rows.pop(j)
   if kind=='duplicate':rows[j]=rows[j-1].copy()
   if kind=='bad_symbol':rows[j]['symbol']='ETHUSDT'
   if kind=='bad_high':rows[j]['high']='90'
   if kind=='offgrid':rows[j]['open_time']=str(int(rows[j]['open_time'])+60000);rows[j]['close_time']=str(int(rows[j]['close_time'])+60000)
   if kind=='order_swap':rows[j],rows[j+1]=rows[j+1],rows[j]
   with p.open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
   digest=hashlib.sha256(p.read_bytes()).hexdigest()
   prov=Provenance('BINANCE','FUTURES_UM','BTCUSDT','15m','mutation-test SHA re-computed',digest)
   try:read_closed_bars(p,prov,as_of_utc=START+12*STEP)
   except D01Rejected as e:results.append({'case':kind,'accepted':False,'reason':e.code})
   else:results.append({'case':kind,'accepted':True})
 passed=sum(not x['accepted'] for x in results)
 return {'seed':20261014,'total':len(results),'rejected':passed,'accepted_corruption':len(results)-passed,
         'all_negative_cases':sorted(set(x['case'] for x in results)),
         'case_details':results,'verdict':'PASS' if passed==len(results) else 'FAIL'}
if __name__=='__main__':
 data=check()
 pathlib.Path(sys.argv[1]).write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print('D01_MUTATION_TEST',data['verdict'],data['rejected'],'/',data['total']);sys.exit(0 if data['verdict']=='PASS' else 2)
