#!/usr/bin/env python3
"""Merge C08 sharded receipts without upgrading an incomplete result to PASS."""
import argparse
import datetime as dt
import json
from pathlib import Path

EXPECTED=315
SYMBOLS={'BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT'}
OK='HTTPS_CHECKSUM_AND_ALL_COLUMNS_REPLAYED'

def summarize(paths):
    if len(paths)!=len(SYMBOLS):
        raise ValueError('MISSING_C08_SYMBOL_SHARD')
    shards=[json.loads(Path(x).read_text(encoding='utf8')) for x in paths]
    sources={};shard_symbols=set();duplicate=[]
    for s in shards:
        if s['full_manifest_declared']!=EXPECTED:
            raise ValueError('UNEXPECTED_C08_MANIFEST_TOTAL')
        if s['data_market']!='BINANCE_USDM_FUTURES_ONLY':
            raise ValueError('NOT_USDM_FUTURES')
        unique_symbols={v['symbol'] for v in s['receipts']}
        if len(unique_symbols)!=1:
            raise ValueError('MIXED_C08_SHARD')
        symbol=next(iter(unique_symbols))
        if symbol in shard_symbols:raise ValueError('DUPLICATE_C08_SHARD')
        shard_symbols.add(symbol)
        if len(s['receipts'])!=s['selected_sources']:
            raise ValueError('SHARD_RECEIPT_COUNT_MISMATCH')
        for receipt in s['receipts']:
            key=receipt['url']
            if key in sources:duplicate.append(key)
            sources[key]=receipt
    if shard_symbols!=SYMBOLS:
        raise ValueError('INCOMPLETE_SYMBOL_SET')
    if duplicate:
        raise ValueError('DUPLICATE_SOURCE_URLS_ACROSS_SHARDS')
    counts={}
    for record in sources.values():
        st=record['status'];counts[st]=counts.get(st,0)+1
    verified=counts.get(OK,0)
    full=(len(sources)==EXPECTED and verified==EXPECTED and
          all(x.get('normalized_all_11_columns_matched',False) for x in sources.values()))
    return {
        'audit':'C08_INDEPENDENT_BINANCE_VISION_2026_FUTURES',
        'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'manifest_expected':EXPECTED,'unique_sources':len(sources),
        'verified_archives':verified,'result':'FULL_315_ATTESTED' if full else 'NOT_FULLY_ATTESTED',
        'statuses':dict(sorted(counts.items())),
        'sources_by_symbol':{sym:sum(r['symbol']==sym for r in sources.values()) for sym in sorted(SYMBOLS)},
        'quarantined_or_unverified_urls':[
            k for k,v in sorted(sources.items()) if v['status']!=OK],
        'limits':'HTTPS TLS + same-host checksum is not a third-party signed origin. No Spot, no mutation, PAPER only.'
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument('output_json')
    p.add_argument('input_json',nargs='+')
    args=p.parse_args()
    out=summarize(args.input_json)
    path=Path(args.output_json)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print(json.dumps({k:out[k] for k in ('result','unique_sources','verified_archives','statuses')},sort_keys=True))
    return 0 if out['result']=='FULL_315_ATTESTED' else 1

if __name__=='__main__':raise SystemExit(main())
