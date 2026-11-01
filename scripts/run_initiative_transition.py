"""Reproduce the D1/4H initiative-transition entry study on archived Binance USD-M bars.

No live API, no exchange keys and no PAPER integration.
Run from repository root:
python scripts/run_initiative_transition.py --out-dir /tmp/ember-initiative
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ember.research.initiative_transition import detect, parse_csv, simulate, summary

BASE = Path("research/fakeout_behavior_20261101")
MAIN = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
COMPARISON = ("STRKUSDT", "ZKUSDT", "LDOUSDT")
CROSS_SYMBOL = ("BNBUSDT", "XRPUSDT", "LINKUSDT", "OPUSDT", "ARBUSDT")
CUTOFF_MS = int(datetime(2025, 6, 1, tzinfo=timezone.utc).timestamp() * 1000)


def summarize_group(items: list[dict]) -> dict:
    tradable = [x for x in items if x["stress_pct"] is not None]
    count = len(tradable)
    return {
        "n_decisions": len(items),
        "n_with_simulated_outcome": count,
        "win_rate_stress": (sum(x["stress_pct"] > 0 for x in tradable) / count if count else None),
        "gross_mean_notional_pct": (sum(x["gross_pct"] for x in tradable) / count if count else None),
        "base_mean_notional_pct": (sum(x["base_pct"] for x in tradable) / count if count else None),
        "stress_mean_notional_pct": (sum(x["stress_pct"] for x in tradable) / count if count else None),
        "negative_stress": sum(x["stress_pct"] <= 0 for x in tradable),
        "exit_reasons": dict(sorted(Counter(x["exit_reason"] for x in items).items())),
    }


def run(data_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    all_decisions: list[dict] = []
    all_attempts: list[dict] = []
    all_outcomes: list[dict] = []
    per_symbol: dict = {}
    symbol_groups = (
        (MAIN, "data", "primary"),
        (COMPARISON, "data", "weak_diagnostic"),
        (CROSS_SYMBOL, "holdout_data", "cross_symbol_explored"),
    )
    for symbols, subdir, group in symbol_groups:
        for symbol in symbols:
            source = data_dir / subdir / f"{symbol}_4h.csv"
            raw = source.read_bytes()
            bars = parse_csv(str(source))
            decision_objects, attempts = detect(symbol, bars)
            outcomes = simulate(decision_objects, bars)
            by_decision = {o.decision_at: o.as_dict() for o in outcomes}
            decisions = [
                {**d.as_dict(), "research_group": group}
                for d in decision_objects
            ]
            records = [
                {**by_decision[d["decision_at"]], "research_group": group,
                 "daily_regime": d["daily_regime"]}
                for d in decisions
            ]
            all_decisions.extend(decisions)
            all_attempts.extend(attempts)
            all_outcomes.extend(records)
            per_symbol[symbol] = summary(decision_objects, attempts, outcomes)
            manifest.append(
                {
                    "symbol": symbol,
                    "group": group,
                    "source": str(source),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "bars": len(bars),
                    "from_utc": datetime.fromtimestamp(bars[0].ts / 1000, tz=timezone.utc).isoformat(),
                    "through_utc": datetime.fromtimestamp(bars[-1].ts / 1000, tz=timezone.utc).isoformat(),
                }
            )
    def write_jsonl(name: str, rows: list[dict]) -> None:
        (out_dir / name).write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
    write_jsonl("entries.jsonl", all_decisions)
    write_jsonl("attempts.jsonl", all_attempts)
    write_jsonl("outcomes.jsonl", all_outcomes)
    (out_dir / "rejected_reasons.csv").write_text(
        "reason,count\n" + "".join(
            f"{reason},{count}\n"
            for reason, count in sorted(
                Counter(x["reason"] for x in all_attempts if x["status"] == "REJECTED").items()
            )
        ),
        encoding="utf-8",
    )
    selections = {
        "all": all_outcomes,
        "primary": [x for x in all_outcomes if x["research_group"] == "primary"],
        "weak_diagnostic": [x for x in all_outcomes if x["research_group"] == "weak_diagnostic"],
        "cross_symbol_explored": [x for x in all_outcomes if x["research_group"] == "cross_symbol_explored"],
        "early": [x for x in all_outcomes if x["decision_at"] < CUTOFF_MS],
        "late": [x for x in all_outcomes if x["decision_at"] >= CUTOFF_MS],
        **{
            f"regime_{regime}": [x for x in all_outcomes if x["daily_regime"] == regime]
            for regime in ("UP", "DOWN", "RANGE", "UNKNOWN")
        },
    }
    report = {
        "study": "INITIATIVE_TRANSITION_EXPLORATORY_V1",
        "validation": "NO_NATIVE_PARITY_NO_EXECUTABLE_FUTURES_PNL",
        "venue": "BINANCE_USDT_M_FUTURES_OHLCV_ARCHIVE",
        "timeframe": "4h_UTC_D1_CLOSED_CONTEXT",
        "rules_frozen": {
            "attempt": "12 prior 4h boundary, >=0.15 prior ATR sweep, high-volume >=1.2x, >=65% rejection",
            "confirmation": "within 1-3 closed 4h, >=0.35 prior ATR favorable response and >=0.15 ATR body",
            "entry": "next 4h open; planned stop beyond failed extreme by 0.15 prior ATR",
            "target": "preexisting opposing 48-bar high/low; >=1.25 prospective structure reward/risk",
            "evaluation": "up to 12 4h bars, OHLC stop-first on ambiguity, 0.20/0.35 pct proxy roundtrip",
            "daily": "ex-ante closed 1D regime is a descriptive partition; not a filter",
        },
        "manifest": manifest,
        "symbol_results": per_symbol,
        "groups": {k: summarize_group(v) for k, v in selections.items()},
        "attempts": len(all_attempts),
        "accepted_decisions": len(all_decisions),
        "rejections": dict(sorted(Counter(
            x["reason"] for x in all_attempts if x["status"] == "REJECTED"
        ).items())),
        "warnings": [
            "All eleven symbol histories have already been explored in other EMBER research; NOT untouched OOS.",
            "No mark, signed funding, leverage, liquidations, exchange orders, orderbook fills, or portfolio margin.",
            "Proxy costs are not verified for these exact symbols/dates; outcomes are not account-return claims.",
            "No threshold tuning from these results. No live or PAPER readiness.",
        ],
    }
    (out_dir / "summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=BASE)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.data_dir, args.out_dir)
    print(json.dumps(
        {"accepted": report["accepted_decisions"], "attempts": report["attempts"],
         "groups": report["groups"], "out_dir": str(args.out_dir)},
        ensure_ascii=False, indent=2
    ))


if __name__ == "__main__":
    main()
