"""C78: Route A source clock checks, never certify an academic Trigger or VC.

Original course requires valid first 1H POI test; actual 15m Trigger
(SSL/BSL/eligible IMB) -> 5m VC, without Trigger -> direct 15m VC.
C67/C73 labels and raw geometric FVG are NOT author assessments.
"""
from dataclasses import dataclass
from collections import Counter

class C78Rejected(ValueError):pass

@dataclass(frozen=True)
class SourceGate:
    symbol:str
    index:int
    parent:str
    physical_visit:str
    geometric_15m:str
    geometric_5m:str
    author_valid_first_test:bool=False
    author_15m_trigger:bool=False
    author_15m_vc:bool=False
    author_5m_vc:bool=False
    author_entry:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def assess(a,b):
    if type(a)!=dict or type(b)!=dict:raise C78Rejected("INPUT")
    for k in ("symbol","side","original_c46_4h_parent_index","c67_route_a_source_fork_state"):
        if a.get(k)!=b.get(k):raise C78Rejected("JOIN_"+k)
    if a["symbol"] not in ("BCHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT") or a["side"] not in ("LONG","SHORT") or type(a["original_c46_4h_parent_index"])!=int:raise C78Rejected("MARKET")
    if a.get("readiness")!="NOT_TRADE_READY" or b.get("readiness")!="NOT_TRADE_READY":raise C78Rejected("READY")
    for d,flags in ((a,("author_15m_trigger","author_15m_vc","author_5m_vc","author_entry","author_stronghl","author_structural_sl","author_1h_poi_valid_first_test","route_b_idm_used","route_c_raid_bos_used")),(b,("author_15m_trigger","author_5m_vc","author_5m_stronghl","author_structural_sl","author_valid_first_1h_poi_test","route_b_idm_used","route_c_raid_bos_used"))):
        if any(d.get(k) is not False for k in flags):raise C78Rejected("FORGED_AUTHOR")
        if any(d.get(k)!=[] for k in ("orders","fills","trades")):raise C78Rejected("FORGED_TRADE")
    s=a.get("state");f=a.get("c67_route_a_source_fork_state");z=b.get("state")
    if z!=a.get("c72_post_15m_first_any_5m_source_state") or z!=a.get("source_first_5m_after_candidate_state"):raise C78Rejected("C72_DRIFT")
    base=(a["symbol"],a["original_c46_4h_parent_index"])
    no="NO_C71_SINGLE_NEW_1H_POI_15M_SOURCE"
    if s=="NOT_NEW_1H_POI_SOURCE_BRANCH":
        if z!=no or f.startswith("NEW_1H_VC_"):raise C78Rejected("BAD_BRANCH")
        return SourceGate(*base,"NO_NEW_1H_POI","NONE","NONE","NONE")
    if s=="NEW_1H_POI_SOURCE_NO_ORIGINAL3M_FIRST_TOUCH":
        if f not in ("FIRST_ANY_1H_SOURCE_OPPOSITE_SIDE","FIRST_ANY_1H_TRIGGER_AND_VC_AMBIGUOUS","FIRST_ANY_1H_TWO_SIDES_AMBIGUOUS") or z!=no:raise C78Rejected("UNSELECTED")
        return SourceGate(*base,"UNSELECTED_1H_SOURCE","NONE","NONE","NONE")
    if not f.startswith("NEW_1H_VC_FIRST_SOURCE_TEST_"):raise C78Rejected("SELECTED_BRANCH")
    touch=a.get("original_first_source3m_touch_closed_ms")
    created=a.get("source_1h_poi_created_at_ms")
    if type(touch)!=int or type(created)!=int or touch<=created or not a.get("original_first_source3m_touch_id"):raise C78Rejected("NO_FIRST_TOUCH")
    if s=="NEW_1H_POI_FIRST_ANY_RAW3M_TOUCH_NO_UNAMBIGUOUS_15M_CHAIN":
        if z!=no or a.get("first_source15m_event_fully_known_ms") is not None:raise C78Rejected("NO_15M_GATE")
        return SourceGate(*base,"SELECTED_1H_SOURCE","WICK_FIRST","NONE","NONE")
    if s not in ("NEW_1H_POI_FIRST_15M_PATTERN_SINGLE_SOURCE_VISIT_NOT_OWNER_VALID","NEW_1H_POI_FIRST_15M_PATTERN_REVISITED_SOURCE_POI_NOT_OWNER_VALID"):raise C78Rejected("UNKNOWN_STATE")
    ep=a.get("episodes_before_first_15m_pattern")
    if type(ep)!=int or ep<1 or (s.endswith("SINGLE_SOURCE_VISIT_NOT_OWNER_VALID") and ep!=1) or (s.endswith("REVISITED_SOURCE_POI_NOT_OWNER_VALID") and ep<2):raise C78Rejected("EPISODES")
    start=a.get("first_source15m_event_pattern_start_ms");close=a.get("first_source15m_event_fully_known_ms");five=b.get("first_any_5m_event_known_ms")
    if any(type(q)!=int for q in (start,close,five)) or not touch<start<close<five or b.get("c71_provisional_15m_known_ms")!=close or b.get("source_start_5m_gate_ms")!=close:raise C78Rejected("LOOKAHEAD")
    kind=a.get("c71_first_any_15m_source_state")
    if kind not in ("FIRST_ANY_NEW1H_POI_15M_IMB_TRIGGER_VS_VC_UNRESOLVED","FIRST_ANY_NEW1H_POI_15M_SNR_TRIGGER_VS_VC_UNRESOLVED"):raise C78Rejected("15M_GEOMETRY")
    m={"FIRST_5M_IMB_ALIGNED_NOT_AUTHOR_VC":"ALIGNED","FIRST_5M_SNR_ALIGNED_NOT_AUTHOR_VC":"ALIGNED","FIRST_5M_SOURCE_OPPOSITE_SIDE":"OPPOSITE","FIRST_5M_SOURCE_MULTIPLE_KINDS_AMBIGUOUS":"AMBIGUOUS"}
    if z not in m or not b.get("first_any_5m_kinds") or not b.get("first_any_5m_sides"):raise C78Rejected("5M_GEOMETRY")
    return SourceGate(*base,"SELECTED_1H_SOURCE","ONE_VISIT" if ep==1 else "MULTIPLE_VISITS","IMB" if "IMB_" in kind else "SNR",m[z])

def tally(rows):
    if type(rows)!=tuple or any(type(r)!=SourceGate or r.readiness!="NOT_TRADE_READY" or any((r.author_valid_first_test,r.author_15m_trigger,r.author_15m_vc,r.author_5m_vc,r.author_entry,r.orders,r.fills,r.trades)) for r in rows):raise C78Rejected("PROMOTION")
    return {"contexts":len(rows),"parent":dict(Counter(r.parent for r in rows)),"touch":dict(Counter(r.physical_visit for r in rows)),"source_15m":dict(Counter(r.geometric_15m for r in rows)),"source_5m":dict(Counter(r.geometric_5m for r in rows)),"author_verified":0,"orders":0,"fills":0,"trades":0,"readiness":"NOT_TRADE_READY"}
