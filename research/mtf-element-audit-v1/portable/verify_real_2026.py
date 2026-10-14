#!/usr/bin/env python3
"""Independent real-history D01/D02/D04 QA (never generate trade decisions).
Checks embedded consolidated Binance USD-M CSV and the manifest packaged in
previous successful research artifact. Does not authenticate remote archives
anew; checks source provenance claim and SHA256 for the CSV as packaged.
"""
import csv,io,json,hashlib,zipfile,math
from collections import defaultdict
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path

ZIP=Path(__file__).resolve().parents[1]/'baselines/binance_futures_2026.zip'
PREFIX='mtf_route/data/history/'
START=int(datetime(2026,4,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,10,13,tzinfo=timezone.utc).timestamp()*1000)
SYMS=['BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT']
REQ=('open_time','open','high','low','close','volume','close_time','symbol')

def get(z,name,tf,symbol,m):
 payload=z.read(PREFIX+name)
 entry=m[(symbol,tf)]
 digest=hashlib.sha256(payload).hexdigest()
 errors=[];seen=set();previous=None;rows=[]
 if digest!=entry['sha256']:errors.append('MANIFEST_SHA_MISMATCH')
 if not entry['sources'] or any('/data/futures/um/' not in x['url'] or len(x['sha256'])!=64 for x in entry['sources']):errors.append('NOT_FUTURES_UM_SOURCE')
 dt={'15m':900000,'1d':86400000}[tf]
 rdr=csv.DictReader(io.StringIO(payload.decode('utf-8-sig')))
 if not set(REQ).issubset(rdr.fieldnames or []):errors.append('MISSING_HEADER')
 for i,x in enumerate(rdr):
  try:
   t=int(x['open_time']);end=int(x['close_time']);v=Decimal(x['volume']);prices=[Decimal(x[k]) for k in ('open','high','low','close')]
   if x['symbol']!=symbol:errors.append('SYMBOL_MISMATCH')
   if t%dt or end!=t+dt-1:errors.append('UTC_ALIGNMENT_'+str(i))
   if previous is not None and t-previous!=dt:errors.append('DISCONTIGUOUS_'+str(i))
   if t in seen:errors.append('DUPLICATE_'+str(i))
   if v<0 or min(prices)<=0 or prices[1]<max(prices[0],prices[2],prices[3]) or prices[2]>min(prices[0],prices[1],prices[3]):errors.append('BAD_OHLCV_'+str(i))
   if tf=='15m' and (t<START or t>=END):errors.append('OUTSIDE_WINDOW_'+str(i))
   if tf=='15m' and t+dt>END:errors.append('UNFINISHED_'+str(i))
   rows.append((t,prices[0],prices[1],prices[2],prices[3],v));seen.add(t);previous=t
  except Exception:errors.append('BAD_ROW_'+str(i))
 if len(rows)!=entry['candles']:errors.append('MANIFEST_COUNT_MISMATCH')
 if tf=='15m' and (len(rows)!=18720 or rows[0][0]!=START or rows[-1][0]+dt!=END):errors.append('EXPECTED_2026_RANGE_INVALID')
 return rows,errors,digest

def main():
 with zipfile.ZipFile(ZIP) as z:
  manifest=json.loads(z.read(PREFIX+'manifest_vision.json').decode())
  m={(x['symbol'],x['tf']):x for x in manifest}
  results={};total_bad=0;volume_worst=Decimal('0');daily_comparisons=0
  for symbol in SYMS:
   q,errq,sha15=get(z,symbol+'_15m.csv','15m',symbol,m)
   d,errd,sha1d=get(z,symbol+'_1d.csv','1d',symbol,m)
   days={t: (o,h,l,c,v) for t,o,h,l,c,v in d}
   buckets=defaultdict(list)
   for b in q:buckets[(b[0]//86400000)*86400000].append(b)
   mismatches=[]
   for day,bars in sorted(buckets.items()):
    ref=days.get(day)
    if ref is None or len(bars)!=96:
     mismatches.append({'day':day,'error':'MISSING_DAILY_OR_INCOMPLETE_QUARTERS'});continue
    native=(bars[0][1],max(x[2] for x in bars),min(x[3] for x in bars),bars[-1][4],sum(x[5] for x in bars))
    dvolume=abs(native[4]-ref[4]);volume_worst=max(volume_worst,dvolume)
    if native[:4]!=ref[:4] or dvolume>Decimal('0.000001'):
     mismatches.append({'day':day,'error':'NATIVE_DAILY_15M_AGGREGATION_MISMATCH','volume_delta':str(dvolume)})
    daily_comparisons+=1
   total_bad+=len(errq)+len(errd)+len(mismatches)
   results[symbol]={'15m':len(q),'1d':len(d),'15m_sha256':sha15,'1d_sha256':sha1d,'csv_issues':errq[:5]+errd[:5],
                    'native_daily_vs_96x15m_mismatches':mismatches[:3],'bad_days':len(mismatches),'checked_days':len(buckets)}
 out={'input_artifact_sha256':hashlib.sha256(ZIP.read_bytes()).hexdigest(),
      'scope':'Packaged 2026 USD-M CSVs; not fresh remote network attestation; excludes unclosed bars',
      'symbols':results,'raw_15m_total':sum(x['15m'] for x in results.values()),
      'native_days_total':daily_comparisons,'biggest_15m_sum_vs_1d_volume_difference':str(volume_worst),
      'total_errors':total_bad,
      'verdict':'PACKAGED_REAL_HISTORY_QA_PASS' if total_bad==0 else 'PACKAGED_REAL_HISTORY_QA_FAIL',
      'counterclaim':'These real files pass, but the generic low-level CSV loader can still accept malformed supplied files; upstream gate had independently screened these archived files.'}
 print(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2))
 return 0 if total_bad==0 else 1
if __name__=='__main__':raise SystemExit(main())
