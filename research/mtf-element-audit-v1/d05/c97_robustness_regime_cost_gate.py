"""C97 pre-registered robustness / market regime and cost-stress decision gate.

No optimizing historical entry/TP thresholds. Read original SHA-frozen
A/B/C paper cases and original Binance BTC daily context (closed UTC days).
Route eligibility assessed by month, cost and chronologically reserved bins;
lack of enough true independent OOS is a FAIL, never a profitable pass.
PAPER RESEARCH ONLY.
"""
from bisect import bisect_right
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal as D
import json
from c89_original_native5m_adaptation_backtest import Bar,STEP
from c91_continuous_causal_route_a_paper import _aggregate,D1
from c95_integrated_paper_three_routes import (
 START,END,_flat,_metrics,_validate,integrated,C95Rejected)
class C97Rejected(ValueError):pass
SOURCE_COST_BPS=14
COST_SCENARIOS=(14,25,40)
REGIME_RETURN_PCT=D("3")     # description, NOT tuned to PnL
MIN_TRADE_PER_EVAL_BIN=10
MIN_EVAL_BINS=2
MIN_ROUTE_TRADES=30
TARGET_PF=D("1.2")
TARGET_STRESSED_PF=D("1.1")
MAX_ILLUSTRATIVE_DD_PCT=D("10")
BINS=(
    ("TRAIN_EARLY","2026-06-15","2026-08-01"),
    ("VALIDATE","2026-08-01","2026-09-20"),
    ("LATE_AUDIT","2026-09-20","2026-10-03"),
)
ROUTES=("A","B","C")
def utc(s):
    return int(datetime.strptime(s,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
def _metadata_days(btc):
    if type(btc) is not tuple or any(type(x) is not Bar for x in btc):
        raise C97Rejected("ORIGINAL_NATIVE_BTC_ONLY")
    daily=_aggregate(btc,D1)
    return daily,[x.close_ms for x in daily]
def regime_at(daily,closes,when):
    """Frozen 7 FULLY CLOSED BTC daily candles; no current day lookahead."""
    n=bisect_right(closes,when)
    if n<8:return "WARMUP_MISSING"
    now=daily[n-1].c;before=daily[n-8].c
    ret=(now/before-D(1))*D(100)
    return "BTC_UP_7D" if ret>=REGIME_RETURN_PCT else (
        "BTC_DOWN_7D" if ret<=-REGIME_RETURN_PCT else "BTC_RANGE_7D")
def _monthly(t):
    return datetime.fromtimestamp(t/1000,timezone.utc).strftime("%Y-%m")
def _cost_case(t,price_bps):
    if price_bps not in COST_SCENARIOS or type(price_bps) is not int:
        raise C97Rejected("UNREGISTERED_COST_STRESS")
    entry=D(t["entry"]);stop=D(t["stop"])
    if not entry.is_finite() or not stop.is_finite() or entry<=0 or entry==stop:
        raise C97Rejected("BAD_ORIGINAL_STRUCTURAL_RISK")
    increased=D(price_bps-SOURCE_COST_BPS)/D(10000)*entry/abs(entry-stop)
    return {**t,"net_r":round(float(D(str(t["net_r"]))-increased),6)}
def _score(xs):
    vals=[D(str(x["net_r"])) for x in xs]
    wins=sum(max(D(0),x) for x in vals)
    losses=-sum(min(D(0),x) for x in vals)
    eq=D(1);peak=eq;dd=D(0)
    for v in vals:
        eq*=1+D("0.01")*v
        if eq<=0:raise C97Rejected("HYPOTHETICAL_EQUITY_BELOW_ZERO")
        peak=max(peak,eq);dd=max(dd,(peak-eq)/peak*D(100))
    return {"n":len(xs),"sum_r":round(float(sum(vals,D(0))),6),
       "win_rate_pct":round(100*sum(v>0 for v in vals)/len(xs),3) if vals else None,
       "pf":round(float(wins/losses),5) if losses else None,
       "dd_1pct_risk_pct":round(float(dd),5)}
def _regime_breakdown(trades,daily,closes):
    by={}
    for t in trades:
        label=regime_at(daily,closes,t["entry_ms"])
        by.setdefault(label,[]).append(t)
    return {k:_score(v) for k,v in sorted(by.items())}
def _calendar_fold(trades,first,last):
    lo,hi=utc(first),utc(last)
    return [x for x in trades if lo<=x["entry_ms"]<hi
            and x["exit_ms"]<=hi]
def analyze(a,b,c,btc_original_native):
    _validate(a,b,c)
    if btc_original_native[0].open_ms!=utc("2026-04-01"):
        raise C97Rejected("BTC_APR_ANCHOR_REQUIRED")
    daily,closes=_metadata_days(btc_original_native)
    if len(daily)<180 or daily[-1].close_ms<utc("2026-10-03"):
        raise C97Rejected("BTC_REAL_DAILY_CALENDAR_TOO_SHORT")
    collections={}
    for label,root in (("A",a),("B",b),("C",c)):
        all_=sorted((x for d in root["by_symbol"].values() for x in d["trades"]),
                    key=lambda x:(x["entry_ms"],x["symbol"]))
        if any("net_r" not in x or "entry" not in x or "stop" not in x for x in all_):
            raise C97Rejected("INCOMPLETE_PAPER_WITNESS")
        folds={name:_score(_calendar_fold(all_,first,last)) for name,first,last in BINS}
        months={}
        for t in all_:months.setdefault(_monthly(t["entry_ms"]),[]).append(t)
        cost={str(k):_score([_cost_case(x,k) for x in all_]) for k in COST_SCENARIOS}
        common=[x for x in all_ if START<=x["entry_ms"]<END]
        # NOTE: absence of C April-Aug price data is NOT evidence of zero
        # C route trades; mark genuine C source coverage explicitly.
        validation=folds["VALIDATE"];late=folds["LATE_AUDIT"]
        qualified=(len(all_)>=MIN_ROUTE_TRADES
             and validation["n"]>=MIN_TRADE_PER_EVAL_BIN
             and late["n"]>=MIN_TRADE_PER_EVAL_BIN
             and validation["pf"] is not None and validation["pf"]>=float(TARGET_PF)
             and late["pf"] is not None and late["pf"]>=float(TARGET_PF)
             and cost["25"]["pf"] is not None and cost["25"]["pf"]>=float(TARGET_STRESSED_PF)
             and cost["25"]["dd_1pct_risk_pct"]<=float(MAX_ILLUSTRATIVE_DD_PCT))
        collections[label]={"source_window":("2026-09-01--2026-10-02" if label=="C" else
                "2026-04-01--2026-10-02"),
            "total":_score(all_),
            "months":{k:_score(v) for k,v in sorted(months.items())},
            "comparably_covered_sep_oct":_score(common),
            "cost":cost,"folds":folds,
            "regimes":_regime_breakdown(all_,daily,closes),
            "eligible_for_paper_forward_research":bool(qualified),
            "qualified_for_live":False,
            "rejection_reasons":[n for n,fail in (
                ("MIN_TOTAL_TRADES",len(all_)<MIN_ROUTE_TRADES),
                ("VALIDATION_SMALL",validation["n"]<MIN_TRADE_PER_EVAL_BIN),
                ("LATE_AUDIT_SMALL",late["n"]<MIN_TRADE_PER_EVAL_BIN),
                ("VALIDATION_PF",validation["pf"] is None or validation["pf"]<float(TARGET_PF)),
                ("LATE_AUDIT_PF",late["pf"] is None or late["pf"]<float(TARGET_PF)),
                ("COST_STRESS_25BPS",cost["25"]["pf"] is None or cost["25"]["pf"]<float(TARGET_STRESSED_PF)),
                ("COST_STRESS_DD",cost["25"]["dd_1pct_risk_pct"]>float(MAX_ILLUSTRATIVE_DD_PCT)))
              if fail]}
    return {"schema":"EMBER_C97_PREDECLARED_ROBUSTNESS_NOT_TUNED",
        "evidence":"RESEARCH_ONLY_NO_PROFIT_GUARANTEES",
        "sources":"SHA_PINNED_C92_C94_C93_PLUS_BINANCE_BTC_FULL_CALENDAR",
        "btc_closed_daily_bars":len(daily),
        "regime_rule":"7 FULLY CLOSED BTC days >=3% UP <=-3% DOWN else RANGE",
        "predeclared_folds":[{"label":a,"start":b,"end_exclusive":c} for a,b,c in BINS],
        "predeclared_cost_bps":list(COST_SCENARIOS),
        "minimum_folds_trades":MIN_TRADE_PER_EVAL_BIN,
        "models":collections,
        "approved_routes":sorted(k for k,v in collections.items()
             if v["eligible_for_paper_forward_research"]),
        "live_approved":False,
        "no_fixed_rr_targets":True,
        "orders":[],"fills":[],"live_trades":[],
        "limitations":["2026 calendar history influenced research hypothesis design",
          "no unseen future OOS","full route C original3m only Sep-Oct",
          "PF/winrate small sample, time splits descriptive",
          "stress 25/40bps illustrative, actual execution/liquidations excluded"]}
def dumps(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf8")
