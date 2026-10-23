"""C45: fail-closed course TEXT contract, not geometry nor trade engine.

Nine original lesson text exports were read from the owner's Google Drive.
17 claims stored separately with exact Drive IDs and lesson anchors.
No per-chart 2023 positive author labelled raw-candle golden was recovered.
A synthetic case matching course text is not a verified entry or signal.
Frozen C37-C44 implemented research approximations remain ADAPTED, untouched.
"""
from dataclasses import dataclass,replace
from pathlib import Path
import json

RULES_PATH=Path(__file__).with_name("C45_RECOVERED_AUTHOR_TEXT_RULES_20261023.json")
ACCEPTED_POI=("IMB","SNR","RB","LIQUIDITY")
ENTRY_VC=("IMB","SNR")
TEXT_ROUTE_MODES={
    "A_4H_TRIGGER_15M_VC":("4H","1H","15M","15M","4H"),
    "A_4H_NO_TRIGGER_1H_VC":("4H",None,"1H",None,"4H"),
    "A_1H_TRIGGER_5M_VC":("1H","15M","5M","5M","1H"),
    "A_1H_NO_TRIGGER_15M_VC":("1H",None,"15M","15M","1H"),
    "B_4H_VC_1H_IDM":("4H","1H",None,"1H","4H"),
    "B_1H_VC_15M_IDM":("1H","15M",None,"15M","1H"),
    "C_1H_RAID_3M_BOS":("1H","3M",None,"3M","1H"),
    "C_1H_RAID_5M_BOS":("1H","5M",None,"5M","1H"),
}
ADAPTED_PROXY_KINDS=("PREVIOUS_CLOSED_4H_RANGE","PREVIOUS_CLOSED_1D_RANGE",
    "C39_C44_HISTORICAL_POTENTIAL_1H_OBSTACLE","C44_PRIOR_CLOSED_4H_RANGE_PROXY",
    "C44_PRIOR_CLOSED_1D_RANGE_PROXY")

@dataclass(frozen=True)
class CourseContextCase:
    mode:str
    context_kind:str
    context_tf:str
    context_is_tested:bool
    verified_typed_poi_source:bool
    context_source_kind:str
    trigger_tf:str|None
    trigger_kind:str|None
    volume_confirmation_tf:str|None
    volume_confirmation_kind:str|None
    entry_tf:str|None
    target_tf:str
    target_kind:str
    stop_kind:str
    confirmed_strong_hl:bool
    raid_wick:bool=False
    bos_position:str|None=None
    direct_idm_within_or_ahead_poi:bool=False
    academic_author_chart_golden_verified:bool=False
    raw_order_approval:bool=False
    raid_kind:str|None=None

@dataclass(frozen=True)
class CourseGate:
    mode:str
    text_only_rule_consistent:bool
    source_claim_ids:tuple[str,...]
    blockers:tuple[str,...]
    author_chart_golden_verified:bool=False
    source_trade_ready:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def recovered_text_claims(path=RULES_PATH):
    data=json.loads(Path(path).read_text(encoding="utf8"))
    if data.get("schema")!="EMBER_C45_RECOVERED_COURSE_TEXT_AUTHOR_CONTRACT_V1":
        raise ValueError("C45_UNRECOGNIZED_COURSE_TEXT_SNAPSHOT")
    files=data["source_files"]
    ids={x["id"] for x in files}
    titles={x["title"] for x in files}
    claims=data["claims"]
    claim_ids=[x["id"] for x in claims]
    if (len(files)!=9 or len(ids)!=9 or len(titles)!=9 or
        len(claims)!=18 or len(set(claim_ids))!=17 or
        any(c["file"] not in titles or c["scope"] not in
            ("TEXT_RULE","KNOWN_LIMITATION") for c in claims) or
        any(not x["url"].startswith("https://drive.google.com/file/d/"+x["id"]+"/")
            for x in files) or
        data["source_only_gate"]!="NEVER_TRADE_READY"):
        raise ValueError("C45_FORGED_OR_INCOMPLETE_TEXT_SOURCE_CLAIMS")
    return {c["id"]:c for c in claims}

def evaluate_text_contract(case,claims=None):
    if not isinstance(case,CourseContextCase):
        raise ValueError("C45_UNTRUSTED_COURSE_CASE")
    if case.raw_order_approval or case.academic_author_chart_golden_verified:
        raise ValueError("C45_FORGED_AUTHOR_GOLDEN_OR_TRADE_APPROVAL")
    claims=claims if claims is not None else recovered_text_claims()
    if set(claims)!=set(recovered_text_claims()):
        raise ValueError("C45_MISSING_RECOVERED_AUTHOR_TEXT_RULE")
    if case.mode not in TEXT_ROUTE_MODES:
        raise ValueError("C45_UNKNOWN_COURSE_ROUTE")
    expected=TEXT_ROUTE_MODES[case.mode]
    failures=[]
    used=["POI-01","POI-02","STRONG-01"]
    def require(test,code):
        if not test:failures.append(code)
    if case.mode.startswith("C_"):
        used=["ROUTE-C-01","ROUTE-C-02","STRONG-01","LIQUIDITY-01"]
        require(case.context_tf=="1H" and case.context_kind=="LIQUIDITY",
                "C45_BOS_NOT_FROM_1H_LIQUIDITY")
        require(case.raid_wick,"C45_BOS_NO_CLEAN_1H_RAID_WICK")
        require(case.trigger_kind in ("3M_BOS","5M_BOS") and
                case.trigger_tf==expected[1] and
                case.trigger_kind==expected[1]+"_BOS",
                "C45_BOS_WRONG_OR_MISSING_3M_5M_CROSS")
        require(case.raid_kind in ("BSL","SSL") and
                case.bos_position==("BELOW_BSL_RAID" if case.raid_kind=="BSL"
                                   else "ABOVE_SSL_RAID"),
                "C45_BOS_NOT_ON_CORRECT_SIDE_OF_RAID")
        require(case.target_tf=="1H" and case.target_kind in
                ("EQL","EQH","FIRST_TROUBLE_AREA"),"C45_BOS_NO_CONTEXTUAL_1H_TARGET")
        require(case.stop_kind=="BEHIND_RAIDED_LIQUIDITY",
                "C45_BOS_STOP_NOT_AFTER_RAIDED_LIQUIDITY")
        require(case.volume_confirmation_tf is None and
                case.volume_confirmation_kind is None,
                "C45_BOS_ROUTE_MIXED_WITH_VC_ENTRY_MODEL")
        require(case.entry_tf==expected[3],"C45_BOS_WRONG_ENTRY_TIMEFRAME")
    else:
        require(case.context_tf==expected[0] and
                case.context_kind in ACCEPTED_POI,
                "C45_CONTEXT_PAIRED_POI_TIMEFRAME_OR_TYPE_MISSING")
        require(case.context_is_tested,"C45_PRIOR_TYPED_POI_TEST_NOT_EVIDENCED")
        require(case.verified_typed_poi_source and
                case.context_source_kind=="ACADEMIC_TYPED_POI" and
                case.context_kind not in ADAPTED_PROXY_KINDS,
                "C45_ADAPTED_CANDLE_RANGE_NOT_AUTHOR_POI")
        require(case.target_tf==expected[4] and
                case.target_kind in ("FTA","EQL","EQH","PDH","PDL"),
                "C45_FTA_WRONG_PARENT_TIMEFRAME")
        if case.mode.startswith("A_"):
            used.extend(["ROUTE-A-01","ROUTE-A-02","ROUTE-A-03","ROUTE-A-04",
                         "ROUTE-A-05","ROUTE-A-06"])
            require(case.trigger_tf==expected[1],"C45_WRONG_ROUTE_A_TRIGGER_TIMEFRAME")
            require(case.trigger_kind in ("BSL","SSL","IMB") if expected[1] is not None
                    else case.trigger_kind is None,
                    "C45_ROUTE_A_TRIGGER_MISSING_OR_FORGED")
            vc_types=("IMB","SNR","RB") if case.mode=="A_4H_NO_TRIGGER_1H_VC" else ENTRY_VC
            require(case.volume_confirmation_tf==expected[2] and
                    case.volume_confirmation_kind in vc_types,
                    "C45_ENTRY_VC_MUST_USE_IMB_OR_SNR")
            require(case.entry_tf==expected[3],"C45_ROUTE_A_ENTRY_TF_INVALID")
            require(case.stop_kind in ("BEHIND_STRONG_HIGH_LOW","BEHIND_PARENT_POI"),
                    "C45_ROUTE_A_STRUCTURAL_STOP_MISSING")
        else:
            used.extend(["ROUTE-B-01","ROUTE-B-02"])
            require(case.trigger_tf==expected[1] and case.trigger_kind=="IDM",
                    "C45_IDM_WRONG_TIMEFRAME_OR_MISSING")
            require(case.volume_confirmation_tf is None and
                    case.volume_confirmation_kind is None,
                    "C45_IDM_MUST_NOT_BORROW_FINAL_ROUTE_A_VC")
            require(case.entry_tf==expected[3],"C45_IDM_ENTRY_TF_INVALID")
            require(case.direct_idm_within_or_ahead_poi,
                    "C45_IDM_NOT_IN_OR_AHEAD_OF_PARENT_POI")
            require(case.stop_kind in ("BEHIND_STRONG_HIGH_LOW","BEHIND_PARENT_POI"),
                    "C45_IDM_STOP_STRUCTURE_MISSING")
        require(case.confirmed_strong_hl,"C45_STRONG_HL_NOT_A_BARE_PIVOT")
    return CourseGate(case.mode,not failures,tuple(sorted(set(used))),
        tuple(dict.fromkeys(failures)))
    
def source_only_c44_compatibility(evidence):
    """Never infer missing academic fields or silently promote C44 to author."""
    required=("original_bos_3m_row_id","source_reaction_confirmed",
              "decisions","original_bos_start_ms","original_bos_closed_ms")
    if not isinstance(evidence,dict) or any(k not in evidence for k in required):
        raise ValueError("C45_MISSING_C44_SOURCE_EVENT_FIELDS")
    if (evidence.get("orders") or evidence.get("trades") or
        evidence.get("readiness")!="NOT_TRADE_READY"):
        raise ValueError("C45_C44_FORGED_EXECUTABLE_OUTPUT")
    if ("verified_typed_poi_source" not in evidence or
        "context_is_tested" not in evidence or
        "academic_author_chart_golden_verified" not in evidence):
        return {"status":"COURSE_AUTHOR_POI_EVIDENCE_NOT_PRESENT",
                "author_ready":False,"orders":0}
    if evidence["academic_author_chart_golden_verified"]:
        raise ValueError("C45_C44_UNSUPPORTED_AUTHOR_GOLDEN")
    return {"status":"COURSE_AUTHOR_POI_NOT_ATTESTED",
            "author_ready":False,"orders":0}
