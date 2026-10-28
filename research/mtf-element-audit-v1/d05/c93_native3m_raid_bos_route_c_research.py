"""C93 independent original-native-3m 1H liquidity raid -> 3m BOS PAPER research.

Original Owner Entry By BOS: fresh 1H fractal wick raid (not body break),
3m BOS *after* raid, BOS below raided BSL or above raided SSL, SL beyond
raided 1H liquidity, TP closest unswept 1H liquidity (FTA), no fixed RR.
Crypto translations of undefined session, pip, fractal are ADAPTED_HYPOTHESIS.
Never substitute 5m for native3m. Historical execution only, no orders.
"""
from bisect import bisect_right
from collections import Counter
from decimal import Decimal as D
from dataclasses import dataclass
import hashlib,json
from c21_native3m_source_bridge import (
    Original3mRow,PERIODS,checked_url,read_original_3m,THREE)
from c89_original_native5m_adaptation_backtest import (
    _safe_http,load_original_native5m,STEP,SPLIT,SOURCES,MIN_RISK_PCT,MAX_RISK_PCT)
from c91_continuous_causal_route_a_paper import OHLC,_metrics
from c90_structural_fta_backtest import Swing
class C93Rejected(ValueError):pass
EVIDENCE="ADAPTED_HYPOTHESIS"
PIVOT=2
ATR_BUFFER=D("0.15")
MIN_RR=D("1.25")
COST_BPS=14
HORIZON_3M=240  # 12h, deliberately bounded research-only model
MONTHLY_DAYS=32
MAX_SWING_AGE=24*3600000
H1=3600000
D1=24*H1

def load_3m_source(c21,c73,*,fetch=_safe_http):
    if type(c21) is not bytes or type(c73) is not bytes:
        raise C93Rejected("FROZEN_BOTH_SOURCES_REQUIRED")
    receipts=json.loads(c21)
    if receipts["native_3m_closed"]!=76800 or receipts["author_3m_bos_goldens"]!=0:
        raise C93Rejected("BAD_ORIGINAL_C21_RECEIPT")
    pinned={r["symbol"]:r["new_original_source_zip"] for r in receipts["observations"]}
    markets5,_=load_original_native5m(c73,fetch=fetch)
    result={};manifest=[]
    for sym in sorted(SOURCES):
        native=[]
        for period,expected in zip(PERIODS,pinned[sym]):
            url=checked_url(sym,period)
            original=read_original_3m(url,fetch(url),fetch(url+".CHECKSUM"),
                symbol=sym,period=period)
            if (original.zip_sha!=expected["original_zip_sha256"] or
                original.csv_sha!=expected["original_csv_sha256"] or
                len(original.rows)!=expected["original_native_3m_rows"]):
                raise C93Rejected("C21_ORIGINAL_3M_PIN_DRIFT")
            if native and original.rows[0].start_ms!=native[-1].known_ms:
                raise C93Rejected("3M_SOURCE_JOIN_GAP")
            native.extend(original.rows)
            manifest.append({"symbol":sym,"period":period,"zip_sha256":original.zip_sha,
                             "csv_sha256":original.csv_sha,"rows":len(original.rows)})
        if len(native)!=15360:raise C93Rejected("MISSING_ORIGINAL_NATIVE3M_ROWS")
        # Every 15m candle must match its 5x3m native and 3x5m native OHLCV,
        # independent checksum-linked archive families.
        fives=markets5[sym]
        if len(fives)!=9216:raise C93Rejected("INDEPENDENT_NATIVE5M_MISSING")
        for i in range(3072):
            a=native[i*5:(i+1)*5];b=fives[i*3:(i+1)*3]
            if not (a[0].start_ms==b[0].open_ms and
                    a[-1].known_ms==b[-1].close_ms and
                    (a[0].open,max(x.high for x in a),min(x.low for x in a),
                     a[-1].close,sum((x.volume for x in a),D(0)))==
                    (b[0].o,max(x.h for x in b),min(x.l for x in b),
                     b[-1].c,sum((x.volume for x in b),D(0)))):
                raise C93Rejected("ORIGINAL_3M_5M_15M_PARITY_MISMATCH")
        result[sym]=tuple(native)
    return result,manifest

def _aggregate3(rows,tf):
    if tf not in (THREE,H1,D1) or not rows:
        raise C93Rejected("3M_AGGREGATE_TF_INPUT")
    n=tf//THREE;out=[]
    for i in range(0,len(rows)-n+1,n):
        window=rows[i:i+n]
        if window[0].start_ms%tf or any(a.known_ms!=b.start_ms for a,b in zip(window,window[1:])):
            raise C93Rejected("NATIVE_3M_AGGREGATE_GAP")
        out.append(OHLC(window[0].start_ms,window[-1].known_ms,
            window[0].open,max(x.high for x in window),
            min(x.low for x in window),window[-1].close,
            sum((x.volume for x in window),D(0))))
    return tuple(out)

def _confirmed(arr,tf,cutoff):
    out=[]
    for i in range(PIVOT,len(arr)-PIVOT):
        cur=arr[i];l=arr[i-PIVOT:i];r=arr[i+1:i+PIVOT+1]
        known=r[-1].close_ms
        if known>cutoff:break
        if all(cur.h>x.h for x in l) and all(cur.h>=x.h for x in r):
            out.append(Swing(tf,"HIGH",cur.h,cur.close_ms,known,PIVOT))
        if all(cur.l<x.l for x in l) and all(cur.l<=x.l for x in r):
            out.append(Swing(tf,"LOW",cur.l,cur.close_ms,known,PIVOT))
    return tuple(out)

def _raid(hour,history,swings):
    """Strict wick-only raid of fresh 1H swing formed previous <=24h."""
    v=[]
    for s in reversed(swings):
        if s.confirmed_ms>hour.start_ms or hour.start_ms-s.pivot_closed_ms>MAX_SWING_AGE:
            continue
        if s.kind=="HIGH" and hour.h>s.price and hour.c<s.price:
            if not any(b.h>=s.price for b in history if s.confirmed_ms<=b.start_ms):
                v.append(("SHORT",s))
        if s.kind=="LOW" and hour.l<s.price and hour.c>s.price:
            if not any(b.l<=s.price for b in history if s.confirmed_ms<=b.start_ms):
                v.append(("LONG",s))
    if not v:return None
    # Ambiguous sweep of both directions in same 1h -> NEVER infer trade path.
    if len({side for side,_ in v})!=1:return None
    return v[0]

def _bos_level(three,pivot_side,raid_close_ms):
    swings=_confirmed(three,THREE,raid_close_ms)
    want="HIGH" if pivot_side=="LONG" else "LOW"
    pre=[s for s in swings if s.kind==want and
         0<=raid_close_ms-s.confirmed_ms<=2*H1]
    return max(pre,key=lambda s:s.confirmed_ms) if pre else None

def _fta(raid_close_ms,side,entry_reference,hour,swings):
    candidates=[]
    for s in swings:
        if s.confirmed_ms>raid_close_ms or s.kind!=("HIGH" if side=="LONG" else "LOW"):
            continue
        if side=="LONG" and s.price<=entry_reference:continue
        if side=="SHORT" and s.price>=entry_reference:continue
        if any((b.h>=s.price if side=="LONG" else b.l<=s.price) for b in hour
               if s.confirmed_ms<=b.start_ms and b.close_ms<=raid_close_ms):
            continue
        candidates.append(s)
    return (min(candidates,key=lambda x:x.price) if side=="LONG" else
            max(candidates,key=lambda x:x.price)) if candidates else None

def _atr3m(rows,k):
    if k<15:return None
    z=rows[k-15:k]
    tr=[max(b.high-b.low,abs(b.high-a.close),abs(b.low-a.close))
        for a,b in zip(z,z[1:])]
    value=sum(tr,D(0))/D(len(tr))
    return value if value>0 else None

def _paper_fill(rows,idx,side,stop,target,fta_pivot,raid,*,cost=COST_BPS):
    if cost!=14 or idx>=len(rows) or idx<15:
        raise C93Rejected("UNSUPPORTED_COST_OR_ENTRY")
    entry=rows[idx].open
    if not ((stop<entry<target) if side=="LONG" else (target<entry<stop)):
        return None,"ENTRY_GAP_INVALID_STRUCTURE"
    risk=abs(entry-stop)
    if not MIN_RISK_PCT<=risk/entry<=MAX_RISK_PCT:
        return None,"CRYPTO_STOP_RISK_BOUNDS"
    rr=abs(target-entry)/risk
    if rr<MIN_RR:return None,"DERIVED_RR_ONLY_FILTER"
    if fta_pivot.confirmed_ms>rows[idx].start_ms:
        raise C93Rejected("FUTURE_FTA")
    exit_price=None;reason="";j=idx
    for j in range(idx,min(idx+HORIZON_3M,len(rows))):
        b=rows[j]
        if side=="LONG":
            if b.open<=stop:exit_price=b.open;reason="STOP_GAP";break
            if b.open>=target:exit_price=target;reason="FTA_AT_OPEN";break
            sl=b.low<=stop;tp=b.high>=target
        else:
            if b.open>=stop:exit_price=b.open;reason="STOP_GAP";break
            if b.open<=target:exit_price=target;reason="FTA_AT_OPEN";break
            sl=b.high>=stop;tp=b.low<=target
        if sl:exit_price=stop;reason="STOP_FIRST_SAME_3M";break
        if tp:exit_price=target;reason="1H_FTA";break
    if exit_price is None:exit_price=rows[j].close;reason="TIME_OUT"
    n=((exit_price-entry) if side=="LONG" else (entry-exit_price))/risk
    n-=D(cost)/D(10000)*entry/risk
    return {"side":side,"entry_ms":rows[idx].start_ms,
      "exit_ms":rows[j].known_ms,"entry":str(entry),"stop":str(stop),
      "target":str(target),"fta":str(fta_pivot.price),"derived_rr":round(float(rr),6),
      "net_r":round(float(n),6),"exit_reason":reason,"source_tf":"NATIVE_3M",
      "route":"C_1H_WICK_RAID_NATIVE3M_BOS","evidence":EVIDENCE,
      "raid_extreme":str(raid.h if side=="SHORT" else raid.l),
      "raid_closed_ms":raid.close_ms,
      "fta_confirmed_ms":fta_pivot.confirmed_ms,
      "readiness":"PAPER_ONLY"}, "OK"

def discover(rows,symbol):
    if symbol not in SOURCES or type(rows) is not tuple or len(rows)!=15360 or any(
        type(x) is not Original3mRow or x.symbol!=symbol or
        (i and rows[i-1].known_ms!=x.start_ms)
        for i,x in enumerate(rows)):
        raise C93Rejected("ONLY_VERIFIED_FULL_NATIVE_3M")
    hour=_aggregate3(rows,H1);days=_aggregate3(rows,D1)
    firsts=_confirmed(hour,H1,rows[-1].known_ms)
    three=tuple(OHLC(r.start_ms,r.known_ms,r.open,r.high,r.low,r.close,r.volume) for r in rows)
    out=[];events=Counter();reject=Counter()
    busy_until=0
    for k,raid in enumerate(hour):
        if k<6 or k>=len(hour)-1:continue
        past=hour[:k]
        all_sw=[s for s in firsts if s.confirmed_ms<=raid.start_ms]
        check=_raid(raid,past,all_sw)
        if check is None:continue
        side,swept=check
        d=[x for x in days if x.close_ms<=raid.start_ms]
        if not d or (side=="LONG" and d[-1].c<d[-1].o) or (
                side=="SHORT" and d[-1].c>d[-1].o):
            reject["PREVIOUS_CLOSED_DAILY_CONTEXT_CONFLICT"]+=1;continue
        events["1H_FRESH_WICK_RAID"]+=1
        endindex=bisect_right([x.known_ms for x in rows],raid.close_ms)
        endindex=min(endindex,len(rows)-1)
        bos=_bos_level(three[:endindex],side,raid.close_ms)
        if bos is None:
            reject["NO_CONFIRMED_3M_BOS_PIVOT"]+=1;continue
        fta=_fta(raid.close_ms,side,raid.c,past,all_sw)
        if fta is None:
            reject["NO_UNCONSUMED_1H_FTA"]+=1;continue
        atr=_atr3m(rows,endindex)
        if atr is None:
            reject["ATR_3M_UNAVAILABLE"]+=1;continue
        stop=(raid.l-ATR_BUFFER*atr if side=="LONG" else raid.h+ATR_BUFFER*atr)
        target=(fta.price-ATR_BUFFER*atr if side=="LONG" else fta.price+ATR_BUFFER*atr)
        for j in range(endindex,min(endindex+20,len(rows)-1)):
            candle=rows[j]
            # after a 1h raid, closed 3m must break PREKNOWN swing level.
            if (side=="SHORT" and not candle.close<bos.price) or (
                    side=="LONG" and not candle.close>bos.price):
                continue
            if (side=="SHORT" and not bos.price<raid.h) or (
                    side=="LONG" and not bos.price>raid.l):
                reject["BOS_WRONG_SIDE_OF_RAID"]+=1;break
            events["NATIVE3M_BOS_AFTER_1H_RAID"]+=1
            t,why=_paper_fill(rows,j+1,side,stop,target,fta,raid)
            if t is None:reject[why]+=1;break
            if t["entry_ms"]<busy_until:
                reject["OVERLAPPING_C_POSITION"]+=1;break
            t.update({"symbol":symbol,"raid_fractal_known_ms":swept.confirmed_ms,
              "raid_fractal_level":str(swept.price),
              "bos_level":str(bos.price),"bos_confirmed_ms":bos.confirmed_ms,
              "bos_close_ms":candle.known_ms})
            if not (swept.confirmed_ms<raid.close_ms<
                candle.known_ms==t["entry_ms"]):
                raise C93Rejected("ROUTE_C_LOOKAHEAD")
            out.append(t);busy_until=t["exit_ms"];events["C_PAPER_CLOSED"]+=1
            break
    return {"symbol":symbol,"native3m_bars":len(rows),
            "events":dict(sorted(events.items())),"rejects":dict(sorted(reject.items())),
            "trades":out}

def analyze(markets,manifest):
    if set(markets)!=SOURCES or len(manifest)!=15:
        raise C93Rejected("MISSING_15_ORIGINAL_SOURCE_3M_ZIPS")
    all_={k:discover(v,k) for k,v in sorted(markets.items())}
    trades=sorted((t for z in all_.values() for t in z["trades"]),
                  key=lambda z:(z["entry_ms"],z["symbol"]))
    early=[x for x in trades if x["entry_ms"]<SPLIT and x["exit_ms"]<=SPLIT]
    late=[x for x in trades if x["entry_ms"]>=SPLIT]
    return {"schema":"C93_ISOLATED_NATIVE_3M_ROUTE_C_BOS_RESEARCH",
      "sources":"15 SOURCE_PINNED_BINANCE_USDM_NATIVE3M_ARCHIVES_WITH_5M_PARITY",
      "pinned_manifest":manifest,"full_native_3m_bars":sum(len(v) for v in markets.values()),
      "author_text":"Owner Entry By BOS: 1H fresh wick raid -> native3m BOS -> closest 1H liquidity FTA, SL beyond swept raid",
      "status":EVIDENCE,"author_semantics_certified":False,"fixed_rr_target":False,
      "early_preselected_none":_metrics(early),"time_late":_metrics(late),
      "all":_metrics(trades),"by_symbol":all_,
      "explicit_gaps":"Previous session geography, DST, original IDM distinct model, strongly authored 3m BOS model not authenticated",
      "selection_bias":"All 3m history causally searched; time split is NOT pristine OOS",
      "orders":[],"fills":[],"live_trades":[],"readiness":"PAPER_RESEARCH_NOT_TRADE_READY"}
def dumps(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf8")
