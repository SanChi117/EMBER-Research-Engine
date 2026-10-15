#!/usr/bin/env python3
"""C08 independent FULL historical Binance USD-M source attestation.

Read the FROZEN original normalized history + manifest, request each listed ZIP
and its .CHECKSUM from Binance Vision over constrained TLS, compare ALL columns
(excluding raw "ignore") of EACH authenticated raw row against its normalized
Futures row. This does not change either input, does not trade, and never treats
manifest self-consistency as source proof. PAPER / research only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import ssl
import time
import urllib.request
import urllib.parse
import zipfile
from collections import Counter
from decimal import Decimal

ROOT=pathlib.Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'tools'))
from strict_vision_d04 import (
    D04Rejected, _SingleHostRedirect, parse_url, verify_raw_zip,
    verify_offline_consolidated_manifest
)

SYMBOLS=('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT')
NORMALIZED=('open_time','open','high','low','close','volume','close_time',
            'quote_volume','trades','taker_buy_base_volume','taker_buy_quote_volume')
PERIOD_MS={'15m':900_000,'1d':86_400_000}
MAX_ZIP=25_000_000
RETRYABLE=(TimeoutError,ConnectionError,OSError)
CURRENT_FROZEN_ARCHIVES=315

def unique_declared_sources(manifest):
    if not isinstance(manifest,list):
        raise D04Rejected('INVALID_MANIFEST')
    indexed={}
    for item in manifest:
        if not isinstance(item,dict) or not {'symbol','tf','sources'}<=set(item):
            raise D04Rejected('INVALID_MANIFEST_RECORD')
        for entry in item['sources']:
            url=entry['url']
            desc=parse_url(url)
            if (desc['symbol'],desc['tf'])!=(item['symbol'],item['tf']):
                raise D04Rejected('MANIFEST_SOURCE_SERIES_MISMATCH')
            if url in indexed:
                raise D04Rejected('DUPLICATE_SOURCE_URL')
            if entry['rows']!=desc['expected_rows']:
                raise D04Rejected('WRONG_MANIFEST_SOURCE_ROWS')
            indexed[url]=dict(entry)
    return indexed

def load_normalized_rows(history_dir,symbol,tf):
    path=pathlib.Path(history_dir)/f'{symbol}_{tf}.csv'
    with path.open(encoding='utf-8-sig',newline='') as handle:
        rows={}
        for row in csv.DictReader(handle):
            if row.get('symbol')!=symbol:
                raise D04Rejected('NORMALIZED_SYMBOL_MISMATCH')
            key=int(row['open_time'])
            if key in rows:
                raise D04Rejected('NORMALIZED_DUPLICATE_TIME')
            rows[key]=row
    return rows

def checked_download(url,max_bytes,timeout):
    # Reuse the audited D04 redirect boundary and parse_url whitelist.
    base=url[:-9] if url.endswith('.CHECKSUM') else url
    parse_url(base)
    if url not in (base,base+'.CHECKSUM'):
        raise D04Rejected('UNSAFE_D04_DOWNLOAD_PATH')
    opener=urllib.request.build_opener(_SingleHostRedirect())
    request=urllib.request.Request(url,headers={'User-Agent':'EMBER-C08-source-audit/1.0'})
    with opener.open(request,timeout=timeout) as response:
        parsed=urllib.parse.urlsplit(response.geturl())
        if parsed.scheme!='https' or parsed.netloc!='data.binance.vision':
            raise D04Rejected('UNTRUSTED_FINAL_DOWNLOAD')
        payload=response.read(max_bytes+1)
    if len(payload)>max_bytes:
        raise D04Rejected('OVERSIZE_SOURCE_DOWNLOAD')
    return payload

def compare_verified_archive(url,zip_bytes,checksum_bytes,declared,normalized):
    """Independent full row-by-row check. verify_raw_zip is C07's existing oracle."""
    verified=verify_raw_zip(url,zip_bytes,checksum_bytes)
    if declared['sha256'].lower()!=verified['zip_sha256']:
        raise D04Rejected('LOCAL_MANIFEST_ZIP_SHA_DIFFERENCE')
    source=parse_url(url)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        with archive.open(source['filename'][:-4]+'.csv') as f:
            text=io.TextIOWrapper(f,encoding='utf-8-sig',newline='')
            reader=csv.reader(text)
            count=0
            for raw in reader:
                if count==0 and raw[0].lower()=='open_time':
                    continue
                timestamp=int(raw[0])
                dest=normalized.get(timestamp)
                if dest is None:
                    raise D04Rejected('SOURCE_BAR_NOT_IN_NORMALIZED')
                for idx,name in enumerate(NORMALIZED):
                    if idx in (0,6,8):
                        try:matched=int(raw[idx])==int(dest[name])
                        except (ValueError,TypeError):matched=False
                    else:
                        try:matched=Decimal(raw[idx])==Decimal(dest[name])
                        except (ValueError,TypeError):matched=False
                    if not matched:
                        raise D04Rejected('SOURCE_NORMALIZED_COLUMN_MISMATCH',
                                          f'{timestamp}:{name}')
                count+=1
    if count!=verified['bars'] or count!=declared['rows']:
        raise D04Rejected('SOURCE_ROWS_DIFFER')
    return {
        'url':url,'status':'HTTPS_CHECKSUM_AND_ALL_COLUMNS_REPLAYED',
        'symbol':source['symbol'],'tf':source['tf'],
        'rows':count,'raw_csv_sha256':verified['raw_csv_sha256'],
        'zip_sha256':verified['zip_sha256'],
        'normalized_all_11_columns_matched':True,
        'origin_limit':'TLS+same-host-CHECKSUM—not a digital signature'
    }

def audit(history_dir,output_path,symbol=None,offline_only=False,
          max_sources=None,timeout=35,retries=1):
    history_dir=pathlib.Path(history_dir)
    offline=verify_offline_consolidated_manifest(history_dir)
    manifest=json.loads((history_dir/'manifest_vision.json').read_text(encoding='utf8'))
    indexed=unique_declared_sources(manifest)
    if len(indexed)!=CURRENT_FROZEN_ARCHIVES:
        raise D04Rejected('UNEXPECTED_DECLARED_ARCHIVE_COUNT',str(len(indexed)))
    selected=[(url,value) for url,value in sorted(indexed.items())
              if symbol is None or parse_url(url)['symbol']==symbol]
    if max_sources is not None:
        selected=selected[:max_sources]
    normalized={}
    records=[]
    for i,(url,declared) in enumerate(selected,1):
        desc=parse_url(url)
        if not offline_only:
            slot=(desc['symbol'],desc['tf'])
            if slot not in normalized:
                normalized[slot]=load_normalized_rows(history_dir,*slot)
            result=None
            for attempt in range(retries+1):
                try:
                    checksum=checked_download(url+'.CHECKSUM',1024,timeout)
                    raw=checked_download(url,MAX_ZIP,timeout)
                    result=compare_verified_archive(
                        url,raw,checksum,declared,normalized[slot])
                    break
                except Exception as exc:
                    # Genuine data/content mismatches are quarantine, NOT retried.
                    if isinstance(exc,D04Rejected):
                        result={'url':url,'status':'QUARANTINED','error':exc.code,
                                'detail':str(exc),'symbol':desc['symbol'],'tf':desc['tf']}
                        break
                    if isinstance(exc,RETRYABLE) and attempt<retries:
                        time.sleep(min(2**attempt,4))
                        continue
                    result={'url':url,'status':'NOT_ATTESTED_NETWORK_FAILURE',
                            'error':type(exc).__name__,'detail':str(exc),
                            'symbol':desc['symbol'],'tf':desc['tf']}
                    break
            assert result is not None
        else:
            result={'url':url,'status':'DECLARED_NOT_ATTESTED_OFFLINE_ONLY',
                    'symbol':desc['symbol'],'tf':desc['tf']}
        records.append(result)
        print(f'{i}/{len(selected)} {desc["symbol"]} {desc["tf"]} '
              f'{result["status"]}',flush=True)
    tallies=dict(sorted(Counter(z['status'] for z in records).items()))
    full=len(selected)==CURRENT_FROZEN_ARCHIVES
    attested=sum(x['status']=='HTTPS_CHECKSUM_AND_ALL_COLUMNS_REPLAYED'
                 for x in records)
    verdict=('FULL_ARCHIVE_ATTESTATION_PASS'
             if full and attested==CURRENT_FROZEN_ARCHIVES else
             'PARTIAL_OR_QUARANTINED_NOT_CERTIFIED')
    output={
        'version':'C08_FULL_HISTORY_ATTESTATION_V1',
        'run_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'data_market':'BINANCE_USDM_FUTURES_ONLY',
        'tls':ssl.OPENSSL_VERSION,
        'full_manifest_declared':len(indexed),
        'selected_sources':len(selected),
        'verified_source_archives':attested,
        'full_coverage':full,
        'offline_integrity_scope':{'series':offline['series_verified'],
                                   'bars':offline['total_bars']},
        'verdict':verdict,'statuses':tallies,
        'receipts':records,'limitations':[
            'Same-host CHECKSUM is not an independent digital signature.',
            'Local manifest integrity alone is not Binance origin proof.',
            'No Spot fallback, no candle modifications.',
            'Incomplete, failed, or quarantined archive stops full certification.'
        ]
    }
    output_path=pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(output,sort_keys=True,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'verdict':verdict,'sources':len(selected),
                      'attested':attested,'counts':tallies},sort_keys=True))
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument('history_dir')
    p.add_argument('output_json')
    p.add_argument('--symbol',choices=SYMBOLS)
    p.add_argument('--offline-only',action='store_true')
    p.add_argument('--max-sources',type=int)
    p.add_argument('--timeout',type=int,default=35)
    p.add_argument('--retries',type=int,default=1)
    a=p.parse_args()
    result=audit(a.history_dir,a.output_json,
                 a.symbol,a.offline_only,a.max_sources,a.timeout,a.retries)
    # Fail CLOSED in full/online production mode. In partial shard mode
    # permit PASS only if all *selected* sources were attested.
    if a.offline_only:
        return 0
    return 0 if (result['verified_source_archives']==result['selected_sources']
                 and result['selected_sources']>0) else 1

if __name__=='__main__':
    raise SystemExit(main())
