"""C116 source: only original Binance USD-M 1m archive is authoritative within experiment.

Derive UTC aligned 3m and 5m independently from the same 1m stream.
Internally consistent != independently true: keep provider SHA and lineage.
PAPER ONLY.
"""
from decimal import Decimal as D, InvalidOperation
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile, BadZipFile
from datetime import datetime,timezone
from dataclasses import dataclass
from c21_native3m_source_bridge import Original3mRow
from c89_original_native5m_adaptation_backtest import Bar, _safe_http, BASE
import csv

class C116SourceError(ValueError):pass
ONE=60000
THREE=3*ONE
FIVE=5*ONE
DAY=24*60*ONE
MAX_ZIP=30_000_000

@dataclass(frozen=True)
class Original1m:
    start_ms:int
    known_ms:int
    o:D
    h:D
    l:D
    c:D
    volume:D

def decimal(s):
    try:
        value=D(s)
    except (InvalidOperation,TypeError,ValueError) as ex:
        raise C116SourceError("ORIGINAL_1M_NONDECIMAL") from ex
    if not value.is_finite():
        raise C116SourceError("ORIGINAL_1M_NONFINITE")
    return value

def daily(symbol,day,*,fetch=_safe_http):
    if not(symbol.endswith("USDT") and symbol.isalnum() and len(symbol)<=18):
        raise C116SourceError("INVALID_FROZEN_MARKET_SYMBOL")
    try:
        dt=datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as ex:
        raise C116SourceError("BAD_DAILY_UTC_DATE") from ex
    if dt.strftime("%Y-%m-%d")!=day:
        raise C116SourceError("NONCANONICAL_UTC_DATE")
    origin=int(dt.timestamp()*1000)
    stem=f"{symbol}-1m-{day}"
    url=f"{BASE}data/futures/um/daily/klines/{symbol}/1m/{stem}.zip"
    archive=fetch(url);checksum=fetch(url+".CHECKSUM")
    if (type(archive) is not bytes or type(checksum) is not bytes or
        not 0<len(archive)<=MAX_ZIP):
        raise C116SourceError("ORIGINAL_1M_PROVIDER_ZIP_MISSING")
    digest=sha256(archive).hexdigest()
    try: fields=checksum.decode("ascii").strip().split()
    except UnicodeDecodeError as ex:
        raise C116SourceError("NO_ASCII_PROVIDER_CHECKSUM") from ex
    if len(fields)!=2 or fields[0].lower()!=digest or fields[1].split("/")[-1]!=stem+".zip":
        raise C116SourceError("ORIGINAL_1M_PROVIDER_CHECKSUM_MISMATCH")
    try:
        with ZipFile(BytesIO(archive)) as z:
            members=z.infolist()
            if (len(members)!=1 or members[0].filename!=stem+".csv" or
                members[0].is_dir() or members[0].flag_bits&1 or
                members[0].file_size>MAX_ZIP):
                raise C116SourceError("INVALID_PROVIDER_ZIP_MEMBERS")
            raw=z.read(members[0])
    except (BadZipFile,EOFError) as ex:
        raise C116SourceError("ORIGINAL_1M_BAD_ZIP") from ex
    try: source=list(csv.reader(raw.decode("utf-8-sig").splitlines()))
    except UnicodeDecodeError as ex:
        raise C116SourceError("ORIGINAL_1M_BAD_UTF8") from ex
    if source and source[0][0].strip().lower() in ("open_time","open time"):
        source=source[1:]
    if len(source)!=1440:
        raise C116SourceError("ORIGINAL_1M_DAY_NOT_1440_BARS")
    bars=[]
    for i,row in enumerate(source):
        if len(row)!=12:raise C116SourceError("ORIGINAL_1M_12_FIELDS_REQUIRED")
        at=origin+i*ONE
        try:
            start,end,trades=int(row[0]),int(row[6]),int(row[8])
            o,h,l,c,v=[decimal(row[n]) for n in (1,2,3,4,5)]
            quote,taker,takerquote=[decimal(row[n]) for n in (7,9,10)]
        except (ValueError,IndexError) as ex:
            raise C116SourceError("ORIGINAL_1M_BAD_CLOCK_OR_COLUMN") from ex
        if start!=at or end!=at+ONE-1 or trades<0:
            raise C116SourceError("ORIGINAL_1M_GAP_DUPLICATE_NOT_CLOSED")
        if (not 0<l<=min(o,c)<=max(o,c)<=h or
            any(x<0 for x in (v,quote,taker,takerquote))):
            raise C116SourceError("ORIGINAL_1M_IMPOSSIBLE_OHLCV")
        bars.append(Original1m(at,at+ONE,o,h,l,c,v))
    receipt={"symbol":symbol,"date":day,
             "source_interval":"ORIGINAL_NATIVE_1M",
             "zip_sha256":digest,"csv_sha256":sha256(raw).hexdigest(),
             "bars":1440,"source":url,"provider_checksum_verified":True}
    return tuple(bars),receipt

def roll(rows,symbol,sha):
    if len(rows)!=1440:
        raise C116SourceError("CANONICAL_1M_DAY_REQUIRED")
    if rows[0].start_ms%DAY:
        raise C116SourceError("CANONICAL_DAY_UTC_ALIGNMENT")
    for i,x in enumerate(rows):
        if not isinstance(x,Original1m) or x.start_ms!=rows[0].start_ms+i*ONE or x.known_ms!=x.start_ms+ONE:
            raise C116SourceError("ONE_MINUTE_SOURCE_GAP")
    def grouped(n):
        ans=[]
        for off in range(0,len(rows),n):
            z=rows[off:off+n]
            if len(z)!=n or z[-1].known_ms!=z[0].start_ms+n*ONE:
                raise C116SourceError("PARTIAL_DERIVED_BAR")
            o,h,l,c=z[0].o,max(b.h for b in z),min(b.l for b in z),z[-1].c
            v=sum((b.volume for b in z),D(0))
            ans.append((z[0].start_ms,o,h,l,c,v))
        return ans
    triples=grouped(3);fives=grouped(5)
    a=tuple(Original3mRow(symbol,t,t+THREE,o,h,l,c,v,
                          "CANONICAL1M:"+sha+":"+str(t),sha)
            for t,o,h,l,c,v in triples)
    b=tuple(Bar(t,o,h,l,c,v) for t,o,h,l,c,v in fives)
    if len(a)!=480 or len(b)!=288:
        raise C116SourceError("DERIVED_3M5M_DAY_INCOMPLETE")
    # Both trade intervals are derived independently from native 1m.
    for j in range(96):
        x=a[5*j:5*j+5];y=b[3*j:3*j+3]
        left=(x[0].start_ms,x[-1].known_ms,x[0].open,
              max(e.high for e in x),min(e.low for e in x),x[-1].close,
              sum((e.volume for e in x),D(0)))
        right=(y[0].open_ms,y[-1].close_ms,y[0].o,
               max(e.h for e in y),min(e.l for e in y),y[-1].c,
               sum((e.volume for e in y),D(0)))
        if left!=right:
            raise C116SourceError("FAILED_CANONICAL_PRICE_AND_VOLUME_PARITY")
    return a,b

def daily_derived(symbol,day,*,fetch=_safe_http):
    one,receipt=daily(symbol,day,fetch=fetch)
    three,five=roll(one,symbol,receipt["zip_sha256"])
    return three,five,receipt
