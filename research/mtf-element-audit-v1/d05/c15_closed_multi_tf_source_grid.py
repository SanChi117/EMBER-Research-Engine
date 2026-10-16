"""B1/C15: closed multi-timeframe OHLCV lineage from TWO original Futures 5m ZIPs.

This proves each 15m/1h/4h/1d candle is an exact Decimal aggregation of
original 5m rows, and never creates an unclosed higher-timeframe candle.
Source provenance is 5m raw ZIP+CSV SHA verified OUTSIDE this module by
the independent F06 live HTTPS and pinned receipt workflow.

It does NOT prove an author 1D/4H POI, entry route, StrongHL, FTA, SL,
or adequate daily lookback. C13 v05 geometric child events remain separate.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"mtf-course-v05"/"src"))
from c10_two_day_original_5m_context import review_two_day_5m,TwoDayRejected
from f03_5m_original_source import Verified5m,PERIOD,DAY,parse_5m_source

TF_MS={"5m":PERIOD,"15m":3*PERIOD,"1h":12*PERIOD,
       "4h":48*PERIOD,"1d":DAY}
PREFIX=(("5m",1),("15m",3),("1h",12),("4h",48),("1d",288))

class MtfLineageRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class ClosedMtfCandle:
    symbol: str
    tf: str
    start_ms: int
    known_at_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source_5m_ids: tuple[str,...]
    archive_zip_sha256s: tuple[str,...]
    price_source_status: str="AGGREGATED_RAW_5M_NOT_NATIVE_1D_OR_4H_ARCHIVE"
    readiness: str="NOT_TRADE_READY"

@dataclass(frozen=True)
class MtfPrefixReview:
    symbol: str
    as_of_ms: int
    by_timeframe: tuple[tuple[str,tuple[ClosedMtfCandle,...]],...]
    daily_coverage: str
    author_route_status: str="NO_AUTHOR_LABELLED_PARENT_POI_STRONGHL_OR_VC"
    readiness: str="NOT_TRADE_READY"

    def candles(self,tf:str)->tuple[ClosedMtfCandle,...]:
        for name,rows in self.by_timeframe:
            if name==tf:
                return rows
        raise MtfLineageRejected("UNKNOWN_TIMEFRAME")

def _decimal_cell(v):
    try:
        x=Decimal(v)
    except (ValueError,InvalidOperation,TypeError) as e:
        raise MtfLineageRejected("NON_DECIMAL_RAW_OHLCV") from e
    if not x.is_finite():
        raise MtfLineageRejected("NONFINITE_RAW_OHLCV")
    return x

def closed_mtf_prefix(first:Verified5m,second:Verified5m,
                      as_of_ms:int)->MtfPrefixReview:
    try:
        # Inherited source/time checks are additive; never rewrite C10.
        check=review_two_day_5m(first,second,as_of_ms)
    except (TwoDayRejected,TypeError,AttributeError) as e:
        raise MtfLineageRejected("INVALID_TWO_DAY_OR_ASOF_SOURCE") from e
    if (first.readiness!="NOT_TRADE_READY" or second.readiness!="NOT_TRADE_READY"
        or first.academic_status!="SOURCE_5M_ONLY_VC_NOT_CERTIFIED"
        or second.academic_status!="SOURCE_5M_ONLY_VC_NOT_CERTIFIED"):
        raise MtfLineageRejected("FORGED_SOURCE_ACADEMIC_READY")
    raw=[]
    for obj in (first,second):
        if not re.fullmatch(r"[0-9a-f]{64}",obj.zip_sha256):
            raise MtfLineageRejected("NOT_A_ORIGINAL_ZIP_SHA")
        for row in obj.rows:
            values=row.original_csv_row
            if len(values)!=12:
                raise MtfLineageRejected("INVALID_ORIGINAL_CSV_FIELDS")
            try:
                start=int(values[0]); end=int(values[6])
            except (ValueError,TypeError) as e:
                raise MtfLineageRejected("MALFORMED_RAW_SOURCE_TIME") from e
            o,h,l,c,v=tuple(_decimal_cell(values[k]) for k in (1,2,3,4,5))
            if (start!=row.bar.start or end+1!=row.bar.end
                or row.raw_id!=obj.zip_sha256+":"+str(start)
                or tuple(float(z) for z in (o,h,l,c))!=
                   (row.bar.o,row.bar.h,row.bar.l,row.bar.c)
                or v!=row.volume or v<0 or
                not (0<l<=min(o,c)<=max(o,c)<=h)):
                raise MtfLineageRejected("RAW_CSV_5M_BAR_CONTRADICTION")
            raw.append((row.bar.start,row.bar.end,o,h,l,c,v,row.raw_id,
                        obj.zip_sha256))
    if len(raw)!=576 or len(set(q[7] for q in raw))!=576:
        raise MtfLineageRejected("INCOMPLETE_OR_DUPLICATED_5M_GRID")
    closed=[r for r in raw if r[1]<=as_of_ms]
    if len(closed)!=check.closed_5m_count:
        raise MtfLineageRejected("PRICE_PREFIX_AND_ORIGINAL_SOURCE_DISAGREE")
    bundles=[]
    for tf,width in PREFIX:
        result=[]
        # All derived bars align to UTC (both days start at midnight UTC).
        for index in range(len(closed)//width):
            seg=closed[index*width:(index+1)*width]
            start=seg[0][0]
            end=seg[-1][1]
            if start%TF_MS[tf] or end!=start+TF_MS[tf]:
                raise MtfLineageRejected("INCOMPLETE_OR_MISALIGNED_TF_CANDLE")
            if any(seg[j][1]!=seg[j+1][0] for j in range(len(seg)-1)):
                raise MtfLineageRejected("GAP_IN_HIGHER_TIMEFRAME_SOURCE")
            if end>as_of_ms:
                raise MtfLineageRejected("LOOKAHEAD_UNCLOSED_DERIVED_BAR")
            result.append(ClosedMtfCandle(
                check.symbol,tf,start,end,seg[0][2],
                max(x[3] for x in seg),min(x[4] for x in seg),
                seg[-1][5],sum((x[6] for x in seg),Decimal(0)),
                tuple(x[7] for x in seg),
                tuple(dict.fromkeys(x[8] for x in seg))))
        bundles.append((tf,tuple(result)))
    days=len(bundles[-1][1])
    # Two closed daily candles cannot establish a source-attested HTF POI,
    # structural sequence or author trading context by themselves.
    status=("NO_CLOSED_DAILY_CANDLE" if days==0 else
            "ONE_DAILY_CANDLE_INSUFFICIENT_AUTHOR_HTF_CONTEXT" if days==1 else
            "TWO_DAILY_CANDLES_INSUFFICIENT_AUTHOR_HTF_CONTEXT")
    return MtfPrefixReview(check.symbol,as_of_ms,tuple(bundles),status)
