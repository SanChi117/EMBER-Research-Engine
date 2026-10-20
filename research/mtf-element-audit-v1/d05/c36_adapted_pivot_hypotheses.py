"""C36 Adapted BOS Pivot Lab: RESEARCH-ONLY deterministic selection hypotheses.

ACADEMIC CORE / C20-C35 cannot be changed or silently imported as author
BOS selection. All 4 routes are *proposed* adapted pivot choices over the
previously frozen C33 candidates that were known at C21 BOS BAR START.

IMPORTANT: C33 is a C21-latest-conditioned retrospective sample. Other
levels are NOT necessarily BOS breaks at C21's break time. The selected
pivot is NOT an entry, historical fill, author label, forward signal or
strategy metric. No live orders or PAPER trade commands.
"""
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
import re

THREE=180_000
START_MS=1788220800000
END_MS=1790985600000
VALIDATION_START_MS=1789603200000 # 2026-09-17T00:00:00Z
HOLDOUT_START_MS=1790294400000    # 2026-09-25T00:00:00Z
FROZEN_C33_SHA="fa17524a942d8227e8ec33e3d1e2c93c860669df"
VARIANTS=(
    "LATEST_CONFIRMED_V1",    # frozen C21 baseline, reference only
    "EARLIEST_CONFIRMED_V1",  # alternate historic technical hypothesis
    "DEEP_RAID_SIDE_V1",      # farthest beyond raided 1h level
    "NEAREST_RAID_SIDE_V1",   # closest eligible level past raided 1h level
)

@dataclass(frozen=True)
class AdaptedPivotChoice:
    hypothesis_id:str
    as_of_ms:int
    original_event_row_id:str
    selected_swing_center_ms:int
    selected_swing_known_ms:int
    selected_level:str
    selected_native_center3m_sha_row_id:str
    differs_from_c21_last:bool
    selection_scope:str="C33_PREKNOWN_SOURCE_OPTIONS_ONLY"
    author_bos_validated:bool=False
    is_bos_break_at_event:bool=False
    paper_signal_allowed:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _strict_bar_id(raw_id,ms):
    if (type(raw_id)!=str or
        re.fullmatch("[0-9a-f]{64}:"+str(ms),raw_id) is None):
        raise ValueError("C36_FABRICATED_ORIGINAL_3M_BAR_PROVENANCE")

def _validate_case(case,*,as_of_ms):
    if type(case)!=dict or type(as_of_ms)!=int:
        raise ValueError("C36_UNTRUSTED_CASE")
    if case.get("readiness")!="NOT_TRADE_READY" or case.get("order_allowed") is not False or case.get("trades")!=[]:
        raise ValueError("C36_AUTHOR_READY_OR_ORDER_FORGERY")
    if case.get("instructor_bos_status")!="NEEDS_AUTHOR_1H_3M_POSITIVE_NEGATIVE_GOLDENS":
        raise ValueError("C36_FORGED_AUTHOR_LABEL")
    if case.get("side") not in ("SHORT","LONG") or case.get("symbol") not in (
        "BCHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT"):
        raise ValueError("C36_INVALID_SOURCE_MARKET_OR_SIDE")
    at=case.get("break_3m_bar_start_ms")
    if type(at)!=int or not START_MS<=at<END_MS or as_of_ms!=at:
        raise ValueError("C36_ASOF_MUST_EQUAL_C21_BREAK_BAR_START")
    close_known=case.get("break_3m_close_known_ms")
    if type(close_known)!=int or close_known!=at+THREE:
        raise ValueError("C36_FUTURE_BREAK_BAR_OR_INVALID_CLOSE")
    _strict_bar_id(case.get("original_break3m_source_row_id"),at)
    raid_ms=case.get("raid_start_ms")
    confirmed=case.get("raid_confirmed_ms")
    if (type(raid_ms)!=int or type(confirmed)!=int or
        raid_ms>=confirmed or confirmed>at):
        raise ValueError("C36_RAID_NOT_CONFIRMED_AT_ASOF")
    try:
        raid_level=Decimal(case["raid_level"])
        raid_extreme=Decimal(case["raid_extreme"])
    except (KeyError,TypeError,ValueError,ArithmeticError) as exc:
        raise ValueError("C36_BAD_RAID_DECIMAL") from exc
    if not all(x.is_finite() and x>0 for x in (raid_level,raid_extreme)):
        raise ValueError("C36_BAD_RAID_DECIMAL")
    if case["side"]=="SHORT" and raid_extreme<=raid_level:
        raise ValueError("C36_MISSING_REAL_WICK_BSL_RAID")
    if case["side"]=="LONG" and raid_extreme>=raid_level:
        raise ValueError("C36_MISSING_REAL_WICK_SSL_RAID")
    candidates=case.get("competing_swings")
    if not isinstance(candidates,list) or not candidates:
        raise ValueError("C36_MISSING_C33_CANDIDATES")
    if (case.get("competing_preknown_swing_count")!=len(candidates) or
        case.get("alternative_preknown_swings")!=len(candidates)-1 or
        case.get("proxy_is_latest_preknown") is not True):
        raise ValueError("C36_C33_RESEARCH_PARENT_TAMPER")
    digest=hashlib.sha256(json.dumps(candidates,sort_keys=True,
          separators=(",",":")).encode()).hexdigest()
    if digest!=case.get("known_eligible_swing_set_sha256"):
        raise ValueError("C36_C33_CANDIDATE_SET_SHA_DRIFT")
    if case.get("original_break3m_source_row_id") is None:
        raise ValueError("C36_NO_ORIGINAL_BREAK_BAR")
    chosen=[]
    identities=set()
    for item in candidates:
        if type(item)!=dict or item.get("kind")!=("LOW" if case["side"]=="SHORT" else "HIGH"):
            raise ValueError("C36_WRONG_3M_SWING_KIND")
        ms=item.get("center_ms")
        known=item.get("known_ms")
        if (type(ms)!=int or type(known)!=int or
            ms<raid_ms or known!=ms+2*THREE or
            known>at or ms>=at):
            raise ValueError("C36_3M_SWING_NOT_KNOWN_AT_EVENT")
        for key,offset in (
            ("original_left3m_sha_row_id",-THREE),
            ("original_center3m_sha_row_id",0),
            ("original_right3m_sha_row_id",THREE)):
            _strict_bar_id(item.get(key),ms+offset)
        try:
            price=Decimal(item["level"])
        except (KeyError,TypeError,ValueError,ArithmeticError) as exc:
            raise ValueError("C36_INVALID_SWING_LEVEL") from exc
        if not price.is_finite() or price<=0:
            raise ValueError("C36_INVALID_SWING_LEVEL")
        if (case["side"]=="SHORT" and price>=raid_level or
            case["side"]=="LONG" and price<=raid_level):
            raise ValueError("C36_WRONG_SIDE_OF_RAID")
        if (item.get("chosen_by_author") is not False or
            item.get("route_status")!="SOURCE_ONLY_AUTHOR_BOS_CHOICE_UNKNOWN"):
            raise ValueError("C36_AUTHOR_PIVOT_FORGERY")
        if type(item.get("selected_by_frozen_c21_proxy"))!=bool:
            raise ValueError("C36_INVALID_C21_PROXY_FLAG")
        identity=ms # only one same-side strict pivot per center bar
        if identity in identities:
            raise ValueError("C36_DUPLICATE_SWING_CANDIDATE")
        identities.add(identity)
        chosen.append((item,price))
    base=[x for x,_ in chosen if x["selected_by_frozen_c21_proxy"]]
    if len(base)!=1:
        raise ValueError("C36_C21_BASELINE_NOT_UNIQUE")
    if (base[0]["center_ms"]!=case.get("frozen_c21_proxy_swing_center_ms") or
        base[0]["level"]!=case.get("frozen_c21_proxy_swing_level")):
        raise ValueError("C36_C21_BASELINE_PARENT_DRIFT")
    if base[0]["known_ms"]!=max(item["known_ms"] for item,_ in chosen):
        raise ValueError("C36_C21_NOT_LAST_PREKNOWN")
    return chosen,base[0]

def _rank(item,price):
    return (item["known_ms"],item["center_ms"],
            item["original_center3m_sha_row_id"])

def choose_adapted_pivot(case,hypothesis_id,*,as_of_ms):
    if hypothesis_id not in VARIANTS:
        raise ValueError("C36_UNREGISTERED_ADAPTED_HYPOTHESIS")
    rows,baseline=_validate_case(case,as_of_ms=as_of_ms)
    if hypothesis_id=="LATEST_CONFIRMED_V1":
        chosen=max(rows,key=lambda v:_rank(*v))[0]
    elif hypothesis_id=="EARLIEST_CONFIRMED_V1":
        chosen=min(rows,key=lambda v:_rank(*v))[0]
    elif hypothesis_id=="DEEP_RAID_SIDE_V1":
        chosen=min(rows,key=lambda v:(v[1],-v[0]["known_ms"]))[0] if case["side"]=="SHORT" else (
            max(rows,key=lambda v:(v[1],v[0]["known_ms"]))[0])
    else: # NEAREST_RAID_SIDE_V1
        chosen=max(rows,key=lambda v:(v[1],v[0]["known_ms"]))[0] if case["side"]=="SHORT" else (
            min(rows,key=lambda v:(v[1],-v[0]["known_ms"]))[0])
    if hypothesis_id=="LATEST_CONFIRMED_V1" and chosen!=baseline:
        raise ValueError("C36_FROZEN_C21_REPLICA_MISMATCH")
    return AdaptedPivotChoice(hypothesis_id,as_of_ms,
        case["original_break3m_source_row_id"],chosen["center_ms"],
        chosen["known_ms"],chosen["level"],
        chosen["original_center3m_sha_row_id"],chosen!=baseline)

def chronological_partition(ms):
    if type(ms)!=int or not START_MS<=ms<END_MS:
        raise ValueError("C36_OUTSIDE_FROZEN_SOURCE_PERIOD")
    if ms<VALIDATION_START_MS:return "DEVELOPMENT"
    if ms<HOLDOUT_START_MS:return "VALIDATION"
    return "HOLDOUT"

def summarize_frozen_c33(c33):
    if (type(c33)!=dict or c33.get("schema")!="EMBER_C33_ORIGINAL_NATIVE_3M_PREKNOWN_BOS_PIVOT_COMPETITION_V1"
        or c33.get("readiness")!="NOT_TRADE_READY" or
        c33.get("author_selected_BOS_goldens")!=0 or c33.get("orders_created")!=0 or
        c33.get("trades_created")!=0):
        raise ValueError("C36_UNTRUSTED_ORIGINAL_C33_RECEIPT")
    markets=c33.get("markets")
    if type(markets)!=list or len(markets)!=5:
        raise ValueError("C36_ORIGINAL_5_MARKETS_NOT_FOUND")
    counts={v:{"n":0,"agrees_with_c21":0} for v in VARIANTS}
    partition={split:{"events":0,"by_variant":{
        variant:{"n":0,"agrees_with_c21":0} for variant in VARIANTS}}
        for split in ("DEVELOPMENT","VALIDATION","HOLDOUT")}
    by_market={}
    detail=[]
    seen=set()
    for market in markets:
        sym=market.get("symbol")
        if sym in seen or sym not in ("BCHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT"):
            raise ValueError("C36_DUPLICATE_OR_UNKNOWN_MARKET")
        seen.add(sym)
        cases=market.get("source_case_competing_swings")
        if type(cases)!=list:
            raise ValueError("C36_MARKET_MISSING_SOURCE_CASES")
        by_market[sym]={"events":len(cases),"by_variant":{
            v:{"n":0,"agrees_with_c21":0} for v in VARIANTS}}
        for case in cases:
            if case.get("symbol")!=sym:
                raise ValueError("C36_C33_SYMBOL_DRIFT")
            asof=case.get("break_3m_bar_start_ms")
            split=chronological_partition(asof)
            partition[split]["events"]+=1
            identity=(sym,case["original_break3m_source_row_id"])
            if identity in seen:
                raise ValueError("C36_DUPLICATE_EVENT")
            seen.add(identity)
            result={}
            for variant in VARIANTS:
                option=choose_adapted_pivot(case,variant,as_of_ms=asof)
                if option.paper_signal_allowed or option.orders or option.trades or option.author_bos_validated:
                    raise ValueError("C36_UNAUTHORIZED_TRADE")
                for bucket in (counts[variant],
                     partition[split]["by_variant"][variant],
                     by_market[sym]["by_variant"][variant]):
                    bucket["n"]+=1
                    bucket["agrees_with_c21"]+=int(not option.differs_from_c21_last)
                result[variant]={"center_ms":option.selected_swing_center_ms,
                    "level":option.selected_level,
                    "native_center_row":option.selected_native_center3m_sha_row_id}
            detail.append({"symbol":sym,"break_bar_row_id":identity[1],
                 "break_bar_start_ms":asof,"partition":split,
                 "c33_candidate_count":len(case["competing_swings"]),
                 "hypotheses":result,
                 "readiness":"NOT_TRADE_READY"})
    total=sum(v["events"] for v in by_market.values())
    if (total!=539 or sum(s["events"] for s in partition.values())!=539 or
        c33.get("totals",{}).get("original_c21_parent_edges")!=539 or
        c33.get("totals",{}).get("total_competing_preknown_swings")!=5285):
        raise ValueError("C36_FROZEN_PARENT_COUNTS_CHANGED")
    if counts["LATEST_CONFIRMED_V1"]["agrees_with_c21"]!=539:
        raise ValueError("C36_C21_BASELINE_DIVERGENCE")
    return {"schema":"EMBER_C36_ADAPTED_BOS_PIVOT_RESEARCH_COMPARE_V1",
        "source_c33_git_blob":FROZEN_C33_SHA,
        "sample_warning":"C21-conditioned closed-break retrospective source event set. Alternative pivot MAY NOT have BOS close at same event. NO trade/PnL/author inference.",
        "original_parent_events":539,"original_swing_candidate_links":5285,
        "variants":list(VARIANTS),"period_partitions":partition,
        "by_market":by_market,"variant_agreement_only":counts,
        "hypothesis_case_detail":detail,
        "author_selected_BOS_goldens":0,"orders_created":0,
        "trades_created":0,"readiness":"NOT_TRADE_READY"}
