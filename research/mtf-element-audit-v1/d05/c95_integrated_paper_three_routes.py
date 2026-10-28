"""C95 cross-route historical PAPER portfolio/integrity gate, A/B/C isolated.

Only consumes SHA-frozen ORIGINAL Binance data-derived C92 A / C94 B /
C93 C source witnesses. Does not recompute trigger semantics from other
routes, does not import HYBRID v2 risk engine, never places orders.

C route has 3m original ONLY Sep1-Oct2; therefore comparison/portfolio
restricts EVERY route to Sep1-Oct2. Early Apr-Aug A/B are separate
source-coverage exploration and cannot be compared to C.
"""
import hashlib,json,itertools
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal as D
from pathlib import Path

START=1788220800000       # Sep 01 UTC
END=1790985600000         # Oct 03 UTC, exclusive
SPLIT=1789862400000
A_SHA="21b41cd9e1c54a25f28abbea08bc603a544bd07ea013703aaba1ce32f96a075d"
B_SHA="1b0e0e5bc131a7a7f7d985cfaf32b09210aca723cb51a4853ca2775331cc7938"
C_SHA="d71733a4f87d61e2bcd6dbc419b8d63f3a815bd0a14d1a440b143359695ba982"
RESEARCH="ADAPTED_HYPOTHESIS"
PRIORITY=("A","B","C")
DAY_R_LIMIT=D("-2")
WEEK_R_LIMIT=D("-5")
RISK_EQUITY=D("0.01")     # illustrative 1% NAV risk per hypothetical trade

class C95Rejected(ValueError):pass

def read_and_pin(path,sha):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sha:raise C95Rejected("FROZEN_SOURCE_SHA_DRIFT")
    return json.loads(raw)

def _validate(xa,xb,xc):
    if xa.get("source_bars")!=266400 or xa.get("all",{}).get("count")!=34:
        raise C95Rejected("NO_REAL_A_266400_PROVENANCE")
    if xa.get("fixed_rr_targets") is not False or xa.get("orders") or xa.get("fills") or xa.get("live_trades"):
        raise C95Rejected("ROUTE_A_FIXED_RR_OR_ORDERS")
    if xb.get("original_bars")!=266400 or xb.get("all",{}).get("count")!=15:
        raise C95Rejected("NO_REAL_B_LIMIT_PROVENANCE")
    if xb.get("fixed_rr_target") is not False or xb.get("limit_fill_mandatory") is not True:
        raise C95Rejected("B_IS_NOT_INDEPENDENT_REAL_LIMIT")
    if xb.get("orders") or xb.get("fills") or xb.get("live_trades"):
        raise C95Rejected("REAL_B_ORDERS_UNSAFE")
    if xc.get("full_native_3m_bars")!=76800 or xc.get("all",{}).get("count")!=58:
        raise C95Rejected("NO_REAL_NATIVE3M_BOS_SOURCE")
    if xc.get("fixed_rr_target") is not False or xc.get("orders") or xc.get("fills") or xc.get("live_trades"):
        raise C95Rejected("C_FIXED_RR_OR_REAL_ORDER")
    for label,source in (("A",xa),("B",xb),("C",xc)):
        if set(source["by_symbol"])!={"BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BCHUSDT"}:
            raise C95Rejected("CRYPTO_UNIVERSE_MISMATCH")
        for sym,market in source["by_symbol"].items():
            for t in market["trades"]:
                if t.get("symbol")!=sym or t.get("evidence")!=RESEARCH or t.get("readiness")!="PAPER_ONLY":
                    raise C95Rejected("FORGED_SOURCE_TRADE")
                if (type(t.get("entry_ms")) is not int or type(t.get("exit_ms")) is not int
                    or not t["entry_ms"]<t["exit_ms"] or
                    type(t.get("net_r")) not in (int,float) or
                    type(t.get("derived_rr")) not in (int,float)):
                    raise C95Rejected("SOURCE_BAD_PAPER_CLOCK_OR_RESULT")
                if t["derived_rr"]<1.25 or t["route"][0]!=label:
                    raise C95Rejected("CROSS_ROUTE_OR_LOW_RR")
                if t.get("target") is None or t.get("stop") is None:
                    raise C95Rejected("MISSING_STRUCTURAL_SL_TP")
                if t.get("fta_confirmed_ms",0)>t["entry_ms"]:
                    raise C95Rejected("FUTURE_FTA_LOOKAHEAD")

def _flat(model,letter):
    return [{"source_route":letter,**t} for v in model["by_symbol"].values()
            for t in v["trades"] if START<=t["entry_ms"]<END]

def _period(ts):
    d=datetime.fromtimestamp(ts/1000,timezone.utc)
    # UTC risk grouping only; academic course session timezone is NOT assumed.
    week=d.isocalendar()
    return d.strftime("%Y-%m-%d"),f"{week.year}-W{week.week:02d}"

def _metrics(trades):
    v=[D(str(x["net_r"])) for x in trades]
    gains=sum((max(D(0),x) for x in v),D(0))
    losses=-sum((min(D(0),x) for x in v),D(0))
    equity=D(1);peak=equity;drawdown=D(0)
    for r in v:
        equity*=D(1)+RISK_EQUITY*r
        if equity<=0:raise C95Rejected("CATASTROPHIC_HYPOTHETICAL_NAV")
        peak=max(peak,equity)
        drawdown=max(drawdown,(peak-equity)/peak*100)
    return {"trades":len(trades),"total_net_r":round(float(sum(v,D(0))),6),
        "win_rate_pct":round(100*sum(r>0 for r in v)/len(v),3) if v else None,
        "profit_factor":round(float(gains/losses),5) if losses else None,
        "illustrative_1pct_risk_compounded_equity_pct":round(float((equity-1)*100),6),
        "illustrative_max_drawdown_pct":round(float(drawdown),6)}

def _play(candidate,*,priority=PRIORITY,global_one=True,limits=True):
    if sorted(priority)!=["A","B","C"]:raise C95Rejected("INVALID_ROUTE_PRIORITY")
    rank={k:i for i,k in enumerate(priority)}
    ordered=sorted(candidate,key=lambda x:(x["entry_ms"],rank[x["source_route"]],x["symbol"]))
    chosen=[];busy_global=0;busy_by={}
    dayloss=Counter();weekloss=Counter();rejects=Counter()
    for t in ordered:
        sym=t["symbol"];timestamp=t["entry_ms"];day,week=_period(timestamp)
        if global_one and timestamp<busy_global:
            rejects["GLOBAL_POSITION_OVERLAP"]+=1;continue
        if timestamp<busy_by.get(sym,0):
            rejects["PER_SYMBOL_POSITION_OVERLAP"]+=1;continue
        # Maintain only REALIZED outcomes whose source positions would
        # already be CLOSED when the next candidate arrives.
        if limits and (dayloss[day]<=DAY_R_LIMIT or weekloss[week]<=WEEK_R_LIMIT):
            rejects["PREDECLARED_DAILY_WEEKLY_STOP"]+=1;continue
        chosen.append(t)
        busy_by[sym]=t["exit_ms"]
        if global_one:busy_global=t["exit_ms"]
        # Realized credit will only be applied when trade exit was before
        # subsequent candidate. Deferred chronological settlement below.
        # For global_one this is safe; for per-symbol mode, schedule it.
        pass
    # Re-run to support correctly CAUSAL settlement across symbols, never
    # credit exits in the future during decisions.
    if not limits:return chosen,rejects
    # Rebuild exact path with exit-based cash events.
    chosen=[];busy_global=0;busy_by={};rejects=Counter()
    active=[]
    dayloss=Counter();weekloss=Counter()
    for t in ordered:
        ts=t["entry_ms"];sym=t["symbol"]
        complete=[a for a in active if a["exit_ms"]<=ts]
        active=[a for a in active if a["exit_ms"]>ts]
        for x in complete:
            day,week=_period(x["exit_ms"])
            dayloss[day]+=D(str(x["net_r"]))
            weekloss[week]+=D(str(x["net_r"]))
        day,week=_period(ts)
        if global_one and active:
            rejects["GLOBAL_POSITION_OVERLAP"]+=1;continue
        if any(x["symbol"]==sym for x in active):
            rejects["PER_SYMBOL_POSITION_OVERLAP"]+=1;continue
        if dayloss[day]<=DAY_R_LIMIT or weekloss[week]<=WEEK_R_LIMIT:
            rejects["PREDECLARED_DAILY_WEEKLY_STOP"]+=1;continue
        active.append(t);chosen.append(t)
    return chosen,rejects

def integrated(xa,xb,xc):
    _validate(xa,xb,xc)
    candidates=_flat(xa,"A")+_flat(xb,"B")+_flat(xc,"C")
    if len({(x["source_route"],x["symbol"],x["entry_ms"],x["route"]) for x in candidates})!=len(candidates):
        raise C95Rejected("DUPLICATED_MULTI_ROUTE_SOURCE_EVENT")
    models={}
    for model in ("A","B","C"):
        s=sorted((t for t in candidates if t["source_route"]==model),
                 key=lambda x:(x["entry_ms"],x["symbol"]))
        models[model]={"samples":_metrics(s),
          "early":_metrics([x for x in s if x["entry_ms"]<SPLIT and x["exit_ms"]<=SPLIT]),
          "late":_metrics([x for x in s if x["entry_ms"]>=SPLIT]),
          "cross_split_omitted":sum(x["entry_ms"]<SPLIT<x["exit_ms"] for x in s)}
    trials={}
    for priority in itertools.permutations(PRIORITY):
        for limit in (True,False):
            scenario="".join(priority)+("_risk_stops" if limit else "_no_risk_stops")
            trades,reasons=_play(candidates,priority=priority,global_one=True,limits=limit)
            trials[scenario]={"route_order":list(priority),"risk_limits":limit,
                "results":_metrics(trades),
                "early":_metrics([x for x in trades if x["entry_ms"]<SPLIT and x["exit_ms"]<=SPLIT]),
                "late":_metrics([x for x in trades if x["entry_ms"]>=SPLIT]),
                "rejections":dict(sorted(reasons.items())),
                "trades":trades}
    return {"schema":"C95_FROZEN_A_B_C_ONE_GLOBAL_POSITION_PAPER_RESEARCH",
       "source_digest":{"A":A_SHA,"B":B_SHA,"C":C_SHA},
       "sources_not_necessarily_same_coverage":True,
       "common_comparison_window":"2026-09-01T00:00:00Z--2026-10-03T00:00:00Z",
       "all_three_routes_research_only":True,"models":models,
       "all_common_window_candidate_metrics":_metrics(candidates),
       "source_precalibrated_with_history":"NOT_PRISTINE_OOS_NO_TRADING_EDGE_CLAIM",
       "all_six_route_priority_orders_tested_not_optimized":True,
       "risk_stop_utc":"1% fixed fractional per hypothetical R; daily -2R weekly -5R; max one global",
       "portfolio_sensitivity":trials,
       "nontradeable":True,"orders":[],"fills":[],"live_trades":[],
       "ready_for_live":False,
       "readiness":"INTEGRATED_PAPER_RESEARCH_ONLY_UNVERIFIED_ACADEMIC_SEMANTICS"}
def from_frozen(root):
    root=Path(root)
    a=read_and_pin(root/"evidence/c92/C92_APR_OCT_5_SYMBOL_FULL_CAUSAL_STRATEGY_REPLAY.json",A_SHA)
    b=read_and_pin(root/"evidence/c94/C94_ORIGINAL_BINANCE_IDM_LIMIT_BOTH_MODELS_PAPER.json",B_SHA)
    c=read_and_pin(root/"evidence/c93/C93_ORIGINAL_NATIVE3M_ROUTE_C_BOS_PAPER_REPLAY.json",C_SHA)
    return integrated(a,b,c)
def dumps(v):return (json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf8")
