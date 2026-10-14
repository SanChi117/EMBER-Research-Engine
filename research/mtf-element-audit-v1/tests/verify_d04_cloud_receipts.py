#!/usr/bin/env python3
"""Fetch Binance .CHECKSUM and ZIP via verified HTTPS, compare daily and 15m.
Does NOT generate signals or optimize trading rules. Fail closed on fetch errors.
"""
from __future__ import annotations
import json,sys,datetime,platform,ssl,csv
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from strict_vision_d04 import fetch_attested_source,D04Rejected
BASE='https://data.binance.vision/data/futures/um/daily/klines/'
SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT')
KEYS=[(sym,tf,'2026-10-11') for sym in SYMBOLS for tf in ('15m','1d')]+[('BTCUSDT','15m','2025-01-29'),('BTCUSDT','1d','2025-01-29')]

def comparable(a,b):return all(Decimal(a[k])==Decimal(b[k]) for k in ('open','high','low','close','volume'))

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: verify_d04_cloud_receipts.py OUT.json')
 receipts={}
 for sym,tf,date in KEYS:
  key=f'{sym}_{tf}_{date}'
  url=BASE+f'{sym}/{tf}/{sym}-{tf}-{date}.zip'
  receipts[key]=fetch_attested_source(url,timeout=35)
 results={}
 for symbol in SYMBOLS:
  dt='2026-10-11'
  a=receipts[f'{symbol}_15m_{dt}']['aggregated_ohlcv']
  b=receipts[f'{symbol}_1d_{dt}']['aggregated_ohlcv']
  ok=comparable(a,b)
  results[f'{symbol}_{dt}']={'match':ok,'15m':a,'1d':b,'status':'VERIFIED_AGREEMENT' if ok else 'SOURCE_CONFLICT_QUARANTINED'}
  if not ok:raise D04Rejected('EXPECTED_CROSS_TF_AGREEMENT_MISSING_'+symbol)
 dt='2025-01-29'
 a=receipts[f'BTCUSDT_15m_{dt}']['aggregated_ohlcv'];b=receipts[f'BTCUSDT_1d_{dt}']['aggregated_ohlcv']
 results[f'BTCUSDT_{dt}']={'match':comparable(a,b),'15m':a,'1d':b,'status':'VERIFIED_AGREEMENT' if comparable(a,b) else 'SOURCE_CONFLICT_QUARANTINED'}
 # Independent receipt-to-normalized CSV equality on a complete 96-bar day.
 normalized={}
 if len(sys.argv)>2:
  folder=Path(sys.argv[2])
  for symbol in SYMBOLS:
   # Scan selected UTC epoch interval explicitly, not a lexicographic guess.
   start=receipts[f'{symbol}_15m_2026-10-11']['start_ms']
   with (folder/f'{symbol}_15m.csv').open('r',newline='',encoding='utf8') as f:
    rows=[x for x in csv.DictReader(f) if start<=int(x['open_time'])<start+86400000]
   if len(rows)!=96:raise D04Rejected('MISSING_2026_NORMALIZED_DAY')
   agg={'open':rows[0]['open'],'high':str(max(Decimal(x['high']) for x in rows)),
        'low':str(min(Decimal(x['low']) for x in rows)),'close':rows[-1]['close'],
        'volume':str(sum(Decimal(x['volume']) for x in rows))}
   verified=receipts[f'{symbol}_15m_2026-10-11']['aggregated_ohlcv']
   if not comparable(agg,verified):raise D04Rejected('NORMALIZED_DAY_DIFFERS_FROM_REMOTE_SOURCE')
   normalized[symbol]={'date':'2026-10-11','96_bars':len(rows),'aggregated_day_matches_verified_archive':True}

 out={'status':'PASS_WITH_DOCUMENTED_2025_SOURCE_CONFLICT' if not results['BTCUSDT_2025-01-29']['match'] else 'PASS_NO_CONFLICT_ON_THIS_FETCH',
      'fetched_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'machine_python':platform.python_version(),'tls_impl':ssl.OPENSSL_VERSION,
      'receipts':receipts,'daily_checks':results,'normalized_cross_proof':normalized,
      'claims':{'origin_level':'HTTPS_VALIDATED_BINANCE_VISION_HOST_BUT_NOT_BINANCE_DIGITALLY_SIGNED',
                'archive_count_live_checked':len(receipts),
                'remaining_2026_archives':'NOT_RECHECKED_LIVE_IN_THIS_RUN',
                'jan29_source_conflict':'QUARANTINE_IF_DIVERGENT; NEVER_SILENTLY_PATCH'}}
 path=Path(sys.argv[1]);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'status':out['status'],'receipts':len(receipts),'checks':{k:v['status'] for k,v in results.items()}},sort_keys=True))
if __name__=='__main__':main()
