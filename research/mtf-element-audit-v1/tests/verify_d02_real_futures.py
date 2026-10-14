#!/usr/bin/env python3
"""D02 verification over frozen USD-M artifact; independent arithmetic cross-check.

No trading setup/PnL. Provenance is inherited from previous D01 SHA manifest
and remains delegated to D04. Native 1h/4h/1w exchange bars NOT in artifact.
"""
import argparse,hashlib,io,json,pathlib,sys,zipfile,csv
from decimal import Decimal as D
from collections import defaultdict
from tempfile import TemporaryDirectory
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from strict_bar_closed import Provenance,read_closed_bars,TF_MS,UTC_WEEK_ANCHOR_MS
from strict_tf_d02 import snapshot_htf,native_snapshot,confirmed_pivots
ASOF=1791849600000  # 2026-10-13T00:00:00Z; checked below to avoid stale constant
from datetime import datetime,timezone
ASOF=int(datetime(2026,10,13,tzinfo=timezone.utc).timestamp()*1000)
SYMS=['BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT']

def run(archive):
    result={'cycle':'C05','component':'D02','as_of_utc':'2026-10-13T00:00:00Z','symbols':SYMS,'per_symbol':[],
            'invariants':{'future_looks':0,'daily_15m_vs_native':0,'weekly_15m_vs_native_1d':0,
                          'hours_1h_independent':0,'hours_4h_independent':0}}
    with zipfile.ZipFile(archive) as z:
        paths={pathlib.PurePosixPath(p).name:p for p in z.namelist() if '/data/history/' in p and p.endswith(('.csv','manifest_vision.json'))}
        source_map={(r['symbol'],r['tf']):r for r in json.loads(z.read(paths['manifest_vision.json']))}
        for symbol in SYMS:
            raw={}; parsed={}
            for tf in ('15m','1d'):
                data=z.read(paths[f'{symbol}_{tf}.csv']);meta=source_map[(symbol,tf)]
                digest=hashlib.sha256(data).hexdigest()
                assert digest==meta['sha256'], 'Original checksum mismatch'
                assert all('/futures/um/' in e['url'] for e in meta['sources'])
                with TemporaryDirectory() as tmp:
                    p=pathlib.Path(tmp)/f'{symbol}_{tf}.csv';p.write_bytes(data)
                    parsed[tf]=read_closed_bars(p,Provenance('BINANCE','FUTURES_UM',symbol,tf,
                                  'fixed prior Vision artifact - D04 still separate',digest),as_of_utc=ASOF)
                raw[tf]=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
            r15=parsed['15m']; native=parsed['1d'];
            s1h=snapshot_htf(r15,'1h',as_of_utc=ASOF)
            s4h=snapshot_htf(r15,'4h',as_of_utc=ASOF)
            s1d=snapshot_htf(r15,'1d',as_of_utc=ASOF)
            s1w=snapshot_htf(r15,'1w',as_of_utc=ASOF)
            wday=snapshot_htf(native,'1w',as_of_utc=ASOF)
            native_by={b.open_at_ms:b for b in native}
            for d in s1d.bars:
                n=native_by[d.open_at_ms]
                assert (d.open,d.high,d.low,d.close,d.volume)==(n.open,n.high,n.low,n.close,n.volume),'daily data mismatch'
                result['invariants']['daily_15m_vs_native']+=1
            weekly_by={b.open_at_ms:b for b in wday.bars}
            for w in s1w.bars:
                ref=weekly_by[w.open_at_ms]
                assert (w.open,w.high,w.low,w.close,w.volume)==(ref.open,ref.high,ref.low,ref.close,ref.volume),'weekly daily-derived mismatch'
                result['invariants']['weekly_15m_vs_native_1d']+=1
            # Independently calculate native 1H/4H aggregates using raw CSV,
            # independent of D01/D02 object / helper implementations.
            for tf,snap in [('1h',s1h),('4h',s4h)]:
                buckets=defaultdict(list);p=TF_MS[tf]
                for row in raw['15m']:
                    t=int(row['open_time']);k=(t//p)*p
                    buckets[k].append(row)
                for bar in snap.bars:
                    rows=buckets[bar.open_at_ms]
                    count=p//TF_MS['15m']
                    assert len(rows)==count and int(rows[0]['open_time'])==bar.open_at_ms
                    assert int(rows[-1]['close_time'])+1==bar.close_exclusive_ms
                    assert (D(rows[0]['open']),max(D(q['high']) for q in rows),
                            min(D(q['low']) for q in rows),D(rows[-1]['close']),
                            sum((D(q['volume']) for q in rows),D(0)))==(
                                bar.open,bar.high,bar.low,bar.close,bar.volume),'independent '+tf+' mismatch'
                    result['invariants']['hours_'+tf+'_independent']+=1
            # Adversarial future modifications: changing ALL later prices after
            # an earlier as-of time cannot change its snapshot or pivot list.
            early_asof=r15[96].close_exclusive_ms
            orig=snapshot_htf(r15,'1h',as_of_utc=early_asof)
            from dataclasses import replace
            changed=list(r15)
            for i in range(100,len(changed),251):
                changed[i]=replace(changed[i],high=D('9999999999'),volume=D('7777777'))
            rerun=snapshot_htf(changed,'1h',as_of_utc=early_asof)
            assert orig==rerun and confirmed_pivots(orig,left=2,right=2)==confirmed_pivots(rerun,left=2,right=2)
            result['invariants']['future_looks']+=1
            result['per_symbol'].append({'symbol':symbol,'raw_15m':len(r15),'native_1d':len(native),
                'derived_1h':len(s1h.bars),'derived_4h':len(s4h.bars),'derived_1d':len(s1d.bars),'derived_1w':len(s1w.bars),
                'partial_week_first':s1w.leading_partial_buckets,'partial_week_last':s1w.trailing_partial_buckets,
                'first_week_open_at_ms':s1w.bars[0].open_at_ms,'last_week_closed_at_ms':s1w.bars[-1].close_exclusive_ms,
                'future_data_cannot_change_past':True})
    result['status']='VERIFIED_FORMAL_D02_ON_EXISTING_2026_FUTURES_RECORDS'
    result['limitations']=['1h/4h are checked against separate arithmetic from raw 15m, not native exchange 1h/4h.',
       '1w is checked against independently aggregated native 1d, not exchange-native 1w.',
       'No real 3m/5m source candles were available in fixed history; synthetic tests only.',
       'Actual point-in-time exchange publish latency/finalization not proven by the as-of bar-end convention.',
       'Provenance D04, semantic pivot StrongHL/IDM and strategy accuracy not verified.']
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();res=run(a.archive)
    pathlib.Path(a.out).write_text(json.dumps(res,sort_keys=True,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(res['status'],res['invariants'],[(x['derived_1h'],x['derived_4h'],x['derived_1d'],x['derived_1w']) for x in res['per_symbol']])
