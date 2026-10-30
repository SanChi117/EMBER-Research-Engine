"""C116 official Binance USD-M original native1m daily ZIP -> derived 3m/5m.

Purpose: avoid treating incompatible independent native3m/native5m archive
price histories as one impossible candle stream. Does NOT claim original
native3m or native5m inputs. Historical PAPER ONLY.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal as D
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile, BadZipFile
import csv

from c21_native3m_source_bridge import Original3mRow
from c89_original_native5m_adaptation_backtest import Bar,BASE,_safe_http

MINUTE=60000
THREE=3*MINUTE
FIVE=5*MINUTE

class C116SourceError(ValueError):pass

@dataclass(frozen=True)
class NativeOne:
    symbol:str
    start_ms:int
    known_ms:int
    open:D
    high:D
    low:D
    close:D
    volume:D
    zip_sha256:str

def daily(symbol,date,*,fetch=_safe_http):
    if type(symbol) is not str or not symbol.endswith("USDT") or len(symbol)>18:
        raise C116SourceError("INVALID_SYMBOL")
    try:
        day=datetime.strptime(date,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError,TypeError) as ex:
        raise C116SourceError("INVALID_DATE") from ex
    if day.strftime("%Y-%m-%d")!=date:
        raise C116SourceError("NONCANONICAL_DATE")
    stem=f"{symbol}-1m-{date}"
    url=f"{BASE}data/futures/um/daily/klines/{symbol}/1m/{stem}.zip"
    data=fetch(url)
    sig=fetch(url+".CHECKSUM")
    if type(data) is not bytes or type(sig) is not bytes or not 0<len(data)<=30000000:
        raise C116SourceError("MISSING_ORIGINAL_NATIVE1M")
    zsha=sha256(data).hexdigest()
    try:
        fields=sig.decode("ascii").strip().split()
    except UnicodeDecodeError as ex:
        raise C116SourceError("NONASCII_PROVIDER_CHECKSUM") from ex
    if len(fields)!=2 or fields[0].lower()!=zsha or fields[1].split("/")[-1]!=stem+".zip":
        raise C116SourceError("ORIGINAL_BINANCE_1M_CHECKSUM_DRIFT")
    try:
        with ZipFile(BytesIO(data)) as z:
            members=z.infolist()
            if (len(members)!=1 or members[0].filename!=stem+".csv" or
                members[0].is_dir() or members[0].flag_bits&1 or
                members[0].file_size>30000000):
                raise C116SourceError("UNEXPECTED_SOURCE_ARCHIVE_MEMBER")
            raw=z.read(members[0])
    except (BadZipFile,EOFError) as ex:
        raise C116SourceError("BINANCE_1M_ZIP_CORRUPT") from ex
    try:
        src=list(csv.reader(raw.decode("utf-8-sig").splitlines()))
        if src and src[0][0].lower().strip() in ("open_time","open time"):
            src=src[1:]
        if len(src)!=1440:
            raise C116SourceError("INCOMPLETE_ORIGINAL_1440_1M_DAY")
        base=int(day.timestamp()*1000)
        out=[]
        for i,r in enumerate(src):
            if len(r)!=12:raise C116SourceError("WRONG_BINANCE_1M_CSV_12_COLUMNS")
            when,closed,count=int(r[0]),int(r[6]),int(r[8])
            o,h,l,c,v=[D(r[k]) for k in (1,2,3,4,5)]
            other=[D(r[k]) for k in (7,9,10)]
            if (when!=base+i*MINUTE or closed!=when+MINUTE-1 or count<0 or
                any(not q.is_finite() for q in (o,h,l,c,v,*other)) or
                not (0<l<=min(o,c)<=max(o,c)<=h and v>=0) or
                any(q<0 for q in other)):
                raise C116SourceError("ORIGINAL_1M_SOURCE_CLOCK_OHLCV_INVALID")
            out.append(NativeOne(symbol,when,when+MINUTE,o,h,l,c,v,zsha))
    except (UnicodeDecodeError,IndexError,ValueError,ArithmeticError) as ex:
        if isinstance(ex,C116SourceError):raise
        raise C116SourceError("ORIGINAL_1M_CSV_UNPARSEABLE") from ex
    receipt={"symbol":symbol,"date":date,"source_interval":"ORIGINAL_NATIVE_1M",
             "zip_sha256":zsha,"csv_sha256":sha256(raw).hexdigest(),
             "native1m_rows":1440,"url":url,"provider_checksum_verified":True}
    return tuple(out),receipt

def validate_raw(rows):
    if type(rows) is not tuple or not rows or any(
       type(x) is not NativeOne or x.start_ms%MINUTE or
       x.known_ms!=x.start_ms+MINUTE or
       (i and rows[i-1].known_ms!=x.start_ms)
       for i,x in enumerate(rows)):
        raise C116SourceError("ORIGINAL_NATIVE1M_TYPE_OR_TIME_GAP")
    if any(x.symbol!=rows[0].symbol for x in rows):
        raise C116SourceError("SYMBOL_MIXED_IN_1M_SOURCE")
    return True

def resample(rows):
    validate_raw(rows)
    if len(rows)%15!=0 or rows[0].start_ms%15//15: # source at UTC minute boundary
        raise C116SourceError("UNALIGNED_1M_SOURCE_WINDOW")
    if rows[0].start_ms%(15*MINUTE):
        raise C116SourceError("ORIGINAL_1M_WINDOW_NOT_15M_ALIGNED")
    symbol=rows[0].symbol
    x3=[]
    x5=[]
    for size,result in ((3,x3),(5,x5)):
        for off in range(0,len(rows),size):
            z=rows[off:off+size]
            start=z[0].start_ms
            span=size*MINUTE
            if len(z)!=size or start%span or z[-1].known_ms!=start+span:
                raise C116SourceError("DERIVED_CANDLE_MISSING_OR_MISALIGNED")
            o=z[0].open;h=max(t.high for t in z);l=min(t.low for t in z)
            c=z[-1].close;volume=sum((t.volume for t in z),D(0))
            if size==3:
                ident=f"CANONICAL_ORIGINAL_1M:{symbol}:{start}"
                result.append(Original3mRow(symbol,start,start+span,o,h,l,c,volume,ident,
                                           "ORIGINAL_1M_ZIP_SEQUENCE"))
            else:
                result.append(Bar(start,o,h,l,c,volume))
    return tuple(x3),tuple(x5)

def verify_joint_15m(x3,x5):
    if len(x3)//5!=len(x5)//3 or len(x3)%5 or len(x5)%3:
        raise C116SourceError("CANONICAL_1M_DERIVED_15M_COUNT")
    for i in range(len(x3)//5):
        a=x3[5*i:5*i+5];b=x5[3*i:3*i+3]
        left=(a[0].start_ms,a[-1].known_ms,a[0].open,
              max(x.high for x in a),min(x.low for x in a),
              a[-1].close,sum((x.volume for x in a),D(0)))
        right=(b[0].open_ms,b[-1].close_ms,b[0].o,
               max(x.h for x in b),min(x.l for x in b),
               b[-1].c,sum((x.volume for x in b),D(0)))
        if left!=right:
            raise C116SourceError("INTERNAL_CANONICAL_1M_15M_PARITY_FAILURE")
    return {"derived_15m_buckets":len(x3)//5,
            "price_and_volume_equal":True,
            "independent_original_3m_or_5m_consumed":False,
            "source":"ONE_ORIGINAL_NATIVE_1M_PROVIDER"}
