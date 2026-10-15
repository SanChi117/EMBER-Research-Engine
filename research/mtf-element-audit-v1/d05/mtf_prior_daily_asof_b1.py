"""B1/C08: join last CLOSED daily bar to current intraday MTF sources.

This is an availability/as-of join, NOT the author's directional Daily Bias.
The supplied previous-day bar and source-15m segment must be source-checked
against original C08 receipts separately. Never promote a current incomplete
daily bar to available higher-timeframe context.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"mtf-course-v05"/"src"))
from course_primitives_v05 import Bar,TF_MS
from mtf_c08_aggregation_b1 import (
    Source15m,MTFClosedHierarchy,DerivedClosedBar,
    MTFSourceRejected,derive_closed_mtf_from_15m
)
DAY=TF_MS["1d"]
CHILD=TF_MS["15m"]

class KnownDailyRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class PreviousDayEvidence:
    bar: Bar
    symbol: str
    source_id: str
    venue: str="BINANCE"
    market: str="USDM_FUTURES"

@dataclass(frozen=True)
class IntradayKnownContext:
    symbol: str
    as_of_ms: int
    prior_daily_bar: Bar
    prior_daily_known_at_ms: int
    prior_daily_source_id: str
    last_closed_1h: DerivedClosedBar | None
    last_closed_4h: DerivedClosedBar | None
    current_1d: None = None
    status: str="PRIOR_1D_PRICE_CONTEXT_AVAILABLE_NOT_ACADEMIC_DAILY_BIAS"
    readiness: str="NOT_TRADE_READY"

def join_previous_closed_daily(previous:PreviousDayEvidence,
                               current_15m:list[Source15m],
                               as_of_ms:int)->IntradayKnownContext:
    """Proves source-time availability, not source-authenticity nor POI validity."""
    if not isinstance(previous,PreviousDayEvidence) or not isinstance(previous.bar,Bar):
        raise KnownDailyRejected("MISSING_VALID_PREVIOUS_DAILY_SOURCE")
    b=previous.bar
    if (b.tf!="1d" or b.start%DAY or b.end!=b.start+DAY
        or not previous.source_id or not isinstance(previous.source_id,str)):
        raise KnownDailyRejected("INVALID_DAILY_BAR_IDENTITY")
    if previous.venue!="BINANCE" or previous.market!="USDM_FUTURES" or not previous.symbol.endswith("USDT"):
        raise KnownDailyRejected("PREVIOUS_NOT_BINANCE_FUTURES")
    if type(as_of_ms) is not int:
        raise KnownDailyRejected("INVALID_AS_OF")
    if not isinstance(current_15m,list) or not current_15m:
        raise KnownDailyRejected("MISSING_CURRENT_INTRADAY_SOURCE")
    first=current_15m[0]
    if not isinstance(first,Source15m) or not isinstance(first.bar,Bar):
        raise KnownDailyRejected("MALFORMED_15M_SOURCES")
    start=first.bar.start
    if start!=b.end:
        raise KnownDailyRejected("NOT_PREVIOUS_UTC_DAY_SOURCE")
    if as_of_ms<=start or as_of_ms>=start+DAY:
        raise KnownDailyRejected("DAILY_CONTEXT_NOT_VALID_AT_AS_OF")
    if first.symbol!=previous.symbol or first.venue!=previous.venue or first.market!=previous.market:
        raise KnownDailyRejected("PREVIOUS_AND_INTRADAY_MARKET_MISMATCH")
    try:
        mtf=derive_closed_mtf_from_15m(current_15m,as_of_ms)
    except MTFSourceRejected as e:
        raise KnownDailyRejected("INTRADAY_SOURCE_REJECTED_"+e.code) from e
    if mtf.bars_1d:
        raise KnownDailyRejected("CURRENT_DAY_DAILY_HINDSIGHT")
    hour=mtf.bars_1h[-1] if mtf.bars_1h else None
    four=mtf.bars_4h[-1] if mtf.bars_4h else None
    if any(e and e.known_at_ms>as_of_ms for e in (hour,four)):
        raise KnownDailyRejected("HIGHER_TIMEFRAME_AFTER_DECISION")
    return IntradayKnownContext(previous.symbol,as_of_ms,b,b.end,previous.source_id,hour,four)
