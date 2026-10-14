#!/usr/bin/env python3
"""D04: Binance USDⓈ-M Futures provenance gate (PAPER research only).

Proofs are tiered: local SHA + URL-shaped manifest is INTEGRITY_ONLY;
HTTPS download from allowlisted Binance Vision host with valid TLS plus paired
.CHECKSUM and ZIP-content checks is SOURCE_ATTESTED_AT_FETCH_TIME.
A .CHECKSUM is NOT a signature and cannot prevent same-origin compromise.
"""
from __future__ import annotations
import calendar,csv,hashlib,io,json,re,urllib.parse,urllib.request,zipfile
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path

HOST='data.binance.vision'
SYMBOL=re.compile(r'[A-Z0-9]{4,30}\Z')
SHA=re.compile(r'[0-9a-f]{64}\Z')
ARCHIVE=re.compile(r'(?P<symbol>[A-Z0-9]{4,30})-(?P<tf>15m|1d)-(?P<date>20\d\d-\d\d(?:-\d\d)?)\.zip\Z')
PERIOD={'15m':900_000,'1d':86_400_000}
NORMALIZED=('open_time','open','high','low','close','volume','close_time','quote_volume','trades','taker_buy_base_volume','taker_buy_quote_volume','symbol')

class D04Rejected(ValueError):
    def __init__(self,code,detail=''):
        self.code=code
        super().__init__(code+((': '+str(detail)) if detail else ''))

def digest(data):return hashlib.sha256(data).hexdigest()

def parse_url(url):
    if not isinstance(url,str):raise D04Rejected('BAD_SOURCE_URL')
    u=urllib.parse.urlsplit(url)
    if u.scheme!='https' or u.netloc!=HOST or u.query or u.fragment or u.username or u.password:
        raise D04Rejected('UNTRUSTED_SOURCE_OR_PROTOCOL')
    if '\\' in u.path or '%' in u.path or '//' in u.path:
        raise D04Rejected('UNSAFE_URL_PATH')
    bits=u.path.split('/')
    if len(bits)!=9 or bits[:4]!=['','data','futures','um'] or bits[4] not in ('daily','monthly') or bits[5]!='klines':
        raise D04Rejected('WRONG_MARKET_OR_FILE_TYPE')
    gran,symbol,tf,filename=bits[4],bits[6],bits[7],bits[8]
    m=ARCHIVE.fullmatch(filename)
    if not m or not SYMBOL.fullmatch(symbol) or m['symbol']!=symbol or m['tf']!=tf:
        raise D04Rejected('SYMBOL_OR_TF_MISMATCH')
    value=m['date']
    if len(value)!=(10 if gran=='daily' else 7):raise D04Rejected('DATE_GRANULARITY_MISMATCH')
    try:
        d=datetime.strptime(value,'%Y-%m-%d' if gran=='daily' else '%Y-%m').replace(tzinfo=timezone.utc)
        start=int(d.timestamp()*1000)
        year,month,day=d.year,d.month,d.day
        if gran=='daily':end=start+86400_000
        else:
            if month==12:nextmonth=datetime(year+1,1,1,tzinfo=timezone.utc)
            else:nextmonth=datetime(year,month+1,1,tzinfo=timezone.utc)
            end=int(nextmonth.timestamp()*1000)
    except ValueError as e:raise D04Rejected('INVALID_ARCHIVE_DATE') from e
    return {'url':url,'symbol':symbol,'tf':tf,'filename':filename,'granularity':gran,'start_ms':start,'end_ms':end,'expected_rows':(end-start)//PERIOD[tf]}

def parse_checksum(blob,filename):
    try:s=blob.decode('ascii').strip()
    except (UnicodeDecodeError,AttributeError) as e:raise D04Rejected('INVALID_CHECKSUM_ENCODING') from e
    m=re.fullmatch(r'([0-9a-fA-F]{64}) [ *]([^\s/\\]+)',s)
    if not m or m[2]!=filename:raise D04Rejected('INVALID_CHECKSUM_FORMAT_OR_NAME')
    return m[1].lower()

def _positive(s,field,allow_zero=False):
    try:x=Decimal(s)
    except (InvalidOperation,ValueError,TypeError) as e:raise D04Rejected('INVALID_NUMERIC_'+field) from e
    if not x.is_finite() or (x<0 if allow_zero else x<=0):raise D04Rejected('BAD_NUMERIC_'+field)
    return x

def verify_raw_zip(url,zip_blob,checksum_blob, *,max_uncompressed=80_000_000, max_archive=25_000_000):
    source=parse_url(url)
    if not isinstance(zip_blob,bytes) or len(zip_blob)>max_archive:raise D04Rejected('BAD_OR_OVERSIZE_ZIP')
    remote=parse_checksum(checksum_blob,source['filename'])
    if digest(zip_blob)!=remote:raise D04Rejected('ARCHIVE_CHECKSUM_MISMATCH')
    try:z=zipfile.ZipFile(io.BytesIO(zip_blob))
    except (zipfile.BadZipFile,ValueError) as e:raise D04Rejected('CORRUPT_ZIP') from e
    with z:
        infos=z.infolist()
        if len(infos)!=1 or infos[0].filename!=source['filename'][:-4]+'.csv':
            raise D04Rejected('UNEXPECTED_ZIP_MEMBERS')
        entry=infos[0]
        if entry.file_size>max_uncompressed or entry.is_dir() or entry.flag_bits&1:
            raise D04Rejected('OVERSIZE_OR_ENCRYPTED_CSV')
        try:raw=z.read(entry)
        except (RuntimeError,zipfile.BadZipFile) as e:raise D04Rejected('CORRUPT_ZIP_CONTENT') from e
    try:content=raw.decode('utf-8-sig')
    except UnicodeDecodeError as e:raise D04Rejected('CSV_ENCODING') from e
    reader=csv.reader(io.StringIO(content,newline=''))
    count=0;first=None;last=None;first_data=None;first_open=None;last_close=None;max_high=None;min_low=None;volume_total=Decimal(0)
    for row in reader:
        if len(row)!=12:raise D04Rejected('WRONG_FUTURES_KLINE_SCHEMA')
        if row[0].strip().lower()=='open_time' and count==0:
            expected=(('open_time',),('open',),('high',),('low',),('close',),('volume',),('close_time',),
                      ('quote_volume','quote_asset_volume'),('count','trades','number_of_trades'),
                      ('taker_buy_volume','taker_buy_base_volume','taker_buy_base_asset_volume'),
                      ('taker_buy_quote_volume','taker_buy_quote_asset_volume'),('ignore',))
            if not all(actual.strip().lower() in names for actual,names in zip(row,expected)):
                raise D04Rejected('UNKNOWN_FUTURES_KLINE_HEADER')
            continue
        if first_data is None:first_data=row
        try:tm=int(row[0]);close=int(row[6])
        except (ValueError,TypeError) as e:raise D04Rejected('INVALID_TIMESTAMP') from e
        if tm!=source['start_ms']+count*PERIOD[source['tf']] or close!=tm+PERIOD[source['tf']]-1:
            raise D04Rejected('MISSING_OR_WRONG_DATE_KLINES')
        o,h,l,c,v=(_positive(row[i],str(i),i==5) for i in (1,2,3,4,5))
        if not (l<=min(o,c)<=max(o,c)<=h):raise D04Rejected('INVALID_OHLC')
        first_open=o if first_open is None else first_open
        last_close=c
        max_high=max(h,max_high) if max_high is not None else h
        min_low=min(l,min_low) if min_low is not None else l
        volume_total+=v
        count+=1;last=tm
        if first is None:first=tm
    if count!=source['expected_rows']:raise D04Rejected('INCOMPLETE_SOURCE_ARCHIVE')
    return {'status':'SOURCE_CHECKSUM_AND_BARS_VERIFIED','source_url':url,'symbol':source['symbol'],'tf':source['tf'],
            'zip_sha256':remote,'raw_csv_sha256':digest(raw),'bars':count,'start_ms':first,'last_ms':last,
            'first_bar_ohlcv':first_data[:7] if first_data else [],
            'aggregated_ohlcv':{'open':str(first_open),'high':str(max_high),'low':str(min_low),'close':str(last_close),'volume':str(volume_total)}}

class _SingleHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        u=urllib.parse.urlsplit(newurl)
        if u.scheme!='https' or u.hostname!=HOST or u.port is not None:
            raise D04Rejected('REDIRECT_TO_UNTRUSTED_HOST')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch_attested_source(url, *,timeout=30):
    """Fetch TWO Binance-host HTTPS objects. Requires trusted machine CA/TLS.
    Not an offline proof and not a cryptographic Binance signature.
    """
    parse_url(url)
    opener=urllib.request.build_opener(_SingleHostRedirect())
    def fetch(one,maxbytes):
        with opener.open(urllib.request.Request(one,headers={'User-Agent':'MTF-D04-Research-Integrity/1.0'}),timeout=timeout) as conn:
            final=urllib.parse.urlsplit(conn.geturl())
            if final.scheme!='https' or final.hostname!=HOST:raise D04Rejected('UNTRUSTED_FINAL_URL')
            data=conn.read(maxbytes+1)
            if len(data)>maxbytes:raise D04Rejected('DOWNLOAD_TOO_LARGE')
            return data
    checksum=fetch(url+'.CHECKSUM',1024)
    archive=fetch(url,25_000_000)
    result=verify_raw_zip(url,archive,checksum)
    result.update({'attestation':'HTTPS_BINANCE_VISION_HOST_AND_CHECKSUM','checksum_url':url+'.CHECKSUM',
                   'limitations':'NOT_A_DIGITAL_SIGNATURE; network-origin and TLS CA trust required'})
    return result

def verify_offline_consolidated_manifest(history_dir, *,required_symbols=('BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','BCHUSDT')):
    """Check 10 CSVs and 10 manifest rows; show that offline integrity is not authenticity."""
    folder=Path(history_dir);p=folder/'manifest_vision.json'
    try:manifest=json.loads(p.read_text(encoding='utf-8'))
    except (FileNotFoundError,ValueError) as e:raise D04Rejected('MISSING_OR_INVALID_MANIFEST') from e
    if not isinstance(manifest,list):raise D04Rejected('INVALID_MANIFEST_SHAPE')
    needed={(s,t) for s in required_symbols for t in ('15m','1d')}
    seen=set();results=[];all_sources=set()
    for item in manifest:
        if not isinstance(item,dict) or not all(k in item for k in ('symbol','tf','candles','sha256','sources')):
            raise D04Rejected('INVALID_MANIFEST_ITEM')
        pair=(item['symbol'],item['tf'])
        if pair not in needed or pair in seen:raise D04Rejected('UNKNOWN_OR_DUPLICATE_MANIFEST_SYMBOL_TF')
        seen.add(pair)
        csvp=folder/(item['symbol']+'_'+item['tf']+'.csv')
        if not csvp.is_file():raise D04Rejected('MISSING_NORMALIZED_CSV')
        blob=csvp.read_bytes();actual=digest(blob)
        if not SHA.fullmatch(item['sha256']) or actual!=item['sha256']:raise D04Rejected('NORMALIZED_CSV_SHA_MISMATCH')
        with io.TextIOWrapper(io.BytesIO(blob),encoding='utf-8-sig',newline='') as fh:
            rd=csv.DictReader(fh)
            if tuple(rd.fieldnames or ())!=NORMALIZED:raise D04Rejected('NORMALIZED_COLUMNS_MISMATCH')
            first=None;last=None;count=0
            for row in rd:
                try:now=int(row['open_time'])
                except (TypeError,ValueError) as e:raise D04Rejected('CSV_BAD_TIME') from e
                if first is None:first=now
                if last is not None and now-last!=PERIOD[item['tf']]:raise D04Rejected('CSV_TIME_GRID_GAP')
                if row['symbol']!=item['symbol'] or int(row['close_time'])!=now+PERIOD[item['tf']]-1:
                    raise D04Rejected('NORMALIZED_SYMBOL_OR_CLOSE_MISMATCH')
                last=now;count+=1
        if not isinstance(item['candles'],int) or count!=item['candles']:raise D04Rejected('MANIFEST_CANDLE_COUNT_MISMATCH')
        sources=item['sources']
        if not isinstance(sources,list) or not sources:raise D04Rejected('EMPTY_OR_MISSING_SOURCE_PROOFS')
        total=0;intervals=[]
        for s in sources:
            if not isinstance(s,dict) or not all(k in s for k in ('url','sha256','rows')):raise D04Rejected('BAD_SOURCE_ENTRY')
            info=parse_url(s['url'])
            if (info['symbol'],info['tf'])!=pair:raise D04Rejected('SOURCE_SYMBOL_TF_DIVERGENCE')
            if info['url'] in all_sources:raise D04Rejected('DUPLICATE_SOURCE_URL')
            all_sources.add(info['url'])
            if not isinstance(s['rows'],int) or s['rows']!=info['expected_rows'] or not SHA.fullmatch(s['sha256']):
                raise D04Rejected('UNVERIFIED_ARCHIVE_ROW_COUNT_OR_HASH_FORMAT')
            intervals.append((info['start_ms'],info['end_ms']))
            total+=s['rows']
        intervals.sort()
        for before,after in zip(intervals,intervals[1:]):
            if before[1]!=after[0]:raise D04Rejected('SOURCE_INTERVAL_OVERLAP_OR_GAP')
        if not intervals or first!=intervals[0][0] or last+PERIOD[item['tf']]!=intervals[-1][1] or total!=count:
            raise D04Rejected('SOURCE_COVERAGE_MISMATCH')
        results.append({'symbol':item['symbol'],'tf':item['tf'],'bars':count,'normalized_csv_sha256':actual,'source_archives_declared':len(sources)})
    if seen!=needed:raise D04Rejected('MISSING_REQUIRED_MARKET_SERIES')
    return {'status':'OFFLINE_INTEGRITY_ONLY','source_authenticity':'NOT_ATTESTED_FROM_OFFLINE_MANIFEST',
            'series_verified':len(results),'total_bars':sum(x['bars'] for x in results),'declared_source_archives':len(all_sources),
            'series':sorted(results,key=lambda x:(x['symbol'],x['tf'])),
            'note':'Hashes on disk do not authenticate Binance origin. Require independent HTTPS .CHECKSUM and ZIP receipt.'}
