"""C71 after *exact* original3m C70 contact: fail-closed Route A source VC/BOS.

Owner '2. Entry by IMB & SNR.txt':
  tested 4H POI + 1H SSL/BSL trigger -> final 15m VC [IMB,SNR].
  No 1H trigger -> 1H VC new 1H POI -> tested 1H POI ->
  15m trigger then 5m VC, OR if no 15m trigger 15m VC [SNR,IMB].
  An actual 4H liquidity raid implies NO 1H trigger.
Owner 'Strong High & Low.txt': liquidity/inefficiency CONTACT followed
by true VC POI OR BOS same/lower TF. C70 original3m wick alone is not
true owner POI first VALID test. A native15m source gap or source 1H
fractal-close BOS does not certify author VC, BOS, StrongHL or entry.

This gate independently replays C70 on the original signed source
before taking the FIRST ANY fully closed 15m [IMB,SNR] source geometry
or 1H preknown fractal close-break BOS, with pattern START no earlier
than contact's *earliest technically eligible 1H/3m known time*.
Never pick a later aligned candidate over an earlier opposite one.
No 5m verification and NEVER trades, stops, FTA, PnL.
"""
from dataclasses import dataclass
from c16_c08_monthly_daily_htf_lineage import TF_MS
from c66_native15m_route_a_source_event_chain import _check15,Source15Event,KINDS as K15
from c63_closed_4h_source_contact_to_first_any_1h_reaction import SourceReactionEvent,KINDS as K1
from c62_academic_snr_rb_imb_liquidity_source_separation import _validate
from c67_route_a_1h_trigger_vs_new_poi_source_fork import RouteAForkSource
from c69_exact_native15m_first_liquidity_raid_vs_poi_test import C69SourceContact
from c70_exact_native3m_first_raid_or_poi_source_wick import (
    Original3mFirstSourceWick,original3m_first_wick_within_c69)
Q=TF_MS["15m"];H=TF_MS["1h"];WINDOW=24*H
SOURCE_BOS="1H_BOS_PREKNOWN_FRACTAL_CLOSE_NOT_OWNER"
STATES=(
 "NO_UNAMBIGUOUS_ORIGINAL3M_CONTACT",
 "NO_FIRST_ANY_SOURCE_POST_GATE_FULL_WINDOW",
 "NO_FIRST_ANY_SOURCE_POST_GATE_RIGHT_CENSORED",
 "FIRST_ANY_SOURCE_OPPOSITE_DIRECTION",
 "FIRST_ANY_SOURCE_TWO_DIRECTIONS_AMBIGUOUS",
 "FIRST_ANY_SOURCE_SAME_TIME_15M_AND_1H_BOS_AMBIGUOUS",
 "FIRST_ANY_SOURCE_SAME_TIME_MULTIPLE_15M_KINDS_AMBIGUOUS",
 "FIRST_ANY_1H_BOS_PROXY_NOT_AUTHOR_VC_OR_BOS",
 "FIRST_ANY_15M_IMB_ALIGNED_NOT_AUTHOR_VC",
 "FIRST_ANY_15M_SNR_ALIGNED_NOT_AUTHOR_VC",
 "FIRST_ANY_NEW1H_POI_15M_IMB_TRIGGER_VS_VC_UNRESOLVED",
 "FIRST_ANY_NEW1H_POI_15M_SNR_TRIGGER_VS_VC_UNRESOLVED"
)
@dataclass(frozen=True)
class PostContactSourceGate:
    symbol:str
    original_4h_source_side:str
    source_route_a_branch:str|None
    source_first3m_contact_id:str|None
    source_first3m_contact_closed_ms:int|None
    original_hour_confirmed_ms:int|None
    earliest_event_pattern_start_gate_ms:int|None
    first_any_confirmed_event_ms:int|None
    first_any_source_event_kinds:tuple[str,...]
    first_any_source_event_sides:tuple[str,...]
    state:str
    observation_end_ms:int|None
    fully_observed_window:bool
    source_first_3m_native15m_decimal_parity:bool
    author_4h_poi_valid_test:bool=False
    author_1h_poi_valid_test:bool=False
    author_1h_trigger:bool=False
    author_15m_trigger:bool=False
    author_15m_vc:bool=False
    author_5m_vc:bool=False
    author_1h_bos:bool=False
    author_stronghl:bool=False
    route_b_idm_approved:bool=False
    route_c_raid_bos_approved:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def classify_after_original3m_contact(fork,c69,c70,native15m,original3m,
                                      hours,events15,events1,*,as_of_ms):
    if (not isinstance(fork,RouteAForkSource)
        or not isinstance(c69,C69SourceContact)
        or not isinstance(c70,Original3mFirstSourceWick)
        or fork.symbol!=c69.symbol or fork.symbol!=c70.symbol
        or fork.original_4h_source_side not in ("LONG","SHORT")
        or c69.side!=fork.original_4h_source_side
        or c70.side!=fork.original_4h_source_side
        or fork.author_4h_poi_first_valid_test or fork.author_1h_trigger
        or fork.author_new_1h_vc_poi or fork.author_new_1h_poi_first_valid_test
        or fork.author_15m_volume_confirmation or fork.author_5m_volume_confirmation
        or fork.author_stronghl or fork.route_b_idm_used or fork.route_c_raid_bos_used
        or fork.orders or fork.fills or fork.trades
        or c69.author_first_valid_poi_test or c69.author_liquidity_raid_confirmed
        or c69.author_stronghl_confirmed or c69.author_sl_level
        or c69.orders or c69.fills or c69.trades
        or c70.author_first_valid_poi_test or c70.author_liquidity_raid
        or c70.author_stronghl or c70.author_volume_confirmation
        or c70.route_b_idm_used or c70.route_c_raid_bos_used
        or c70.orders or c70.fills or c70.trades
        or any(x.readiness!="NOT_TRADE_READY" for x in (fork,c69,c70))
        or not isinstance(events15,tuple) or not isinstance(events1,tuple)):
        raise ValueError("C71_UNTRUSTED_OR_AUTHOR_PROMOTED_PARENT")
    bars=_check15(native15m,as_of_ms=as_of_ms)
    hbars=_validate(hours,as_of_ms)
    if (as_of_ms%H or bars[0].symbol!=fork.symbol or
        hbars[0].symbol!=fork.symbol or bars[-1].known_at_ms!=as_of_ms
        or hbars[-1].known_at_ms!=as_of_ms):
        raise ValueError("C71_UNALIGNED_SOURCE_ASOF")
    # Recompute ALL original 3m provenance, 5:1 bar parity and first
    # native3m wick, not merely trust a claimed previous C70 receipt.
    expected=original3m_first_wick_within_c69(
        fork,c69,native15m,original3m,as_of_ms=as_of_ms)
    if c70!=expected:
        raise ValueError("C71_C70_FIRST_ORIGINAL3M_SOURCE_ID_OR_PRICE_DRIFT")
    b15={x.start_ms:x for x in bars}
    b1={x.start_ms:x for x in hbars}
    for e in events15:
        if (not isinstance(e,Source15Event) or e.kind not in K15 or
            e.side not in ("LONG","SHORT") or
            e.author_volume_confirmation or e.author_entry
            or e.orders or e.trades or
            e.known_ms-e.pattern_start_ms!=3*Q or
            e.pattern_start_ms not in b15 or e.known_ms-Q not in b15 or
            e.first_original15m_id!=b15[e.pattern_start_ms].origin_raw_row_id
            or e.last_original15m_id!=b15[e.known_ms-Q].origin_raw_row_id
            or e.known_ms>as_of_ms):
            raise ValueError("C71_FUTURE_FORGED_15M_SOURCE_OR_AUTHOR")
    for e in events1:
        if (not isinstance(e,SourceReactionEvent) or e.kind not in K1 or
            e.side not in ("LONG","SHORT") or
            e.is_author_vc or e.is_author_bos or e.is_author_stronghl
            or e.orders or e.trades or
            e.first_pattern_bar_start_ms not in b1 or
            e.raw_first_original15m_id!=b1[e.first_pattern_bar_start_ms].source_native_15m_rows[0]
            or e.fully_known_ms-e.first_pattern_bar_start_ms!=(
                H if e.kind=="BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE"
                else 2*H if e.kind=="RB_1H_SOURCE" else 3*H)
            or e.fully_known_ms>as_of_ms):
            raise ValueError("C71_FUTURE_FORGED_1H_SOURCE_OR_AUTHOR")
    # Actual *first* 3m contact is earlier than full 1h close on raids.
    # Gate ALL future pattern starts at the later close, never backdate.
    known=c70.earliest_source_claim_eligible_ms
    def result(state,at=None,kinds=(),sides=(),end=None,full=False):
        return PostContactSourceGate(
            fork.symbol,fork.original_4h_source_side,
            fork.first_source_1h_category,
            c70.actual_first_native3m_id,
            c70.actual_first_native3m_closed_ms,
            c69.source_event_fully_known_ms,known,at,
            tuple(kinds),tuple(sides),state,end,full,
            c70.five_original3m_to_native15m_ohlcv_equal)
    if (c70.actual_first_native3m_id is None or known is None or
        not c70.five_original3m_to_native15m_ohlcv_equal):
        return result(STATES[0])
    if (known< c70.actual_first_native3m_closed_ms or
        known<c69.source_event_fully_known_ms or known>as_of_ms or
        known%Q):
        raise ValueError("C71_SOURCE_CONTACT_NOT_CLOSED_BEFORE_GATE")
    if (fork.first_source_1h_category=="NEW_1H_VC_POI"
        and c70.source_status!="NEW1H_POI_FIRST_ORIGINAL3M_WICK_TEST_NOT_AUTHOR_VALID"):
        raise ValueError("C71_NEW_1H_POI_NOT_FROM_C70_WICK")
    if (fork.first_source_1h_category=="TRIGGER"
        and not c70.source_status.startswith("RAID_FIRST_")):
        raise ValueError("C71_UNSUPPORTED_SOURCE_1H_TRIGGER")
    horizon=known+WINDOW
    end=min(as_of_ms,horizon)
    candidates=[]
    for e in events15:
        if e.pattern_start_ms>=known and e.known_ms<=end:
            candidates.append((e.known_ms,e.side,e.kind,"15M"))
    for e in events1:
        if (e.kind=="BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE" and
            e.first_pattern_bar_start_ms>=known and
            e.fully_known_ms<=end):
            candidates.append((e.fully_known_ms,e.side,SOURCE_BOS,"1H"))
    full=as_of_ms>=horizon
    if not candidates:
        return result(STATES[1] if full else STATES[2],
                      end=end,full=full)
    first_time=min(z[0] for z in candidates)
    first=tuple(z for z in candidates if z[0]==first_time)
    kinds=tuple(sorted({z[2] for z in first}))
    sides=tuple(sorted({z[1] for z in first}))
    tf=tuple(sorted({z[3] for z in first}))
    if len(sides)>1:state=STATES[4]
    elif sides[0]!=fork.original_4h_source_side:state=STATES[3]
    elif len(tf)>1:state=STATES[5]
    elif len(kinds)>1:state=STATES[6]
    elif tf==("1H",):state=STATES[7]
    elif fork.first_source_1h_category=="NEW_1H_VC_POI":
        state=STATES[10] if kinds==("15M_CLASSIC_IMB_SOURCE_ONLY",) else STATES[11]
    else:
        state=STATES[8] if kinds==("15M_CLASSIC_IMB_SOURCE_ONLY",) else STATES[9]
    return result(state,first_time,kinds,sides,end,full)
