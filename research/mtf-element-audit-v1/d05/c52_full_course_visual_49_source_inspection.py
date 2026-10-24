"""C52: direct visual inspection of all 49 course PNG; strictly source-only.

Eight full market screenshots have VERIFIED READABLE TradingView publisher
headers (EURUSD OANDA/SAXO, 2024/2025 PUBLICATION timestamps, not candle dates).
Other cropped market charts lack verifiable source header. Teaching diagrams
and nested desktop screenshots are NOT trade chart-positive goldens.
No crypto 2026 original source can be linked to these FX images by assumption.
Images are retained privately on owner Drive; only IDs, hashes of 8
visually source-verified full charts and conservative observations stored.
"""
from dataclasses import dataclass
from pathlib import Path
import json
from c51_academic_visual_source_golden_gate import audited_inventory,INVENTORY

FULL_SOURCE_HEADERS={
 "1b78gDdyIZO21QWoKKRUK47PbYyq35U3C":("EURUSD","OANDA","4H","2025-01-20 14:25 UTC+02:00","b47e0e794b17afa5e82b1640687e6083ce03a80a848b778f38b597c602c65bec",128782,(2475,1241)),
 "1F0LLCklPaPNCBWHwVpsKUPqp1hdsh35p":("EURUSD","SAXO","4H","2025-01-07 19:48 UTC+01:00","0652541c0bb64317beb86a2b20c4cb883eb69fe8bb25f70a1060e341249d551f",101488,(2274,1241)),
 "1JlQcYmNst3GEp4ohLArGVL9eqJi8i2-b":("EURUSD","SAXO","4H","2025-01-07 19:49 UTC+01:00","40a9129fc3653375a41e6095f2872308cfdf1bcdae3ac35b88e7ccbba49f9069",100584,(2274,1241)),
 "153eXt9lGrrhRumOfFsLQryS-3FBBX8Vl":("EURUSD","OANDA","4H","2024-05-26 13:08 UTC+02:00","de7ce6822ba004a2c5ea2a5fcf6ef40afff82e9ddf1ba5b487896d9cb96b2342",63578,(1835,850)),
 "1HuwTCxVYvm_YSmaPpZ2RxD7PA9UuzwtC":("EURUSD","OANDA","1H","2024-05-26 13:09 UTC+02:00","6e0b5bb26b3639e35e264e5c9910b1fa0b583a457b41bd7809d8197a1bfa383f",62740,(1835,850)),
 "1obj4bBVqplvrL2E_iNHXOHoOaDhj5gKx":("EURUSD","OANDA","15M","2024-05-26 13:10 UTC+02:00","95cfbcc5079236202b0639e0a95991367564055acdf988d82e2cac6c3851a50e",78547,(1835,850)),
 "1OeV2mNl-nlbvGNPPJYiFVtDSnB3lFCC3":("EURUSD","OANDA","4H","2024-05-26 13:26 UTC+02:00","6ceeba623f486aca67da6967ac84adb9458ccb470c414c094741a608cbf0bbfa",65265,(1835,850)),
 "1tJW5eTs2TRK2mYTOgQxPJtcnSz41-DIP":("EURUSD","OANDA","1H","2024-05-26 13:27 UTC+02:00","9677783dd1af287b403fb69f3ddacedfb44e706ea8044fb3e13551dd7d1e6946",67216,(1835,850)),
}
CONCEPTUAL_IDS={
 "1L7sXn8-RHn7p1J8-8qDs8XbRDyCJYoDN", # POI annotated conceptual SNR
 "1Qa6fxonLzWkxbxTPO3jo5oNJ3DNeCVdd", # POI OB diagram
 "1IwN9b1dLQFj1_pPKE8RA-wqMdMf1UBo-", # POI RB diagram
 "1m_Dbbs1XrkPGh4y3TY7czaLGRCBc_z71", # POI FVG diagram
 "15iGjZdGhX-ScEB1TXyMxnvD5LHS8CnJT", # entry conceptual route
 "1YziNr_aqDbfUMhrt1b5zfg31yrFR-qCR", # entry conceptual route
 "1IhQMc8F6Ir1ZXA2Ymit3RGIhhu0T-OWg", # entry conceptual route
 "1FdyrtyZYzYcw_y2MZn_s6jrknQjiWR5L", # explicit text source 4H->1H->15m; 1H->15m->5m
}
CATEGORIES=(
 "FULL_CHART_READABLE_EURUSD_SOURCE_HEADER",
 "CROPPED_MARKET_STYLE_CHART_NO_VERIFIABLE_PROVIDER",
 "CONCEPTUAL_OR_COURSE_RULE_DIAGRAM",
 "DESKTOP_SCREENSHOT_NESTED_LESSON_VIEW",
)
ACADEMIC_BARRIERS=(
 "PUBLISH_TIMESTAMP_NOT_ORIGINAL_CANDLE_CLOSE",
 "NO_INDEPENDENT_EXCHANGE_HISTORICAL_OHLC_SAME_FEED_MATCH",
 "NO_AUTHOR_ENTRY_SL_TP_CANDLE_TIMESTAMP_GOLDEN",
 "SOURCE_VERIFIED_POI_FIRST_TEST_VOLUME_CONFIRMATION_MISSING",
 "NO_CAUSAL_ENTRY_OR_ORDER_FILL_REPRODUCTION",
)

@dataclass(frozen=True)
class CourseFigure:
    drive_id:str
    source_folder:str
    image_name:str
    original_drive_url:str
    inspected:bool
    figure_kind:str
    visible_instrument:str|None
    visible_data_provider:str|None
    visible_timeframe:str|None
    visible_tradingview_publication_timestamp:str|None
    original_market_bar_timestamp:str|None
    original_author_annotated_trade_golden:bool=False
    independently_valid_market_source_raw_bar:bool=False
    study_only:bool=True
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def review_all_original_course_figures(*,author_label_override=None,
            market_source_override=None,
            physical_private_binary_validator=None):
    if author_label_override is not None or market_source_override is not None:
        raise ValueError("C52_UNVERIFIED_AUTHOR_LABEL_OR_EXTERNAL_MARKET_SOURCE_PROMOTION")
    sources,old=audited_inventory()
    if (len(sources)!=49 or len(old)!=6 or
        len(FULL_SOURCE_HEADERS)!=8 or len(CONCEPTUAL_IDS)!=8):
        raise ValueError("C52_SOURCE_REGISTRY_COUNT_DRIFT")
    if not set(FULL_SOURCE_HEADERS).issubset(sources) or not CONCEPTUAL_IDS.issubset(sources):
        raise ValueError("C52_MISSING_VISUALLY_VERIFIED_COURSE_IMAGE_ID")
    if set(FULL_SOURCE_HEADERS)&CONCEPTUAL_IDS:
        raise ValueError("C52_AMBIGUOUS_IMAGE_CATEGORY")
    # Verify independently captured original PNG binary dimensions/hash when
    # a trustworthy caller explicitly supplies a source-digest validator.
    # This is optional: ordinary GitHub CI cannot read private Drive images.
    if physical_private_binary_validator is not None:
        for ident,meta in FULL_SOURCE_HEADERS.items():
            if physical_private_binary_validator(ident,meta[4],meta[5],meta[6]) is not True:
                raise ValueError("C52_UNVERIFIED_ORIGINAL_DRIVE_PNG_BYTES")
    figure_list=[]
    for ident,(folder,f) in sorted(sources.items(),key=lambda z:z[0]):
        if ident in FULL_SOURCE_HEADERS:
            sym,provider,tf,publication,_,_,_=FULL_SOURCE_HEADERS[ident]
            kind=CATEGORIES[0]
        elif ident in CONCEPTUAL_IDS:
            kind=CATEGORIES[2];sym=provider=tf=publication=None
        elif folder in ("POI",):
            kind=CATEGORIES[1];sym=provider=tf=publication=None
        else:
            kind=CATEGORIES[3];sym=provider=tf=publication=None
        figure_list.append(CourseFigure(ident,folder,f["name"],f["drive_url"],
            True,kind,sym,provider,tf,publication,None))
    sizes={name:sum(x.figure_kind==name for x in figure_list) for name in CATEGORIES}
    if sizes!={
        CATEGORIES[0]:8,CATEGORIES[1]:19,
        CATEGORIES[2]:8,CATEGORIES[3]:14,
    }:raise ValueError("C52_ALL_49_VISUAL_SOURCE_TYPES_DRIFT")
    return tuple(figure_list)

def assert_c52_course_author_golden(*,figures,claimed_author_entry=False,
                      claimed_raw_market_timestamp=None,claimed_provider_match=None):
    if (claimed_author_entry or claimed_raw_market_timestamp is not None
        or claimed_provider_match is not None):
        raise ValueError("C52_SOURCE_IMAGE_CANNOT_PROVE_ACADEMIC_TRADE_GOLDEN")
    if (len(figures)!=49 or
        any(not isinstance(x,CourseFigure) or
            x.original_author_annotated_trade_golden or
            x.independently_valid_market_source_raw_bar or
            x.orders or x.trades or x.readiness!="NOT_TRADE_READY"
            or x.original_market_bar_timestamp is not None for x in figures)):
        raise ValueError("C52_UNTRUSTED_COURSE_VISUAL_GOLDEN_REVIEW")
    return {"figures":49,"provider_timeframe_headers":8,
        "known_original_raw_candle_golden":0,"author_verified_entry":0,
        "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"}
