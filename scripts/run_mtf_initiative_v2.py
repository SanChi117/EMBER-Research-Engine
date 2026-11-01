"""Reproduce MTF V2 on PINNED genuine Binance USDT-M 15m futures klines.

python -m scripts.run_mtf_initiative_v2 --out-dir /tmp/ember-mtf-v2
No API credentials, live orders, PAPER writes or network required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ember.research.mtf_v2_bars import H4, aggregate, read_futures_15m
from ember.research.mtf_v2_evaluation import simulate, summarize, v1_same_data
from ember.research.mtf_v2_signals import detect

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "OPUSDT", "STRKUSDT", "ZKUSDT")
DATA_ROOT = Path("research/mtf_initiative_v2/data")
SUFFIX = "_15m_20260917_20261031.csv"
SEP = datetime(2026, 10, 15, tzinfo=timezone.utc).timestamp() * 1000


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in records),
        encoding="utf-8",
    )


def run(directory: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest, accepted, events, outcomes = [], [], [], []
    reports: dict[str, dict] = {}
    by_model: dict[str, list] = {}
    by_model_common: dict[str, list] = {}
    for symbol in SYMBOLS:
        source = directory / (symbol + SUFFIX)
        raw = source.read_bytes()
        bars = read_futures_15m(source)
        four = aggregate(bars, H4)
        common_start = four[130].ts + H4 if len(four) > 130 else 2**63
        manifest.append(
            {
                "symbol": symbol, "source": str(source),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bars_15m": len(bars), "bars_4h": len(four),
                "first_open": bars[0].ts, "last_closed_at": bars[-1].ts + 900_000,
                "v1_comparable_start_at": common_start,
            }
        )
        symbol_report: dict = {}
        for flow in (True, False):
            entries, state_events = detect(symbol, bars, require_flow=flow)
            model = "MTF_V2_FLOW" if flow else "MTF_V2_PRICE_ONLY"
            for e in entries:
                assert e.parent_4h_close <= e.attempt_1h_close - 3_600_000
                assert e.attempt_1h_close < e.confirm_1h_close < e.trigger_15m_close
                assert e.trigger_15m_close == e.eligible_entry_at
            result = simulate(entries, bars)
            symbol_report[model] = summarize(result)
            accepted.extend(e.as_dict() for e in entries)
            events.extend({"model": model, **e} for e in state_events)
            outcomes.extend(x.as_dict() for x in result)
            by_model.setdefault(model, []).extend(result)
            by_model_common.setdefault(model, []).extend(
                x for x in result if x.decision_at >= common_start
            )
        original = v1_same_data(symbol, bars)
        symbol_report["V1_4H_ONLY"] = summarize(original)
        by_model.setdefault("V1_4H_ONLY", []).extend(original)
        by_model_common.setdefault("V1_4H_ONLY", []).extend(
            x for x in original if x.decision_at >= common_start
        )
        outcomes.extend(x.as_dict() for x in original)
        reports[symbol] = symbol_report

    write_jsonl(out_dir / "entries.jsonl", accepted)
    write_jsonl(out_dir / "state_events.jsonl", events)
    write_jsonl(out_dir / "outcomes.jsonl", outcomes)
    report = {
        "name": "EMBER_MTF_INITIATIVE_V2_EXPLORATORY",
        "status": "NOT_VERIFIED_DO_NOT_TRADE",
        "market": "BINANCE_USDT_M_FUTURES_15M",
        "window": "2026-09-17_to_2026-10-31_UTC",
        "data": manifest,
        "frozen_rules": {
            "higher_tf": "D1 CLOSED context, 4H 2-left/2-right confirmed pivots and ATR14",
            "1h_attempt": "4H pivot sweep >=.10 ATR4 and reclaim, volume>=1.15x",
            "1h_flow_failure": "taker-buy fraction <=.48 at low, >=.52 at high",
            "1h_transfer": "1-3 closed H1 bars; response >=.15 ATR4, directional body >=.08 ATR4, opposing taker flow",
            "15m_trigger": "close beyond six previous M15 bars, volume>=1.10x, aligned taker flow",
            "entry": "next M15 open, gap-invalid if structure RR <1.25",
            "exit": "4H-derived failed-extreme stop +.15 ATR4 buffer; opposite 4H confirmed pivot as target, 48h time stop",
            "proxy_fees": "0.20% base or 0.35% stress round trip NOT actual Binance execution",
        },
        "by_symbol": reports,
        "totals": {name: summarize(items) for name, items in by_model.items()},
        "common_window_after_v1_warmup": {
            name: summarize(items) for name, items in by_model_common.items()
        },
        "flow_direction": {
            f"{name}_{side}": summarize([x for x in items if x.side == side])
            for name, items in by_model.items()
            for side in ("long", "short")
        },
        "flow_regime": {
            f"{symbol}_{name}": {
                "contests": sum(
                    x["event"] == "H1_CONTEST" and x["model"] == name and x["symbol"] == symbol
                    for x in events
                ),
                "transfers": sum(
                    x["event"] == "H1_TRANSFER" and x["model"] == name and x["symbol"] == symbol
                    for x in events
                ),
                "entries": sum(
                    x["event"] == "ENTRY_READY" and x["model"] == name and x["symbol"] == symbol
                    for x in events
                ),
            }
            for symbol in SYMBOLS
            for name in ("MTF_V2_FLOW", "MTF_V2_PRICE_ONLY")
        },
        "calendar_diagnostics": {
            f"{name}_{period}": summarize(
                [x for x in items if (x.decision_at < SEP if period == "early" else x.decision_at >= SEP)]
            )
            for name, items in by_model.items()
            for period in ("early", "late")
        },
        "rejections": dict(sorted(Counter(
            (x["model"], x.get("reason", "NA"))
            for x in events if x["event"] in ("REJECTED", "EXPIRED")
        ).items())),
        "warnings": [
            "ALL sample histories have been researched before. Not independent OOS.",
            "SMOKE ORIGINAL strategy is NOT reproduced here: price-only is a controlled ablation, not native SMOKE parity.",
            "V1 4H detector and MTF V2 differ in logic and warmup; common-window stats are descriptive comparison only.",
            "No exchange fee tier, funding, mark liquidation, L2 queue, opening fill certainty, portfolio drawdown or capital ledger.",
            "One month plus 15 days of source history; low trade counts can make results meaningless.",
            "Taker-buy share measures executed aggressive buy volume, not full causal identification of control.",
            "No post-result threshold tuning. No live or PAPER integration.",
        ],
    }
    (out_dir / "summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DATA_ROOT)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.data_dir, args.out_dir)
    print(json.dumps(
        {
            "status": report["status"], "totals": report["totals"],
            "common_window": report["common_window_after_v1_warmup"],
            "by_symbol": report["by_symbol"], "out_dir": str(args.out_dir),
        },
        ensure_ascii=False, sort_keys=True,
    ))


if __name__ == "__main__":
    main()
