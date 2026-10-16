"""D05/F01: typed, fail-closed review of five author TDA branching routes.

Grounded in source text:
  https://drive.google.com/file/d/14KFoZCWoJEue_WmlOyXg0sBZoXsozP2M/view
and source teaching schematic, already catalogued at
  d05/C02_TDA_SOURCE_ROUTE_TOPOLOGY.json
This is topology+known-at QA, *not* geometric academic POI, VC or entry.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
TOPOLOGY=HERE/"C02_TDA_SOURCE_ROUTE_TOPOLOGY.json"
SOURCE_TEXT="https://drive.google.com/file/d/14KFoZCWoJEue_WmlOyXg0sBZoXsozP2M/view"
C08_TIMEFRAMES=frozenset(("15m","1d"))
ORDER={"1w":604800000,"1d":86400000,"4h":14400000,
       "1h":3600000,"15m":900000,"5m":300000}
STEP_TF={
    "DAILY_CONTEXT":"1d",
    "4H_FRACTAL_LIQUIDITY":"4h",
    "4H_VC_POI":"4h",
    "1H_VC_NEW_POI":"1h",
    "1H_VC_POI":"1h",
    "1H_LIQUIDITY_IMB_TRIGGER":"1h",
    "15M_LIQUIDITY_IMB_TRIGGER":"15m",
    "15M_VC_ENTRY":"15m",
    "5M_VC_ENTRY":"5m",
}
KNOWN_ROUTES={
    "ORANGE":("DAILY_CONTEXT","4H_FRACTAL_LIQUIDITY","1H_VC_NEW_POI","15M_VC_ENTRY"),
    "GREEN":("DAILY_CONTEXT","4H_FRACTAL_LIQUIDITY","1H_VC_POI",
             "15M_LIQUIDITY_IMB_TRIGGER","5M_VC_ENTRY"),
    "RED":("DAILY_CONTEXT","4H_VC_POI","1H_LIQUIDITY_IMB_TRIGGER","15M_VC_ENTRY"),
    "BLUE":("DAILY_CONTEXT","4H_VC_POI","1H_VC_NEW_POI",
            "15M_LIQUIDITY_IMB_TRIGGER","5M_VC_ENTRY"),
    "YELLOW":("DAILY_CONTEXT","4H_VC_POI","1H_VC_NEW_POI","15M_VC_ENTRY"),
}
class TDARouteRejected(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

@dataclass(frozen=True)
class RouteStepEvidence:
    name: str
    timeframe: str
    known_at_ms: int
    source_uid: str
    symbol: str
    market: str="BINANCE_USDM_FUTURES"
    course_semantics_approved: bool=False
    c08_native_source_verified: bool=False

@dataclass(frozen=True)
class RouteReview:
    route_color: str
    available_at_ms: int
    step_names: tuple[str,...]
    missing_step_names: tuple[str,...]
    data_gaps: tuple[str,...]
    semantic_gaps: tuple[str,...]
    topology_status: str="AUTHOR_TDA_SOURCE_TOPOLOGY_ONLY"
    readiness: str="NOT_TRADE_READY"

def verify_source_route_schema()->dict:
    """Reject edited/injected flowcharts rather than silently changing source."""
    try:
        raw=json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    except (OSError,ValueError) as e:
        raise TDARouteRejected("MISSING_OR_INVALID_TDA_TOPOLOGY") from e
    paths=raw.get("paths")
    if raw.get("source_image_drive_id")!="12XL6Lk1xZ_qZ_CHiqTucV8_fUYXo7yFv" or (
       raw.get("source_sha256")!="87d1e38b4350625487b63e46376ae4fa919fc248c6875dddd8b22454c2fb4781"):
        raise TDARouteRejected("SOURCE_DIAGRAM_SHA_ID_MISMATCH")
    if not isinstance(paths,list) or len(paths)!=5:
        raise TDARouteRejected("WRONG_ROUTE_COUNT")
    indexed={}
    for p in paths:
        if not isinstance(p,dict) or p.get("color") in indexed:
            raise TDARouteRejected("DUPLICATE_OR_BAD_ROUTE")
        indexed[p["color"]]=p
    if set(indexed)!=set(KNOWN_ROUTES):
        raise TDARouteRejected("ROUTE_COLOR_SET_CHANGED")
    for color,names in KNOWN_ROUTES.items():
        p=indexed[color]
        if tuple(p.get("steps",()))!=names or p.get("entry_tf")!=STEP_TF[names[-1]]:
            raise TDARouteRejected("COURSE_BRANCH_OR_TF_CHANGED")
    if raw.get("approvals",{}).get("numeric_automated_signals_approved")!=0:
        raise TDARouteRejected("ILLEGAL_ACADEMIC_APPROVAL_IN_SOURCE_DIAGRAM")
    return indexed

def inspect_tda_route(color:str,steps:list[RouteStepEvidence],as_of_ms:int)->RouteReview:
    verify_source_route_schema()
    if color not in KNOWN_ROUTES:
        raise TDARouteRejected("UNKNOWN_ROUTE_COLOR")
    if type(as_of_ms) is not int or as_of_ms<0:
        raise TDARouteRejected("INVALID_AS_OF")
    if not isinstance(steps,list) or any(not isinstance(s,RouteStepEvidence) for s in steps):
        raise TDARouteRejected("MALFORMED_ROUTE_STEPS")
    expected=KNOWN_ROUTES[color]
    if len(steps)>len(expected):
        raise TDARouteRejected("EXTRA_ROUTE_STEPS")
    if any(s.name!=expected[i] for i,s in enumerate(steps)):
        raise TDARouteRejected("OUT_OF_ORDER_OR_FALSE_BRANCH")
    if len({s.source_uid for s in steps})!=len(steps) or any(not s.source_uid for s in steps):
        raise TDARouteRejected("MISSING_OR_REUSED_EVENT_SOURCE_UID")
    if steps and (not steps[0].symbol or any(s.symbol!=steps[0].symbol for s in steps)):
        raise TDARouteRejected("CROSS_SYMBOL_ROUTE")
    last=-1
    for s in steps:
        if s.market!="BINANCE_USDM_FUTURES":
            raise TDARouteRejected("WRONG_SOURCE_MARKET")
        if s.timeframe!=STEP_TF[s.name]:
            raise TDARouteRejected("TIMEFRAME_DOES_NOT_MATCH_AUTHOR_BRANCH")
        if type(s.known_at_ms) is not int or s.known_at_ms>as_of_ms or s.known_at_ms<last:
            raise TDARouteRejected("LOOKAHEAD_OR_UNORDERED_EVIDENCE")
        if s.known_at_ms%ORDER[s.timeframe]:
            raise TDARouteRejected("EVENT_KNOWN_AT_NOT_CLOSED_TF")
        last=s.known_at_ms
    data_gaps=tuple(s.name for s in steps if s.timeframe=="5m" and s.c08_native_source_verified)
    # A Boolean receipt declared by a caller is not proof of a native C08 5m
    # archive; no 5m C08 data exists in the currently approved manifest.
    source_gaps=tuple(s.name for s in steps if s.timeframe=="5m" or
                      (s.timeframe in C08_TIMEFRAMES and not s.c08_native_source_verified))
    semantic_gaps=tuple(s.name for s in steps if not s.course_semantics_approved)
    return RouteReview(color,as_of_ms,tuple(s.name for s in steps),
                       tuple(expected[len(steps):]),source_gaps,
                       semantic_gaps)
