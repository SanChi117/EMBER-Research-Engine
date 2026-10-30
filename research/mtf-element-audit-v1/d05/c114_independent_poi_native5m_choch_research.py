#!/usr/bin/env python3
"""C114: distinct 4H POI first-touch -> original native5m CHoCH observational test.

Frozen before source read; no C109 market entry conditions. No live orders.
Comparisons are observational, NEVER causal identification by fiat.
"""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
import hashlib, json, random
from pathlib import Path

import c104_native3m_source as provider3
import c114_original_native5m_daily_source as provider5
import c105_parent4h_structural_geometry as p4
import c93_native3m_raid_bos_route_c_research as swings
import c113_final_execution_geometry_research as prior
from c91_continuous_causal_route_a_paper import _fvg

class C114Error(ValueError): pass
SYMBOLS = ("BNBUSDT","XLMUSDT","HBARUSDT","INJUSDT","OPUSDT","ALGOUSDT",
           "CHZUSDT","ICPUSDT","SEIUSDT","PENDLEUSDT","LINKUSDT","UNIUSDT")
WINDOWS = (
    ("WIN_A", datetime(2025,1,1,tzinfo=timezone.utc), datetime(2025,2,26,tzinfo=timezone.utc)),
    ("WIN_B", datetime(2026,2,1,tzinfo=timezone.utc), datetime(2026,3,29,tzinfo=timezone.utc)),
)
DAY=p4.D1
H=p4.H
THREE=180000
FIVE=300000
LANDMARK=6*H
AGE=48*H
HOLD=48*H
WARMUP=7*DAY
END_EMBARGO=HOLD+LANDMARK
REPS=2000
BOOT_SEED=11420261030
BPS=(14,25,40)
EXPECTED_3M_ZIPS=1344
EXPECTED_5M_ZIPS=1344
EXPECTED_3M_BARS=645120
EXPECTED_5M_BARS=387072
PRECOMMIT="cycles/B1_C114_PRECOMMIT_INDEPENDENT_4H_POI_5M_REACTION_PREDICTIVE_VALUE_RU.md"

def frozen():
    if len(SYMBOLS)!=12 or len(set(SYMBOLS))!=12:
        raise C114Error("CHANGED_UNIVERSE")
    if any((e-b).days!=56 for _,b,e in WINDOWS):
        raise C114Error("CHANGED_WINDOWS")
    if BOOT_SEED!=11420261030 or REPS!=2000 or LANDMARK!=6*H:
        raise C114Error("MUTATED_STATISTICS_OR_LANDMARK")
    prior.frozen()
    return True

def dates(begin,end):
    return tuple((begin+timedelta(days=i)).strftime("%Y-%m-%d")
                 for i in range((end-begin).days))

def download(window):
    """All native3m & native5m archives (with distinct original SHA sources)."""
    _,begin,end=window
    days=dates(begin,end)
    oldsyms,olddays=provider3.SYMBOLS,provider3.DAYS
    work=[(s,d) for s in SYMBOLS for d in days]
    try:
        provider3.SYMBOLS,provider3.DAYS=SYMBOLS,days
        def task(k):
            s,d=k
            a,m=provider3.daily(s,d)
            b,n=provider5.daily(s,d)
            return s,d,a,m,b,n
        with ThreadPoolExecutor(max_workers=12) as pool:
            data=list(pool.map(task,work))
    finally:
        provider3.SYMBOLS,provider3.DAYS=oldsyms,olddays
    m3={s:[] for s in SYMBOLS}
    m5={s:[] for s in SYMBOLS}
    receipts3,receipts5=[],[]
    for s,d,a,ma,b,mb in data:
        if (len(a)!=480 or len(b)!=288 or
            ma["symbol"]!=s or ma["date"]!=d or
            mb["symbol"]!=s or mb["date"]!=d or
            ma["bars"]!=480 or mb["bars"]!=288):
            raise C114Error("MISSING_UNTRUSTED_DAILY_PROVIDER")
        if m3[s] and m3[s][-1].known_ms!=a[0].start_ms:
            raise C114Error("NATIVE3M_DAY_GAP")
        if m5[s] and m5[s][-1].close_ms!=b[0].open_ms:
            raise C114Error("NATIVE5M_DAY_GAP")
        m3[s].extend(a);m5[s].extend(b)
        receipts3.append(ma);receipts5.append(mb)
    if len(receipts3)!=672 or len(receipts5)!=672:
        raise C114Error("ORIGINAL_SOURCE_INCOMPLETE")
    lo=int(begin.timestamp()*1000);hi=int(end.timestamp()*1000)
    parity_evidence={}
    for s in SYMBOLS:
        a,b=m3[s],m5[s]
        if (len(a)!=56*480 or len(b)!=56*288 or
            a[0].start_ms!=lo or a[-1].known_ms!=hi or
            b[0].open_ms!=lo or b[-1].close_ms!=hi):
            raise C114Error("INCOMPLETE_NATIVE_3M_OR_5M")
        parity_evidence[s]=independent_15m_parity(tuple(a),tuple(b))
    if (len({(x["symbol"],x["date"]) for x in receipts3})!=672 or
        len({(x["symbol"],x["date"]) for x in receipts5})!=672):
        raise C114Error("DUPLICATE_PROVIDER_DAY")
    return {s:tuple(m3[s]) for s in SYMBOLS}, {s:tuple(m5[s]) for s in SYMBOLS}, receipts3,receipts5,parity_evidence

def independent_15m_parity(threes,fives):
    """Strict original 15m OHLC parity, report bounded decimal volume drift."""
    if len(threes)//5!=len(fives)//3:
        raise C114Error("PARITY_15M_BAR_COUNT")
    nonidentical=0
    max_relative=D(0)
    for j in range(len(threes)//5):
        a=threes[5*j:5*j+5];b=fives[3*j:3*j+3]
        lhs=(a[0].start_ms,a[-1].known_ms,a[0].open,
             max(x.high for x in a),min(x.low for x in a),a[-1].close)
        rhs=(b[0].open_ms,b[-1].close_ms,b[0].o,
             max(x.h for x in b),min(x.l for x in b),b[-1].c)
        if lhs!=rhs:
            raise C114Error("ORIGINAL_3M_5M_OHLC_MISMATCH_AT_15M_"+
                            str(j)+"_3m="+str(lhs)+"_5m="+str(rhs))
        av=sum((x.volume for x in a),D(0))
        bv=sum((x.volume for x in b),D(0))
        if av!=bv:
            diff=abs(av-bv)
            relative=diff/max(av,bv) if max(av,bv)>0 else D(0)
            if relative>D("0.0001"):
                raise C114Error("ORIGINAL_3M_5M_VOLUME_DRIFT_GT_1BP_AT_15M_"+
                                str(j)+"_3m="+str(av)+"_5m="+str(bv)+
                                "_relative="+str(relative))
            nonidentical+=1
            max_relative=max(max_relative,relative)
    return {"aligned15m":len(threes)//5,
            "bounded_volume_nonidentical_buckets":nonidentical,
            "max_relative_15m_volume_drift":str(max_relative),
            "strict_ohlc_price_clock_parity":True,
            "volume_tolerance_relative":"0.0001"}

def range_class(pivots,asof,price,side):
    xs=[s for s in pivots if s.confirmed_ms<=asof]
    recent={}
    for s in xs:
        recent[s.kind]=s
    if set(recent)!={"HIGH","LOW"}:
        return "NO_RANGE",None
    hi,lo=recent["HIGH"].price,recent["LOW"].price
    if hi<=lo:return "NO_RANGE",None
    mid=(hi+lo)/D(2)
    state="DISCOUNT" if price<mid else "PREMIUM" if price>mid else "MIDPOINT"
    return state,{"top":str(hi),"bottom":str(lo),"mid":str(mid),
                  "high_confirmed_ms":recent["HIGH"].confirmed_ms,
                  "low_confirmed_ms":recent["LOW"].confirmed_ms}

def day_direction(pivots,asof):
    z={kind:[p for p in pivots if p.kind==kind and p.confirmed_ms<=asof][-2:]
       for kind in ("HIGH","LOW")}
    if any(len(q)<2 for q in z.values()):return "D1_UNKNOWN"
    h,l=z["HIGH"],z["LOW"]
    if h[-1].price>h[-2].price and l[-1].price>l[-2].price:return "D1_HH_HL"
    if h[-1].price<h[-2].price and l[-1].price<l[-2].price:return "D1_LH_LL"
    return "D1_MIXED"

def five_pre_touch_structure(pivots,asof,side):
    hi=[s for s in pivots if s.kind=="HIGH" and s.confirmed_ms<=asof]
    lo=[s for s in pivots if s.kind=="LOW" and s.confirmed_ms<=asof]
    if len(hi)<2 or len(lo)<2:
        return None
    if side=="LONG":
        okay=hi[-2].price>hi[-1].price and lo[-2].price>lo[-1].price
        return hi[-1] if okay else None
    if side=="SHORT":
        okay=hi[-2].price<hi[-1].price and lo[-2].price<lo[-1].price
        return lo[-1] if okay else None
    raise C114Error("BAD_PARENT_SIDE")

def choch_after_t0(fives,starts5,sw5,t0,side):
    level=five_pre_touch_structure(sw5,t0,side)
    if level is None:return None,"NO_CHoCH_STRUCTURAL_SOURCE"
    lastclosed_idx=bisect_right(starts5,t0)-1
    if lastclosed_idx<0:return None,"NO_NATIVE5M_WARMUP"
    # A bar starting before t0 is not available until its full close.
    lastclosed_idx=bisect_right(starts5,t0-FIVE)-1
    if lastclosed_idx<0:return None,"NO_NATIVE5M_ASOF"
    prev=fives[lastclosed_idx]
    if prev.close_ms>t0 or level.confirmed_ms>t0:
        raise C114Error("FUTURE_5M_SWING")
    boundary=t0+LANDMARK
    for i in range(lastclosed_idx+1,len(fives)):
        bar=fives[i]
        if bar.close_ms>boundary:break
        if bar.open_ms<t0:
            # An original 5m bar that straddles the 3m first touch cannot
            # establish a fully post-touch structure break.
            prev=bar
            continue
        bullish=(side=="LONG" and prev.c<=level.price<bar.c and bar.c>bar.o)
        bearish=(side=="SHORT" and prev.c>=level.price>bar.c and bar.c<bar.o)
        if bullish or bearish:
            return {
                "breach_level":str(level.price),
                "breach_known_ms":bar.close_ms,
                "swing_confirmed_ms":level.confirmed_ms,
                "swing_pivot_closed_ms":level.pivot_closed_ms,
                "crossing_close":str(bar.c),
                "candle_5m_open_ms":bar.open_ms,
                "kind":"NATIVE5M_2L2R_STRUCTURAL_CLOSE_CHOCH"
            },"CONFIRMED"
        prev=bar
    return None,"NO_DIRECTIONAL_CONFIRMED_CROSS"

def touch_candidate(z,bar,prev4,now):
    if not(z.created_ms<bar.known_ms<=z.created_ms+AGE):
        return False
    if any((p.c<z.lower if z.side=="LONG" else p.c>z.upper)
           for p in prev4 if z.created_ms<p.close_ms<=bar.start_ms):
        return False
    return bar.high>=z.lower and bar.low<=z.upper

def early_competing(t0,landmark,bar0,rows,starts3,z,closed4,sw4,all_four):
    """ITTs retain early hits and do not condition treatment eligibility on survival."""
    atr=p4.four_atr(closed4)
    stop=(z.lower-p4.PAD*atr if z.side=="LONG" else z.upper+p4.PAD*atr)
    candidate,_=p4.parent_plan(z,t0,bar0.close,closed4,sw4,rows,starts3)
    target=D(candidate["target"]) if candidate is not None else None
    i=bisect_left(starts3,t0)
    j=bisect_left(starts3,landmark)
    for row in rows[i:j]:
        if z.side=="LONG":
            if row.low<=stop:return {"status":"EARLY_COMPETING_STOP","known_ms":row.known_ms}
            if target is not None and row.high>=target:return {"status":"EARLY_COMPETING_TP","known_ms":row.known_ms}
        else:
            if row.high>=stop:return {"status":"EARLY_COMPETING_STOP","known_ms":row.known_ms}
            if target is not None and row.low<=target:return {"status":"EARLY_COMPETING_TP","known_ms":row.known_ms}
    if any((b.c<z.lower if z.side=="LONG" else b.c>z.upper)
           for b in all_four if t0<b.close_ms<=landmark):
        return {"status":"EARLY_COMPETING_PARENT_4H_INVALIDATION",
                "known_ms":landmark}
    return {"status":"SURVIVED_6H_LANDMARK",
            "known_ms":landmark,
            "early_frozen_target_available":target is not None}

def execution(z,t0,landmark,rows,starts3,four,closed4ms,sw4):
    j=bisect_left(starts3,landmark)
    if j>=len(rows) or rows[j].start_ms!=landmark:
        raise C114Error("NATIVE3M_LANDMARK_NOT_ALIGNED")
    n4=bisect_right(closed4ms,landmark)
    closed4=four[:n4]
    plan,reason=p4.parent_plan(z,landmark,rows[j].open,closed4,sw4,rows,starts3)
    if plan is None:
        return None,reason
    trade=p4.simulate(rows,j,z.side,plan,bps=14)
    if trade["exit_ms"]>rows[-1].known_ms:
        raise C114Error("CENSORED_48H")
    if not (trade["parent_tf"]==trade["stop_source_tf"]==trade["target_source_tf"]=="4H"):
        raise C114Error("LOW_TF_EXIT_LEAK")
    return trade,"FILLED"

def risk_bin(trade):
    if trade is None:return "UNADMITTED"
    entry,stop,tar=map(D,(trade["entry"],trade["stop"],trade["target"]))
    p=abs(entry-stop)/entry
    if D("0.002")<=p<D(".01"): a="RISK_0_2_TO_1"
    elif D(".01")<=p<D(".03"):a="RISK_1_TO_3"
    elif D(".03")<=p<=D(".10"):a="RISK_3_TO_10"
    else:raise C114Error("RISK_OUTSIDE_PRECOMMITTED_BINS")
    rr=abs(tar-entry)/abs(entry-stop)
    reward="REWARD_1_25_TO_2" if rr<2 else "REWARD_2_TO_4" if rr<4 else "REWARD_GE_4"
    return a+"_"+reward

def first_zone_target(four,asof,side,reference):
    # Secondary observation only: nearest *preknown opposing* 4H FVG edge;
    # never used as alternative TP.
    others=[]
    for i in range(2,len(four)):
        if four[i].close_ms>asof:break
        z=_fvg(four[i-2:i+1])
        if z is None:continue
        d,low,high=z
        if d==side:continue
        edge=low if side=="LONG" else high
        if (edge>reference if side=="LONG" else edge<reference):
            others.append((edge,four[i].close_ms))
    if not others:return None
    e,t=(min(others,key=lambda v:v[0]) if side=="LONG"
         else max(others,key=lambda v:v[0]))
    return {"edge":str(e),"zone_created_ms":t}

def per_symbol(three,five,symbol,window):
    if type(three) is not tuple or type(five) is not tuple:
        raise C114Error("SOURCE_TUPLE_REQUIRED")
    _,begin,end=window
    begin_ms=int(begin.timestamp()*1000)
    end_ms=int(end.timestamp()*1000)
    t0_min=begin_ms+WARMUP
    t0_max=end_ms-END_EMBARGO
    starts3=[x.start_ms for x in three]
    starts5=[x.open_ms for x in five]
    four=p4.aggregate(three,p4.H4)
    daily=p4.aggregate(three,p4.D1)
    sw4=swings._confirmed(four,p4.H4,end_ms)
    sw5=swings._confirmed(five,FIVE,end_ms)
    sw1d=swings._confirmed(daily,p4.D1,end_ms)
    closed4ms=[x.close_ms for x in four]
    zones=[]
    for j in range(2,len(four)):
        v=_fvg(four[j-2:j+1])
        if v is None:continue
        side,low,high=v
        if not 0<low<high:raise C114Error("PARENT_FVG_INVALID")
        z=p4.Parent(side,low,high,four[j].close_ms,
                    side+":"+str(four[j].close_ms)+":"+str(low)+":"+str(high))
        zones.append(z)
    # Stop tracking parent after its first 3m wick touch; parent identity
    # is independent of all exit and confirmation filters.
    ledger=[]
    all_touches=Counter()
    for z in zones:
        if z.created_ms+AGE < t0_min:continue
        a=bisect_left(starts3,z.created_ms)
        b=bisect_left(starts3,z.created_ms+AGE)
        touched=None
        for k in range(a,b+1):
            if k>=len(three):break
            bar=three[k]
            n4=bisect_right(closed4ms,bar.start_ms)
            if not touch_candidate(z,bar,four[:n4],bar.start_ms):
                continue
            touched=(k,bar)
            break
        if touched is None:
            all_touches["NO_4H_FIRST_TOUCH_WITHIN_48H"]+=1
            continue
        k,bar=touched
        t0=bar.known_ms
        all_touches["4H_FIRST_PHYSICAL_TOUCH"]+=1
        if not t0_min<=t0<t0_max:
            all_touches["WARMUP_OR_TERMINAL_EMBARGO"]+=1
            continue
        landmark=t0+LANDMARK
        i4=bisect_right(closed4ms,t0)
        prior4=four[:i4]
        if len(prior4)<15:raise C114Error("MISSING_H4_SOURCE_WARMUP")
        rc,range_info=range_class(sw4,t0,bar.close,z.side)
        dd=day_direction(sw1d,t0)
        confirm,status=choch_after_t0(five,starts5,sw5,t0,z.side)
        early=early_competing(t0,landmark,bar,three,starts3,z,prior4,sw4,four)
        trade,why=(execution(z,t0,landmark,three,starts3,four,closed4ms,sw4)
                   if early["status"]=="SURVIVED_6H_LANDMARK"
                   else (None,"EARLY_COMPETING_EVENT"))
        target2=(first_zone_target(four,landmark,z.side,D(trade["entry"]))
                 if trade is not None else None)
        e={
            "symbol":symbol,"parent_id":z.parent_id,"side":z.side,
            "parent_created_ms":z.created_ms,"parent_low":str(z.lower),
            "parent_high":str(z.upper),"t0_touch_known_ms":t0,
            "landmark_ms":landmark,"range_class":rc,"range_info":range_info,
            "d1_structure":dd,"five_pre_touch_has_structure":
                five_pre_touch_structure(sw5,t0,z.side) is not None,
            "treatment":"T_CHoCH" if confirm else "C_NO_CHoCH",
            "choch":confirm,"choch_status":status,"early":early,
            "status":why,"risk_bin":risk_bin(trade),
            "matched_id":None,"trade":trade,"next_opposite_4h_fvg":target2,
        }
        # The raw first-touch cohort stays intact, including early losses and
        # no source or inadmissible geometry. No profitable survivors-only framing.
        ledger.append(e)
    return {"symbol":symbol, "source_bars_native3m":len(three),
            "source_bars_native5m":len(five),
            "all_fvg_parents":len(zones),
            "touch_counters":dict(all_touches), "events":ledger}

def key(e):
    return (e["symbol"],
            datetime.fromtimestamp(e["t0_touch_known_ms"]/1000,timezone.utc).strftime("%Y-%m"),
            e["side"],e["range_class"],e["risk_bin"])

def match_events(events):
    # Matching uses ONLY source-known at landmark variables and never exit/PnL.
    controls=defaultdict(list)
    for e in events:
        if e["treatment"]=="C_NO_CHoCH" and e["trade"] is not None:
            controls[key(e)].append(e)
    for v in controls.values():
        v.sort(key=lambda e:(e["t0_touch_known_ms"],e["parent_id"]))
    pairs=[];used=set()
    treatment=sorted((e for e in events if e["treatment"]=="T_CHoCH"),
                     key=lambda x:(x["t0_touch_known_ms"],x["parent_id"]))
    for t in treatment:
        if t["trade"] is None:continue
        bucket=controls[key(t)]
        c=next((x for x in bucket if x["parent_id"] not in used),None)
        if c is None:continue
        used.add(c["parent_id"])
        ident=f"{t['symbol']}:{t['t0_touch_known_ms']}:{t['parent_id']}->{c['parent_id']}"
        t["matched_id"]=ident;c["matched_id"]=ident
        pairs.append({"id":ident,"symbol":t["symbol"],
                      "t0":t["t0_touch_known_ms"],"t":t,"c":c})
    return pairs

def net_r(t,bps):
    if t is None:return 0.0
    e,stop=map(D,(t["entry"],t["stop"]))
    net=D(str(t["net_r"]))-D(bps-14)/D(10000)*e/abs(e-stop)
    return float(net)

def score(events,bps):
    # Include no-trades as zero outcomes in denominator, never PF manipulation.
    trades=[e["trade"] for e in events if e["trade"] is not None]
    vals=[net_r(t,bps) for t in trades]
    pos=sum(v for v in vals if v>0)
    loss=-sum(v for v in vals if v<0)
    tp=sum(t["exit_reason"] in ("4H_STRUCTURAL_FTA","FTA_AT_OPEN") for t in trades)
    stop=sum("STOP" in t["exit_reason"] for t in trades)
    return {"signals":len(events),"fills":len(trades),
            "net_total_r":round(sum(vals),6),
            "mean_r_per_itt_event":round(sum(vals)/len(events),6) if events else None,
            "mean_r_per_fill":round(sum(vals)/len(trades),6) if trades else None,
            "pf":round(pos/loss,6) if loss else None,
            "tp_before_sl_n":tp,"sl_first_n":stop,
            "tp_probability_filled":round(tp/len(trades),6) if trades else None}

def boot_delta(pairs,seed=BOOT_SEED,reps=REPS):
    if not pairs:return {"n_blocks":0,"low95":None,"mean":None}
    blocks=defaultdict(list)
    for p in pairs:
        when=datetime.fromtimestamp(p["t0"]/1000,timezone.utc)
        iso=when.isocalendar()
        block=(p["symbol"],iso.year,iso.week)
        blocks[block].append(net_r(p["t"]["trade"],25)-net_r(p["c"]["trade"],25))
    keys=sorted(blocks)
    rng=random.Random(seed)
    means=[]
    for _ in range(reps):
        picks=[keys[rng.randrange(len(keys))] for j in range(len(keys))]
        values=[v for k in picks for v in blocks[k]]
        means.append(sum(values)/len(values))
    means.sort()
    return {"n_blocks":len(keys),"bootstrap_reps":reps,"seed":seed,
            "low95":round(means[int(.025*reps)],6),
            "high95":round(means[int(.975*reps)-1],6),
            "observed_delta":round(sum(sum(x) for x in blocks.values())/
                                   len(pairs),6)}

def matched_directional(pairs):
    if not pairs:return None
    a=[p["t"]["trade"] for p in pairs]
    b=[p["c"]["trade"] for p in pairs]
    return score([{"trade":x} for x in a],25)["tp_probability_filled"], \
           score([{"trade":x} for x in b],25)["tp_probability_filled"]

def evaluate(window,threes,fives,rec3,rec5,parity_evidence):
    _,begin,end=window
    if (len(rec3)!=672 or len(rec5)!=672 or
        set(threes)!=set(SYMBOLS) or set(fives)!=set(SYMBOLS)):
        raise C114Error("INCOMPLETE_SOURCE_UNIVERSE")
    source={s:per_symbol(threes[s],fives[s],s,window) for s in SYMBOLS}
    events=[e for s in SYMBOLS for e in source[s]["events"]]
    pairs=match_events(events)
    treated=[e for e in events if e["treatment"]=="T_CHoCH"]
    control=[e for e in events if e["treatment"]=="C_NO_CHoCH"]
    fold=int((begin+timedelta(days=28)).timestamp()*1000)
    early=[p for p in pairs if p["t0"]<fold]
    late=[p for p in pairs if p["t0"]>=fold]
    Tmatched=[p["t"] for p in pairs];Cmatched=[p["c"] for p in pairs]
    scores={
        "T_ALL":{str(b):score(treated,b) for b in BPS},
        "C_ALL":{str(b):score(control,b) for b in BPS},
        "T_MATCHED":{str(b):score(Tmatched,b) for b in BPS},
        "C_MATCHED":{str(b):score(Cmatched,b) for b in BPS},
    }
    boots=boot_delta(pairs)
    alltrades=[e["trade"] for e in treated if e["trade"] is not None]
    # Deterministic per-symbol capacity for an actually feasible DD path;
    # DOES NOT delete overlapping events from independent signal quality study.
    use=[];busy={s:0 for s in SYMBOLS};skipped=0
    for x in sorted(alltrades,key=lambda t:(t["entry_ms"],t["symbol"],t["parent_id"])):
        if x["entry_ms"]<busy[x["symbol"]]:
            skipped+=1;continue
        use.append(x);busy[x["symbol"]]=x["exit_ms"]
    portfolio=prior.portfolio_dd(use,threes,25)
    portfolio["capacity_blocked_treated"] = skipped
    directions=matched_directional(pairs)
    early_direction=matched_directional(early)
    late_direction=matched_directional(late)
    reasons=[]
    if len(pairs)<40:reasons.append("NO_POWER_MATCHED_PAIRS_LT_40")
    if len(early)<10 or len(late)<10:
        reasons.append("NO_POWER_TEMPORAL_MATCHED_FOLD")
    t25=scores["T_MATCHED"]["25"]
    t40=scores["T_MATCHED"]["40"]
    if t25["net_total_r"]<=0:reasons.append("T_NET_25_NONPOSITIVE")
    if t25["pf"] is None or t25["pf"]<=1.2:reasons.append("T_PF25_LOW")
    if t40["pf"] is None or t40["pf"]<=1.1:reasons.append("T_PF40_LOW")
    if boots["low95"] is None or boots["low95"]<=0:
        reasons.append("BOOTSTRAP_DELTA_NOT_POSITIVE")
    if directions is None or directions[0] is None or directions[1] is None or directions[0]<=directions[1]:
        reasons.append("MATCHED_TP_FIRST_PASSAGE_NOT_SUPERIOR")
    for name,dx in (("EARLY",early_direction),("LATE",late_direction)):
        if dx is None or dx[0] is None or dx[1] is None or dx[0]<=dx[1]:
            reasons.append(name+"_MATCHED_TP_NOT_SUPERIOR")
    if portfolio["dd_adverse_wick_pct_upper_bound"]>=10:
        reasons.append("DD_UPPERBOUND_GE_10")
    # NO_POWER dominates economic gate and should never be treated as PASS.
    state="NO_POWER" if any(x.startswith("NO_POWER") for x in reasons) else (
        "FAIL" if reasons else "HISTORICAL_SCREEN_PASS_PAPER_ONLY")
    return {
        "window":window[0],"start":begin.isoformat(),"end_exclusive":end.isoformat(),
        "source_3m_zips":len(rec3),"source_5m_zips":len(rec5),
        "original3m_bars":sum(len(x) for x in threes.values()),
        "original5m_bars":sum(len(x) for x in fives.values()),
        "source_receipts_3m":rec3,"source_receipts_5m":rec5,
        "source_15m_cross_archive_parity":parity_evidence,
        "per_symbol":source, "cohort":{
            "initial_touch_eligible_events":len(events),
            "treated_n":len(treated),"controls_n":len(control),
            "treated_early_competing":sum(e["early"]["status"].startswith("EARLY_COMPETING") for e in treated),
            "control_early_competing":sum(e["early"]["status"].startswith("EARLY_COMPETING") for e in control),
            "treated_unmatched_n":len(treated)-len(pairs),
            "control_unused_n":len(control)-len(pairs),
            "matched_pairs_n":len(pairs),
            "matched_early_fold_n":len(early),"matched_late_fold_n":len(late),
            "events_without_5m_structural_source":sum(not e["five_pre_touch_has_structure"] for e in events),
        },
        "matched_pair_indices":[{"id":p["id"],"symbol":p["symbol"],
                                  "t0":p["t0"],
                                  "t_parent_id":p["t"]["parent_id"],
                                  "c_parent_id":p["c"]["parent_id"]} for p in pairs],
        "scores":scores,
        "bootstrap":boots,"matched_tp_probabilities":directions,
        "early_fold_matched_tp_probabilities":early_direction,
        "late_fold_matched_tp_probabilities":late_direction,
        "portfolio":portfolio,
        "admission":{"state":state,"reasons":reasons,"live_approved":False,
                     "historical_only":True,"funding_missing":True,
                     "causal_effect_identified":False},
    }

def run():
    frozen()
    windows={}
    for w in WINDOWS:
        a,b,ra,rb,parity=download(w)
        windows[w[0]]=evaluate(w,a,b,ra,rb,parity)
    return {
        "schema":"C114_INDEPENDENT_4H_FVG_FIRST_TOUCH_NATIVE5M_CHOCH_MATCHED",
        "precommit":PRECOMMIT,
        "original_3m_zip_total":sum(x["source_3m_zips"] for x in windows.values()),
        "original_5m_zip_total":sum(x["source_5m_zips"] for x in windows.values()),
        "original_3m_bar_total":sum(x["original3m_bars"] for x in windows.values()),
        "original_5m_bar_total":sum(x["original5m_bars"] for x in windows.values()),
        "historical_screen_pass_both_windows":all(
            x["admission"]["state"]=="HISTORICAL_SCREEN_PASS_PAPER_ONLY" for x in windows.values()),
        "causal_effect_proven":False,"paper_only":True,"live_approved":False,
        "true_prospective_oos":False,"funding_missing":True,
        "real_orders":[],"real_fills":[],"live_trades":[],
        "windows":windows
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    result=run()
    if (result["original_3m_zip_total"]!=EXPECTED_3M_ZIPS or
        result["original_5m_zip_total"]!=EXPECTED_5M_ZIPS or
        result["original_3m_bar_total"]!=EXPECTED_3M_BARS or
        result["original_5m_bar_total"]!=EXPECTED_5M_BARS):
        raise C114Error("SOURCE_COUNT_NOT_PREDECLARED")
    folder=args.output_dir;folder.mkdir(parents=True,exist_ok=True)
    receipts={}
    for name,payload in result["windows"].items():
        fn=f"C114_{name}_ORIGINAL_3M5M_EVENT_AND_PAIR_LEDGER.json"
        raw=(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
        (folder/fn).write_bytes(raw)
        receipts[name]={"filename":fn,"sha256":hashlib.sha256(raw).hexdigest(),
                        "bytes":len(raw),"admission":payload["admission"],
                        "cohort":payload["cohort"],"scores":payload["scores"],
                        "bootstrap":payload["bootstrap"],"portfolio":payload["portfolio"]}
    summary={k:v for k,v in result.items() if k!="windows"}
    summary["window_receipts"]=receipts
    blob=(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    (folder/"C114_SUMMARY.json").write_bytes(blob)
    print(json.dumps({"source_zips":result["original_3m_zip_total"]+
                       result["original_5m_zip_total"],
                      "screen_pass":result["historical_screen_pass_both_windows"],
                      "windows":receipts,"summary_sha256":hashlib.sha256(blob).hexdigest()},
                     ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
