"""C59 — academic Strong High/Low, first POI test and Route A 4H-IMB veto.

Read from OWNER's exact Strong High & Low.txt, Fair Value Gap Imbalance.txt
and 2. Entry by IMB & SNR.txt on Google Drive, rechecked 2026-10-25.

AUTHOR TEXT:
  (1) Strong HL requires liquidity/inefficiency CONTACT then a confirming
      VC POI or BOS *movement*, not merely a pivot/fractal.
  (2) A real POI's first test matters; repeated contact is not pristine.
  (3) When 4H context is IMB, do NOT count a 1H IMB INSIDE it as trigger.
  (4) Contextual 1H trigger is BSL/SSL or conditionally IMB; final Route A
      entry VC is separately 15m IMB/SNR. Do not mix with Route B IDM.

Neither text nor previously source-frozen original C46/C47/C58 are an
author-labelled price/candle golden. This module is a fail-closed evidence
contract only, and can NEVER approve author entries, stops or orders.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum

class Relation(str,Enum):
    INSIDE="1H_IMB_ENTIRELY_INSIDE_4H_IMB"
    OVERLAP="1H_IMB_PARTIALLY_OVERLAPS_4H_IMB"
    OUTSIDE="1H_IMB_OUTSIDE_4H_IMB"

@dataclass(frozen=True)
class AcademicStructureCase:
    """Independent text-level case: positive consistency is NOT verification."""
    route:str
    parent_poi_kind:str
    parent_context_tf:str
    parent_was_known:bool
    first_valid_poi_test_confirmed:bool
    independent_author_poi_selection:bool
    price_contact_kind:str|None
    contact_known_ms:int|None
    confirming_movement_kind:str|None
    confirming_movement_known_ms:int|None
    confirming_movement_tf:str|None
    confirmed_extreme_kind:str|None
    strong_extreme_source_verified:bool
    lower_tf_trigger_kind:str|None
    child_imb_relation:Relation|None=None
    author_chart_golden_verified:bool=False
    place_order:bool=False

@dataclass(frozen=True)
class SemanticGate:
    route:str
    text_constraints_met:bool
    blockers:tuple[str,...]
    course_author_price_golden_verified:bool=False
    author_poi_approved:bool=False
    strong_high_low_approved:bool=False
    approved_signal:bool=False
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def _ms(x):
    return type(x) is int and x>=0

def course_stronghl_firsttest_gate(x):
    """Positive ONLY means hypothetical *text* consistency; NO trade-ready."""
    if not isinstance(x,AcademicStructureCase):
        raise ValueError("C59_UNTRUSTED_COURSE_CASE")
    if x.author_chart_golden_verified or x.place_order:
        raise ValueError("C59_FORGED_AUTHOR_GOLDEN_OR_ORDER")
    if x.route not in ("A_4H_TRIGGER_15M_VC","A_4H_NO_TRIGGER_1H_VC",
                     "B_4H_VC_1H_IDM","B_1H_VC_15M_IDM"):
        raise ValueError("C59_UNKNOWN_ROUTE")
    if x.parent_poi_kind not in ("IMB","SNR","RB","LIQUIDITY"):
        raise ValueError("C59_INVALID_POI_TYPE")
    blockers=[]
    def require(p,code):
        if not p:blockers.append(code)
    require(x.parent_context_tf in ("4H","1H") and
        (x.parent_context_tf=="4H" if x.route!="B_1H_VC_15M_IDM" else
         x.parent_context_tf=="1H"),
        "C59_WRONG_POI_CONTEXT_TF")
    require(x.parent_was_known and x.independent_author_poi_selection,
        "C59_UNSELECTED_CONTEXT_NOT_AUTHOR_POI")
    require(x.first_valid_poi_test_confirmed,
        "C59_FIRST_VALID_POI_TEST_NOT_PROVEN")
    require(x.price_contact_kind in ("LIQUIDITY","INEFFICIENCY"),
        "C59_STRONGHL_CONTACT_NOT_LIQUIDITY_OR_INEFFICIENCY")
    require(_ms(x.contact_known_ms),
        "C59_STRONGHL_CONTACT_MISSING_CLOSED_TIME")
    require(x.confirming_movement_kind in ("VC_POI","BOS"),
        "C59_STRONGHL_NO_VC_POI_OR_BOS_CONFIRMATION")
    require(x.confirming_movement_tf in ("1H","15M","5M","4H"),
        "C59_STRONGHL_CONFIRMATION_TF_UNKNOWN")
    require(_ms(x.confirming_movement_known_ms) and
            _ms(x.contact_known_ms) and
            x.confirming_movement_known_ms>x.contact_known_ms,
        "C59_STRONGHL_CONFIRMED_BEFORE_OR_AT_CONTACT")
    require(x.confirmed_extreme_kind in ("STRONG_HIGH","STRONG_LOW") and
            x.strong_extreme_source_verified,
        "C59_BARE_PIVOT_NOT_STRONG_HIGH_LOW")
    if x.route.startswith("A_"):
        require(x.lower_tf_trigger_kind in ("BSL","SSL","IMB") if
                x.route=="A_4H_TRIGGER_15M_VC" else
                x.lower_tf_trigger_kind is None,
                "C59_ROUTE_A_TRIGGER_MODEL_MIX")
        if (x.parent_context_tf=="4H" and x.parent_poi_kind=="IMB"
            and x.lower_tf_trigger_kind=="IMB"):
            require(x.child_imb_relation is Relation.OUTSIDE,
                "C59_1H_IMB_INSIDE_4H_IMB_NOT_VALID_ROUTE_A_TRIGGER")
    else:
        require(x.lower_tf_trigger_kind=="IDM",
            "C59_ROUTE_B_MUST_KEEP_IDM_SEPARATE")
    return SemanticGate(x.route,not blockers,tuple(dict.fromkeys(blockers)))

def _num(value):
    if not isinstance(value,str):
        raise ValueError("C59_UNTRUSTED_ORIGINAL_ZONE_PRICE")
    try:z=Decimal(value)
    except (InvalidOperation,ValueError) as e:
        raise ValueError("C59_UNTRUSTED_ORIGINAL_ZONE_PRICE") from e
    if not z.is_finite() or z<=0:
        raise ValueError("C59_UNTRUSTED_ORIGINAL_ZONE_PRICE")
    return z

def nested_original_imb_relation(parent_bottom,parent_top,child_bottom,child_top):
    """Closed-zone source geometry. Boundary touch counts as INSIDE."""
    a,b,c,d=map(_num,(parent_bottom,parent_top,child_bottom,child_top))
    if not (a<b and c<d):raise ValueError("C59_REVERSED_SOURCE_ZONE")
    if a<=c and d<=b:return Relation.INSIDE
    if d<a or c>b:return Relation.OUTSIDE
    return Relation.OVERLAP

SOURCE_STATUSES=("NO_4H_SOURCE_FIRST_CONTACT",
 "4H_FIRST_CONTACT_NO_LATER_1H_SOURCE",
 "LATER_1H_IMB_INSIDE_PARENT_4H_IMB_VETO",
 "LATER_1H_IMB_PARTIALLY_OVERLAPS_PARENT_VETO",
 "LATER_1H_IMB_OUTSIDE_PARENT_GEOMETRY_ONLY")
 
def source_parent_contract(parent46,child47,liquidity58):
    """Check three immutable original source records are the same parent.
    Return a labeled technical relation, never any author approval.
    """
    if not all(isinstance(x,dict) for x in (parent46,child47,liquidity58)):
        raise ValueError("C59_UNTRUSTED_SOURCE_PARENT")
    c=parent46.get("candidate")
    if not isinstance(c,dict):
        raise ValueError("C59_MISSING_4H_SOURCE_CANDIDATE")
    if any((c.get("author_poi_certified"),parent46.get("academic_poi_test_certified"),
            parent46.get("academic_volume_confirmation_certified"),
            child47.get("course_typed_poi_approved"),
            child47.get("course_first_valid_test_approved"),
            child47.get("course_volume_confirmation_approved"),
            liquidity58.get("author_typed_poi_verified"),
            liquidity58.get("author_stronghl_verified"),
            liquidity58.get("academic_idm_approved"),
            child47.get("author_chart_golden_count"))):
        raise ValueError("C59_UNSUPPORTED_AUTHOR_SOURCE_PROMOTION")
    for x in (c,parent46,child47,liquidity58):
        if x.get("orders") or x.get("trades"):
            raise ValueError("C59_FORGED_ORDERS_IN_SOURCE_EVIDENCE")
    if (parent46.get("readiness")!="NOT_TRADE_READY" or
        child47.get("readiness")!="NOT_TRADE_READY" or
        liquidity58.get("readiness")!="NOT_TRADE_READY" or
        c.get("source_status")!="C46_NATIVE_4H_CLASSIC_IMB_GEOMETRY_ONLY"):
        raise ValueError("C59_SOURCE_PARENT_NOT_RESEARCH_ONLY")
    if (child47.get("original4h_zone_known_ms")!=c.get("fully_known_ms") or
        liquidity58.get("four_hour_gap_fully_known_ms")!=c.get("fully_known_ms") or
        child47.get("original4h_zone_side")!=c.get("side") or
        liquidity58.get("technical_4h_imb_side")!=c.get("side") or
        child47.get("original4h_zone_first_raw3m_ids")!=
            c.get("three_original_source_first_native3m_ids") or
        parent46.get("first_contact_original3m_id")!=
            child47.get("original4h_first_contact_native3m_id") or
        parent46.get("first_contact_original3m_id")!=
            liquidity58.get("first_contact_original3m_id") or
        parent46.get("first_contact_closed_known_ms")!=
            child47.get("original4h_first_contact_closed_known_ms") or
        parent46.get("first_contact_bar_start_ms")!=
            liquidity58.get("first_contact_bar_start_ms") or
        str(_num(c["bottom"]))!=str(_num(liquidity58["technical_4h_imb_bottom"])) or
        str(_num(c["top"]))!=str(_num(liquidity58["technical_4h_imb_top"]))):
        raise ValueError("C59_CROSS_FROZEN_C46_C47_C58_PARENT_ID_DRIFT")
    ival=liquidity58.get("preknown_inside_1h_liquidity")
    if not isinstance(ival,list) or any(not isinstance(x,dict) or
        x.get("author_idm_certified") or x.get("strong_high_low_author_certified")
        for x in ival):
        raise ValueError("C59_FALSE_AUTHOR_IDM_IN_SOURCE_PARENT")
    h=child47.get("first_post_contact_1h_imb_source")
    if parent46.get("first_contact_original3m_id") is None:
        if h is not None or ival:
            raise ValueError("C59_FUTURE_CHILD_WITHOUT_PARENT_CONTACT")
        status=SOURCE_STATUSES[0];relation=None
    elif h is None:
        status=SOURCE_STATUSES[1];relation=None
    else:
        if (not isinstance(h,dict) or h.get("academic_vc_certified") or
            h.get("orders") or h.get("trades") or
            h.get("fully_known_ms") is None or
            h["fully_known_ms"]<=parent46["first_contact_closed_known_ms"] or
            h.get("side")!=c.get("side")):
            raise ValueError("C59_FORGED_OR_PRE_CONTACT_1H_IMB_SOURCE")
        relation=nested_original_imb_relation(c["bottom"],c["top"],
                                              h["bottom"],h["top"])
        status={Relation.INSIDE:SOURCE_STATUSES[2],
                Relation.OVERLAP:SOURCE_STATUSES[3],
                Relation.OUTSIDE:SOURCE_STATUSES[4]}[relation]
    return {
        "status":status,
        "relation":relation.value if relation is not None else None,
        "source_4h_known_ms":c["fully_known_ms"],
        "first_original3m_contact_id":parent46.get("first_contact_original3m_id"),
        "post_contact_1h_imb_known_ms":h["fully_known_ms"] if h else None,
        "source_1h_preknown_liquidity_count":len(ival),
        "first_touch_source_geometry_only":True,
        "course_author_first_valid_test":False,
        "course_author_strongHL":False,
        "course_author_routeA_trigger":False,
        "course_author_routeB_IDM":False,
        "orders":0,"trades":0,"readiness":"NOT_TRADE_READY"
    }
