"""RESET-08: strictly lagged UTC day-window, immutable rules, no execution."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

from . import backtest_limit_v2 as ticket
from .data_contract import END, START, SYMBOLS, load_raw
from .reset08_btc_contract import check_btc

DAY = 86_400_000
LOOKBACK = 365
MIN_ALT = 6
MIN_BREADTH = 6


def median_dec(values: list[D]) -> D:
    if not values:
        raise ValueError("EMPTY_MEDIAN_INPUT")
    items = sorted(values)
    n = len(items)
    return items[n // 2] if n % 2 else (
        items[n // 2 - 1] + items[n // 2]
    ) / D(2)


def advance_state(open_now: bool, conditions: tuple[bool, bool, bool],
                  *, known: bool) -> bool:
    """3/3 opens, two failures close; unknown never opens or enters control."""
    if not known:
        return False
    if all(conditions):
        return True
    if sum(not flag for flag in conditions) >= 2:
        return False
    return open_now


def utc_day(ts: int) -> str:
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date().isoformat()


def daily_measures(rows: list[list]) -> tuple[dict[int, D], dict[int, D]]:
    bars = ticket.bar_rows(rows)
    atr = ticket._atr_series(bars)
    closes = {b.ts: b.c for b in bars}
    volatility = {
        b.ts: atr[i] / b.c
        for i, b in enumerate(bars) if atr[i] is not None
    }
    return closes, volatility


def build_calendar(
    btc_rows: list[list], alt_daily: dict[str, list[list]],
    *, start_ms: int = START, end_ms: int = END,
) -> dict:
    """For D, all market inputs are D-1 or EARLIER, with full lookbacks."""
    if set(alt_daily) != set(SYMBOLS):
        raise ValueError("RESET08_TEN_ALT_UNIVERSE_REQUIRED")
    btc_close, _ = daily_measures(btc_rows)
    alt_close = {}
    alt_vol = {}
    for symbol in SYMBOLS:
        alt_close[symbol], alt_vol[symbol] = daily_measures(alt_daily[symbol])
    cross_medians: dict[int, D] = {}
    for t in sorted(btc_close):
        available = [alt_vol[s][t] for s in SYMBOLS if t in alt_vol[s]]
        if len(available) >= MIN_ALT:
            cross_medians[t] = median_dec(available)

    state = False
    days = []
    for d in range(start_ms, end_ms, DAY):
        prev = d - DAY
        btc_50 = [btc_close.get(prev - i * DAY) for i in range(50)]
        btc_30 = btc_close.get(prev - 30 * DAY)
        reference = [cross_medians.get(prev - i * DAY)
                     for i in range(1, LOOKBACK + 1)]
        known = (all(x is not None for x in btc_50)
                 and btc_30 is not None
                 and prev in cross_medians
                 and all(x is not None for x in reference))
        breadth = sum(
            t in alt_close[s]
            and t - 30 * DAY in alt_close[s]
            and alt_close[s][t] > alt_close[s][t - 30 * DAY]
            for s in SYMBOLS for t in (prev,)
        )
        if known:
            btc_bull = (
                btc_close[prev] > sum(btc_50, D(0)) / D(50)
                and btc_close[prev] > btc_30
            )
            alt_bull = breadth >= MIN_BREADTH
            vol_expand = cross_medians[prev] > median_dec(reference)
            flags = (btc_bull, alt_bull, vol_expand)
        else:
            flags = (False, False, False)
        state = advance_state(state, flags, known=known)
        days.append({
            "day_ms": d, "day": utc_day(d),
            "state": "OPEN" if state and known else "CLOSED",
            "known": known, "btc": flags[0], "breadth": flags[1],
            "volatility": flags[2], "breadth_count": breadth,
        })

    periods = []
    active = None
    for row in days:
        if row["state"] == "OPEN":
            if active is None:
                active = {"start": row["day"], "end": row["day"],
                          "days": 0}
            active["end"] = row["day"]
            active["days"] += 1
        elif active is not None:
            periods.append(active)
            active = None
    if active is not None:
        periods.append(active)
    open_count = sum(x["state"] == "OPEN" for x in days)
    unknown_count = sum(not x["known"] for x in days)
    share = D(open_count) / D(len(days))
    return {
        "days": days, "windows": periods,
        "days_total": len(days), "days_open": open_count,
        "days_unclassifiable": unknown_count,
        "window_share": format(share, "f"),
    }


def from_pinned_data(
    raw_root: Path, *, alt_manifest: Path, btc_manifest: Path,
) -> dict:
    alt_sha = json.loads(alt_manifest.read_text())
    btc_sha = json.loads(btc_manifest.read_text())
    if set(btc_sha) != {"1d", "4h"}:
        raise ValueError("RESET08_BTC_TWO_FILE_PIN_REQUIRED")
    check_btc(raw_root, btc_sha)
    btc_rows = json.loads((raw_root / "BTCUSDT_1d.json").read_text())
    alt_rows = {
        s: load_raw(raw_root, s, "1d", expected_sha=alt_sha[s]["1d"])[0]
        for s in SYMBOLS
    }
    return build_calendar(btc_rows, alt_rows)
