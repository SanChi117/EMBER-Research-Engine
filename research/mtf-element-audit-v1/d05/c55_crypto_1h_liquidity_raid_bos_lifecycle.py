"""C55 independent 1H liquidity raid -> 3M close BOS life-cycle audit.

Reuse frozen C20B 1H confirmed fractal and C21B original 3M observer;
do NOT rewrite the academic engine or promote a technical swing to author BOS.
Every state is source-only, time-ordered and fail-closed. Only ORIGINAL
USDT-M crypto, PAPER, zero orders, fills, outcomes or promises.
"""
from dataclasses import dataclass
from decimal import Decimal
from c21_native3m_source_bridge import C21Native3mResult,THREE
from c21b_original_3m_raid_break_geometry import (
    observe_native3m_raid_break,_source,_hours,ThreeBreak,ThreeObservation)
from c20b_hourly_fractal_source_observer import (
    observe_fractals_and_first_breach,FirstWickObservation)
HOUR=3600000
ROUTE="C_1H_RAID_3M_BOS"
STATES=(
    "LEVEL_PREKNOWN_NO_FIRST_BREACH",
    "FIRST_BREACH_BODY_NOT_WICK_RAID",
    "FIRST_WICK_NEEDS_NEXT_CLOSED_1H",
    "FIRST_WICK_NONFRACTAL",
    "CONFIRMED_1H_RAID_NO_CLOSED_3M_BREAK",
    "CONFIRMED_1H_RAID_WITH_ADAPTED_3M_CLOSED_BREAK",
)
BLOCKERS=(
    "ACADEMIC_LIQUIDITY_SOURCE_NOT_AUTHOR_VERIFIED",
    "ACADEMIC_BOS_SWING_SELECTION_NOT_VERIFIED",
    "ACADEMIC_FULL_4H_1H_ROUTE_CONTEXT_NOT_VERIFIED",
    "ACADEMIC_ENTRY_SL_TP_FTA_NOT_VERIFIED",
    "NO_FILLS_OR_INDEPENDENT_FORWARD_TEST",
)
@dataclass(frozen=True)
class LiquidityLifecycle:
    symbol:str
    source_as_of_ms:int
    route:str
    hourly_liquidity_kind:str
    hourly_fractal_center_ms:int
    liquidity_price:Decimal
    hourly_liquidity_known_ms:int
    source_1h_three_bar_original3m_ids:tuple[str,...]
    first_breach_start_ms:int|None
    first_breach_close_ms:int|None
    first_raid_confirmed_known_ms:int|None
    confirmed_raid_extreme:Decimal|None
    adapted_swing_known_ms:int|None
    adapted_break_close_known_ms:int|None
    adapted_break_original3m_id:str|None
    source_state:str
    academic_bos_verified:bool=False
    academic_entry_verified:bool=False
    source_blockers:tuple[str,...]=BLOCKERS
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C55LifecycleReview:
    symbol:str
    as_of_ms:int
    original_closed_native3m_count:int
    complete_1h_count:int
    preknown_1h_fractal_liquidity_levels:int
    first_confirmed_wick_raids:int
    adapted_closed_native3m_breaks:int
    lifecycle:tuple[LiquidityLifecycle,...]
    academic_author_confirmed_bos:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def classify_raid(raid,observed_break,*,symbol,as_of_ms):
    if not isinstance(raid,FirstWickObservation):
        raise ValueError("C55_UNTRUSTED_FIRST_WICK_SOURCE")
    p=raid.fractal
    if (p.kind not in ("BSL","SSL") or
        not isinstance(p.level,Decimal) or not p.level.is_finite() or p.level<=0 or
        type(p.center_ms) is not int or type(p.known_ms) is not int or
        p.known_ms>as_of_ms or p.known_ms<=p.center_ms or
        len(p.source_rows)!=60 or
        any(not isinstance(i,str) or ":" not in i for i in p.source_rows)):
        raise ValueError("C55_UNTRUSTED_PREKNOWN_1H_LIQUIDITY")
    if (raid.first_breach_ms is None)!=(raid.first_breach_close_ms is None):
        raise ValueError("C55_PARTIAL_FIRST_BREACH_SOURCE")
    if raid.first_breach_ms is None:
        if raid.verdict!="NO_FIRST_BREACH" or raid.confirmed_at_ms is not None or observed_break is not None or raid.extreme is not None:
            raise ValueError("C55_FORGED_EVENT_WITHOUT_FIRST_BREACH")
        state=STATES[0]
    else:
        if (type(raid.first_breach_ms) is not int or
            type(raid.first_breach_close_ms) is not int or
            raid.first_breach_ms<p.known_ms or
            raid.first_breach_close_ms!=raid.first_breach_ms+HOUR or
            raid.first_breach_close_ms>as_of_ms or
            not isinstance(raid.extreme,Decimal) or not raid.extreme.is_finite() or
            (raid.extreme<=p.level if p.kind=="BSL" else raid.extreme>=p.level)):
            raise ValueError("C55_FIRST_BREACH_NOT_CAUSALLY_PREKNOWN")
        if raid.verdict=="FIRST_BREACH_BODY":
            state=STATES[1]
        elif raid.verdict=="WICK_NEEDS_FOLLOWING_CLOSED_HOUR":
            state=STATES[2]
        elif raid.verdict=="WICK_NONFRACTAL":
            state=STATES[3]
        elif raid.verdict=="WICK_FRACTAL_GEOMETRY":
            state=STATES[5] if observed_break is not None else STATES[4]
        else:
            raise ValueError("C55_UNKNOWN_FIRST_WICK_LIFECYCLE")
        if raid.verdict=="WICK_FRACTAL_GEOMETRY":
            if (type(raid.confirmed_at_ms) is not int or
                raid.confirmed_at_ms!=raid.first_breach_close_ms+HOUR or
                raid.confirmed_at_ms>as_of_ms):
                raise ValueError("C55_NOT_A_CLOSED_FOLLOWING_1H_CONFIRMATION")
        elif raid.confirmed_at_ms is not None:
            raise ValueError("C55_PREMATURE_OR_FORGED_1H_RAID_CONFIRMATION")
    if observed_break is not None:
        br=observed_break
        if (not isinstance(br,ThreeBreak) or
            raid.verdict!="WICK_FRACTAL_GEOMETRY" or
            br.pivot_kind!=p.kind or br.pivot_center_ms!=p.center_ms or
            br.raid_start_ms!=raid.first_breach_ms or
            br.raid_confirmed_ms!=raid.confirmed_at_ms or
            br.raid_level!=p.level or br.raid_extreme!=raid.extreme or
            br.side!=("SHORT" if p.kind=="BSL" else "LONG") or
            br.status!="RESEARCH_3M_STRICT_PIVOT_CLOSE_BREAK_NOT_AUTHOR_BOS" or
            br.swing.kind!=("LOW" if p.kind=="BSL" else "HIGH") or
            br.swing.center_ms<br.raid_start_ms or
            br.swing.known_ms<br.raid_start_ms+THREE or
            br.swing.known_ms>br.break_start_ms or
            br.break_start_ms<br.raid_confirmed_ms or
            br.break_known_ms!=br.break_start_ms+THREE or
            br.break_known_ms>as_of_ms or
            not isinstance(br.break_close,Decimal) or not br.break_close.is_finite() or
            (br.break_close>=br.swing.level if p.kind=="BSL"
             else br.break_close<=br.swing.level) or
            not br.source_original_3m_row_id.endswith(":"+str(br.break_start_ms)) or
            len(br.swing.native3m_ids)!=3):
            raise ValueError("C55_FUTURE_OR_FORGED_ADAPTED_BOS_EVENT")
    else:
        br=None
    return LiquidityLifecycle(symbol,as_of_ms,ROUTE,p.kind,
        p.center_ms,p.level,p.known_ms,p.source_rows,
        raid.first_breach_ms,raid.first_breach_close_ms,
        raid.confirmed_at_ms,raid.extreme,
        br.swing.known_ms if br else None,
        br.break_known_ms if br else None,
        br.source_original_3m_row_id if br else None,state)

def audit_original_1h_liquidity_and_3m_bos(line,*,as_of_ms):
    if not isinstance(line,C21Native3mResult):
        raise ValueError("C55_NOT_ORIGINAL_C21_CRYPTO_SOURCE")
    # C21B _source checks original fully closed UTC bar stream and raw ZIP IDs,
    # including 2026 Sep->Oct archive boundary, then takes requested prefix.
    rows=_source(line,as_of_ms)
    hours=_hours(rows)
    pivots,raids=observe_fractals_and_first_breach(hours)
    old=observe_native3m_raid_break(line,as_of_ms=as_of_ms)
    if (old.symbol!=line.symbol or old.as_of_ms!=as_of_ms or
        old.source_native3m_rows!=len(rows) or
        old.source_hourly_closed!=len(hours) or
        old.closed_fractal_levels!=len(pivots) or
        len(raids)!=len(pivots) or
        old.confirmed_first_wick_raids!=sum(x.confirmed_at_ms is not None for x in raids)
        or old.readiness!="NOT_TRADE_READY" or old.author_bos_approved or old.trades):
        raise ValueError("C55_BASE_1H_3M_ORIGINAL_SOURCE_DRIFT")
    used=set()
    events=[]
    for raid in raids:
        matching=[(i,z) for i,z in enumerate(old.potential_breaks)
                  if (z.pivot_kind,z.pivot_center_ms,z.raid_start_ms)==
                   (raid.fractal.kind,raid.fractal.center_ms,raid.first_breach_ms)]
        if len(matching)>1:
            raise ValueError("C55_DUPLICATE_BREAK_FOR_ONE_RAID")
        found=matching[0][1] if matching else None
        if matching:used.add(matching[0][0])
        events.append(classify_raid(raid,found,symbol=line.symbol,as_of_ms=as_of_ms))
    if len(used)!=len(old.potential_breaks):
        raise ValueError("C55_ORPHAN_OR_DUPLICATE_C21B_BREAK")
    if sum(x.source_state==STATES[5] for x in events)!=len(old.potential_breaks):
        raise ValueError("C55_ADAPTED_BOS_COUNTS_DRIFT")
    return C55LifecycleReview(line.symbol,as_of_ms,len(rows),len(hours),
        len(pivots),old.confirmed_first_wick_raids,
        len(old.potential_breaks),tuple(events))
