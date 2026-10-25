"""C72 original Binance USD-M 5m source: 3 native5m == 1 original15m;
after C71 provisional NEW 1H POI 15m pattern, first ANY closed 5m
IMB or conservative SNR geometry. No author VALID POI/Trigger/VC/trade.

IMPORTANT: the *.CHECKSUM downloaded from Binance's SAME host only
confirms transport/source consistency, NOT independent authentication.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit
import csv, hashlib,io,re,zipfile
from c16_c08_monthly_daily_htf_lineage import SYMBOLS,SEPT_START,OCT_START,END,DAY
from c21_native3m_source_bridge import PERIODS,STARTS
from c66_native15m_route_a_source_event_chain import _check15
from c71_post_contact_closed_15m_vc_1h_bos_semantic_gate import PostContactSourceGate
from strict_vision_d04 import parse_checksum

FIVE=300000;Q=900000;H=3600000
SHA=re.compile(r"[0-9a-f]{64}\Z")
K_IMB="5M_CLASSIC_IMB_WICK_GAP_SOURCE"
K_SNR_LIQ="5M_SNR_PREKNOWN_LIQUIDITY_SOURCE"
K_SNR_IMB="5M_SNR_PRIOR_IMB_SOURCE"
KINDS=(K_IMB,K_SNR_LIQ,K_SNR_IMB)
STATES=("NO_C71_SINGLE_NEW_1H_POI_15M_SOURCE",
        "NO_5M_VC_SOURCE_FULL_24H_WINDOW",
        "NO_5M_VC_SOURCE_RIGHT_CENSORED",
        "FIRST_5M_SOURCE_OPPOSITE_SIDE",
        "FIRST_5M_SOURCE_TWO_SIDES_AMBIGUOUS",
        "FIRST_5M_SOURCE_MULTIPLE_KINDS_AMBIGUOUS",
        "FIRST_5M_IMB_ALIGNED_NOT_AUTHOR_VC",
        "FIRST_5M_SNR_ALIGNED_NOT_AUTHOR_VC")
class C72Rejected(ValueError):pass

@dataclass(frozen=True)
class Original5m:
    symbol:str
    start_ms:int
    known_ms:int
    open:Decimal
    high:Decimal
    low:Decimal
    close:Decimal
    volume:Decimal
    zip_sha:str
    raw_id:str

@dataclass(frozen=True)
class Original5mArchive:
    symbol:str
    period:str
    zip_sha:str
    csv_sha:str
    url:str
    rows:tuple[Original5m,...]
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class Original5mReview:
    symbol:str
    as_of_ms:int
    rows:tuple[Original5m,...]
    original_archive_shas:tuple[str,...]
    native15m_3_to_1_decimal_equalities:int
    author_5m_vc:bool=False
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

@dataclass(frozen=True)
class Source5mEvent:
    kind:str
    side:str
    pattern_start_ms:int
    known_ms:int
    first_bar_id:str
    last_bar_id:str
    technical_proof:str
    author_volume_confirmation:bool=False
    orders:tuple=()
    trades:tuple=()

@dataclass(frozen=True)
class C72RouteA5mSource:
    symbol:str
    side:str
    source_branch:str|None
    c71_provisional_15m_known_ms:int|None
    source_start_5m_gate_ms:int|None
    first_any_5m_event_known_ms:int|None
    first_any_5m_kinds:tuple[str,...]
    first_any_5m_sides:tuple[str,...]
    state:str
    fully_observed_24h:bool
    author_valid_first_1h_poi_test:bool=False
    author_15m_trigger:bool=False
    author_5m_vc:bool=False
    author_5m_stronghl:bool=False
    author_structural_sl:bool=False
    route_b_idm_used:bool=False
    route_c_raid_bos_used:bool=False
    orders:tuple=()
    fills:tuple=()
    trades:tuple=()
    readiness:str="NOT_TRADE_READY"

def original5m_url(symbol,period):
    if symbol not in SYMBOLS or period not in PERIODS:
        raise C72Rejected("C72_UNTRUSTED_MARKET_PERIOD")
    kind="monthly" if len(period)==7 else "daily"
    url=f"https://data.binance.vision/data/futures/um/{kind}/klines/{symbol}/5m/{symbol}-5m-{period}.zip"
    v=urlsplit(url)
    if v.scheme!="https" or v.netloc!="data.binance.vision" or v.query or v.fragment:
        raise C72Rejected("C72_UNSAFE_5M_URL")
    return url

def _decimal(x):
    try:z=Decimal(x)
    except (TypeError,InvalidOperation,ValueError) as e:
        raise C72Rejected("C72_BAD_DECIMAL") from e
    if not z.is_finite():raise C72Rejected("C72_NONFINITE_DECIMAL")
    return z

def parse_original5m_zip(symbol,period,archive,checksum):
    url=original5m_url(symbol,period)
    if not isinstance(archive,bytes) or not isinstance(checksum,bytes) or not 0<len(archive)<=25000000:
        raise C72Rejected("C72_MISSING_OR_OVERSIZE_ARCHIVE")
    name=url.rsplit("/",1)[-1]
    sha=hashlib.sha256(archive).hexdigest()
    try:actual=parse_checksum(checksum,name)
    except (TypeError,ValueError) as e:raise C72Rejected("C72_INVALID_CHECKSUM") from e
    if actual!=sha:raise C72Rejected("C72_SOURCE_ZIP_CHECKSUM_MISMATCH")
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            infos=z.infolist()
            if (len(infos)!=1 or infos[0].filename!=name[:-4]+".csv" or
                infos[0].is_dir() or infos[0].flag_bits&1 or
                infos[0].file_size>35000000):
                raise C72Rejected("C72_BAD_ZIP_MEMBER")
            raw=z.read(infos[0])
        table=list(csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline="")))
    except (zipfile.BadZipFile, UnicodeError, KeyError, RuntimeError) as e:
        raise C72Rejected("C72_CORRUPT_ORIGINAL_ZIP") from e
    if table and table[0][0].strip().lower()=="open_time":
        if len(table[0])!=12:raise C72Rejected("C72_UNEXPECTED_CSV_HEADER")
        table=table[1:]
    expected=(30*DAY if period=="2026-09" else DAY)//FIVE
    if len(table)!=expected:raise C72Rejected("C72_INCOMPLETE_5M_PERIOD")
    start=STARTS[PERIODS.index(period)]
    rows=[]
    for i,row in enumerate(table):
        if len(row)!=12:raise C72Rejected("C72_WRONG_NATIVE_5M_COLCOUNT")
        at=start+i*FIVE
        try:t=int(row[0]);close=int(row[6]);trades=int(row[8])
        except (ValueError,TypeError) as e:raise C72Rejected("C72_BAD_5M_TIME") from e
        if t!=at or close!=at+FIVE-1 or trades<0:
            raise C72Rejected("C72_GAPPED_REORDERED_OR_UNCLOSED_5M")
        o,h,l,c,v=(_decimal(row[j]) for j in (1,2,3,4,5))
        quote,taker,takerquote=(_decimal(row[j]) for j in (7,9,10))
        if not (0<l<=min(o,c)<=max(o,c)<=h and
                min(v,quote,taker,takerquote)>=0):
            raise C72Rejected("C72_IMPOSSIBLE_ORIGINAL5M_OHLCV")
        rows.append(Original5m(symbol,at,at+FIVE,o,h,l,c,v,sha,sha+":"+str(at)))
    return Original5mArchive(symbol,period,sha,hashlib.sha256(raw).hexdigest(),url,tuple(rows))

def reconcile_original5m_to_native15m(archives,native15m,*,as_of_ms):
    # Compare FULL 32d original archives before as-of cropping; avoids future
    # data sneaking into OHLCV parity for a shorter prefix.
    if (type(archives) is not tuple or len(archives)!=3 or
        type(native15m) is not tuple or type(as_of_ms) is not int or
        as_of_ms%FIVE or not SEPT_START<=as_of_ms<=END):
        raise C72Rejected("C72_UNTRUSTED_5M_RECONCILIATION_INPUT")
    if not native15m:raise C72Rejected("C72_INCOMPLETE_ORIGINAL15M_CONTEXT")
    native=_check15(native15m,as_of_ms=END)
    symbol=native[0].symbol
    if len(native)!=3072 or native[0].start_ms!=SEPT_START:
        raise C72Rejected("C72_INCOMPLETE_ORIGINAL15M_CONTEXT")
    full=[];shas=[]
    for a,period,start in zip(archives,PERIODS,STARTS):
        if (not isinstance(a,Original5mArchive) or a.symbol!=symbol or
            a.period!=period or a.readiness!="NOT_TRADE_READY" or
            a.url!=original5m_url(symbol,period) or
            not SHA.fullmatch(a.zip_sha) or not SHA.fullmatch(a.csv_sha) or
            len(a.rows)!=(30*DAY if period=="2026-09" else DAY)//FIVE):
            raise C72Rejected("C72_WRONG_5M_ORIGINAL_ARCHIVE")
        for i,x in enumerate(a.rows):
            t=start+i*FIVE
            if (not isinstance(x,Original5m) or x.symbol!=symbol or
                x.start_ms!=t or x.known_ms!=t+FIVE or
                x.zip_sha!=a.zip_sha or x.raw_id!=a.zip_sha+":"+str(t)
                or not all(isinstance(y,Decimal) and y.is_finite() for y in
                    (x.open,x.high,x.low,x.close,x.volume))
                or not(0<x.low<=min(x.open,x.close)<=max(x.open,x.close)<=x.high and x.volume>=0)):
                raise C72Rejected("C72_FORGED_5M_RAW_ID_OR_OHLCV")
        full.extend(a.rows);shas.append(a.zip_sha)
    if len(full)!=9216:
        raise C72Rejected("C72_WRONG_32DAY_NATIVE5M_COUNT")
    for i,p in enumerate(native):
        triple=full[i*3:i*3+3]
        source=(triple[0].start_ms,triple[-1].known_ms,triple[0].open,
          max(x.high for x in triple),min(x.low for x in triple),
          triple[-1].close,sum((x.volume for x in triple),Decimal(0)))
        old=(p.start_ms,p.known_at_ms,p.open,p.high,p.low,p.close,p.volume)
        if source!=old:raise C72Rejected("C72_GENUINE_5M_TO_NATIVE15M_DECIMAL_DRIFT")
    return Original5mReview(symbol,as_of_ms,tuple(x for x in full if x.known_ms<=as_of_ms),
                            tuple(shas),3072)

def scan_original5m_source_events(review):
    if (not isinstance(review,Original5mReview) or
        review.readiness!="NOT_TRADE_READY" or review.author_5m_vc or
        review.fills or review.trades):
        raise C72Rejected("C72_UNTRUSTED_ORIGINAL5M_REVIEW")
    bars=review.rows;events=[];gaps=[];levels=[]
    for i,z in enumerate(bars):
        if (z.symbol!=review.symbol or z.known_ms>review.as_of_ms or
            z.known_ms!=z.start_ms+FIVE or z.start_ms%FIVE or
            z.raw_id!=z.zip_sha+":"+str(z.start_ms)):
            raise C72Rejected("C72_UNTRUSTED_5M_SOURCE_BAR")
        # Source 5m strict pre-known local fractals; mark as swept after
        # preceding candle, and never accept pivots formed using future.
        if i:
            previous=bars[i-1]
            levels=[x for x in levels if (
                previous.high<=x[1] if x[0]=="BSL" else previous.low>=x[1])]
        if i>=3:
            a,p,n=bars[i-3:i]
            if p.high>a.high and p.high>n.high:
                levels.append(("BSL",p.high,n.known_ms))
            if p.low<a.low and p.low<n.low:
                levels.append(("SSL",p.low,n.known_ms))
        # Native5m classic wick-only gap: 3 actual fully-closed source bars
        if i>=2:
            a,m=bars[i-2:i]
            if a.high<z.low:
                side="LONG";bottom=a.high;top=z.low
            elif z.high<a.low:
                side="SHORT";bottom=z.high;top=a.low
            else:side=None
            if side:
                events.append(Source5mEvent(K_IMB,side,a.start_ms,z.known_ms,
                    a.raw_id,z.raw_id,"THREE_NATIVE5M_FULLY_CLOSED_WICK_GAP_ONLY"))
                gaps.append((side,bottom,top,z.known_ms))
        if i<2:continue
        a,y,k=bars[i-2:i+1]
        if a.close<a.open and y.close>y.open:
            side="LONG"
            if not(k.close>k.open and k.close>max(a.high,y.high)):continue
        elif a.close>a.open and y.close<y.open:
            side="SHORT"
            if not(k.close<k.open and k.close<min(a.low,y.low)):continue
        else:continue
        # Reject weak bare opposite body pair. SNR requires prior
        # liquidity-or-IMB source interaction known BEFORE pair starts.
        prior=tuple(v for v in levels if v[2]<=a.start_ms)
        liquidity=next((v for v in reversed(prior) if
             (v[0]=="SSL" and side=="LONG" and (a.low<v[1] or y.low<v[1])) or
             (v[0]=="BSL" and side=="SHORT" and (a.high>v[1] or y.high>v[1]))),None)
        old_gap=next((g for g in reversed(gaps) if g[0]==side and
             g[3]<=a.start_ms and (a.high>=g[1] and a.low<=g[2] or
             y.high>=g[1] and y.low<=g[2])),None)
        if liquidity:
            kind=K_SNR_LIQ;proof="THIRD_CLOSED_5M_SNR_PREKNOWN_LOCAL_LIQUIDITY_SOURCE"
        elif old_gap:
            kind=K_SNR_IMB;proof="THIRD_CLOSED_5M_SNR_OLDER_NATIVE5M_IMB_SOURCE"
        else:continue
        events.append(Source5mEvent(kind,side,a.start_ms,k.known_ms,
                    a.raw_id,k.raw_id,proof))
    return tuple(sorted(events,key=lambda e:(e.known_ms,e.kind,e.side,e.first_bar_id)))

def first_any_5m_after_provisional15m(c71,review,events):
    if (not isinstance(c71,PostContactSourceGate) or
        not isinstance(review,Original5mReview) or not isinstance(events,tuple)
        or c71.symbol!=review.symbol or c71.readiness!="NOT_TRADE_READY"
        or c71.author_4h_poi_valid_test or c71.author_1h_poi_valid_test
        or c71.author_1h_trigger or c71.author_15m_trigger
        or c71.author_15m_vc or c71.author_5m_vc or c71.author_1h_bos
        or c71.author_stronghl or c71.route_b_idm_approved or
        c71.route_c_raid_bos_approved or c71.orders or c71.fills or c71.trades
        or review.author_5m_vc or review.fills or review.trades):
        raise C72Rejected("C72_FAKE_OWNER_VC_OR_WRONG_SOURCE")
    bars={z.start_ms:z for z in review.rows}
    for e in events:
        if (not isinstance(e,Source5mEvent) or e.kind not in KINDS or
            e.side not in ("LONG","SHORT") or e.author_volume_confirmation
            or e.orders or e.trades or
            e.pattern_start_ms not in bars or e.known_ms-FIVE not in bars
            or e.known_ms-e.pattern_start_ms!=3*FIVE or
            e.first_bar_id!=bars[e.pattern_start_ms].raw_id or
            e.last_bar_id!=bars[e.known_ms-FIVE].raw_id or
            e.known_ms>review.as_of_ms):
            raise C72Rejected("C72_FORGED_5M_EVENT_OR_FUTURE")
    def out(state,at=None,first=(),full=False,gate=None):
        return C72RouteA5mSource(c71.symbol,c71.original_4h_source_side,
          c71.source_route_a_branch,c71.first_any_confirmed_event_ms,gate,
          at,tuple(sorted({z.kind for z in first})),
          tuple(sorted({z.side for z in first})),state,full)
    # A C71 15m IMB/SNR source is NOT an author-selected 15m Trigger.
    # Only NEW1H source POI branch could even hypothetically need 5m VC.
    branch=c71.source_route_a_branch=="NEW_1H_VC_POI"
    status=c71.state.startswith("FIRST_ANY_NEW1H_POI_15M_")
    at=c71.first_any_confirmed_event_ms
    if not branch or not status or type(at) is not int:
        return out(STATES[0])
    if at%Q or at>review.as_of_ms or at<c71.earliest_event_pattern_start_gate_ms:
        raise C72Rejected("C72_BAD_15M_SOURCE_CLOSE_GATE")
    horizon=at+24*H;end=min(review.as_of_ms,horizon)
    future=tuple(e for e in events if
                 e.pattern_start_ms>=at and e.known_ms<=end)
    full=review.as_of_ms>=horizon
    if not future:return out(STATES[1] if full else STATES[2],full=full,gate=at)
    first_time=min(e.known_ms for e in future)
    first=tuple(e for e in future if e.known_ms==first_time)
    sides={z.side for z in first}
    kinds={z.kind for z in first}
    if len(sides)>1:state=STATES[4]
    elif c71.original_4h_source_side not in sides:state=STATES[3]
    elif len(kinds)>1:state=STATES[5]
    elif kinds=={K_IMB}:state=STATES[6]
    else:state=STATES[7]
    return out(state,first_time,first,full,at)
