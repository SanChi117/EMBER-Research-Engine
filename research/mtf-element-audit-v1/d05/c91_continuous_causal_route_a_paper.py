"""C91 full-continuous Binance native5m causal Route-A PAPER research engine.

Never reads C73 preselected P0 contexts to DISCOVER events. Academic text:
Daily POI/liquidity->4H POI/VC->(1H Trigger->15m VC) OR
(1H new VC POI->its first test->15m direct VC OR 15m Trigger->5m VC).
Structural SL = StrongHL proxy/POI border; TP = same-parent 4H/1H FTA,
no fixed RR. All underspecified detectors tagged ADAPTED_HYPOTHESIS.
No author-verified signals, investment advice, or live execution.
"""
from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal as D
import json

from c89_original_native5m_adaptation_backtest import (
    Bar,STEP,SPLIT,COST_BPS,MIN_RISK_PCT,MAX_RISK_PCT,
    SOURCES,load_original_native5m)
from c90_structural_fta_backtest import (
    ClosedBar,Swing,atr5m,ATR_PAD,MIN_RR_FILTER)

class C91Rejected(ValueError): pass
HOUR=12*STEP
H4=4*HOUR
D1=24*HOUR
WEEK=7*D1
WEEK_ANCHOR=4*D1        # Unix Thursday -> Monday
PIVOT_WIDTH=2
MAX_ZONE_AGE=12*H4     # adapted: 48h
MAX_TOUCHED_AGE=8*HOUR # adapted: allowed sequence lifetime
MIN_RR=MIN_RR_FILTER
HOLD=144               # 12h
EVIDENCE="ADAPTED_HYPOTHESIS"
ROUTES=("A_4H_POI_1H_RAID_15M_VC",
        "A_1H_NEW_POI_FIRST_TEST_15M_DIRECT_VC",
        "A_1H_NEW_POI_FIRST_TEST_15M_RAID_5M_VC")

@dataclass(frozen=True)
class OHLC:
    start_ms:int
    close_ms:int
    o:D
    h:D
    l:D
    c:D
    vol:D

@dataclass
class Zone:
    side:str
    lower:D
    upper:D
    created_ms:int
    phase:str="WAIT_FIRST_4H_TEST"
    first_touch_ms:int=0
    phase_ms:int=0
    created_1h_ms:int=0
    child_lower:D=D("0")
    child_upper:D=D("0")
    child_visited:bool=False
    last_outside:bool=True
    child_kind:str=""
    trigger_kind:str=""
    parent_tf:str="4h"
    done:bool=False

def _aggregate(native,tf,anchor=0):
    if type(native) is not tuple or any(type(b) is not Bar for b in native):
        raise C91Rejected("ORIGINAL_TYPED_NATIVE5M_ONLY")
    if tf%STEP or tf<STEP or type(anchor) is not int or anchor%STEP:
        raise C91Rejected("INVALID_TF_ANCHOR")
    out=[];bucket=[];origin=None;last=None
    for b in native:
        if last is not None and b.open_ms!=last+STEP:
            raise C91Rejected("ORIGINAL_SOURCE_GAP")
        last=b.open_ms
        key=(b.open_ms-anchor)//tf
        if origin is not None and key!=origin:
            if len(bucket)==tf//STEP and bucket[0].open_ms%tf==anchor%tf:
                out.append(OHLC(bucket[0].open_ms,bucket[-1].close_ms,
                                bucket[0].o,max(x.h for x in bucket),
                                min(x.l for x in bucket),bucket[-1].c,
                                sum((x.volume for x in bucket),D(0))))
            bucket=[]
        origin=key
        bucket.append(b)
    if len(bucket)==tf//STEP and bucket[0].open_ms%tf==anchor%tf:
        out.append(OHLC(bucket[0].open_ms,bucket[-1].close_ms,
                        bucket[0].o,max(x.h for x in bucket),
                        min(x.l for x in bucket),bucket[-1].c,
                        sum((x.volume for x in bucket),D(0))))
    return tuple(out)

def _fvg(last3):
    if len(last3)!=3:return None
    a,_,c=last3
    if a.close_ms+2*(a.close_ms-a.start_ms)!=c.close_ms:
        raise C91Rejected("FVG_NONCONSECUTIVE")
    if c.l>a.h:return ("LONG",a.h,c.l)
    if c.h<a.l:return ("SHORT",c.h,a.l)
    return None

def _raid(series,side):
    """1h or 15m closed sweep of PREVIOUS 4 closed bars with rejection."""
    if len(series)<5:return False
    b=series[-1];previous=series[-5:-1]
    if side=="LONG":
        low=min(x.l for x in previous)
        return b.l<low and b.c>low and b.c>b.o
    high=max(x.h for x in previous)
    return b.h>high and b.c<high and b.c<b.o

def _vc(series,side):
    """IMB or SNR breakout proxy on fully CLOSED TF."""
    if len(series)<4:return ""
    f=_fvg(series[-3:])
    if f and f[0]==side:return "IMB"
    b=series[-1];prev=series[-2]
    if side=="LONG" and b.c>prev.h and b.c>b.o:return "SNR"
    if side=="SHORT" and b.c<prev.l and b.c<b.o:return "SNR"
    return ""

def _weekly_daily_context(days,weeks,side,signal_ms):
    """D1 and 1W known-at event, neither partial future day nor week."""
    d=[x for x in days if x.close_ms<=signal_ms]
    w=[x for x in weeks if x.close_ms<=signal_ms]
    if len(d)<2 or len(w)<1:return False
    bullish=d[-1].c>=d[-2].c and w[-1].c>=w[-1].o
    bearish=d[-1].c<=d[-2].c and w[-1].c<=w[-1].o
    return bullish if side=="LONG" else bearish

def _structural(source,idx,zone,side,parent_tf,swings1,swings4,swings15):
    """Only previous closed 5m; parent TF FTA from source-confirmed swings."""
    if idx<15:return None,"ATR_NOT_READY"
    b=source[idx]
    atr=atr5m(source[idx-15:idx])
    signal_ms=b.open_ms
    # Swings generated against completed HTF history; only confirmed <= signal.
    sw=swings4 if parent_tf=="4h" else swings1
    target_kind="HIGH" if side=="LONG" else "LOW"
    fta=[]
    for v in sw:
        if v.confirmed_ms>signal_ms or v.kind!=target_kind:continue
        if side=="LONG" and v.price<=source[idx-1].c:continue
        if side=="SHORT" and v.price>=source[idx-1].c:continue
        start=bisect_right([r.open_ms for r in source],v.confirmed_ms-1)
        if any((k.h>=v.price if side=="LONG" else k.l<=v.price)
               for k in source[start:idx]):
            continue
        fta.append(v)
    if not fta:return None,"NO_UNCONSUMED_PARENT_FTA"
    first=(min(fta,key=lambda x:x.price) if side=="LONG" else
           max(fta,key=lambda x:x.price))
    target=first.price-ATR_PAD*atr if side=="LONG" else first.price+ATR_PAD*atr
    prior15=[s for s in swings15 if s.confirmed_ms<=signal_ms and
             s.kind==("LOW" if side=="LONG" else "HIGH") and
             (s.price<source[idx-1].c if side=="LONG" else s.price>source[idx-1].c)]
    if not prior15:return None,"NO_CONFIRMED_STRONGHL"
    strong=max(prior15,key=lambda x:x.confirmed_ms)
    low=zone.child_lower if parent_tf=="1h" else zone.lower
    high=zone.child_upper if parent_tf=="1h" else zone.upper
    edge=min(low,strong.price) if side=="LONG" else max(high,strong.price)
    stop=edge-ATR_PAD*atr if side=="LONG" else edge+ATR_PAD*atr
    # FTA / SL identified BEFORE subsequent next-open entry; immutable.
    if not ((stop<source[idx-1].c<target) if side=="LONG"
            else (target<source[idx-1].c<stop)):
        return None,"STRUCTURE_WRONG_SIDE_AT_SIGNAL"
    return {"stop":stop,"target":target,"fta":first.price,
       "fta_tf":parent_tf,"fta_confirmed_ms":first.confirmed_ms,
       "stronghl":strong.price,"stronghl_confirmed_ms":strong.confirmed_ms,
       "signal_close":source[idx-1].c,
       "signal_ms":signal_ms,"atr":atr},"OK"

def _simulate(source,idx,side,struct,cost_bps=14):
    if cost_bps not in COST_BPS or type(cost_bps) is not int:
        raise C91Rejected("COST_UNSUPPORTED")
    if idx>=len(source):return None,"NO_NEXT_OPEN"
    entry=source[idx].o;stop=struct["stop"];target=struct["target"]
    if not (stop<entry<target if side=="LONG" else target<entry<stop):
        return None,"GAP_DESTROYS_STRUCTURAL_PLAN"
    risk=abs(entry-stop)
    if not MIN_RISK_PCT<=risk/entry<=MAX_RISK_PCT:
        return None,"STRUCTURAL_STOP_RISK_BOUNDS"
    rr=abs(target-entry)/risk
    if rr<MIN_RR:return None,"DERIVED_RR_FILTER"
    last=min(idx+HOLD,len(source))
    if last==idx:return None,"NO_FORWARD_CANDLES"
    exit_price=None;reason="";j=idx
    for j in range(idx,last):
        bar=source[j]
        if j>idx and bar.open_ms!=source[j-1].close_ms:
            raise C91Rejected("FUTURE_NATIVE5M_GAP")
        if side=="LONG":
            if bar.o<=stop:exit_price=bar.o;reason="STOP_GAP";break
            if bar.o>=target:exit_price=target;reason="FTA_OPEN";break
            hit_sl=bar.l<=stop;hit_tp=bar.h>=target
        else:
            if bar.o>=stop:exit_price=bar.o;reason="STOP_GAP";break
            if bar.o<=target:exit_price=target;reason="FTA_OPEN";break
            hit_sl=bar.h>=stop;hit_tp=bar.l<=target
        if hit_sl:exit_price=stop;reason="STOP_FIRST_AMBIGUOUS";break
        if hit_tp:exit_price=target;reason="STRUCTURAL_FTA";break
    if exit_price is None:
        exit_price=source[j].c;reason="TIME_OUT"
    net=((exit_price-entry) if side=="LONG" else (entry-exit_price))/risk
    net-=D(cost_bps)/D(10000)*entry/risk
    return {"entry_ms":source[idx].open_ms,"exit_ms":source[j].close_ms,
            "entry":str(entry),"stop":str(stop),"target":str(target),
            "fta":str(struct["fta"]),"fta_tf":struct["fta_tf"],
            "derived_rr":round(float(rr),6),
            "net_r":round(float(net),6),"exit_reason":reason,
            "fee_slip_roundtrip_bps":cost_bps,
            "evidence":EVIDENCE}, "OK"

def discover_symbol(source,symbol):
    """Evaluate each bar causally, independent of C73/P0 lookups."""
    if symbol not in SOURCES or len(source)<500 or type(source) is not tuple:
        raise C91Rejected("MARKET_TOO_SHORT_OR_UNKNOWN")
    if any(type(x) is not Bar for x in source) or any(
            a.close_ms!=b.open_ms for a,b in zip(source,source[1:])):
        raise C91Rejected("NATIVE5M_PROVENANCE_OR_GAP")
    fifteen=_aggregate(source,15*60*1000)
    hour=_aggregate(source,HOUR)
    four=_aggregate(source,H4)
    days=_aggregate(source,D1)
    weeks=_aggregate(source,WEEK,WEEK_ANCHOR)
    # Static detected extrema are hidden until fully confirmed in the live loop.
    def sw(arr,tf):
        out=[]
        for k in range(PIVOT_WIDTH,len(arr)-PIVOT_WIDTH):
            mid=arr[k]
            before=arr[k-PIVOT_WIDTH:k]
            after=arr[k+1:k+PIVOT_WIDTH+1]
            confirmed=after[-1].close_ms
            if all(mid.h>x.h for x in before) and all(mid.h>=x.h for x in after):
                out.append(Swing(tf,"HIGH",mid.h,mid.close_ms,confirmed,PIVOT_WIDTH))
            if all(mid.l<x.l for x in before) and all(mid.l<=x.l for x in after):
                out.append(Swing(tf,"LOW",mid.l,mid.close_ms,confirmed,PIVOT_WIDTH))
        return tuple(out)
    s15=sw(fifteen,15*60*1000)
    s1=sw(hour,HOUR)
    s4=sw(four,H4)  # C90 confirms same proxy semantics
    fvg4={b.close_ms:_fvg(four[k-2:k+1]) for k,b in enumerate(four) if k>=2}
    h1_by_close={x.close_ms:k for k,x in enumerate(hour)}
    m15_by_close={x.close_ms:k for k,x in enumerate(fifteen)}
    fvg1={x.close_ms:_fvg(hour[k-2:k+1]) for k,x in enumerate(hour) if k>=2}
    zones=[];emitted=[];rejects=Counter();source_events=Counter()
    last_exited=source[0].open_ms
    for idx in range(1,len(source)-1):
        b=source[idx]
        now=b.close_ms
        if now in fvg4 and fvg4[now]:
            side,low,high=fvg4[now]
            if _weekly_daily_context(days,weeks,side,now):
                zones.append(Zone(side,low,high,now))
                source_events["4H_PARENT_FVG_CREATED"]+=1
            else:rejects["D1_W1_CONTEXT_NOT_ALIGNED"]+=1
        m1=hour[h1_by_close[now]-4:h1_by_close[now]+1] if now in h1_by_close and h1_by_close[now]>=4 else ()
        m15=fifteen[m15_by_close[now]-3:m15_by_close[now]+1] if now in m15_by_close and m15_by_close[now]>=3 else ()
        for z in zones:
            if z.done or now<=z.created_ms:continue
            if now-z.created_ms>MAX_ZONE_AGE or (z.first_touch_ms and now-z.first_touch_ms>MAX_TOUCHED_AGE):
                z.done=True;rejects["ZONE_EXPIRED"]+=1;continue
            if (z.side=="LONG" and b.c<z.lower or z.side=="SHORT" and b.c>z.upper):
                z.done=True;rejects["POI_INVALIDATED_ON_5M_CLOSE"]+=1;continue
            touch=b.h>=z.lower and b.l<=z.upper
            if z.phase=="WAIT_FIRST_4H_TEST":
                if touch:
                    z.phase="WAIT_1H_BRANCH";z.first_touch_ms=now;z.phase_ms=now
                    source_events["4H_FIRST_PHYSICAL_TEST"]+=1
                continue
            if z.phase=="WAIT_1H_BRANCH":
                if m1 and _raid(m1,z.side) and now>z.first_touch_ms:
                    z.phase="WAIT_15M_VC";z.phase_ms=now;z.trigger_kind="1H_LIQUIDITY_RAID"
                    source_events["1H_RAID_TRIGGER"]+=1
                elif now in fvg1 and fvg1[now] and fvg1[now][0]==z.side and now>z.first_touch_ms:
                    _,low,high=fvg1[now]
                    # nested 4h IMB->1h IMB is NOT author approved. Reject.
                    if (low>=z.lower and high<=z.upper):
                        rejects["NESTED_4H_IMB_1H_IMB_VETO"]+=1
                        continue
                    z.child_lower=low;z.child_upper=high;z.created_1h_ms=now
                    z.phase="WAIT_1H_FIRST_TEST";z.phase_ms=now
                    source_events["1H_CHILD_NEW_IMB"]+=1
                continue
            if z.phase=="WAIT_1H_FIRST_TEST":
                child_touch=b.h>=z.child_lower and b.l<=z.child_upper
                if child_touch and now>z.created_1h_ms:
                    if z.child_visited:
                        z.done=True;rejects["SECOND_CHILD_VISIT"]+=1;continue
                    if z.last_outside:
                        z.child_visited=True;z.phase="WAIT_15M_CHILD_BRANCH";z.phase_ms=now
                        source_events["1H_CHILD_FIRST_PHYSICAL_TEST"]+=1
                z.last_outside=not child_touch
                continue
            candidate=None;parent="4h"
            if z.phase=="WAIT_15M_VC" and m15 and now>z.phase_ms and _vc(m15,z.side):
                candidate=ROUTES[0]
            if z.phase=="WAIT_15M_CHILD_BRANCH":
                parent="1h"
                if m15 and now>z.phase_ms:
                    if _raid(m15,z.side):
                        z.phase="WAIT_5M_VC";z.phase_ms=now
                        source_events["15M_RAID_TRIGGER"]+=1
                    elif _vc(m15,z.side):
                        candidate=ROUTES[1]
            if z.phase=="WAIT_5M_VC" and now>z.phase_ms:
                # 5m FVG or SNR confirmation; no unreconciled 1H-child nested pattern.
                m5=tuple(OHLC(x.open_ms,x.close_ms,x.o,x.h,x.l,x.c,x.volume)
                         for x in source[max(0,idx-3):idx+1])
                if _vc(m5,z.side):candidate=ROUTES[2];parent="1h"
            if candidate is None:continue
            source_events["TECHNICAL_CLOSED_VC"]+=1
            # One structural candidate per zone; no optional fitted RR target.
            struct,why=_structural(source,idx+1,z,z.side,parent,s1,s4,s15)
            z.done=True
            if struct is None:rejects[why]+=1;continue
            outcome,why=_simulate(source,idx+1,z.side,struct)
            if outcome is None:rejects[why]+=1;continue
            if outcome["entry_ms"]<last_exited:
                rejects["OVERLAPPING_POSITION_SYMBOL"]+=1;continue
            outcome.update({"symbol":symbol,"route":candidate,
                            "context":"ADAPTED_D1_W1_4H",
                            "poi_created_ms":z.created_ms,
                            "poi_first_test_ms":z.first_touch_ms,
                            "trigger_close_ms":z.phase_ms,
                            "vc_close_ms":now,
                            "fta_confirmed_ms":struct["fta_confirmed_ms"],
                            "stronghl_confirmed_ms":struct["stronghl_confirmed_ms"],
                            "readiness":"PAPER_ONLY"})
            if not (outcome["poi_created_ms"]<outcome["poi_first_test_ms"]<
                outcome["vc_close_ms"]==outcome["entry_ms"]):
                raise C91Rejected("INTERNAL_LOOKAHEAD_OR_ROUTE_ORDER")
            emitted.append(outcome)
            last_exited=outcome["exit_ms"]
            source_events["PAPER_RESEARCH_CLOSED"]+=1
        zones=[z for z in zones if not z.done]
    return {"symbol":symbol,"native5m_bars":len(source),"completed_tf_bars":{
       "15m":len(fifteen),"1h":len(hour),"4h":len(four),
       "1d":len(days),"1w":len(weeks)},
       "zones":dict(sorted(source_events.items())),"rejections":dict(sorted(rejects.items())),
       "trades":emitted}

def _metrics(rows):
    v=[t["net_r"] for t in rows]
    wins=sum(x>0 for x in v);gain=sum(max(0,x) for x in v)
    loss=-sum(min(0,x) for x in v)
    # net R is not equity return; per-trade risk scaling required for DD.
    equity=D(100);peak=equity;dd=D(0)
    for x in rows:
        equity+=D(str(x["net_r"]))
        peak=max(peak,equity)
        if peak:dd=max(dd,(peak-equity)/peak*100)
    return {"count":len(v),"total_net_r":round(sum(v),6),
       "avg_net_r":round(sum(v)/len(v),6) if v else None,
       "win_rate_pct":round(100*wins/len(v),3) if v else None,
       "profit_factor":round(gain/loss,5) if loss else None,
       "max_drawdown_units_for_1R_equals_1_equity_unit_pct":round(float(dd),5),
       "baseline_equity_units":100}

def analyze(markets,manifest):
    if set(markets)!=SOURCES or len(manifest) not in (15,40):
        raise C91Rejected("ORIGINAL_5_SYMBOLS_15_OR_40_ARCHIVES_REQUIRED")
    all_results={sym:discover_symbol(markets[sym],sym) for sym in sorted(markets)}
    flat=sorted((t for x in all_results.values() for t in x["trades"]),
                key=lambda t:(t["entry_ms"],t["symbol"]))
    # Already predetermined 2026-09-20, no strategy optimization based on late.
    train=[x for x in flat if x["entry_ms"]<SPLIT and x["exit_ms"]<=SPLIT]
    purged=[x for x in flat if x["entry_ms"]<SPLIT<x["exit_ms"]]
    test=[x for x in flat if x["entry_ms"]>=SPLIT]
    return {"schema":"EMBER_C91_UNSELECTED_CAUSAL_ROUTE_A_NATIVE5M_PAPER",
        "academic_scope":"Route A ONLY; isolated B IDM and C Raid-BOS NOT CLAIMED IMPLEMENTED",
        "rule_status":EVIDENCE,
        "source_selection":"ALL_CONTINUOUS_NATIVE5M_NO_C73_P0_EVENT_SELECTION",
        "source_market":("BINANCE_USDM_15_SHA_FROZEN_ZIP" if len(manifest)==15 else "BINANCE_USDM_ORIGINAL_FULL_CALENDAR_ARCHIVES_WITH_PROVENANCE"),
        "archives":manifest,
        "source_bars":sum(len(x) for x in markets.values()),
        "fixed_rr_targets":False,
        "structural_target":"nearest eligible unconsumed parent 4H/1H swing FTA",
        "structural_stop":"last confirmed 15m StrongHL proxy plus 4H/1H POI edge",
        "split_ms":SPLIT,
        "split_note":"time holdout only; same source period informed prior model work and NOT pristine untouched OOS",
        "baseline_train":_metrics(train),"held_out_time":_metrics(test),
        "embargo_crossing_split":len(purged),
        "all":_metrics(flat),"by_symbol":all_results,
        "route_counts":dict(sorted(Counter(t["route"] for t in flat).items())),
        "orders":[],"fills":[],"live_trades":[],"readiness":"PAPER_RESEARCH_NOT_TRADE_READY"}
def dumps(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
