"""C108 minimal linked 4H FVG parent -> new 1H FVG child -> first test -> 15m IMB.
Research adaptation of owner-source 1H_PARENT, 1H_FIRST_TEST and direct 15m VC.
C105 4H stop/4H target geometry is entirely reused unchanged.
No imported LuxAlgo code or additional indicator zoo. PAPER ONLY.
"""
from dataclasses import dataclass
from decimal import Decimal as D
import c105_parent4h_structural_geometry as h4
from c91_continuous_causal_route_a_paper import _fvg

class C108Reject(ValueError):pass
@dataclass
class LinkedParent:
    side:str
    lower:D
    upper:D
    created_ms:int
    parent_id:str
    state:str="WAIT_PARENT_FIRST_TEST"
    first_touch_ms:int=0
    child_created_ms:int=0
    child_low:D=D("0")
    child_high:D=D("0")
    child_id:str=""
    child_first_test_ms:int=0
    vc_ms:int=0
    done:bool=False

def build_parent(last3_4h,days,weeks):
    parent,reason=h4.zone_from_three(last3_4h,days,weeks)
    if parent is None:return None,reason
    return LinkedParent(parent.side,parent.lower,parent.upper,
        parent.created_ms,parent.parent_id),"OK"

def parent_touch(x,c):
    if x.state!="WAIT_PARENT_FIRST_TEST" or c.close_ms<=x.created_ms:
        return False
    return c.h>=x.lower and c.l<=x.upper

def parent_invalidated(x,closed_h4):
    if closed_h4.close_ms<=x.created_ms:return False
    return (closed_h4.c<x.lower if x.side=="LONG" else closed_h4.c>x.upper)

def child_from_closed_h1(x,three):
    """Adaptation: 1H FVG born only AFTER first parent's 4H first test.
    C91 explicit nested 4H FVG -> 1H FVG veto is conserved.
    """
    if x.state!="WAIT_1H_CHILD" or len(three)!=3:
        return None,"NOT_1H_CHILD_PHASE"
    a,b,c=three
    if not(a.close_ms==b.start_ms and b.close_ms==c.start_ms
           and c.close_ms>x.first_touch_ms):
        return None,"H1_CHILD_NOT_CLOSED_AFTER_4H_TOUCH"
    fvg=_fvg(three)
    if not fvg or fvg[0]!=x.side:
        return None,"NO_MATCHING_1H_IMB"
    side,lo,hi=fvg
    if not 0<lo<hi:raise C108Reject("INVALID_NEW_1H_IMB")
    if lo>=x.lower and hi<=x.upper:
        return None,"NESTED_4H_IMB_1H_IMB_VETO"
    return (lo,hi,c.close_ms),"OK"

def adopt_child(x,created):
    if x.state!="WAIT_1H_CHILD" or created is None:
        raise C108Reject("EARLY_CHILD_CREATION")
    lo,hi,at=created
    if at<=x.first_touch_ms or not 0<lo<hi:
        raise C108Reject("NONCAUSAL_CHILD")
    x.child_low=lo;x.child_high=hi;x.child_created_ms=at
    x.child_id=x.parent_id+":H1:"+str(at)+":"+str(lo)+":"+str(hi)
    x.state="WAIT_CHILD_FIRST_TEST"
    return x

def child_first_touch(x,m15):
    if x.state!="WAIT_CHILD_FIRST_TEST" or m15.close_ms<=x.child_created_ms:
        return False
    return m15.h>=x.child_low and m15.l<=x.child_high

def adopt_child_first_test(x,m15):
    if not child_first_touch(x,m15) or x.child_first_test_ms:
        raise C108Reject("FIRST_1H_CHILD_PHYSICAL_TEST_REQUIRED")
    x.child_first_test_ms=m15.close_ms
    x.state="WAIT_15M_DIRECT_IMB"
    return x

def direct_15m_imb(x,last3):
    if x.state!="WAIT_15M_DIRECT_IMB" or len(last3)!=3:
        return False
    a,b,c=last3
    if not(a.close_ms==b.start_ms and b.close_ms==c.start_ms
           and c.close_ms>x.child_first_test_ms):
        return False
    fvg=_fvg(last3)
    return bool(fvg and fvg[0]==x.side)

def eligible_ttl(x,now):
    if type(now) is not int:raise C108Reject("NON_INT_TIME")
    if now>x.created_ms+h4.MAX_AGE:return "PARENT_48H_EXPIRED"
    if x.first_touch_ms and now>x.first_touch_ms+h4.TTL:
        return "PARENT_FIRST_TOUCH_8H_TTL_EXPIRED"
    return ""

def protective_stop_semantics(x,exit_reason,closed_h4):
    """Descriptive; must NEVER revise the executable 3m protective stop price.
    It is legitimate for protective SL to fire while the 4H zone stays 'narratively'
    valid at its later H4 close. Record distinction and do not move stop.
    """
    if exit_reason not in ("STOP_GAP","STOP_FIRST_SAME_3M"):
        return {"protective_stop_triggered":False,
                "parent_validity_at_4h_close":"NOT_A_STOP"}
    return {"protective_stop_triggered":True,
        "parent_validity_at_4h_close":(
            "INVALIDATED" if parent_invalidated(x,closed_h4) else "STILL_VALID"),
        "risk_policy":"EXECUTABLE_NATIVE3M_PROTECTIVE_STOP_NEVER_WIDEN",
        "setup_policy":"4H_CLOSE_PARENT_VALIDITY_DISTINCT_FROM_RISK_SL"}
