"""C68 technical crypto Strong High/Low *candidate* lifecycle, NOT academic StrongHL.

User's original Strong High & Low.txt says contact with liquidity OR
inefficiency must happen BEFORE motion confirmation forming [VC] POI or
BOS, on same or lower timeframe. Order Flow.txt additionally requires
both liquidity and IMB *for a real OF*. Neither a bare pivot nor volume
alone is author VC, and a gap alone does not certify real VC.

C67 technical Route A 1H fork → *source contact* (1H SSL/BSL raid, OR
subsequent 15m wick test of a proposed 1H POI) → earliest ANY actually
closed candidate 15m IMB/SNR or 1H strict fractal close-break BOS proxy.
Anchor min/max of ORIGINAL native15m from contact bar through BEFORE
confirmation event starts. Reject any pre-confirmation breach. No
lookahead or author upgrade. No SL/TP/orders/PNL or B/C route mixing.
"""
from dataclasses import dataclass
from decimal import Decimal
from c16_c08_monthly_daily_htf_lineage import NativeKline,TF_MS
from c66_native15m_route_a_source_event_chain import _check15,Source15Event,KINDS as K15
from c63_closed_4h_source_contact_to_first_any_1h_reaction import SourceReactionEvent
from c67_route_a_1h_trigger_vs_new_poi_source_fork import RouteAForkSource
Q=TF_MS["15m"]
H=TF_MS["1h"]
WINDOW=24*H
STATES=(
  "NO_C67_SINGLE_SOURCE_CONTACT",
  "1H_IMB_TRIGGER_CREATION_NOT_A_LIQUIDITY_OR_POI_TEST",
  "CONTACT_SOURCE_BAR_UNAVAILABLE",
  "NO_POST_CONTACT_SOURCE_CONFIRMATION_FULL_WINDOW",
  "NO_POST_CONTACT_SOURCE_CONFIRMATION_RIGHT_CENSORED",
  "FIRST_ANY_SOURCE_CONFIRMATION_BOTH_SIDES_AMBIGUOUS",
  "FIRST_ANY_SOURCE_CONFIRMATION_OPPOSITE_SIDE",
  "SOURCE_ANCHOR_BREACHED_BEFORE_CONFIRMATION_CLOSED",
  "SOURCE_EXTREME_WITH_POST_CONTACT_CONFIRMATION_NOT_AUTHOR"
)
@dataclass(frozen=True)
class TechnicalStrongHL:
    symbol:str
    original_source_side:str
    c67_route_a_source_state:str
    source_contact_kind:str|None
    source_contact_start_ms:int|None
    source_contact_original15m_id:str|None
    source_first_any_confirmation_kind:str|None
    source_first_any_confirmation_side:str|None
    source_first_any_confirmation_known_ms:int|None
    source_earliest_any_event_kinds:tuple[str,...]
    source_extreme_anchor_price:str|None
    source_extreme_first_original15m_id:str|None
    source_anchor_protected_only_after_ms:int|None
    source_status:str
    observation_end_ms:int|None
    source_fully_observed_window:bool
    author_verified_liquidity_or_inefficiency_contact:bool=False
    author_verified_vc_or_bos:bool=False
    author_verified_stronghl:bool=False
    author_verified_of:bool=False
    author_structural_stop:bool=False
    route_b_idm_evaluated:bool=False
    route_c_raid_bos_evaluated:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _anchor_extreme(bars,start,until,side):
    source=tuple(x for x in bars if start<=x.start_ms<until)
    if not source:return None,None
    v=(min(x.low for x in source) if side=="LONG"
       else max(x.high for x in source))
    first=next(x for x in source if
         (x.low==v if side=="LONG" else x.high==v))
    return v,first.origin_raw_row_id

def observe_source_stronghl_after_contact(fork,bars,events15,events1,
                                           *,as_of_ms):
    """Strict first-any timestamps, no cherry picked favorable side."""
    if (not isinstance(fork,RouteAForkSource) or
        fork.author_4h_poi_first_valid_test or fork.author_1h_trigger or
        fork.author_new_1h_vc_poi or fork.author_new_1h_poi_first_valid_test or
        fork.author_15m_volume_confirmation or fork.author_5m_volume_confirmation or
        fork.author_stronghl or fork.route_b_idm_used or fork.route_c_raid_bos_used or
        fork.orders or fork.fills or fork.trades or fork.readiness!="NOT_TRADE_READY"
        or fork.original_4h_source_side not in ("LONG","SHORT") or
        not isinstance(events15,tuple) or not isinstance(events1,tuple)):
        raise ValueError("C68_FORGED_OWNER_STRONGHL_OR_ROUTE")
    a=_check15(bars,as_of_ms=as_of_ms)
    if (a[0].symbol!=fork.symbol or as_of_ms%H or
        as_of_ms!=a[-1].known_at_ms):
        raise ValueError("C68_SOURCE_ASOF_OR_SYMBOL_MISMATCH")
    by={x.start_ms:x for x in a}
    for e in events15:
        if (not isinstance(e,Source15Event) or e.kind not in K15 or
            e.side not in ("LONG","SHORT") or
            e.author_volume_confirmation or e.author_entry or
            e.orders or e.trades or
            e.pattern_start_ms not in by or e.known_ms-Q not in by or
            by[e.pattern_start_ms].origin_raw_row_id!=e.first_original15m_id or
            by[e.known_ms-Q].origin_raw_row_id!=e.last_original15m_id or
            e.known_ms-e.pattern_start_ms!=3*Q or e.known_ms>as_of_ms):
            raise ValueError("C68_FORGED_OR_FUTURE_NATIVE15M_SOURCE_VC")
    for e in events1:
        if (not isinstance(e,SourceReactionEvent) or
            e.is_author_vc or e.is_author_bos or e.is_author_stronghl or
            e.orders or e.trades or e.fully_known_ms>as_of_ms or
            e.fully_known_ms-e.first_pattern_bar_start_ms!=(
              H if e.kind=="BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE"
              else 2*H if e.kind=="RB_1H_SOURCE" else 3*H) or
            e.first_pattern_bar_start_ms not in by or
            by[e.first_pattern_bar_start_ms].origin_raw_row_id!=e.raw_first_original15m_id):
            raise ValueError("C68_FORGED_OR_FUTURE_NATIVE1H_SOURCE_BOS")
    def out(state,contact_kind=None,contact=None,c_ev=None,all_kinds=(),
            v=None,first_id=None,protected=None,end=None,full=False):
        return TechnicalStrongHL(
            fork.symbol,fork.original_4h_source_side,fork.state,
            contact_kind,contact.start_ms if contact else None,
            contact.origin_raw_row_id if contact else None,
            c_ev[0] if c_ev else None,c_ev[1] if c_ev else None,
            c_ev[2] if c_ev else None,tuple(all_kinds),
            str(v) if v is not None else None,first_id,protected,
            state,end,full)
    first=fork.source_first_1h_event
    if first is None or fork.first_source_1h_category not in (
            "TRIGGER","NEW_1H_VC_POI") or
        fork.source_first_1h_conflict_kinds and len(
            fork.source_first_1h_conflict_kinds)>1 or
        fork.state in ("FIRST_ANY_1H_TRIGGER_AND_VC_AMBIGUOUS",
                       "FIRST_ANY_1H_TWO_SIDES_AMBIGUOUS",
                       "FIRST_ANY_1H_SOURCE_OPPOSITE_SIDE")):
        return out(STATES[0])
    if fork.first_source_1h_category=="TRIGGER":
        if first.kind not in ("1H_SSL_RAID_SOURCE","1H_BSL_RAID_SOURCE"):
            return out(STATES[1])
        if first.side!=fork.original_4h_source_side:
            return out(STATES[0])
        # C67 1H wick raid (original 1H derived) is only fully KNOWN
        # after it closes; identify the exact first native15m source candle
        # breaking that level? Not present in C67 event. Conservatively
        # use LAST 15m bar of the raid 1H, known at close; do NOT pretend
        # this was precise first wick raid or author liquidity contact.
        touchstart=first.fully_known_ms-Q
        kind="ADAPTED_1H_RAID_LAST_NATIVE15M_BAR"
        gate=first.fully_known_ms
    else:
        if (fork.source_first_new_1h_poi_test_closed_ms is None or
            fork.source_first_new_1h_poi_test_native15m_id is None):
            return out(STATES[0])
        gate=fork.source_first_new_1h_poi_test_closed_ms
        touchstart=gate-Q
        kind="ADAPTED_NEW_1H_POI_FIRST_NATIVE15M_WICK_TEST"
        if gate<=first.fully_known_ms:
            raise ValueError("C68_NEW_1H_POI_TEST_BEFORE_1H_FULLY_KNOWN")
    contact=by.get(touchstart)
    if contact is None:
        return out(STATES[2],kind)
    if (first.fully_known_ms>as_of_ms or contact.known_at_ms!=gate or
        first.side!=fork.original_4h_source_side):
        raise ValueError("C68_INVALID_OR_FUTURE_SOURCE_CONTACT")
    if (fork.first_source_1h_category=="NEW_1H_VC_POI" and
        contact.origin_raw_row_id!=fork.source_first_new_1h_poi_test_native15m_id):
        raise ValueError("C68_FORGED_NEW_1H_POI_NATIVE15M_TEST_SOURCE_ID")
    end=min(as_of_ms,gate+WINDOW)
    candidates=[]
    for ev in events15:
        if ev.pattern_start_ms>=gate and ev.known_ms<=end:
            candidates.append((ev.known_ms,ev.side,ev.kind,ev.pattern_start_ms))
    for ev in events1:
        if (ev.kind=="BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE" and
            ev.first_pattern_bar_start_ms>=gate and ev.fully_known_ms<=end):
            candidates.append((ev.fully_known_ms,ev.side,
                               "1H_SOURCE_BOS_PREKNOWN_FRACTAL_CLOSE",
                               ev.first_pattern_bar_start_ms))
    full=as_of_ms>=gate+WINDOW
    if not candidates:
        return out(STATES[3] if full else STATES[4],kind,contact,end=end,full=full)
    at=min(x[0] for x in candidates)
    first_any=tuple(sorted((x for x in candidates if x[0]==at),
                           key=lambda x:(x[1],x[2],x[3])))
    sides={x[1] for x in first_any}
    sel=first_any[0]
    source_kinds=tuple(sorted({x[2] for x in first_any}))
    summary=(sel[2], "BOTH" if len(sides)>1 else sel[1],at)
    # Do NOT use a later favorable VC instead of first opposite reaction.
    if len(sides)>1:
        return out(STATES[5],kind,contact,summary,source_kinds,end=end,full=full)
    if sel[1]!=fork.original_4h_source_side:
        return out(STATES[6],kind,contact,summary,source_kinds,end=end,full=full)
    earliest_start=min(x[3] for x in first_any)
    price,raw=_anchor_extreme(a,contact.start_ms,earliest_start,
                               fork.original_4h_source_side)
    if price is None:
        return out(STATES[2],kind,contact,summary,source_kinds,end=end,full=full)
    formation=tuple(x for x in a if earliest_start<=x.start_ms<at)
    violated=any(
       (x.low<price if fork.original_4h_source_side=="LONG"
        else x.high>price) for x in formation)
    return out(STATES[7] if violated else STATES[8],kind,contact,summary,
               source_kinds,price,raw,at if not violated else None,
               end,full)
