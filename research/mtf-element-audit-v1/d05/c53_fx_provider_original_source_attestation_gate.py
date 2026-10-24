"""C53 independent FX provenance gate for the 8 genuine course EURUSD figures.

Important: original screenshots are TradingView PUBLISHED on certain dates,
not candles necessarily from those dates. Raw historical candles shown in the
8 chart pictures are NOT presently obtained from exact OANDA/SAXO feed.
A validated provider-only OHLC receipt cannot certify an academic POI/VC
chart golden without exact candle-time, price-basis and visually matched OHLC.

Public API documentation (not downloaded price evidence):
- developer.oanda.com/rest-live-v20/instrument-ep/
- developer.saxo/openapi/referencedocs/chart/v3/charts/get__chart
- help.oanda.com historical vs live group data differences.
"""
from dataclasses import dataclass
from decimal import Decimal
import re
from c52_full_course_visual_49_source_inspection import (
 FULL_SOURCE_HEADERS,review_all_original_course_figures,CATEGORIES)
HOUR=60*60*1000
TF_MILLIS={"15M":15*60*1000,"1H":HOUR,"4H":4*HOUR}
PRICE_SIDES=("MID","BID","ASK")
AUTHORS_GOLDENS_REQUIRED=(
 "MATCHED_PROVIDER_AND_PRICE_GROUP_ORIGINALLY_SHOWN_BY_TRADINGVIEW",
 "ACTUAL_SCREENSHOT_BAR_TIME_AND_SOURCE_RAW_CANDLE_ID",
 "EXACT_CHART_BAR_OHLC_LEVEL_CROSSCHECK_NO_LOOKAHEAD",
 "TRUE_AUTHOR_TYPED_POI_FIRST_TEST_AND_ROUTE_VC",
 "ACADEMIC_STRUCTURAL_STRONG_HL_FTA_ENTRY_SL_TP",
 "NEGATIVE_GOLDEN_REVIEW_AND_FORWARD_OOS_SEPARATELY",
)
OFFICIAL_DOCUMENTATION={
 "OANDA":"https://developer.oanda.com/rest-live-v20/instrument-ep/",
 "SAXO":"https://developer.saxobank.com/openapi/referencedocs/chart/v3/charts/get__chart",
}
STATES=("SOURCE_NOT_RETRIEVED","PROVIDER_ONLY_SOURCE_RECEIVED_CHART_CANDLE_UNALIGNED")

@dataclass(frozen=True)
class SourceBarReceipt:
    """Data-only receipt. Cannot turn into author validation by supplying flags."""
    provider:str
    instrument:str
    timeframe:str
    pricing_component:str
    original_provider_source_endpoint:str
    native_source_digest_sha256:str
    start_ms:int
    closed_known_ms:int
    open:str
    high:str
    low:str
    close:str
    source_closed_bar_id:str
    fully_closed:bool
    source_original_chart_match_author_verified:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class CourseOriginalFxSourceGate:
    original_course_image_id:str
    original_tradingview_provider:str
    original_tradingview_instrument:str
    original_tradingview_tf:str
    chart_publication_time_NOT_market_bar_time:str
    raw_source_receipt_present:bool
    source_attestation_state:str
    screenshot_bar_timestamp_verified:bool=False
    screenshot_quote_price_side_verified:bool=False
    independently_matched_chart_bar_ohlc:bool=False
    actual_original_author_POI_or_VC_golden:bool=False
    author_entry_trade_ready:bool=False
    required_missing_goldens:tuple[str,...]=AUTHORS_GOLDENS_REQUIRED
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _validated_receipt(r,*,expected_provider,expected_tf):
    if not isinstance(r,SourceBarReceipt):
        raise ValueError("C53_UNTRUSTED_RAW_FX_SOURCE_RECEIPT")
    if (r.source_original_chart_match_author_verified or r.orders or r.trades or
        not r.fully_closed):
        raise ValueError("C53_FORGED_AUTHOR_CHART_MATCH_OR_UNCLOSED_DATA")
    if (r.provider!=expected_provider or r.instrument!="EURUSD" or
        r.timeframe!=expected_tf or r.timeframe not in TF_MILLIS or
        r.provider not in OFFICIAL_DOCUMENTATION or
        r.pricing_component not in PRICE_SIDES):
        raise ValueError("C53_PROVIDER_INSTRUMENT_TF_OR_PRICE_SIDE_MISMATCH")
    if not r.original_provider_source_endpoint.startswith(
        "https://") or not (
        ("oanda" in r.original_provider_source_endpoint.lower() if r.provider=="OANDA"
        else "saxo" in r.original_provider_source_endpoint.lower())):
        raise ValueError("C53_CANDLE_SOURCE_ENDPOINT_WRONG_PROVIDER")
    if (not re.fullmatch(r"[a-f0-9]{64}",r.native_source_digest_sha256)
        or not r.source_closed_bar_id or
        type(r.start_ms) is not int or type(r.closed_known_ms) is not int or
        r.start_ms%TF_MILLIS[r.timeframe] or
        r.closed_known_ms!=r.start_ms+TF_MILLIS[r.timeframe]):
        raise ValueError("C53_NONCAUSAL_OR_UNTRACEABLE_FX_OHLC_ID")
    raw=[]
    for x in (r.open,r.high,r.low,r.close):
        if not isinstance(x,str):
            raise ValueError("C53_NONDECIMAL_FX_OHLC")
        try:d=Decimal(x)
        except Exception:raise ValueError("C53_NONDECIMAL_FX_OHLC")
        if not d.is_finite():raise ValueError("C53_NONDECIMAL_FX_OHLC")
        raw.append(d)
    op,hi,lo,cl=raw
    if not (Decimal("0.5")<lo<=min(op,cl)<=max(op,cl)<=hi<Decimal("2.0")):
        raise ValueError("C53_MALFORMED_OR_FOREIGN_FX_OHLC")
    return True

def assess_course_figure_original_fx_source(image_id,*,market_receipt=None,
                                            proposed_raw_author_golden=False,
                                            proposed_screenshot_candle_time=None):
    if image_id not in FULL_SOURCE_HEADERS:
        raise ValueError("C53_NOT_ONE_OF_EIGHT_ORIGINAL_READABLE_FX_CHARTS")
    if proposed_raw_author_golden or proposed_screenshot_candle_time is not None:
        raise ValueError("C53_FORGED_AUTHOR_SOURCE_TIME_OR_ENTRY_GOLDEN")
    figures={x.drive_id:x for x in review_all_original_course_figures()}
    fig=figures[image_id]
    provider=fig.visible_data_provider
    tf=fig.visible_timeframe
    if (fig.figure_kind!=CATEGORIES[0] or provider not in OFFICIAL_DOCUMENTATION
        or tf not in TF_MILLIS or fig.visible_instrument!="EURUSD"
        or fig.original_market_bar_timestamp is not None):
        raise ValueError("C53_CORRUPTED_C52_FX_SOURCE_HEADER")
    if market_receipt is not None:
        _validated_receipt(market_receipt,expected_provider=provider,expected_tf=tf)
    return CourseOriginalFxSourceGate(image_id,provider,fig.visible_instrument,
        tf,fig.visible_tradingview_publication_timestamp,
        market_receipt is not None,STATES[int(market_receipt is not None)])

def review_all_eight_original_course_fx_sources():
    result=tuple(assess_course_figure_original_fx_source(k)
                 for k in sorted(FULL_SOURCE_HEADERS))
    assert len(result)==8
    assert all(x.source_attestation_state==STATES[0] for x in result)
    assert all(x.orders==x.trades==() and x.readiness=="NOT_TRADE_READY"
               for x in result)
    return result
