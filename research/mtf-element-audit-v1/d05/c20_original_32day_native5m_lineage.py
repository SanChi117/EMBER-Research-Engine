"""B1/C20 read-only original Binance USD-M 5m 32d source bridge.

5m did NOT belong to frozen C08 approvals. Independent 15 new original 5m
ZIP/.CHECKSUM receipts, native September monthly + Oct1,2 daily, are needed.
Exact Decimal reconstruction of *every* C08 source-pinned native 15m O/H/L/C/V
guards 5m lineage. An attestable price feed is NOT an author-approved 1h raid
or 3m/5m BOS, signal, order, PNL, or academic trade route. PAPER ONLY.
"""
from __future__ import annotations
import csv,hashlib,io,re,zipfile
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit
from typing import Optional
from c16_c08_monthly_daily_htf_lineage import (
    ExtendedHTFReview,NativeKline,SEPT_START,OCT_START,END,DAY,TF_MS,SYMBOLS)
from c18_native_15m_child_witness_graph import _verify_review,C18Rejected
from f03_5m_original_source import (
    Verified5m,Source5mRow,parse_5m_source,verify_original_5m,
    FiveMinuteRejected)
# Preserve archived D04 checksum semantics, no new trust assumption.
from strict_vision_d04 import parse_checksum

FIVE=300_000
DATES=("2026-09","2026-10-01","2026-10-02")
SLOTS=(SEPT_START,OCT_START,OCT_START+DAY)
MONTH_ROW_COUNT=30*DAY//FIVE
SHA=re.compile(r"^[0-9a-f]{64}$")
MONTH_PATH=re.compile(r"^/data/futures/um/monthly/klines/([A-Z0-9]+)/5m/\1-5m-(20\d\d-\d\d)\.zip$")
DAILY_PATH=re.compile(r"^/data/futures/um/daily/klines/([A-Z0-9]+)/5m/\1-5m-(20\d\d-\d\d-\d\d)\.zip$")

class C20Rejected(ValueError):
    def __init__(self,code:str):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class NativeFiveMinute:
    symbol:str
    start_ms:int
    known_at_ms:int
    open:Decimal
    high:Decimal
    low:Decimal
    close:Decimal
    volume:Decimal
    origin_raw_row_id:str
    origin_zip_sha256:str

@dataclass(frozen=True)
class C20FiveMinuteArchive:
    symbol:str
    month_or_day:str
    url:str
    zip_sha256:str
    raw_csv_sha256:str
    rows:tuple[NativeFiveMinute,...]
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C20NativeSourceLineage:
    symbol:str
    as_of_ms:int
    original_5m_closed:tuple[NativeFiveMinute,...]
    source_zip_shas:tuple[str,str,str]
    original_15m_equalities:int
    verified_original_1d_equalities:int
    source_5m_total_days:int=32
    author_source_status:str="AUTHOR_GOLDEN_SOURCE_UNAVAILABLE"
    readiness:str="NOT_TRADE_READY"
    provenance:str="NATIVE_BINANCE_USDM_5M_SAME_HOST_SHA_PLUS_NATIVE_C08_15M_DECIMAL_OHLCV_PARITY"
    bos_status:str="BOS_5M_NOT_YET_AUTHOR_CERTIFIED"

def _trust_path(url:str,period:str,symbol:str)->str:
    u=urlsplit(url)
    if (u.scheme!="https" or u.netloc!="data.binance.vision" or
        u.query or u.fragment or u.username or u.password or
        "%" in u.path or "\\" in u.path or "//" in u.path):
        raise C20Rejected("UNTRUSTED_5M_ARCHIVE_HOST_OR_PATH")
    m=(MONTH_PATH if period=="2026-09" else DAILY_PATH).fullmatch(u.path)
    if not m or m.group(1)!=symbol or m.group(2)!=period or symbol not in SYMBOLS:
        raise C20Rejected("WRONG_5M_MARKET_SYMBOL_OR_ARCHIVE_PERIOD")
    return u.path.rsplit("/",1)[-1]

def _dec(value:str)->Decimal:
    try: d=Decimal(value)
    except (InvalidOperation,TypeError,ValueError) as e:raise C20Rejected("BAD_5M_NATIVE_NUMBER") from e
    if not d.is_finite():raise C20Rejected("NONFINITE_5M_NATIVE_NUMBER")
    return d

def parse_original_native5m(url:str,archive:bytes,checksum:bytes,
                            *,symbol:str,period:str)->C20FiveMinuteArchive:
    """Reject all archive URL/CSV/ZIP forgery; native raw OHLCV retained as Decimal."""
    filename=_trust_path(url,period,symbol)
    if (type(archive) is not bytes or type(checksum) is not bytes or
        not (0<len(archive)<=25_000_000)):
        raise C20Rejected("MISSING_OR_OVERSIZE_5M_ORIGINAL")
    checksum_hash=hashlib.sha256(archive).hexdigest()
    try:
        listed=parse_checksum(checksum,filename)
    except (ValueError,TypeError) as e:raise C20Rejected("INVALID_SAME_HOST_5M_CHECKSUM") from e
    if listed!=checksum_hash:raise C20Rejected("WRONG_5M_ZIP_SHA_OR_CHECKSUM")
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            infos=z.infolist()
            if (len(infos)!=1 or infos[0].filename!=filename[:-4]+".csv" or
                infos[0].is_dir() or infos[0].flag_bits&1 or
                infos[0].file_size>12_000_000):
                raise C20Rejected("UNSAFE_5M_ZIP_MEMBER")
            raw=z.read(infos[0])
        csv_text=raw.decode("utf-8-sig")
        rows=list(csv.reader(io.StringIO(csv_text,newline="")))
    except (zipfile.BadZipFile,RuntimeError,KeyError,UnicodeDecodeError) as e:
        raise C20Rejected("UNREADABLE_5M_ORIGINAL_ARCHIVE") from e
    if rows and rows[0] and rows[0][0].strip().lower()=="open_time":
        if len(rows[0])!=12:raise C20Rejected("MALFORMED_5M_HEADER")
        rows=rows[1:]
    expected=MONTH_ROW_COUNT if period=="2026-09" else DAY//FIVE
    if len(rows)!=expected:raise C20Rejected("INCOMPLETE_NATIVE_5M_PERIOD")
    start=SLOTS[DATES.index(period)]
    output=[]
    for i,r in enumerate(rows):
        if len(r)!=12:raise C20Rejected("NOT_12_COLUMNS_5M_FUTURES_KLINE")
        at=start+i*FIVE
        try:
            t=int(r[0]);clt=int(r[6]);ntrades=int(r[8])
        except (TypeError,ValueError) as e:raise C20Rejected("INVALID_NATIVE_5M_TIME_OR_TRADES") from e
        if t!=at or clt!=at+FIVE-1 or ntrades<0:
            raise C20Rejected("GAPPED_OR_UNCLOSED_5M_SOURCE_GRID")
        o,h,l,c,v=(_dec(r[k]) for k in (1,2,3,4,5))
        q,tk_base,tk_quote=(_dec(r[k]) for k in (7,9,10))
        if not (0<l<=min(o,c)<=max(o,c)<=h and min(v,q,tk_base,tk_quote)>=0):
            raise C20Rejected("IMPOSSIBLE_OR_NEGATIVE_5M_OHLCV")
        output.append(NativeFiveMinute(symbol,at,at+FIVE,o,h,l,c,v,
                                       checksum_hash+":"+str(at),checksum_hash))
    return C20FiveMinuteArchive(symbol,period,url,checksum_hash,
                                hashlib.sha256(raw).hexdigest(),tuple(output))

def reconcile_32day_native5m(five:tuple[C20FiveMinuteArchive,...],
                             verified_c16:ExtendedHTFReview,*,
                             as_of_ms:int)->C20NativeSourceLineage:
    """Never upgrade 5m provenance from unchecked file names or object claims.

    Independent network source downloader must establish ZIP + same-host
    checksum; caller's historical C08 receipts must also be independently
    pinned in GitHub CI. Full source is checked, then only <=as_of returned.
    """
    if not isinstance(verified_c16,ExtendedHTFReview):
        raise C20Rejected("NOT_A_C16_PRICE_REVIEW")
    if type(as_of_ms) is not int or not SEPT_START<=as_of_ms<=END or as_of_ms%FIVE:
        raise C20Rejected("NOT_A_CLOSED_5M_ASOF")
    if verified_c16.as_of_ms!=END:
        raise C20Rejected("MISSING_FULL_C08_15M_COMPARISON_WINDOW")
    try:_verify_review(verified_c16)
    except C18Rejected as e:raise C20Rejected("INVALID_NATIVE_15M_C08_LINEAGE") from e
    symbol=verified_c16.symbol
    if not isinstance(five,tuple) or len(five)!=3:
        raise C20Rejected("MISSING_NATIVE_SEPTEMBER_PLUS_OCTOBER_5M")
    allrows=[]
    shas=[]
    for a,date,start in zip(five,DATES,SLOTS):
        if not isinstance(a,C20FiveMinuteArchive) or a.symbol!=symbol or a.month_or_day!=date or a.readiness!="NOT_TRADE_READY":
            raise C20Rejected("WRONG_SYMBOL_OR_5M_ARCHIVE_SET")
        _trust_path(a.url,date,symbol)
        if not SHA.fullmatch(a.zip_sha256) or not SHA.fullmatch(a.raw_csv_sha256):
            raise C20Rejected("INVALID_ORIGINAL_5M_SHA")
        if len(a.rows)!=(MONTH_ROW_COUNT if date=="2026-09" else DAY//FIVE):
            raise C20Rejected("INCOMPLETE_5M_ROWS_FOR_SOURCE_PERIOD")
        for i,b in enumerate(a.rows):
            if (not isinstance(b,NativeFiveMinute) or b.symbol!=symbol or
                b.start_ms!=start+i*FIVE or b.known_at_ms!=start+(i+1)*FIVE or
                b.origin_zip_sha256!=a.zip_sha256 or
                b.origin_raw_row_id!=a.zip_sha256+":"+str(b.start_ms) or
                not all(isinstance(x,Decimal) and x.is_finite() for x in
                        (b.open,b.high,b.low,b.close,b.volume)) or
                not (0<b.low<=min(b.open,b.close)<=max(b.open,b.close)<=b.high and b.volume>=0)):
                raise C20Rejected("ALTERED_GAPPED_OR_FORGED_ORIGINAL_5M_ROW")
        allrows.extend(a.rows)
        shas.append(a.zip_sha256)
    if len(allrows)!=9216 or len(verified_c16.native_15m_closed)!=3072:
        raise C20Rejected("NOT_FULL_32_DAY_NATIVE_5M_15M")
    for i,old in enumerate(verified_c16.native_15m_closed):
        triple=allrows[i*3:i*3+3]
        eq=(old.start_ms,old.known_at_ms,old.open,old.high,old.low,old.close,old.volume)
        reconstructed=(triple[0].start_ms,triple[-1].known_at_ms,triple[0].open,
                       max(x.high for x in triple),min(x.low for x in triple),
                       triple[-1].close,sum((x.volume for x in triple),Decimal(0)))
        if eq!=reconstructed:
            raise C20Rejected("NATIVE_5M_VS_C08_15M_OHLCV_PARITY_FAIL")
    return C20NativeSourceLineage(
        symbol,as_of_ms,tuple(x for x in allrows if x.known_at_ms<=as_of_ms),
        tuple(shas),3072,verified_c16.crosschecked_native_1d)
