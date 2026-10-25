"""C66 owner Route A crypto research: 4H POI source → 1H → native15m.

Owner '2. Entry by IMB & SNR.txt' establishes TWO DISTINCT branches:
  4H POI test → 1H BSL/SSL/IMB TRIGGER → 15m VC [IMB,SNR] entry;
  no 1H trigger → 1H VC [IMB,SNR,RB] = NEW 1H POI → test that POI,
  then 15m trigger → 5m VC, OR 15m VC [SNR,IMB].
A technical 1H C63 SNR/RB/IMB event cannot establish which branch
happened; do not authorize an entry from simply the first post-1H 15m.
15m strict 3-bar gap, SNR anchored in preknown 15m liquidity or older
gap interaction, weaker MB excluded as VC; native CSV raw IDs verified.
Everything is ADAPTED SOURCE GEOMETRY only: no author chart goldens,
owner VC, IDM Route B, Raid→BOS Route C, SL, TP, orders, fills or trades.
"""
from dataclasses import dataclass
from decimal import Decimal
import re
from c16_c08_monthly_daily_htf_lineage import NativeKline,TF_MS,SEPT_START,SYMBOLS
from c63_closed_4h_source_contact_to_first_any_1h_reaction import SourceReactionChain
Q=TF_MS["15m"]
H=TF_MS["1h"]
WINDOW=24*H
HEX=re.compile(r"[0-9a-f]{64}:[0-9]{13}\Z")

@dataclass(frozen=True)
class Source15Event:
    kind:str
    side:str
    pattern_start_ms:int
    known_ms:int
    first_original15m_id:str
    last_original15m_id:str
    source_reference_ms:int|None
    proof:str
    author_volume_confirmation:bool=False
    author_entry:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class RouteA15SourceReview:
    symbol:str
    technical_4h_side:str
    source_4h_first3m_contact_id:str|None
    first_closed_1h_source_event_ms:int|None
    selected_source_1h_event_side:str|None
    route_a_branch_status:str
    first_any_native15m_technical_event_ms:int|None
    first_any_native15m_events:tuple[Source15Event,...]
    first_any_native15m_side:str|None
    observation_end_ms:int|None
    window_full:bool
    route_a_author_4h_poi_test:bool=False
    route_a_author_1h_trigger:bool=False
    route_a_author_new_1h_vc_poi_test:bool=False
    route_a_author_15m_vc:bool=False
    route_b_idm_evaluated:bool=False
    route_c_raid_bos_evaluated:bool=False
    author_15m_stronghl:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

KINDS=("15M_CLASSIC_IMB_SOURCE_ONLY","15M_SNR_LIQUIDITY_SOURCE_ONLY",
       "15M_SNR_PRIOR_IMB_SOURCE_ONLY")
STATES=("NO_4H_FIRST_SOURCE_TOUCH","AMBIGUOUS_1H_SOURCE_DIRECTION",
        "NO_FIRST_CLOSED_1H_SOURCE_EVENT","OPPOSITE_1H_SOURCE_DIRECTION",
        "1H_KIND_UNRESOLVED_NO_OWNER_TRIGGER_VC",
        "FIRST_ANY_15M_SOURCE_SAME_DIRECTION",
        "FIRST_ANY_15M_SOURCE_OPPOSITE_DIRECTION",
        "FIRST_ANY_15M_SOURCE_BOTH_DIRECTIONS",
        "NO_15M_SOURCE_CANDIDATE_FULL_WINDOW",
        "NO_15M_SOURCE_CANDIDATE_RIGHT_CENSORED")

def _check15(rows,*,as_of_ms):
    if (not isinstance(rows,tuple) or not rows or type(as_of_ms) is not int or
        as_of_ms%Q or not (SEPT_START<=as_of_ms<=rows[-1].known_at_ms)):
        raise ValueError("C66_INVALID_OR_UNCLOSED_NATIVE15M_SOURCE")
    symbol=rows[0].symbol
    prev=None
    for v in rows:
        if (not isinstance(v,NativeKline) or v.tf!="15m" or v.symbol!=symbol
            or symbol not in SYMBOLS or type(v.start_ms) is not int
            or v.start_ms%Q or v.known_at_ms!=v.start_ms+Q
            or (prev is not None and v.start_ms!=prev)
            or not isinstance(v.origin_zip_sha256,str) or
            not re.fullmatch(r"[a-f0-9]{64}",v.origin_zip_sha256) or
            v.origin_raw_row_id!=v.origin_zip_sha256+":"+str(v.start_ms)
            or not all(isinstance(z,Decimal) and z.is_finite() for z in
                (v.open,v.high,v.low,v.close,v.volume))
            or not (0<v.low<=min(v.open,v.close)<=max(v.open,v.close)<=v.high and v.volume>=0)):
            raise ValueError("C66_FORGED_NATIVE15M_OHLCV_ID_OR_TIME")
        prev=v.known_at_ms
    return tuple(x for x in rows if x.known_at_ms<=as_of_ms)

def scan_original15m_source(rows,*,as_of_ms):
    bars=_check15(rows,as_of_ms=as_of_ms)
    levels=[]
    gaps=[]
    events=[]
    for i,x in enumerate(bars):
        if i:
            previous=bars[i-1]
            levels=[z for z in levels if (
                previous.high<=z[1] if z[0]=="BSL" else previous.low>=z[1])]
        if i>=3:
            a,p,z=bars[i-3:i]
            if p.high>a.high and p.high>z.high:
                levels.append(("BSL",p.high,z.known_at_ms))
            if p.low<a.low and p.low<z.low:
                levels.append(("SSL",p.low,z.known_at_ms))
        # Only the levels and gaps already known when this first bar starts.
        if i>=2:
            a,m=bars[i-2:i]
            if a.high<x.low:side="LONG";bottom=a.high;top=x.low
            elif x.high<a.low:side="SHORT";bottom=x.high;top=a.low
            else:side=None
            if side:
                events.append(Source15Event("15M_CLASSIC_IMB_SOURCE_ONLY",side,
                    a.start_ms,x.known_at_ms,a.origin_raw_row_id,
                    x.origin_raw_row_id,None,"THREE_FULLY_CLOSED_15M_WICK_GAP"))
                gaps.append((side,bottom,top,x.known_at_ms))
        if i<2:continue
        # SNR = two opposing bodies + the NEXT confirming bar.
        # The pair must START after a liquidity/gap witness was known.
        a,y,z=bars[i-2:i+1]
        if a.close<a.open and y.close>y.open:
            side="LONG"
            if not(z.close>z.open and z.close>max(a.high,y.high)):continue
        elif a.close>a.open and y.close<y.open:
            side="SHORT"
            if not(z.close<z.open and z.close<min(a.low,y.low)):continue
        else:continue
        # This scan's current levels[] may contain pivots only confirmed at
        # the second pair candle. Only use known BEFORE first pair started.
        # A pivot can be marked swept by current pair; reconstructed prior
        # knowledge is conserved using levels snapshots below.
        pivots=_levels_known_before_pair(bars,i-2)
        liquidity=next((
            known for kind,price,known in reversed(pivots)
            if ((side=="LONG" and kind=="SSL" and
                 (a.low<price or y.low<price)) or
                (side=="SHORT" and kind=="BSL" and
                 (a.high>price or y.high>price)))
        ),None)
        prior_gap=next((
            g for g in reversed(gaps)
            if g[0]==side and g[3]<=a.start_ms and
               any(t.high>=g[1] and t.low<=g[2] for t in (a,y))
        ),None)
        if liquidity is not None:
            kind="15M_SNR_LIQUIDITY_SOURCE_ONLY";reference=liquidity
            proof="OPPOSITE_PAIR_THIRD_CLOSE_WITH_PREKNOWN_LIQUIDITY_TEST"
        elif prior_gap is not None:
            kind="15M_SNR_PRIOR_IMB_SOURCE_ONLY";reference=prior_gap[3]
            proof="OPPOSITE_PAIR_THIRD_CLOSE_WITH_OLDER_3BAR_GAP_TEST"
        else:
            continue # MB weaker without independent source work; never VC
        events.append(Source15Event(kind,side,a.start_ms,z.known_at_ms,
            a.origin_raw_row_id,z.origin_raw_row_id,reference,proof))
    return tuple(sorted(events,key=lambda e:(e.known_ms,e.kind,e.side,e.first_original15m_id)))

def _levels_known_before_pair(bars,start_idx):
    """Strict three-bar source fractal preknown at pair start, unswept
    by all candles AFTER pivot became known and BEFORE first pair bar.
    """
    known=[]
    for j in range(3,start_idx+1):
        a,p,z=bars[j-3:j]
        if p.high>a.high and p.high>z.high:
            known.append(("BSL",p.high,z.known_at_ms))
        if p.low<a.low and p.low<z.low:
            known.append(("SSL",p.low,z.known_at_ms))
    return tuple((kind,price,known_ms) for kind,price,known_ms in known
        if all((v.high<=price if kind=="BSL" else v.low>=price)
             for v in bars[:start_idx] if v.start_ms>=known_ms))

def route_a_15m_source_review(chain,events,*,as_of_ms):
    if (not isinstance(chain,SourceReactionChain) or chain.symbol not in SYMBOLS
        or type(as_of_ms) is not int or as_of_ms%Q or
        not isinstance(events,tuple) or
        chain.has_author_selected_poi or chain.has_author_first_valid_poi_test
        or chain.has_author_vc_or_bos or chain.has_author_stronghl
        or chain.author_trade_approved or chain.orders or chain.trades
        or chain.readiness!="NOT_TRADE_READY"):
        raise ValueError("C66_FORGED_4H_1H_CONTEXT_OR_AUTHOR_PROMOTION")
    for e in events:
        if (not isinstance(e,Source15Event) or e.kind not in KINDS or
            e.side not in ("LONG","SHORT") or
            type(e.known_ms) is not int or type(e.pattern_start_ms) is not int
            or e.known_ms>as_of_ms or e.known_ms%Q or
            e.pattern_start_ms%Q or e.pattern_start_ms>=e.known_ms or
            e.known_ms-e.pattern_start_ms!=3*Q or
            not isinstance(e.first_original15m_id,str) or
            not isinstance(e.last_original15m_id,str) or
            not HEX.fullmatch(e.first_original15m_id) or
            not HEX.fullmatch(e.last_original15m_id) or
            int(e.first_original15m_id.split(":")[1])!=e.pattern_start_ms or
            int(e.last_original15m_id.split(":")[1])!=e.known_ms-Q or
            e.author_volume_confirmation or e.author_entry or e.orders or e.trades):
            raise ValueError("C66_FUTURE_OR_FORGED_15M_SOURCE_EVENT")
    side=chain.original_4h_side
    known=chain.first_any_source_event_known_ms
    direction=chain.first_any_side
    def out(status,first=None,items=(),event_side=None,end=None,full=False):
        return RouteA15SourceReview(chain.symbol,side,
            chain.original_first3m_contact_id,known,direction,status,
            first,items,event_side,end,full)
    if chain.original_first3m_contact_id is None:
        return out(STATES[0])
    if direction=="BOTH":return out(STATES[1])
    if known is None:return out(STATES[2])
    if (known>as_of_ms or not chain.first_any_source_events or
        any(x.fully_known_ms!=known or x.side!=direction or
            x.is_author_vc or x.is_author_bos or x.is_author_stronghl or
            x.orders or x.trades or
            x.first_pattern_bar_start_ms<chain.first3m_contact_closed_ms
            for x in chain.first_any_source_events)):
        raise ValueError("C66_FORGED_OR_FUTURE_C63_FIRST_ANY")
    if direction!=side:return out(STATES[3])
    # Important: this is SOURCE 1H event, not a certified owner trigger
    # or owner VC POI. A distinction is deliberately NOT inferred.
    end=min(as_of_ms,known+WINDOW)
    after=[e for e in events if e.pattern_start_ms>=known and e.known_ms<=end]
    first=min((e.known_ms for e in after),default=None)
    earliest=tuple(e for e in after if e.known_ms==first) if first is not None else ()
    sides={e.side for e in earliest}
    label=(STATES[7] if len(sides)>1 else
       STATES[5] if side in sides else STATES[6]) if earliest else (
       STATES[8] if as_of_ms>=known+WINDOW else STATES[9])
    event_side="BOTH" if len(sides)>1 else next(iter(sides)) if sides else None
    return out(label,first,earliest,event_side,end,as_of_ms>=known+WINDOW)
