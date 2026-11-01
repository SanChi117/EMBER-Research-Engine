"""P06: three EX-ANTE confirmed structural TP candidates and BE-after-TP1 policy.

Source candle dataset is frozen real Binance USDT-M Futures. This file does
not compute profit, trade outcomes, size, commissions or orders. TP/SL geometry
is adaptation research, NOT original FreqHub / FailureToReturn implementation.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDLES = HERE / "binance_usdtm_closed_20261101.csv"
EXPECTED_SHA256 = "b885da6dc7e80ea81c7bfb97ec1fb3da615e31824af48625f81cdd376d9a7ee7"
SIGNAL_MS = 1790931599999  # 2026-10-02 08:59:59.999 UTC
SPEC = (
    ("TP1", "1h", 86365.5, "2026-09-22T08:59:59.999Z"),
    ("TP2", "4h", 86699.9, "2026-09-22T15:59:59.999Z"),
    ("TP3", "4h", 87247.3, "2026-09-23T07:59:59.999Z"),
)
ENTRY_OBSERVED_NEXT_OPEN = 86205.2
STRUCTURAL_SL_HYPOTHESIS = 84820.7


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def read_frozen():
    assert hashlib.sha256(CANDLES.read_bytes()).hexdigest() == EXPECTED_SHA256
    with CANDLES.open(newline="") as f:
        raw = list(csv.DictReader(f))
    candles = {}
    for interval in ("1h", "1d"):
        candles[interval] = [
            {"ot": int(x["open_time"]), "ct": int(x["close_time"]),
             "open": float(x["open"]), "high": float(x["high"]),
             "low": float(x["low"]), "close": float(x["close"])}
            for x in raw if x["symbol"] == "BTCUSDT" and x["interval"] == interval
            and int(x["close_time"]) <= SIGNAL_MS
        ]
        assert all(candles[interval][j]["ct"] < candles[interval][j+1]["ct"]
                   for j in range(len(candles[interval])-1))
    hourly = candles["1h"]
    groups = {}
    for candle in hourly:
        groups.setdefault(candle["ot"] // (4*3600*1000), []).append(candle)
    # 4h candles are CLOSED ONLY, no 08:00–11:59 candle at the 08:59 signal.
    candles["4h"] = []
    for _, group in sorted(groups.items()):
        if len(group) == 4:
            candles["4h"].append({
                "ot": group[0]["ot"], "ct": group[-1]["ct"],
                "open": group[0]["open"], "high": max(x["high"] for x in group),
                "low": min(x["low"] for x in group), "close": group[-1]["close"]
            })
    return candles


def confirmed_pivots(candles, left=2, right=2):
    """Two left + two right CLOSED candles: no hindsight during original signal."""
    found = []
    for i in range(left, len(candles)-right):
        high = candles[i]["high"]
        if all(high > candles[k]["high"] for k in range(i-left,i+right+1) if k != i):
            found.append({
                "level": high,
                "pivot_close": iso(candles[i]["ct"]),
                "confirmed_at": iso(candles[i+right]["ct"]),
                "confirmed_ms": candles[i+right]["ct"]
            })
    return found


def create_plan():
    candles = read_frozen()
    hourly = candles["1h"]
    ix = next((i for i,r in enumerate(hourly) if r["ct"] == SIGNAL_MS), None)
    assert ix is not None, "Source P06 signal bar missing"
    assert round(hourly[ix]["close"],2) == 86205.1
    raw_all = []
    with CANDLES.open(newline="") as f:
        for r in csv.DictReader(f):
            if r["symbol"] == "BTCUSDT" and r["interval"] == "1h":
                raw_all.append(r)
    assert float(raw_all[ix+1]["open"]) == ENTRY_OBSERVED_NEXT_OPEN
    observed_local_low = min(r["low"] for r in hourly[ix-6:ix+1])
    assert observed_local_low == STRUCTURAL_SL_HYPOTHESIS, observed_local_low

    targets = []
    for name,tf,level,date in SPEC:
        matches = [p for p in confirmed_pivots(candles[tf])
                   if abs(p["level"]-level)<1e-7 and p["pivot_close"]==date]
        assert len(matches)==1,(name,matches)
        p=matches[0]
        assert p["confirmed_ms"] < SIGNAL_MS
        assert ENTRY_OBSERVED_NEXT_OPEN < level
        targets.append({
            "id": name, "timeframe":tf, "price":level,
            "structural_source":"PREVIOUS_CONFIRMED_2_LEFT_2_RIGHT_SWING_HIGH",
            "pivot_close_utc":p["pivot_close"],
            "confirmed_at_utc":p["confirmed_at"],
            "known_at_signal":True,
            "original_FreqHub_TP":False,
        })
    assert [p["price"] for p in targets]==sorted(p["price"] for p in targets)

    other = {}
    for key,tf,price in [
        ("between_TP1_TP2_H1_signal_high","1h",86616.5),
        ("between_TP2_TP3_H1_confirmed_swing","1h",86888.0),
        ("beyond_TP3_daily_confirmed_swing","1d",87385.1)
    ]:
        if key=="between_TP1_TP2_H1_signal_high":
            assert hourly[ix]["high"]==price
            other[key]={"level":price,"observed_at_signal":True}
        else:
            p=next((x for x in confirmed_pivots(candles[tf]) if abs(x["level"]-price)<1e-7),None)
            assert p is not None and p["confirmed_ms"] < SIGNAL_MS,key
            other[key]={"level":price,"pivot_close_utc":p["pivot_close"],
                        "confirmed_at_utc":p["confirmed_at"]}

    plan = {
        "classification":"MECHANISM_ADAPTATION_HYPOTHESIS_NO_ORIGINAL_ORDERS",
        "original_code_unmodified":True,
        "symbol":"BTCUSDT",
        "setup":"P06 FailureToReturn",
        "source_signal_close_utc":iso(SIGNAL_MS),
        "source_signal_close":86205.1,
        "next_open_observed_at_execution_bar_not_known_in_advance":ENTRY_OBSERVED_NEXT_OPEN,
        "initial_structural_SL_hypothesis":STRUCTURAL_SL_HYPOTHESIS,
        "targets": targets,
        "other_known_barriers":other,
        "management_state_machine":[
            {"state":"POSITION_OPEN",
             "action":"Retain original independent initial SL hypothesis until an actual TP1 partial fill"},
            {"event":"TP1_PARTIAL_FILL_CONFIRMED",
             "action":"After confirmation, change remaining stop to executed entry price (price-level BE)",
             "new_stop_price":ENTRY_OBSERVED_NEXT_OPEN},
            {"event":"TP2_PARTIAL_FILL_CONFIRMED",
             "action":"Close second tranche; remaining tranche retains BE unless independently defined structural trailing policy"},
            {"event":"TP3_FILLED",
             "action":"Close remaining tranche"}
        ],
        "explicit_limits":[
            "Source P06 contains fixed 8% SL and timed ROI, NOT this three-target structure",
            "TP1, TP2 and TP3 were known before the entry signal; next-open price is retrospective observation",
            "Break-even by entry price is not fee/funding-adjusted economic breakeven",
            "Intrabar ordering of TP1 vs a returning BE stop cannot be known from OHLCV alone",
            "No position-sizing or partial-exit percentage is specified in the current mechanism-only stage",
            "No claim of reachability or performance; no live, PAPER or exchange order"
        ]
    }
    return plan


if __name__ == "__main__":
    print("EMBER_P06_STRUCTURAL_LADDER="+json.dumps(create_plan(),ensure_ascii=False))
