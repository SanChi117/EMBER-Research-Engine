"""Independent 2026 USD-M D01 acceptance. Excludes all trade/PnL signals.

Reads existing immutable Binance Vision evidence artifact, requiring exact
CSV digests recorded before this cycle. Performs an additional row-level
scan independent of strict_bar_closed module, plus cross-timeframe OHLCV.
No network or secret access.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, pathlib, sys, zipfile
from decimal import Decimal
from datetime import datetime, timezone
from collections import defaultdict
from tempfile import TemporaryDirectory
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from strict_bar_closed import Provenance,read_closed_bars,TF_MS
SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT')
AS_OF=int(datetime(2026,10,13,tzinfo=timezone.utc).timestamp()*1000)

def run(archive):
    result={'audit':'D01_FUTURES_2026_20261014','rules':'frozen from previously verified manifest','as_of_utc':'2026-10-13T00:00:00Z','files':[], 'daily_overlap_checked':0,'daily_volume_discrepancies':0}
    with zipfile.ZipFile(archive) as z:
        paths={pathlib.PurePosixPath(n).name:n for n in z.namelist() if '/data/history/' in n and n.endswith(('.csv','manifest_vision.json'))}
        manifest=json.loads(z.read(paths['manifest_vision.json']))
        assert len(manifest)==10, 'unexpected manifest length'
        info={(row['symbol'],row['tf']):row for row in manifest}
        parsed={}
        for symbol in SYMBOLS:
            for tf in ('15m','1d'):
                meta=info[(symbol,tf)]
                filename=f'{symbol}_{tf}.csv';body=z.read(paths[filename]);digest=hashlib.sha256(body).hexdigest()
                assert digest==meta['sha256'], f'prior-manifest digest mismatch {symbol}/{tf}'
                assert all('/futures/um/' in src['url'] for src in meta['sources']), f'source cross-market {symbol}/{tf}'
                with TemporaryDirectory() as temp:
                    p=pathlib.Path(temp)/filename;p.write_bytes(body)
                    bs=read_closed_bars(p,Provenance('BINANCE','FUTURES_UM',symbol,tf,
                        'prior frozen Vision manifest, D04 authenticity delegated',digest),as_of_utc=AS_OF)
                assert len(bs)==meta['candles'],f'count mismatch {symbol}/{tf}'
                assert len(bs)==(18720 if tf=='15m' else 1016),'unexpected calendar window'
                # Independent raw cursor, distinct from D01 parser: verify every open/close
                # directly from CSV; and volumes matched as exact decimal values.
                rows=list(csv.DictReader(io.StringIO(body.decode('utf-8-sig'))))
                assert len(rows)==len(bs)
                a=int(rows[0]['open_time']);last=-1
                independent_volume=Decimal('0')
                for i,row in enumerate(rows):
                    t=int(row['open_time']); ct=int(row['close_time'])
                    assert t==a+i*TF_MS[tf] and ct==t+TF_MS[tf]-1, 'independent cursor fail'
                    assert t>last and t+TF_MS[tf]<=AS_OF,'independent ordering/asof fail'
                    independent_volume+=Decimal(row['volume']);last=t
                assert independent_volume==sum((b.volume for b in bs),Decimal('0'))
                result['files'].append({'symbol':symbol,'timeframe':tf,'bars':len(bs),
                    'first_ms':bs[0].open_at_ms,'last_end_exclusive_ms':bs[-1].close_exclusive_ms,
                    'sha256':digest,'independent_cursor':'PASS','D01_contract':'PASS'})
                parsed[(symbol,tf)]=bs
        # 15m/daily agreement only on days fully covered by 15m sample.
        for symbol in SYMBOLS:
            b15=parsed[(symbol,'15m')];d1={b.open_at_ms:b for b in parsed[(symbol,'1d')]}
            grouped=defaultdict(list)
            for b in b15:grouped[b.open_at_ms//TF_MS['1d']*TF_MS['1d']].append(b)
            for day,parts in grouped.items():
                assert len(parts)==96 and day in d1, 'missing full UTC day'
                daily=d1[day]
                assert parts[0].open==daily.open and parts[-1].close==daily.close
                assert max(x.high for x in parts)==daily.high and min(x.low for x in parts)==daily.low
                assert sum((x.volume for x in parts),Decimal('0'))==daily.volume, 'volume mismatch'
                result['daily_overlap_checked']+=1
        result['total_15m_bars']=sum(f['bars'] for f in result['files'] if f['timeframe']=='15m')
        result['total_1d_bars']=sum(f['bars'] for f in result['files'] if f['timeframe']=='1d')
        result['result']='VERIFIED_FORMAL_D01_SCHEMA_AND_ASOF_ON_DECLARED_VISION_HISTORY'
        result['limitations']=['Authenticity of Vision .CHECKSUM depends on external D04 gate; D01 only verifies local digest against frozen manifest.',
         'No semantic trading setup inference; no PnL evaluation.',
         'Not a guarantee against later source replacement outside immutable archived bytes.']
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True)
    args=p.parse_args();r=run(args.archive)
    pathlib.Path(args.out).write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
    print(r['result'],'files',len(r['files']),'15m',r['total_15m_bars'],'1d',r['total_1d_bars'],'daily_overlap',r['daily_overlap_checked'])