"""C34 source-text negative-only BOS rule gate, not an author BOS detector.

Source: original Ukrainian '4. Entry By BOS.txt' (Drive id
1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO); other entry lessons are
NOT a substitute for the inaccessible author-labeled Notion 2023 backtest.

Flags below are explicit *scenario premises*, not data observations made
by this module. Never infer trades, author BOS pivot, 15-pip crypto stop,
IANA session timezone, intrabar ticks, FTA ranking or limit fills.
"""
from dataclasses import dataclass
from decimal import Decimal

SOURCE_BOS="https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view"
AUTHOR_BACKTEST_MISSING="https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21"

@dataclass(frozen=True)
class C34RulePremises:
    raid_side:str
    raid_interaction:str
    selected_bos_level:Decimal|None
    raid_liquidity_level:Decimal|None
    model_3m_bos_exists:bool|None
    proper_target_exists:bool|None
    first_trouble_undermines_rr:bool|None
    stop_is_beyond_swept_liquidity:bool|None
    reaction_confirmed:bool|None=None
    author_selected_bos_pivot_documented:bool=False
    author_goldens_positive_and_negative:bool=False
    asserted_session_timezone:str|None=None
    stop_size_pips:Decimal|None=None
    price_cross_tick_order_documented:bool=False
    exact_limit_retest_documented:bool=False

@dataclass(frozen=True)
class C34SourceRuleJudgment:
    mandatory_invalidation_codes:tuple[str,...]
    missing_academic_evidence:tuple[str,...]
    instructor_route_classification:str
    available_for_paper_signals:bool=False
    market_orders_allowed:bool=False
    limit_orders_allowed:bool=False
    trades_allowed:bool=False
    readiness:str="NOT_TRADE_READY"

def _check_bool_or_none(name,v):
    if v is not None and type(v) is not bool:
        raise ValueError("C34_UNTRUSTED_TRI_STATE_"+name)

def _check_positive_price(name,v):
    if v is not None and (type(v) is not Decimal or not v.is_finite() or v<=0):
        raise ValueError("C34_UNTRUSTED_DECIMAL_"+name)

def judge_textual_bos_rules(p):
    if not isinstance(p,C34RulePremises):
        raise ValueError("C34_UNTRUSTED_RULE_PREMISES")
    if p.raid_side not in ("BSL","SSL"):
        raise ValueError("C34_INVALID_RAID_DIRECTION")
    if p.raid_interaction not in ("WICK","BODY","NONE","UNKNOWN"):
        raise ValueError("C34_INVALID_RAID_INTERACTION")
    for field in ("model_3m_bos_exists","proper_target_exists",
                  "first_trouble_undermines_rr",
                  "stop_is_beyond_swept_liquidity","reaction_confirmed"):
        _check_bool_or_none(field,getattr(p,field))
    for field in ("author_selected_bos_pivot_documented",
                  "author_goldens_positive_and_negative",
                  "price_cross_tick_order_documented",
                  "exact_limit_retest_documented"):
        if type(getattr(p,field)) is not bool:
            raise ValueError("C34_UNTRUSTED_AUTHOR_OR_ROUTE_FLAG_"+field)
    for field in ("selected_bos_level","raid_liquidity_level","stop_size_pips"):
        _check_positive_price(field,getattr(p,field))
    if p.asserted_session_timezone is not None and (
        type(p.asserted_session_timezone) is not str or
        len(p.asserted_session_timezone)>128 or not p.asserted_session_timezone.strip()):
        raise ValueError("C34_INVALID_ASSERTED_TIMEZONE")

    # Even caller claiming to possess an author pivot cannot upgrade this
    # textual observer. Need an independently source-attested labeled case.
    invalid=[]
    if p.raid_interaction in ("NONE","BODY"):
        invalid.append("AUTHOR_REQUIRES_1H_FRACTAL_WICK_RAID")
    if p.model_3m_bos_exists is False:
        invalid.append("AUTHOR_3M_BOS_ABSENT")
    if p.proper_target_exists is False:
        invalid.append("AUTHOR_PROPER_TARGET_ABSENT")
    if p.first_trouble_undermines_rr is True:
        invalid.append("AUTHOR_FTA_BLOCKS_REWARD_RISK")
    if p.stop_is_beyond_swept_liquidity is False:
        invalid.append("AUTHOR_SL_NOT_BEYOND_SWEPT_LIQUIDITY")
    if p.selected_bos_level is not None and p.raid_liquidity_level is not None:
        if p.raid_side=="BSL" and p.selected_bos_level>=p.raid_liquidity_level:
            invalid.append("AUTHOR_BSL_RAID_REQUIRES_BOS_BELOW_LEVEL")
        if p.raid_side=="SSL" and p.selected_bos_level<=p.raid_liquidity_level:
            invalid.append("AUTHOR_SSL_RAID_REQUIRES_BOS_ABOVE_LEVEL")

    missing=[
       "AUTHOR_SELECTED_3M_BOS_PIVOT_POSITIVE_NEGATIVE_GOLDENS_MISSING",
       "ORIGINAL_2023_AUTHOR_BACKTEST_UNAVAILABLE",
       "AUTHOR_TRADE_CONTEXT_REACTION_AND_SOURCE_LABELS_UNVERIFIED",
       "AUTHOR_SESSION_IANA_TIMEZONE_DST_UNVERIFIED",
       "AUTHOR_FTA_RANKING_AND_STOP_BUFFER_UNVERIFIED"
    ]
    if p.raid_interaction=="UNKNOWN":
        missing.append("1H_WICK_RAID_SOURCE_NOT_SHOWN")
    if p.model_3m_bos_exists is None:
        missing.append("3M_BOS_SOURCE_NOT_SHOWN")
    if p.selected_bos_level is None or p.raid_liquidity_level is None:
        missing.append("AUTHOR_BOS_TO_RAID_LEVEL_COMPARISON_NOT_POSSIBLE")
    if p.proper_target_exists is None:
        missing.append("PROPER_TARGET_NOT_VERIFIED")
    if p.first_trouble_undermines_rr is None:
        missing.append("FIRST_TROUBLE_RR_NOT_VERIFIED")
    if p.stop_is_beyond_swept_liquidity is None:
        missing.append("STOP_BEYOND_RAID_NOT_VERIFIED")
    if p.reaction_confirmed is not True:
        missing.append("LOCAL_RAID_REACTION_SOURCE_NOT_VERIFIED")
    if not p.price_cross_tick_order_documented:
        missing.append("MARKET_PRICE_TICK_ORDER_NOT_VERIFIED")
    if not p.exact_limit_retest_documented:
        missing.append("LIMIT_RETEST_PRICE_EXPIRY_NOT_VERIFIED")
    # Instructor note says 15 pips on another instrument. Without an
    # instrument and definition of pip this number is NOT portable to crypto.
    if p.stop_size_pips is not None:
        missing.append("STOP_15_PIPS_UNIT_NOT_PORTABLE_TO_CRYPTO")

    return C34SourceRuleJudgment(
        tuple(invalid),tuple(missing),
        "SOURCE_TEXT_RULE_INVALIDATION_ONLY" if invalid else
        "ACADEMIC_BOS_AUTHOR_CHOICE_INDETERMINATE")
