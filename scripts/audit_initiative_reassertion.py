"""V3 follow-up: did the losing side fail to reassert control?

RESEARCH-ONLY, predeclared observational event study on frozen 50-contract
Binance USD-M Futures 1H candles. NOT a new trading strategy or OOS.

Every qualified V3 signal waits exactly THREE fully closed 1H bars after
its original transfer confirmation. Both treated and control candidates
then use the SAME next-open clock, unchanged original 4H stop and TP and
24-hour stop-first path. This avoids the invalid comparison of an earlier
entry against a later-known retest (immortal-time bias). All observed
features are available before the later decision. Market survival before
that decision is an explicit restriction for BOTH comparison groups.

We deliberately leave the original V3 recognition and negative ledger
unchanged; the hypothesis is examined, NOT promoted to a live filter.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from scripts.audit_mtf_v3_independence import choose_symbol_nonoverlap
from scripts.run_mtf_v3_transfers import read_jsonl
from scripts.run_mtf_v3_universe import DATA_DIR, load_batched

H1 = 3_600_000
DAY = 86_400_000
OBSERVE_BARS = 3
FUTURE_BARS = 24
MIN_RR = 1.25  # unchanged from original V3 replay
STRESS_PCT = .35  # unchanged V3 fee/slippage proxy
SEED = 20261101
STOP_REASONS = {"STOP", "GAP_STOP", "BOTH_STOP_FIRST"}


def classify_reassertion(window: list, *, side: str,
                         contact_close: float) -> str:
    """At checkpoint, did old side retry the contact close and fail?

    Long: an observed LOW <= known contact-close is old-side challenge;
    challenge candle CLOSE > contact-close is successful defense, with
    all subsequent observed closes staying > contact-close.
    Short is exactly sign-symmetric. The last checkpoint is after all
    included candles CLOSE; never use any future candle to label entry.
    """
    if len(window) != OBSERVE_BARS:
        raise ValueError("must have exactly 3 previously closed 1H bars")
    sign = 1 if side == "long" else -1 if side == "short" else 0
    if not sign:
        raise ValueError("side must be long or short")
    attempt_idxs = [
        i for i, b in enumerate(window)
        if sign * (b.low if sign == 1 else b.high) <= sign*contact_close
    ]
    if not attempt_idxs:
        return "NO_REASSERTION"
    for i in attempt_idxs:
        if (
            sign * (window[i].close-contact_close) > 0
            and all(sign*(b.close-contact_close)>0 for b in window[i+1:])
        ):
            return "OLD_SIDE_REASSERTION_FAILED"
    return "OLD_SIDE_REASSERTION_NOT_REJECTED"


def evaluate_path(series: list, *, entry_idx: int, sign: int,
                  entry: float, stop: float, target: float) -> dict:
    """Unchanged 24H conservative OHLC order; no funding/mark/queue claims."""
    if entry_idx+FUTURE_BARS > len(series):
        return {"status":"CENSORED_FUTURE"}
    for k in range(entry_idx,entry_idx+FUTURE_BARS):
        b = series[k]
        if k > entry_idx and sign*(b.open-stop)<=0:
            price, reason, at = b.open, "GAP_STOP", b.ts
            break
        stop_hit = b.low<=stop if sign==1 else b.high>=stop
        target_hit = b.high>=target if sign==1 else b.low<=target
        if stop_hit:
            price, reason, at = stop, (
                "BOTH_STOP_FIRST" if target_hit else "STOP"
            ), b.ts+H1
            break
        if target_hit:
            price, reason, at = target, "4H_OPPOSITE_ZONE", b.ts+H1
            break
        if k==entry_idx+FUTURE_BARS-1:
            price, reason, at = b.close, "TIME_24H", b.ts+H1
    gross=sign*(price-entry)/entry*100
    return {
        "status":"SIMULATED","exit_at":at,
        "exit_reason":reason,
        "gross_nominal_pct":gross,
        "stress_proxy_nominal_pct":gross-STRESS_PCT,
    }


def delayed_case(original: dict, event: dict, bars: list, index: dict) -> dict:
    """Reevaluate the unchanged V3 stop/target from a fixed later clock."""
    if original["status"]!="SIMULATED":
        raise ValueError("input must be original V3 complete simulation")
    side=original["side"]
    sign=1 if side=="long" else -1
    confirmed_at=original["confirmed_at"]
    idx=index.get(confirmed_at-H1)
    if idx is None or bars[idx].ts+H1!=confirmed_at:
        raise ValueError("original transfer confirmation not found as closed 1H")
    if original["contact_at"] != event["event_at"]:
        raise ValueError("original contact mismatch")
    if not (
        event["available_at"] <= event["event_at"] <= confirmed_at
        and event["h4_close_available_at"] <= event["event_at"]
    ):
        raise ValueError("source event uses future or unavailable 4H")
    first=idx+1
    end=first+OBSERVE_BARS
    decision_at=bars[end-1].ts+H1 if end<=len(bars) else None
    result={
        "symbol":original["symbol"],"event_id":original["event_id"],
        "research_variant":original["research_variant"],
        "side":side,"zone_family":original["zone_family"],
        "confirmed_at":confirmed_at,"decision_at":decision_at,
        "checkpoint_offset_1h":OBSERVE_BARS,
        "original_result_nominal_pct":original["stress_proxy_nominal_pct"],
        "state":"UNCLASSIFIED","status":"UNCLASSIFIED",
    }
    if end+FUTURE_BARS>len(bars):
        return {**result,"status":"CENSORED_AT_FIXED_CHECKPOINT"}
    window=bars[first:end]
    if len(window)!=OBSERVE_BARS or any(
        b.ts+H1>decision_at for b in window
    ):
        raise ValueError("observation window not closed at the decision clock")
    stop=original["stop"]
    target=original["target"]
    if target is None:
        raise ValueError("missing original 4H target")
    for b in window:
        stop_hit=b.low<=stop if sign==1 else b.high>=stop
        target_hit=b.high>=target if sign==1 else b.low<=target
        if stop_hit and target_hit:
            return {**result,"status":"PRECHECK_BOTH_STOP_FIRST"}
        if stop_hit:
            return {**result,"status":"PRECHECK_STOP"}
        if target_hit:
            return {**result,"status":"PRECHECK_TARGET"}
    state=classify_reassertion(
        window,side=side,contact_close=event["contact_close"],
    )
    entry_bar=bars[end]
    if entry_bar.ts!=decision_at:
        raise ValueError("delayed entry does not follow completed 3H checkpoint")
    entry=entry_bar.open
    risk=sign*(entry-stop)
    room=sign*(target-entry)
    rr=room/risk if risk>0 else -1
    result={
        **result,"state":state,"entry_at":entry_bar.ts,
        "entry":entry,"stop":stop,"target":target,"rr_asof":rr,
    }
    if risk<=0 or room<=0 or rr<MIN_RR:
        return {**result,"status":"RR_OR_SIDE_INVALID_AT_DELAYED_OPEN"}
    return {**result,**evaluate_path(
        bars,entry_idx=end,sign=sign,
        entry=entry,stop=stop,target=target,
    )}


def describe(rows: list[dict]) -> dict:
    if not rows:
        return {"n":0,"mean_after_stress_pct":None,"stop_fraction":None,
                "win_fraction":None,"days":0,"symbols":0}
    net=[r["stress_proxy_nominal_pct"] for r in rows]
    return {
        "n":len(rows),
        "mean_after_stress_pct":round(sum(net)/len(net),6),
        "median_after_stress_pct":round(median(net),6),
        "gross_mean_pct":round(sum(r["gross_nominal_pct"] for r in rows)/len(rows),6),
        "win_fraction":round(sum(x>0 for x in net)/len(net),6),
        "stop_fraction":round(
            sum(r["exit_reason"] in STOP_REASONS for r in rows)/len(rows),6,
        ),
        "days":len({r["entry_at"]//DAY for r in rows}),
        "symbols":len({r["symbol"] for r in rows}),
    }


def day_block_contrast(rows: list[dict], treated: str, comparator: str) -> dict:
    """Descriptive grouped bootstrap; non-independent samples remain so."""
    a=[r for r in rows if r["state"]==treated]
    b=[r for r in rows if r["state"]==comparator]
    if not a or not b:
        return {"n_treated":len(a),"n_control":len(b),
                "delta_net_pct":None,"day_bootstrap_95pct":None}
    difference=(
        sum(r["stress_proxy_nominal_pct"] for r in a)/len(a)
        -sum(r["stress_proxy_nominal_pct"] for r in b)/len(b)
    )
    days=defaultdict(list)
    for r in a+b:
        days[r["entry_at"]//DAY].append(r)
    keys=sorted(days)
    estimates=[]
    if len(keys)>=8:
        rng=random.Random(SEED)
        for _ in range(300):
            chosen=[r for day in (rng.choice(keys) for _ in keys) for r in days[day]]
            x=[r["stress_proxy_nominal_pct"] for r in chosen if r["state"]==treated]
            y=[r["stress_proxy_nominal_pct"] for r in chosen if r["state"]==comparator]
            if x and y:
                estimates.append(sum(x)/len(x)-sum(y)/len(y))
        estimates.sort()
    return {
        "n_treated":len(a),"n_control":len(b),
        "delta_net_pct":round(difference,6),
        "day_bootstrap_95pct":[
            round(estimates[int(.025*len(estimates))],6),
            round(estimates[int(.975*len(estimates))],6),
        ] if len(estimates)>=100 else None,
        "unit":"UTC day cluster; not an independent regime OOS",
    }


def audit(contacts: list[dict], trials: list[dict], sources: dict) -> tuple[dict,list[dict]]:
    known={e["event_id"]:e for e in contacts}
    indices={symbol:{b.ts:i for i,b in enumerate(src["1h"])}
             for symbol,src in sources.items()}
    variants={}
    all_cases=[]
    for variant in ("PRICE_ONLY","TAKER_CONFIRMED"):
        original=[r for r in trials if r["research_variant"]==variant
                  and r["status"]=="SIMULATED"]
        nonoverlap,removed=choose_symbol_nonoverlap(original)
        cases=[
            delayed_case(r,known[r["event_id"]],sources[r["symbol"]]["1h"],
                         indices[r["symbol"]])
            for r in nonoverlap
        ]
        all_cases.extend(cases)
        counts=Counter(r["status"] for r in cases)
        eligible=[r for r in cases if r["status"]=="SIMULATED"]
        states=Counter(r["state"] for r in eligible)
        variants[variant]={
            "original_simulated":len(original),
            "nonoverlap_original":len(nonoverlap),
            "original_overlapping_removed":len(removed),
            "precheck_and_censor_counts":dict(sorted(counts.items())),
            "eligible_after_checkpoint":len(eligible),
            "states_in_eligible":dict(sorted(states.items())),
            "delayed_all_eligible":describe(eligible),
            "by_state":{
                state:describe([r for r in eligible if r["state"]==state])
                for state in (
                    "OLD_SIDE_REASSERTION_FAILED",
                    "OLD_SIDE_REASSERTION_NOT_REJECTED",
                    "NO_REASSERTION",
                )
            },
            "failed_old_side_vs_no_reassertion":day_block_contrast(
                eligible,"OLD_SIDE_REASSERTION_FAILED","NO_REASSERTION",
            ),
            "failed_old_side_vs_not_rejected":day_block_contrast(
                eligible,"OLD_SIDE_REASSERTION_FAILED",
                "OLD_SIDE_REASSERTION_NOT_REJECTED",
            ),
        }
    return {
        "status":"EXPLORATORY_REASSERTION_DIAGNOSTIC_NOT_OOS_NOT_VERIFIED",
        "data":"V3 frozen original 50 Binance USD-M 1H/4H source batches",
        "fixed_post_confirmation_observation_hours":OBSERVE_BARS,
        "trade_structure":"original V3 4H stop/TP, 1.25 RR next delayed open, "
                          "24H OHLC stop-first, unchanged 0.35pct stress cost",
        "definition":"original transfer confirmed then across next 3 fully CLOSED 1H bars "
                     "old side probes contact_close and one probe closes reclaimed "
                     "and all subsequent closes remain on new-control side",
        "survival_condition":"exclude BOTH treated and controls when original 4H stop "
                             "or target touched during 3H observation",
        "two_variants_related":"PRICE_ONLY and TAKER_CONFIRMED share source signals",
        "variants":variants,
        "warnings":[
            "Prior V3 history is already known; even date split is NOT untouched OOS.",
            "Fixed delayed-entry groups are conditional on 3H survival and 1.25 RR: "
            "do not compare their net means directly to original early V3 trades.",
            "A 1H low/high cannot establish actual order-flow cause or intrabar order.",
            "Observation label is not a predictive fact at original earlier V3 entry.",
            "All outcomes are hypothetical futures price OHLC, not funding/mark/fills "
            "or a financed Binance portfolio.",
            "No parameter tuning; no claim of true predictive edge from single sample.",
            "Source POI still V3 as-of approximation, not V4 source-native execution.",
        ],
    },all_cases


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",type=Path,required=True)
    ap.add_argument("--data-dir",type=Path,default=DATA_DIR)
    args=ap.parse_args()
    sources,receipt=load_batched(args.data_dir)
    contacts=read_jsonl(args.out_dir/"all_contacts.jsonl")
    trials=read_jsonl(args.out_dir/"structural_transfer_paths.jsonl")
    report,cases=audit(contacts,trials,sources)
    report["source_receipts"]=receipt
    (args.out_dir/"reassertion_diagnostic.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8",
    )
    (args.out_dir/"reassertion_cases.jsonl").write_text(
        "".join(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n" for row in cases),
        encoding="utf-8",
    )
    print(json.dumps({
        "status":report["status"],"variants":report["variants"],
    },ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
