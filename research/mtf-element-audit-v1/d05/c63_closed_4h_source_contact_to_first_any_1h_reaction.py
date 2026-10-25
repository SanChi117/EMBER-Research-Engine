"""C63: 4H source-only IMB first native3m wick contact -> first ANY
subsequent closed 1H technical VC/BOS event, strict chronology.

Reject favorable-only retrospective selection, open candles, invented
StrongHL, route conversion, orders. Original Binance USD-M candle IDs are
required for event proof; synthetic unit tests have distinct synthetic IDs.
1H candidate types: C62 IMB classic, C62 source SNR/MB/RB and
new preknown strict 1H three-bar fractal close break BOS_PROXY.
NO author POI, VC, true BOS, StrongHL, stop or actual trade.
"""
from dataclasses import dataclass
from decimal import Decimal
import re
from c16_c08_monthly_daily_htf_lineage import TF_MS,SEPT_START,DerivedClosedTF
from c62_academic_snr_rb_imb_liquidity_source_separation import (
    _validate,_preknown_unswept_levels_schedule)
HOUR=TF_MS["1h"]
THREE=180000
MAX_WINDOW_MS=24*HOUR
RAW=re.compile(r"[0-9a-f]{64}:[0-9]{13}\Z")
KINDS=("CLASSIC_1H_IMB_SOURCE","SNR_1H_SOURCE","RB_1H_SOURCE",
       "BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE")
STATUS=("NO_4H_SOURCE_FIRST_CONTACT","FIRST_ANY_SAME_SIDE_SOURCE_ONLY",
        "FIRST_ANY_OPPOSITE_SIDE_SOURCE_ONLY","FIRST_ANY_BOTH_SIDES_AMBIGUOUS",
        "FULL_WINDOW_NO_SOURCE_EVENT","RIGHT_CENSORED_NO_SOURCE_EVENT")
@dataclass(frozen=True)
class SourceReactionEvent:
    kind:str
    side:str
    first_pattern_bar_start_ms:int
    fully_known_ms:int
    raw_first_original15m_id:str
    provenance:str
    is_author_vc:bool=False
    is_author_bos:bool=False
    is_author_stronghl:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class SourceReactionChain:
    symbol:str
    original_4h_side:str
    original_4h_fully_known_ms:int
    original_first3m_contact_id:str|None
    first3m_contact_closed_ms:int|None
    source_window_end_ms:int|None
    fully_observed_24h_window:bool
    status:str
    first_any_source_event_known_ms:int|None
    first_any_source_events:tuple[SourceReactionEvent,...]
    first_any_side:str|None
    had_source_contact_inefficiency_only:bool
    has_author_selected_poi:bool=False
    has_author_first_valid_poi_test:bool=False
    has_author_vc_or_bos:bool=False
    has_author_stronghl:bool=False
    author_trade_approved:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _valid_id(raw,start):
    return (isinstance(raw,str) and bool(RAW.fullmatch(raw)) and
            int(raw.split(":")[1])==start)

def bos_source_events_from_closed_original_1h(hours,*,as_of_ms):
    bars=_validate(hours,as_of_ms)
    schedule=_preknown_unswept_levels_schedule(bars)
    result=[]
    for i,x in enumerate(bars):
        if i<3:continue
        # A previously fully confirmed and unbreached 1H strict three-bar
        # fractal is a technical boundary, *never academic Strong High/Low*.
        pre=schedule[i]
        directions=set()
        for kind,price,known in pre:
            if known>x.start_ms:raise ValueError("C63_FUTURE_FRACTAL_LEVEL")
            if kind=="BSL" and x.close>price:directions.add("LONG")
            if kind=="SSL" and x.close<price:directions.add("SHORT")
        for side in sorted(directions):
            result.append(SourceReactionEvent(
                "BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE",side,
                x.start_ms,x.known_at_ms,x.source_native_15m_rows[0],
                "STRICT_PREKNOWN_ORIGINAL1H_FRACTAL_CLOSE_BREAK_NOT_AUTHOR_BOS"))
    return tuple(result)

def convert_c62_closed_source_events(c62_result,hours,*,as_of_ms):
    """Preserve ALL source events (including opposite) in first-any decision.
    Do not treat MB as volume confirmation. RB contextual only; SNR and
    IMB do NOT automatically constitute author VC or final Route A entry.
    """
    bars=_validate(hours,as_of_ms)
    if (not isinstance(c62_result,dict) or c62_result.get("symbol")!=bars[0].symbol or
        c62_result.get("as_of_ms")!=as_of_ms or
        c62_result.get("author_goldens")!=0 or
        c62_result.get("orders")!=0 or c62_result.get("trades")!=0 or
        c62_result.get("readiness")!="NOT_TRADE_READY"):
        raise ValueError("C63_UNTRUSTED_C62_SOURCE")
    gap_entries=c62_result.get("technical_original_1h_imb_gaps")
    blocks=c62_result.get("technical_1h_snr_rb_separate_cases")
    if not isinstance(gap_entries,tuple) or not isinstance(blocks,tuple):
        raise ValueError("C63_UNTRUSTED_SOURCE_EVENT_TYPES")
    by_start={x.start_ms:x for x in bars}
    events=[]
    for gap in gap_entries:
        if (gap.side not in ("LONG","SHORT") or
            gap.status!="TECHNICAL_ORIGINAL1H_CLASSIC_3CANDLE_WICK_GAP_NOT_AUTHOR_POI"
            or type(gap.known_ms) is not int or gap.known_ms>as_of_ms or
            gap.known_ms-3*HOUR not in by_start or
            tuple(gap.three_first_native15m_ids)!=tuple(
                by_start[gap.known_ms-3*HOUR+k*HOUR].source_native_15m_rows[0]
                for k in range(3))):
            raise ValueError("C63_FORGED_TECHNICAL_1H_CLASSIC_GAP")
        events.append(SourceReactionEvent(
          "CLASSIC_1H_IMB_SOURCE",gap.side,gap.known_ms-3*HOUR,
          gap.known_ms,gap.three_first_native15m_ids[0],
          "C62_THREE_FULLY_CLOSED_HOURS_CLASSIC_WICK_GAP_ONLY"))
    for x in blocks:
        if (x.type not in ("RB","SNR_OR_MB") or x.side not in ("LONG","SHORT") or
            x.author_classified_poi or x.author_volume_confirmation or
            x.author_stronghl or x.orders or x.trades):
            raise ValueError("C63_FORGED_C62_AUTHOR_POI")
        if x.source_class.startswith("MB_") or x.source_class.startswith("RB_TWO_"):
            continue  # do not turn invalid MB or bare pair into VC events
        if x.source_class.startswith("RB_WICK_ONLY_") and x.type=="RB":
            kind="RB_1H_SOURCE"
        elif x.source_class.startswith("SNR_ACCEPTED_") and x.type=="SNR_OR_MB":
            kind="SNR_1H_SOURCE"
        else:raise ValueError("C63_WRONG_C62_BLOCK_CLASS")
        t=x.pair_first_known_ms-HOUR
        if (type(t) is not int or t not in by_start or
            x.fully_known_ms not in (t+2*HOUR,t+3*HOUR) or
            x.fully_known_ms>as_of_ms or
            x.pair_first_native15m_id!=by_start[t].source_native_15m_rows[0] or
            x.pair_second_native15m_id!=by_start[t+HOUR].source_native_15m_rows[0] or
            (kind=="SNR_1H_SOURCE" and
              x.confirmation_first_native15m_id!=by_start[t+2*HOUR].source_native_15m_rows[0]) or
            (kind=="RB_1H_SOURCE" and x.confirmation_first_native15m_id is not None)):
            raise ValueError("C63_C62_SOURCE_1H_ID_OR_TIME_DRIFT")
        events.append(SourceReactionEvent(kind,x.side,t,x.fully_known_ms,
           x.pair_first_native15m_id,"C62_SOURCE_ONLY_PROXY_NO_AUTHOR_POI_OR_VC"))
    events.extend(bos_source_events_from_closed_original_1h(hours,as_of_ms=as_of_ms))
    return tuple(sorted(events,key=lambda x:(
        x.fully_known_ms,x.kind,x.side,x.raw_first_original15m_id)))

def source_first_any_after_contact(*,symbol,side,zone_known_ms,
     first_original3m_id,first_contact_known_ms,events,as_of_ms):
    if (symbol not in ("BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT") or
        side not in ("LONG","SHORT") or
        type(zone_known_ms) is not int or
        type(as_of_ms) is not int or as_of_ms%HOUR or
        zone_known_ms%TF_MS["4h"] or
        zone_known_ms<SEPT_START or zone_known_ms>as_of_ms or
        not isinstance(events,tuple)):
        raise ValueError("C63_UNTRUSTED_4H_SOURCE_CONTRACT")
    if first_original3m_id is None:
        if first_contact_known_ms is not None:
            raise ValueError("C63_FORGED_MISSING_FIRST_SOURCE_CONTACT")
        return SourceReactionChain(symbol,side,zone_known_ms,
           None,None,None,False,STATUS[0],None,(),None,False)
    if (type(first_contact_known_ms) is not int or
        not _valid_id(first_original3m_id,first_contact_known_ms-THREE) or
        first_contact_known_ms<=zone_known_ms or
        first_contact_known_ms>as_of_ms):
        raise ValueError("C63_INVALID_FIRST_ORIGINAL_3M_CONTACT")
    right_edge=first_contact_known_ms+MAX_WINDOW_MS
    fully_observed=(as_of_ms>=right_edge)
    consider=[]
    for e in events:
        if (not isinstance(e,SourceReactionEvent) or e.kind not in KINDS or
            e.side not in ("LONG","SHORT") or type(e.fully_known_ms) is not int or
            type(e.first_pattern_bar_start_ms) is not int or
            not _valid_id(e.raw_first_original15m_id,e.first_pattern_bar_start_ms) or
            e.fully_known_ms>as_of_ms or e.fully_known_ms%HOUR or
            e.first_pattern_bar_start_ms%HOUR or
            e.first_pattern_bar_start_ms>=e.fully_known_ms or
            e.is_author_vc or e.is_author_bos or e.is_author_stronghl or
            e.orders or e.trades):
            raise ValueError("C63_FORGED_OR_FUTURE_1H_EVENT")
        # Never inspect a pattern formed partly before original contact,
        # even if the last bar closes later.
        if e.first_pattern_bar_start_ms>=first_contact_known_ms and (
            e.fully_known_ms<=right_edge
        ):
            consider.append(e)
    first=min((z.fully_known_ms for z in consider),default=None)
    earliest=tuple(x for x in consider if x.fully_known_ms==first) if first is not None else ()
    if earliest:
        sides={z.side for z in earliest}
        cls=STATUS[3] if len(sides)>1 else STATUS[1] if side in sides else STATUS[2]
        direction="BOTH" if len(sides)>1 else next(iter(sides))
    else:
        cls=STATUS[4] if fully_observed else STATUS[5]
        direction=None
    return SourceReactionChain(symbol,side,zone_known_ms,
        first_original3m_id,first_contact_known_ms,right_edge,
        fully_observed,cls,first,earliest,direction,True)
