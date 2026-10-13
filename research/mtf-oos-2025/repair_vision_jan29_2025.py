#!/usr/bin/env python3
"""Fix a documented Binance Vision MONTHLY 15m / DAILY 1d archive conflict.

STRICT and NARROW: only 2025-01-29, only 5 declared symbols, only if daily
Binance Vision ZIP (independent .CHECKSUM) matches native 1d OHLC+volume.
No strategy code changes. Fail closed if any additional mismatch is present.
The correction runs before signals/PnL; prior original corpus is immutable in
GitHub Actions artifact 38482979222. No live orders.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,tempfile
from pathlib import Path
from datetime import datetime,timezone
from get_history import save,HEADER
from get_history_vision import archive

SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT')
DAY=1738108800000 # 2025-01-29 UTC
DAY_MS=86400000
STEP=900000

def read_raw(p):
    with Path(p).open(newline='',encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    if set(HEADER).difference(rows[0] if rows else {}):raise ValueError('Unknown Binance OHLCV CSV header')
    return rows

def same_price(a,b):
    return all(math.isclose(float(a[k]),float(b[k]),rel_tol=1e-7,abs_tol=1e-7)
               for k in ('open','high','low','close'))

def by_day(rows):
    ans={}
    for z in rows:
        dt=int(z['open_time'])//DAY_MS*DAY_MS
        ans.setdefault(dt,[]).append(z)
    return ans

def conflicting_dates(daily,quarter):
    daily_by_start={int(x['open_time']):x for x in daily}
    issues=[]
    for t,arr in by_day(quarter).items():
        d=daily_by_start.get(t)
        if not d:raise ValueError('Missing native 1d day')
        if len(arr)!=96:raise ValueError('Incomplete UTC 15m candles')
        derived=dict(open=arr[0]['open'],high=str(max(float(x['high']) for x in arr)),
                     low=str(min(float(x['low']) for x in arr)),close=arr[-1]['close'])
        if not same_price(derived,d):raise ValueError('15m vs 1d OHLC mismatch '+str(t))
        vol=sum(float(z['volume']) for z in arr)
        if not math.isclose(vol,float(d['volume']),rel_tol=1e-5,abs_tol=1e-6):issues.append(t)
    return sorted(issues)

def validate_override(archive_rows,native):
    if len(archive_rows)!=96:raise ValueError('Daily Vision override must contain exactly 96 quarters')
    times=[int(z[0]) for z in archive_rows]
    if times!=[DAY+i*STEP for i in range(96)]:raise ValueError('Correction is not contiguous 2025-01-29 15m')
    asdict=[dict(zip(HEADER[:11],z)) for z in archive_rows]
    if not same_price({'open':asdict[0]['open'],'high':str(max(float(x['high']) for x in asdict)),
        'low':str(min(float(x['low']) for x in asdict)),'close':asdict[-1]['close']},native):
        raise ValueError('Daily Vision 15m prices do not agree with independently archived native 1d')
    volume=sum(float(x['volume']) for x in asdict)
    if not math.isclose(volume,float(native['volume']),rel_tol=1e-5,abs_tol=1e-6):
        raise ValueError('Daily Vision override volume still differs from native 1d')
    return volume

def run(data_dir,out):
    p=Path(data_dir);out=Path(out)
    manifest=json.loads((p/'manifest_vision.json').read_text(encoding='utf-8'))
    if not isinstance(manifest,list) or len(manifest)!=10:raise ValueError('Expected original 10-file verified VISION manifest')
    index={(x['symbol'],x['tf']):x for x in manifest}
    staged={};evidence={}
    for symbol in SYMBOLS:
        quarter=read_raw(p/f'{symbol}_15m.csv');native=read_raw(p/f'{symbol}_1d.csv')
        date_issues=conflicting_dates(native,quarter)
        if date_issues!=[DAY]:raise ValueError('Monthly/native 1d conflicts are NOT precisely Jan 29 '+symbol+': '+repr(date_issues))
        original_sha=hashlib.sha256((p/f'{symbol}_15m.csv').read_bytes()).hexdigest()
        rec=index[(symbol,'15m')]
        if original_sha!=rec['sha256']:raise ValueError('Source manifest mismatch before correction')
        rows,src=archive(symbol,'15m','2025-01',daily='2025-01-29')  # checks official .CHECKSUM
        d=next(x for x in native if int(x['open_time'])==DAY)
        newvol=validate_override(rows,d)
        original=[x for x in quarter if DAY<=int(x['open_time'])<DAY+DAY_MS]
        updates=[dict(zip(HEADER[:11],z),symbol=symbol) for z in rows]
        if any(not same_price(a,b) for a,b in zip(original,updates)):
            raise ValueError('Price difference on Jan 29; refusing revision without manual audit')
        bytime={int(x['open_time']):x for x in updates}
        corrected=[bytime.get(int(x['open_time']),x) for x in quarter]
        if conflicting_dates(native,corrected):raise ValueError('Post-override must reconcile ALL 365 days '+symbol)
        staged[symbol]=corrected
        evidence[symbol]={
          'fixed_day':'2025-01-29','monthly_total_volume':round(sum(float(x['volume']) for x in original),9),
          'official_vision_daily_volume':round(newvol,9),
          'native_daily_volume':float(d['volume']),
          'modified_quarters':sum(a['volume']!=b['volume'] for a,b in zip(original,updates)),
          'source_manifest_sha256_original':original_sha,
          'new_source':{**src,'rows':len(rows)},
          'reason':'Official monthly 15m archive differs on one day from native 1d; official DAILY 15m zip plus CHECKSUM resolves discrepancy',
        }
    # Two-phase: no original gets modified until all five source/volume checks pass.
    with tempfile.TemporaryDirectory(prefix='mtf_vision_qa_') as tmp:
        temp=Path(tmp)
        for symbol,corrected in staged.items():
            digest=save([[z.get(k,'') for k in HEADER] for z in corrected],temp/f'{symbol}_15m.csv')
            evidence[symbol]['corrected_csv_sha256']=digest
            index[(symbol,'15m')]['sha256']=digest
            index[(symbol,'15m')]['corrections']=[evidence[symbol]]
            index[(symbol,'15m')]['sources'].append(evidence[symbol]['new_source'])
        # Recheck corrected staged files match the immutable native archive.
        for symbol in SYMBOLS:
            if conflicting_dates(read_raw(p/f'{symbol}_1d.csv'),read_raw(temp/f'{symbol}_15m.csv')):
                raise ValueError('Staged validation mismatch')
        for symbol in SYMBOLS:os.replace(temp/f'{symbol}_15m.csv',p/f'{symbol}_15m.csv')
    (p/'manifest_vision.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    out.parent.mkdir(parents=True,exist_ok=True)
    result={'status':'OFFICIAL_DAILY_VISION_CORRECTION_VERIFIED',
            'data_market':'Binance Futures USD-M','day':'2025-01-29','all_other_days_untouched':True,
            'no_trading_logic_change':True,'source':'original monthly + independent verified daily .zip.CHECKSUM',
            'coins':evidence}
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    pa=argparse.ArgumentParser()
    pa.add_argument('--data-dir',default='data/oos_2025')
    pa.add_argument('--out',default='results_05/JAN29_DATA_QA.json')
    args=pa.parse_args();print(run(args.data_dir,args.out)['status'])