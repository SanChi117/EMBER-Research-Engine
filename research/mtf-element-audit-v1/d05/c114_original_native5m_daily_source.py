"""C114 exact daily Binance Vision USD-M native5m; independent from native3m."""
import csv
from datetime import datetime, timezone
from decimal import Decimal as D
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile, BadZipFile
from c89_original_native5m_adaptation_backtest import Bar, STEP, BASE, _safe_http

class C114SourceError(ValueError): pass

def daily(symbol, date, *, fetch=_safe_http):
    if not symbol.endswith("USDT") or len(symbol)>18:
        raise C114SourceError("INVALID_SYMBOL")
    if datetime.strptime(date,"%Y-%m-%d").strftime("%Y-%m-%d")!=date:
        raise C114SourceError("INVALID_DATE")
    stem=f"{symbol}-5m-{date}"
    url=f"{BASE}data/futures/um/daily/klines/{symbol}/5m/{stem}.zip"
    data=fetch(url)
    chk=fetch(url+".CHECKSUM")
    if type(data) is not bytes or type(chk) is not bytes or not 0<len(data)<=30000000:
        raise C114SourceError("MISSING_NATIVE5M_ZIP")
    digest=sha256(data).hexdigest()
    try:
        fields=chk.decode("ascii").strip().split()
    except UnicodeDecodeError as ex:
        raise C114SourceError("CHECKSUM_ASCII_MISSING") from ex
    if len(fields)!=2 or fields[0].lower()!=digest or fields[1].split("/")[-1]!=stem+".zip":
        raise C114SourceError("BINANCE_PROVIDER_CHECKSUM_DRIFT")
    try:
        with ZipFile(BytesIO(data)) as z:
            members=z.infolist()
            if (len(members)!=1 or members[0].filename!=stem+".csv" or
                members[0].is_dir() or members[0].flag_bits&1 or
                members[0].file_size>30000000):
                raise C114SourceError("NATIVE5M_ARCHIVE_MEMBERS_INVALID")
            raw=z.read(members[0])
    except (BadZipFile,EOFError) as ex:
        raise C114SourceError("INVALID_BINANCE_ZIP") from ex
    try:
        rows=list(csv.reader(raw.decode("utf-8-sig").splitlines()))
        if rows and rows[0][0].lower().strip() in ("open_time","open time"):
            rows=rows[1:]
        if len(rows)!=288:
            raise C114SourceError("REQUIRES_EXACT_288_NATIVE5M")
        start=int(datetime.strptime(date,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
        result=[]
        for i,r in enumerate(rows):
            if len(r)!=12:
                raise C114SourceError("NATIVE5M_CSV_12_COLUMNS")
            at=start+i*STEP
            stamp,closed,count=int(r[0]),int(r[6]),int(r[8])
            o,h,l,c,v=[D(r[k]) for k in (1,2,3,4,5)]
            if (stamp!=at or closed!=at+STEP-1 or count<0 or
                any(not x.is_finite() for x in (o,h,l,c,v)) or
                not (0<l<=min(o,c)<=max(o,c)<=h and v>=0)):
                raise C114SourceError("NATIVE5M_OHLC_OR_CLOCK_BAD")
            result.append(Bar(at,o,h,l,c,v))
    except (UnicodeDecodeError,IndexError,ValueError,ArithmeticError) as ex:
        if isinstance(ex,C114SourceError): raise
        raise C114SourceError("UNPARSEABLE_ORIGINAL_NATIVE5M_CSV") from ex
    return tuple(result),{
        "symbol":symbol,"date":date,"timeframe":"NATIVE_5M",
        "zip_sha256":digest,"csv_sha256":sha256(raw).hexdigest(),
        "bars":len(result),"source":url,
        "provider_checksum_verified":True,
        "independent_5m_zip":True
    }
