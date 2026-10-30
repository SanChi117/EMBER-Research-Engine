#!/usr/bin/env python3
"""C116 prereg original USD-M 1m -> deterministic 3m/5m, original C114 economics.

Statistical controls: matched no-CHoCH and symbol-week paired-label sign-flip.
All metadata and source amendments are pinned before C116 archive price reads.
PAPER research, never send orders.
"""
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict,Counter
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
from pathlib import Path
import argparse,hashlib,json,random

import c116_canonical_original_native1m_source as raw1
import c114_independent_poi_native5m_choch_research as original

class C116Rejected(ValueError):pass
FROZEN_SOURCE_C114_SHA="36d677166f4091f2ce66084dfb75f2407c72cbf735483cb3ee584a687ba41e6f"
PRECOMMIT="cycles/B1_C116_PRECOMMIT_NATIVE1M_4H_ZONE_REACTION_RANDOM_CONTROL_RU.md"
WINDOWS=(
    ("WIN_A",datetime(2026,4,1,tzinfo=timezone.utc),
              datetime(2026,5,27,tzinfo=timezone.utc)),
    ("WIN_B",datetime(2026,7,1,tzinfo=timezone.utc),
              datetime(2026,8,26,tzinfo=timezone.utc)))
SEED=11620261030
PERMUTATIONS=2000
EXPECTED_1M_ZIPS=1344
EXPECTED_1M_BARS=1935360
EXPECTED_DERIVED3=645120
EXPECTED_DERIVED5=387072
_original_per_symbol=original.per_symbol

def frozen():
    src=Path(original.__file__).read_bytes()
    if hashlib.sha256(src).hexdigest()!=FROZEN_SOURCE_C114_SHA:
        raise C116Rejected("ORIGINAL_C114_ECONOMIC_CORE_MODIFIED")
    if len(WINDOWS)!=2 or any((end-start)!=timedelta(days=56)
                              for _,start,end in WINDOWS):
        raise C116Rejected("CHANGED_PRECOMMITTED_2026_WINDOWS")
    if (SEED!=11620261030 or PERMUTATIONS!=2000 or
        original.REPS!=2000 or original.BOOT_SEED!=11420261030 or
        original.BPS!=(14,25,40) or
        original.LANDMARK!=6*original.H or
        len(original.SYMBOLS)!=12):
        raise C116Rejected("CHANGED_ECONOMIC_HYPOTHESIS_OR_CONTROLS")
    original.frozen()
    return True

def price_lineage_per_symbol(three,five,symbol,window):
    """C115 engineering-only known parent/symbol attribution, no pricing changes."""
    z=_original_per_symbol(three,five,symbol,window)
    for event in z["events"]:
        t=event.get("trade")
        if t is None:continue
        if t.get("symbol",event["symbol"])!=event["symbol"]:
            raise C116Rejected("MISATTRIBUTED_SYMBOL")
        if t.get("parent_id",event["parent_id"])!=event["parent_id"]:
            raise C116Rejected("MISATTRIBUTED_4H_PARENT")
        t["symbol"]=event["symbol"]
        t["parent_id"]=event["parent_id"]
    return z

def canonical_download(window):
    """At most 672 real original 1m daily provider files per 56-day window."""
    _,start,end=window
    days=original.dates(start,end)
    targets=[(sym,day) for sym in original.SYMBOLS for day in days]
    if len(targets)!=672 or len(set(targets))!=672:
        raise C116Rejected("ORIGINAL_1M_PROVIDER_TASKS_NOT_672")
    def task(pair):
        sym,day=pair
        a,b,receipt=raw1.daily_derived(sym,day)
        return sym,day,a,b,receipt
    with ThreadPoolExecutor(max_workers=10) as pool:
        data=list(pool.map(task,targets))
    m3={s:[] for s in original.SYMBOLS}
    m5={s:[] for s in original.SYMBOLS}
    receipts3,receipts5=[],[]
    for sym,day,a,b,source in data:
        if (source["symbol"]!=sym or source["date"]!=day or
            source["source_interval"]!="ORIGINAL_NATIVE_1M" or
            not source["provider_checksum_verified"] or
            len(a)!=480 or len(b)!=288):
            raise C116Rejected("INVALID_PROVIDER_LINEAGE_OR_DERIVED_BAR_COUNTS")
        if m3[sym] and m3[sym][-1].known_ms!=a[0].start_ms:
            raise C116Rejected("DERIVED_3M_CROSS_DAY_GAP")
        if m5[sym] and m5[sym][-1].close_ms!=b[0].open_ms:
            raise C116Rejected("DERIVED_5M_CROSS_DAY_GAP")
        m3[sym].extend(a);m5[sym].extend(b)
        shared={"symbol":sym,"date":day,"source_original_interval":"1m",
                "source_original_zip_sha256":source["zip_sha256"],
                "csv_sha256":source["csv_sha256"],"source":source["source"],
                "provider_checksum_verified":True}
        receipts3.append({**shared,"derived_timeframe":"3m","bars":480})
        receipts5.append({**shared,"derived_timeframe":"5m","bars":288})
    lo=int(start.timestamp()*1000);hi=int(end.timestamp()*1000)
    evidence={}
    for sym in original.SYMBOLS:
        a=tuple(m3[sym]);b=tuple(m5[sym])
        if (len(a)!=56*480 or len(b)!=56*288 or
            a[0].start_ms!=lo or a[-1].known_ms!=hi or
            b[0].open_ms!=lo or b[-1].close_ms!=hi):
            raise C116Rejected("UNTRUSTED_DERIVED_PRICE_CLOCK")
        # C114 method strictly checks cross-series high/low/open/close;
        # this still matters as an independent assembly regression.
        ec=original.independent_15m_parity(a,b)
        if (not ec["strict_ohlc_price_clock_parity"] or
            ec["bounded_volume_nonidentical_buckets"]!=0):
            raise C116Rejected("CANONICAL_1M_3M5M_INVARIANT_FAILED")
        evidence[sym]={
            "aligned15m":ec["aligned15m"],
            "strict_ohlc_price_clock_parity":True,
            "volume_nonidentical_bucket_count":0,
            "original_1m_not_independent_3m5m":True,
            "same_canonical_provider_source":True}
    if len(receipts3)!=672 or len(receipts5)!=672:
        raise C116Rejected("SOURCE_RECEIPT_COUNT_MISMATCH")
    return ({s:tuple(m3[s]) for s in original.SYMBOLS},
            {s:tuple(m5[s]) for s in original.SYMBOLS},
            receipts3,receipts5,evidence)

@contextmanager
def research_scope():
    frozen()
    old=(original.WINDOWS,original.PRECOMMIT,
         original.download,original.per_symbol)
    try:
        original.WINDOWS=WINDOWS
        original.PRECOMMIT=PRECOMMIT
        original.download=canonical_download
        original.per_symbol=price_lineage_per_symbol
        yield
    finally:
        (original.WINDOWS,original.PRECOMMIT,
         original.download,original.per_symbol)=old

def matched_differences(payload):
    events={(symbol,e["parent_id"]):e
            for symbol,z in payload["per_symbol"].items() for e in z["events"]}
    diffs=[]
    for pair in payload["matched_pair_indices"]:
        a=events.get((pair["symbol"],pair["t_parent_id"]))
        b=events.get((pair["symbol"],pair["c_parent_id"]))
        if (a is None or b is None or
            a["treatment"]!="T_CHoCH" or b["treatment"]!="C_NO_CHoCH" or
            a["trade"] is None or b["trade"] is None):
            raise C116Rejected("MATCHED_PAIR_SOURCE_OR_TRADE_LEAK")
        dt=datetime.fromtimestamp(pair["t0"]/1000,timezone.utc)
        iso=dt.isocalendar()
        diffs.append(((pair["symbol"],iso.year,iso.week),
            original.net_r(a["trade"],25)-original.net_r(b["trade"],25)))
    return diffs

def paired_label_placebo(differences,seed=SEED,permutations=PERMUTATIONS):
    """Randomly flip ALL paired difference signs within symbol-week blocks.

    Conditional label placebo, NOT a random price entry or causal A/B test.
    Predeclared statistic: observed mean T-C netR25 (paired), one-sided p.
    """
    if seed!=SEED or permutations!=PERMUTATIONS:
        raise C116Rejected("PLACEBO_PRECOMMIT_SEED_OR_REPS_DRIFT")
    if not differences:
        return {"matched_pairs":0,"n_symbol_week_blocks":0,
                "observed_mean_delta_net25":None,"p_one_sided":None,
                "placebo_exceeds_observed":None,"validity":"NO_POWER"}
    grouped=defaultdict(list)
    for key,value in differences:
        grouped[key].append(value)
    keys=sorted(grouped)
    observed=sum(d for _,d in differences)/len(differences)
    rng=random.Random(seed)
    exceeds=0
    for _ in range(permutations):
        candidate=sum((1 if rng.getrandbits(1) else -1)*sum(grouped[k])
                      for k in keys)/len(differences)
        if candidate>=observed-1e-12:exceeds+=1
    return {"matched_pairs":len(differences),"n_symbol_week_blocks":len(keys),
            "observed_mean_delta_net25":round(observed,8),
            "p_one_sided":round((1+exceeds)/(1+permutations),8),
            "placebo_exceeds_observed":exceeds,"seed":seed,
            "permutations":permutations,
            "validity":"CONDITIONAL_PAIRED_LABEL_PLACEBO_NOT_RANDOM_MARKET_ENTRY"}

def directional_diagnostics(events):
    by={}
    for name in ("T_CHoCH","C_NO_CHoCH"):
        for side in ("LONG","SHORT"):
            group=[e for e in events if e["treatment"]==name and e["side"]==side]
            trades=[e["trade"] for e in group if e["trade"] is not None]
            key=name+"_"+side
            by[key]={
                "all_itt_event_n":len(group),"filled_n":len(trades),
                "score_25bps":original.score(group,25),
                "score_40bps":original.score(group,40),
                "stop_exit_n":sum("STOP" in x["exit_reason"] for x in trades),
                "time_exit_n":sum("TIMEOUT" in x["exit_reason"] for x in trades),
            }
    return by

def diagnostics_and_gates(payload):
    events=[event for s in original.SYMBOLS
            for event in payload["per_symbol"][s]["events"]]
    differences=matched_differences(payload)
    placebo=paired_label_placebo(differences)
    side=directional_diagnostics(events)
    baseline=payload["admission"]["state"]
    power=baseline=="NO_POWER" or not differences
    if power:state="NO_POWER"
    elif baseline!="HISTORICAL_SCREEN_PASS_PAPER_ONLY":state="FAIL"
    elif placebo["p_one_sided"] is None or placebo["p_one_sided"]>=.05:
        state="FAIL"
    else:state="HISTORICAL_SCREEN_PASS_PAPER_ONLY"
    payload["c116_diagnostic"]={
        "pair_label_placebo":placebo,
        "directional_t_c":side,
        "source_original_native1m_sha_receipts":672,
        "derived3m_daily_sets":672,"derived5m_daily_sets":672,
        "random_market_entry_control_implemented":False,
        "original_c114_source_scoring_untouched":True,
        "paper_only":True,"live_approved":False,
        "extra_pass_condition_placebo_p_lt_0_05":True}
    payload["c116_gate"]={
        "state":state,"historical_only":True,
        "original_c114_state":baseline,
        "original_c114_fail_reasons":payload["admission"]["reasons"],
        "placebo_p_one_sided":placebo["p_one_sided"],
        "live_approved":False}
    # C114's names refer to original3m/5m ZIP in old provider. They are
    # misleading for C116 and are renamed, not presented as original archives.
    payload["derived3m_daily_sets"]=payload.pop("source_3m_zips")
    payload["derived5m_daily_sets"]=payload.pop("source_5m_zips")
    payload["derived3m_bar_count"]=payload.pop("original3m_bars")
    payload["derived5m_bar_count"]=payload.pop("original5m_bars")
    payload["derived3m_receipts"]=payload.pop("source_receipts_3m")
    payload["derived5m_receipts"]=payload.pop("source_receipts_5m")
    return state

def run():
    with research_scope():
        result=original.run()
    if (result["original_3m_zip_total"]!=EXPECTED_1M_ZIPS or
        result["original_5m_zip_total"]!=EXPECTED_1M_ZIPS or
        result["original_3m_bar_total"]!=EXPECTED_DERIVED3 or
        result["original_5m_bar_total"]!=EXPECTED_DERIVED5):
        raise C116Rejected("CANONICAL_SOURCE_AND_DERIVED_COUNTS_NOT_PREDECLARED")
    result["canonical_original_1m_zip_total"]=EXPECTED_1M_ZIPS
    result["canonical_original_1m_bar_total"]=EXPECTED_1M_BARS
    result["derived_3m_daily_sets"]=result.pop("original_3m_zip_total")
    result["derived_5m_daily_sets"]=result.pop("original_5m_zip_total")
    result["derived_3m_bar_total"]=result.pop("original_3m_bar_total")
    result["derived_5m_bar_total"]=result.pop("original_5m_bar_total")
    states={}
    for key,payload in result["windows"].items():
        states[key]=diagnostics_and_gates(payload)
    result["schema"]="C116_ORIGINAL_NATIVE1M_CANONICAL_TREATMENT_CONTROL_H4_5M"
    result["precommit"]=PRECOMMIT
    result["original_c114_engine_sha256"]=FROZEN_SOURCE_C114_SHA
    result["random_label_control"]="SYMBOL_WEEK_PAIRED_SIGN_FLIP"
    result["random_market_entry_control_implemented"]=False
    result["c116_windows_gate"]=states
    result["historical_screen_pass_both_windows"]=all(
        z=="HISTORICAL_SCREEN_PASS_PAPER_ONLY" for z in states.values())
    result["paper_only"]=True
    result["live_approved"]=False
    result["canonical_1m_not_trade_ground_truth"]=True
    result["no_orders_executed"]=True
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    result=run()
    folder=args.output_dir
    folder.mkdir(parents=True,exist_ok=True)
    receipts={}
    for key,payload in result["windows"].items():
        name=f"C116_{key}_CANONICAL_NATIVE1M_EVENT_PAIR_LEDGER.json"
        raw=(json.dumps(payload,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode()
        (folder/name).write_bytes(raw)
        receipts[key]={"filename":name,"sha256":hashlib.sha256(raw).hexdigest(),
                       "bytes":len(raw),
                       "gate":payload["c116_gate"],
                       "cohort":payload["cohort"],
                       "scores":payload["scores"],
                       "placebo":payload["c116_diagnostic"]["pair_label_placebo"],
                       "directional":payload["c116_diagnostic"]["directional_t_c"],
                       "portfolio":payload["portfolio"]}
    summary={k:v for k,v in result.items() if k!="windows"}
    summary["window_receipts"]=receipts
    b=(json.dumps(summary,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode()
    (folder/"C116_SUMMARY.json").write_bytes(b)
    print(json.dumps({"source_1m_zip_count":EXPECTED_1M_ZIPS,
                      "source_1m_bars":EXPECTED_1M_BARS,
                      "two_period_gate":result["c116_windows_gate"],
                      "screens_pass":result["historical_screen_pass_both_windows"],
                      "evidence":receipts,
                      "summary_sha256":hashlib.sha256(b).hexdigest(),
                      "live_approved":False},sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
