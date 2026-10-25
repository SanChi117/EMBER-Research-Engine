"""C55 crypto-only 1H BSL/SSL wick raid -> 3M closed BOS research bridge.

Reuses independently frozen original C37 source 3m scan (four adapted
pivot hypotheses), NOT 4H C46 IMB. Maintains independent course route
C_1H_RAID_3M_BOS versus 5M (separate exact native5M evidence needed).
1H pivot must be fully known 2h after center; wick raid only after pivot
known; raid confirmed after next 1H; 3m swing confirmed BEFORE BOS BAR
START; only then 3m closed breakout becomes knowable. NO TRADES.
"""
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
import re
from c37_native_adapted_bos_event_scanner import AdaptedClosedBreak
from c36_adapted_pivot_hypotheses import VARIANTS
from c45_recovered_course_text_contract import TEXT_ROUTE_MODES,recovered_text_claims
HOUR=3600000
THREE=180000
ORIGINAL_CRYPTO_SYMBOLS=("BCHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT")
COURSE_C_ROUTES=("C_1H_RAID_3M_BOS","C_1H_RAID_5M_BOS")
STATES=("ADAPTED_1H_WICK_RAID_TO_CLOSED_3M_BREAK_NOT_AUTHOR_BOS",
        "NATIVE5M_SOURCE_MUST_BE_EVALUATED_SEPARATELY_NOT_BORROWED_FROM_3M")
BLOCKERS=(
 "ACADEMIC_1H_LIQUIDITY_LEVEL_ORIGINAL_AUTHOR_NOT_VERIFIED",
 "ACADEMIC_RAID_WICK_AND_BOS_Swing_SEMANTICS_NOT_AUTHOR_VERIFIED",
 "ORIGINAL_AUTHOR_ENTRY_STOP_FTA_STRONG_HL_NOT_VERIFIED",
 "OOS_FEES_SLIPPAGE_FILLS_NOT_VALIDATED",
)
RAW3_ID=re.compile(r"[a-f0-9]{64}:[0-9]{13}$")

@dataclass(frozen=True)
class C55RouteCObservation:
    symbol:str
    route_c_mode:str
    source_status:str
    source_hypothesis:str
    raid_type:str
    candidate_1h_liquidity_fractal_center_ms:int
    candidate_1h_liquidity_fully_known_ms:int
    raid_first_1h_breach_start_ms:int
    raid_wick_fully_confirmed_ms:int
    source_original3m_break_bar_id:str|None
    source_original3m_break_bar_closed_ms:int|None
    data_source_timeframe:str|None
    academic_BOS_author_verified:bool=False
    author_course_entry_ready:bool=False
    blocker_reasons:tuple[str,...]=BLOCKERS
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _fx(d):
    try:x=Decimal(str(d))
    except (ValueError,InvalidOperation):raise ValueError("C55_INVALID_CRYPTO_SOURCE_LEVEL")
    if not x.is_finite() or x<=0:raise ValueError("C55_INVALID_CRYPTO_SOURCE_LEVEL")
    return x

def validate_adapted_original_3m_break(e):
    if not isinstance(e,AdaptedClosedBreak):
        raise ValueError("C55_UNTRUSTED_C37_EVENT")
    if (e.hypothesis_id not in VARIANTS or
        e.symbol not in ORIGINAL_CRYPTO_SYMBOLS or
        e.raid_fractal_kind not in ("BSL","SSL") or
        e.status!="ADAPTED_RESEARCH_CLOSED_BREAK_NOT_AUTHOR_BOS" or
        e.author_bos_approved or e.paper_trade_allowed or e.orders or e.trades):
        raise ValueError("C55_FORGED_CRYPTO_SOURCE_OR_AUTHOR_ENTRY")
    if e.side!=("SHORT" if e.raid_fractal_kind=="BSL" else "LONG"):
        raise ValueError("C55_RAID_DIRECTION_AND_ENTRY_SIDE_MISMATCH")
    for n in (e.raid_fractal_center_ms,e.raid_first_breach_ms,
              e.raid_confirmed_ms,e.swing_center_ms,e.swing_confirmed_ms,
              e.break_bar_start_ms,e.break_bar_closed_known_ms):
        if type(n) is not int or n<=0:
            raise ValueError("C55_INVALID_CLOSED_EVENT_TIMESTAMP")
    center=e.raid_fractal_center_ms
    breach=e.raid_first_breach_ms
    raid_known=e.raid_confirmed_ms
    start=e.break_bar_start_ms
    if (center%HOUR or breach%HOUR or raid_known%HOUR or
        breach<center+2*HOUR or raid_known!=breach+2*HOUR or
        e.swing_center_ms%THREE or e.swing_confirmed_ms!=e.swing_center_ms+2*THREE or
        e.swing_center_ms<breach or
        e.swing_confirmed_ms<breach+HOUR or
        e.swing_confirmed_ms>start or
        raid_known>start or start%THREE or
        e.break_bar_closed_known_ms!=start+THREE):
        raise ValueError("C55_LOOKAHEAD_PIVOT_RAID_OR_3M_BOS")
    for value,start_ms in ((e.break_original_native3m_row_id,start),
                           (e.swing_center_native3m_row_id,e.swing_center_ms)):
        if (not isinstance(value,str) or not RAW3_ID.fullmatch(value)
            or int(value.rsplit(":",1)[1])!=start_ms):
            raise ValueError("C55_BAD_ORIGINAL_CRYPTO_RAW3M_CANDLE_ID")
    level=_fx(e.raid_level)
    extreme=_fx(e.raid_extreme)
    swing=_fx(e.swing_level)
    close=_fx(e.break_close)
    if e.raid_fractal_kind=="BSL":
        if not(extreme>level and swing<level and close<swing):
            raise ValueError("C55_WICK_BOS_PRICE_GEOMETRY_INVALID")
    elif not(extreme<level and swing>level and close>swing):
        raise ValueError("C55_WICK_BOS_PRICE_GEOMETRY_INVALID")
    return True

def adapted_3m_and_explicit_unassessed_5m(e):
    validate_adapted_original_3m_break(e)
    if set(COURSE_C_ROUTES)-set(TEXT_ROUTE_MODES) or len(recovered_text_claims())!=18:
        raise ValueError("C55_COURSE_ROUTE_C_SOURCE_CONTRACT_DRIFT")
    baseline={
        "symbol":e.symbol,"source_hypothesis":e.hypothesis_id,
        "raid_type":e.raid_fractal_kind,
        "candidate_1h_liquidity_fractal_center_ms":e.raid_fractal_center_ms,
        "candidate_1h_liquidity_fully_known_ms":e.raid_fractal_center_ms+2*HOUR,
        "raid_first_1h_breach_start_ms":e.raid_first_breach_ms,
        "raid_wick_fully_confirmed_ms":e.raid_confirmed_ms,
    }
    one=C55RouteCObservation(route_c_mode=COURSE_C_ROUTES[0],
        source_status=STATES[0],
        source_original3m_break_bar_id=e.break_original_native3m_row_id,
        source_original3m_break_bar_closed_ms=e.break_bar_closed_known_ms,
        data_source_timeframe="3M",**baseline)
    other=C55RouteCObservation(route_c_mode=COURSE_C_ROUTES[1],
        source_status=STATES[1],
        source_original3m_break_bar_id=None,
        source_original3m_break_bar_closed_ms=None,
        data_source_timeframe=None,**baseline)
    return one,other
