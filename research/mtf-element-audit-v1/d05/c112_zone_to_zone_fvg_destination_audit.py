#!/usr/bin/env python3
"""C112: Does C109 full-confirmation actually move from a 4H FVG POI to the
nearest opposing fresh 4H FVG POI before original 4H protective stop?
Causal zone destination, physical 3m first passage. No extra indicator,
NO alteration of frozen C109, 4H SL or next original 3m entry. PAPER ONLY.
"""
from bisect import bisect_left,bisect_right
from collections import Counter
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
from pathlib import Path
import argparse,hashlib,json
import c109_simple_p4_core_vs_original_research as core
import c110_blind_unchanged_c109_second_regime as unchanged
import c105_parent4h_structural_geometry as h4
from c91_continuous_causal_route_a_paper import _fvg

class C112Rejected(ValueError):pass
PRECOMMIT="cycles/B1_C112_PRECOMMIT_ZONE_TO_ZONE_CORE_FVG_DESTINATION_HYPOTHESIS_RU.md"
WINDOWS=(
 ("WIN_A",datetime(2024,7,1,tzinfo=timezone.utc),
  datetime(2024,9,3,tzinfo=timezone.utc),
  datetime(2024,8,2,tzinfo=timezone.utc)),
 ("WIN_B",datetime(2024,10,1,tzinfo=timezone.utc),
  datetime(2024,12,4,tzinfo=timezone.utc),
  datetime(2024,11,2,tzinfo=timezone.utc)))
CORE_SHA=unchanged.CORE_SHA
ARM="B1_C109_4H_PIVOT_FTA_FROZEN"
ALT="C112_OPPOSING_FRESH_4H_FVG_ZONE_TARGET"
ZIPS=1536
SOURCE_BARS=737280
FIELDS=unchanged.CAL_FIELDS

def frozen():
    unchanged.source_code_verified()
    if len(WINDOWS)!=2 or len(core.SYMBOLS)!=12 or ZIPS!=1536 or SOURCE_BARS!=737280:
        raise C112Rejected("INVALID_PRECOMMITTED_ZONE_WINDOWS")
    if any((end-start)!=timedelta(days=64) or not start<fold<end
           for label,start,end,fold in WINDOWS):
        raise C112Rejected("WRONG_2024_SOURCE_WINDOW")
    return True

@contextmanager
def scoped(window):
    frozen()
    label,start,end,fold=window
    old={p:getattr(core,p) for p in FIELDS}
    try:
        core.BEGIN=start;core.END=end
        core.BEGIN_MS=int(start.timestamp()*1000)
        core.END_MS=int(end.timestamp()*1000)
        core.DAYS=tuple((start+timedelta(days=i)).strftime("%Y-%m-%d") for i in range(64))
        core.WARMUP_END=core.BEGIN_MS+7*core.DAY_MS
        core.LAST_ENTRY=core.END_MS-48*h4.H
        core.FOLD_MS=int(fold.timestamp()*1000)
        if (core.ZIPS!=768 or core.BARS_PER_SYMBOL!=30720 or
            not core.WARMUP_END<core.FOLD_MS<core.LAST_ENTRY):
            raise C112Rejected("SCOPED_UNREGISTERED_DATE")
        yield
    finally:
        for p,v in old.items():setattr(core,p,v)

def gap_candidates_at_entry(side,entry,entry_ms,four,rows,starts):
    """Use ONLY already completed H4 bars; find nearest opposing as-of fresh
    FVG whose 3m near edge has never traded since birth and BEFORE entry.
    No D1/W1 requirement for the OPPOSING (potential supply/demand) FVG.
    """
    if side not in ("LONG","SHORT") or not isinstance(entry,D) or entry<=0:
        raise C112Rejected("INVALID_FVG_SOURCE_SIDE")
    limit=bisect_right([x.close_ms for x in four],entry_ms)
    old=four[:limit]
    candidates=[]
    all_forward=[]
    for k in range(2,len(old)):
        tri=old[k-2:k+1]
        x=_fvg(tri)
        if not x or x[0]==side:continue
        sign,low,high=x
        if not 0<low<high:raise C112Rejected("BAD_FVG_ZONE_BOUNDS")
        near=(low if side=="LONG" else high)
        if (side=="LONG" and near<=entry) or (side=="SHORT" and near>=entry):
            continue
        created=tri[-1].close_ms
        if created>entry_ms:raise C112Rejected("UNCONFIRMED_OPPOSING_4H_FVG")
        desc={"side":sign,"low":str(low),"high":str(high),
              "created_ms":created,"near":str(near),
              "id":sign+":"+str(created)+":"+str(low)+":"+str(high)}
        all_forward.append(desc)
        j=bisect_left(starts,created)
        end=bisect_left(starts,entry_ms)
        if any(b.high>=low and b.low<=high for b in rows[j:end]):
            continue
        candidates.append((abs(near-entry),created,desc))
    if not candidates:
        return None,{"visible_historical_opposing":len(all_forward),
                     "fresh_opposing":0}
    candidates.sort(key=lambda q:(q[0],q[1],q[2]["id"]))
    return candidates[0][2],{"visible_historical_opposing":len(all_forward),
                             "fresh_opposing":len(candidates)}

def unconditioned_first_visit(rows,starts,entry_ms,horizon_ms,zone,side):
    """Observational only: does raw next 48h reach zone NEAR edge, ignoring
    actual trade exiting at SL/FTA? NEVER a simulated trade fill."""
    begin=bisect_left(starts,entry_ms)
    end=bisect_left(starts,horizon_ms)
    near=D(zone["near"])
    for b in rows[begin:end]:
        touch=b.high>=near if side=="LONG" else b.low<=near
        if touch:return b.known_ms
    return None

def zone_alt_trade(base,zone,rows,starts,closed4):
    """Exactly same entry and hard 4H SL; destination just before FVG near
    edge using same fixed original 4H ATR14 * 0.15 safety padding.
    Invalid RR is not silently substituted with original 4H pivot.
    """
    if not zone:return None,"NO_KNOWN_FRESH_OPPOSING_4H_FVG"
    e=D(base["entry"]);sl=D(base["stop"]);atr=D(base["atr4h"])
    side=base["side"]
    near=D(zone["near"])
    if not closed4 or closed4[-1].close_ms>base["entry_ms"]:
        raise C112Rejected("FUTURE_ATR_FOR_FVG_DESTINATION")
    actual_atr=h4.four_atr(closed4)
    if actual_atr!=atr:
        raise C112Rejected("4H_ATR_SOURCE_MISMATCH")
    tp=near-h4.PAD*atr if side=="LONG" else near+h4.PAD*atr
    if not(sl<e<tp if side=="LONG" else tp<e<sl):
        return None,"4H_FVG_ZONE_TP_WRONG_SIDE"
    rr=abs(tp-e)/abs(e-sl)
    if not h4.MIN_RISK<=abs(e-sl)/e<=h4.MAX_RISK:
        return None,"ORIGINAL_4H_STOP_RISK_INVALID"
    if rr<h4.MIN_RR:
        return None,"FRESH_FVG_DESTINATION_DERIVED_RR_LT_1_25"
    idx=bisect_left(starts,base["entry_ms"])
    if idx>=len(rows) or rows[idx].open!=e:
        raise C112Rejected("NEXT_NATIVE_3M_OPEN_NOT_ORIGINAL")
    alt_plan={"entry":str(e),"stop":str(sl),"target":str(tp),
         "zone_created_ms":base["zone_created_ms"],
         "parent_id":base["parent_id"],
         "parent_tf":"4H","stop_source_tf":"4H","target_source_tf":"4H",
         "target_source":"FRESH_OPPOSING_4H_FVG_NEAR_EDGE",
         "stop_source":base["stop_source"],
         "pad_source":base["pad_source"],
         "atr4h":base["atr4h"],"fta":base["fta"],
         "derived_rr":round(float(rr),6)}
    filled=h4.simulate(rows,idx,side,alt_plan,bps=14)
    filled["symbol"]=base["symbol"]
    filled["opposing_fvg_id"]=zone["id"]
    filled["opposing_fvg_created_ms"]=zone["created_ms"]
    filled["opposing_fvg_near_edge"]=zone["near"]
    filled["opposing_fvg_lower"]=zone["low"]
    filled["opposing_fvg_upper"]=zone["high"]
    filled["comparison_entry_baseline_rr"]=base["derived_rr"]
    filled["frozen_baseline_target"]=base["target"]
    filled["frozen_baseline_exit_reason"]=base["exit_reason"]
    if not (zone["created_ms"]<filled["entry_ms"] and
            filled["stop"]==base["stop"] and
            filled["entry"]==base["entry"] and
            filled["parent_tf"]==filled["stop_source_tf"]==
            filled["target_source_tf"]=="4H"):
        raise C112Rejected("RETROFITTED_ENTRY_OR_STOP_OR_WRONG_TF")
    return filled,"OK"

def per_symbol(rows,symbol):
    original=core.replay_per_symbol(rows,symbol)
    base=original["by_arm"][core.ARM_CORE]["trades"]
    fours=h4.aggregate(rows,h4.H4)
    closed4times=[b.close_ms for b in fours]
    starts=[b.start_ms for b in rows]
    ledger=[];valid_alts=[];paired_orig=[];reasons=Counter()
    for t in base:
        created=t["entry_ms"]
        closed4=fours[:bisect_right(closed4times,created)]
        fresh,counts=gap_candidates_at_entry(
            t["side"],D(t["entry"]),created,fours,rows,starts)
        alternate,reason=zone_alt_trade(t,fresh,rows,starts,closed4)
        reasons[reason]+=1
        horizon=min(t["entry_ms"]+48*h4.H,core.END_MS)
        observational=(unconditioned_first_visit(rows,starts,created,horizon,
                    fresh,t["side"]) if fresh else None)
        record={"symbol":symbol,"entry_ms":created,"side":t["side"],
            "frozen_original_entry":t["entry"],
            "frozen_original_stop":t["stop"],
            "frozen_original_4h_fta_target":t["target"],
            "frozen_original_netR14":t["net_r"],
            "frozen_original_exit_reason":t["exit_reason"],
            "frozen_original_exit_ms":t["exit_ms"],
            "known_opposing_fvg":fresh,
            "opposing_zone_candidates":counts,
            "opposing_zone_raw_near_touch_within_48h_after_entry_ms":observational,
            "alternate_eligible":alternate is not None,
            "alternate_reject_reason":reason,
            "alternate_paper":alternate}
        ledger.append(record)
        if alternate is not None:
            valid_alts.append(alternate)
            paired_orig.append(t)
    return {"symbol":symbol,
        "original_4h_fta_paper_trades":base,
        "all_source_original_4h_zone_to_zone_diagnostics":ledger,
        "valid_alternative_trades":valid_alts,
        "paired_original_trades":paired_orig,
        "rejected":dict(sorted(reasons.items())),
        "source_bars":len(rows)}

def evaluate(window,market,manifest):
    if set(market)!=set(core.SYMBOLS) or len(manifest)!=768:
        raise C112Rejected("REQUIRED_ORIGINAL_768_ZIPS")
    by={s:per_symbol(market[s],s) for s in core.SYMBOLS}
    full=[t for x in by.values() for t in x["original_4h_fta_paper_trades"]]
    matched=[t for x in by.values() for t in x["paired_original_trades"]]
    alts=[t for x in by.values() for t in x["valid_alternative_trades"]]
    records=[r for x in by.values() for r in x["all_source_original_4h_zone_to_zone_diagnostics"]]
    if len(matched)!=len(alts) or len(records)!=len(full):
        raise C112Rejected("PAIRED_TRADE_CENSORING")
    def s(trades):return core.score(trades)
    sums=Counter()
    for rec in records:
        if rec["known_opposing_fvg"]:
            sums["has_known_fresh_opposing_4h_fvg"]+=1
            if rec["opposing_zone_raw_near_touch_within_48h_after_entry_ms"] is not None:
                sums["raw_opposing_4h_zone_touched_in_original_48h"]+=1
        if rec["alternate_eligible"]:sums["admissible_same_4h_stop_fvg_target"]+=1
        sums["all_original_core_paper_entries"]+=1
    return {"window":window[0],
        "start_utc":window[1].strftime("%Y-%m-%d"),
        "end_exclusive_utc":window[2].strftime("%Y-%m-%d"),
        "source_zip_count":len(manifest),
        "original_native3m_bars":sum(len(market[s]) for s in core.SYMBOLS),
        "source_manifest":manifest,
        "per_symbol":by,"classifications":dict(sorted(sums.items())),
        "economic":{
          "ALL_ORIGINAL_4H_PIVOT_FTA":s(full),
          "MATCHED_ORIGINAL_4H_PIVOT_FTA":s(matched),
          "MATCHED_OPPOSING_FRESH_4H_FVG":s(alts)},
        "historical_only_not_prospective":True}

def run():
    frozen()
    result={}
    for window in WINDOWS:
        with scoped(window):
            market,manifest=core.provider_3m()
            result[window[0]]=evaluate(window,market,manifest)
    if sum(z["source_zip_count"] for z in result.values())!=ZIPS or sum(
        z["original_native3m_bars"] for z in result.values())!=SOURCE_BARS:
        raise C112Rejected("INCOMPLETE_TWO_REGIMES")
    both=all(z["economic"]["MATCHED_OPPOSING_FRESH_4H_FVG"]["admission"]
               ["passes_historical_screen"] for z in result.values())
    return {"schema":"C112_P4_FVG_TO_NEXT_FRESH_OPPOSING_P4_FVG_ZONE_FIRST_PASSAGE",
        "precommit":PRECOMMIT,"C109_source_sha256":CORE_SHA,
        "market_claim":"HYPOTHESIS_NOT_AXIOM",
        "only_existing_4h_zone_structure":True,
        "same_unchanged_original_entry_and_4h_protective_stop":True,
        "new_indicators":0,"fixed_rr_target":False,
        "original_total_zip_count":ZIPS,"original_native3m_bars":SOURCE_BARS,
        "windows":result,"both_historical_windows_pass":both,
        "true_future_prospective_oos":False,
        "live_approved":False,"orders":[],"fills":[],"live_trades":[],
        "interpretation":"conditional_on_C109_entry, not an isolated causal proof of the reaction itself"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    x=run()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    pins={};overview={}
    for name,period in x["windows"].items():
        fn="C112_"+name+"_ZONE_TO_ZONE_ORIGINAL_768_ZIPS.json"
        raw=(json.dumps(period,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
        (args.output_dir/fn).write_bytes(raw)
        pins[name]={"filename":fn,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
        overview[name]={"counts":period["classifications"],"economics":{
            arm:{"n":v["scores"]["25"]["n"],
              "netR25":v["scores"]["25"]["sum_r"],
              "PF25":v["scores"]["25"]["pf"],
              "R40":v["scores"]["40"]["sum_r"],
              "PF40":v["scores"]["40"]["pf"],
              "DD25":v["scores"]["25"]["dd_1pct_risk_pct"],
              "earlyN":v["scores"]["fold_early_n"],
              "lateN":v["scores"]["fold_late_n"],
              "admission":v["admission"]}
            for arm,v in period["economic"].items()}}
    manifest={k:v for k,v in x.items() if k!="windows"}
    manifest["original_window_receipts"]=pins
    manifest["period_metrics"]=overview
    raw=(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    (args.output_dir/"C112_TWO_WINDOWS_SUMMARY.json").write_bytes(raw)
    print(json.dumps({"source_zips":ZIPS,"native3m":SOURCE_BARS,
        "metrics":overview,"evidence_sha":hashlib.sha256(raw).hexdigest(),
        "evidence_bytes":len(raw),"source_receipts":pins},
        ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
