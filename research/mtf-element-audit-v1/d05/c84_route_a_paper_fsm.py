"""C84 Route A PAPER-only research state machine. Never emits orders.

Source geometry and the hypothetical scenario route are separate channels.
No uploaded or derived event can be AUTHOR_VERIFIED without independently
authenticated original author positive AND negative crypto chart goldens.
"""
from dataclasses import dataclass, replace
from collections import Counter
from c83_owner_course_text_crosswalk import source_matched_queue
from c81_source_authenticated_review_queue import validate_queue

class C84Rejected(ValueError): pass

@dataclass(frozen=True)
class Event:
    name: str
    close_ms: int
    kind: str = ""
    status: str = "ADAPTED_HYPOTHESIS"
    route: str = "A"
    missing_bars: bool = False
    purported_author_media: bool = False

@dataclass(frozen=True)
class State:
    phase: str = "START"
    known_ms: int = -1
    visits: int = 0
    parent: str = ""
    one_hour_poi: str = ""
    observations: tuple = ()
    history: tuple = ()
    author_verified: bool = False
    entry_allowed: bool = False
    orders: tuple = ()
    fills: tuple = ()
    trades: tuple = ()
    readiness: str = "NOT_TRADE_READY"

TRIGGER = {"SSL_RAID","BSL_RAID","ELIGIBLE_IMB"}
VC = {"IMB","SNR"}
ONEH = {"RB_RAID","RB_IMB","SNR","IMB"}
EVENTS = {"4H_POI","4H_FIRST_TEST","4H_RAID","1H_TRIGGER",
          "1H_NEW_POI","1H_TOUCH","1H_FIRST_TEST","15M_TRIGGER",
          "15M_DIRECT_VC","15M_VC_AFTER_1H_TRIGGER","5M_VC",
          "INVALIDATE","DATA_GAP"}
TERMINAL = {"SCENARIO_ONLY","INVALIDATED"}

def advance(s,e):
    if type(s) is not State or type(e) is not Event:
        raise C84Rejected("BAD_EVENT_OR_STATE_TYPE")
    if s.author_verified or s.entry_allowed or s.orders or s.fills or s.trades or s.readiness!="NOT_TRADE_READY":
        raise C84Rejected("FORGED_TRADE_STATE")
    if type(e.close_ms) is not int or e.close_ms<=s.known_ms or e.close_ms<0:
        raise C84Rejected("LOOKAHEAD_OR_NONCLOSED_TIME")
    if e.route!="A" or e.name not in EVENTS:
        raise C84Rejected("ROUTE_B_C_OR_UNKNOWN_EVENT")
    if e.status not in ("UNKNOWN","SOURCE_TECHNICAL","ADAPTED_HYPOTHESIS","AUTHOR_VERIFIED"):
        raise C84Rejected("INVALID_EVIDENCE_CLASS")
    if e.purported_author_media or e.status=="AUTHOR_VERIFIED":
        raise C84Rejected("NO_AUTHENTICATED_AUTHOR_CRYPTO_GOLDEN")
    if e.missing_bars or e.name=="DATA_GAP":
        raise C84Rejected("SOURCE_BAR_GAP")
    # Technical price coincidences never create academic triggers or tests.
    if e.status in ("UNKNOWN","SOURCE_TECHNICAL"):
        return replace(s,known_ms=e.close_ms,
          observations=s.observations+((e.name,e.close_ms,e.status),))
    if s.phase in TERMINAL:
        raise C84Rejected("TERMINAL_STATE")
    k=e.name; d=e.kind; p=s.phase
    next_phase=None; extra={}
    if k=="INVALIDATE":
        next_phase="INVALIDATED"
    elif (p,k)==("START","4H_POI"):
        if d not in {"RB","SNR","IMB","LIQUIDITY"}: raise C84Rejected("4H_POI_KIND")
        next_phase="WAIT_4H_FIRST_TEST";extra["parent"]=d
    elif (p,k)==("WAIT_4H_FIRST_TEST","4H_RAID"):
        next_phase="WAIT_1H_NEW_POI"
    elif (p,k)==("WAIT_4H_FIRST_TEST","4H_FIRST_TEST"):
        next_phase="WAIT_1H_BRANCH"
    elif (p,k)==("WAIT_1H_BRANCH","1H_TRIGGER"):
        if d not in TRIGGER:raise C84Rejected("1H_TRIGGER_KIND")
        if s.parent=="IMB" and d=="ELIGIBLE_IMB":
            raise C84Rejected("NESTED_4H_IMB_1H_IMB_VETO")
        next_phase="WAIT_15M_VC_FROM_1H_TRIGGER"
    elif p in {"WAIT_1H_BRANCH","WAIT_1H_NEW_POI"} and k=="1H_NEW_POI":
        if d not in ONEH:raise C84Rejected("RB_RAID_OR_IMB_MISSING")
        next_phase="WAIT_1H_TOUCH";extra["one_hour_poi"]=d
    elif (p,k)==("WAIT_15M_VC_FROM_1H_TRIGGER","15M_VC_AFTER_1H_TRIGGER"):
        if d not in VC:raise C84Rejected("INVALID_15M_VC")
        next_phase="SCENARIO_ONLY"
    elif (p,k)==("WAIT_1H_TOUCH","1H_TOUCH"):
        next_phase="WAIT_1H_FIRST_TEST";extra["visits"]=1
    elif (p,k)==("WAIT_1H_FIRST_TEST","1H_TOUCH"):
        next_phase="WAIT_1H_FIRST_TEST";extra["visits"]=s.visits+1
    elif (p,k)==("WAIT_1H_FIRST_TEST","1H_FIRST_TEST"):
        if s.visits!=1:raise C84Rejected("REVISIT_CANNOT_BE_FIRST")
        next_phase="WAIT_15M_BRANCH"
    elif (p,k)==("WAIT_15M_BRANCH","15M_TRIGGER"):
        if d not in TRIGGER:raise C84Rejected("15M_TRIGGER_KIND")
        # 1H IMB with nested 15m IMB remains an unverified adaptation.
        next_phase="WAIT_5M_VC"
    elif (p,k)==("WAIT_15M_BRANCH","15M_DIRECT_VC"):
        if d not in VC:raise C84Rejected("DIRECT_15M_VC_KIND")
        next_phase="SCENARIO_ONLY"
    elif (p,k)==("WAIT_5M_VC","5M_VC"):
        if d not in VC:raise C84Rejected("5M_VC_KIND")
        next_phase="SCENARIO_ONLY"
    if next_phase is None:
        raise C84Rejected("ILLEGAL_ROUTE_ORDER_"+p+"_"+k)
    return replace(s,phase=next_phase,known_ms=e.close_ms,
      history=s.history+((k,e.close_ms),),**extra)

def simulate(events):
    s=State()
    for e in events:s=advance(s,e)
    return s

def original153_projection(c73,c72,c81):
    """Revalidate frozen exact source SHA and 153 cases before projecting."""
    q=source_matched_queue(c73,c72,c81)
    validate_queue(q)
    rows=[]
    for x in q:
        if x.priority==0:
            clocks=(x.poi_created_ms,x.first_original_3m_close_ms,
                    x.source15m_known_ms,x.first5m_known_ms)
            if any(type(t) is not int for t in clocks) or not clocks[0]<clocks[1]<clocks[2]<clocks[3]:
                raise C84Rejected("P0_SOURCE_CLOCK")
            if type(x.visits_before_source15m) is not int or x.visits_before_source15m<1:
                raise C84Rejected("INVALID_P0_VISITS")
            if x.first5m_kind.endswith("_NOT_AUTHOR_VC"):label="SOURCE_5M_ALIGNED"
            elif x.first5m_kind=="FIRST_5M_SOURCE_OPPOSITE_SIDE":label="SOURCE_5M_OPPOSITE"
            else:label="SOURCE_5M_AMBIGUOUS"
        elif x.priority==1:
            if x.source15m_known_ms is not None or x.first5m_known_ms is not None:
                raise C84Rejected("P1_FUTURE_CLOCK")
            label="FIRST_RAW3M_TOUCH_ONLY"
        elif x.priority==2:
            if x.first_original_3m_close_ms is not None or x.source15m_known_ms is not None or x.first5m_known_ms is not None:
                raise C84Rejected("P2_UNSELECTED_PROMOTION")
            label="UNSELECTED_1H_PARENT"
        elif x.priority==3:
            if x.poi_kind!="NO_NEW_1H_POI" or x.source15m_known_ms is not None or x.first5m_known_ms is not None:
                raise C84Rejected("P3_PARENT_PROMOTION")
            label="NO_SELECTED_1H_POI"
        else:raise C84Rejected("BAD_PRIORITY")
        rows.append({"case":x.source_key,"priority":x.priority,"source_observation":label,
             "source_visits":x.visits_before_source15m,
             "phase":"NO_PARENT_SOURCE" if x.priority==3 else "WAIT_AUTHENTIC_4H_FIRST_TEST",
             "author_4h_first_test":False,"author_1h_first_test":False,
             "author_15m_trigger":False,"author_direct_15m_vc":False,
             "author_5m_vc":False,"entry_allowed":False,"orders":[],
             "fills":[],"trades":[],"readiness":"NOT_TRADE_READY"})
    if len(rows)!=153 or len({r["case"] for r in rows})!=153:raise C84Rejected("SOURCE_COUNT")
    return rows

def summarize(rows):
    if len(rows)!=153 or len({r["case"] for r in rows})!=153:raise C84Rejected("COUNT")
    if any(r["entry_allowed"] or r["orders"] or r["fills"] or r["trades"] or
           r["readiness"]!="NOT_TRADE_READY" for r in rows):
        raise C84Rejected("TRADE_PROMOTION")
    return {"schema":"C84_ROUTE_A_SOURCE_ONLY_FSM_V1","total":153,
      "priority":dict(sorted(Counter(str(r["priority"]) for r in rows).items())),
      "observations":dict(sorted(Counter(r["source_observation"] for r in rows).items())),
      "author_goldens":0,"author_accepted_transitions":0,"orders":0,
      "fills":0,"trades":0,"readiness":"NOT_TRADE_READY"}
