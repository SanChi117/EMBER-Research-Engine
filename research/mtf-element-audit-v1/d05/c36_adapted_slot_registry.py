"""C36 research-only strategy slot registry: academic core + adapted modules.

Not an autonomous trading strategy or execution adapter. Existing academic
C20-C35 original rules, ZIP evidence and 105 SHA ledger are read-only.

Only C36 BOS_PIVOT adaptation has technical variants. Reaction/POI/FTA/SL
are not silently made operational. The entry route is a C32 *observer*,
not a market or limit order.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from c36_adapted_pivot_hypotheses import VARIANTS,FROZEN_C33_SHA

ACADEMIC_CORE_REFERENCE={
    "academic_original_evidence":"C20-C35_READ_ONLY",
    "raid_known_at":"1H_FRACTAL_WICK_ONLY_SOURCE_COMPONENT",
    "bos_source":"INSTRUCTOR_SELECTED_3M_PIVOT_UNATTESTED",
    "snapshot_git_blob_C33":FROZEN_C33_SHA,
    "status":"PARTIALLY_SOURCE_VERIFIED_NOT_COMPLETE_AUTHOR_METHOD",
}
ACADEMIC_CORE_ID=sha256(json.dumps(ACADEMIC_CORE_REFERENCE,
    sort_keys=True,separators=(",",":")).encode()).hexdigest()

SLOTS={
    "RAID_1H":{"owner":"ACADEMIC_CORE","variants":(),
        "status":"SOURCE_GEOMETRY_OBSERVER_ONLY"},
    "REACTION":{"owner":"ADAPTED","variants":(),
        "status":"MISSING_VALIDATED_REACTION_ALGORITHM"},
    "BOS_PIVOT":{"owner":"ADAPTED","variants":VARIANTS,
        "status":"SELECTION_DISAGREEMENT_ONLY_NO_AUTHOR_GOLDENS"},
    "ENTRY":{"owner":"ACADEMIC_CORE","variants":(),
        "status":"TWO_C32_SOURCE_OBSERVERS_ONLY_NO_FILLS"},
    "FIRST_TROUBLE_AREA":{"owner":"ADAPTED","variants":(),
        "status":"NO_AUTHOR_PRIORITY_AND_NO_VALIDATED_ADAPTED_ROUTE"},
    "STOP_TARGET":{"owner":"ADAPTED","variants":(),
        "status":"NO_ATTESTED_FTA_SL_RR_AND_NO_TICK_ORDER"},
}

@dataclass(frozen=True)
class ResearchAssembly:
    academic_core_id:str
    parent_original_source_git_blob:str
    adapted_selection:tuple[tuple[str,str],...]
    unresolved_slots:tuple[str,...]
    audit_status:str="PARTIAL_ADAPTED_SLOT_DESIGN_ONLY"
    author_method_reproduced:bool=False
    technical_backtest_ready:bool=False
    paper_order_placement_allowed:bool=False
    real_order_placement_allowed:bool=False
    optimized_parameters:tuple=()
    backtest_results:tuple=()
    orders:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def create_research_assembly(adapted_choices,*,core_id=ACADEMIC_CORE_ID,
                              original_c33_git_blob=FROZEN_C33_SHA):
    if (type(core_id)!=str or core_id!=ACADEMIC_CORE_ID or
        original_c33_git_blob!=FROZEN_C33_SHA):
        raise ValueError("C36_ACADEMIC_CORE_OR_SOURCE_MUTATION_DENIED")
    if type(adapted_choices)!=dict:
        raise ValueError("C36_UNTRUSTED_ADAPTED_SELECTION")
    selected=[]
    for slot,choice in adapted_choices.items():
        if slot not in SLOTS:
            raise ValueError("C36_UNKNOWN_SLOT")
        opts=SLOTS[slot]["variants"]
        if SLOTS[slot]["owner"]!="ADAPTED":
            raise ValueError("C36_CANNOT_REPLACE_ACADEMIC_CORE")
        if choice not in opts:
            raise ValueError("C36_UNREGISTERED_OR_UNTESTED_ADAPTED_VARIANT")
        selected.append((slot,choice))
    # A research selection cannot fill all connected and validated slots.
    unresolved=tuple(k for k,v in SLOTS.items()
        if v["status"]!="SOURCE_GEOMETRY_OBSERVER_ONLY"
           and (k not in adapted_choices or k!="BOS_PIVOT"))
    return ResearchAssembly(core_id,FROZEN_C33_SHA,tuple(sorted(selected)),unresolved)

def slot_manifest():
    return {"schema":"EMBER_C36_VERSIONED_ACADEMIC_ADAPTED_RESEARCH_SLOTS_V1",
       "core_id":ACADEMIC_CORE_ID,
       "academic_core":dict(ACADEMIC_CORE_REFERENCE),
       "registered_slots":{k:{"owner":v["owner"],"variants":list(v["variants"]),
         "status":v["status"]} for k,v in SLOTS.items()},
       "holdout_caution":"C36 September 2026 holdout structural agreement was already inspected; it is NOT a pristine performance holdout. Reserve independently future original price data with realistic fees, execution and strategy freeze if full research engine is built.",
       "optimization_status":"NOT_STARTED_NO_PROFIT_TARGET_OBJECTIVE",
       "paper_execution_status":"FORBIDDEN_UNTIL_FULL_CAUSAL_BOS_ENTRY_FTA_SL_ASSEMBLY_VALIDATED",
       "real_execution_status":"FORBIDDEN",
       "author_goldens":0,"orders":0,"trades":0,
       "readiness":"NOT_TRADE_READY"}
