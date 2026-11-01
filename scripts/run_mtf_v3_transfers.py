"""V3 50-futures exploratory point-in-time TRANSFER->STRUCTURAL ENTRY replay.

Reads immutable contact registry from the V3 archive replay; never enters at
original contact knowing future transfer. ENTRY becomes eligible only after
a *subsequent fully closed 1H transfer*; 4H stop and target known at contact.
This is NOT executable USDT-M PnL (mark/funding/fill/portfolio absent).
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from scripts.run_mtf_v3_universe import DATA_DIR, SEED, load_batched

H1 = 3_600_000


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]


def replay(contacts: list[dict], sources: dict, zones: list[dict],
           *, require_flow: bool) -> list[dict]:
    """Causal two-stage candidate + conservative OHLC stop/target path."""
    by_zone = {(z["symbol"],z["zone_id"]):z for z in zones}
    by_hour = {
        sym:{b.ts+H1:i for i,b in enumerate(frames["1h"])}
        for sym,frames in sources.items()
    }
    trials=[]
    for e in contacts:
        symbol=e["symbol"]
        series=sources[symbol]["1h"]
        event_idx=by_hour[symbol].get(e["event_at"])
        sign=1 if e["side"]=="long" else -1
        base = {
            "symbol":symbol,"event_id":e["event_id"],"contact_at":e["event_at"],
            "side":e["side"],"zone_family":e["zone_family"],
            "taker_flow_filter":require_flow,
            "zone_id":e["zone_id"],
            "stop":e["indicative_stop"],
            "target":e["opposite_structural_target"],
            "effort_volume_ratio":e["effort_volume_ratio"],
            "contact_aggressor_pressure":e["aggressor_pressure"],
        }
        if not (
            e["penetration_atr4"]>0 and e["reclaimed_zone_at_close"]
            and e["effort_volume_ratio"]>=1.15
        ):
            continue
        if event_idx is None:
            raise ValueError(f"hourly alignment missing {symbol}")
        if e["opposite_structural_target"] is None:
            trials.append({**base,"status":"NO_OPPOSITE_4H_STRUCTURE"})
            continue
        t_zone=by_zone[(symbol,e["zone_id"])]
        confirm_idx=None
        early_invalid=False
        for j in range(event_idx+1,min(event_idx+4,len(series))):
            b=series[j]
            if b.low<=e["indicative_stop"] if sign==1 else b.high>=e["indicative_stop"]:
                early_invalid=True
                break
            response=sign*(b.close-e["contact_close"])/e["h4_atr_asof"]
            fraction=b.taker_buy/b.volume if b.volume else .5
            flow_ok = (fraction>=.52 if sign==1 else fraction<=.48)
            if response>=.10 and (not require_flow or flow_ok):
                confirm_idx=j
                break
        if early_invalid:
            trials.append({**base,"status":"STOP_BROKEN_BEFORE_CONFIRM"})
            continue
        if confirm_idx is None:
            trials.append({**base,"status":"NO_TRANSFER_WITHIN_3H"})
            continue
        decision=series[confirm_idx]
        decision_at=decision.ts+H1
        # Parent zone can expire or break while response forms.
        if (t_zone["broken_at"] is not None and t_zone["broken_at"]<=decision_at
            or t_zone.get("expires_at") is not None and t_zone["expires_at"]<=decision_at):
            trials.append({**base,"status":"4H_ZONE_NOT_ACTIVE_AT_CONFIRM",
                           "confirmed_at":decision_at})
            continue
        stop=e["indicative_stop"]
        target=e["opposite_structural_target"]
        risk=sign*(decision.close-stop)
        room=sign*(target-decision.close)
        rr=room/risk if risk>0 else -1
        if risk<=0 or room<=0 or rr<1.25:
            trials.append({**base,"status":"INADEQUATE_H4_STRUCTURE",
                           "confirmed_at":decision_at,"preopen_rr":rr})
            continue
        entry_idx=confirm_idx+1
        if entry_idx>=len(series):
            trials.append({**base,"status":"CENSORED_AT_CONFIRM",
                           "confirmed_at":decision_at})
            continue
        entry_bar=series[entry_idx]
        entry=entry_bar.open
        risk_open=sign*(entry-stop)
        room_open=sign*(target-entry)
        if risk_open<=0 or room_open<=0 or room_open/risk_open<1.25:
            trials.append({**base,"status":"NEXT_OPEN_GAP_INVALID",
                           "confirmed_at":decision_at,"entry_at":entry_bar.ts})
            continue
        if entry_idx+24>len(series):
            trials.append({**base,"status":"CENSORED_FUTURE_PATH",
                           "confirmed_at":decision_at,"entry_at":entry_bar.ts})
            continue
        exit_price=None
        exit_at=None
        exit_reason=None
        for k in range(entry_idx,entry_idx+24):
            b=series[k]
            if k>entry_idx and sign*(b.open-stop)<=0:
                exit_price,exit_at,exit_reason=b.open,b.ts,"GAP_STOP"
                break
            hit_stop=b.low<=stop if sign==1 else b.high>=stop
            hit_target=b.high>=target if sign==1 else b.low<=target
            if hit_stop:
                exit_price,exit_at,exit_reason=stop,b.ts+H1,(
                    "BOTH_STOP_FIRST" if hit_target else "STOP"
                )
                break
            if hit_target:
                exit_price,exit_at,exit_reason=target,b.ts+H1,"4H_OPPOSITE_ZONE"
                break
            if k==entry_idx+23:
                exit_price,exit_at,exit_reason=b.close,b.ts+H1,"TIME_24H"
        assert exit_price is not None and exit_at is not None
        gross=sign*(exit_price-entry)/entry*100
        trials.append({
            **base,"status":"SIMULATED",
            "confirmed_at":decision_at,"entry_at":entry_bar.ts,
            "entry":entry,"exit_at":exit_at,"exit":exit_price,
            "exit_reason":exit_reason,"preopen_rr":rr,
            "gross_nominal_pct":gross,"stress_proxy_nominal_pct":gross-.35,
        })
    return trials


def describe_trials(trials: list[dict]) -> dict:
    complete=[t for t in trials if t["status"]=="SIMULATED"]
    n=len(complete)
    vals=sorted(t["stress_proxy_nominal_pct"] for t in complete)
    days={t["entry_at"]//86400000 for t in complete}
    return {
        "contacts_pass_initial_sweep_effort":len(trials),
        "simulated":n,
        "unique_utc_entry_days":len(days),
        "rejections":dict(sorted(Counter(t["status"] for t in trials if t["status"]!="SIMULATED").items())),
        "exit_reasons":dict(sorted(Counter(t["exit_reason"] for t in complete).items())),
        "win_rate":sum(x>0 for x in vals)/n if n else None,
        "mean_stress_pct_per_nominal":sum(vals)/n if n else None,
        "median_stress_pct_per_nominal":vals[n//2] if n else None,
        "worst_stress_pct_per_nominal":vals[0] if n else None,
        "best_stress_pct_per_nominal":vals[-1] if n else None,
    }


def run(out_dir:Path,data_dir:Path) -> dict:
    sources,receipts=load_batched(data_dir)
    contacts=read_jsonl(out_dir/"all_contacts.jsonl")
    zones=read_jsonl(out_dir/"zones.jsonl")
    all_trials=[]
    stats={}
    for flow in (False,True):
        items=replay(contacts,sources,zones,require_flow=flow)
        tag="TAKER_CONFIRMED" if flow else "PRICE_ONLY"
        for x in items:
            x["research_variant"]=tag
        all_trials.extend(items)
        stats[tag]=describe_trials(items)
        stats[tag]["by_zone_family"]={
            fam:describe_trials([x for x in items if x["zone_family"]==fam])
            for fam in ("order_block","fvg","swing")
        }
        stats[tag]["by_side"]={
            side:describe_trials([x for x in items if x["side"]==side])
            for side in ("long","short")
        }
        stats[tag]["by_calendar_period"]={
            p:describe_trials([x for x in items if "confirmed_at" in x and (
                x["confirmed_at"]<datetime(2026,10,1,tzinfo=timezone.utc).timestamp()*1000
                if p=="SEPT" else x["confirmed_at"]>=datetime(2026,10,1,tzinfo=timezone.utc).timestamp()*1000
            )])
            for p in ("SEPT","OCT")
        }
    (out_dir/"structural_transfer_paths.jsonl").write_text(
        "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in all_trials),
        encoding="utf-8",
    )
    summary={
        "status":"RESEARCH_ONLY_NOT_VERIFIED_NOT_EXECUTION_GRADE",
        "source_receipt_count":len(receipts),
        "source_4h":"SMOKE-derived swing/OB/FVG zone known-at birth/break/expiry",
        "trigger_1h":"after CONTACT candle and within subsequent 3 fully CLOSED hours",
        "execution":"next fully formed 1H candle OPEN, not 15m; proof-of-mechanism only",
        "risk":"4H-zone boundary +0.15 ATR4 buffer, target nearest known opposite 4H zone",
        "outcome":"24h OHLC path, stop-first on ambiguity, 0.35pct hypothetical roundtrip costs",
        "variants":stats,
        "warnings":[
            "NOT user's exact native SMOKE strategy and NOT a proven strategy",
            "No 15m execution available for all 50 pairs in the 1H archive",
            "No actual mark/funding/liquidation/exchange queue/margin/portfolio risk",
            "Many zones on same symbol may produce overlapping correlated trade hypotheses",
            "Short 2026-Aug/Oct data window, non-OOS and no durable regime proof",
            "Taker transfer studied as an ex-ante confirmation available at H1 close",
        ],
    }
    (out_dir/"transfer_study.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8",
    )
    return summary


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--out-dir",type=Path,required=True)
    parser.add_argument("--data-dir",type=Path,default=DATA_DIR)
    args=parser.parse_args()
    result=run(args.out_dir,args.data_dir)
    print(json.dumps({"variants":result["variants"],"status":result["status"]},sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
