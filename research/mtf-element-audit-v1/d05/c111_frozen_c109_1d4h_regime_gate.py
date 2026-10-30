#!/usr/bin/env python3
"""C111. Exactly ONE preregistered as-of H4+1D market regime gate.
Frozen C109 trading implementation reused, not forked/edited; native Binance
3m provider ZIP checksums; two never-tested 2025 calendar windows; PAPER only.
"""
import argparse
import hashlib
import json
from bisect import bisect_right
from collections import Counter
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
from pathlib import Path

import c109_simple_p4_core_vs_original_research as core
import c110_blind_unchanged_c109_second_regime as freeze
import c105_parent4h_structural_geometry as h4
from c91_continuous_causal_route_a_paper import WEEK_ANCHOR

class C111Rejected(ValueError):pass
PRECOMMIT="cycles/B1_C111_PRECOMMIT_SINGLE_REGIME_GATE_TWO_UNSEEN_CRYPTO_WINDOWS_RU.md"
CAL_FIELDS=freeze.CAL_FIELDS
CONTROL="B1_C109_UNCHANGED"
GATED="B2_C111_1D_4H_REGIME"
WINDOWS=(
 ("WIN_A",datetime(2025,3,1,tzinfo=timezone.utc),datetime(2025,5,4,tzinfo=timezone.utc),
  datetime(2025,4,2,tzinfo=timezone.utc)),
 ("WIN_B",datetime(2025,7,1,tzinfo=timezone.utc),datetime(2025,9,3,tzinfo=timezone.utc),
  datetime(2025,8,2,tzinfo=timezone.utc)))
EFFICIENCY=D(1)/D(3)
SOURCE_SHA=freeze.CORE_SHA
EXPECTED_PER_PERIOD=768
EXPECTED_TOTAL_ZIPS=1536
EXPECTED_TOTAL_BARS=737280

def pins():
    if not freeze.source_code_verified():
        raise C111Rejected("C109_BYTE_SOURCE_UNVERIFIED")
    if (len(WINDOWS)!=2 or len(core.SYMBOLS)!=12 or
        len(set(core.SYMBOLS))!=12 or EFFICIENCY!=D(1)/D(3)):
        raise C111Rejected("NOT_PRECOMMITTED_SINGLE_GATE")
    for name,start,end,fold in WINDOWS:
        if (end-start)!=timedelta(days=64) or not start<fold<end:
            raise C111Rejected("INVALID_64DAY_REGIME_WINDOW_"+name)
    return True

@contextmanager
def scoped_new_window(record):
    """Alter only data-calendar globals; restore absolutely every value."""
    pins()
    label,start,end,fold=record
    old={name:getattr(core,name) for name in CAL_FIELDS}
    try:
        core.BEGIN=start;core.END=end
        core.BEGIN_MS=int(start.timestamp()*1000)
        core.END_MS=int(end.timestamp()*1000)
        core.DAYS=tuple((start+timedelta(days=i)).strftime("%Y-%m-%d") for i in range(64))
        core.WARMUP_END=core.BEGIN_MS+7*core.DAY_MS
        core.LAST_ENTRY=core.END_MS-48*h4.H
        core.FOLD_MS=int(fold.timestamp()*1000)
        if not(core.ZIPS==EXPECTED_PER_PERIOD and core.BARS_PER_SYMBOL==30720
               and core.FOLD_MS>core.WARMUP_END and core.FOLD_MS<core.LAST_ENTRY):
            raise C111Rejected("BAD_SCOPED_CALENDAR")
        yield
    finally:
        for name,value in old.items():
            setattr(core,name,value)

def regime_from_completed(side,asof,four,days,close4=None,closeday=None):
    """Independent strictly as-of direction + 6 H4 close steps efficiency.
    Return (boolean, reason, proof). No future bar may influence a decision.
    """
    if side not in ("LONG","SHORT") or not isinstance(asof,int):
        raise C111Rejected("BAD_DIRECTION_OR_CLOCK")
    if close4 is None:close4=tuple(x.close_ms for x in four)
    if closeday is None:closeday=tuple(x.close_ms for x in days)
    h=bisect_right(close4,asof)
    d=bisect_right(closeday,asof)
    if h<7 or d<4:
        return False,"UNAVAILABLE_FULLY_CLOSED_H4_D1_HISTORY",{}
    f=four[h-7:h]; daily=days[d-4:d]
    if len(f)!=7 or len(daily)!=4 or f[-1].close_ms>asof or daily[-1].close_ms>asof:
        raise C111Rejected("HTF_FUTURE_PRICE_AVAILABLE")
    if (asof-f[-1].close_ms>=h4.H4 or
        asof-daily[-1].close_ms>=h4.D1):
        raise C111Rejected("STALE_HTF_SOURCE_GAP")
    for chain,tf in ((f,h4.H4),(daily,h4.D1)):
        if any(b.close_ms!=a.close_ms+tf for a,b in zip(chain,chain[1:])):
            raise C111Rejected("GAP_IN_CLOSED_HTF_PRICE_SOURCE")
    delta4=f[-1].c-f[0].c
    delta1=daily[-1].c-daily[0].c
    total=sum((abs(b.c-a.c) for a,b in zip(f,f[1:])),D(0))
    efficiency=(abs(delta4)/total if total>0 else D(0))
    proof={"asof_closed_1h_ms":asof,
       "4h_last_known_close_ms":f[-1].close_ms,
       "1d_last_known_close_ms":daily[-1].close_ms,
       "4h_6_step_delta":str(delta4),
       "1d_3_step_delta":str(delta1),
       "4h_6_step_efficiency":str(efficiency),
       "regime_threshold":"1/3",
       "asof_no_future":True}
    if total==0 or delta4==0 or delta1==0:
        return False,"FLAT_OR_ZERO_MOVEMENT",proof
    if (delta4>0)!=(side=="LONG"):
        return False,"4H_DIRECTION_OPPOSES_SETUP",proof
    if (delta1>0)!=(side=="LONG"):
        return False,"1D_DIRECTION_OPPOSES_SETUP",proof
    if efficiency<EFFICIENCY:
        return False,"4H_PRICE_PATH_CHOPPY",proof
    return True,"ALIGNED_TREND_AT_ASOF_H1_CLOSE",proof

def two_arms_for_one_symbol(rows,symbol):
    """Do a FULL NEW chronological original state-machine replay twice.
    Never filter already-exited losers out of a trade journal.
    """
    old_reclaim=core.full_reclaim
    original=core.replay_per_symbol(rows,symbol)
    control=original["by_arm"][core.ARM_CORE]
    closed4=h4.aggregate(rows,h4.H4)
    close4=tuple(x.close_ms for x in closed4)
    closedays=h4.aggregate(rows,h4.D1)
    closeday=tuple(x.close_ms for x in closedays)
    scanned=Counter()
    accepted={}
    def gate_reclaim(zone,hour):
        if not old_reclaim(zone,hour):return False
        ok,why,proof=regime_from_completed(
            zone.side,hour.close_ms,closed4,closedays,close4,closeday)
        scanned[why]+=1
        if ok:
            # Gate is registered at the real 1H closed reaction, before 15m
            # confirmation and before the next original 3m entry.
            accepted[(zone.parent_id,hour.close_ms)]=proof
        return ok
    try:
        core.full_reclaim=gate_reclaim
        filtered=core.replay_per_symbol(rows,symbol)
    finally:
        core.full_reclaim=old_reclaim
    gated=filtered["by_arm"][core.ARM_CORE]
    ledger=[]
    for trade in gated["trades"]:
        copy=dict(trade)
        clock=(trade["parent_id"],trade["closed_1h_confirmation_ms"])
        if clock not in accepted:
            raise C111Rejected("NONCAUSAL_POST_EXIT_FILTERING")
        proof=accepted[clock]
        if not (proof["4h_last_known_close_ms"]<=clock[1] and
                proof["1d_last_known_close_ms"]<=clock[1] and
                clock[1]<copy["confirmed_15m_vc_ms"]==copy["entry_ms"]):
            raise C111Rejected("GATE_ASSIGNED_AFTER_ENTRY_OR_LOOKAHEAD")
        copy["arm"]=GATED
        copy["regime_proof"]=proof
        if not(copy["parent_tf"]==copy["stop_source_tf"]==
               copy["target_source_tf"]=="4H" and
               copy["risk_stop_policy"]=="PHYSICAL_NATIVE3M_H4_FVG_EDGE_ATR4H_DO_NOT_WIDEN"):
            raise C111Rejected("4H_PARENT_PROTECTIVE_STOP_FTA_CHANGED")
        ledger.append(copy)
    return {"symbol":symbol,
      CONTROL:{"trades":control["trades"],"events":control["events"],
               "rejections":control["rejections"]},
      GATED:{"trades":ledger,"events":gated["events"],
             "rejections":gated["rejections"],
             "gate_checks":dict(sorted(scanned.items()))},
      "source_candles":original["confirmed_bars"]}

def analysis_period(window,market,manifest):
    if set(market)!=set(core.SYMBOLS) or len(manifest)!=EXPECTED_PER_PERIOD:
        raise C111Rejected("PRECOMMITTED_768_ORIGINAL_SOURCE_INCOMPLETE")
    by={symbol:two_arms_for_one_symbol(market[symbol],symbol)
        for symbol in core.SYMBOLS}
    arms={}
    for arm in (CONTROL,GATED):
        trades=sorted((t for s in core.SYMBOLS for t in by[s][arm]["trades"]),
            key=lambda t:(t["entry_ms"],t["symbol"]))
        arm_scores=core.score(trades)
        event_counts=Counter()
        rejects=Counter()
        checks=Counter()
        for sym in core.SYMBOLS:
            event_counts.update(by[sym][arm]["events"])
            rejects.update(by[sym][arm]["rejections"])
            checks.update(by[sym][arm].get("gate_checks",{}))
        arms[arm]={"trades":trades,**arm_scores,
          "events":dict(sorted(event_counts.items())),
          "rejections":dict(sorted(rejects.items())),
          "gate_checks":dict(sorted(checks.items()))}
    return {
      "window":window[0],
      "start_utc":window[1].strftime("%Y-%m-%d"),
      "end_exclusive_utc":window[2].strftime("%Y-%m-%d"),
      "fold_boundary_utc":window[3].strftime("%Y-%m-%d"),
      "source_zip_count":len(manifest),
      "native3m_bars":sum(len(rows) for rows in market.values()),
      "source_manifest":manifest,
      "per_symbol":by,
      "arms":arms,
      "paper_only":True,
      "truly_prospective_future_oos":False}

def run():
    pins()
    out={}
    for window in WINDOWS:
        with scoped_new_window(window):
            market,manifest=core.provider_3m()
            result=analysis_period(window,market,manifest)
        out[window[0]]=result
    if (sum(x["source_zip_count"] for x in out.values())!=EXPECTED_TOTAL_ZIPS or
        sum(x["native3m_bars"] for x in out.values())!=EXPECTED_TOTAL_BARS):
        raise C111Rejected("TWO_FULL_ORIGINAL_TIME_REGIMES_REQUIRED")
    # Combined diagnostic is NOT a standalone simultaneous-portfolio PnL.
    each={}
    for arm in (CONTROL,GATED):
        trades=sorted((t for x in out.values() for t in x["arms"][arm]["trades"]),
            key=lambda t:(t["entry_ms"],t["symbol"]))
        each[arm]={"n":len(trades),
          "costs":{str(b):core.c105.metric(trades,b) for b in h4.BPS},
          "status":"EXPLORATORY_NOT_PORTFOLIO_EQUITY"}
    a=out["WIN_A"]["arms"][GATED]
    b=out["WIN_B"]["arms"][GATED]
    all_pass=(a["admission"]["passes_historical_screen"] and
              b["admission"]["passes_historical_screen"])
    return {"schema":"C111_ONE_REGIME_GATE_STRICT_ASOF_H4_1D_FROZEN_C109",
      "precommit":PRECOMMIT,"source_strategy_sha256":SOURCE_SHA,
      "symbols":list(core.SYMBOLS),"original_source_total_zip_count":EXPECTED_TOTAL_ZIPS,
      "original_source_total_native3m_bars":EXPECTED_TOTAL_BARS,
      "gate":"H4_6_CLOSE_STEPS_SIGN_PLUS_EFFICIENCY_GTE_1_3_AND_D1_3_CLOSE_STEPS_SIGN_AT_CLOSED_H1",
      "time_of_gate":"FULLY_CLOSED_1H_REACTION_BEFORE_15M_VC",
      "no_trading_rule_change_to_entry_or_SL_TP":True,
      "windows":out,"combined_exploratory_only":each,
      "both_historical_windows_pass":all_pass,
      "historical_not_forward_prospective_OOS":True,
      "live_approved":False,"orders":[],"fills":[],"live_trades":[],
      "readiness":"NO_LIVE_ONLY_PAPER_RESEARCH"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    out=run()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    receipts={}
    overview={}
    for key,period in out["windows"].items():
        name="C111_"+key+"_768_ORIGINAL_NATIVE3M_SOURCE_AND_TRADES.json"
        raw=(json.dumps(period,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
        (args.output_dir/name).write_bytes(raw)
        receipts[key]={"filename":name,"bytes":len(raw),
                 "sha256":hashlib.sha256(raw).hexdigest()}
        overview[key]={}
        for arm,a in period["arms"].items():
            overview[key][arm]={
              "n":a["scores"]["25"]["n"],
              "netR25":a["scores"]["25"]["sum_r"],
              "pf25":a["scores"]["25"]["pf"],
              "netR40":a["scores"]["40"]["sum_r"],
              "pf40":a["scores"]["40"]["pf"],
              "dd25":a["scores"]["25"]["dd_1pct_risk_pct"],
              "early_n":a["scores"]["fold_early_n"],
              "late_n":a["scores"]["fold_late_n"],
              "earlyR25":a["folds"]["early"]["25"]["sum_r"],
              "lateR25":a["folds"]["late"]["25"]["sum_r"],
              "screen":a["admission"],
              "gate_checks":a["gate_checks"],
              "event_counts":a["events"]
            }
    summary={k:v for k,v in out.items() if k!="windows"}
    summary["window_evidence_pins"]=receipts
    summary["per_window_metrics"]=overview
    overview_bytes=(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    fname="C111_REGIME_GATE_TWO_WINDOW_PINNED_SUMMARY.json"
    (args.output_dir/fname).write_bytes(overview_bytes)
    print(json.dumps({"total_zips":out["original_source_total_zip_count"],
       "bars":out["original_source_total_native3m_bars"],
       "overview":overview,
       "both_windows_pass":out["both_historical_windows_pass"],
       "sha_summary":hashlib.sha256(overview_bytes).hexdigest(),
       "bytes_summary":len(overview_bytes),
       "window_files":receipts},ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
