"""C98: PRECOMMITTED Oct03-Oct26 original Binance paper forward-history check.

Frozen parameters BEFORE any downloaded Oct03+ data. Source-only:
* Binance USD-M native5m daily for A/B; native3m daily for C.
* Full Apr01 start for A/B, Sep25-Oct26 rolling32d for C93.
* Every ZIP + provider CHECKSUM + CSV SHA + UTC exact OHLCV, parity.
* No changes to A/B/C event/stop/FTA/RR models; no live orders.
This is additional historically reserved evidence, NOT truly prospective live
forward data and NOT proof of stable return.
"""
from calendar import monthrange
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D,InvalidOperation
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile,BadZipFile
import csv,json
from c89_original_native5m_adaptation_backtest import (
    BASE,Bar,STEP,SOURCES,_safe_http,parse_original5m_csv,C89Rejected)
from c21_native3m_source_bridge import Original3mRow,THREE
from c92_extended_original_native5m_full_continuous import load_extended_original
from c93_native3m_raid_bos_route_c_research import load_3m_source,discover as discover_c
from c91_continuous_causal_route_a_paper import discover_symbol as discover_a
from c94_idm_limit_route_b_research import discover as discover_b
from c96_canonical_history_warmup_invariance import (
    validate_calendar,_complete,A_EMBARGO,B_EMBARGO)
from c97_robustness_regime_cost_gate import _cost_case,_score
class C98Rejected(ValueError):pass
START=datetime(2026,10,3,tzinfo=timezone.utc)
END=datetime(2026,10,27,tzinfo=timezone.utc)
START_MS=int(START.timestamp()*1000)
END_MS=int(END.timestamp()*1000)
MAX_ZIP=30000000
EXPECTED_SYMBOLS=tuple(sorted(SOURCES))
DAYS=tuple((START+timedelta(days=i)).strftime("%Y-%m-%d") for i in range((END-START).days))
TF=("5m","3m")
EXPECTED_MONTH_ARCHIVES=40
EXPECTED_NEW_ARCHIVES=len(EXPECTED_SYMBOLS)*len(DAYS)*len(TF)
MIN_OOS_N=10
MAX_DD=D("10")
MIN_PF=D("1.2")
EVIDENCE="PRECOMMITTED_2026_10_28_PAPER_SOURCE_ONLY"
def ms(date):
    return int(datetime.strptime(date,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
def _dec(x):
    try: v=D(x)
    except (TypeError,ValueError,InvalidOperation) as e:raise C98Rejected("INVALID_NUMERIC") from e
    if not v.is_finite():raise C98Rejected("NONFINITE_NUMERIC")
    return v

def daily_zip(sym,tf,date,*,fetch=_safe_http):
    if sym not in SOURCES or tf not in TF or date not in DAYS:
        raise C98Rejected("UNREGISTERED_RESEARCH_COIN_TF_DAY")
    name=f"{sym}-{tf}-{date}"
    url=f"{BASE}data/futures/um/daily/klines/{sym}/{tf}/{name}.zip"
    data=fetch(url)
    checksum=fetch(url+".CHECKSUM")
    if type(data) is not bytes or type(checksum) is not bytes or not 0<len(data)<=MAX_ZIP:
        raise C98Rejected("MISSING_OR_OVERSIZED_ORIGINAL_BINANCE_DAILY_ZIP")
    checksum_fields=checksum.decode("ascii").strip().split()
    digest=sha256(data).hexdigest()
    if (len(checksum_fields)!=2 or checksum_fields[0].lower()!=digest
            or checksum_fields[1].split("/")[-1]!=name+".zip"):
        raise C98Rejected("BINANCE_DAILY_PROVIDER_CHECKSUM_FAIL")
    try:
        with ZipFile(BytesIO(data)) as z:
            info=z.infolist()
            if (len(info)!=1 or info[0].filename!=name+".csv"
                    or info[0].is_dir() or info[0].flag_bits&1
                    or info[0].file_size>MAX_ZIP):
                raise C98Rejected("UNSAFE_ZIP_OR_SOURCE_MEMBER")
            raw=z.read(info[0])
    except BadZipFile as e:raise C98Rejected("CORRUPT_OFFICIAL_ZIP") from e
    start=ms(date)
    step=STEP if tf=="5m" else THREE
    expected=86400000//step
    # Binance close_time required; no partial/unclosed bars.
    lines=list(csv.reader(raw.decode("utf-8-sig").splitlines()))
    if lines and lines[0][0].strip().lower() in ("open_time","open time"):
        lines=lines[1:]
    if len(lines)!=expected:raise C98Rejected("PARTIAL_OFFICIAL_DAILY_HISTORY")
    out=[]
    for i,r in enumerate(lines):
        if len(r)!=12:raise C98Rejected("WRONG_ORIGINAL_BINANCE_CSV_COLUMNS")
        at=start+i*step
        try:
            orig_open=int(r[0]);close_stamp=int(r[6]);trades=int(r[8])
        except (ValueError,TypeError) as e:
            raise C98Rejected("NATIVE_DAILY_CLOCK_OR_TRADE_COUNT_INVALID") from e
        if orig_open!=at or close_stamp!=at+step-1 or trades<0:
            raise C98Rejected("NATIVE_DAILY_UNCLOSED_GAP_OR_REORDER")
        o,h,l,c,v=(_dec(r[j]) for j in (1,2,3,4,5))
        quote,taker,taker_quote=(_dec(r[j]) for j in (7,9,10))
        if not (0<l<=min(o,c)<=max(o,c)<=h and min(v,quote,taker,taker_quote)>=0):
            raise C98Rejected("IMPOSSIBLE_ORIGINAL_NATIVE_PRICE_VOLUME")
        if tf=="5m":
            out.append(Bar(at,o,h,l,c,v))
        else:
            out.append(Original3mRow(sym,at,at+step,o,h,l,c,v,
                             digest+":"+str(at),digest))
    return tuple(out),{"symbol":sym,"timeframe":tf,"date":date,
                        "zip_sha256":digest,"csv_sha256":sha256(raw).hexdigest(),
                        "bars":len(out),"url":url,"readiness":"PAPER_ORIGINAL_ONLY"}

def load_new_original(*,fetch=_safe_http):
    tasks=[(sym,tf,date) for sym in EXPECTED_SYMBOLS for tf in TF for date in DAYS]
    def one(t):
        row,meta=daily_zip(*t,fetch=fetch)
        return t,row,meta
    with ThreadPoolExecutor(max_workers=10) as pool:
        found=list(pool.map(one,tasks))
    if len(found)!=EXPECTED_NEW_ARCHIVES:raise C98Rejected("NOT_ALL_NEW_SOURCE_ARCHIVES")
    outputs={(sym,tf):[] for sym in EXPECTED_SYMBOLS for tf in TF}
    receipts=[]
    for (sym,tf,date),rows,meta in found:
        arr=outputs[(sym,tf)]
        if arr:
            old_end=(arr[-1].close_ms if tf=="5m" else arr[-1].known_ms)
            new_start=(rows[0].open_ms if tf=="5m" else rows[0].start_ms)
            if old_end!=new_start:raise C98Rejected("MULTIDAY_ORIGINAL_JOIN_GAP")
        arr.extend(rows);receipts.append(meta)
    return {k:tuple(v) for k,v in outputs.items()},receipts

def verify_daily_parity(x3,x5,symbol):
    if len(x3)!=(END_MS-START_MS)//THREE or len(x5)!=(END_MS-START_MS)//STEP:
        raise C98Rejected("ORIGINAL_3M_5M_SOURCE_PERIOD_MISMATCH")
    eq=0
    for i in range(len(x5)//3):
        p=x3[i*5:(i+1)*5];q=x5[i*3:(i+1)*3]
        lhs=(p[0].start_ms,p[-1].known_ms,p[0].open,
             max(v.high for v in p),min(v.low for v in p),
             p[-1].close,sum((v.volume for v in p),D(0)))
        rhs=(q[0].open_ms,q[-1].close_ms,q[0].o,max(v.h for v in q),
             min(v.l for v in q),q[-1].c,sum((v.volume for v in q),D(0)))
        if lhs!=rhs:raise C98Rejected(f"INDEPENDENT_3M_5M_NATIVE15M_MISMATCH_{symbol}_{i}")
        eq+=1
    return eq

def _only_forward(rows):
    return [x for x in rows if START_MS<=x["entry_ms"]<END_MS
            and x["exit_ms"]<=END_MS]
def _baseline_compare(baseline,fresh,embargo):
    def signature(x):
        return tuple((k,x.get(k)) for k in ("symbol","route","entry_ms","exit_ms",
                   "entry","stop","target","fta","derived_rr","net_r","exit_reason"))
    def eligible(x):
        return x["entry_ms"]+embargo<=START_MS and x["exit_ms"]<=START_MS
    old=sorted((signature(x) for x in baseline if eligible(x)),key=repr)
    new=sorted((signature(x) for x in fresh if eligible(x)),key=repr)
    if old!=new:raise C98Rejected("PREVIOUS_FROZEN_RESEARCH_EVENTS_CHANGED")
    return {"prior_source_trades_unchanged":len(old),"comparison_exact":True}
def _score_scenarios(trades):
    return {str(k):_score([_cost_case(t,k) for t in trades]) for k in (14,25,40)}
def _admission(test):
    s=test["25"]
    reasons=[]
    if s["n"]<MIN_OOS_N:reasons.append("OOS_SAMPLE_BELOW_10")
    if s["sum_r"]<=0:reasons.append("OOS_AFTER_COST_NEGATIVE")
    if s["pf"] is None or D(str(s["pf"]))<=MIN_PF:reasons.append("OOS_PF_BELOW_1_2")
    if D(str(s["dd_1pct_risk_pct"]))>=MAX_DD:reasons.append("OOS_DD_ABOVE_10_PCT")
    return {"passes_new_oct_historical_screen":not reasons,
        "reasons":reasons,"live_approved":False,
        "warning":"One new 24-day historical period does not prove stable future edge."}

def run(c73,c21,old_a,old_b,*,fetch=_safe_http):
    if type(c73) is not bytes or type(c21) is not bytes:
        raise C98Rejected("FROZEN_HISTORICAL_SOURCE_REQUIRED")
    # Rehydrate old exact pinned 40 archive 5m Apr-Oct02; immutable route code.
    history,meta=load_extended_original(c73,fetch=fetch)
    new,receipts=load_new_original(fetch=fetch)
    if len(receipts)!=EXPECTED_NEW_ARCHIVES:
        raise C98Rejected("HOLDOUT_ARCHIVES_INCOMPLETE")
    five_all={};report={}
    for sym in EXPECTED_SYMBOLS:
        ext=new[(sym,"5m")]
        if history[sym][-1].close_ms!=ext[0].open_ms or ext[-1].close_ms!=END_MS:
            raise C98Rejected("APR_HISTORY_AND_OCT_HOLDOUT_NOT_CONTIGUOUS")
        five_all[sym]=history[sym]+ext
        validate_calendar(five_all[sym],sym,minimum_end=END_MS)
        eq=verify_daily_parity(new[(sym,"3m")],ext,sym)
        report[sym]={"native15m_3m5m_equalities":eq,
                     "new_native5m_bars":len(ext),
                     "new_native3m_bars":len(new[(sym,"3m")])}
    # Read original native 3m old period C21 SHA-pinned Sep+Oct1/2.
    old3,old3_manifest=load_3m_source(c21,c73,fetch=fetch)
    new_results={"A":[],"B":[],"C":[]}
    prev_checks={"A":{},"B":{}}
    for sym in EXPECTED_SYMBOLS:
        src=five_all[sym]
        a=discover_a(src,sym)
        b=discover_b(src,sym)
        prev_checks["A"][sym]=_baseline_compare(
           old_a["by_symbol"][sym]["trades"],a["trades"],A_EMBARGO)
        prev_checks["B"][sym]=_baseline_compare(
           old_b["by_symbol"][sym]["trades"],b["trades"],B_EMBARGO)
        new_results["A"].extend(_only_forward(a["trades"]))
        new_results["B"].extend(_only_forward(b["trades"]))
        merged3=old3[sym]+new[(sym,"3m")]
        if merged3[-1].known_ms!=END_MS:raise C98Rejected("ORIGINAL_NATIVE3M_END_UNCLOSED")
        rolling=merged3[-(32*24*60//3):]
        if rolling[0].start_ms!=END_MS-32*86400000 or len(rolling)!=15360:
            raise C98Rejected("C93_32D_WARMUP_WRONG")
        c=discover_c(rolling,sym)
        new_results["C"].extend(_only_forward(c["trades"]))
    result={}
    for model,trades in new_results.items():
        trades.sort(key=lambda t:(t["entry_ms"],t["symbol"]))
        costs=_score_scenarios(trades)
        result[model]={"trades":trades,"cost_sensitivity":costs,
                       "gate":_admission(costs)}
    return {"schema":"EMBER_C98_PRECOMMITTED_UNTOUCHED_ORIGINAL_BINANCE_OCT03_TO_OCT26",
       "precommit":"B1_C98_PRECOMMITTED_OCT03_OCT26_UNSEEN_SOURCE_TEST_RU.md",
       "period_start_ms":START_MS,"period_end_exclusive_ms":END_MS,
       "only_original_source":True,"research_evidence":EVIDENCE,
       "new_archive_count":len(receipts),"new_source_manifest":receipts,
       "old_40_archive_manifest":meta,"old_15_native3m_archive_manifest":old3_manifest,
       "verification":report,"old_A_B_exact_replay":prev_checks,
       "research_models":result,
       "all_three_validated_on_new_period":True,
       "no_fixed_rr":True,
       "all_models_trade_approved":False,
       "orders":[],"fills":[],"live_trades":[],
       "explanation":"Historical post-October02 time window was not in old C91-C97 backtests; still not prospective/live blind OOS."}
def dumps(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf8")
