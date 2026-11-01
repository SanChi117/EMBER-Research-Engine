"""Reproducible 50-contract USD-M V3 POI/initiative event registry.

Run from checked-out repo:
  python -m scripts.run_mtf_v3_universe --out-dir results/mtf_v3

NO trading recommendations, strategy optimization or PAPER writes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from ember.research.mtf_v2_bars import H1, H4, FlowBar
from ember.research.mtf_v3_registry import registry, validate_hourly
from ember.research.mtf_v3_zones import build_source_zones, validate_four

DATA_DIR = Path("research/mtf_v3_universe/data")
SEED = 20261101


def load_batched(directory: Path) -> tuple[dict, list[dict]]:
    pool: dict[str, dict] = defaultdict(lambda: {"1h":[],"4h":[]})
    receipt = []
    for path in sorted(directory.glob("binance_usdm_1h_4h_batch*.csv")):
        raw = path.read_bytes()
        with path.open(encoding="utf-8",newline="") as handle:
            rows = list(csv.DictReader(handle))
        symbols = set()
        for r in rows:
            symbol, tf = r["symbol"], r["tf"]
            if tf not in ("1h","4h") or not symbol.endswith("USDT"):
                raise ValueError("invalid futures venue/symbol")
            pool[symbol][tf].append(FlowBar(
                int(r["time_ms"]),float(r["open"]),float(r["high"]),
                float(r["low"]),float(r["close"]),float(r["volume"]),
                float(r["taker_buy_base"]),
            ))
            symbols.add(symbol)
        receipt.append({
            "path": str(path),"sha256":hashlib.sha256(raw).hexdigest(),
            "rows":len(rows),"symbols":sorted(symbols),
        })
    if not pool:
        raise ValueError("no research CSV sources")
    for symbol, frames in pool.items():
        validate_hourly(frames["1h"])
        validate_four(frames["4h"])
        if len(frames["1h"]) < 1200 or len(frames["4h"]) < 600:
            raise ValueError(f"insufficient source history: {symbol}")
        if frames["1h"][-1].ts + H1 > frames["4h"][-1].ts + H4:
            raise ValueError(f"4H history ends before 1H: {symbol}")
    return dict(pool), receipt


def inspect_tf_agreement(one: list[FlowBar], four: list[FlowBar]) -> dict:
    """Check 1H->4H aggregation only for fully overlapped UTC four hours."""
    h = {bar.ts:bar for bar in one}
    compared = 0
    mismatches = 0
    for b in four:
        part = [h.get(b.ts+k*H1) for k in range(4)]
        if any(x is None for x in part):
            continue
        compared += 1
        if (abs(part[0].open-b.open)>max(1e-8, b.open*1e-8)
            or abs(part[-1].close-b.close)>max(1e-8,b.close*1e-8)
            or abs(max(x.high for x in part)-b.high)>max(1e-8,b.high*1e-8)
            or abs(min(x.low for x in part)-b.low)>max(1e-8,b.low*1e-8)
            or abs(sum(x.volume for x in part)-b.volume)>max(1e-6,b.volume*.000001)):
            mismatches += 1
    return {"compared_full_4h_bars":compared,"ohlcv_mismatches":mismatches}


def describe(events: list[dict], labels: dict[str,dict], horizon: str = "12") -> dict:
    selected = []
    for event in events:
        label = labels.get(event["event_id"])
        if label and label["status"]=="LABELED" and horizon in label["forward_close_returns_pct"]:
            selected.append((event,label))
    n=len(selected)
    values=[l["forward_close_returns_pct"][horizon] for _,l in selected]
    if not n:
        return {"total":len(events),"matured":0,"avg_forward_directional_pct":None}
    vals=sorted(values)
    unique_days=len({e["event_at"]//86400000 for e,_ in selected})
    return {
        "total":len(events),
        "matured":n,
        "unique_utc_days":unique_days,
        "positive_price_response":sum(x>0 for x in values),
        "positive_price_response_rate":sum(x>0 for x in values)/n,
        "avg_forward_directional_pct":sum(values)/n,
        "median_forward_directional_pct":vals[n//2],
        "negative_after_hypothetical_035pct_cost":sum(x<=.35 for x in values),
        "mean_after_hypothetical_035pct_cost":sum(values)/n-.35,
        "mean_future_MFE_pct":sum(l["forward_max_favorable_pct"][horizon] for _,l in selected)/n,
        "mean_future_MAE_pct":sum(l["forward_max_adverse_pct"][horizon] for _,l in selected)/n,
    }


def ci_by_utc_day(events: list[dict], label_by_id: dict[str,dict],
                  *, horizon: str = "12", simulations: int = 300) -> dict:
    """Cluster bootstrap at UTC-day level; descriptive, NOT independent OOS."""
    buckets: dict[int,list[float]] = defaultdict(list)
    for e in events:
        l=label_by_id.get(e["event_id"])
        if l and l["status"]=="LABELED" and horizon in l["forward_close_returns_pct"]:
            buckets[e["event_at"]//86400000].append(l["forward_close_returns_pct"][horizon])
    days=list(sorted(buckets))
    if len(days)<10:
        return {"days":len(days),"block_bootstrap_mean_95pct":None}
    rng=random.Random(SEED)
    estimates=[]
    for _ in range(simulations):
        sample=[rng.choice(days) for _ in days]
        flat=[x for day in sample for x in buckets[day]]
        estimates.append(sum(flat)/len(flat))
    estimates.sort()
    return {
        "days":len(days),"resamples":simulations,"unit":"UTC DAY, pooled cross-symbol dependence",
        "block_bootstrap_mean_95pct":[estimates[int(.025*simulations)],estimates[int(.975*simulations)]],
    }


def run(data_dir: Path,out_dir: Path) -> dict:
    out_dir.mkdir(parents=True,exist_ok=True)
    pool,receipts=load_batched(data_dir)
    all_contacts:list[dict]=[]
    all_labels:list[dict]=[]
    all_zones:list[dict]=[]
    all_zone_events:list[dict]=[]
    symbol_status={}
    for symbol in sorted(pool):
        frames=pool[symbol]
        one,four=frames["1h"],frames["4h"]
        agreement=inspect_tf_agreement(one,four)
        if agreement["ohlcv_mismatches"]:
            raise ValueError(f"cross-TF OHLCV mismatch {symbol}: {agreement}")
        zones,z_events=build_source_zones(four)
        contacts,labels=registry(symbol,one,four,zones)
        for record in zones:
            all_zones.append({"symbol":symbol,**record.to_dict()})
        for z_event in z_events:
            all_zone_events.append({"symbol":symbol,**z_event})
        all_contacts.extend(e.as_dict() for e in contacts)
        all_labels.extend(l.as_dict() for l in labels)
        symbol_status[symbol]={
            "source_1h_bars":len(one),"source_4h_bars":len(four),
            "source_1h_start":one[0].ts,"source_4h_start":four[0].ts,
            "source_last_closed_at":one[-1].ts+H1,
            "zone_births":len(zones),"zone_events":len(z_events),
            "unique_contact_episodes":len(contacts),
            "label_matured":sum(l.status=="LABELED" for l in labels),
            "tf_parity":agreement,
        }

    def jsonl(name:str,rows:list[dict]) -> None:
        (out_dir/name).write_text(
            "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in rows),
            encoding="utf-8",
        )
    jsonl("zones.jsonl",all_zones)
    jsonl("zone_events.jsonl",all_zone_events)
    jsonl("all_contacts.jsonl",all_contacts)
    jsonl("forward_labels_NOT_TRADING.jsonl",all_labels)
    by_id={l["event_id"]:l for l in all_labels}
    high_effort=[
        e for e in all_contacts
        if e["effort_volume_ratio"]>=1.15 and e["penetration_atr4"]>0
        and e["reclaimed_zone_at_close"]
    ]
    with_pressure=[e for e in high_effort if e["aggressor_pressure"]>=.04]
    without_pressure=[e for e in high_effort if e["aggressor_pressure"]<.04]
    cohorts={
        "all_source_zone_contacts":all_contacts,
        "all_sweep_reclaims":[e for e in all_contacts if e["penetration_atr4"]>0 and e["reclaimed_zone_at_close"]],
        "high_effort_sweep_reclaims":high_effort,
        "high_effort_with_taker_aggressor":with_pressure,
        "high_effort_without_taker_aggressor":without_pressure,
        "other_zone_contacts":[e for e in all_contacts if e["penetration_atr4"]<=0],
    }
    for family in ("order_block","swing","fvg"):
        cohorts[f"source_{family}"]=[e for e in all_contacts if e["zone_family"]==family]
    for direction in ("long","short"):
        cohorts[f"side_{direction}"]=[e for e in all_contacts if e["side"]==direction]
    label_transfer=[e for e in all_contacts if by_id[e["event_id"]]["prospective_transfer_at"] is not None]
    unconfirmed=[e for e in all_contacts if by_id[e["event_id"]]["prospective_transfer_at"] is None]
    cohorts["H1_FUTURE_TRANSFER_LABEL_NOT_INPUT"]=label_transfer
    cohorts["H1_NO_TRANSFER_LABEL_NOT_INPUT"]=unconfirmed
    group_stats={
        name:{"12h":describe(items,by_id,"12"),"24h":describe(items,by_id,"24"),
              "bootstrap_12h":ci_by_utc_day(items,by_id)}
        for name,items in cohorts.items()
    }
    by_symbol={
        sym:describe([e for e in all_contacts if e["symbol"]==sym],by_id,"12")
        for sym in pool
    }
    by_month={
        month:describe([e for e in all_contacts if datetime.fromtimestamp(e["event_at"]/1000,timezone.utc).strftime("%Y-%m")==month],by_id,"12")
        for month in sorted({datetime.fromtimestamp(e["event_at"]/1000,timezone.utc).strftime("%Y-%m") for e in all_contacts})
    }
    events_per_day=Counter(e["event_at"]//86400000 for e in all_contacts)
    return_report={
        "status":"RESEARCH_ONLY_NOT_VERIFIED_NO_TRADING",
        "source":"Binance USD-M 1H+4H klines original, closed, taker-buy included",
        "source_receipts":receipts,
        "symbols_count":len(pool),
        "bars_1h":sum(x["source_1h_bars"] for x in symbol_status.values()),
        "bars_4h":sum(x["source_4h_bars"] for x in symbol_status.values()),
        "zones":len(all_zones),
        "zone_lifecycle_events":len(all_zone_events),
        "contact_episodes":len(all_contacts),
        "forward_labels":len(all_labels),
        "unique_utc_days":len(events_per_day),
        "max_same_utc_day_events":max(events_per_day.values(),default=0),
        "by_symbol":symbol_status,
        "descriptive_12h_per_symbol":by_symbol,
        "descriptive_by_month":by_month,
        "predeclared_diagnostics":group_stats,
        "warnings":[
            "Only curated currently visible USD-M contract symbols; historical delisting survivorship bias NOT solved.",
            "Not source-native SMOKE zone parity: source-derived geometry with event-time lifecycle, different dedup/score/departure.",
            "1H window about 62.5 days, 4H background about 166.7 days; not several independent market regimes.",
            "All zone contacts are logged, sometimes multiple per price event: correlated, NEVER treat as independent trades.",
            "Forward 1/3/6/12/24h directional moves are labels, not entries or executable PnL.",
            "Hypothetical 0.35pct haircut is NOT real funding, fills, mark, spread or liquidation.",
            "Future 1H response/transfer is a label available after its closing hour: never use at original contact time.",
            "Insufficient independent multi-regime OOS and no verified profitable strategy. Paper and LIVE blocked.",
        ],
    }
    (out_dir/"summary.json").write_text(
        json.dumps(return_report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf-8",
    )
    return return_report


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-dir",type=Path,default=DATA_DIR)
    parser.add_argument("--out-dir",type=Path,required=True)
    args=parser.parse_args()
    result=run(args.data_dir,args.out_dir)
    print(json.dumps({
        "status":result["status"],
        "symbols_count":result["symbols_count"],
        "bars_1h":result["bars_1h"],"bars_4h":result["bars_4h"],
        "zones":result["zones"],"contact_episodes":result["contact_episodes"],
        "unique_utc_days":result["unique_utc_days"],
        "max_same_utc_day_events":result["max_same_utc_day_events"],
        "predeclared_diagnostics":result["predeclared_diagnostics"],
        "descriptive_by_month":result["descriptive_by_month"],
    },ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
