#!/usr/bin/env python3
"""EMBER Z01: independent causal 4H swing-zone + 5M structure vs first touch.
PAPER-only precommitted structural experiment. DO NOT integrate into C109.
"""
from bisect import bisect_left, bisect_right
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D, InvalidOperation
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import argparse
import csv
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'d05'))
from c89_original_native5m_adaptation_backtest import BASE, _safe_http

MINUTE = 60000
THREE = 3 * MINUTE
FIVE = 5 * MINUTE
FIFTEEN = 15 * MINUTE
HOUR = 60 * MINUTE
FOUR = 4 * HOUR
DAY = 24 * HOUR
TF = (THREE, FIVE, FIFTEEN, FOUR, DAY)
PIVOT = 2
PAD = D("0.15")
STOP_PAD = D("0.35")
RR_MIN = D("1.25")
RISK_MIN = D("0.002")
RISK_MAX = D("0.10")
MAX_ZONE_AGE = 7 * DAY
MAX_WAIT = 4 * HOUR
HOLD = 48 * HOUR
WARMUP = 14 * DAY
EMBARGO = 72 * HOUR
BPS = (14, 25, 40)
SYMBOLS = ("BNBUSDT","XLMUSDT","HBARUSDT","INJUSDT","OPUSDT","ALGOUSDT",
           "CHZUSDT","ICPUSDT","SEIUSDT","PENDLEUSDT","LINKUSDT","UNIUSDT")
WINDOWS = (
    ("WIN_A", "2025-05-05", "2025-07-01", "2025-06-02", 57),
    ("WIN_B", "2026-02-01", "2026-04-06", "2026-03-05", 64),
)
SOURCE_ZIPS = 1452
SOURCE_1M_BARS = 2090880
class Z01Error(ValueError):
    pass

@dataclass(frozen=True)
class Bar:
    start_ms: int
    close_ms: int
    o: D
    h: D
    l: D
    c: D
    v: D

@dataclass(frozen=True)
class Swing:
    kind: str
    price: D
    pivot_close_ms: int
    confirmed_ms: int

@dataclass(frozen=True)
class Zone:
    id: str
    side: str
    created_ms: int
    low: D
    high: D
    pivot: D
    stop: D
    target: D
    atr: D
    range_low: D
    range_high: D
    d1_context: str

def stamp(date):
    return int(datetime.strptime(date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc).timestamp()*1000)

def validate_constants():
    assert len(SYMBOLS)==12 and len(set(SYMBOLS))==12
    assert sum(x[4] for x in WINDOWS)*len(SYMBOLS)==SOURCE_ZIPS
    assert SOURCE_ZIPS*1440==SOURCE_1M_BARS
    for _, first, last, fold, ndays in WINDOWS:
        assert stamp(last)-stamp(first)==ndays*DAY
        assert stamp(first)+WARMUP<stamp(fold)<stamp(last)-EMBARGO
    return True

def price(v):
    try:
        x=D(str(v))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise Z01Error("BAD_SOURCE_PRICE") from e
    if not x.is_finite():
        raise Z01Error("NONFINITE_SOURCE_PRICE")
    return x

def parse_daily_zip(blob, symbol, day, checksum):
    if symbol not in SYMBOLS or day not in {
        (datetime.strptime(w[1],"%Y-%m-%d")+timedelta(days=k)).strftime("%Y-%m-%d")
        for w in WINDOWS for k in range(w[4])
    }:
        raise Z01Error("NON_PRECOMMITTED_SOURCE_DAY")
    stem=f"{symbol}-1m-{day}"
    h=sha256(blob).hexdigest()
    fields=checksum.decode("ascii").strip().split()
    if len(fields)!=2 or fields[0].lower()!=h or fields[1].split("/")[-1]!=stem+".zip":
        raise Z01Error("BINANCE_CHECKSUM_MISMATCH")
    try:
        with ZipFile(BytesIO(blob)) as z:
            members=z.infolist()
            if (len(members)!=1 or members[0].filename!=stem+".csv" or
                members[0].is_dir() or members[0].flag_bits&1 or
                members[0].file_size>30000000):
                raise Z01Error("BAD_ORIGINAL_BINANCE_ZIP_MEMBER")
            raw=z.read(members[0])
    except (BadZipFile, EOFError) as e:
        raise Z01Error("BAD_ZIP") from e
    records=list(csv.reader(raw.decode("utf-8-sig").splitlines()))
    if records and records[0][0].strip().lower() in ("open_time","open time"):
        records=records[1:]
    if len(records)!=1440:
        raise Z01Error("INCOMPLETE_NATIVE1M_DAY")
    base=stamp(day)
    bars=[]
    for i,row in enumerate(records):
        if len(row)!=12:
            raise Z01Error("WRONG_BINANCE_CSV_FORMAT")
        at=base+i*MINUTE
        try:
            open_ms,close_ms,transactions=int(row[0]),int(row[6]),int(row[8])
            o,high,low,c,volume=(price(row[k]) for k in (1,2,3,4,5))
            quote,taker,takerquote=(price(row[k]) for k in (7,9,10))
        except (IndexError, ValueError) as e:
            raise Z01Error("BAD_NATIVE1M_CSV") from e
        if open_ms!=at or close_ms!=at+MINUTE-1 or transactions<0:
            raise Z01Error("NATIVE_1M_CLOCK_DUPLICATE_OR_LOOKAHEAD")
        if not(0<low<=min(o,c)<=max(o,c)<=high and
               min(volume,quote,taker,takerquote)>=0):
            raise Z01Error("IMPOSSIBLE_NATIVE_1M_OHLCV")
        bars.append(Bar(at,at+MINUTE,o,high,low,c,volume))
    return tuple(bars),{
        "symbol":symbol, "date":day, "source_tf":"NATIVE_1M",
        "zip_sha256":h, "csv_sha256":sha256(raw).hexdigest(),
        "bars":len(bars),
        "url":f"{BASE}data/futures/um/daily/klines/{symbol}/1m/{stem}.zip"}

def daily(symbol, day, fetch=_safe_http):
    stem=f"{symbol}-1m-{day}"
    url=f"{BASE}data/futures/um/daily/klines/{symbol}/1m/{stem}.zip"
    blob,check=fetch(url),fetch(url+".CHECKSUM")
    if not isinstance(blob,bytes) or not isinstance(check,bytes) or len(blob)>30000000:
        raise Z01Error("UNAVAILABLE_NATIVE1M_SOURCE")
    return parse_daily_zip(blob,symbol,day,check)

def load_symbol(symbol, window, fetch=_safe_http):
    _,begin,end,_,days=window
    dates=tuple((datetime.strptime(begin,"%Y-%m-%d")+timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(days))
    with ThreadPoolExecutor(max_workers=10) as pool:
        fetched=list(pool.map(lambda d: daily(symbol,d,fetch),dates))
    bars=[];receipts=[]
    for chunk,meta in fetched:
        if bars and bars[-1].close_ms!=chunk[0].start_ms:
            raise Z01Error("GAPPED_ORIGINAL_1M_DAY")
        bars.extend(chunk)
        receipts.append(meta)
    if len(bars)!=days*1440 or bars[0].start_ms!=stamp(begin) or bars[-1].close_ms!=stamp(end):
        raise Z01Error("WRONG_FULL_ORIGINAL_1M_SPAN")
    return tuple(bars),receipts

def aggregate(source, tf):
    """Only exact closed source, UTC aligned. All 3m/5m/15m are from 1m."""
    if tf not in TF or not source or source[0].start_ms%tf:
        raise Z01Error("MISALIGNED_AGGREGATION")
    n=tf//MINUTE
    if len(source)%n:
        raise Z01Error("PARTIAL_HIGHER_TIMEFRAME")
    out=[]
    for start in range(0,len(source),n):
        seq=source[start:start+n]
        if seq[-1].close_ms!=seq[0].start_ms+tf:
            raise Z01Error("NONCLOSED_SOURCE_BAR")
        out.append(Bar(seq[0].start_ms,seq[-1].close_ms,
                       seq[0].o,max(x.h for x in seq),min(x.l for x in seq),
                       seq[-1].c,sum((x.v for x in seq),D(0))))
    return tuple(out)

def swings(source, tf):
    if tf not in (DAY,FOUR,FIVE):
        raise Z01Error("SWING_NOT_REGISTERED")
    out=[]
    for i in range(PIVOT,len(source)-PIVOT):
        a=source[i]; left=source[i-2:i];right=source[i+1:i+3]
        if any(x.close_ms!=y.start_ms for x,y in zip(source[i-2:i+2],source[i-1:i+3])):
            raise Z01Error("NONCONSECUTIVE_SWING_SOURCE")
        known=right[-1].close_ms
        if all(a.h>x.h for x in left) and all(a.h>=x.h for x in right):
            out.append(Swing("HIGH",a.h,a.close_ms,known))
        if all(a.l<x.l for x in left) and all(a.l<=x.l for x in right):
            out.append(Swing("LOW",a.l,a.close_ms,known))
    return tuple(sorted(out,key=lambda z:(z.confirmed_ms,z.kind,z.pivot_close_ms)))

def atr_four(four, known_ms):
    closed=[b for b in four if b.close_ms<=known_ms]
    if len(closed)<15:
        return None
    tail=closed[-15:]
    value=sum((max(b.h-b.l,abs(b.h-prev.c),abs(b.l-prev.c))
               for prev,b in zip(tail,tail[1:])),D(0))/D(14)
    return value if value>0 else None

def d1_structure(confirmed_daily):
    highs=[s for s in confirmed_daily if s.kind=="HIGH"]
    lows=[s for s in confirmed_daily if s.kind=="LOW"]
    if len(highs)<2 or len(lows)<2:
        return "NEUTRAL"
    if highs[-1].price>highs[-2].price and lows[-1].price>lows[-2].price:
        return "UP_HH_HL"
    if highs[-1].price<highs[-2].price and lows[-1].price<lows[-2].price:
        return "DOWN_LH_LL"
    return "NEUTRAL"

def build_zones(four,days):
    hsw=swings(four,FOUR)
    dsw=swings(days,DAY)
    last={}
    zones=[];fail=Counter()
    for s in hsw:
        last[s.kind]=s
        hi,lo=last.get("HIGH"),last.get("LOW")
        if not hi or not lo or lo.price>=hi.price:
            fail["NO_VALID_PREKNOWN_4H_RANGE"]+=1
            continue
        atr=atr_four(four,s.confirmed_ms)
        if atr is None:
            fail["NO_PREKNOWN_4H_ATR"]+=1
            continue
        mid=(lo.price+hi.price)/2
        side="LONG" if s.kind=="LOW" else "SHORT"
        if (side=="LONG" and s.price>=mid) or (side=="SHORT" and s.price<=mid):
            fail["WRONG_PREMIUM_DISCOUNT"]+=1
            continue
        zlow,zhi=s.price-PAD*atr,s.price+PAD*atr
        sl=s.price-STOP_PAD*atr if side=="LONG" else s.price+STOP_PAD*atr
        tp=hi.price-PAD*atr if side=="LONG" else lo.price+PAD*atr
        if not(0<zlow<zhi and ((sl<zlow<tp) if side=="LONG" else (tp<zhi<sl))):
            fail["INVALID_PREKNOWN_4H_STRUCTURE"]+=1
            continue
        daily_asof=[x for x in dsw if x.confirmed_ms<=s.confirmed_ms]
        zones.append(Zone(
            id=f"{side}:{s.pivot_close_ms}:{s.confirmed_ms}:{str(s.price)}",
            side=side,created_ms=s.confirmed_ms,low=zlow,high=zhi,
            pivot=s.price,stop=sl,target=tp,atr=atr,
            range_low=lo.price,range_high=hi.price,
            d1_context=d1_structure(daily_asof)))
    return tuple(zones),dict(fail)

def first_touch(zone, minute, four_closes, begin_ms, end_ms):
    starts=[x.start_ms for x in minute]
    begin=bisect_left(starts,zone.created_ms)
    finish=bisect_left(starts,min(zone.created_ms+MAX_ZONE_AGE,end_ms))
    checked_four={x.close_ms:x for x in four_closes}
    for i in range(begin,finish):
        b=minute[i]
        if b.close_ms in checked_four:
            v=checked_four[b.close_ms]
            if (zone.side=="LONG" and v.c<zone.stop) or (
                zone.side=="SHORT" and v.c>zone.stop):
                return None,"PRE_TOUCH_4H_INVALIDATED"
        if b.h>=zone.low and b.l<=zone.high:
            if not begin_ms<=b.close_ms<end_ms:
                return None,"FIRST_TOUCH_OUTSIDE_EVALUABLE_CLOCK"
            return (i,b.close_ms),"OK"
    return None,"NO_FIRST_TEST_WITHIN_7_DAYS"

def pretrend_and_level(side, touch_ms, s5):
    prior=[x for x in s5 if x.confirmed_ms<=touch_ms]
    highs=[x for x in prior if x.kind=="HIGH"]
    lows=[x for x in prior if x.kind=="LOW"]
    if len(highs)<2 or len(lows)<2:
        return None,"INSUFFICIENT_PRETOUCH_5M_PIVOTS"
    if side=="LONG":
        if not(highs[-1].price<highs[-2].price and
               lows[-1].price<lows[-2].price):
            return None,"NO_OPPOSITE_5M_DOWNTREND"
        return highs[-1].price,"OK"
    if not(highs[-1].price>highs[-2].price and
           lows[-1].price>lows[-2].price):
        return None,"NO_OPPOSITE_5M_UPTREND"
    return lows[-1].price,"OK"

def find_choc(zone,touch_ms,minute,five,s5):
    level,reason=pretrend_and_level(zone.side,touch_ms,s5)
    if level is None:
        return None,reason
    five_closes=[x.close_ms for x in five]
    k=bisect_right(five_closes,touch_ms)
    mins=[x.close_ms for x in minute]
    first=bisect_left(mins,touch_ms)
    last=bisect_right(mins,touch_ms+MAX_WAIT)
    stop_event=None
    for m in minute[first:last]:
        if (zone.side=="LONG" and m.l<=zone.stop) or (
            zone.side=="SHORT" and m.h>=zone.stop):
            stop_event=m.close_ms
            break
    while k<len(five):
        b=five[k]
        if b.close_ms>touch_ms+MAX_WAIT:
            break
        if k:
            old=five[k-1]
            cross=((old.c<=level<b.c and b.c>b.o) if zone.side=="LONG"
                   else (old.c>=level>b.c and b.c<b.o))
            if cross:
                if stop_event is not None and stop_event<=b.close_ms:
                    return None,"STOP_BEFORE_5M_CONFIRMATION"
                return b.close_ms,"OK"
        k+=1
    return None,"NO_5M_CHOC_WITHIN_4H"

def plan(zone,entry):
    if not entry>0:
        return None,"INVALID_NATIVE3M_ENTRY"
    if not(zone.stop<entry<zone.target if zone.side=="LONG"
           else zone.target<entry<zone.stop):
        return None,"H4_SL_TP_WRONG_SIDE"
    r=abs(entry-zone.stop)
    if not RISK_MIN<=r/entry<=RISK_MAX:
        return None,"H4_STOP_RISK_OUTSIDE_BOUNDS"
    if abs(zone.target-entry)/r<RR_MIN:
        return None,"DERIVED_H4_RR_BELOW_1_25"
    return {"entry":entry,"stop":zone.stop,"target":zone.target,"risk":r},"OK"

def simulate(zone,three,entry_pos,reason,source_ms,fold_ms):
    b=three[entry_pos]
    p,why=plan(zone,b.o)
    if p is None:
        # A0 market-at-next-open cannot retroactively vanish after a gap
        # through the preknown H4 stop; conservatively count immediate loss.
        gap_cross=(b.o<=zone.stop if zone.side=="LONG" else b.o>=zone.stop)
        if reason=="A0_FIRST_TOUCH" and gap_cross:
            reference=zone.high if zone.side=="LONG" else zone.low
            original_risk=abs(reference-zone.stop)
            if original_risk<=0:raise Z01Error("BAD_H4_STOP_FOR_GAP")
            sign=D(1) if zone.side=="LONG" else D(-1)
            gross=min(D(-1),sign*(b.o-reference)/original_risk)
            return {"parent_zone_id":zone.id,"side":zone.side,
                "entry_ms":b.start_ms,"exit_ms":b.close_ms,
                "origin_touch_ms":source_ms,
                "fold":"EARLY" if source_ms<fold_ms else "LATE",
                "entry":str(reference),"stop":str(zone.stop),"target":str(zone.target),
                "exit_price":str(b.o),"exit_reason":"PREENTRY_STOP_GAP_LOSS",
                "gross_r":round(float(gross),7),
                "risk_percent":round(float(100*original_risk/reference),6),
                "derived_rr":0.0,"stop_source_tf":"4H","target_source_tf":"4H",
                "entry_model":reason,"d1_context":zone.d1_context,
                "funding_included":False}, "OK"
        return None,why
    e,sl,tp,r=p["entry"],p["stop"],p["target"],p["risk"]
    finish=min(len(three),entry_pos+HOLD//THREE)
    exit_p=None;exit_reason=None;end_ms=None
    for j in range(entry_pos,finish):
        x=three[j]
        if j>entry_pos and three[j-1].close_ms!=x.start_ms:
            raise Z01Error("BROKEN_3M_PRICE_CONTINUITY")
        if zone.side=="LONG":
            if x.o<=sl:exit_p=x.o;exit_reason="STOP_GAP"
            elif x.l<=sl:exit_p=sl;exit_reason="STOP_FIRST_NATIVE3M"
            elif x.o>=tp:exit_p=tp;exit_reason="TP_OPEN"
            elif x.h>=tp:exit_p=tp;exit_reason="4H_TARGET"
        else:
            if x.o>=sl:exit_p=x.o;exit_reason="STOP_GAP"
            elif x.h>=sl:exit_p=sl;exit_reason="STOP_FIRST_NATIVE3M"
            elif x.o<=tp:exit_p=tp;exit_reason="TP_OPEN"
            elif x.l<=tp:exit_p=tp;exit_reason="4H_TARGET"
        if exit_p is not None:
            end_ms=x.close_ms
            break
    if exit_p is None:
        last=three[finish-1]
        exit_p=last.c;end_ms=last.close_ms;exit_reason="TIME_OUT_48H"
    if end_ms>three[-1].close_ms:
        raise Z01Error("RIGHT_CENSORED_3M_EXECUTION")
    sign=D(1) if zone.side=="LONG" else D(-1)
    gross=sign*(exit_p-e)/r
    return {
        "parent_zone_id":zone.id,"side":zone.side,
        "entry_ms":b.start_ms,"exit_ms":end_ms,
        "origin_touch_ms":source_ms,"fold":"EARLY" if source_ms<fold_ms else "LATE",
        "entry":str(e),"stop":str(sl),"target":str(tp),
        "exit_price":str(exit_p),"exit_reason":exit_reason,
        "gross_r":round(float(gross),7),
        "risk_percent":round(float(100*r/e),6),
        "derived_rr":round(float(abs(tp-e)/r),6),
        "stop_source_tf":"4H","target_source_tf":"4H",
        "entry_model":reason,"d1_context":zone.d1_context,
        "funding_included":False,
    },"OK"

def run_symbol(source, symbol, window):
    _,start_date,end_date,fold_date,_=window
    begin_ms,end_ms,fold_ms=stamp(start_date),stamp(end_date),stamp(fold_date)
    if not source or source[0].start_ms!=begin_ms or source[-1].close_ms!=end_ms:
        raise Z01Error("BAD_FULL_UNSEEN_SOURCE_WINDOW")
    three=aggregate(source,THREE)
    five=aggregate(source,FIVE)
    fifteen=aggregate(source,FIFTEEN)
    four=aggregate(source,FOUR)
    days=aggregate(source,DAY)
    s5=swings(five,FIVE)
    zones,rejections=build_zones(four,days)
    opportunities=[]
    for zone in zones:
        event,status=first_touch(zone,source,four,begin_ms+WARMUP,end_ms-EMBARGO)
        if event is not None:
            i,ms=event
            opportunities.append((ms,zone,i))
        else:
            rejections[status]=rejections.get(status,0)+1
    opportunities.sort(key=lambda x:(x[0],x[1].id))
    start3=[b.start_ms for b in three]
    close15=[b.close_ms for b in fifteen]
    minute_closes=[b.close_ms for b in source]
    arm_data={k:[] for k in ("A0_FIRST_TOUCH","B1_5M_CONFIRM_15M_EXEC")}
    busy={k:0 for k in arm_data}
    for ms,zone,origin_i in opportunities:
        root={"symbol":symbol,"touch_ms":ms,"zone_id":zone.id,
              "side":zone.side,"zone_created_ms":zone.created_ms,
              "range_low":str(zone.range_low),"range_high":str(zone.range_high),
              "zone_low":str(zone.low),"zone_high":str(zone.high),
              "source_atr4h":str(zone.atr),
              "4h_stop":str(zone.stop),"4h_tp":str(zone.target),
              "d1_context_at_zone_creation":zone.d1_context}
        for arm in arm_data:
            rec={**root,"arm":arm,"status":"", "trade":None}
            if ms<busy[arm]:
                rec["status"]="CAPACITY_BLOCKED"
            else:
                if arm=="A0_FIRST_TOUCH":
                    k=bisect_left(start3,ms)
                    if k>=len(three) or start3[k]<ms:
                        raise Z01Error("BROKEN_NEXT_3M_ENTRY")
                    confirm_ms=None
                else:
                    confirm_ms,reason=find_choc(zone,ms,source,five,s5)
                    rec["5m_confirmation_ms"]=confirm_ms
                    if confirm_ms is None:
                        rec["status"]=reason
                        arm_data[arm].append(rec)
                        continue
                    j=bisect_left(close15,confirm_ms)
                    if j>=len(close15):
                        raise Z01Error("MISSING_CLOSED_15M_EXECUTION_CLOCK")
                    execute_ms=close15[j]
                    if execute_ms<=ms:
                        raise Z01Error("CONFIRMATION_BEFORE_4H_TOUCH")
                    # 4H stop / target already touched before entry: cancellation, not win
                    interim=source[origin_i:bisect_left(minute_closes,execute_ms)]
                    bad=any((z.l<=zone.stop if zone.side=="LONG" else z.h>=zone.stop)
                            for z in interim)
                    target_hit=any((z.h>=zone.target if zone.side=="LONG" else z.l<=zone.target)
                                   for z in interim)
                    if bad or target_hit:
                        rec["status"]="STOP_BEFORE_ENTRY" if bad else "TARGET_ALREADY_TOUCHED_BEFORE_ENTRY"
                        arm_data[arm].append(rec)
                        continue
                    k=bisect_left(start3,execute_ms)
                    if k>=len(three) or start3[k]!=execute_ms:
                        raise Z01Error("FUTURE_OR_MISSING_NEXT_3M_OPEN")
            trade,reason=simulate(zone,three,k,arm,ms,fold_ms)
            if trade is not None:
                trade["symbol"]=symbol
                rec["trade"]=trade
                rec["status"]="FILLED"
                busy[arm]=trade["exit_ms"]
            else:
                rec["status"]=reason
            arm_data[arm].append(rec)
    if not all(len(arm_data[k])==len(opportunities) for k in arm_data):
        raise Z01Error("MISSING_ZERO_FILL_OPPORTUNITIES")
    return {"symbol":symbol,"source_1m":len(source),
            "confirmed_h4_swing_zones":len(zones),
            "first_touch_opportunities":len(opportunities),
            "zone_rejections":dict(rejections),
            "arms":{a:{"ledger":x,
                       "counts":dict(Counter(v["status"] for v in x)),
                       "trades":[v["trade"] for v in x if v["trade"] is not None]}
                    for a,x in arm_data.items()}},three

def score(ledger,bps):
    trades=[r["trade"] for r in ledger if r["trade"] is not None]
    values=[]
    for t in trades:
        e,sl=D(t["entry"]),D(t["stop"])
        value=D(str(t["gross_r"]))-D(bps)/D(10000)*e/abs(e-sl)
        values.append(float(value))
    profits=sum(max(0,x) for x in values)
    losses=sum(max(0,-x) for x in values)
    return {"opportunities":len(ledger),"fills":len(trades),
            "fill_rate":len(trades)/len(ledger) if ledger else 0,
            "net_r":round(sum(values),6),
            "mean_r_per_first_touch":round(sum(values)/len(ledger),6) if ledger else None,
            "pf":round(profits/losses,6) if losses else None,
            "fold_early_n":sum(t["fold"]=="EARLY" for t in trades),
            "fold_late_n":sum(t["fold"]=="LATE" for t in trades),
            "zero_fills":len(ledger)-len(trades)}

def paper_portfolio_dd(trades,bars3,bps):
    """Explicit constant 1% starting-equity R risk. Marks open 3m worst wick.
    Not real margin, funding, exchange execution, or compounded equity.
    """
    market=tuple(sorted(bars3))
    if not market:return None
    lengths={len(bars3[s]) for s in market}
    if len(lengths)!=1:raise Z01Error("MISSING_PORTFOLIO_3M_CLOCK")
    by={s:sorted([t for t in trades if t["symbol"]==s],
                 key=lambda v:v["entry_ms"]) for s in market}
    pointers={s:0 for s in market}
    realized=D(0);peak=D(100);maxdd=D(0);maxopen=0
    for i in range(next(iter(lengths))):
        stamp=bars3[market[0]][i].close_ms
        mark=D(0);count=0
        for s in market:
            bar=bars3[s][i]
            if bar.close_ms!=stamp:raise Z01Error("3M_PORTFOLIO_CLOCK_MISALIGNMENT")
            z=by[s];k=pointers[s]
            while k<len(z) and z[k]["exit_ms"]<=stamp:
                t=z[k]
                e,sl=D(t["entry"]),D(t["stop"])
                realized+=D(str(t["gross_r"]))-D(bps)/D(10000)*e/abs(e-sl)
                k+=1
            pointers[s]=k
            if k<len(z) and z[k]["entry_ms"]<stamp<z[k]["exit_ms"]:
                t=z[k];e,sl=D(t["entry"]),D(t["stop"])
                risk=abs(e-sl)
                worst=bar.l if t["side"]=="LONG" else bar.h
                sign=D(1) if t["side"]=="LONG" else D(-1)
                mark+=sign*(worst-e)/risk-D(bps)/D(10000)*e/risk
                count+=1
        maxopen=max(maxopen,count)
        equity=D(100)+realized+mark
        peak=max(peak,equity)
        if peak>0:maxdd=max(maxdd,(peak-equity)*D(100)/peak)
    return {"max_adverse_wick_dd_pct":round(float(maxdd),6),
            "max_concurrent_positions":maxopen,
            "capital_policy":"STATIC_1PCT_INITIAL_CAPITAL_PER_TRADE_NOT_LEVERAGED",
            "funding_known":False}

def assess(window,market,manifest):
    outcomes={};bars3={}
    for sym,source in market.items():
        item,three=run_symbol(source,sym,window)
        outcomes[sym]=item;bars3[sym]=three
    names=("A0_FIRST_TOUCH","B1_5M_CONFIRM_15M_EXEC")
    combined={name:[rec for sym in SYMBOLS
                    for rec in outcomes[sym]["arms"][name]["ledger"]]
              for name in names}
    scores={name:{str(b):score(combined[name],b) for b in BPS} for name in names}
    portfolio={name:paper_portfolio_dd([
        r["trade"] for r in combined[name] if r["trade"]], bars3, 25) for name in names}
    base=scores[names[0]]["25"];test=scores[names[1]]["25"]
    high=scores[names[1]]["40"]
    reasons=[]
    if test["fills"]<30:reasons.append("NO_POWER_B1_N_LT_30")
    if min(test["fold_early_n"],test["fold_late_n"])<10:
        reasons.append("NO_POWER_EARLY_LATE_LT_10")
    if test["net_r"]<=0:reasons.append("B1_NEGATIVE_NET_R25")
    if test["pf"] is None or test["pf"]<=1.2:reasons.append("B1_PF25_NOT_GT_1_2")
    if high["pf"] is None or high["pf"]<=1.1:reasons.append("B1_PF40_NOT_GT_1_1")
    if test["net_r"]<=base["net_r"]:reasons.append("B1_NOT_BETTER_THAN_A0")
    if portfolio[names[1]] is None or portfolio[names[1]]["max_adverse_wick_dd_pct"]>=10:
        reasons.append("B1_PORTFOLIO_DD_NOT_LT_10")
    return {
        "window":window[0],"source_count":len(manifest),
        "source_manifest":manifest,
        "source_native1m_bars":sum(len(q) for q in market.values()),
        "by_symbol":outcomes, "scores":scores,"portfolio":portfolio,
        "admission":{"passes":not reasons,"failure_reasons":reasons,
                     "paper_only":True,"live_allowed":False,
                     "prospective_oos":False}
    }

def run():
    validate_constants()
    windows={}
    for window in WINDOWS:
        market={};receipts=[]
        # 1m original source must be used for every TF, no 3m->5m interpolation.
        for sym in SYMBOLS:
            data,meta=load_symbol(sym,window)
            market[sym]=data;receipts.extend(meta)
        result=assess(window,market,receipts)
        if result["source_count"]!=window[4]*len(SYMBOLS):
            raise Z01Error("INCOMPLETE_SOURCE_ARCHIVES")
        windows[window[0]]=result
    return {"schema":"EMBER_Z01_H4_DEALING_RANGE_5M_CONFIRM_VS_FIRST_TOUCH",
        "original_source_1m_zips":sum(x["source_count"] for x in windows.values()),
        "original_source_1m_bars":sum(x["source_native1m_bars"] for x in windows.values()),
        "precommit":"cycles/Z01_PRECOMMIT_STRUCTURAL_4H_SWING_POI_5M_CONFIRM_FIRST_TOUCH_CONTROL_RU.md",
        "windows":windows,
        "both_economic_pass":all(x["admission"]["passes"] for x in windows.values()),
        "paper_only":True,"live_allowed":False,"funding_absent":True,
        "historical_not_forward_oos":True,"orders":[],"fills":[]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True,type=Path)
    args=p.parse_args()
    result=run()
    if result["original_source_1m_zips"]!=SOURCE_ZIPS or result["original_source_1m_bars"]!=SOURCE_1M_BARS:
        raise Z01Error("ORIGINAL_SOURCE_1M_INCOMPLETE")
    target=args.output_dir;target.mkdir(parents=True,exist_ok=True)
    pins={}
    for name,window in result["windows"].items():
        fn=f"Z01_{name}_ORIGINAL_1M_REPLAY.json"
        data=(json.dumps(window,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
        (target/fn).write_bytes(data)
        pins[name]={"filename":fn,"sha256":sha256(data).hexdigest(),"bytes":len(data),
                    "scores":window["scores"],"portfolio":window["portfolio"],
                    "admission":window["admission"]}
    overview={k:v for k,v in result.items() if k!="windows"}
    overview["period_receipts"]=pins
    data=(json.dumps(overview,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    (target/"Z01_SUMMARY.json").write_bytes(data)
    print(json.dumps({"source_zip_count":SOURCE_ZIPS,"source_1m_bars":SOURCE_1M_BARS,
                      "periods":pins,"both_pass":result["both_economic_pass"],
                      "summary_sha256":sha256(data).hexdigest()},ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    main()
