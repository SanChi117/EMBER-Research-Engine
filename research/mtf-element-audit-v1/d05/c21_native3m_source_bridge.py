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
