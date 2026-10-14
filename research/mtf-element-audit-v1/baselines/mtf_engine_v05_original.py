#!/usr/bin/env python3
"""MTF education route research emulator v0.3, no exchange/trading API.

Research hypotheses, not a validated reconstruction of annotated course charts.
Event-time discipline: structural detections only mature at final confirmation candle close.
Version 0.2 separates OB/RB, SNR break/retest and consumed liquidity; these remain course proxies.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Optional

Q=900_000
STEPS={'15m':Q,'1h':4*Q,'4h':16*Q,'1d':96*Q,'1w':672*Q}
ALGO='MTF_ROUTE_RESEARCH_0.3.0'

@dataclass(frozen=True)
class Bar:
    start:int;end:int;o:float;h:float;l:float;c:float;v:float;tf:str='15m'

@dataclass(frozen=True)
class Feature:
    id:str; tf:str; type:str; side:str; lo:float;hi:float
    origin:int; known:int; source:str; parents:tuple[str,...]=()

@dataclass(frozen=True)
class TradeIdea:
    id:str;route:str;parent_id:str;trigger_id:str;vc_id:str;side:str
    known:int;entry:float;stop:float;target:float;net_rr:float;qty:float
    unit_risk:float;note:str;target_tf:str;capital_risk_pct:float=0.005


def iso(t):return datetime.fromtimestamp(t/1000,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def ms(s):
    t=str(s).strip();return int(t) if t.isdecimal() else int(datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()*1000)

def load_csv(path,symbol=None,tf="15m"):
    p=Path(path);content=p.read_bytes();digest=hashlib.sha256(content).hexdigest()
    data=[]
    with p.open(encoding='utf-8-sig',newline='') as f:
        for x in csv.DictReader(f):
            if symbol and x.get('symbol') and x['symbol'].upper()!=symbol.upper():continue
            start=ms(x.get('open_time') or x.get('time'))
            vals=[float(x[k]) for k in ('open','high','low','close')]
            o,h,l,c=vals;v=float(x.get('volume') or 0)
            if any(not math.isfinite(z) for z in [*vals,v]) or min(o,h,l,c)<=0 or v<0 or h<max(o,c,l) or l>min(o,c,h):raise ValueError('Bad OHLCV at '+str(start))
            data.append(Bar(start,start+STEPS[tf],o,h,l,c,v,tf))
    data.sort(key=lambda x:x.start)
    for a,b in zip(data,data[1:]):
        if b.start-a.start!=STEPS[tf]:raise ValueError('Missing/duplicate candle '+iso(a.start))
    return data,digest

def aggregate(data,tf):
    """Only complete UTC buckets: partial HTF candle is never visible."""
    if tf=='15m':return data[:]
    period=STEPS[tf]
    buckets=defaultdict(list)
    for b in data:
        if tf=='1w':start=((b.start+3*86_400_000)//period)*period-3*86_400_000
        else:start=(b.start//period)*period
        buckets[start].append(b)
    out=[]
    for start,a in sorted(buckets.items()):
        if len(a)!=period//STEPS[data[0].tf] or a[0].start!=start or a[-1].end!=start+period:continue
        out.append(Bar(start,start+period,a[0].o,max(x.h for x in a),min(x.l for x in a),a[-1].c,sum(x.v for x in a),tf))
    return out

def atr(barset,i,n=14):
    if i<n:return None
    a=barset[i-n:i];tr=[]
    for j,x in enumerate(a):
        p=a[j-1].c if j else x.o
        tr.append(max(x.h-x.l,abs(x.h-p),abs(x.l-p)))
    return sum(tr)/len(tr)

def tag(tf,kind,t,prefix=''):
    return f'{tf}:{kind}:{t}:{prefix}'

def features(bars,tf):
    """FVG: three closed candles; pivot: left/right=2; SNR: confirmed pivot broken.
    RB: two opposing candles with liquidity sweep or interaction with prior FVG.
    SNR/RB are computational label hypotheses requiring visual ground-truth audit.
    """
    f=[];active_highs=[];active_lows=[]
    last_break=set();pending_snr=[];consumed_liquidity=set()
    for i,b in enumerate(bars):
        # Pivots from right-confirmation candles, never from pivot's own time.
        j=i-2
        if j>=2:
            left=bars[j-2:j];right=bars[j+1:j+3];p=bars[j]
            if p.h>max(z.h for z in left+right):
                obj=Feature(tag(tf,'PIV_H',p.start),tf,'PIV_H','SHORT',p.h,p.h,p.start,b.end,'PIVOT_2_2')
                f.append(obj);active_highs.append(obj)
            if p.l<min(z.l for z in left+right):
                obj=Feature(tag(tf,'PIV_L',p.start),tf,'PIV_L','LONG',p.l,p.l,p.start,b.end,'PIVOT_2_2')
                f.append(obj);active_lows.append(obj)
        if i>=2:
            first=bars[i-2]
            if b.l>first.h: f.append(Feature(tag(tf,'IMB_LONG',b.start),tf,'IMB','LONG',first.h,b.l,first.start,b.end,'THREE_CANDLE_FVG'))
            if b.h<first.l: f.append(Feature(tag(tf,'IMB_SHORT',b.start),tf,'IMB','SHORT',b.h,first.l,first.start,b.end,'THREE_CANDLE_FVG'))
        a=atr(bars,i) or max(b.h-b.l,b.c*.001)
        # SNR differs from breakout: flip MUST be subsequently retested and held.
        # Candidate is intentionally not emitted as a mature SNR POI.
        remaining=[]
        for candidate,created_index in pending_snr:
            if i<=created_index:remaining.append((candidate,created_index));continue
            if i-created_index>20:continue  # declared lab hypothesis; not a course claim
            if (candidate.side=='LONG' and b.c<candidate.lo) or (candidate.side=='SHORT' and b.c>candidate.hi):continue
            if b.h>=candidate.lo and b.l<=candidate.hi and ((candidate.side=='LONG' and b.c>candidate.hi) or (candidate.side=='SHORT' and b.c<candidate.lo)):
                f.append(Feature(tag(tf,'SNR_HOLD',b.start,candidate.id),tf,'SNR',candidate.side,candidate.lo,candidate.hi,candidate.origin,b.end,'BREAK_RETEST_AND_HOLD',(candidate.id,*candidate.parents)))
                continue
            remaining.append((candidate,created_index))
        pending_snr=remaining
        for prev,side in [(active_highs,'LONG'),(active_lows,'SHORT')]:
            if not prev:continue
            p=prev[-1];level=p.hi if side=='LONG' else p.lo
            if p.known>=b.end or p.id in last_break:continue
            crossed=(b.c>level and bars[i-1].c<=level) if side=='LONG' else (b.c<level and bars[i-1].c>=level)
            if crossed:
                last_break.add(p.id)
                w=min(.20*a,.005*level)
                pending_snr.append((Feature(tag(tf,'SNR_PENDING_'+side,b.start,p.id),tf,'SNR_PENDING',side,level-w,level+w,b.start,b.end,'BREAK_NOT_YET_RETESTED',(p.id,)),i))
        # A wick raid MUST exceed a previously confirmed swing, and close back through it.
        for prev,side in [(active_lows,'LONG'),(active_highs,'SHORT')]:
            if not prev:continue
            p=prev[-1];level=p.lo if side=='LONG' else p.hi
            if p.known>=b.end or p.id in consumed_liquidity:continue
            crossed=(b.l<level if side=='LONG' else b.h>level)
            if crossed:
                consumed_liquidity.add(p.id)
                if ((b.c>level) if side=='LONG' else (b.c<level)):
                    f.append(Feature(tag(tf,'RAID_'+side,b.start,p.id),tf,'RAID',side,b.l,b.h,b.start,b.end,'WICK_RECLAIM_FIRST_RAID_ONLY',(p.id,)))
        if i:
            prev=bars[i-1]
            # OB requires a full BODY engulf of the preceding opposing candle.
            bull_engulf=prev.c<prev.o and b.c>b.o and b.c>=prev.o and b.o<=prev.c
            bear_engulf=prev.c>prev.o and b.c<b.o and b.c<=prev.o and b.o>=prev.c
            if bull_engulf or bear_engulf:
                side='LONG' if bull_engulf else 'SHORT'
                # Source OB zone is the prior opposing candle (body/wick ambiguity logged).
                f.append(Feature(tag(tf,'OB_'+side,b.start),tf,'OB',side,prev.l,prev.h,prev.start,b.end,'OB_PRIOR_OPPOSING_CANDLE_BODY_ENGULFED'))
            # RB is NOT synonymous with engulfing. It is an opposing candle pair
            # with actual liquidation/IMB interaction and zone marked by WICKS.
            bull_rb=prev.c<prev.o and b.c>b.o
            bear_rb=prev.c>prev.o and b.c<b.o
            if bull_rb or bear_rb:
                side='LONG' if bull_rb else 'SHORT'
                lo=min(prev.l,b.l);hi=max(prev.h,b.h)
                # The course requires a WICK raid or a WICK-only touch of a
                # PRE-EXISTING same-side IMB, not an overlap of candle bodies
                # with an unrelated/newly-created FVG.
                recent=[x for x in f if x.tf==tf and x.origin>=prev.start-3*STEPS[tf] and x.lo<=hi and x.hi>=lo]
                raid=any(x.type=='RAID' and x.side==side and prev.start<=x.origin<=b.start
                         and x.known<=b.end for x in recent)
                imb_wick=False
                for x in recent:
                    if x.type!='IMB' or x.side!=side or x.known>prev.end:continue
                    for z in (prev,b):
                        if side=='LONG' and z.l<x.hi and min(z.o,z.c)>=x.hi:
                            imb_wick=True
                        if side=='SHORT' and z.h>x.lo and max(z.o,z.c)<=x.lo:
                            imb_wick=True
                interacting=raid or imb_wick
                if interacting:
                    body_floor=min(prev.o,prev.c,b.o,b.c)
                    body_ceiling=max(prev.o,prev.c,b.o,b.c)
                    zlo,zhi=(lo,body_floor) if side=='LONG' else (body_ceiling,hi)
                    if zhi>zlo:
                        f.append(Feature(tag(tf,'RB_'+side,b.start),tf,'RB',side,zlo,zhi,prev.start,b.end,'RB_WICK_WITH_RAID_OR_IMB'))
    return sorted(f,key=lambda x:(x.known,x.id))

def intersects(b,poi):return b.h>=poi.lo and b.l<=poi.hi

def permits_one_hour_imb_trigger(parent):
    """Only RB/SNR 4H parents permit the course's nested 1H IMB trigger."""
    return parent.tf=='4h' and parent.type in ('RB','SNR')

def entry_quote(route,parent,trigger,vc,side,known,E,S,pivmap,fee=.0005,slippage=.0002,risk_pct=.005,
                min_rr=2.0,stop_buffer=.0003,target_buffer=.0003,notional_cap=3.0,fta_policy='COURSE_PARENT_FTA',fta_source_tf=None):
    """All capital assumptions normalized to 1 USDT of balance; q is base units per 1 USDT.
    FTA is *nearest known available* obstacle, record selected TF; no made-up target.
    """
    L=side=='LONG'
    if not (parent.known<trigger.known<vc.known<=known):return None,'FUTURE_OR_OUT_OF_ORDER'
    if not all(math.isfinite(x) and x>0 for x in (E,S)) or not (E>S if L else E<S):return None,'BAD_STOP'
    barrier=[]
    for tf,items in pivmap.items():
        # Micro-15m swing noise is not automatically a parental FTA.
        if tf=='15m':continue
        for f in items:
            if f.known>known:continue
            if f.type!=('PIV_H' if L else 'PIV_L'):continue
            p=f.hi if L else f.lo
            if (p>E if L else p<E):barrier.append((abs(p-E),p,tf,f.id))
    if not barrier:return None,'NO_FTA'
    if fta_policy=='COURSE_PARENT_FTA':
        source_tf=fta_source_tf or ('1h' if route.startswith('C_') else parent.tf)
        selection=[x for x in barrier if x[2]==source_tf]
        if not selection:return None,'NO_SOURCE_TF_FTA'
    elif fta_policy=='V22_FIRST_OBSTACLE':selection=barrier
    else:raise ValueError('Unknown frozen FTA policy')
    _,P,tf,fid=min(selection)
    other=min(barrier)
    conflict=other[2]!=tf and other[0]<abs(P-E)
    # No assumed 2R TP; first relevant obstacle before costs.
    T=P*(1-target_buffer if L else 1+target_buffer)
    if not (T>E if L else T<E):return None,'NO_FREE_SPACE'
    friction=fee+slippage
    loss=abs(E-S)+friction*(E+S)
    reward=abs(T-E)-friction*(E+T)
    rr=reward/loss
    if rr<min_rr:return None,'LOW_NET_RR'
    quantity=min(risk_pct/loss,notional_cap/E)
    if quantity<=0:return None,'SIZE_ZERO'
    name=tag('15m','IDEA',known,route+':'+parent.id+':'+trigger.id+':'+vc.id)
    return TradeIdea(name,route,parent.id,trigger.id,vc.id,side,known,E,S,T,rr,quantity,loss,fta_policy+'; FTA='+fid+'; FTA_PIVOT_PROXY; STRONGHL_PROXY; nearer_other_tf='+str(conflict),tf,risk_pct),'OK'

def simulate(idea,bars,start_idx,expiry_bars=12,hold_bars=96,fee=.0005,slippage=.0002):
    """Single order path from NEXT 15m candle. Limit touch != guaranteed fill.
    No profit credit for target-before-fill; same-bar SL/TP -> SL first.
    Costed R outputs normalized to planned stop loss, gap-through stops worsened.
    """
    L=idea.side=='LONG';E=idea.entry;S=idea.stop;T=idea.target
    end=min(len(bars),start_idx+1+expiry_bars)
    fill=None
    for j in range(start_idx+1,end):
        b=bars[j]
        target_reached=b.h>=T if L else b.l<=T
        touched=b.l<=E if L else b.h>=E
        stop_reached=b.l<=S if L else b.h>=S
        # If target before entry inside same bar ordering unknowable.
        if target_reached and not touched:return {'status':'TARGET_BEFORE_FILL','r':None}
        if target_reached and touched:return {'status':'AMBIGUOUS_BEFORE_FILL','r':None}
        if stop_reached and not touched:return {'status':'INVALIDATED_BEFORE_FILL','r':None}
        if touched:
            # gap past stop cannot count as a clean limit fill, no reliable path
            if (b.o<S if L else b.o>S):return {'status':'GAP_BEYOND_STOP_BEFORE_FILL','r':None}
            fill=j;break
    if fill is None:
        if end==len(bars) and len(bars)<start_idx+1+expiry_bars:
            return {'status':'PENDING_UNRESOLVED','r':None}
        return {'status':'NO_FILL','r':None}
    cutoff=min(fill+hold_bars,len(bars))
    for j in range(fill,cutoff):
        b=bars[j];sl=b.l<=S if L else b.h>=S;tp=b.h>=T if L else b.l<=T
        if sl:
            realized_stop=min(b.o,S) if L else max(b.o,S)
            # Entry friction, exit friction at worse gap stop
            pnl=(realized_stop-E if L else E-realized_stop)-(fee+slippage)*(E+realized_stop)
            return {'status':'SL_FIRST_AMBIGUOUS' if tp else 'SL','r':pnl/idea.unit_risk,'fill':iso(bars[fill].start),'exit':iso(b.end),'ambiguous':tp}
        if tp:
            return {'status':'TP','r':idea.net_rr,'fill':iso(bars[fill].start),'exit':iso(b.end)}
    if cutoff==len(bars):return {'status':'CENSORED','r':None,'fill':iso(bars[fill].start)}
    b=bars[cutoff-1]
    pnl=(b.c-E if L else E-b.c)-(fee+slippage)*(E+b.c)
    return {'status':'TIME_EXIT','r':pnl/idea.unit_risk,'fill':iso(bars[fill].start),'exit':iso(b.end)}

def route_replay(data,market_symbol='BTCUSDT',min_rr=2.0,allow_B=True,allow_C=True,native=None,strict_daily=True,fta_policy='COURSE_PARENT_FTA',fee=.0005,slippage=.0002):
    """Stream of closed candles. Paths are independent exploratory idea outcomes.
    No representation of an entire exchange portfolio, correlation or guaranteed fills.
    """
    if not data:raise ValueError('Empty 15m history')
    streams={tf:aggregate(data,tf) for tf in ('15m','1h','4h','1d','1w')}
    if native:
        for tf,source in native.items():
            if tf not in ('1h','4h','1d','1w'):raise ValueError('Invalid native TF')
            if any(x.tf!=tf for x in source):raise ValueError('Native TF mismatch')
            streams[tf]=[b for b in source if b.end<=data[-1].end]
        if '1d' in native and '1w' not in native:streams['1w']=aggregate(streams['1d'],'1w')
    feats={tf:features(streams[tf],tf) for tf in streams}
    timeline=defaultdict(list);pivmap={tf:[] for tf in streams}
    for tf,events in feats.items():
        for e in events:timeline[e.known].append(e)
    snapshots=[];ideas=[];samples=[];diag=Counter();parents={};triggers=[];childvc=[];feature_by_id={};trigger_strong={}
    daily_features=feats['1d']
    def daily_anchor(p):
        # As-of known 1D FVG/SNR/RB or confirmed external liquidity swing.
        choices=[x for x in daily_features if x.known<=p.known and x.type in ('IMB','SNR','RB','PIV_H','PIV_L') and x.side==p.side and x.lo<=p.hi and p.lo<=x.hi]
        # Point-in-time consumption: a pivot already raided, or a POI closed
        # through its invalidation before this 4h formation, is not an anchor.
        def still_active(x):
            for day in streams['1d']:
                if day.end<=x.known:continue
                if day.end>p.known:break
                if x.type=='PIV_H' and day.h>x.hi:return False
                if x.type=='PIV_L' and day.l<x.lo:return False
                if x.type not in ('PIV_H','PIV_L'):
                    if (x.side=='LONG' and day.c<x.lo) or (x.side=='SHORT' and day.c>x.hi):return False
            return True
        choices=[x for x in choices if still_active(x)]
        return max(choices,key=lambda x:x.known) if choices else None
    def add_parent(e):
        anchor=daily_anchor(e)
        if strict_daily and anchor is None:
            diag['NO_DAILY_ANCHOR_REJECTED']+=1;return
        # A 4H VC intersecting an earlier 1D anchor is an auditable candidate
        # for the course's distinct 4H VC -> 1H IDM route. StrongHL is still
        # explicitly only a PROXY until independently annotated screenshots.
        strong4=None
        if anchor is not None:
            h4=[z for z in streams['4h'] if e.origin<=z.start and z.end<=e.known]
            contact=[z for z in h4 if intersects(z,anchor)]
            if contact:
                first_contact=contact[0].end
                post=[z for z in h4 if first_contact<=z.end<=e.known]
                if post:strong4=min(z.l for z in post) if e.side=='LONG' else max(z.h for z in post)
        parents[e.id]={'poi':e,'tested':None,'invalid':None,'daily_anchor':anchor.id if anchor else None,
                       'daily_anchor_feature':anchor,'strong4_proxy':strong4}
        diag['parent_poi_detected']+=1
    idx={tf:0 for tf in streams};last_15={b.end:i for i,b in enumerate(data)}
    seen_ideas=set();issued_route_trigger=set();max_age=3*86_400_000;max_child=8*3_600_000
    # Carry strictly earlier native higher-TF knowledge into the first 15m candle.
    first=data[0].end if data else 0
    for tf,arr in feats.items():
        for e in arr:
            if e.known>=first:continue
            feature_by_id[e.id]=e
            if e.type.startswith('PIV_'):pivmap[e.tf].append(e)
            if e.tf=='4h' and e.type in ('IMB','SNR','RB'):add_parent(e)
    h1_at={x.end:x for x in streams['1h']}
    # Remove levels already violated before the first scanned 15m candle.
    for tf,existing in pivmap.items():
        candles=[b for b in streams[tf] if b.end<first]
        pivmap[tf]=[p for p in existing if not any(b.end>p.known and (b.c>p.hi if p.type=='PIV_H' else b.c<p.lo) for b in candles)]
    htf_end={tf:{x.end:x for x in streams[tf]} for tf in ('1h','4h','1d','1w')}
    for b in data:
        now=b.end
        events=timeline.get(now,[])
        # A violated pivot no longer qualifies as an unconsumed first barrier.
        for tf,bar_index in htf_end.items():
            hbar=bar_index.get(now)
            if hbar:
                pivmap[tf]=[p for p in pivmap[tf] if not (p.known<now and (hbar.c>p.hi if p.type=='PIV_H' else hbar.c<p.lo))]
        # At shared closure: higher TF first, but no formation and test at the same timestamp.
        events.sort(key=lambda x:(-STEPS[x.tf],x.id))
        for e in events:
            feature_by_id[e.id]=e
            if e.type.startswith('PIV_'):pivmap[e.tf].append(e)
            if e.tf=='4h' and e.type in ('IMB','SNR','RB'):add_parent(e)
        # Test parent on completed 1H bar only, never at POI confirmation time.
        if now in h1_at:
            hour=h1_at[now]
            if hour:
                for obj in parents.values():
                    p=obj['poi'];
                    if p.known>=now or obj['invalid'] is not None:continue
                    if obj['tested'] is None and intersects(hour,p):
                        obj['tested']=now;diag['4h_poi_tested']+=1
                    # zone destroyed by close through wrong side: no fresh signals.
                    if (p.side=='LONG' and hour.c<p.lo-.001*hour.c) or (p.side=='SHORT' and hour.c>p.hi+.001*hour.c):
                        obj['invalid']=now
                # Existing completed tested POI + 1h wick raid in compatible direction.
                for e in events:
                    if e.tf!='1h' or e.type!='RAID':continue
                    eligible=[o for o in parents.values() if o['tested'] is not None and o['tested']<=now and o['invalid'] is None and o['poi'].side==e.side and o['poi'].known<e.known and now-o['tested']<=max_age and intersects(hour,o['poi'])]
                    for o in eligible:
                        triggers.append((o['poi'],e,now));diag['1h_raid_parent_link']+=1
                        recent=[z for z in streams['1h'] if o['tested']<=z.end<=now]
                        if recent:trigger_strong[(o['poi'].id,e.id)]=(min(z.l for z in recent) if e.side=='LONG' else max(z.h for z in recent))
                # Course allows a 1H IMB trigger ONLY if its parent 4H zone
                # is RB/SNR. 4H IMB + nested 1H IMB is specifically excluded.
                for e in events:
                    if e.tf!='1h' or e.type!='IMB':continue
                    eligible=[o for o in parents.values() if o['tested'] is not None and o['tested']<=now
                              and o['invalid'] is None and permits_one_hour_imb_trigger(o['poi'])
                              and o['poi'].side==e.side and o['poi'].known<e.known
                              and now-o['tested']<=max_age and intersects(hour,o['poi'])]
                    for o in eligible:
                        triggers.append((o['poi'],e,now));diag['1h_imb_trigger_parent_rb_snr']+=1
                        recent=[z for z in streams['1h'] if o['tested']<=z.end<=now]
                        if recent:trigger_strong[(o['poi'].id,e.id)]=(min(z.l for z in recent) if e.side=='LONG' else max(z.h for z in recent))
                # Need actual 1H VC formation in area, not volume SMA.
                for e in events:
                    if e.tf!='1h' or e.type not in ('IMB','SNR','RB'):continue
                    eligible=[o for o in parents.values() if o['tested'] and o['poi'].side==e.side and o['invalid'] is None and o['poi'].known<e.known and (now-o['tested']<=2*3_600_000 or intersects(hour,o['poi']))]
                    for o in eligible:
                        # StrongHL candidate must include ACTUAL parent POI contact
                        # and a later VC, with the source extreme frozen at VC close.
                        h1=streams['1h'];test_at=o['tested'];recent=[x for x in h1 if test_at<=x.end<=now]
                        if not recent or now-test_at>8*3_600_000:continue
                        strong=min(x.l for x in recent) if e.side=='LONG' else max(x.h for x in recent)
                        # Exclude an extreme already broken by the VC close itself.
                        if (e.side=='LONG' and hour.c<=strong) or (e.side=='SHORT' and hour.c>=strong):continue
                        childvc.append((o['poi'],e,strong,now));diag['1h_vc_parent_link']+=1
        # Separate 4H-VC/1H-IDM path must run at the close of a 1H pivot.
        # Do not conflate it with the 15m branch below.
        for e in events:
            if e.tf!='1h' or e.type not in ('PIV_L','PIV_H') or not allow_B:continue
            # The independently taught 4H VC -> 1H IDM branch (NOT 15m).
            # Use confirmed 1H pivots, and do not demand an additional BOS.
            for o in parents.values():
                p=o['poi'];anchor=o['daily_anchor_feature'];strong=o['strong4_proxy']
                if anchor is None or strong is None or o['invalid'] is not None:continue
                if not (p.known<e.known<=p.known+max_child):continue
                if (e.type=='PIV_L' and p.side!='LONG') or (e.type=='PIV_H' and p.side!='SHORT'):continue
                E=e.lo if p.side=='LONG' else e.hi
                if not (strong<E<=p.hi if p.side=='LONG' else p.lo<=E<strong):
                    diag['B4_IDM_OUTSIDE_4H_PROTECTED_RANGE']+=1;continue
                S=strong-.0003*E if p.side=='LONG' else strong+.0003*E
                idea,reason=entry_quote('B_IDM',anchor,p,e,p.side,now,E,S,pivmap,
                                        min_rr=min_rr,fta_policy=fta_policy,fta_source_tf='4h',fee=fee,slippage=slippage)
                diag['B4_'+reason]+=1
                key=('B4',p.id)
                if idea and idea.id not in seen_ideas and key not in issued_route_trigger:
                    from dataclasses import replace
                    idea=replace(idea,note=idea.note+'; SUBROUTE=4H_VC_TO_1H_IDM; STRONGHL=PROXY')
                    ideas.append(idea);seen_ideas.add(idea.id);issued_route_trigger.add(key)
                elif idea:diag['B4_DUPLICATE_TRIGGER_SKIPPED']+=1
        # 15m route emit after already confirmed 1h parents; this is an IDEA, not a fill.
        for e in events:
            if e.tf!='15m':continue
            if e.type in ('IMB','SNR'):
                for parent,trigger,t in triggers:
                    if parent.side!=e.side or not (t<e.known<=t+max_child):continue
                    if parent.known>=t:continue
                    # One route idea per trigger/VC, not repeated after each candle.
                    E=(e.lo+e.hi)/2;S=((trigger_strong.get((parent.id,trigger.id),trigger.lo)-.0003*E)
                       if e.side=='LONG' else (trigger_strong.get((parent.id,trigger.id),trigger.hi)+.0003*E))
                    idea,reason=entry_quote('A_VC_IMB_SNR',parent,trigger,e,e.side,now,E,S,pivmap,min_rr=min_rr,fta_policy=fta_policy,fee=fee,slippage=slippage)
                    diag['A_'+reason]+=1
                    key=('A',trigger.id)
                    if idea and idea.id not in seen_ideas and key not in issued_route_trigger:
                        ideas.append(idea);seen_ideas.add(idea.id);issued_route_trigger.add(key)
                    elif idea:diag['A_DUPLICATE_TRIGGER_SKIPPED']+=1
            if e.type in ('PIV_L','PIV_H') and allow_B:
                for parent,vc,strong,t in childvc:
                    if e.tf!='15m':continue
                    if not(t<e.known<=t+max_child):continue
                    if (e.type=='PIV_L' and vc.side!='LONG') or (e.type=='PIV_H' and vc.side!='SHORT'):continue
                    E=e.lo;S=(strong-.0003*E if vc.side=='LONG' else strong+.0003*E)
                    # IDM pivot must be located in the structural protected range, not arbitrary faraway swing.
                    if not (strong<E<max(vc.hi,parent.hi) if vc.side=='LONG' else min(vc.lo,parent.lo)<E<strong):
                        diag['B_IDM_OUTSIDE_PROTECTED_RANGE']+=1;continue
                    idea,reason=entry_quote('B_IDM',parent,vc,e,vc.side,now,E,S,pivmap,min_rr=min_rr,fta_policy=fta_policy,fee=fee,slippage=slippage)
                    diag['B_'+reason]+=1
                    key=('B',vc.id)
                    if idea and idea.id not in seen_ideas and key not in issued_route_trigger:
                        ideas.append(idea);seen_ideas.add(idea.id);issued_route_trigger.add(key)
                    elif idea:diag['B_DUPLICATE_TRIGGER_SKIPPED']+=1
            if e.type in ('SNR',) and allow_C:
                # C is an explicit 15m PROXY for source's 1H->3/5m BOS; never label original.
                for parent,trigger,t in triggers:
                    if trigger.side!=e.side or not(t<e.known<=t+max_child):continue
                    E=e.hi if e.side=='LONG' else e.lo;S=trigger.lo-.0003*E if e.side=='LONG' else trigger.hi+.0003*E
                    idea,reason=entry_quote('C_BOS_15M_PROXY',parent,trigger,e,e.side,now,E,S,pivmap,min_rr=min_rr,fta_policy=fta_policy,fee=fee,slippage=slippage)
                    diag['C_'+reason]+=1
                    key=('C',trigger.id)
                    if idea and idea.id not in seen_ideas and key not in issued_route_trigger:
                        ideas.append(idea);seen_ideas.add(idea.id);issued_route_trigger.add(key)
                    elif idea:diag['C_DUPLICATE_TRIGGER_SKIPPED']+=1
        if now in last_15 and len(snapshots)<150:snapshots.append({'at':iso(now),'known_events':len(events),'parents':len(parents),'triggers':len(triggers)})
    # Independent route-level outcomes, not a portfolio equity curve.
    case=[]
    for idea in ideas:
        try: start_idx=last_15[idea.known]
        except KeyError:continue
        r=simulate(idea,data,start_idx,fee=fee,slippage=slippage)
        case.append({**asdict(idea),**r,'at':iso(idea.known)})
    # Context annotations are descriptive and strictly use known earlier snapshots.
    def context(at):
        chart={};
        for tf in ('1d','1w'):
            x=[z for z in feats[tf] if z.known<=at and z.type.startswith('PIV_')]
            high=[z.hi for z in x if z.type=='PIV_H'][-2:];low=[z.lo for z in x if z.type=='PIV_L'][-2:]
            state='UNKNOWN'
            if len(high)==2 and len(low)==2:
                if high[-1]>high[-2] and low[-1]>low[-2]:state='UP'
                elif high[-1]<high[-2] and low[-1]<low[-2]:state='DOWN'
                else:state='MIXED'
            chart[tf]=state
        utc_hour=datetime.fromtimestamp(at/1000,timezone.utc)
        london=utc_hour.astimezone(ZoneInfo('Europe/London')).hour
        ny=utc_hour.astimezone(ZoneInfo('America/New_York')).hour
        tokyo=utc_hour.astimezone(ZoneInfo('Asia/Tokyo')).hour
        return {'1d_pivots':chart['1d'],'1w_pivots':chart['1w'],'london_session':8<=london<12,'new_york_session':9<=ny<13,'asia_session':9<=tokyo<15,'macro':'UNKNOWN','sector':'UNKNOWN','oi':'UNKNOWN','funding':'UNKNOWN'}
    for row in case:row['global_context_at_signal']=context(ms(row['at']))
    stats={}
    for route in ['A_VC_IMB_SNR','B_IDM','C_BOS_15M_PROXY']:
        rows=[x for x in case if x['route']==route]
        paid=[x for x in rows if x['r'] is not None]
        w=sum(x['r'] for x in paid if x['r']>0);loss=-sum(x['r'] for x in paid if x['r']<0)
        stats[route]={'ideas':len(rows),'resolved':len(paid),'outcomes':dict(Counter(x['status'] for x in rows)),'total_R_independent':round(sum(x['r'] for x in paid),4),'avg_R_resolved':round(sum(x['r'] for x in paid)/len(paid),4) if paid else None,'PF_independent':round(w/loss,3) if loss else None,'not_a_portfolio':True}
    readiness={'strict_daily_link_required':strict_daily,'history_1d_ge_50':len(streams['1d'])>=50,'history_1w_ge_10':len(streams['1w'])>=10,'complete_90d_15m':len(data)>=90*96,'no_external_price_anchors':True}
    return {'algorithm':ALGO,'symbol':market_symbol,'fta_policy':fta_policy,'costs':{'fee_per_side':fee,'slippage_per_side':slippage},'readiness':readiness,'candles':{tf:len(x) for tf,x in streams.items()},'first':iso(data[0].start) if data else None,'last':iso(data[-1].end) if data else None,'features':{tf:dict(Counter(z.type for z in arr)) for tf,arr in feats.items()},'diagnostics':dict(diag),'routes':stats,'qualified_ideas':case,'early_snapshots':snapshots}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--csv',required=True);ap.add_argument('--out',default='results');ap.add_argument('--symbol',default='BTCUSDT');ap.add_argument('--min-rr',type=float,default=2.0)
    ap.add_argument('--fee',type=float,default=.0005)
    ap.add_argument('--slippage',type=float,default=.0002)
    ap.add_argument('--cutoff',default=None,help='exclude unclosed candles at UTC timestamp')
    ap.add_argument('--htf-1d',default=None,help='optional REAL daily history, daily candles before current 15m sample')
    ap.add_argument('--htf-1w',default=None,help='optional REAL weekly history')
    ap.add_argument('--shadow-no-daily',action='store_true',help='UNVERIFIED shadow: relax daily POI anchor for diagnostics only')
    ap.add_argument('--fta-policy',choices=['COURSE_PARENT_FTA','V22_FIRST_OBSTACLE'],default='COURSE_PARENT_FTA')
    args=ap.parse_args();bars,digest=load_csv(args.csv,args.symbol)
    if args.cutoff:bars=[b for b in bars if b.end<=ms(args.cutoff)]
    if not bars:raise ValueError('No closed 15m bars')
    native={};native_sha={}
    for tf,path in [('1d',args.htf_1d),('1w',args.htf_1w)]:
        if path:
            data_tf,digest_tf=load_csv(path,args.symbol,tf)
            native[tf]=data_tf;native_sha[tf]=digest_tf
    result=route_replay(bars,args.symbol,args.min_rr,native=native,strict_daily=not args.shadow_no_daily,fta_policy=args.fta_policy,fee=args.fee,slippage=args.slippage)
    result['native_input_sha256']=native_sha
    result['input_sha256']=digest;result['disclaimer']='Exploratory approximations. No independent OOS. Not a live signal, not validated profitability. No trading.'
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    (out/'metrics.json').write_text(json.dumps({k:v for k,v in result.items() if k not in ('qualified_ideas','early_snapshots')},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/'ideas.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in result['qualified_ideas']),encoding='utf-8')
    (out/'feature_timeline.json').write_text(json.dumps(result['early_snapshots'],indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('qualified_ideas','early_snapshots')},indent=2,ensure_ascii=False))
if __name__=='__main__':main()