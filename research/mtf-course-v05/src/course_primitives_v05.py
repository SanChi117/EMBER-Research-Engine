#!/usr/bin/env python3
"""Source-aligned MTF primitives (educational, PAPER-only, no exchange I/O).

Standalone v0.5 research layer. Do not confuse with frozen 0.3/0.4, and do
not use its output for claims about fills or profitability. All decisions are
made only after the latest closed bar; 3m/5m are separate from 15m proxy.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

TF_MS = {'3m':180_000, '5m':300_000, '15m':900_000,
         '1h':3_600_000, '4h':14_400_000, '1d':86_400_000}

@dataclass(frozen=True)
class Bar:
    start: int
    end: int
    o: float
    h: float
    l: float
    c: float
    tf: str
    def __post_init__(self):
        if self.tf not in TF_MS or self.end-self.start!=TF_MS[self.tf]:
            raise ValueError('invalid timeframe or bar duration')
        if min(self.o,self.h,self.l,self.c)<=0 or self.l>min(self.o,self.c) or self.h<max(self.o,self.c):
            raise ValueError('invalid OHLC')

@dataclass(frozen=True)
class Pivot:
    id: str
    tf: str
    kind: str               # HIGH or LOW (not by itself StrongHL)
    value: float
    origin: int
    known: int

@dataclass(frozen=True)
class Raid:
    id: str
    side: str               # SHORT after BSL; LONG after SSL
    liquidity_pivot_id: str
    liquidity_level: float
    extreme: float
    origin: int
    known: int
    tf: str = '1h'

@dataclass(frozen=True)
class BosEvent:
    id: str
    route: str
    side: str
    raid_id: str
    swing_id: str
    broken_level: float
    origin: int
    known: int
    tf: str

@dataclass(frozen=True)
class Imbalance:
    id: str
    tf: str
    side: str
    lo: float
    hi: float
    origin: int
    known: int


def confirmed_imb(bars: list[Bar]) -> list[Imbalance]:
    """Course classic three-bar wick gap; middle bar COLOR is not a gate.

    No promise of eventual fill; a fully formed FVG is known only at the
    close of the third candle. BPR and inverted FVG require separate rules.
    """
    if not bars:return []
    validate_bars(bars,bars[0].tf)
    f=[]
    for i in range(2,len(bars)):
        first,third=bars[i-2],bars[i]
        if third.l>first.h:
            f.append(Imbalance(f'IMB:{third.tf}:LONG:{third.start}',third.tf,'LONG',first.h,third.l,first.start,third.end))
        elif third.h<first.l:
            f.append(Imbalance(f'IMB:{third.tf}:SHORT:{third.start}',third.tf,'SHORT',third.h,first.l,first.start,third.end))
    return f


def imbs_after_trigger(*, bars: list[Bar], trigger_known: int, side: str,
                       tf: str='5m') -> list[Imbalance]:
    """5m IMB candidate after 15m trigger; *not* a completed Route A trade."""
    if tf!='5m' or side not in ('LONG','SHORT'):
        raise ValueError('course 1h-15m-5m branch requires 5m IMB and side')
    return [x for x in confirmed_imb(bars) if x.known>trigger_known and
            x.origin>=trigger_known and x.side==side]


@dataclass(frozen=True)
class BosPaperQuote:
    """Hypothetical NEXT-open market quote; not a filled exchange order."""
    side: str
    known: int
    entry: float
    stop: float
    target: float
    net_rr: float
    raid_id: str
    bos_id: str
    fta_id: str


def quote_bos_next_open(*, raid: Raid, bos: BosEvent, next_bar: Bar,
                        first_1h_fta: Pivot, stop_buffer_frac: float=0.0,
                        costs_per_side: float=0.0007) -> BosPaperQuote:
    """No imaginary in-candle market fill. First 1H target must be preknown.

    Numeric entries here are NEXT bar's open, not the BOS candle close; the
    resulting quote is a research scenario, not guaranteed executable.
    """
    if bos.raid_id!=raid.id or bos.side!=raid.side or bos.route!='C_1H_RAID_3M5M_BOS':
        raise ValueError('no matching raid and BOS')
    if bos.tf not in ('3m','5m') or next_bar.tf!=bos.tf or next_bar.start!=bos.known:
        raise ValueError('no next fully aligned execution bar')
    if first_1h_fta.tf!='1h' or first_1h_fta.known>bos.known:
        raise ValueError('missing future-free 1H FTA')
    if not (0<=stop_buffer_frac<=0.05 and 0<=costs_per_side<=0.05):
        raise ValueError('invalid cost/stop-buffer')
    E=next_bar.o
    S=raid.extreme*(1+stop_buffer_frac if raid.side=='SHORT' else 1-stop_buffer_frac)
    T=first_1h_fta.value
    if raid.side=='SHORT':
        if not (T<E<S):raise ValueError('no natural stop / meaningful downside target')
        raw_win=E-T;raw_loss=S-E
    else:
        if not (S<E<T):raise ValueError('no natural stop / meaningful upside target')
        raw_win=T-E;raw_loss=E-S
    net_win=raw_win-costs_per_side*(E+T)
    net_loss=raw_loss+costs_per_side*(E+S)
    if net_win<=0:raise ValueError('cost-adjusted FTA has no positive reward')
    return BosPaperQuote(raid.side,next_bar.start,E,S,T,net_win/net_loss,raid.id,bos.id,first_1h_fta.id)


@dataclass(frozen=True)
class POI:
    id: str
    tf: str
    side: str
    lo: float
    hi: float
    known: int
    def __post_init__(self):
        if self.lo>=self.hi or self.side not in ('LONG','SHORT'):
            raise ValueError('invalid zone')

@dataclass(frozen=True)
class Evidence:
    kind: str              # LIQUIDITY_CONTACT / POI_CONTACT, VC_IMB / VC_SNR / VC_RB / BOS
    side: str
    known: int
    level: float
    ref_id: str

@dataclass(frozen=True)
class StrongHL:
    id: str
    side: str
    value: float
    contact_ref: str
    confirmation_ref: str
    origin: int
    known: int

@dataclass(frozen=True)
class IDMLevel:
    id: str
    pivot_id: str
    side: str
    value: float
    location: str          # INSIDE_POI / IN_FRONT_OF_POI
    known: int
    poi_id: str
    strong_id: str


def validate_bars(bars: list[Bar], tf: str) -> None:
    if tf not in TF_MS: raise ValueError('unsupported timeframe')
    for i,b in enumerate(bars):
        if b.tf!=tf: raise ValueError('mixed timeframes')
        if i and b.start!=bars[i-1].end:
            raise ValueError('missing/overlapping bars; avoid partial history')


def confirmed_pivots(bars: list[Bar], *, left: int=2, right: int=2) -> list[Pivot]:
    """Emit pivot ONLY at end of right-hand confirmation candle."""
    if left<1 or right<1: raise ValueError('confirm windows >=1')
    if not bars: return []
    validate_bars(bars,bars[0].tf)
    result=[]
    for i in range(left,len(bars)-right):
        b=bars[i]
        neighbors=bars[i-left:i]+bars[i+1:i+right+1]
        for typ,valid,val in [('HIGH',all(b.h>x.h for x in neighbors),b.h),
                              ('LOW',all(b.l<x.l for x in neighbors),b.l)]:
            if valid:
                result.append(Pivot(f'{b.tf}:{typ}:{b.start}',b.tf,typ,val,b.start,bars[i+right].end))
    return sorted(result,key=lambda p:(p.known,p.id))


def confirmed_hourly_raids(bars_1h: list[Bar], pivots_1h: list[Pivot],
                           *, freshness_ms: int=86_400_000) -> list[Raid]:
    """Only fresh, previously CONFIRMED 1H fractals; wick sweep + reclaim.

    The course's previous-session/previous-day rule is approximated by an
    explicit 24h freshness ceiling. Session time zone is not silently guessed.
    """
    validate_bars(bars_1h,'1h')
    if freshness_ms<=0: raise ValueError('freshness must be positive')
    active=[];consumed=set();out=[]
    sorted_p=sorted((p for p in pivots_1h if p.tf=='1h'), key=lambda x:(x.known,x.id))
    k=0
    for b in bars_1h:
        while k<len(sorted_p) and sorted_p[k].known<=b.start:
            active.append(sorted_p[k]);k+=1
        candidates=[]
        for p in active:
            if p.id in consumed or not (0<b.start-p.origin<=freshness_ms):continue
            if p.kind=='HIGH' and b.h>p.value and b.c<p.value:
                candidates.append((p,'SHORT',b.h))
            if p.kind=='LOW' and b.l<p.value and b.c>p.value:
                candidates.append((p,'LONG',b.l))
            # A wick breach without reclaim still consumes the fractal liquidity.
            if (p.kind=='HIGH' and b.h>p.value) or (p.kind=='LOW' and b.l<p.value):
                consumed.add(p.id)
        # Avoid selecting the same bar as opposing liquidity raids: ambiguity.
        if {'LONG','SHORT'}.issubset({side for _,side,_ in candidates}):continue
        for p,side,extreme in candidates:
            out.append(Raid(f'1h:RAID:{side}:{b.start}:{p.id}',side,p.id,p.value,extreme,b.start,b.end))
    return out


def bos_after_raid(bars_ltf: list[Bar], pivots_ltf: list[Pivot],
                   raids_1h: list[Raid], *, max_wait_ms: Optional[int]=None) -> list[BosEvent]:
    """Actual 3m/5m close BOS AFTER a confirmed 1h wick-raid.

    Incremental, no future candles in the signal decision. A known pivot is
    accessible only after its right-hand confirmation bars close. Any bar
    breaching the raided wick invalidates the setup. Default no session TTL:
    its timezone/cutoff is unresolved in the primary course screenshots;
    a caller may explicitly apply max_wait_ms as a RESEARCH assumption.
    """
    if not bars_ltf:return []
    tf=bars_ltf[0].tf
    if tf not in ('3m','5m'):raise ValueError('BOS course path demands 3m or 5m')
    validate_bars(bars_ltf,tf)
    if max_wait_ms is not None and max_wait_ms<=0:raise ValueError('bad wait window')
    pivots=sorted((p for p in pivots_ltf if p.tf==tf),key=lambda x:(x.known,x.id))
    raids=sorted((r for r in raids_1h if r.tf=='1h'),key=lambda x:(x.known,x.id))
    result=[];active=[];pi=0;ri=0;last_high=None;last_low=None
    for j,b in enumerate(bars_ltf):
        while pi<len(pivots) and pivots[pi].known<=b.start:
            p=pivots[pi];pi+=1
            if p.kind=='HIGH':last_high=p
            elif p.kind=='LOW':last_low=p
        while ri<len(raids) and raids[ri].known<=b.start:
            active.append(raids[ri]);ri+=1
        remains=[]
        for r in active:
            if max_wait_ms is not None and b.start-r.known>max_wait_ms:continue
            if (r.side=='SHORT' and b.h>r.extreme) or (r.side=='LONG' and b.l<r.extreme):continue
            if j==0:
                remains.append(r);continue
            p=last_low if r.side=='SHORT' else last_high
            if p is None or p.origin>=b.start or (p.value>=r.liquidity_level if r.side=='SHORT' else p.value<=r.liquidity_level):
                remains.append(r);continue
            prev=bars_ltf[j-1]
            broken=(prev.c>=p.value and b.c<p.value) if r.side=='SHORT' else (prev.c<=p.value and b.c>p.value)
            if broken:
                result.append(BosEvent(f'{tf}:BOS:{r.side}:{b.start}:{r.id}',
                    'C_1H_RAID_3M5M_BOS',r.side,r.id,p.id,p.value,b.start,b.end,tf))
            else:
                remains.append(r)
        active=remains
    return result


def confirmed_strong_hl(*, side: str, extreme: float, origin: int, contact: Evidence,
                        confirmation: Evidence) -> StrongHL:
    """A swing extremum cannot become StrongHL absent contact AND later VC/BOS."""
    if side not in ('LONG','SHORT') or extreme<=0:raise ValueError('bad side/extreme')
    if contact.kind not in ('LIQUIDITY_CONTACT','POI_CONTACT') or confirmation.kind not in ('VC_IMB','VC_SNR','VC_RB','BOS'):
        raise ValueError('missing required course evidence')
    if contact.side!=side or confirmation.side!=side or not (origin<=contact.known<confirmation.known):
        raise ValueError('incorrect side or causal confirmation')
    return StrongHL(f'STRONG:{side}:{origin}:{confirmation.ref_id}',side,extreme,contact.ref_id,
                    confirmation.ref_id,origin,confirmation.known)


def select_idm(*, poi: POI, strong: StrongHL, pivots: list[Pivot],
               as_of: int, entry_tf: str) -> list[IDMLevel]:
    """IDM is confirmed lower-TF fractal liquidity inside OR in front of POI.

    No final BOS/retest required for *candidate* selection; this is not a
    limit order. StrongHL must exist first; price distance ahead of zone not
    filtered (source leaves it qualitative). FTA/risk must be checked later.
    """
    if (poi.tf,entry_tf) not in (('4h','1h'),('1h','15m')):
        raise ValueError('unsupported source IDM hierarchy')
    if poi.side!=strong.side or strong.known>as_of or poi.known>as_of:
        return []
    out=[]
    for p in pivots:
        if p.tf!=entry_tf or p.known>as_of:continue
        if (poi.side=='LONG' and (p.kind!='LOW' or p.value<=strong.value)) or (poi.side=='SHORT' and (p.kind!='HIGH' or p.value>=strong.value)):
            continue
        inside=poi.lo<=p.value<=poi.hi
        ahead=p.value>poi.hi if poi.side=='LONG' else p.value<poi.lo
        if not inside and not ahead:continue
        out.append(IDMLevel(f'IDM:{poi.id}:{p.id}',p.id,poi.side,p.value,
                            'INSIDE_POI' if inside else 'IN_FRONT_OF_POI',max(strong.known,p.known),poi.id,strong.id))
    return out


class PoiLifecycle:
    """Strict first test AFTER zone known; no history retrofits or repeat entries."""
    def __init__(self,poi:POI):
        self.poi=poi;self.state='FRESH';self.tested_at:Optional[int]=None
    def advance(self,bar:Bar)->str:
        if bar.start<self.poi.known:return self.state
        if self.state!='FRESH':return self.state
        broken=(bar.c<self.poi.lo if self.poi.side=='LONG' else bar.c>self.poi.hi)
        if broken:self.state='INVALIDATED'
        elif bar.h>=self.poi.lo and bar.l<=self.poi.hi:
            self.state='TESTED';self.tested_at=bar.end
        return self.state