"""C56: distinct original Binance 5m Route C vs 3m known-close on SAME 1H raid.

C20B source: authenticated original native5m 15 signed Binance USD-M ZIP,
hourly native OHLC equal C08, first preknown BSL/SSL wick raid and closed
5m price-break. C37 latest original3m independent 45 ZIP source.
Only matched SAME 1H parent (kind, center, first breach, raid confirmation)
is comparable. Never borrow 3m source row IDs as 5m or vice versa.
ADAPTED technical research, never author BOS or fill/trade.
"""
from dataclasses import dataclass
from decimal import Decimal
import re
from c20b_five_minute_break_observer import CloseBreakWitness
from c37_native_adapted_bos_event_scanner import AdaptedClosedBreak
from c55_crypto_1h_liquidity_raid_3m_bos_route_c_guard import validate_adapted_original_3m_break
FIVE=300000
HOUR=3600000
REG=re.compile(r"[a-f0-9]{64}:[0-9]{13}$")
TYPES=("FIRST_3M_CLOSE_EARLIER","FIRST_5M_CLOSE_EARLIER","SAME_KNOWN_CLOSE_TIME")
MISSING=("NO_5M_RESEARCH_CLOSED_BREAK_FOR_PARENT","NO_3M_RESEARCH_CLOSED_BREAK_FOR_PARENT")
BARRIERS=(
  "TECHNICAL_1H_FRACTAL_RAID_NOT_AUTHOR_SELECTED",
  "ADAPTED_SWING_SELECTION_NOT_AUTHOR_BOS",
  "ORIGINAL_AUTHOR_ENTRY_SL_TP_STRONGHL_FTA_UNKNOWN",
  "MARKET_EXECUTION_SLIPPAGE_OOS_UNTESTED",
)

@dataclass(frozen=True)
class C56CrossTimeframeParent:
    symbol:str
    raid_type:str
    first_1h_pivot_center_ms:int
    first_1h_breach_ms:int
    raid_closed_known_ms:int
    original_3m_bos_raw_id:str|None
    original_3m_bos_known_ms:int|None
    original_5m_bos_raw_id:str|None
    original_5m_bos_known_ms:int|None
    source_status:str
    author_bos_approved:bool=False
    author_fill_approved:bool=False
    blockers:tuple[str,...]=BARRIERS
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _amount(v):
    d=Decimal(str(v))
    if not d.is_finite() or d<=0:
        raise ValueError("C56_BAD_PRICE")
    return d

def validate_original_crypto_5m_break(e):
    if not isinstance(e,CloseBreakWitness):
        raise ValueError("C56_UNTRUSTED_ORIGINAL5M_SOURCE")
    r=e.raid;p=e.raid_pivot;s=e.swing
    if (p!=r.fractal or p.kind not in ("BSL","SSL") or
        e.side!=("SHORT" if p.kind=="BSL" else "LONG") or
        e.status!="RESEARCH_ONLY_CLOSED_5M_STRUCTURE_BREAK_NOT_AUTHOR_BOS"):
        raise ValueError("C56_INVALID_PARENT_RAID_OR_AUTHOR_FRAUD")
    if (not isinstance(p.center_ms,int) or not isinstance(p.known_ms,int) or
        p.known_ms!=p.center_ms+2*HOUR or
        r.first_breach_ms is None or r.confirmed_at_ms is None or
        r.verdict!="WICK_FRACTAL_GEOMETRY" or
        r.first_breach_close_ms!=r.first_breach_ms+HOUR or
        r.confirmed_at_ms!=r.first_breach_ms+2*HOUR or
        p.known_ms>r.first_breach_ms or
        r.first_breach_ms%HOUR or
        s.origin_ms<r.first_breach_ms or
        s.known_ms!=s.origin_ms+2*FIVE or
        s.known_ms<r.first_breach_ms+HOUR or
        s.known_ms>e.start_ms or
        e.start_ms<r.confirmed_at_ms or
        e.start_ms%FIVE or e.known_ms!=e.start_ms+FIVE):
        raise ValueError("C56_FUTURE_1H_RAID_5M_SWING_OR_UNCLOSED_BOS")
    if (not isinstance(e.source_row_id,str) or not REG.fullmatch(e.source_row_id)
        or int(e.source_row_id.rsplit(":",1)[1])!=e.start_ms
        or len(s.source_ids)!=3
        or not all(isinstance(i,str) and REG.fullmatch(i) for i in s.source_ids)
        or int(s.source_ids[1].rsplit(":",1)[1])!=s.origin_ms):
        raise ValueError("C56_BAD_ORIGINAL_NATIVE5M_SOURCE_ROW_IDS")
    _amount(p.level);_amount(r.extreme);_amount(s.level);_amount(e.close)
    if p.kind=="BSL":
        if not(r.extreme>p.level>s.level>e.close):
            raise ValueError("C56_RAID_SWING_BREAK_LEVELS_INCONSISTENT")
    elif not(r.extreme<p.level<s.level<e.close):
        raise ValueError("C56_RAID_SWING_BREAK_LEVELS_INCONSISTENT")
    return True

def c37_parent_key(e):
    validate_adapted_original_3m_break(e)
    return e.raid_fractal_kind,e.raid_fractal_center_ms,e.raid_first_breach_ms,e.raid_confirmed_ms

def c20_parent_key(e):
    validate_original_crypto_5m_break(e)
    return e.raid_pivot.kind,e.raid_pivot.center_ms,e.raid.first_breach_ms,e.raid.confirmed_at_ms

def compare_original_3m_5m_same_hourly_raid(*,symbol,e3=None,e5=None):
    if symbol not in ("BCHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT"):
        raise ValueError("C56_UNSUPPORTED_CRYPTO_SOURCE_SYMBOL")
    if e3 is None and e5 is None:
        raise ValueError("C56_MISSING_BOTH_SOURCE_TIMEFRAMES")
    key3=c37_parent_key(e3) if e3 is not None else None
    key5=c20_parent_key(e5) if e5 is not None else None
    if e3 is not None and (e3.symbol!=symbol or e3.hypothesis_id!="LATEST_CONFIRMED_V1"):
        raise ValueError("C56_NONBASELINE_OR_FOREIGN_ORIGINAL3M_SOURCE")
    if key3 is not None and key5 is not None and key3!=key5:
        raise ValueError("C56_FALSE_PARENT_MATCH_DIFFERENT_1H_RAIDS")
    kind,center,breach,confirmed=key3 or key5
    if e3 is None:status=MISSING[1]
    elif e5 is None:status=MISSING[0]
    elif e3.break_bar_closed_known_ms<e5.known_ms:status=TYPES[0]
    elif e3.break_bar_closed_known_ms>e5.known_ms:status=TYPES[1]
    else:status=TYPES[2]
    return C56CrossTimeframeParent(symbol,kind,center,breach,confirmed,
        e3.break_original_native3m_row_id if e3 is not None else None,
        e3.break_bar_closed_known_ms if e3 is not None else None,
        e5.source_row_id if e5 is not None else None,
        e5.known_ms if e5 is not None else None,status)
