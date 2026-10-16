"""B1/C16: 32-day C08 native 15m ↔ native 1d original USD-M source proof.

Reuses frozen D04 source validator and C08 receipts. The September 2026
MONTHLY original archives plus Oct 1-2 DAILY original archives form 32
contiguous UTC days. Independent native 1d and 15m streams must match O/H/L/C/V
exactly via Decimal, including a strict as-of prefix for 1h/4h.

No one-bar lookahead. No author-approved POI/StrongHL, FTA, SL or trade.
"""
from __future__ import annotations
import csv,io,re,sys,zipfile
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from strict_vision_d04 import parse_url,verify_raw_zip,D04Rejected

DAY=86_400_000
TF_MS={"15m":900_000,"1h":3_600_000,"4h":14_400_000,"1d":DAY}
SEPT_START=1788220800000  # 2026-09-01 00:00 UTC
OCT_START=1790812800000   # 2026-10-01 00:00 UTC
END=1790985600000         # 2026-10-03 00:00 UTC
SYMBOLS=frozenset(("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"))
TARGET_DAYS=32

class HTFSourceRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class NativeKline:
    symbol: str
    tf: str
    start_ms: int
    known_at_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    origin_raw_row_id: str
    origin_zip_sha256: str

@dataclass(frozen=True)
class NativeSourceArchive:
    symbol: str
    tf: str
    period_start_ms: int
    period_end_ms: int
    archive_url: str
    zip_sha256: str
    raw_csv_sha256: str
    rows: tuple[NativeKline,...]
    readiness: str="NOT_TRADE_READY"

@dataclass(frozen=True)
class DerivedClosedTF:
    symbol: str
    tf: str
    start_ms: int
    known_at_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source_native_15m_rows: tuple[str,...]
    source_native_15m_zip_shas: tuple[str,...]
    provenance: str="DERIVED_EXACT_DECIMAL_FROM_C08_NATIVE_15M"
    author_status: str="ACADEMIC_HTF_POI_NOT_CERTIFIED"

@dataclass(frozen=True)
class ExtendedHTFReview:
    symbol: str
    as_of_ms: int
    native_15m_closed: tuple[NativeKline,...]
    native_1d_closed: tuple[NativeKline,...]
    derived_1h_closed: tuple[DerivedClosedTF,...]
    derived_4h_closed: tuple[DerivedClosedTF,...]
    crosschecked_native_1d: int
    author_status: str="NO_AUTHOR_LABELLED_1D_4H_POI"
    readiness: str="NOT_TRADE_READY"

def _number(x):
    try:r=Decimal(x)
    except (ValueError,TypeError,InvalidOperation) as ex:
        raise HTFSourceRejected("NON_NUMERIC_RAW_PRICE") from ex
    if not r.is_finite():
        raise HTFSourceRejected("NONFINITE_RAW_PRICE")
    return r

def c08_bound_archive(url: str, archive:bytes, checksum:bytes,receipt:dict)->NativeSourceArchive:
    """Full native D04 content proof + C08 frozen receipt SHA is mandatory.

    Synthetic test bytes may be used ONLY for unit tests, not source claims.
    The caller must independently pin the C08 receipt Git blob.
    """
    try:
        info=parse_url(url)
        check=verify_raw_zip(url,archive,checksum)
    except (D04Rejected,TypeError,ValueError,zipfile.BadZipFile) as e:
        raise HTFSourceRejected("NOT_VALID_ORIGINAL_C08_BINANCE_ARCHIVE") from e
    if not isinstance(receipt,dict) or (receipt.get("url")!=url or
        receipt.get("status")!="HTTPS_CHECKSUM_AND_ALL_COLUMNS_REPLAYED" or
        receipt.get("normalized_all_11_columns_matched") is not True or
        receipt.get("symbol")!=info["symbol"] or receipt.get("tf")!=info["tf"] or
        receipt.get("rows")!=info["expected_rows"] or
        receipt.get("zip_sha256")!=check["zip_sha256"] or
        receipt.get("raw_csv_sha256")!=check["raw_csv_sha256"]):
        raise HTFSourceRejected("NOT_AN_IMMUTABLE_C08_RECEIPT_MATCH")
    if info["symbol"] not in SYMBOLS or info["tf"] not in ("15m","1d"):
        raise HTFSourceRejected("NOT_FIVE_SYMBOL_15M_OR_1D")
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            data=z.read(info["filename"][:-4]+".csv").decode("utf-8-sig")
    except (zipfile.BadZipFile,UnicodeDecodeError,KeyError) as e:
        raise HTFSourceRejected("BAD_ARCHIVE_MEMBER") from e
    raw=list(csv.reader(io.StringIO(data,newline="")))
    if raw and raw[0][0].lower()=="open_time":raw=raw[1:]
    if len(raw)!=info["expected_rows"]:
        raise HTFSourceRejected("INCOMPLETE_NATIVE_TIMEFRAME_ARCHIVE")
    bars=[]
    period=TF_MS[info["tf"]]
    for idx,row in enumerate(raw):
        if len(row)!=12:
            raise HTFSourceRejected("INVALID_NATIVE_CSV_COLUMNS")
        try:start=int(row[0]);end=int(row[6])
        except (ValueError,TypeError) as e:
            raise HTFSourceRejected("INVALID_NATIVE_BAR_TIMESTAMP") from e
        if (start!=info["start_ms"]+idx*period or end+1!=start+period):
            raise HTFSourceRejected("INVALID_NATIVE_GRID")
        o,h,l,c,v=(_number(row[k]) for k in (1,2,3,4,5))
        if not (0<l<=min(o,c)<=max(o,c)<=h and v>=0):
            raise HTFSourceRejected("INVALID_NATIVE_OHLCV")
        bars.append(NativeKline(info["symbol"],info["tf"],start,end+1,
                                o,h,l,c,v,check["zip_sha256"]+":"+str(start),
                                check["zip_sha256"]))
    return NativeSourceArchive(info["symbol"],info["tf"],info["start_ms"],
                               info["end_ms"],url,check["zip_sha256"],
                               check["raw_csv_sha256"],tuple(bars))

def _combine(segment:tuple[NativeKline,...],tf:str)->DerivedClosedTF:
    if not segment or len(segment)!=(TF_MS[tf]//TF_MS["15m"]):
        raise HTFSourceRejected("INCOMPLETE_CLOSED_NATIVE_15M_SET")
    start,end=segment[0].start_ms,segment[-1].known_at_ms
    if start%TF_MS[tf] or end!=start+TF_MS[tf] or any(
        a.known_at_ms!=b.start_ms for a,b in zip(segment,segment[1:])
    ):
        raise HTFSourceRejected("NOT_A_CONTIGUOUS_CLOSED_HTF_BUCKET")
    return DerivedClosedTF(
        segment[0].symbol,tf,start,end,segment[0].open,
        max(x.high for x in segment),min(x.low for x in segment),
        segment[-1].close,sum((x.volume for x in segment),Decimal(0)),
        tuple(x.origin_raw_row_id for x in segment),
        tuple(dict.fromkeys(x.origin_zip_sha256 for x in segment)))

def extended_32day_prefix(native15:tuple[NativeSourceArchive,...],
                          native1d:tuple[NativeSourceArchive,...],
                          as_of_ms:int)->ExtendedHTFReview:
    """Requires September full month + Oct1 and Oct2, both independently native.

    Never use data after as_of in returned historical prefix; validation may
    inspect source integrity of a complete offline archive.
    """
    if type(as_of_ms) is not int or as_of_ms%TF_MS["15m"] or not SEPT_START<=as_of_ms<=END:
        raise HTFSourceRejected("INVALID_OR_FUTURE_ASOF")
    if not isinstance(native15,tuple) or not isinstance(native1d,tuple) or len(native15)!=3 or len(native1d)!=3:
        raise HTFSourceRejected("MISSING_REQUIRED_MONTH_AND_TWO_DAYS")
    slots=(SEPT_START,OCT_START,OCT_START+DAY)
    allpieces=(native15,native1d)
    for tf,parts in zip(("15m","1d"),allpieces):
        if any(not isinstance(part,NativeSourceArchive) or part.tf!=tf or
               part.period_start_ms!=start or
               part.period_end_ms!=(OCT_START if i==0 else start+DAY) or
               part.readiness!="NOT_TRADE_READY" or
               not re.fullmatch("[0-9a-f]{64}",part.zip_sha256) or
               not re.fullmatch("[0-9a-f]{64}",part.raw_csv_sha256) or
               len(part.rows)!=(30*96 if tf=="15m" else 30) if i==0 else False
               for i,(part,start) in enumerate(zip(parts,slots))):
            # Remaining checks below deliberately distinguish monthly vs daily
            raise HTFSourceRejected("INVALID_NATIVE_TIMEFRAME_ARCHIVE_SET")
    # Explicit full source proof object checks, not acceptance by archive name.
    for tf,parts in zip(("15m","1d"),allpieces):
        for i,(p,start) in enumerate(zip(parts,slots)):
            expected_rows=(30 if i==0 else 1)*(96 if tf=="15m" else 1)
            if (p.period_start_ms!=start or
                p.period_end_ms!=(OCT_START if i==0 else start+DAY) or
                len(p.rows)!=expected_rows or p.tf!=tf or
                p.readiness!="NOT_TRADE_READY"):
                raise HTFSourceRejected("INVALID_ARCHIVE_PERIOD_SIZE")
    symbol=native15[0].symbol
    if symbol not in SYMBOLS or any(p.symbol!=symbol for group in allpieces for p in group):
        raise HTFSourceRejected("MIXED_MARKET_OR_SYMBOL")
    assembled={}
    for tf,pieces in zip(("15m","1d"),allpieces):
        rows=tuple(v for p in pieces for v in p.rows)
        if len(rows)!=(TARGET_DAYS*(96 if tf=="15m" else 1)):
            raise HTFSourceRejected("SOURCE_HISTORY_NOT_32_DAYS")
        period=TF_MS[tf]
        for i,row in enumerate(rows):
            if (row.symbol!=symbol or row.tf!=tf or
                row.start_ms!=SEPT_START+i*period or
                row.known_at_ms!=row.start_ms+period or
                row.origin_zip_sha256!=pieces[0 if i<(30*96 if tf=="15m" else 30) else 1 if i<(31*96 if tf=="15m" else 31) else 2].zip_sha256 or
                row.origin_raw_row_id!=row.origin_zip_sha256+":"+str(row.start_ms) or
                not (0<row.low<=min(row.open,row.close)<=max(row.open,row.close)<=row.high
                     and row.volume>=0)):
                raise HTFSourceRejected("SOURCE_CANDLE_ROW_LINEAGE_OR_GRID_MISMATCH")
        assembled[tf]=rows
    closed15=tuple(x for x in assembled["15m"] if x.known_at_ms<=as_of_ms)
    closed1d=tuple(x for x in assembled["1d"] if x.known_at_ms<=as_of_ms)
    # Only complete CLOSED native15 buckets are present in TF outputs.
    result={}
    for tf in ("1h","4h","1d"):
        width=TF_MS[tf]//TF_MS["15m"]
        complete=tuple(_combine(closed15[i:i+width],tf)
                       for i in range(0,len(closed15)//width*width,width))
        result[tf]=complete
    if len(result["1d"])!=len(closed1d):
        raise HTFSourceRejected("MISSING_OR_LOOKAHEAD_DAILY_CANDLE")
    for raw,derived in zip(closed1d,result["1d"]):
        if (raw.start_ms,raw.known_at_ms,raw.open,raw.high,raw.low,raw.close,raw.volume)!=(
            derived.start_ms,derived.known_at_ms,derived.open,derived.high,
            derived.low,derived.close,derived.volume):
            raise HTFSourceRejected("NATIVE_1D_VS_DERIVED_15M_OHLCV_MISMATCH")
    return ExtendedHTFReview(symbol,as_of_ms,closed15,closed1d,
                             result["1h"],result["4h"],len(closed1d))
