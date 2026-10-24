"""C50: challenge the retrospective 4H-touch -> later-1H IMB as timely course VC.

This is a SOURCE-ONLY causal/semantic audit, not a signal. It JOINs independently
frozen C47 and C49 source observations on the SAME 4H candidate and exact first
original3m ID. Original course Route A 4H POI -> 1H trigger -> 15m entry VC
is NOT equivalent to any later 1H classic IMB; alternatively a contextual
1H VC without 1H trigger still needs a verified typed 4H POI and first test.
Neither is certified by these source records. No orders/trades.
"""
from dataclasses import dataclass
from c21b_original_3m_raid_break_geometry import THREE,HOUR
from c45_recovered_course_text_contract import recovered_text_claims
from c47_post_4h_contact_1h_imb_source_link import C47SourceJoin,FourToOneSourceObservation
from c49_original3m_post_contact_directional_close import (
    C49SourceReview,C49ParentReactionSource,HORIZONS)
TWENTY_FOUR=24*HOUR
MODES=(
  "NO_ORIGINAL_4H_FIRST_3M_CONTACT",
  "CONTACT_NO_DIRECTIONAL_3M_CLOSE_WITHIN_12H",
  "DIRECTIONAL_CLOSE_NO_LATER_1H_IMB",
  "FIRST_1H_IMB_CLOSED_AFTER_24H_OBSERVATION_WINDOW",
  "FIRST_DIRECTIONAL_3M_CLOSE_BEFORE_1H_IMB_CLOSE",
  "FIRST_DIRECTIONAL_3M_CLOSE_AT_1H_IMB_CLOSE",
  "FIRST_1H_IMB_CLOSE_BEFORE_DIRECTIONAL_3M_CLOSE",
)
BLOCKERS=(
  "AUTHOR_TYPED_4H_POI_SOURCE_UNVERIFIED",
  "ACADEMIC_POI_FIRST_TEST_UNVERIFIED",
  "COURSE_1H_TRIGGER_VS_CONTEXTUAL_1H_VC_UNRESOLVED",
  "AUTHOR_1H_VOLUME_CONFIRMATION_UNVERIFIED",
  "COURSE_REQUIRED_15M_ENTRY_VC_AND_STRONG_HL_UNVERIFIED",
  "PARENT_4H_FTA_ORIGINAL_AUTHOR_GOLDEN_UNVERIFIED",
)
CITED_RULE_IDS=("POI-01","POI-02","POI-03","ROUTE-A-01","ROUTE-A-02",
                 "ROUTE-A-05","ROUTE-A-06","STRONG-01","STATUS-01")

@dataclass(frozen=True)
class C50Context:
    symbol:str
    parent_4h_original3m_ids:tuple[str,str,str]
    first_3m_contact_id:str|None
    first_3m_contact_close_ms:int|None
    first_12h_directional_original3m_id:str|None
    first_12h_directional_close_ms:int|None
    first_12h_direction:str|None
    first_later_1h_imb_first_original3m_id:str|None
    first_later_1h_imb_closed_known_ms:int|None
    mode:str
    within_24h_later_1h_source:bool
    course_source_blockers:tuple[str,...]=BLOCKERS
    course_author_poi_test_verified:bool=False
    course_author_1h_volume_confirmation_verified:bool=False
    source_trade_ready:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class C50Review:
    symbol:str
    as_of_ms:int
    original_4h_candidate_count:int
    original3m_first_contact_count:int
    classified_context_count:int
    source_contexts:tuple[C50Context,...]
    necessary_course_claim_ids:tuple[str,...]=CITED_RULE_IDS
    author_verified_poi_count:int=0
    author_verified_1h_vc_count:int=0
    author_verified_entry_count:int=0
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def classify_original_context(a,b,*,as_of_ms):
    if not isinstance(a,FourToOneSourceObservation) or not isinstance(b,C49ParentReactionSource):
        raise ValueError("C50_UNTRUSTED_C47_C49_SOURCE_JOIN")
    if (a.course_typed_poi_approved or a.course_first_valid_test_approved
        or a.course_volume_confirmation_approved or a.author_chart_golden_count
        or b.academic_valid_first_test or b.academic_valid_reaction
        or a.orders or a.trades or b.orders or b.trades
        or a.readiness!="NOT_TRADE_READY" or b.readiness!="NOT_TRADE_READY"):
        raise ValueError("C50_FORGED_ACADEMIC_CONTEXT_OR_TRADE")
    if (a.original4h_zone_side not in ("LONG","SHORT")
        or a.original4h_zone_side!=b.original_4h_zone_side
        or a.original4h_zone_known_ms!=b.original_4h_zone_fully_known_ms
        or a.original4h_zone_known_ms>as_of_ms
        or len(a.original4h_zone_first_raw3m_ids)!=3
        or any(not isinstance(i,str) or not i for i in a.original4h_zone_first_raw3m_ids)
        or len(b.window_observations)!=len(HORIZONS)):
        raise ValueError("C50_ORIGINAL_4H_SOURCE_OR_TIME_MISMATCH")
    touch=a.original4h_first_contact_closed_known_ms
    if (touch!=b.source_original3m_first_contact_closed_ms or
        a.original4h_first_contact_native3m_id!=b.source_original3m_first_contact_id):
        raise ValueError("C50_MISMATCHED_ORIGINAL_FIRST_3M_CONTACT")
    if touch is None:
        if a.first_post_contact_1h_imb_source is not None or a.post_contact_same_side_1h_candidate_count:
            raise ValueError("C50_FICTITIOUS_FOLLOWUP_WITHOUT_TOUCH")
    elif (type(touch) is not int or touch%THREE or
          touch<=a.original4h_zone_known_ms or touch>as_of_ms or
          not a.original4h_first_contact_native3m_id):
        raise ValueError("C50_INVALID_FIRST_CONTACT_TIMESTAMP")
    for q,(name,horizon) in zip(b.window_observations,HORIZONS):
        if (q.horizon_id!=name or q.horizon_ms!=horizon or
            q.as_of_ms!=as_of_ms or q.author_reaction_certified
            or q.author_volume_confirmation_certified or
            q.orders or q.trades or q.readiness!="NOT_TRADE_READY"):
            raise ValueError("C50_FORGED_OR_MISALIGNED_C49_SOURCE_HORIZON")
    reaction=b.window_observations[2]
    if reaction.status not in ("NO_PARENT_4H_FIRST_CONTACT_AS_OF",
                              "FIRST_LATER_FAVORABLE_3M_CLOSE",
                              "FIRST_LATER_ADVERSE_3M_CLOSE",
                              "NO_LATER_DIRECTIONAL_CLOSE_HORIZON_COMPLETE",
                              "NO_LATER_DIRECTIONAL_CLOSE_WINDOW_OPEN"):
        raise ValueError("C50_UNRECOGNIZED_PRICE_CLOSE_EVENT")
    t=reaction.first_later_event_close_known_ms
    if t is not None:
        if (touch is None or type(t) is not int or t<=touch or t>as_of_ms
            or t>touch+12*HOUR or not reaction.first_later_event_original3m_id
            or reaction.status not in ("FIRST_LATER_FAVORABLE_3M_CLOSE",
                                        "FIRST_LATER_ADVERSE_3M_CLOSE")
            or reaction.favorable_3m_close==reaction.adverse_3m_close):
            raise ValueError("C50_FUTURE_OR_FORGED_3M_DIRECTIONAL_CLOSE")
    elif (reaction.first_later_event_original3m_id is not None
          or reaction.first_later_event_close_price is not None
          or reaction.favorable_3m_close or reaction.adverse_3m_close):
        raise ValueError("C50_ORPHAN_PRICE_CLOSE_ID")
    src=a.first_post_contact_1h_imb_source
    known=None
    if src is not None:
        known=src.fully_known_ms
        if (touch is None or src.academic_vc_certified or src.orders or src.trades
            or a.post_contact_same_side_1h_candidate_count<1
            or src.side!=a.original4h_zone_side
            or src.first_hour_start_ms<touch
            or src.second_hour_start_ms!=src.first_hour_start_ms+HOUR
            or src.third_hour_start_ms!=src.second_hour_start_ms+HOUR
            or known!=src.third_hour_start_ms+HOUR
            or known>as_of_ms or
            len(src.first_raw_native3m_ids)!=3 or
            any(not isinstance(z,str) or not z for z in src.first_raw_native3m_ids)):
            raise ValueError("C50_FORGED_OR_FUTURE_ORIGINAL_1H_SOURCE")
    elif a.post_contact_same_side_1h_candidate_count:
        raise ValueError("C50_ORPHAN_LATER_1H_COUNT")
    if touch is None:
        if reaction.status!="NO_PARENT_4H_FIRST_CONTACT_AS_OF" or t is not None:
            raise ValueError("C50_NO_TOUCH_HAS_FUTURE_PRICE")
        mode=MODES[0]
    elif t is None:
        if reaction.status=="NO_PARENT_4H_FIRST_CONTACT_AS_OF":
            raise ValueError("C50_TOUCH_WITH_NO_TOUCH_STATUS")
        mode=MODES[1]
    elif known is None:
        mode=MODES[2]
    elif known>touch+TWENTY_FOUR:
        mode=MODES[3]
    elif t<known:
        mode=MODES[4]
    elif t==known:
        mode=MODES[5]
    else:
        mode=MODES[6]
    direction=(("FAVORABLE" if reaction.favorable_3m_close else "ADVERSE")
               if t is not None else None)
    return C50Context(a.symbol,a.original4h_zone_first_raw3m_ids,
        a.original4h_first_contact_native3m_id,touch,
        reaction.first_later_event_original3m_id,t,direction,
        src.first_raw_native3m_ids[0] if src else None,known,
        mode,known is not None and touch is not None and known<=touch+TWENTY_FOUR)

def review_course_1h_source_causality(source_47,source_49):
    if not isinstance(source_47,C47SourceJoin) or not isinstance(source_49,C49SourceReview):
        raise ValueError("C50_UNTRUSTED_SOURCE_REPORT_TYPES")
    if (source_47.symbol!=source_49.symbol or
        source_47.as_of_ms!=source_49.as_of_ms or
        source_47.original_native3m_closed!=source_49.original_native3m_closed or
        source_47.original_source4h_candidates!=source_49.original_4h_source_candidates or
        source_47.original_source4h_first_contacts!=source_49.native3m_first_contact_count or
        len(source_47.observations)!=source_47.original_source4h_candidates or
        len(source_49.observations)!=source_49.original_4h_source_candidates):
        raise ValueError("C50_C47_C49_PARENT_SOURCE_PROVENANCE_DRIFT")
    if (source_47.author_vc_goldens or source_47.author_poi_goldens
        or source_49.course_reaction_goldens or source_49.course_volume_confirmation_goldens
        or source_47.orders or source_47.trades or source_49.orders or source_49.trades
        or source_47.readiness!="NOT_TRADE_READY"
        or source_49.readiness!="NOT_TRADE_READY"):
        raise ValueError("C50_FORGED_COURSE_AUTHOR_APPROVAL")
    claims=recovered_text_claims()
    if not set(CITED_RULE_IDS).issubset(claims):
        raise ValueError("C50_MISSING_ORIGINAL_COURSE_TEXT_REQUIREMENTS")
    events=tuple(classify_original_context(a,b,as_of_ms=source_47.as_of_ms)
                 for a,b in zip(source_47.observations,source_49.observations))
    if sum(x.first_3m_contact_id is not None for x in events)!=source_47.original_source4h_first_contacts:
        raise ValueError("C50_CONTACT_COUNT_DRIFT")
    return C50Review(source_47.symbol,source_47.as_of_ms,
        len(events),source_47.original_source4h_first_contacts,len(events),events)
