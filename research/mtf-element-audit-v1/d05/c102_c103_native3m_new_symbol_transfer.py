#!/usr/bin/env python3
"""C102/C103: frozen C93 native3m Raid→BOS source-only crypto transfer.

Four predeclared models on 5 never-used symbols, 32 closed UTC days.
No live orders, no fixed-RR target, no use of future outcomes as filters.
All symbols/dates/thresholds are precommitted and cannot be optimized in run.
"""
import argparse
import csv
import hashlib
import json
from bisect import bisect_right
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D,InvalidOperation
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile,BadZipFile

from c21_native3m_source_bridge import Original3mRow,THREE
from c89_original_native5m_adaptation_backtest import _safe_http,BASE
from c91_continuous_causal_route_a_paper import OHLC
from c97_robustness_regime_cost_gate import _score
import c93_native3m_raid_bos_route_c_research as c93

class C102Rejected(ValueError): pass
SYMBOLS=("ADAUSDT","AVAXUSDT","DOGEUSDT","LINKUSDT","SUIUSDT")
BEGIN=datetime(2026,9,26,tzinfo=timezone.utc)
END=datetime(2026,10,28,tzinfo=timezone.utc)
BEGIN_MS=int(BEGIN.timestamp()*1000)
END_MS=int(END.timestamp()*1000)
WARMUP_DAYS=7
EMBARGO_HOURS=12
DAY_MS=86400000
COSTS=(14,25,40)
VARIANTS=("BASELINE","V_COST","V_CLOCK","V_BOTH")
MIN_RISK_FRAC=D("0.005")  # engineering 25bps -> <=.5R
MAX_BOS_DELAY_MS=15*60*1000
DAYS=tuple((BEGIN+timedelta(days=i)).strftime("%Y-%m-%d")
           for i in range((END-BEGIN).days))
EXPECTED_ZIPS=160
EXPERIMENT="PRECOMMIT_2026_10_30_C102_C103_OTHER_COINS_NO_PRIOR_C93"
TRAIN_END_MS=int(datetime(2026,10,15,tzinfo=timezone.utc).timestamp()*1000)

def dec(x):
    try:z=D(str(x))
    except (InvalidOperation,TypeError,ValueError) as e:raise C102Rejected("INVALID_PRICE") from e
    if not z.is_finite():raise C102Rejected("NONFINITE_NUMBER")
    return z

def timestamp(date):
    return int(datetime.strptime(date,"%Y-%m-%d").replace(
        tzinfo=timezone.utc).timestamp()*1000)

def native_daily(sym,date,*,fetch=_safe_http):
    if sym not in SYMBOLS or date not in DAYS:
        raise C102Rejected("UNREGISTERED_SYMBOL_OR_DATE")
    name=f"{sym}-3m-{date}"
    url=f"{BASE}data/futures/um/daily/klines/{sym}/3m/{name}.zip"
    data=fetch(url);check=fetch(url+".CHECKSUM")
    if type(data) is not bytes or type(check) is not bytes or not 0<len(data)<=30000000:
        raise C102Rejected("BINANCE_ORIGINAL_SOURCE_MISSING")
    zipsha=hashlib.sha256(data).hexdigest()
    words=check.decode("ascii").strip().split()
    if len(words)!=2 or words[0].lower()!=zipsha or words[1].split("/")[-1]!=name+".zip":
        raise C102Rejected("BINANCE_PROVIDER_CHECKSUM_MISMATCH")
    try:
        with ZipFile(BytesIO(data)) as z:
            members=z.infolist()
            if (len(members)!=1 or members[0].filename!=name+".csv"
                or members[0].is_dir() or members[0].flag_bits&1
                or members[0].file_size>30000000):
                raise C102Rejected("UNSAFE_NATIVE3M_ZIP")
            original=z.read(members[0])
    except (BadZipFile,EOFError) as e:
        raise C102Rejected("BAD_BINANCE_ZIP_BYTES") from e
    lines=list(csv.reader(original.decode("utf-8-sig").splitlines()))
    if lines and lines[0][0].strip().lower() in ("open_time","open time"):
        lines=lines[1:]
    if len(lines)!=480:raise C102Rejected("NOT_FULL_ORIGINAL_NATIVE3M_DAY")
    out=[];at=timestamp(date)
    for i,row in enumerate(lines):
        if len(row)!=12:raise C102Rejected("WRONG_BINANCE_CSV_SCHEMA")
        start=at+i*THREE
        try:
            t0,t1,trades=int(row[0]),int(row[6]),int(row[8])
            o,h,l,c,v=[dec(row[j]) for j in (1,2,3,4,5)]
            quote,taker,taker_quote=[dec(row[j]) for j in (7,9,10)]
        except C102Rejected:
            raise
        except (ValueError,IndexError) as e:
            raise C102Rejected("BAD_NATIVE_TIMESTAMP_OR_CSV") from e
        if t0!=start or t1!=start+THREE-1 or trades<0:
            raise C102Rejected("NATIVE3M_CLOCK_GAP_DUPLICATE_OR_UNCLOSED")
        if not (0<l<=min(o,c)<=max(o,c)<=h and
                min(v,quote,taker,taker_quote)>=0):
            raise C102Rejected("IMPOSSIBLE_ORIGINAL_NATIVE_PRICE_VOLUME")
        out.append(Original3mRow(sym,start,start+THREE,o,h,l,c,v,
                       zipsha+":"+str(start),zipsha))
    return tuple(out),{"symbol":sym,"date":date,"timeframe":"NATIVE_3M",
       "zip_sha256":zipsha,"csv_sha256":hashlib.sha256(original).hexdigest(),
       "bars":len(out),"source":url}

def download_original(*,fetch=_safe_http):
    tasks=[(sym,day) for sym in SYMBOLS for day in DAYS]
    def one(item):
        sym,day=item
        return item,*native_daily(sym,day,fetch=fetch)
    with ThreadPoolExecutor(max_workers=8) as pool:
        result=list(pool.map(one,tasks))
    if len(result)!=EXPECTED_ZIPS:
        raise C102Rejected("MISSING_ORIGINAL_160_SOURCE_ZIPS")
    original={sym:[] for sym in SYMBOLS};proof=[]
    for (sym,date),bars,meta in result:
        group=original[sym]
        if group and group[-1].known_ms!=bars[0].start_ms:
            raise C102Rejected("NATIVE3M_DAY_JOIN_GAP")
        group.extend(bars);proof.append(meta)
    for sym,rows in original.items():
        if len(rows)!=15360 or rows[0].start_ms!=BEGIN_MS or rows[-1].known_ms!=END_MS:
            raise C102Rejected("NOT_CLOSED_32DAY_NATIVE3M_HISTORY")
    return {sym:tuple(v) for sym,v in original.items()},proof

def candidate_events(rows,symbol):
    """Reuse original C93 event definitions verbatim, WITHOUT its whitelist.

    Separate event discovery from independent per-variant busy/overlap accounting.
    Candidate evaluation uses only information confirmed before entry.
    """
    if symbol not in SYMBOLS or type(rows) is not tuple or len(rows)!=15360:
        raise C102Rejected("ONLY_PREREGISTERED_FULL_NATIVE3M")
    if any(type(x) is not Original3mRow or x.symbol!=symbol or
           (i and rows[i-1].known_ms!=x.start_ms)
           for i,x in enumerate(rows)):
        raise C102Rejected("FORGED_NATIVE3M_OR_CLOCK")
    hour=c93._aggregate3(rows,c93.H1)
    days=c93._aggregate3(rows,c93.D1)
    firsts=c93._confirmed(hour,c93.H1,rows[-1].known_ms)
    three=tuple(OHLC(r.start_ms,r.known_ms,r.open,r.high,r.low,r.close,r.volume) for r in rows)
    known=[x.known_ms for x in rows]
    events=[];reject=Counter()
    for k,raid in enumerate(hour):
        if k<6 or k>=len(hour)-1:continue
        past=hour[:k]
        all_sw=[s for s in firsts if s.confirmed_ms<=raid.start_ms]
        check=c93._raid(raid,past,all_sw)
        if check is None:continue
        side,swept=check
        d=[x for x in days if x.close_ms<=raid.start_ms]
        if not d or (side=="LONG" and d[-1].c<d[-1].o) or (
                 side=="SHORT" and d[-1].c>d[-1].o):
            reject["CONFLICT_CLOSED_DAILY_CONTEXT"]+=1;continue
        endindex=min(bisect_right(known,raid.close_ms),len(rows)-1)
        bos=c93._bos_level(three[:endindex],side,raid.close_ms)
        if bos is None:
            reject["NO_PREKNOWN_NATIVE3M_BOS_LEVEL"]+=1;continue
        fta=c93._fta(raid.close_ms,side,raid.c,past,all_sw)
        if fta is None:
            reject["NO_UNSWEPT_1H_FTA"]+=1;continue
        atr=c93._atr3m(rows,endindex)
        if atr is None:
            reject["NO_NATIVE3M_ATR"]+=1;continue
        stop=raid.l-c93.ATR_BUFFER*atr if side=="LONG" else raid.h+c93.ATR_BUFFER*atr
        target=fta.price-c93.ATR_BUFFER*atr if side=="LONG" else fta.price+c93.ATR_BUFFER*atr
        for j in range(endindex,min(endindex+20,len(rows)-1)):
            candle=rows[j]
            if (side=="SHORT" and not candle.close<bos.price) or (
                 side=="LONG" and not candle.close>bos.price):
                continue
            if (side=="SHORT" and not bos.price<raid.h) or (
                 side=="LONG" and not bos.price>raid.l):
                reject["BOS_WRONG_SIDE_OF_RAID"]+=1;break
            # The only structural execution engine is the untouched original C93.
            t,why=c93._paper_fill(rows,j+1,side,stop,target,fta,raid)
            if t is None:
                reject[why]+=1;break
            t.update({"symbol":symbol,"raid_fractal_known_ms":swept.confirmed_ms,
                "raid_fractal_level":str(swept.price),
                "bos_level":str(bos.price),"bos_confirmed_ms":bos.confirmed_ms,
                "bos_close_ms":candle.known_ms})
            if not(swept.confirmed_ms<raid.close_ms<candle.known_ms==t["entry_ms"]):
                raise C102Rejected("ROUTE_C_ORIGINAL_LOOKAHEAD")
            if not BEGIN_MS+WARMUP_DAYS*DAY_MS<=t["entry_ms"]<END_MS-EMBARGO_HOURS*3600000:
                reject["OUTSIDE_PREDECLARED_EVAL_WINDOW"]+=1;break
            if t["exit_ms"]>END_MS:
                reject["RIGHT_CENSORED"]+=1;break
            t["raid_to_bos_minutes"]=(candle.known_ms-raid.close_ms)//60000
            events.append(t)
            break
    events.sort(key=lambda t:(t["entry_ms"],t["symbol"]))
    return events,dict(sorted(reject.items()))

def eligible(t,variant):
    if variant not in VARIANTS:raise C102Rejected("UNREGISTERED_VARIANT")
    if t.get("source_tf")!="NATIVE_3M" or t.get("route")!="C_1H_WICK_RAID_NATIVE3M_BOS":
        raise C102Rejected("INCOMPATIBLE_TRADING_ROUTE")
    e=dec(t["entry"]);stop=dec(t["stop"]);target=dec(t["target"])
    if e<=0 or e==stop or t["bos_close_ms"]!=t["entry_ms"] or t["raid_closed_ms"]>=t["bos_close_ms"]:
        raise C102Rejected("INVALID_PREENTRY_CAUSAL_STRUCTURE")
    if not ((stop<e<target) if t["side"]=="LONG" else (target<e<stop)):
        raise C102Rejected("INVALID_STRUCTURAL_SL_FTA_SIDE")
    risk=abs(e-stop)/e
    cost_ok=risk>=MIN_RISK_FRAC
    clock_ok=0<t["bos_close_ms"]-t["raid_closed_ms"]<=MAX_BOS_DELAY_MS
    return (variant=="BASELINE" or
        (variant=="V_COST" and cost_ok) or
        (variant=="V_CLOCK" and clock_ok) or
        (variant=="V_BOTH" and cost_ok and clock_ok))

def select_sequential(events,variant):
    """No global outcome-based selection. Independently respect C93 symbol busy state."""
    busy=0;chosen=[]
    for t in events:
        if not eligible(t,variant):continue
        if t["entry_ms"]<busy:continue
        chosen.append(t);busy=t["exit_ms"]
    return chosen

def price_stress(t,bps):
    if type(bps) is not int or bps not in COSTS:
        raise C102Rejected("UNREGISTERED_COST_STRESS")
    e=dec(t["entry"]);stop=dec(t["stop"])
    if e<=0 or e==stop:raise C102Rejected("INVALID_STRUCTURAL_RISK")
    v=dec(t["net_r"])-D(bps-14)*e/D(10000)/abs(e-stop)
    return {**t,"net_r":round(float(v),6)}

def score(trades,bps):
    z=sorted((price_stress(t,bps) for t in trades),key=lambda x:(x["entry_ms"],x["symbol"]))
    return _score(z)

def admit(scores):
    z=scores["25"];high=scores["40"]
    reasons=[]
    if z["n"]<30:reasons.append("NO_POWER_N_LT_30")
    if scores.get("fold_early_n",0)<10 or scores.get("fold_late_n",0)<10:
        reasons.append("NO_POWER_TEMPORAL_FOLD")
    if z["sum_r"]<=0:reasons.append("NEGATIVE_NETR25")
    if z["pf"] is None or z["pf"]<=1.2:reasons.append("PF25_NOT_ABOVE_1_2")
    if high["pf"] is None or high["pf"]<=1.1:reasons.append("PF40_NOT_ABOVE_1_1")
    if z["dd_1pct_risk_pct"]>=10:reasons.append("DD_NOT_BELOW_10")
    return {"passes_historical_screen":not reasons,
       "reasons":reasons,"live_approved":False,
       "warning":"Four simultaneously compared research variants still need a third truly unseen OOS."}

def analyze(markets,receipts):
    if set(markets)!=set(SYMBOLS) or len(receipts)!=EXPECTED_ZIPS:
        raise C102Rejected("INCOMPLETE_FROZEN_SOURCE_UNIVERSE")
    if len({(x["symbol"],x["date"]) for x in receipts})!=EXPECTED_ZIPS:
        raise C102Rejected("DUPLICATE_ORIGINAL_SOURCE")
    signals={};rejects={}
    for sym in SYMBOLS:
        signals[sym],rejects[sym]=candidate_events(markets[sym],sym)
    variants={}
    for variant in VARIANTS:
        bysym={sym:select_sequential(signals[sym],variant) for sym in SYMBOLS}
        t=sorted((q for rows in bysym.values() for q in rows),
                 key=lambda x:(x["entry_ms"],x["symbol"]))
        early=[x for x in t if x["entry_ms"]<TRAIN_END_MS]
        late=[x for x in t if x["entry_ms"]>=TRAIN_END_MS]
        scores={str(b):score(t,b) for b in COSTS}
        scores["fold_early_n"]=len(early);scores["fold_late_n"]=len(late)
        fold={"early":{str(b):score(early,b) for b in COSTS},
              "late":{str(b):score(late,b) for b in COSTS}}
        variants[variant]={"trades":t,"scores":scores,
            "by_symbol_n":{s:len(bysym[s]) for s in SYMBOLS},
            "folds":fold,"admission":admit(scores)}
    baseline=variants["BASELINE"]["trades"]
    for model in VARIANTS[1:]:
        for t in variants[model]["trades"]:
            if t not in baseline:
                # Filtered strategy is allowed to expose alternate events after an
                # earlier baseline trade; all must exist in raw pre-entry candidates.
                if t not in signals[t["symbol"]]:
                    raise C102Rejected("VARIANT_FABRICATED_TRADE")
    return {"schema":"EMBER_C102_C103_FIVE_NEW_SYMBOL_ORIGINAL_NATIVE3M_TRANSFER",
       "precommit":"B1_C102_C103_PRECOMMIT_NEW_SYMBOL_NATIVE3M_TRANSFER_RU.md",
       "research_only":True,"sample":"HISTORICAL_NEW_SYMBOL_TRANSFER_NOT_LIVE_OOS",
       "symbols":list(SYMBOLS),"start_utc":"2026-09-26","end_exclusive_utc":"2026-10-28",
       "source_manifest":receipts,"source_zip_count":len(receipts),
       "original_native3m_bars":sum(len(x) for x in markets.values()),
       "candidate_events_by_symbol":{s:len(signals[s]) for s in SYMBOLS},
       "preexecution_rejections":rejects,
       "variants":variants,
       "no_fixed_rr":True,"original_c93_modified":False,
       "orders":[],"fills":[],"live_trades":[],
       "status":"PAPER_ONLY_NOT_TRADE_READY"}

def dump(z):
    return (json.dumps(z,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    market,receipts=download_original()
    z=analyze(market,receipts)
    data=dump(z)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(data)
    print(json.dumps({"archive_count":len(receipts),"native3m_bars":z["original_native3m_bars"],
         "variant_results":{k:{"n":v["scores"]["25"]["n"],
          "netR25":v["scores"]["25"]["sum_r"],
          "pf25":v["scores"]["25"]["pf"],
          "passed":v["admission"]["passes_historical_screen"]}
          for k,v in z["variants"].items()},
         "witness_bytes":len(data),"witness_sha256":hashlib.sha256(data).hexdigest()},
        ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
