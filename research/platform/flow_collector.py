"""TZ-2: read-only Binance USD-M public REST collection, no orders or keys."""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable

from .flow_ledger import FlowStore

REST = "https://fapi.binance.com"
OI_ENDPOINT = "/fapi/v1/openInterest"
PREMIUM_ENDPOINT = "/fapi/v1/premiumIndex"
SETTLEMENT_ENDPOINT = "/fapi/v1/fundingRate"
HOUR_MS = 3_600_000
UNIVERSE = Path(__file__).resolve().parents[2] / "research/collector_universe.json"


class TransportFailure(RuntimeError):
    pass


class SourceSchemaDrift(RuntimeError):
    pass


def symbols_from_config(path: Path = UNIVERSE) -> tuple[str, ...]:
    config = json.loads(path.read_text(encoding="utf-8"))
    expected = ("SOLUSDT", "LINKUSDT", "AVAXUSDT", "NEARUSDT", "SUIUSDT",
                "ARBUSDT", "APTUSDT", "INJUSDT", "TIAUSDT", "DOGEUSDT",
                "BTCUSDT", "ETHUSDT")
    if set(config) != {"exchange", "market", "symbols", "reason"} or (
        config["exchange"] != "BINANCE" or config["market"] != "USDT_M_FUTURES"
        or tuple(config["symbols"]) != expected
    ):
        raise ValueError("COLLECTOR_UNIVERSE_NOT_OWNER_APPROVED")
    return expected


def request_public_json(endpoint: str, params: dict[str, str | int]) -> object:
    if endpoint not in (OI_ENDPOINT, PREMIUM_ENDPOINT, SETTLEMENT_ENDPOINT):
        raise TransportFailure("UNAPPROVED_BINANCE_ENDPOINT")
    url = REST + endpoint + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "EMBER-Flow-Research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status != 200:
                raise TransportFailure(f"HTTP_STATUS_{response.status}")
            raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise SourceSchemaDrift("OVERSIZE_BINANCE_RESPONSE")
            return json.loads(raw)
    except (TimeoutError, urllib.error.URLError, OSError) as exc:
        raise TransportFailure(type(exc).__name__) from exc
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise SourceSchemaDrift("NONJSON_BINANCE_RESPONSE") from exc


def _number(value: object, *, positive: bool = False) -> str:
    if type(value) is not str:
        raise SourceSchemaDrift("PROVIDER_DECIMAL_NOT_STRING")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise SourceSchemaDrift("INVALID_PROVIDER_DECIMAL") from exc
    if not result.is_finite() or (positive and result <= 0):
        raise SourceSchemaDrift("INVALID_PROVIDER_DECIMAL")
    return format(result, "f")


def _epoch(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise SourceSchemaDrift("INVALID_PROVIDER_TIMESTAMP")
    return value


def _dict(value: object) -> dict:
    if type(value) is not dict:
        raise SourceSchemaDrift("PROVIDER_EXPECTED_OBJECT")
    return value


def _append(store: FlowStore, stream: str, event_type: str, event_id: str,
            *, symbol: str, source: str, now_ms: int, **data: object) -> None:
    store.append(stream, event_id=event_id, event_type=event_type, payload={
        "observed_at_ms": now_ms, "source": REST + source if source.startswith("/") else source,
        "symbol": symbol, **data,
    })


def _present(store: FlowStore, stream: str) -> set[str]:
    return {row["event_id"] for row in store.events(stream)}


def _status(store: FlowStore, stream: str, kind: str, symbol: str, now: int,
            slot: int, reason: str, *, source: str, existing: set[str]) -> None:
    eid = f"{stream}:{kind}:{symbol}:{slot}"
    if eid not in existing:
        _append(store, stream, kind, eid, symbol=symbol, source=source,
                now_ms=now, slot_ms=slot, reason=reason)
        existing.add(eid)


def collect_once(
    store: FlowStore, symbols: tuple[str, ...], *, now_ms: int,
    fetch: Callable[[str, dict[str, str | int]], object] = request_public_json,
) -> dict[str, int]:
    """One REST cycle. Missing source => explicit GAP; malformed => SCHEMA_DRIFT."""
    if tuple(symbols) != symbols_from_config():
        raise ValueError("INVALID_COLLECTOR_SYMBOLS")
    slot = now_ms // HOUR_MS * HOUR_MS
    oi_ids = _present(store, "oi")
    funding_ids = _present(store, "funding")
    stats = {"oi_written": 0, "oi_gap": 0, "funding_written": 0, "funding_gap": 0}
    for stream, ids in (("oi", oi_ids), ("funding", funding_ids)):
        restart = f"{stream}:COLLECTOR_RESTART:{now_ms}"
        if restart not in ids:
            _append(store, stream, "COLLECTOR_RESTART", restart, symbol="*",
                    source="EMBER_COLLECTOR_START", now_ms=now_ms,
                    run_started_at_ms=now_ms)
            ids.add(restart)
        if now_ms - slot > 15 * 60_000:
            _status(store, stream, "SCHEDULER_JITTER", "*", now_ms, slot,
                    "STARTED_MORE_THAN_15_MIN_AFTER_UTC_HOUR",
                    source="GITHUB_ACTIONS_OR_HOST_SCHEDULER", existing=ids)

    # Annotate (do not backfill) missing OI hourly slots from the LAST
    # observed slot of each symbol, but only after the initial collection.
    for symbol in symbols:
        observed_slots = [
            r["payload"]["slot_ms"] for r in store.events("oi")
            if r["event_type"] == "OI_SNAPSHOT"
            and r["payload"]["symbol"] == symbol
        ]
        if observed_slots:
            last_slot = max(observed_slots)
            if slot - last_slot > 7 * 24 * HOUR_MS:
                raise ValueError("COLLECTOR_RECOVERY_WINDOW_EXCEEDS_7_DAYS")
            for missed in range(last_slot + HOUR_MS, slot, HOUR_MS):
                _status(store, "oi", "GAP", symbol, now_ms, missed,
                        "PROCESS_NOT_RUNNING_OR_SOURCE_UNAVAILABLE",
                        source=OI_ENDPOINT, existing=oi_ids)

    for symbol in symbols:
        eid = f"oi:{symbol}:{slot}"
        if eid not in oi_ids:
            try:
                row = _dict(fetch(OI_ENDPOINT, {"symbol": symbol}))
                if row.get("symbol") != symbol:
                    raise SourceSchemaDrift("OI_SYMBOL_MISMATCH")
                value = _number(row.get("openInterest"), positive=True)
                provider_time = _epoch(row.get("time"))
                if provider_time > now_ms + 120_000:
                    raise SourceSchemaDrift("OI_FUTURE_PROVIDER_TIME")
                _append(store, "oi", "OI_SNAPSHOT", eid, symbol=symbol,
                        source=OI_ENDPOINT, now_ms=now_ms, slot_ms=slot,
                        open_interest_contract_units=value,
                        provider_time_ms=provider_time)
                oi_ids.add(eid)
                stats["oi_written"] += 1
            except SourceSchemaDrift as exc:
                _status(store, "oi", "SCHEMA_DRIFT", symbol, now_ms, slot,
                        str(exc), source=OI_ENDPOINT, existing=oi_ids)
                raise
            except TransportFailure as exc:
                _status(store, "oi", "GAP", symbol, now_ms, slot,
                        str(exc), source=OI_ENDPOINT, existing=oi_ids)
                stats["oi_gap"] += 1

        schedule_eid = f"funding:schedule:{symbol}:{slot}"
        if schedule_eid not in funding_ids:
            try:
                row = _dict(fetch(PREMIUM_ENDPOINT, {"symbol": symbol}))
                if row.get("symbol") != symbol:
                    raise SourceSchemaDrift("FUNDING_SYMBOL_MISMATCH")
                rate = _number(row.get("lastFundingRate"))
                next_time = _epoch(row.get("nextFundingTime"))
                mark_time = _epoch(row.get("time"))
                if next_time <= mark_time or mark_time > now_ms + 120_000:
                    raise SourceSchemaDrift("INVALID_FUNDING_SCHEDULE_CHRONOLOGY")
                _append(store, "funding", "FUNDING_SCHEDULE", schedule_eid,
                        symbol=symbol, source=PREMIUM_ENDPOINT,
                        now_ms=now_ms, funding_rate_indicative=rate,
                        next_funding_time_ms=next_time,
                        provider_time_ms=mark_time, slot_ms=slot)
                funding_ids.add(schedule_eid)
                stats["funding_written"] += 1
            except SourceSchemaDrift as exc:
                _status(store, "funding", "SCHEMA_DRIFT", symbol, now_ms,
                        slot, str(exc), source=PREMIUM_ENDPOINT,
                        existing=funding_ids)
                raise
            except TransportFailure as exc:
                _status(store, "funding", "GAP", symbol, now_ms, slot,
                        str(exc), source=PREMIUM_ENDPOINT,
                        existing=funding_ids)
                stats["funding_gap"] += 1

        # Provider-sourced realized settlements may be discovered late.
        # Their observed_at_ms remains NOW; historical settlement time is
        # NEVER fabricated as the observation time.
        try:
            history = fetch(SETTLEMENT_ENDPOINT, {
                "symbol": symbol, "startTime": max(1, now_ms - 72 * HOUR_MS),
                "endTime": now_ms, "limit": 100,
            })
            if type(history) is not list:
                raise SourceSchemaDrift("FUNDING_HISTORY_NOT_ARRAY")
            for item in history:
                row = _dict(item)
                if row.get("symbol") != symbol:
                    raise SourceSchemaDrift("FUNDING_HISTORY_SYMBOL_MISMATCH")
                settlement = _epoch(row.get("fundingTime"))
                realized = _number(row.get("fundingRate"))
                event_id = f"funding:settled:{symbol}:{settlement}"
                if event_id not in funding_ids:
                    _append(store, "funding", "FUNDING_SETTLED", event_id,
                            symbol=symbol, source=SETTLEMENT_ENDPOINT,
                            now_ms=now_ms, funding_time_ms=settlement,
                            funding_rate_realized=realized)
                    funding_ids.add(event_id)
                    stats["funding_written"] += 1
        except SourceSchemaDrift as exc:
            _status(store, "funding", "SCHEMA_DRIFT", symbol, now_ms,
                    slot, str(exc), source=SETTLEMENT_ENDPOINT,
                    existing=funding_ids)
            raise
        except TransportFailure as exc:
            _status(store, "funding", "GAP", symbol, now_ms, slot,
                    "FUNDING_HISTORY_" + str(exc), source=SETTLEMENT_ENDPOINT,
                    existing=funding_ids)
            stats["funding_gap"] += 1
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="data/flows")
    parser.add_argument("--universe", default=str(UNIVERSE))
    args = parser.parse_args()
    now_ms = int(time.time() * 1000)
    symbols = symbols_from_config(Path(args.universe))
    store = FlowStore(args.root)
    print(json.dumps(collect_once(store, symbols, now_ms=now_ms), sort_keys=True))


if __name__ == "__main__":
    main()
