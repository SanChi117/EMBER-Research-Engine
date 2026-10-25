"""C67 owner Route A: keep 1H trigger and new 1H VC POI branches separate.

Original lesson '2. Entry by IMB & SNR.txt':
 (A) 4H *valid author POI test* -> 1H BSL/SSL/allowed IMB trigger
     -> 15m VC IMB/SNR (not RB);
 (B) no 1H trigger -> 1H VC SNR/RB/IMB *new* POI ->
     first valid 1H POI test -> 15m trigger -> 5m VC or
     15m VC in absence of trigger.
 1H classic IMB wholly inside parent 4H IMB cannot be 1H trigger.
All geometry below is observational Binance source, NOT an author valid
POI test, VC, StrongHL, target, entry or approved Route A signal.
Never promote a native15m wick touch into author first VALID test.
Route B IDM and Route C raid->3m/5m BOS remain separate.
"""
from dataclasses import dataclass
from decimal import Decimal
from c46_original_4h_classic_imb_first_contact import PoiContactObservation
from c16_c08_monthly_daily_htf_lineage import TF_MS,DerivedClosedTF,NativeKline
from c62_academic_snr_rb_imb_liquidity_source_separation import (
    _validate,_preknown_unswept_levels_schedule)
from c63_closed_4h_source_contact_to_first_any_1h_reaction import (
    SourceReactionEvent,KINDS as E1KINDS)
from c66_native15m_route_a_source_event_chain import (
    _check15,Source15Event,KINDS as E15KINDS)
H=TF_MS["1h"]
Q=TF_MS["15m"]
WINDOW=24*H

TRIGGER=("1H_SSL_RAID_SOURCE","1H_BSL_RAID_SOURCE",
         "1H_IMB_ALLOWED_NONNESTED_SOURCE")
VC=("1H_NEW_VC_IMB_SOURCE","1H_NEW_VC_RB_SOURCE","1H_NEW_VC_SNR_SOURCE")
FORK_STATES=(
 "NO_4H_SOURCE_FIRST_TOUCH",
 "FIRST_ANY_1H_SOURCE_OPPOSITE_SIDE",
 "FIRST_ANY_1H_TRIGGER_AND_VC_AMBIGUOUS",
 "FIRST_ANY_1H_TWO_SIDES_AMBIGUOUS",
 "NO_1H_SOURCE_FORK_FULL_WINDOW",
 "NO_1H_SOURCE_FORK_RIGHT_CENSORED",
 "TRIGGER_FIRST_15M_IMB_SNR_SAME_SOURCE",
 "TRIGGER_FIRST_15M_IMB_SNR_OPPOSITE_SOURCE",
 "TRIGGER_FIRST_15M_BOTH_SIDES_AMBIGUOUS",
 "TRIGGER_FIRST_NO_15M_SOURCE_FULL_WINDOW",
 "TRIGGER_FIRST_NO_15M_SOURCE_RIGHT_CENSORED",
 "NEW_1H_VC_NO_SUBSEQUENT_POI_SOURCE_TEST",
 "NEW_1H_VC_FIRST_SOURCE_TEST_15M_TRIGGER_NEEDS_5M_VC",
 "NEW_1H_VC_FIRST_SOURCE_TEST_15M_VC_NO_TRIGGER",
 "NEW_1H_VC_FIRST_SOURCE_TEST_NO_15M_CANDIDATE",
 "NEW_1H_VC_FIRST_SOURCE_TEST_15M_OPPOSITE_SOURCE",
 "NEW_1H_VC_FIRST_SOURCE_TEST_15M_TWO_SIDES_AMBIGUOUS")
@dataclass(frozen=True)
class OneHourForkSource:
    category:str
    side:str
    kind:str
    pattern_start_ms:int
    fully_known_ms:int
    first_original15m_id:str
    source_reference:str|None
    zone_bottom:str|None=None
    zone_top:str|None=None
    nested_1h_imb_inside_4h:bool=False
    owner_trigger_approved:bool=False
    owner_new_vc_poi_approved:bool=False

@dataclass(frozen=True)
class RouteAForkSource:
    symbol:str
    original_4h_source_side:str
    original_4h_first_native3m_contact_id:str|None
    first_source_1h_category:str|None
    first_source_1h_kind:str|None
    first_source_1h_known_ms:int|None
    source_first_1h_event:OneHourForkSource|None
    source_first_1h_conflict_kinds:tuple[str,...]
    source_first_new_1h_poi_test_native15m_id:str|None
    source_first_new_1h_poi_test_closed_ms:int|None
    first_15m_after_gate_kind:str|None
    first_15m_after_gate_side:str|None
    first_15m_after_gate_known_ms:int|None
    state:str
    nested_1h_imb_4h_trigger_vetoed:int
    censored_at_ms:int|None
    author_4h_poi_first_valid_test:bool=False
    author_1h_trigger:bool=False
    author_new_1h_vc_poi:bool=False
    author_new_1h_poi_first_valid_test:bool=False
    author_15m_volume_confirmation:bool=False
    author_5m_volume_confirmation:bool=False
    author_stronghl:bool=False
    route_b_idm_used:bool=False
    route_c_raid_bos_used:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _zone_for_event(e,lookup):
    if e.kind=="CLASSIC_1H_IMB_SOURCE":
        a=lookup.get(e.first_pattern_bar_start_ms)
        c=lookup.get(e.fully_known_ms-H)
        if a is None or c is None:raise ValueError("C67_1H_IMB_SOURCE_NOT_IN_BARS")
        if e.side=="LONG" and a.high<c.low:return a.high,c.low
        if e.side=="SHORT" and c.high<a.low:return c.high,a.low
        raise ValueError("C67_FAKE_1H_IMB_GAP_GEOMETRY")
    if e.kind in ("RB_1H_SOURCE","SNR_1H_SOURCE"):
        # Technical *pair wick envelope* is deliberately conservative,
        # NOT owner-selected 1h RB/SNR POI zone.
        a=lookup.get(e.first_pattern_bar_start_ms)
        b=lookup.get(e.first_pattern_bar_start_ms+H)
        if a is None or b is None:raise ValueError("C67_MISSING_1H_SOURCE_PAIR")
        return min(a.low,b.low),max(a.high,b.high)
    return None,None

def observe_1h_route_a_source_events(observation,hours,oneh_source_events,*,as_of_ms):
    if (not isinstance(observation,PoiContactObservation) or
        observation.candidate.author_poi_certified or
        observation.academic_poi_test_certified or
        observation.academic_volume_confirmation_certified or
        observation.orders or observation.trades or
        observation.readiness!="NOT_TRADE_READY"):
        raise ValueError("C67_AUTHOR_POI_FORGERY_OR_WRONG_C46")
    bars=_validate(hours,as_of_ms)
    lookup={x.start_ms:x for x in bars}
    preknown=_preknown_unswept_levels_schedule(bars)
    c=observation.candidate
    lower=Decimal(c.bottom);upper=Decimal(c.top)
    if (c.side not in ("LONG","SHORT") or
        not lower.is_finite() or not upper.is_finite() or
        lower<=0 or lower>=upper or
        c.fully_known_ms>as_of_ms or not isinstance(oneh_source_events,tuple)):
        raise ValueError("C67_FAKE_OR_FUTURE_C46_POI")
    found=[]
    nested=0
    for i,x in enumerate(bars):
        if x.start_ms<c.fully_known_ms:continue
        for typ,level,known in preknown[i]:
            if known>x.start_ms:raise ValueError("C67_FUTURE_1H_LIQUIDITY")
            if c.side=="LONG" and typ=="SSL" and x.low<level and x.open>=level and x.close>=level:
                found.append(OneHourForkSource("TRIGGER",c.side,"1H_SSL_RAID_SOURCE",
                  x.start_ms,x.known_at_ms,x.source_native_15m_rows[0],
                  "PREKNOWN_UNSWEPT_1H_SSL_STRICT_FRACTAL_SOURCE"))
            if c.side=="SHORT" and typ=="BSL" and x.high>level and x.open<=level and x.close<=level:
                found.append(OneHourForkSource("TRIGGER",c.side,"1H_BSL_RAID_SOURCE",
                  x.start_ms,x.known_at_ms,x.source_native_15m_rows[0],
                  "PREKNOWN_UNSWEPT_1H_BSL_STRICT_FRACTAL_SOURCE"))
    for e in oneh_source_events:
        if (not isinstance(e,SourceReactionEvent) or e.kind not in E1KINDS
            or e.side not in ("LONG","SHORT") or
            e.is_author_vc or e.is_author_bos or e.is_author_stronghl
            or e.orders or e.trades or
            e.fully_known_ms>as_of_ms or
            e.first_pattern_bar_start_ms not in lookup or
            e.raw_first_original15m_id!=lookup[e.first_pattern_bar_start_ms].source_native_15m_rows[0]):
            raise ValueError("C67_INVALID_OR_FUTURE_1H_SOURCE_EVENT")
        if e.kind=="BOS_PREKNOWN_1H_FRACTAL_CLOSE_SOURCE":
            continue # not 1H BSL/SSL raid; not author VC
        lo,hi=_zone_for_event(e,lookup)
        if e.kind=="CLASSIC_1H_IMB_SOURCE":
            is_nested=lo>=lower and hi<=upper
            if (is_nested and e.side==c.side and
                e.first_pattern_bar_start_ms>=c.fully_known_ms):
                nested+=1
            else:
                found.append(OneHourForkSource("TRIGGER",e.side,
                    "1H_IMB_ALLOWED_NONNESTED_SOURCE",e.first_pattern_bar_start_ms,
                    e.fully_known_ms,e.raw_first_original15m_id,
                    "1H_CLASSIC_IMB_NOT_FULLY_WITHIN_4H_TECHNICAL_IMB",
                    str(lo),str(hi)))
        # Contextual 1H VC candidate is not an author-selected POI.
        kind={"CLASSIC_1H_IMB_SOURCE":"1H_NEW_VC_IMB_SOURCE",
              "SNR_1H_SOURCE":"1H_NEW_VC_SNR_SOURCE",
              "RB_1H_SOURCE":"1H_NEW_VC_RB_SOURCE"}[e.kind]
        found.append(OneHourForkSource("NEW_1H_VC_POI",e.side,kind,
            e.first_pattern_bar_start_ms,e.fully_known_ms,
            e.raw_first_original15m_id,
            "C62_1H_CONTEXTUAL_SOURCE_PATTERN_NOT_OWNER_VC",
            str(lo),str(hi),e.kind=="CLASSIC_1H_IMB_SOURCE" and is_nested))
    return tuple(sorted(found,key=lambda z:(z.fully_known_ms,z.category,z.kind,
                                           z.side,z.first_original15m_id))),nested

def route_a_fork_1h_to_15m(observation,hours,original15m,oneh_source_events,
                            source15m_events,*,as_of_ms):
    bars=_validate(hours,as_of_ms)
    n15=_check15(original15m,as_of_ms=as_of_ms)
    if (bars[0].symbol!=n15[0].symbol or
        bars[-1].known_at_ms!=n15[-1].known_at_ms or
        observation.candidate.fully_known_ms>as_of_ms or
        type(as_of_ms) is not int or as_of_ms%H or
        not isinstance(source15m_events,tuple)):
        raise ValueError("C67_DIFFERENT_OR_FUTURE_SOURCE")
    by15={x.start_ms:x for x in n15}
    for e in source15m_events:
        if (not isinstance(e,Source15Event) or e.kind not in E15KINDS or
            e.side not in ("LONG","SHORT") or
            e.author_volume_confirmation or e.author_entry or
            e.orders or e.trades or e.known_ms>as_of_ms or
            e.known_ms-e.pattern_start_ms!=3*Q or
            e.first_original15m_id!=(
               by15[e.pattern_start_ms].origin_raw_row_id
               if e.pattern_start_ms in by15 else None) or
            e.last_original15m_id!=(
               by15[e.known_ms-Q].origin_raw_row_id
               if e.known_ms-Q in by15 else None)):
            raise ValueError("C67_FORGED_15M_OWNER_VOLUME_OR_SOURCE")
    ev,nested=observe_1h_route_a_source_events(
        observation,hours,oneh_source_events,as_of_ms=as_of_ms)
    c=observation.candidate
    touch=observation.first_contact_closed_known_ms
    if (touch is not None and
        (touch<=c.fully_known_ms or touch>as_of_ms or
         not observation.first_contact_original3m_id)):
        raise ValueError("C67_INVALID_FIRST_ORIGINAL3M_CONTACT")
    def make(status,first=None,conflicts=(),testbar=None,
             first15=None,end=None):
        return RouteAForkSource(
            bars[0].symbol,c.side,observation.first_contact_original3m_id,
            first.category if first else None,first.kind if first else None,
            first.fully_known_ms if first else None,first,
            tuple(conflicts),testbar.origin_raw_row_id if testbar else None,
            testbar.known_at_ms if testbar else None,
            first15.kind if first15 else None,first15.side if first15 else None,
            first15.known_ms if first15 else None,status,nested,end)
    if touch is None:return make(FORK_STATES[0])
    window_end=min(as_of_ms,touch+WINDOW)
    # Event pattern must have STARTED strictly after closed parent source touch.
    eligible=tuple(x for x in ev if x.pattern_start_ms>=touch
                   and x.fully_known_ms<=window_end)
    if not eligible:
        return make(FORK_STATES[4] if as_of_ms>=touch+WINDOW
                    else FORK_STATES[5],end=window_end)
    at=min(x.fully_known_ms for x in eligible)
    simultaneous=tuple(x for x in eligible if x.fully_known_ms==at)
    categories={x.category for x in simultaneous}
    sides={x.side for x in simultaneous}
    names=tuple(sorted({x.kind for x in simultaneous}))
    chosen=simultaneous[0]
    if len(sides)>1:
        return make(FORK_STATES[3],chosen,names,end=window_end)
    if chosen.side!=c.side:
        return make(FORK_STATES[1],chosen,names,end=window_end)
    if len(categories)>1:
        return make(FORK_STATES[2],chosen,names,end=window_end)
    if chosen.category=="TRIGGER":
        # First ANY next 15m technical event only after fully known trigger;
        # 15m completion cannot borrow pre-trigger pattern candles.
        follow=tuple(x for x in source15m_events if
            x.pattern_start_ms>=at and x.known_ms<=min(as_of_ms,at+WINDOW))
        if not follow:
            return make(FORK_STATES[9] if as_of_ms>=at+WINDOW
                        else FORK_STATES[10],chosen,end=min(as_of_ms,at+WINDOW))
        t=min(x.known_ms for x in follow)
        earliest=tuple(x for x in follow if x.known_ms==t)
        directions={x.side for x in earliest}
        status=(FORK_STATES[8] if len(directions)>1 else
                FORK_STATES[6] if c.side in directions else FORK_STATES[7])
        return make(status,chosen,names,first15=earliest[0],end=min(as_of_ms,at+WINDOW))
    # NEW_1H_VC_POI: full source bar contact after owner candidate is known;
    # source wick-only TEST is NEVER upgraded to author first VALID POI test.
    if chosen.zone_bottom is None or chosen.zone_top is None:
        raise ValueError("C67_NO_SOURCE_1H_NEW_POI_BOUNDARY")
    lo=Decimal(chosen.zone_bottom);hi=Decimal(chosen.zone_top)
    touches=tuple(v for v in n15 if v.start_ms>=at and
                  v.low<=hi and v.high>=lo)
    if not touches:
        return make(FORK_STATES[11],chosen,names,end=as_of_ms)
    first_test=touches[0]
    gate=first_test.known_at_ms
    next15=tuple(x for x in source15m_events
        if x.pattern_start_ms>=gate and x.known_ms<=min(as_of_ms,gate+WINDOW))
    if not next15:
        return make(FORK_STATES[14],chosen,names,first_test,end=min(as_of_ms,gate+WINDOW))
    t=min(z.known_ms for z in next15)
    first=tuple(x for x in next15 if x.known_ms==t)
    # Preserve the actual earliest ANY, never pick preferred side/kind
    # after a new 1H POI source test. A 15m geometry is not author Trigger/VC.
    if len({z.side for z in first})>1:
        return make(FORK_STATES[16],chosen,names,first_test,first[0],min(as_of_ms,gate+WINDOW))
    if first[0].side!=c.side:
        return make(FORK_STATES[15],chosen,names,first_test,first[0],min(as_of_ms,gate+WINDOW))
    if len({z.kind for z in first})>1:
        return make(FORK_STATES[16],chosen,names,first_test,first[0],min(as_of_ms,gate+WINDOW))
    # Even a 15m classic source IMB is not an academic trigger without
    # correct POI support and parent first VALID test; 5m VC still absent.
    if first[0].kind=="15M_CLASSIC_IMB_SOURCE_ONLY":
        return make(FORK_STATES[12],chosen,names,first_test,first[0],min(as_of_ms,gate+WINDOW))
    return make(FORK_STATES[13],chosen,names,first_test,first[0],min(as_of_ms,gate+WINDOW))
