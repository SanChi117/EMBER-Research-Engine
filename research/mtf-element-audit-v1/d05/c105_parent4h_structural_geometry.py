"""C105: causal SAME PARENT 4H FVG POI/SL/TP geometry. PAPER ONLY.
No 1H, 15m or 3m pivot/ATR is allowed in exit geometry.
Academic concepts are adapted and empirically unvalidated.
"""
from bisect import bisect_left
from collections import Counter
from decimal import Decimal as D
from dataclasses import dataclass
from c91_continuous_causal_route_a_paper import OHLC,_fvg,_vc,_weekly_daily_context,WEEK_ANCHOR
import c93_native3m_raid_bos_route_c_research as c93
from c21_native3m_source_bridge import Original3mRow,THREE

H=3600000
H4=4*H
D1=24*H
W1=7*D1
M15=15*60000
TTL=8*H
MAX_AGE=48*H
MAX_HOLD=48*H//THREE
PAD=D("0.15")
MIN_RR=D("1.25")
MIN_RISK=D("0.002")
MAX_RISK=D("0.10")
LOOKBACK=14
BPS=(14,25,40)
EVIDENCE="ADAPTED_4H_OWNER_PARENT_NO_AUTHOR_GOLDEN"
class C105Rejected(ValueError):pass

@dataclass
class Parent:
    side:str
    lower:D
    upper:D
    created_ms:int
    parent_id:str
    first_touch_ms:int=0
    rejection_ms:int=0
    state:str="WAIT_FIRST_TOUCH"
    done:bool=False

def aggregate(rows,tf,anchor=0):
    if tf not in (M15,H,H4,D1,W1) or type(rows) is not tuple or not rows:
        raise C105Rejected("UNREGISTERED_ORIGINAL_TF")
    if type(anchor) is not int or anchor!= (WEEK_ANCHOR if tf==W1 else 0):
        raise C105Rejected("BAD_UTC_TF_ANCHOR")
    if any(type(x) is not Original3mRow or
           (i and rows[i-1].known_ms!=x.start_ms) for i,x in enumerate(rows)):
        raise C105Rejected("NATIVE3M_TYPE_OR_CLOCK_GAP")
    n=tf//THREE;out=[]
    for off in range(0,len(rows)):
        if (rows[off].start_ms-anchor)%tf:continue
        if off+n>len(rows):break
        seq=rows[off:off+n]
        if seq[-1].known_ms!=seq[0].start_ms+tf:raise C105Rejected("ORIGINAL_TF_GAP")
        out.append(OHLC(seq[0].start_ms,seq[-1].known_ms,seq[0].open,
            max(x.high for x in seq),min(x.low for x in seq),
            seq[-1].close,sum((x.volume for x in seq),D(0))))
    return tuple(out)

def four_atr(closed4):
    """14 *fully closed* 4H true ranges use 15 closed H4 bars."""
    if type(closed4) is not tuple or len(closed4)<LOOKBACK+1:
        raise C105Rejected("H4_ATR_WARMUP")
    z=closed4[-LOOKBACK-1:]
    if any(a.close_ms!=b.start_ms for a,b in zip(z,z[1:])):
        raise C105Rejected("H4_ATR_GAP")
    tr=[max(b.h-b.l,abs(b.h-a.c),abs(b.l-a.c))
        for a,b in zip(z,z[1:])]
    v=sum(tr,D(0))/D(len(tr))
    if v<=0:raise C105Rejected("ZERO_4H_ATR")
    return v

def zone_from_three(series,days,weeks):
    """Three *closed* 4H bars; last is at creation, D1/W1 context only as-of."""
    if len(series)!=3:raise C105Rejected("THREE_CLOSED_4H_REQUIRED")
    a,b,c=series
    if a.close_ms!=b.start_ms or b.close_ms!=c.start_ms:
        raise C105Rejected("NONCONSECUTIVE_4H")
    x=_fvg(series)
    if x is None:return None,"NO_4H_FVG"
    side,lo,hi=x
    if not _weekly_daily_context(days,weeks,side,c.close_ms):
        return None,"D1_W1_PARENT_CONTEXT_CONFLICT"
    if not 0<lo<hi:raise C105Rejected("INVALID_4H_FVG")
    return Parent(side,lo,hi,c.close_ms,
        side+":"+str(c.close_ms)+":"+str(lo)+":"+str(hi)),"OK"

def first_touch(zone,candle):
    if zone.state!="WAIT_FIRST_TOUCH" or candle.close_ms<=zone.created_ms:
        return False
    return candle.h>=zone.lower and candle.l<=zone.upper

def rejection(zone,hour):
    if zone.state!="WAIT_1H_REJECTION" or hour.close_ms<=zone.first_touch_ms:
        return False
    touch=hour.h>=zone.lower and hour.l<=zone.upper
    midpoint=(zone.lower+zone.upper)/D(2)
    return bool(touch and ((hour.c>midpoint and hour.c>hour.o) if zone.side=="LONG" else
                           (hour.c<midpoint and hour.c<hour.o)))

def vc(zone,known15):
    if zone.state!="WAIT_15M_VC" or len(known15)<4 or known15[-1].close_ms<=zone.rejection_ms:
        return False
    return bool(_vc(known15[-4:],zone.side))

def parent_plan(zone,entry_ms,entry,closed4,sw4,original3,bar_starts):
    """Compute 4H-only SL and TP from as-of closed H4. No fallback 1H/3m."""
    if type(entry) is not D or entry<=0 or not original3:
        raise C105Rejected("ENTRY_OR_ORIGINAL_MISSING")
    if zone.created_ms>=entry_ms or not closed4 or closed4[-1].close_ms>entry_ms:
        raise C105Rejected("FUTURE_OR_UNCONFIRMED_PARENT_4H")
    if any(v.close_ms>entry_ms for v in closed4):
        raise C105Rejected("FUTURE_4H_BAR")
    atr=four_atr(closed4)
    margin=PAD*atr
    sl=(zone.lower-margin) if zone.side=="LONG" else (zone.upper+margin)
    typ="HIGH" if zone.side=="LONG" else "LOW"
    target_candidates=[]
    for s in sw4:
        if s.tf_ms!=H4 or s.kind!=typ or s.confirmed_ms>entry_ms:
            continue
        if (zone.side=="LONG" and s.price<=entry) or (zone.side=="SHORT" and s.price>=entry):
            continue
        first=bisect_left(bar_starts,s.confirmed_ms)
        last=bisect_left(bar_starts,entry_ms)
        if any((x.high>=s.price if zone.side=="LONG" else x.low<=s.price)
               for x in original3[first:last]):
            continue
        target_candidates.append(s)
    if not target_candidates:return None,"NO_UNCONSUMED_CONFIRMED_4H_FTA"
    fta=(min(target_candidates,key=lambda s:s.price) if zone.side=="LONG" else
         max(target_candidates,key=lambda s:s.price))
    tp=(fta.price-margin) if zone.side=="LONG" else (fta.price+margin)
    if not (sl<entry<tp if zone.side=="LONG" else tp<entry<sl):
        return None,"4H_SL_FTA_WRONG_SIDE"
    risk=abs(entry-sl);rr=abs(tp-entry)/risk
    if not MIN_RISK<=risk/entry<=MAX_RISK:
        return None,"4H_STOP_RISK_BOUNDS"
    if rr<MIN_RR:return None,"DERIVED_4H_RR_BELOW_1_25"
    return {"entry":str(entry),"stop":str(sl),"target":str(tp),
      "fta":str(fta.price),"fta_confirmed_ms":fta.confirmed_ms,
      "fta_pivot_closed_ms":fta.pivot_closed_ms,
      "parent_tf":"4H","stop_source_tf":"4H","target_source_tf":"4H",
      "zone_lower":str(zone.lower),"zone_upper":str(zone.upper),
      "zone_created_ms":zone.created_ms,"parent_id":zone.parent_id,
      "stop_source":"4H_FVG_FAR_EDGE","target_source":"4H_UNCONSUMED_CONFIRMED_PIVOT",
      "pad_source":"ATR_FULLY_CLOSED_4H","atr4h":str(atr),
      "derived_rr":round(float(rr),6),"source_tf":"NATIVE_3M",
      "evidence":EVIDENCE},"OK"

def simulate(rows,idx,side,plan,bps=14):
    if bps not in BPS or type(bps) is not int:raise C105Rejected("UNREGISTERED_FEE")
    if side not in ("LONG","SHORT") or type(rows) is not tuple:
        raise C105Rejected("WRONG_ROUTE")
    if idx<0 or idx>=len(rows) or rows[idx].open!=D(plan["entry"]):
        raise C105Rejected("NEXT_ORIGINAL_NATIVE3M_OPEN_REQUIRED")
    e=D(plan["entry"]);sl=D(plan["stop"]);tp=D(plan["target"])
    if not (sl<e<tp if side=="LONG" else tp<e<sl):
        raise C105Rejected("BROKEN_4H_PARENT_PRICE_GEOMETRY")
    risk=abs(e-sl);last=min(idx+MAX_HOLD,len(rows));reason="";exitprice=None;j=idx
    for j in range(idx,last):
        x=rows[j]
        if j>idx and rows[j-1].known_ms!=x.start_ms:
            raise C105Rejected("ORIGINAL_FUTURE_3M_SOURCE_GAP")
        if side=="LONG":
            if x.open<=sl:exitprice=x.open;reason="STOP_GAP";break
            if x.open>=tp:exitprice=tp;reason="FTA_AT_OPEN";break
            hit_sl=x.low<=sl;hit_tp=x.high>=tp
        else:
            if x.open>=sl:exitprice=x.open;reason="STOP_GAP";break
            if x.open<=tp:exitprice=tp;reason="FTA_AT_OPEN";break
            hit_sl=x.high>=sl;hit_tp=x.low<=tp
        if hit_sl:exitprice=sl;reason="STOP_FIRST_SAME_3M";break
        if hit_tp:exitprice=tp;reason="4H_STRUCTURAL_FTA";break
    if exitprice is None:
        exitprice=rows[j].close;reason="TIME_OUT_48H"
    net=((exitprice-e) if side=="LONG" else (e-exitprice))/risk-D(bps)/D(10000)*e/risk
    return {"entry_ms":rows[idx].start_ms,"exit_ms":rows[j].known_ms,
        "side":side,"exit_reason":reason,
        "net_r":round(float(net),6),**plan,"fee_slip_roundtrip_bps":bps,
        "route":"P4_4H_FVG_1H_REACTION_15M_VC","readiness":"PAPER_ONLY"}
