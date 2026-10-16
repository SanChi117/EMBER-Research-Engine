"""B1/C21A source-only original Binance USD-M native 3m proof, PAPER ONLY.

New source: September 2026 original monthly 3m ZIP plus original Oct 1/2
daily 3m ZIP and same-host .CHECKSUM. Five native 3m bars must exactly
reconstruct each independently C08 source-pinned native 15m OHLCV candle.
This validates price-data lineage only, NOT any author-approved 3m BOS.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
from urllib.parse import urlsplit
import csv,hashlib,io,re,zipfile
from c16_c08_monthly_daily_htf_lineage import SEPT_START,OCT_START,END,DAY,SYMBOLS
from strict_vision_d04 import parse_checksum

THREE=180000
PERIODS=("2026-09","2026-10-01","2026-10-02")
STARTS=(SEPT_START,OCT_START,OCT_START+DAY)
ZIPSHA=re.compile(r"[0-9a-f]{64}\Z")

class C21Rejected(ValueError):pass

@dataclass(frozen=True)
class Original3mRow:
    symbol:str
    start_ms:int
    known_ms:int
    open:Decimal
    high:Decimal
    low:Decimal
    close:Decimal
    volume:Decimal
    raw_id:str
    zip_sha:str

@dataclass(frozen=True)
class Original3mArchive:
    symbol:str
    period:str
    url:str
    zip_sha:str
    csv_sha:str
    rows:tuple[Original3mRow,...]
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C21Native3mResult:
    symbol:str
    as_of_ms:int
    original_3m_closed:tuple[Original3mRow,...]
    original_zip_shas:tuple[str,str,str]
    native_15m_ohlcv_equalities:int
    native_1d_equalities:int
    author_bos_approved:int=0
    trade_approved:int=0
    readiness:str="NOT_TRADE_READY"
    author_status:str="AUTHOR_GOLDEN_SOURCE_UNAVAILABLE"

def checked_url(symbol,period):
    if symbol not in SYMBOLS or period not in PERIODS:
        raise C21Rejected("NOT_A_FIVE_SYMBOL_OR_32DAY_SOURCE")
    unit="monthly" if len(period)==7 else "daily"
    return ("https://data.binance.vision/data/futures/um/"+unit+
            "/klines/"+symbol+"/3m/"+symbol+"-3m-"+period+".zip")

def verified_name(url,symbol,period):
    expected=checked_url(symbol,period)
    if not isinstance(url,str) or url!=expected:
        raise C21Rejected("UNTRUSTED_USDM_3M_HOST_SYMBOL_OR_PERIOD")
    u=urlsplit(url)
    if (u.scheme!="https" or u.netloc!="data.binance.vision" or
        u.username or u.password or u.query or u.fragment or
        "%" in u.path or "\\" in u.path or "//" in u.path):
        raise C21Rejected("UNSAFE_3M_URI")
    return expected.rsplit("/",1)[-1]

def decimal(x):
    try:value=Decimal(x)
    except (InvalidOperation,ValueError,TypeError) as e:raise C21Rejected("BAD_3M_DECIMAL") from e
    if not value.is_finite():raise C21Rejected("NONFINITE_3M_OHLCV")
    return value

def read_original_3m(url,archive,checksum,*,symbol,period):
    name=verified_name(url,symbol,period)
    if (type(archive) is not bytes or type(checksum) is not bytes or
        not 0<len(archive)<=30000000):
        raise C21Rejected("MISSING_OR_OVERSIZE_ORIGINAL_3M")
    sha=hashlib.sha256(archive).hexdigest()
    try:check=parse_checksum(checksum,name)
    except (ValueError,TypeError) as e:
        raise C21Rejected("INVALID_SOURCE_CHECKSUM_3M") from e
    if check!=sha:raise C21Rejected("ORIGINAL_3M_ZIP_SHA_MISMATCH")
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            infos=z.infolist()
            if (len(infos)!=1 or infos[0].filename!=name[:-4]+".csv"
                or infos[0].is_dir() or infos[0].flag_bits&1
                or infos[0].file_size>20000000):
                raise C21Rejected("UNSAFE_ORIGINAL_3M_ZIP")
            raw=z.read(infos[0])
        text=raw.decode("utf-8-sig")
        table=list(csv.reader(io.StringIO(text,newline="")))
    except (zipfile.BadZipFile,KeyError,UnicodeError,RuntimeError) as e:
        raise C21Rejected("CORRUPT_ORIGINAL_3M_ZIP") from e
    if table and table[0][0].strip().lower()=="open_time":
        if len(table[0])!=12:raise C21Rejected("WRONG_ORIGINAL_3M_HEADER")
        table=table[1:]
    expected=(30*DAY if period=="2026-09" else DAY)//THREE
    if len(table)!=expected:raise C21Rejected("INCOMPLETE_3M_SOURCE_PERIOD")
    base=STARTS[PERIODS.index(period)]
    out=[]
    for i,r in enumerate(table):
        if len(r)!=12:raise C21Rejected("ORIGINAL_3M_NEEDS_12_COLUMNS")
        at=base+i*THREE
        try:
            t=int(r[0]);close=int(r[6]);trades=int(r[8])
        except (TypeError,ValueError) as e:
            raise C21Rejected("INVALID_NATIVE_3M_TIME_OR_TRADECOUNT") from e
        if t!=at or close!=at+THREE-1 or trades<0:
            raise C21Rejected("GAPPED_UNCLOSED_OR_REORDERED_3M")
        o,h,l,c,v=(decimal(r[j]) for j in (1,2,3,4,5))
        quote,taker,takerquote=(decimal(r[j]) for j in (7,9,10))
        if not (0<l<=min(o,c)<=max(o,c)<=h and
                min(v,quote,taker,takerquote)>=0):
            raise C21Rejected("IMPOSSIBLE_NATIVE_3M_OHLCV")
        out.append(Original3mRow(symbol,at,at+THREE,o,h,l,c,v,
                                 sha+":"+str(at),sha))
    return Original3mArchive(symbol,period,url,sha,
                             hashlib.sha256(raw).hexdigest(),tuple(out))

def reconcile_native_3m(archives,c08,*,as_of_ms):
    """Full original 32d source and C08 native 15m parity before as-of crop."""
    from c16_c08_monthly_daily_htf_lineage import ExtendedHTFReview
    from c18_native_15m_child_witness_graph import _verify_review
    if not isinstance(c08,ExtendedHTFReview) or c08.as_of_ms!=END:
        raise C21Rejected("MISSING_FULL_C08_PRICE_CONTEXT")
    if type(as_of_ms) is not int or not SEPT_START<=as_of_ms<=END or as_of_ms%THREE:
        raise C21Rejected("FUTURE_OR_NONCLOSED_3M_ASOF")
    try:_verify_review(c08)
    except ValueError as e:raise C21Rejected("INVALID_C08_NATIVE_PRICE_REVIEW") from e
    if type(archives) is not tuple or len(archives)!=3:
        raise C21Rejected("MISSING_THREE_3M_ARCHIVES")
    full=[]
    shas=[]

    for a,period,start in zip(archives,PERIODS,STARTS):
        if (not isinstance(a,Original3mArchive) or a.symbol!=c08.symbol
            or a.period!=period or a.readiness!="NOT_TRADE_READY"):
            raise C21Rejected("WRONG_ORIGINAL_3M_ARCHIVE")
        verified_name(a.url,c08.symbol,period)
        if not ZIPSHA.fullmatch(a.zip_sha) or not ZIPSHA.fullmatch(a.csv_sha):
            raise C21Rejected("INVALID_3M_RECEIPT_DIGEST")
        count=(30*DAY if period=="2026-09" else DAY)//THREE
        if len(a.rows)!=count:raise C21Rejected("INCOMPLETE_3M_SOURCE_ROWS")
        for i,r in enumerate(a.rows):
            at=start+i*THREE
            if (not isinstance(r,Original3mRow) or r.symbol!=c08.symbol
                or r.start_ms!=at or r.known_ms!=at+THREE
                or r.zip_sha!=a.zip_sha or r.raw_id!=a.zip_sha+":"+str(at)
                or not all(isinstance(x,Decimal) and x.is_finite() for x in
                    (r.open,r.high,r.low,r.close,r.volume))
                or not (0<r.low<=min(r.open,r.close)<=max(r.open,r.close)<=r.high
                    and r.volume>=0)):
                raise C21Rejected("ALTERED_NATIVE_3M_SOURCE_ROWS")
        full.extend(a.rows)
        shas.append(a.zip_sha)

    if len(full)!=15360 or len(c08.native_15m_closed)!=3072:
        raise C21Rejected("NOT_32_DAY_SOURCE_ALIGNED")
    for i,p in enumerate(c08.native_15m_closed):
        five=full[i*5:i*5+5]
        native=(five[0].start_ms,five[-1].known_ms,five[0].open,
                max(x.high for x in five),min(x.low for x in five),
                five[-1].close,sum((x.volume for x in five),Decimal(0)))
        frozen=(p.start_ms,p.known_at_ms,p.open,p.high,p.low,p.close,p.volume)
        if native!=frozen:
            raise C21Rejected("NATIVE_3M_VS_C08_15M_DECIMAL_OHLCV_DRIFT")
    return C21Native3mResult(
        c08.symbol,as_of_ms,tuple(x for x in full if x.known_ms<=as_of_ms),
        tuple(shas),3072,c08.crosschecked_native_1d)
