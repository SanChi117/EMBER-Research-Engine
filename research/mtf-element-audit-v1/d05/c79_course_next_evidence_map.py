"""C79: original course Route A next-evidence map, NOT a trading signal.

No owner-authenticated crypto positive/negative goldens are supplied.
This module states what the original course requires NEXT in a HYPOTHETICAL
route, not that an observed source candle proves the requirement.
It never emits entries, execution, SL, TP or an approval.
"""
from dataclasses import dataclass

class C79Rejected(ValueError): pass

TRIGGERS={"NONE","SSL_RAID","BSL_RAID","ELIGIBLE_IMB"}
POIS={"RB","SNR","IMB","LIQUIDITY"}
POSSIBLE_VC={"IMB","SNR"}
@dataclass(frozen=True)
class CourseGate:
    next_evidence: str
    parent_branch: str
    author_authenticated: bool=False
    source_sufficiency: str="UNPROVEN_AUTHOR_GOLDEN"
    entry_allowed: bool=False
    orders: tuple=()
    fills: tuple=()
    trades: tuple=()
    readiness: str="NOT_TRADE_READY"

def hypothetical_next_step(parent_tf,parent_poi,parent_raid,trigger_1h,
                           first_1h_poi_test,trigger_15m,vc_kind,
                           *, from_4h_reaction):
    """Model the exact source course's event hierarchy, never assess market.

    parent_raid: 4H actual raid hypothesis, distinct from 4H POI test.
    first_1h_poi_test: DECLARED_SCENARIO, not proof that real candles pass.
    """
    if type(parent_tf)!=str or parent_tf not in ("4H","1H"):
        raise C79Rejected("UNKNOWN_PARENT_TF")
    if parent_poi not in POIS or type(parent_raid)!=bool or type(from_4h_reaction)!=bool:
        raise C79Rejected("INVALID_PARENT")
    if trigger_1h not in TRIGGERS or trigger_15m not in TRIGGERS or first_1h_poi_test not in ("NOT_TESTED","SOURCE_TOUCH_ONLY","HYPOTHETICAL_AUTHOR_VALID"):
        raise C79Rejected("INVALID_TRIGGER_OR_FIRST_TEST")
    if vc_kind not in ("NONE","IMB","SNR","RB","LIQUIDITY"):
        raise C79Rejected("INVALID_VC_TYPE")
    if parent_tf=="4H":
        if first_1h_poi_test!="NOT_TESTED" or trigger_15m!="NONE":
            raise C79Rejected("NO_1H_NEW_POI_CONTEXT")
        if parent_raid:
            if trigger_1h!="NONE":raise C79Rejected("4H_RAID_MEANS_NO_1H_TRIGGER")
            return CourseGate("REQUIRE_1H_VC_RB_SNR_IMB_NEW_POI","4H_RAID")
        if trigger_1h=="NONE":
            return CourseGate("REQUIRE_1H_VC_RB_SNR_IMB_NEW_POI","4H_POI_NO_1H_TRIGGER")
        if trigger_1h=="ELIGIBLE_IMB" and parent_poi=="IMB":
            raise C79Rejected("NESTED_1H_IMB_NOT_ALLOWED_INSIDE_4H_IMB")
        return CourseGate("REQUIRE_15M_VC_IMB_OR_SNR","4H_POI_1H_TRIGGER")
    if parent_raid or trigger_1h!="NONE" or not from_4h_reaction:
        raise C79Rejected("1H_POI_NEEDS_4H_REACTION_NO_1H_TRIGGER")
    if parent_poi=="LIQUIDITY":
        raise C79Rejected("1H_POI_TYPES_ONLY_RB_SNR_IMB")
    if first_1h_poi_test!="HYPOTHETICAL_AUTHOR_VALID":
        return CourseGate("REQUIRE_AUTHOR_VALID_FIRST_1H_POI_TEST","1H_NEW_POI")
    if trigger_15m=="NONE":
        return CourseGate("REQUIRE_DIRECT_15M_VC_IMB_OR_SNR","1H_POI_NO_15M_TRIGGER")
    if trigger_15m=="ELIGIBLE_IMB" and parent_poi=="IMB":
        return CourseGate("REQUIRE_AUTHOR_REVIEW_OF_NESTED_15M_IMB_ELIGIBILITY","1H_IMB_NESTED_ADAPTED_HYPOTHESIS")
    return CourseGate("REQUIRE_5M_VC_IMB_OR_SNR","1H_POI_WITH_15M_TRIGGER")
