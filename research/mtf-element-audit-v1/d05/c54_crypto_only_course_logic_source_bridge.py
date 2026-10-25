"""C54 owner scope correction: course images TEACH LOGIC, BINANCE USD-M CRYPTO is target.

Preserve frozen C45 route academic TEXT mechanics separately from C46/47
research-only 4H/1H classic IMB. Never require EURUSD/OANDA/SAXO original
image candles and never treat 2024/25 FX chart publication as trade event.

All market evidence must be original closed crypto 3m/15m/1h/4h with causal
provenance, never borrowed from teacher screenshot; no trading enabled.
"""
from dataclasses import dataclass
import re
from c45_recovered_course_text_contract import (
    TEXT_ROUTE_MODES,recovered_text_claims,CourseContextCase,
    evaluate_text_contract)
THREE=3*60*1000
HOUR=60*60*1000
TF_MS={"3M":THREE,"5M":5*60*1000,"15M":15*60*1000,
       "1H":HOUR,"4H":4*HOUR}
TARGET="CRYPTO_BINANCE_USDM_ORIGINAL_CLOSED_OHLC_ONLY"
ILLUSTRATION_ROLE="COURSE_STRUCTURE_LOGIC_EXAMPLE_NOT_MARKET_PRICE_OR_EXECUTABLE_TRADE"
COURSE_ROLE_INDEPENDENT=(
    "A_IMB_SNR", "B_IDM", "C_RAID_TO_BOS")
SOURCE_MISSING=(
    "ACADEMIC_POI_TYPED_CLASSIFICATION_NOT_VERIFIED",
    "ACADEMIC_FIRST_VALID_POI_TEST_NOT_VERIFIED",
    "ACADEMIC_TRIGGER_OR_VOLUME_CONFIRMATION_ROUTE_NOT_VERIFIED",
    "STRUCTURAL_STRONG_HL_PARENT_FTA_SL_TP_NOT_VERIFIED",
    "COURSE_FIDELITY_PAPER_OOS_EXECUTION_FEES_NOT_VERIFIED")
ROUTE_MAP={
    "A_4H_TRIGGER_15M_VC":"A_IMB_SNR",
    "A_4H_NO_TRIGGER_1H_VC":"A_IMB_SNR",
    "A_1H_TRIGGER_5M_VC":"A_IMB_SNR",
    "A_1H_NO_TRIGGER_15M_VC":"A_IMB_SNR",
    "B_4H_VC_1H_IDM":"B_IDM",
    "B_1H_VC_15M_IDM":"B_IDM",
    "C_1H_RAID_3M_BOS":"C_RAID_TO_BOS",
    "C_1H_RAID_5M_BOS":"C_RAID_TO_BOS",
}
TECHNICAL_TAG="ADAPTED_NATIVE_CRYPTO_IMB_SOURCE_NOT_COURSE_POI_OR_VC"

@dataclass(frozen=True)
class CryptoTechnicalParent:
    symbol:str
    source_as_of_ms:int
    side:str
    original_4h_source3m_ids:tuple[str,str,str]
    original_4h_known_ms:int
    first_original3m_touch_id:str|None
    first_original3m_touch_known_ms:int|None
    first_later_1h_technical_imb_source3m_id:str|None
    first_later_1h_technical_imb_known_ms:int|None
    author_poi_verified:bool=False
    academic_first_test_verified:bool=False
    academic_volume_confirmation_verified:bool=False
    source_tag:str=TECHNICAL_TAG
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class CryptoCourseOverlay:
    symbol:str
    target_market:str
    source_as_of_ms:int
    original_4h_raw3m_ids:tuple[str,str,str]
    course_mode:str
    route_family:str
    academic_timeframe_sequence:tuple
    course_illustration_role:str
    market_source_lineage:str
    known_parent_before_first_touch:bool
    observed_first_native3m_touch:bool
    observed_later_fully_closed_1h_technical_imb:bool
    later_1h_source_is_not_automatic_vc:bool
    academic_PoI_VC_entry_confirmed:bool
    academic_semantic_requirements_missing:tuple[str,...]=SOURCE_MISSING
    final_state:str="COURSE_LOGIC_ONLY_NOT_TRADE_READY"
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _validate_id(ident,*,required):
    if ident is None:
        if required:raise ValueError("C54_MISSING_RAW_NATIVE_CRYPTO_CANDLE_ID")
        return None
    if not isinstance(ident,str) or not re.fullmatch(r"[a-f0-9]{64}:[0-9]{13}",ident):
        raise ValueError("C54_FORGED_NONCRYPTO_NATIVE_SOURCE_ID")
    return ident

def _raw_start(id):
    return int(id.rsplit(":",1)[1])

def validate_original_crypto_parent(x):
    if not isinstance(x,CryptoTechnicalParent):
        raise ValueError("C54_UNTRUSTED_CRYPTO_TECHNICAL_SOURCE")
    if (not isinstance(x.symbol,str) or
        not re.fullmatch(r"(BTC|ETH|SOL|XRP|BCH)USDT",x.symbol) or
        type(x.source_as_of_ms) is not int or
        type(x.original_4h_known_ms) is not int or
        x.side not in ("LONG","SHORT") or
        x.source_tag!=TECHNICAL_TAG or
        x.author_poi_verified or x.academic_first_test_verified or
        x.academic_volume_confirmation_verified or x.orders or x.trades or
        x.readiness!="NOT_TRADE_READY"):
        raise ValueError("C54_FORGED_MARKET_SCOPE_OR_ACADEMIC_POI_VC")
    if len(x.original_4h_source3m_ids)!=3:
        raise ValueError("C54_THREE_ORIGINAL_4H_CANDLES_REQUIRED")
    for k in x.original_4h_source3m_ids:_validate_id(k,required=True)
    firsts=[_raw_start(i) for i in x.original_4h_source3m_ids]
    if (firsts[1]-firsts[0]!=4*HOUR or
        firsts[2]-firsts[1]!=4*HOUR or
        x.original_4h_known_ms!=firsts[2]+4*HOUR or
        x.original_4h_known_ms>x.source_as_of_ms or
        any(i.split(":")[0]!=x.original_4h_source3m_ids[0].split(":")[0]
            for i in x.original_4h_source3m_ids)):
        raise ValueError("C54_NONCAUSAL_OR_MIXED_4H_CRYPTO_SOURCE")
    touch=_validate_id(x.first_original3m_touch_id,required=False)
    later=_validate_id(x.first_later_1h_technical_imb_source3m_id,required=False)
    if (touch is None)!=(x.first_original3m_touch_known_ms is None):
        raise ValueError("C54_TOUCH_BAR_ID_KNOWN_AT_MISMATCH")
    if (later is None)!=(x.first_later_1h_technical_imb_known_ms is None):
        raise ValueError("C54_LATER_1H_CANDLE_ID_KNOWN_AT_MISMATCH")
    prefix=x.original_4h_source3m_ids[0].split(":")[0]
    if touch is not None:
        if (touch.split(":")[0]!=prefix or
            type(x.first_original3m_touch_known_ms) is not int or
            x.first_original3m_touch_known_ms!=_raw_start(touch)+THREE or
            x.first_original3m_touch_known_ms<=x.original_4h_known_ms or
            x.first_original3m_touch_known_ms>x.source_as_of_ms):
            raise ValueError("C54_CRYPTO_FIRST_TOUCH_PRE_PARENT_OR_FUTURE")
    if later is not None:
        if (touch is None or later.split(":")[0]!=prefix or
            type(x.first_later_1h_technical_imb_known_ms) is not int or
            _raw_start(later)%HOUR or
            x.first_later_1h_technical_imb_known_ms!=_raw_start(later)+3*HOUR or
            _raw_start(later)<x.first_original3m_touch_known_ms or
            x.first_later_1h_technical_imb_known_ms>x.source_as_of_ms):
            raise ValueError("C54_TECHNICAL_1H_VC_FUTURE_OR_ORPHAN")
    return True

def overlay_crypto_course_routes(parent,*,illustration=None,mode=None):
    validate_original_crypto_parent(parent)
    if illustration is not None:
        # Cross-market pictures are teaching rules, never market source inputs.
        raise ValueError("C54_COURSE_IMAGES_ARE_LOGIC_NOT_SOURCE_CANDLES")
    if set(ROUTE_MAP)!=set(TEXT_ROUTE_MODES):
        raise ValueError("C54_C45_ACADEMIC_ROUTE_REGISTRY_DRIFT")
    claims=recovered_text_claims()
    if len(claims)!=18:
        raise ValueError("C54_ORIGINAL_ACADEMY_18_RULES_MISSING")
    if mode is not None and mode not in ROUTE_MAP:
        raise ValueError("C54_UNKNOWN_ROUTE_NOT_IN_ACADEMY")
    modes=(mode,) if mode else tuple(ROUTE_MAP)
    result=[]
    for variant in modes:
        family=ROUTE_MAP[variant]
        expected=TEXT_ROUTE_MODES[variant]
        # The existing 4H IMB is only a technical research overlay, NOT
        # academic 4H typed POI/1H typed POI or raid/IDM entry trigger.
        state=("TECHNICAL_FIRST_TOUCH_UNKNOWN" if parent.first_original3m_touch_id is None
               else "TECHNICAL_1H_IMB_AFTER_TOUCH_ONLY"
               if parent.first_later_1h_technical_imb_source3m_id is not None
               else "TECHNICAL_FIRST_TOUCH_WITHOUT_1H_SOURCE")
        result.append(CryptoCourseOverlay(
            parent.symbol,TARGET,parent.source_as_of_ms,
            parent.original_4h_source3m_ids,variant,family,
            expected,ILLUSTRATION_ROLE,
            "ORIGINAL_BINANCE_USDM_NATIVE3M_AND_VALIDATED_NATIVE15M",
            parent.first_original3m_touch_id is None or
              parent.original_4h_known_ms<parent.first_original3m_touch_known_ms,
            parent.first_original3m_touch_id is not None,
            parent.first_later_1h_technical_imb_source3m_id is not None,
            True,False,SOURCE_MISSING,state))
    return tuple(result)

def original_c45_route_semantic_probe():
    """Check academically expected route mechanics WITHOUT certifying signal."""
    specs=tuple((k,ROUTE_MAP[k],TEXT_ROUTE_MODES[k]) for k in ROUTE_MAP)
    assert len(specs)==8
    assert all(x[1] in COURSE_ROLE_INDEPENDENT for x in specs)
    return specs
