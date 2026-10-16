"""D05/F03: strict original Binance USD-M Futures 5m archive source bridge.

5m is absent from FROZEN C08's 315 archive approvals. This is a separate,
single-archive provenance contract using the D04 same-host checksum oracle.
Only a downloaded source that matches its original .CHECKSUM is attested.
No native C08 5m flag, course Volume Confirmation, orders or READY.
"""
from __future__ import annotations
import csv
import hashlib
import io
import re
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from decimal import Decimal,InvalidOperation
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from strict_vision_d04 import parse_checksum,_SingleHostRedirect
sys.path.insert(0,str(ROOT.parent/"mtf-course-v05"/"src"))
from course_primitives_v05 import Bar,confirmed_imb

PERIOD=300_000
ALLOWED=frozenset(("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"))
DAY=86_400_000
RE=re.compile(r"/data/futures/um/daily/klines/([A-Z0-9]+)/5m/([A-Z0-9]+)-5m-(20[0-9]{2}-[0-9]{2}-[0-9]{2})\\.zip\\Z")
CSV_HEADER=("open_time","open","high","low","close","volume","close_time",
            "quote_volume","trades","taker_buy_base_volume","taker_buy_quote_volume","ignore")

class FiveMinuteRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class Source5mRow:
    bar: Bar
    volume: Decimal
    original_csv_row: tuple[str,...]
    raw_id: str

@dataclass(frozen=True)
class Verified5m:
    archive_url: str
    symbol: str
    day_start_ms: int
    zip_sha256: str
    raw_csv_sha256: str
    rows: tuple[Source5mRow,...]
    raw_origin_status: str="BINANCE_VISION_HTTPS_PLUS_SAME_HOST_CHECKSUM_NOT_DIGITAL_SIGNATURE"
    academic_status: str="SOURCE_5M_ONLY_VC_NOT_CERTIFIED"
    readiness: str="NOT_TRADE_READY"

def parse_5m_source(url:str):
    if not isinstance(url,str):
        raise FiveMinuteRejected("INVALID_URL")
    u=urllib.parse.urlsplit(url)
    if (u.scheme!="https" or u.netloc!="data.binance.vision"
        or u.query or u.fragment or u.username or u.password
        or "%" in u.path or "\\\\" in u.path or "//" in u.path):
        raise FiveMinuteRejected("NOT_TRUSTED_BINANCE_5M_FUTURES_PATH")
    m=RE.fullmatch(u.path)
    if m is None or m[1]!=m[2] or m[1] not in ALLOWED:
        raise FiveMinuteRejected("NOT_APPROVED_FUTURES_SYMBOL_OR_5M_PATH")
    try:
        date=datetime.strptime(m[3],"%Y-%m-%d").replace(tzinfo=timezone.utc)
        if date.strftime("%Y-%m-%d")!=m[3]: raise ValueError("bad day")
    except ValueError as e:raise FiveMinuteRejected("INVALID_UTC_DATE") from e
    return m[1],int(date.timestamp()*1000),m[2]+"-5m-"+m[3]+".zip"

def _positive_dec(v,name,zero=False):
    try:x=Decimal(v)
    except (InvalidOperation,ValueError,TypeError) as e:
        raise FiveMinuteRejected("BAD_NUMBER_"+name) from e
    if not x.is_finite() or (x<0 if zero else x<=0):
        raise FiveMinuteRejected("INVALID_NUMBER_"+name)
    return x

def verify_original_5m(url:str,archive:bytes,checksum:bytes)->Verified5m:
    symbol,start,filename=parse_5m_source(url)
    if not isinstance(archive,bytes) or not isinstance(checksum,bytes) or not (0<len(archive)<=25_000_000):
        raise FiveMinuteRejected("MISSING_OR_OVERSIZE_ORIGINAL_ARCHIVE")
    sh=hashlib.sha256(archive).hexdigest()
    try:remote=parse_checksum(checksum,filename)
    except (ValueError,TypeError) as e:raise FiveMinuteRejected("INVALID_REMOTE_CHECKSUM") from e
    if sh!=remote:
        raise FiveMinuteRejected("SOURCE_CHECKSUM_MISMATCH")
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            infos=z.infolist()
            if (len(infos)!=1 or infos[0].filename!=filename[:-4]+".csv"
                or infos[0].file_size>8_000_000 or infos[0].flag_bits&1 or infos[0].is_dir()):
                raise FiveMinuteRejected("BAD_ZIP_MEMBERS_OR_SIZE")
            raw=z.read(infos[0])
    except (zipfile.BadZipFile,RuntimeError) as e:
        raise FiveMinuteRejected("CORRUPT_SOURCE_ZIP") from e
    try:
        content=raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise FiveMinuteRejected("CSV_BAD_ENCODING") from e
    records=list(csv.reader(io.StringIO(content,newline="")))
    if records and records[0] and records[0][0].strip().lower()=="open_time":
        if len(records[0])!=12 or records[0][0].strip().lower()!="open_time":
            raise FiveMinuteRejected("UNEXPECTED_KLINE_HEADER")
        records=records[1:]
    if len(records)!=288:
        raise FiveMinuteRejected("NOT_COMPLETE_288_FIVE_MINUTE_CANDLES")
    output=[]
    for i,values in enumerate(records):
        if len(values)!=12:
            raise FiveMinuteRejected("WRONG_RAW_FUTURES_ROW_FIELDS")
        try:tm=int(values[0]);close=int(values[6]);trades=int(values[8])
        except (ValueError,TypeError) as e:raise FiveMinuteRejected("BAD_SOURCE_TIMESTAMP_OR_TRADE_COUNT") from e
        if tm!=start+i*PERIOD or close!=tm+PERIOD-1 or trades<0:
            raise FiveMinuteRejected("SOURCE_TIME_GRID_GAP_OR_CLOSE_ERROR")
        op,hi,lo,cl=[_positive_dec(values[j],str(j)) for j in (1,2,3,4)]
        vol=_positive_dec(values[5],"volume",True)
        _positive_dec(values[7],"quote_volume",True)
        _positive_dec(values[9],"taker_base",True)
        _positive_dec(values[10],"taker_quote",True)
        if not lo<=min(op,cl)<=max(op,cl)<=hi:
            raise FiveMinuteRejected("IMPOSSIBLE_RAW_OHLC")
        bar=Bar(tm,close+1,float(op),float(hi),float(lo),float(cl),"5m")
        output.append(Source5mRow(bar,vol,tuple(values),sh+":"+values[0]))
    return Verified5m(url,symbol,start,sh,hashlib.sha256(raw).hexdigest(),tuple(output))

def download_source_5m(url:str,timeout:int=40)->Verified5m:
    """Two trusted HTTPS reads; same-host .CHECKSUM is NOT a digital signature."""
    parse_5m_source(url)
    opener=urllib.request.build_opener(_SingleHostRedirect())
    def fetch(one,limit):
        with opener.open(urllib.request.Request(one,headers={"User-Agent":"EMBER-F03-5m-academic-source/1.0"}),timeout=timeout) as res:
            final=urllib.parse.urlsplit(res.geturl())
            if final.scheme!="https" or final.netloc!="data.binance.vision":
                raise FiveMinuteRejected("SOURCE_REDIRECT_NOT_TRUSTED")
            payload=res.read(limit+1)
        if len(payload)>limit:raise FiveMinuteRejected("OVERSIZE_REMOTE_SOURCE")
        return payload
    remote=fetch(url+".CHECKSUM",1024)
    raw=fetch(url,25_000_000)
    return verify_original_5m(url,raw,remote)

def source_5m_imbs(proof:Verified5m,as_of_ms:int):
    """Original unchanged course-v05 IMB geometry known after its 3rd 5m close.

    This applies on one *fully source-attested* 5m day. Caller must still
    provide HTF POI/15m trigger and independent academic VC semantics.
    """
    if not isinstance(proof,Verified5m):
        raise FiveMinuteRejected("NO_ATTESTED_5M_PROOF_OBJECT")
    if type(as_of_ms) is not int or as_of_ms%PERIOD:
        raise FiveMinuteRejected("5M_AS_OF_NOT_CLOSED")
    if as_of_ms<proof.day_start_ms or as_of_ms>proof.day_start_ms+DAY:
        raise FiveMinuteRejected("5M_AS_OF_OUTSIDE_ATTESTED_DAY")
    before=[r.bar for r in proof.rows if r.bar.end<=as_of_ms]
    out=confirmed_imb(before)
    if any(x.known>as_of_ms for x in out):
        raise FiveMinuteRejected("FUTURE_5M_IMBALANCE")
    return tuple(out)
