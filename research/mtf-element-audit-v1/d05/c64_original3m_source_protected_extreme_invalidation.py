"""C64: original Binance native3m contact -> first-any CLOSED technical reaction
-> frozen source-only extreme -> first wick and first CLOSED body invalidation.

Owner Strong High & Low.txt: contact liquidity/inefficiency AND subsequent
VC POI or BOS. Owner Order Flow.txt: invalidation can be close beyond last
OF structural link BOS, or opposite POI after reaching a target. Therefore
wick breach is NOT academic OF invalidation and a min/max over an arbitrary
source contact interval is NOT author StrongHL. The latter is recorded only
as a source candidate anchor with explicit independent status.

Never infer entry, SL/TP, win, OF reversal, StrongHL, author POI or fills.
"""
from dataclasses import dataclass
from decimal import Decimal
import re
from c21_native3m_source_bridge import Original3mRow,THREE
from c16_c08_monthly_daily_htf_lineage import TF_MS,SEPT_START,SYMBOLS
from c63_closed_4h_source_contact_to_first_any_1h_reaction import SourceReactionChain

HOUR=TF_MS["1h"]
OBSERVE=24*HOUR
RAW=re.compile(r"[a-f0-9]{64}:[0-9]{13}\Z")
STATUS=(
  "NO_ORIGINAL_4H_FIRST_CONTACT",
  "FIRST_ANY_AMBIGUOUS_NO_PROTECTED_DIRECTION",
  "NO_1H_REACTION_NO_PROTECTED_CANDIDATE",
  "REACTION_START_NOT_AFTER_CONTACT",
  "SOURCE_ANCHOR_BREACHED_BEFORE_EVENT_CONFIRMATION",
  "SOURCE_ANCHOR_KNOWN_AT_REACTION_CLOSE"
)
@dataclass(frozen=True)
class SourceProtectedExtremeAudit:
    symbol:str
    original_4h_parent_side:str
    event_side:str|None
    first_contact_native3m_id:str|None
    source_event_known_ms:int|None
    source_candidate_direction_extreme:str|None
    original_native3m_extreme_witness_id:str|None
    source_extreme_frozen_at_ms:int|None
    source_preactivation_breach_first3m_id:str|None
    source_status:str
    first_postevent_wick_breach_id:str|None
    first_postevent_3m_close_beyond_id:str|None
    first_postevent_1h_close_beyond_id:str|None
    observed_postevent_window_end_ms:int|None
    full_24h_postevent_source_observed:bool
    wick_breach_not_OF_invalidation:bool=True
    source_strict_fractal_not_StrongHL:bool=True
    author_labeled_stronghl:bool=False
    author_labeled_OF_invalidation:bool=False
    author_labeled_stop_loss:bool=False
    author_selected_poi:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _none(chain,status):
    return SourceProtectedExtremeAudit(
       chain.symbol,chain.original_4h_side,chain.first_any_side,
       chain.original_first3m_contact_id,chain.first_any_source_event_known_ms,
       None,None,None,None,status,None,None,None,None,False)

def _source(rows,symbol,asof):
    if (not isinstance(rows,tuple) or not rows or symbol not in SYMBOLS or
        type(asof) is not int or asof%THREE or asof<SEPT_START):
        raise ValueError("C64_UNTRUSTED_ORIGINAL3M_PREFIX")
    last=None
    for x in rows:
        if (not isinstance(x,Original3mRow) or x.symbol!=symbol
            or type(x.start_ms) is not int or x.start_ms%THREE
            or x.known_ms!=x.start_ms+THREE
            or (last is not None and x.start_ms!=last)
            or not isinstance(x.zip_sha,str) or
            not re.fullmatch(r"[a-f0-9]{64}",x.zip_sha)
            or x.raw_id!=x.zip_sha+":"+str(x.start_ms)
            or not all(isinstance(v,Decimal) and v.is_finite()
                for v in (x.open,x.high,x.low,x.close,x.volume))
            or not (0<x.low<=min(x.open,x.close)<=max(x.open,x.close)<=x.high
                    and x.volume>=0)):
            raise ValueError("C64_FORGED_OR_UNCLOSED_NATIVE3M")
        last=x.known_ms
    if rows[-1].known_ms!=asof:
        raise ValueError("C64_PHYSICAL_SOURCE_PREFIX_MUST_END_AT_ASOF")
    return rows

def _bad(side,bar,price,kind):
    value=(bar.low if kind=="wick" else bar.close) if side=="LONG" else (
           bar.high if kind=="wick" else bar.close)
    return value<price if side=="LONG" else value>price

def inspect_original_source_protected_extreme(chain,original3m,hourly,*,as_of_ms):
    """Actual source lifetime proof, no retrospective anchor repositioning.

    rows must be a physically supplied contiguous ORIGINAL 3m suffix
    ending at 'as_of_ms', beginning at original first contact bar (or for
    no-contact at arbitrary valid source prefix). Hourly is the authentic
    derived CLOSED original 1h prefix as of as_of_ms.
    """
    if (not isinstance(chain,SourceReactionChain) or
        chain.symbol not in SYMBOLS or chain.original_4h_side not in ("LONG","SHORT")
        or chain.has_author_stronghl or chain.has_author_vc_or_bos or
        chain.has_author_first_valid_poi_test or chain.has_author_selected_poi or
        chain.author_trade_approved or chain.orders or chain.trades or
        chain.readiness!="NOT_TRADE_READY"):
        raise ValueError("C64_FORGED_SOURCE_CHAIN_OR_AUTHOR_PROMOTION")
    rows=_source(original3m,chain.symbol,as_of_ms)
    from c16_c08_monthly_daily_htf_lineage import DerivedClosedTF
    if (not isinstance(hourly,tuple) or not hourly or
        type(as_of_ms) is not int or as_of_ms%HOUR):
        raise ValueError("C64_UNTRUSTED_ORIGINAL_1H_PREFIX")
    for i,z in enumerate(hourly):
        if (not isinstance(z,DerivedClosedTF) or z.symbol!=chain.symbol
            or z.tf!="1h" or z.known_at_ms!=z.start_ms+HOUR
            or z.known_at_ms>as_of_ms or len(z.source_native_15m_rows)!=4
            or (i and z.start_ms!=hourly[i-1].known_at_ms)
            or not all(isinstance(v,Decimal) and v.is_finite()
              for v in (z.open,z.high,z.low,z.close,z.volume))
            or not(0<z.low<=min(z.open,z.close)<=max(z.open,z.close)<=z.high)):
            raise ValueError("C64_FAKE_OR_FUTURE_1H_PREFIX")
    if hourly[-1].known_at_ms!=as_of_ms:
        raise ValueError("C64_ORIGINAL_1H_MUST_END_AT_ASOF")
    if chain.original_first3m_contact_id is None:
        if chain.status!="NO_4H_SOURCE_FIRST_CONTACT" or chain.first_any_source_events:
            raise ValueError("C64_FORGED_MISSING_SOURCE_CONTACT")
        return _none(chain,STATUS[0])
    if (chain.first3m_contact_closed_ms is None or
        chain.first3m_contact_closed_ms<=chain.original_4h_fully_known_ms or
        not RAW.fullmatch(chain.original_first3m_contact_id) or
        int(chain.original_first3m_contact_id.split(":")[1])!=
           chain.first3m_contact_closed_ms-THREE or
        rows[0].raw_id!=chain.original_first3m_contact_id or
        rows[0].known_ms!=chain.first3m_contact_closed_ms or
        chain.first3m_contact_closed_ms>as_of_ms):
        raise ValueError("C64_FIRST_SOURCE_CONTACT_ID_OR_TIME_MISMATCH")
    if chain.status=="FIRST_ANY_BOTH_SIDES_AMBIGUOUS":
        if (chain.first_any_side!="BOTH" or
            len({x.side for x in chain.first_any_source_events})!=2):
            raise ValueError("C64_INVALID_SAME_TIME_AMBIGUITY")
        return _none(chain,STATUS[1])
    if chain.status in ("FULL_WINDOW_NO_SOURCE_EVENT",
                        "RIGHT_CENSORED_NO_SOURCE_EVENT"):
        if chain.first_any_source_events or chain.first_any_source_event_known_ms is not None:
            raise ValueError("C64_FAKE_ABSENT_REACTION_EVENT")
        return _none(chain,STATUS[2])
    if chain.status not in ("FIRST_ANY_SAME_SIDE_SOURCE_ONLY",
                            "FIRST_ANY_OPPOSITE_SIDE_SOURCE_ONLY"):
        raise ValueError("C64_UNSUPPORTED_FIRST_ANY_STATUS")
    events=chain.first_any_source_events
    if (not events or chain.first_any_side not in ("LONG","SHORT")
        or chain.first_any_source_event_known_ms is None
        or chain.first_any_source_event_known_ms>as_of_ms or
        any(x.fully_known_ms!=chain.first_any_source_event_known_ms
            or x.side!=chain.first_any_side
            or x.is_author_stronghl or x.is_author_vc or x.is_author_bos
            or x.orders or x.trades for x in events)):
        raise ValueError("C64_INVALID_1H_SOURCE_EVENT_OR_FUTURE")
    known_hourly={h.start_ms:h for h in hourly}
    for event in events:
        parent=known_hourly.get(event.first_pattern_bar_start_ms)
        if (parent is None or
            event.raw_first_original15m_id!=parent.source_native_15m_rows[0]):
            raise ValueError("C64_SOURCE_EVENT_NOT_AN_ORIGINAL_1H_ID")
    first_pattern=min(x.first_pattern_bar_start_ms for x in events)
    if first_pattern<chain.first3m_contact_closed_ms:
        return _none(chain,STATUS[3])
    anchor_bars=tuple(x for x in rows if (
        x.start_ms>=rows[0].start_ms and x.known_ms<=first_pattern))
    if not anchor_bars:
        raise ValueError("C64_NO_CLOSED_SOURCE_PRE_EVENT_ANCHOR")
    side=chain.first_any_side
    price=(min(x.low for x in anchor_bars) if side=="LONG" else
           max(x.high for x in anchor_bars))
    witness=next(x for x in anchor_bars
                 if (x.low==price if side=="LONG" else x.high==price))
    confirm_at=chain.first_any_source_event_known_ms
    # The source candidate freezes only once event closes, never retroactively
    # backdated to the extreme raw bar. Any intervening breach is flagged.
    forming=tuple(x for x in rows if first_pattern<=x.start_ms
                  and x.known_ms<=confirm_at)
    bad_pre=next((x.raw_id for x in forming
                  if _bad(side,x,price,"wick")),None)
    if bad_pre is not None:
        return SourceProtectedExtremeAudit(
          chain.symbol,chain.original_4h_side,side,
          chain.original_first3m_contact_id,confirm_at,str(price),
          witness.raw_id,confirm_at,bad_pre,STATUS[4],
          None,None,None,None,False)
    end=min(as_of_ms,confirm_at+OBSERVE)
    after=tuple(x for x in rows
                if x.start_ms>=confirm_at and x.known_ms<=end)
    first_wick=next((x.raw_id for x in after
                      if _bad(side,x,price,"wick")),None)
    first_close3=next((x.raw_id for x in after
                       if _bad(side,x,price,"close")),None)
    hour_closes=tuple(h for h in hourly
         if h.start_ms>=confirm_at and h.known_at_ms<=end)
    first_close1=next((h.source_native_15m_rows[0] for h in hour_closes
                       if _bad(side,h,price,"close")),None)
    return SourceProtectedExtremeAudit(
        chain.symbol,chain.original_4h_side,side,
        chain.original_first3m_contact_id,confirm_at,str(price),
        witness.raw_id,confirm_at,None,STATUS[5],
        first_wick,first_close3,first_close1,end,
        as_of_ms>=confirm_at+OBSERVE)
