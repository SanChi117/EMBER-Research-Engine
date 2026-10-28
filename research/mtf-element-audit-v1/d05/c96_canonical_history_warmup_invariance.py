"""C96: deterministic historical warm-up, embargo and prefix-invariance QA.

Purpose: do NOT infer route stability from different lengths of loaded market
history. Fix a canonical historical anchor (2026-04-01) and a strictly
PRE-REGISTERED 8-full-week/56-closed-day minimum decision warmup. Old C91
standalone Sep1 loads insufficient historical context; reject instead of
silently comparing it with full C92 April+ prehistory.

Nothing in this module computes a target from a fixed RR, changes model
thresholds after seeing performance, or places exchange orders. PAPER ONLY.
"""
from collections import Counter
from datetime import datetime,timezone
from hashlib import sha256
import json
from c89_original_native5m_adaptation_backtest import Bar,STEP,SOURCES
from c91_continuous_causal_route_a_paper import (
 discover_symbol as discover_a, HOUR,D1,WEEK,WEEK_ANCHOR,HOLD)
from c94_idm_limit_route_b_research import discover as discover_b,TTL
from c95_integrated_paper_three_routes import _metrics as portfolio_metrics
class C96Rejected(ValueError):pass
def stamp(y,m,d):
    return int(datetime(y,m,d,tzinfo=timezone.utc).timestamp()*1000)
CANONICAL_START=stamp(2026,4,1)
EVAL_START=stamp(2026,6,15)
EVAL_END=stamp(2026,10,3)
PREFIX_CUTOFF=stamp(2026,9,1)
FIRST_WEEKLY_BOUNDARY=stamp(2026,4,6)
MIN_WEEKLY_BARS=8
MIN_CLOSED_DAILY=56
MAX_B_LIMIT_TTL_PLUS_HOLD=(TTL+HOLD)*STEP
A_EMBARGO=HOLD*STEP
B_EMBARGO=(TTL+HOLD)*STEP
STATUS="RESEARCH_ONLY_WARMUP_CONTRACT"

def validate_calendar(source,symbol,*,minimum_end=EVAL_END):
    """Fail closed on SEP-only incomplete warmup or mixed/partial source."""
    if symbol not in SOURCES or type(source) is not tuple:
        raise C96Rejected("UNSUPPORTED_SYMBOL_OR_TUPLE")
    if not source or type(source[0]) is not Bar or source[0].open_ms!=CANONICAL_START:
        raise C96Rejected("CANONICAL_2026_04_01_ANCHOR_REQUIRED")
    if any(type(x) is not Bar or x.close_ms-x.open_ms!=STEP for x in source):
        raise C96Rejected("NON_NATIVE_CLOSED5M_SOURCE")
    if any(a.close_ms!=b.open_ms for a,b in zip(source,source[1:])):
        raise C96Rejected("ORIGINAL_MARKET_CALENDAR_GAP")
    if source[-1].close_ms<max(minimum_end,EVAL_START):
        raise C96Rejected("INSUFFICIENT_CLOSED_SOURCE_HORIZON")
    # Explicit 8 fully-closed UTC/Monday weeks, 56 full days as-of eval.
    days=(EVAL_START-CANONICAL_START)//D1
    weeks=(EVAL_START-FIRST_WEEKLY_BOUNDARY)//WEEK
    if days<MIN_CLOSED_DAILY or weeks<MIN_WEEKLY_BARS:
        raise C96Rejected("W1_D1_EVALUATION_WARMUP_NOT_MET")
    return {"symbol":symbol,"anchor_ms":CANONICAL_START,
      "calendar_bars":len(source),"end_exclusive_ms":source[-1].close_ms,
      "min_full_days_at_evaluation":days,
      "min_closed_full_weeks_at_evaluation":weeks,
      "evaluation_start_ms":EVAL_START,
      "status":"HISTORICAL_CONTEXT_VERIFIED"}

def _signature(t):
    keys=("symbol","route","entry_ms","exit_ms","entry","stop",
          "target","fta","derived_rr","net_r","exit_reason")
    return tuple((k,t.get(k)) for k in keys)

def _complete(trades,cutoff,embargo,*,eval_start=EVAL_START):
    """Only trades whose entire possible decision/execution horizon is
    before cutoff. Otherwise a truncated prefix could call TIME_OUT early.
    """
    return sorted((_signature(t) for t in trades
      if eval_start<=t["entry_ms"] and
         t["entry_ms"]+embargo<=cutoff and t["exit_ms"]<=cutoff),
      key=lambda x:(dict(x)["entry_ms"],dict(x)["symbol"],dict(x)["route"]))

def prefix_test(full,prefix,model,cutoff=PREFIX_CUTOFF,*,full_outputs=None):
    """Same immutable anchor, different future-suffix availability.

    Must compare complete trade signatures, not just counts or PnL.
    No silently altered target, FTA, SL, fill clock or signal.
    """
    if model not in ("A","B") or cutoff<=EVAL_START or type(cutoff) is not int:
        raise C96Rejected("UNREGISTERED_PREFIX_TEST")
    full_by_symbol={}
    for sym in sorted(SOURCES):
        validate_calendar(full[sym],sym)
        validate_calendar(prefix[sym],sym,minimum_end=cutoff)
        if prefix[sym]!=full[sym][:len(prefix[sym])]:
            raise C96Rejected("SOURCE_BYTES_OR_PREFIX_CHANGED")
        if prefix[sym][-1].close_ms!=cutoff:
            raise C96Rejected("PREFIX_NOT_CLOSED_AT_BOUNDARY")
        run=discover_a if model=="A" else discover_b
        whole=run(full[sym],sym) if full_outputs is None else full_outputs[sym]
        partial=run(prefix[sym],sym)
        embargo=A_EMBARGO if model=="A" else B_EMBARGO
        left=_complete(whole["trades"],cutoff,embargo)
        right=_complete(partial["trades"],cutoff,embargo)
        full_by_symbol[sym]={"full":len(left),"prefix":len(right),
           "consistent":left==right,
           "first_mismatched":next(((str(a),str(b)) for a,b in
              zip(left,right) if a!=b),None),
           "full_trade_signatures_sha256":sha256(repr(left).encode()).hexdigest(),
           "prefix_trade_signatures_sha256":sha256(repr(right).encode()).hexdigest()}
    return {"model":model,"boundary_ms":cutoff,
            "embargo_ms":A_EMBARGO if model=="A" else B_EMBARGO,
            "by_symbol":full_by_symbol,
            "all_consistent":all(x["consistent"] for x in full_by_symbol.values()),
            "uses_source_pinned_full_results":full_outputs is not None}

def anchor_comparison(full,source_only_sep):
    """Explain the actual 1-vs-2 difference WITHOUT pretending unchanged
    warmup. Reject Sep-only as invalid canonical evaluation input.
    """
    for sym in sorted(SOURCES):validate_calendar(full[sym],sym)
    mismatches=[]
    for sym in sorted(SOURCES):
        try:validate_calendar(source_only_sep[sym],sym)
        except C96Rejected as e:mismatches.append({"symbol":sym,"reason":str(e)})
    if len(mismatches)!=5:
        raise C96Rejected("EXPECTED_SEPTEMBER_INSUFFICIENT_CONTEXT_NOT_DETECTED")
    return {"standalone_sep_start_is_rejected":True,"five_rejected":mismatches,
        "april_anchored_eval_begin":"2026-06-15",
        "disclaimer":"Canonical April anchor is source-comparison contract, NOT an optimized trading parameter."}

def dumps(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
