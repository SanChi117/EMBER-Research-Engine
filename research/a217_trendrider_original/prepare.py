"""Genuine Binance UM only; reuse A203 parser/receipt infrastructure."""
import sys,json,hashlib,calendar
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'native_candidate_screen_20261031'))
from a203_prepare_2025_holdout_source import load_zip,millis
ROOT=Path(sys.argv[1]); OUT=ROOT/'data'/'futures';OUT.mkdir(parents=True,exist_ok=True)
CACHE=ROOT/'cache';CACHE.mkdir(exist_ok=True)
BASE='https://data.binance.vision/data/futures/um/monthly'
def stamp(y,m):return int(datetime(y,m,1,tzinfo=timezone.utc).timestamp()*1000)
START=stamp(2023,1); END=stamp(2026,10)
def fetch(job):
 s,kind,y,m=job; ym=f'{y}-{m:02}'
 tf='1h' if kind=='mark' else kind
 sub='markPriceKlines' if kind=='mark' else 'klines'
 url=f'{BASE}/{sub}/{s}/{tf}/{s}-{tf}-{ym}.zip' if kind!='funding' else f'{BASE}/fundingRate/{s}/{s}-fundingRate-{ym}.zip'
 cp=CACHE/f'{s}-{kind}-{ym}.json'
 if cp.exists(): rows,receipt=json.loads(cp.read_text())
 else:
  rows,receipt=load_zip(url);cp.write_text(json.dumps([rows,receipt]))
 vals=[]
 if kind=='funding':
  h=[x.lower().replace('_','') for x in rows[0]];ti=h.index('calctime');ri=h.index('lastfundingrate')
  vals=[[millis(r[ti]),float(r[ri])] for r in rows[1:] if r]
 else:
  for r in rows:
   if not r or not r[0].isdigit():continue
   t=millis(r[0]);o,h,l,c,v=map(float,r[1:6]);assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0
   vals.append([t,o,h,l,c,v])
 return job, vals, receipt
jobs=[(s,k,y,m) for s in ('BTCUSDT','ETHUSDT','SOLUSDT','LINKUSDT') for k in ('1h','1d','5m','mark','funding') for y in range(2023,2027) for m in range(1,13) if (y,m)<(2026,10) and (k not in ('5m','mark','funding') or y>=2024)]
allrows={};receipts={}
with ThreadPoolExecutor(max_workers=16) as ex:
 for i,f in enumerate(as_completed([ex.submit(fetch,j) for j in jobs])):
  j,rows,receipt=f.result();s,k,y,m=j;allrows.setdefault((s,k),[]).extend(rows);receipts['/'.join(map(str,j))]=receipt
  if i%50==0:print('DOWNLOADED',i+1,'/',len(jobs),flush=True)
manifest={'source_receipts':receipts,'files':{},'limitations':['historical spread/orderbook unavailable','funding settlement subsecond timestamp floored to hour for native Freqtrade accounting']}
for (s,k),rows in allrows.items():
 rows.sort(key=lambda r:r[0]);step={'1h':3600000,'1d':86400000,'5m':300000,'mark':3600000}.get(k)
 begin=START if k in ('1h','1d') else stamp(2024,1)
 if k=='funding':
  fixed={}
  for t,v in rows:
   assert t%3600000<=1000 and (t//3600000)*3600000 not in fixed
   fixed[t//3600000*3600000]=v
  rows=[[t,*([fixed.get(t,0.)]*4),0.] for t in range(begin,END,3600000)]
 else:
  idx={r[0]:r for r in rows}; assert len(idx)==len(rows)
  missing=set(range(begin,END,step))-set(idx)
  if missing and k=='mark':
   for day in sorted({datetime.fromtimestamp(t/1000,timezone.utc).strftime('%Y-%m-%d') for t in missing}):
    u=f'https://data.binance.vision/data/futures/um/daily/markPriceKlines/{s}/1h/{s}-1h-{day}.zip'
    raw,rec=load_zip(u);receipts[s+'/daily/'+day]=rec
    for r in raw:
     if r and r[0].isdigit():
      t=millis(r[0]);v=[t,*map(float,r[1:6])]
      if t in idx:assert idx[t]==v
      else:idx[t]=v
   rows=[idx[t] for t in sorted(idx)]
  assert [r[0] for r in rows]==list(range(begin,END,step)),('GAP',s,k,len(missing))
 name=s[:-4]+'_USDT_USDT-'+({'mark':'1h-mark','funding':'1h-funding_rate'}.get(k,k+'-futures'))+'.json'
 b=json.dumps(rows,separators=(',',':')).encode();(OUT/name).write_bytes(b);manifest['files'][name]={'sha256':hashlib.sha256(b).hexdigest(),'n':len(rows)}
 if k=='1h':
  agg=[]
  for i in range(0,len(rows),4):
   r=rows[i:i+4]; assert len(r)==4 and r[0][0]%(4*3600000)==0
   agg.append([r[0][0],r[0][1],max(v[2] for v in r),min(v[3] for v in r),r[-1][4],sum(v[5] for v in r)])
  name=s[:-4]+'_USDT_USDT-4h-futures.json';b=json.dumps(agg,separators=(',',':')).encode();(OUT/name).write_bytes(b);manifest['files'][name]={'sha256':hashlib.sha256(b).hexdigest(),'n':len(agg),'derived':'closed UTC groups of four genuine 1h bars'}
(ROOT/'source_manifest.json').write_text(json.dumps(manifest,indent=2));print('DATA_COMPLETE',flush=True)
