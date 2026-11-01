"""V3 initiative continuation vs fakeout: reproducible causal DIAGNOSTIC.

Not a strategy, an optimization search, a new signal or a portfolio.
Reads the immutable V3 50 USD-M futures archive and its exact paper replay.
Records entry-time evidence distinguishing stopped, profitable and time-expired
outcomes; explicitly flags tests that do not separate them. NO FUTURE LABELS
used as predictors; all comparisons on previously-known observations.
"""
from __future__ import annotations

import argparse
import json
import random
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

from scripts.audit_mtf_v3_independence import choose_symbol_nonoverlap
from scripts.run_mtf_v3_transfers import read_jsonl
from scripts.run_mtf_v3_universe import DATA_DIR, load_batched

DAY = 86_400_000
STOP_REASONS = {"STOP", "GAP_STOP", "BOTH_STOP_FIRST"}
SEED = 20261101

# ALL cuts chosen based on the physical meaning of observable inputs, before
# observing ANY variant outcomes. They are NOT tuned to optimize historical PnL.
# >= .04 is the already recorded V3 original taker-aggressor contrast.
TESTS = {
    "preentry_stop_beyond_previous_1h_range": ("stop_per_prior_1h_true_range", 1.0),
    "preentry_stop_beyond_1x_4h_atr": ("stop_per_4h_atr", 1.0),
    "contact_reaction_closes_in_outer_30pct": ("close_position", 0.7),
    "contact_effort_at_least_1_5x": ("effort_volume_ratio", 1.5),
    "contact_adverse_aggressor_pressure_0_04": ("aggressor_pressure", 0.04),
    "contact_sweep_penetrates_more_0_1atr4": ("penetration_atr4", 0.1),
}
FEATURES_TO_COMPARE = (
    "stop_per_prior_1h_true_range", "stop_per_4h_atr", "close_position",
    "effort_volume_ratio", "aggressor_pressure", "penetration_atr4",
    "zone_prior_retests", "zone_4h_age", "preopen_rr",
)


def prior_hour_true_range(bars: list, entry_at: int) -> float:
    """Only 24 hourly bars COMPLETED before entry open. Excludes entry bar."""
    timestamps = [b.ts for b in bars]
    idx = bisect_left(timestamps, entry_at)
    if idx < 25 or idx >= len(bars) or bars[idx].ts != entry_at:
        raise ValueError("missing 1H pre-entry warmup or start clock")
    ranges = []
    for i in range(idx - 24, idx):
        b, previous = bars[i], bars[i - 1]
        if b.ts + 3_600_000 > entry_at:
            raise ValueError("future hourly bar in entry-time feature")
        ranges.append(max(
            b.high - b.low,
            abs(b.high - previous.close),
            abs(b.low - previous.close),
        ))
    noise = median(ranges)
    if noise <= 0:
        raise ValueError("zero pre-entry 1H market range")
    return noise


def enrich(rows: list[dict], contacts: dict[str, dict], sources: dict) -> list[dict]:
    """Features are known by entry open; future trade result is label ONLY."""
    output = []
    for row in rows:
        if row["status"] != "SIMULATED":
            continue
        e = contacts[row["event_id"]]
        symbol = row["symbol"]
        entry_at = row["entry_at"]
        if not (
            e["available_at"] <= row["confirmed_at"] <= entry_at
            and e["h4_close_available_at"] <= e["event_at"] <= row["confirmed_at"]
        ):
            raise ValueError("as-of ordering violated")
        if row["contact_at"] != e["event_at"]:
            raise ValueError("contact/event mismatch")
        one = sources[symbol]["1h"]
        noise = prior_hour_true_range(one, entry_at)
        distance = abs(row["entry"] - row["stop"])
        atr4 = e["h4_atr_asof"]
        if distance <= 0 or atr4 <= 0:
            raise ValueError("invalid V3 4H risk geometry")
        output.append({
            "symbol": symbol, "event_id":row["event_id"],
            "zone_family": row["zone_family"], "side": row["side"],
            "contact_at":row["contact_at"], "confirmed_at":row["confirmed_at"],
            "entry_at":entry_at, "exit_at":row["exit_at"],
            "zone_age": e["zone_4h_age"], "zone_prior_retests":e["zone_prior_retests"],
            "d1_bias_asof":e["d1_bias_asof"],
            "d1_aligned":(
                (e["side"] == "long" and e["d1_bias_asof"] == "UP")
                or (e["side"] == "short" and e["d1_bias_asof"] == "DOWN")
            ),
            "stop_per_prior_1h_true_range":distance/noise,
            "stop_per_4h_atr":distance/atr4,
            "close_position":e["close_position"],
            "effort_volume_ratio":e["effort_volume_ratio"],
            "aggressor_pressure":e["aggressor_pressure"],
            "penetration_atr4":e["penetration_atr4"],
            "preopen_rr":row["preopen_rr"],
            "outcome_nominal_pct":row["stress_proxy_nominal_pct"],
            "gross_nominal_pct":row["gross_nominal_pct"],
            "exit_reason":row["exit_reason"],
        })
    return output


def stats(rows: list[dict]) -> dict:
    if not rows:
        return {"n":0,"mean_nominal_pct":None,"win_fraction":None,
                "stop_fraction":None, "median_nominal_pct":None,
                "unique_symbols":0,"unique_utc_days":0}
    values = [r["outcome_nominal_pct"] for r in rows]
    return {
        "n":len(rows), "mean_nominal_pct":round(sum(values)/len(values), 6),
        "win_fraction":round(sum(v>0 for v in values)/len(values), 6),
        "stop_fraction":round(sum(r["exit_reason"] in STOP_REASONS for r in rows)/len(rows), 6),
        "median_nominal_pct":round(median(values), 6),
        "gross_mean_nominal_pct":round(sum(r["gross_nominal_pct"] for r in rows)/len(rows), 6),
        "unique_symbols":len({r["symbol"] for r in rows}),
        "unique_utc_days":len({r["entry_at"]//DAY for r in rows}),
    }


def split_chronologically(rows: list[dict]) -> dict[str, list[dict]]:
    """Frozen 2/3 vs 1/3 UTC-day cut; 24h embargo around chosen cut.
    
    Both periods are previously studied V3 history, so these are NOT true OOS.
    """
    days = sorted({r["entry_at"]//DAY for r in rows})
    if len(days) < 9:
        raise ValueError("too few observed days to diagnose time variation")
    boundary_day = days[(len(days)*2)//3]
    boundary = boundary_day*DAY
    return {
        "earlier": [r for r in rows if r["entry_at"] < boundary-DAY],
        "embargo": [r for r in rows if boundary-DAY <= r["entry_at"] < boundary+DAY],
        "later": [r for r in rows if r["entry_at"] >= boundary+DAY],
        "boundary_utc": datetime.fromtimestamp(boundary/1000, tz=timezone.utc).isoformat(),
    }


def day_resampled_delta(rows: list[dict], feature: str, cutoff: float) -> dict:
    """Same-day-stratified high-minus-low nominal mean difference.

    Resamples whole UTC days (both sides), preserving within-day symbol
    co-movement, but NOT correcting all market correlation or selection bias.
    """
    buckets: dict[int,list[dict]] = defaultdict(list)
    for r in rows:
        buckets[r["entry_at"]//DAY].append(r)
    days = sorted(buckets)
    high = [r for r in rows if r[feature]>=cutoff]
    low = [r for r in rows if r[feature]<cutoff]
    if not high or not low:
        return {"delta_mean_nominal_pct":None,"bootstrap_95pct":None}
    diff = stats(high)["mean_nominal_pct"]-stats(low)["mean_nominal_pct"]
    if len(days) < 8:
        return {"delta_mean_nominal_pct":round(diff, 6), "bootstrap_95pct":None}
    rng = random.Random(SEED)
    estimates = []
    for _ in range(300):
        samples = [r for day in (rng.choice(days) for _ in days) for r in buckets[day]]
        positive = [r["outcome_nominal_pct"] for r in samples if r[feature]>=cutoff]
        negative = [r["outcome_nominal_pct"] for r in samples if r[feature]<cutoff]
        if positive and negative:
            estimates.append(sum(positive)/len(positive)-sum(negative)/len(negative))
    estimates.sort()
    return {
        "delta_mean_nominal_pct":round(diff, 6),
        "bootstrap_95pct": [
            round(estimates[int(.025*len(estimates))],6),
            round(estimates[int(.975*len(estimates))],6),
        ] if len(estimates)>=100 else None,
        "bootstrap_unit":"UTC calendar day, all symbol exposures grouped",
    }


def contrast(rows: list[dict], feature: str, cutoff: float) -> dict:
    yes = [r for r in rows if r[feature]>=cutoff]
    no = [r for r in rows if r[feature]<cutoff]
    return {
        "feature":feature,"cutoff":cutoff,
        "above_or_equal":stats(yes),"below":stats(no),
        "difference":day_resampled_delta(rows,feature,cutoff),
    }


def examples(rows: list[dict]) -> list[dict]:
    """Descriptive pairs only, not a predictive signal or matched causal effect."""
    groups = defaultdict(lambda:{"positive":[],"stopped":[]})
    for row in rows:
        key = (row["symbol"],row["zone_family"],row["side"],
               row["entry_at"]//(7*DAY))
        if row["outcome_nominal_pct"]>0:
            groups[key]["positive"].append(row)
        elif row["exit_reason"] in STOP_REASONS:
            groups[key]["stopped"].append(row)
    pairs = []
    for key,group in sorted(groups.items()):
        winners = sorted(group["positive"],key=lambda r:r["entry_at"])
        losers = sorted(group["stopped"],key=lambda r:r["entry_at"])
        if not winners or not losers:
            continue
        for win in winners[:1]:
            loser = min(losers,key=lambda r:(
                sum(abs(win[f]-r[f]) for f in (
                    "close_position", "penetration_atr4",
                    "aggressor_pressure", "stop_per_4h_atr"
                )), r["event_id"]
            ))
            pairs.append({
                "symbol":key[0],"family":key[1],"side":key[2],
                "winner_event":win["event_id"],"loser_event":loser["event_id"],
                "winner_time":win["entry_at"],"loser_time":loser["entry_at"],
                "winner_nominal_pct":round(win["outcome_nominal_pct"],5),
                "loser_nominal_pct":round(loser["outcome_nominal_pct"],5),
                "winner_entry_known":{f:round(win[f],5) for f in FEATURES_TO_COMPARE
                                      if f in win},
                "loser_entry_known":{f:round(loser[f],5) for f in FEATURES_TO_COMPARE
                                     if f in loser},
                "WARNING":"selected after outcomes; illustrates ambiguous look-alikes only",
            })
    return pairs[:25]


def audit(contacts: list[dict], trials: list[dict], sources: dict) -> dict:
    known = {r["event_id"]:r for r in contacts}
    if len(known) != len(contacts):
        raise ValueError("duplicate contact event identifiers")
    variants = {}
    example_rows = []
    for variant in ("PRICE_ONLY","TAKER_CONFIRMED"):
        original = [
            r for r in trials
            if r["research_variant"]==variant and r["status"]=="SIMULATED"
        ]
        dedup, overlap = choose_symbol_nonoverlap(original)
        enriched = enrich(dedup,known,sources)
        periods = split_chronologically(enriched)
        views = {}
        for segment in ("earlier","later"):
            rows = periods[segment]
            views[segment] = {
                "overall":stats(rows),
                "outcome_reasons":dict(Counter(r["exit_reason"] for r in rows)),
                "feature_contrasts":{
                    name:contrast(rows, f, cutoff)
                    for name,(f,cutoff) in TESTS.items()
                },
                "context":{
                    "d1_aligned":stats([r for r in rows if r["d1_aligned"]]),
                    "d1_other":stats([r for r in rows if not r["d1_aligned"]]),
                    "by_zone_family":{
                        fam:stats([r for r in rows if r["zone_family"]==fam])
                        for fam in ("order_block","swing","fvg")
                    },
                },
            }
        variants[variant] = {
            "original_simulations":len(original),
            "one_active_hypothesis_per_symbol":len(enriched),
            "overlap_rejected":len(overlap),
            "original_nonoverlap_baseline":stats(enriched),
            "time_split_utc":periods["boundary_utc"],
            "time_split_embargoed":len(periods["embargo"]),
            "by_frozen_period":views,
            "cross_period_consistency":{
                name:{
                    "earlier_delta":views["earlier"]["feature_contrasts"][name]["difference"]["delta_mean_nominal_pct"],
                    "later_delta":views["later"]["feature_contrasts"][name]["difference"]["delta_mean_nominal_pct"],
                    "same_effect_sign": (
                        (a>0)==(b>0) if a is not None and b is not None else None
                    ),
                }
                for name,(f,c) in TESTS.items()
                for a,b in [(
                    views["earlier"]["feature_contrasts"][name]["difference"]["delta_mean_nominal_pct"],
                    views["later"]["feature_contrasts"][name]["difference"]["delta_mean_nominal_pct"],
                )]
            },
        }
        if variant=="PRICE_ONLY":
            example_rows=examples(enriched)
    return {
        "status":"RESEARCH_ONLY_DIAGNOSTIC_NO_PROFIT_CLAIM",
        "subject":"Already frozen V3 50-symbol initiative transfer attempts",
        "initial_test_precommitted":TESTS,
        "source":"original V3 archived Binance USDT-M 1H+4H + V3 simulated trade journal",
        "result_type":"causal-entry-time known feature contrast, later exit OUTCOME only",
        "variants":variants,"example_pairs":example_rows,
        "warnings":[
            "No retroactive optimizer, no new trade rules or real orders",
            "This archive was previously analyzed, so early-vs-late is temporal replication NOT true untouched OOS",
            "Feature contrasts are multiple exploratory comparisons; a positive contrast is not a demonstrated edge",
            "Most same-day and multi-symbol events are dependent; block bootstrap approximates day dependence only",
            "0.35pct assumed haircut, no actual signed funding, mark/liquidation, spread or order fills",
            "An old 4H zone replica, not V4 corrected source-native selection; past V3 labels retained unchanged",
            "Stop/target and results are pre-existing V3 simulation, not profitable actionable signals",
        ],
    }


def run(out_dir: Path, data_dir: Path) -> dict:
    out_dir.mkdir(parents=True,exist_ok=True)
    sources,receipts=load_batched(data_dir)
    contacts=read_jsonl(out_dir/"all_contacts.jsonl")
    trials=read_jsonl(out_dir/"structural_transfer_paths.jsonl")
    report=audit(contacts,trials,sources)
    report["data_receipts"]=receipts
    (out_dir/"initiative_failure_diagnostic.json").write_text(
        json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status":report["status"],
        "variants": {
            variant: {
                "baseline":data["original_nonoverlap_baseline"],
                "time_split_utc":data["time_split_utc"],
                "time_split_embargoed":data["time_split_embargoed"],
                "cross_period_consistency":data["cross_period_consistency"],
                "earlier":data["by_frozen_period"]["earlier"]["feature_contrasts"],
                "later":data["by_frozen_period"]["later"]["feature_contrasts"],
                "early_exit_reasons":data["by_frozen_period"]["earlier"]["outcome_reasons"],
                "later_exit_reasons":data["by_frozen_period"]["later"]["outcome_reasons"],
            } for variant,data in report["variants"].items()
        },
        "lookalike_example_pairs":report["example_pairs"][:6],
    },ensure_ascii=False,sort_keys=True))
    return report


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--out-dir",type=Path,required=True)
    parser.add_argument("--data-dir",type=Path,default=DATA_DIR)
    args=parser.parse_args()
    run(args.out_dir,args.data_dir)


if __name__=="__main__":
    main()
